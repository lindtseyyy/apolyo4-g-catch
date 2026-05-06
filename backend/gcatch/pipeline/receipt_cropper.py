"""GCash receipt field extractor.

Isolates the white card panel from a receipt screenshot, runs OCR, and
extracts individual fields: name, phone, amount, total, ref#, date.
"""

import re
import shutil
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import pytesseract
from PIL import Image


# ---------------------------------------------------------------------------
# White card detection
# ---------------------------------------------------------------------------

def extract_white_card(cv_img):
    """Find the white card panel in a receipt image.

    Returns (card_crop, bbox) where bbox is (x1, y1, x2, y2). Falls back
    to the full image if no white panel is detected.
    """
    h, w = cv_img.shape[:2]

    hsv = cv2.cvtColor(cv_img, cv2.COLOR_BGR2HSV)
    lower_white = np.array([0, 0, 200], dtype=np.uint8)
    upper_white = np.array([180, 40, 255], dtype=np.uint8)
    mask = cv2.inRange(hsv, lower_white, upper_white)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 30))
    closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    best_bbox = None
    best_area = 0

    for cnt in contours:
        x, y, cw, ch = cv2.boundingRect(cnt)
        area = cw * ch
        if cw >= w * 0.50 and ch >= h * 0.15 and area > best_area:
            best_bbox = (x, y, x + cw, y + ch)
            best_area = area

    if best_bbox is None:
        return cv_img.copy(), (0, 0, w, h)

    x1, y1, x2, y2 = best_bbox
    x1 = max(0, x1 - 2)
    y1 = max(0, y1 - 2)
    x2 = min(w, x2 + 2)
    y2 = min(h, y2 + 2)

    return cv_img[y1:y2, x1:x2], (x1, y1, x2, y2)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_image(path):
    cv_img = cv2.imread(str(path))
    if cv_img is None:
        raise FileNotFoundError(f"Cannot read image: {path}")
    return cv_img


def _cv2pil(cv_img):
    return Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))


def _get_ocr_data(pil_img):
    config = "--oem 3 --psm 6"
    return pytesseract.image_to_data(
        pil_img, output_type=pytesseract.Output.DICT, config=config
    )


def _words_with_boxes(ocr_data):
    rows = []
    for i, text in enumerate(ocr_data["text"]):
        t = text.strip()
        if not t:
            continue
        rows.append({
            "text": t,
            "x": ocr_data["left"][i],
            "y": ocr_data["top"][i],
            "w": ocr_data["width"][i],
            "h": ocr_data["height"][i],
            "conf": int(ocr_data["conf"][i]),
        })
    return rows


def _find_word(words, pattern, flags=re.IGNORECASE):
    rx = re.compile(pattern, flags)
    for w in words:
        if rx.search(w["text"]):
            return w
    return None


def _find_words(words, pattern, flags=re.IGNORECASE):
    rx = re.compile(pattern, flags)
    return [w for w in words if rx.search(w["text"])]


def _words_in_row(words, anchor_y, tolerance=20):
    return [w for w in words if abs((w["y"] + w["h"] // 2) - anchor_y) <= tolerance]


def _bbox_of(word_list):
    xs = [w["x"] for w in word_list]
    ys = [w["y"] for w in word_list]
    x2s = [w["x"] + w["w"] for w in word_list]
    y2s = [w["y"] + w["h"] for w in word_list]
    return min(xs), min(ys), max(x2s), max(y2s)


def _pad_bbox(bbox, pad, img_shape):
    h, w = img_shape[:2]
    x1, y1, x2, y2 = bbox
    return max(0, x1 - pad), max(0, y1 - pad), min(w, x2 + pad), min(h, y2 + pad)


def _joined_text(word_list):
    return " ".join(w["text"] for w in sorted(word_list, key=lambda w: w["x"]))


# ---------------------------------------------------------------------------
# Field extractors (coordinates relative to card crop)
# ---------------------------------------------------------------------------

def extract_amount(words, img_shape):
    """Locate the Amount value and return (bbox, text)."""
    amount_labels = _find_words(words, r"^Amount$")
    target_label = None
    for lbl in amount_labels:
        row = _words_in_row(words, lbl["y"] + lbl["h"] // 2, tolerance=20)
        if not any(re.search(r"Total", w["text"], re.I) for w in row):
            target_label = lbl
            break
    if target_label is None:
        return None, ""

    row = _words_in_row(words, target_label["y"] + target_label["h"] // 2, tolerance=20)
    value_words = [
        w for w in row
        if w["x"] > target_label["x"] + target_label["w"]
        and re.search(r"[\d,\.]+", w["text"])
    ]
    if not value_words:
        return None, ""
    return _pad_bbox(_bbox_of(value_words), 2, img_shape), _joined_text(value_words)


def extract_total_amount(words, img_shape):
    """Locate the Total amount value and return (bbox, text)."""
    total_lbl = _find_word(words, r"^Total$")
    if total_lbl is None:
        return None, ""

    total_cy = total_lbl["y"] + total_lbl["h"] // 2
    candidate_words = [
        w for w in words
        if abs((w["y"] + w["h"] // 2) - total_cy) <= 40
        and w["x"] > total_lbl["x"] + 50
        and re.search(r"[\d,\.₱P]", w["text"])
    ]
    if not candidate_words:
        candidate_words = [
            w for w in words
            if total_lbl["y"] <= w["y"] <= total_lbl["y"] + 80
            and re.search(r"[₱P]\d|^\d{2,}", w["text"])
        ]
    if not candidate_words:
        return None, ""
    return _pad_bbox(_bbox_of(candidate_words), 2, img_shape), _joined_text(candidate_words)


def extract_name(words, img_shape):
    phone = _find_word(words, r"\+63")
    if phone is None:
        return None, ""
    name_candidates = [
        w for w in words
        if (phone["y"] - 130) < w["y"] < (phone["y"] - 5)
    ]
    if not name_candidates:
        return None, ""

    rows_by_y = {}
    for w in name_candidates:
        cy = w["y"] + w["h"] // 2
        placed = False
        for key in list(rows_by_y):
            if abs(cy - key) <= 15:
                rows_by_y[key].append(w)
                placed = True
                break
        if not placed:
            rows_by_y[cy] = [w]
    best_row = max(rows_by_y.keys())
    name_words = rows_by_y[best_row]
    return _pad_bbox(_bbox_of(name_words), 2, img_shape), _joined_text(name_words)


def extract_phone(words, img_shape):
    token = _find_word(words, r"^\+63$")
    if token is None:
        token = _find_word(words, r"\+63\d")
        if token:
            bbox = _pad_bbox(
                (token["x"], token["y"], token["x"] + token["w"], token["y"] + token["h"]),
                6, img_shape,
            )
            return bbox, token["text"]
        return None, ""

    row = _words_in_row(words, token["y"] + token["h"] // 2, tolerance=18)
    phone_parts = [w for w in row if re.search(r"[\d\+\.·•·]", w["text"])]
    if not phone_parts:
        phone_parts = [token]
    return _pad_bbox(_bbox_of(phone_parts), 2, img_shape), _joined_text(phone_parts)


def extract_ref_and_date(words, img_shape, card_cv=None):
    """Extract reference number and date. Handles single-line and two-line layouts."""
    ref_label = _find_word(words, r"^Ref$|^Ref\.$|^Ref\s*No")
    if ref_label is None:
        return (None, ""), (None, "")

    img_h, img_w = img_shape[:2]
    y_top = max(0, ref_label["y"] - 8)
    y_bottom = min(img_h, ref_label["y"] + ref_label["h"] + 130)

    strip_words = None
    strip_y_offset = 0

    if card_cv is not None:
        strip = card_cv[y_top:y_bottom, :]
        strip_pil = _cv2pil(strip)
        sd = pytesseract.image_to_data(
            strip_pil, output_type=pytesseract.Output.DICT, config="--oem 3 --psm 6",
        )
        strip_words = []
        for i, text in enumerate(sd["text"]):
            t = text.strip()
            if not t:
                continue
            strip_words.append({
                "text": t,
                "x": sd["left"][i],
                "y": sd["top"][i],
                "w": sd["width"][i],
                "h": sd["height"][i],
            })
        strip_y_offset = y_top
        ref_in_strip = _find_word(strip_words, r"^Ref$|^Ref\.$|^Ref\s*No")
        if ref_in_strip:
            ref_label = ref_in_strip
        band_words = strip_words
    else:
        band_words = [w for w in words if y_top <= w["y"] <= y_bottom]

    month_abbrs = r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
    date_token_pattern = re.compile(
        rf"^({month_abbrs}|\d{{1,2}},?|\d{{4}}|\d{{1,2}}:\d{{2}}|AM|PM)$",
        re.IGNORECASE,
    )

    def _is_ref_token(w):
        t = w["text"]
        if not re.fullmatch(r"\d{3,}", t):
            return False
        if re.fullmatch(r"(19|20)\d{2}", t):
            return False
        return True

    def _is_date_token(w):
        t = w["text"]
        if re.fullmatch(r"\d{6,}", t):
            return False
        return bool(date_token_pattern.match(t))

    all_ref_candidates = [
        w for w in band_words
        if _is_ref_token(w) and w["x"] > ref_label["x"]
    ]

    col_split = (
        max(w["x"] + w["w"] for w in all_ref_candidates) + 20
        if all_ref_candidates else img_w // 2
    )

    left_words = [w for w in band_words if (w["x"] + w["w"]) <= col_split]
    right_words = [w for w in band_words if w["x"] > col_split]

    ref_number_words = [
        w for w in left_words
        if _is_ref_token(w) and w["x"] > ref_label["x"]
    ]
    date_words = [w for w in right_words if _is_date_token(w)]

    if not ref_number_words:
        ref_number_words = [w for w in band_words if _is_ref_token(w) and w["x"] > ref_label["x"]]
    if not date_words:
        date_words = [w for w in band_words if _is_date_token(w)]

    ref_number_words = sorted(ref_number_words, key=lambda w: (w["y"], w["x"]))
    date_words = sorted(date_words, key=lambda w: (w["y"], w["x"]))

    def _make_bbox(wlist):
        x1, y1, x2, y2 = _bbox_of(wlist)
        return (x1, y1 + strip_y_offset, x2, y2 + strip_y_offset)

    ref_bbox, ref_text = (
        _pad_bbox(_make_bbox(ref_number_words), 2, img_shape),
        _joined_text(ref_number_words),
    ) if ref_number_words else (None, "")

    date_bbox, date_text = (
        _pad_bbox(_make_bbox(date_words), 2, img_shape),
        _joined_text(date_words),
    ) if date_words else (None, "")

    return (ref_bbox, ref_text), (date_bbox, date_text)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def process_receipt(input_path, out_dir="processed_receipts"):
    """Extract all fields from a GCash receipt image.

    Returns a dict with field texts, crop paths, and metadata.
    """
    out_dir = Path(out_dir)
    raw_dir = out_dir / "full"
    card_dir = out_dir / "card"
    fields_dir = out_dir / "cropped"
    for d in (raw_dir, card_dir, fields_dir):
        d.mkdir(parents=True, exist_ok=True)

    stem = Path(input_path).stem

    raw_dest = raw_dir / Path(input_path).name
    shutil.copy2(input_path, raw_dest)

    full_cv = _load_image(input_path)

    card_cv, card_bbox = extract_white_card(full_cv)
    card_path = str(card_dir / f"{stem}__card.png")
    cv2.imwrite(card_path, card_cv)

    card_pil = _cv2pil(card_cv)
    ocr_data = _get_ocr_data(card_pil)
    words = _words_with_boxes(ocr_data)

    result = {
        "source_file": str(input_path),
        "raw_copy": str(raw_dest),
        "card_crop": card_path,
        "card_bbox": card_bbox,
        "processed_at": datetime.now().isoformat(),
        "fields": {},
    }

    src_ext = Path(input_path).suffix.lower() or ".jpg"
    card_x1, card_y1 = card_bbox[0], card_bbox[1]

    def _save_field(name, bbox, text):
        if bbox is None:
            result["fields"][name] = {"text": text or "NOT_FOUND", "crop": None}
            return
        bx1, by1, bx2, by2 = bbox
        full_bbox = (bx1 + card_x1, by1 + card_y1, bx2 + card_x1, by2 + card_y1)
        crop_path = str(fields_dir / f"{stem}__{name}{src_ext}")
        x1, y1, x2, y2 = full_bbox
        ext = Path(crop_path).suffix.lower()
        if ext in (".jpg", ".jpeg"):
            cv2.imwrite(crop_path, full_cv[y1:y2, x1:x2], [cv2.IMWRITE_JPEG_QUALITY, 100])
        else:
            cv2.imwrite(crop_path, full_cv[y1:y2, x1:x2])
        result["fields"][name] = {"text": text, "crop": crop_path}

    name_bbox, name_text = extract_name(words, card_cv.shape)
    if name_bbox is None:
        amount_lbl = _find_word(words, r"^Amount$")
        if amount_lbl:
            cw = card_cv.shape[1]
            name_bbox = _pad_bbox((0, 0, cw, amount_lbl["y"] - 10), 0, card_cv.shape)
            name_text = "SEE_CROP"
    _save_field("name", name_bbox, name_text)

    phone_bbox, phone_text = extract_phone(words, card_cv.shape)
    if phone_bbox is None:
        amount_lbl = _find_word(words, r"^Amount$")
        if amount_lbl:
            cw = card_cv.shape[1]
            mid_y = amount_lbl["y"] // 2
            phone_bbox = _pad_bbox((0, mid_y - 50, cw, mid_y + 50), 0, card_cv.shape)
            phone_text = "SEE_CROP"
    _save_field("phone_number", phone_bbox, phone_text)

    amount_bbox, amount_text = extract_amount(words, card_cv.shape)
    _save_field("amount", amount_bbox, amount_text)

    total_bbox, total_text = extract_total_amount(words, card_cv.shape)
    _save_field("total_amount", total_bbox, total_text)

    (ref_bbox, ref_text), (date_bbox, date_text) = extract_ref_and_date(words, card_cv.shape, card_cv=card_cv)
    _save_field("reference_number", ref_bbox, ref_text)
    _save_field("date", date_bbox, date_text)

    return result


def extract_amount_field_from_receipt(input_path, output_path=None):
    """Extract just the Amount field crop from a receipt image.

    Returns the cropped amount image (BGR numpy array) and the OCR'd text.
    """
    full_cv = _load_image(input_path)
    card_cv, card_bbox = extract_white_card(full_cv)

    card_pil = _cv2pil(card_cv)
    ocr_data = _get_ocr_data(card_pil)
    words = _words_with_boxes(ocr_data)

    amount_bbox, amount_text = extract_amount(words, card_cv.shape)
    if amount_bbox is None:
        return None, ""

    card_x1, card_y1 = card_bbox[0], card_bbox[1]
    bx1, by1, bx2, by2 = amount_bbox
    full_bbox = (bx1 + card_x1, by1 + card_y1, bx2 + card_x1, by2 + card_y1)

    x1, y1, x2, y2 = full_bbox
    amount_crop = full_cv[y1:y2, x1:x2]

    if output_path:
        cv2.imwrite(str(output_path), amount_crop)

    return amount_crop, amount_text


def extract_total_amount_field_from_receipt(input_path, output_path=None):
    """Extract just the Total Amount field crop from a receipt image.

    Finds the "Total" label via OCR and crops the value next to it.
    Returns the cropped total amount image (BGR numpy array) and the OCR'd text.
    """
    full_cv = _load_image(input_path)
    card_cv, card_bbox = extract_white_card(full_cv)

    card_pil = _cv2pil(card_cv)
    ocr_data = _get_ocr_data(card_pil)
    words = _words_with_boxes(ocr_data)

    total_bbox, total_text = extract_total_amount(words, card_cv.shape)
    if total_bbox is None:
        return None, ""

    card_x1, card_y1 = card_bbox[0], card_bbox[1]
    bx1, by1, bx2, by2 = total_bbox
    full_bbox = (bx1 + card_x1, by1 + card_y1, bx2 + card_x1, by2 + card_y1)

    x1, y1, x2, y2 = full_bbox
    total_crop = full_cv[y1:y2, x1:x2]

    if output_path:
        cv2.imwrite(str(output_path), total_crop)

    return total_crop, total_text


def extract_all_field_crops(input_path):
    """Extract all recognizable fields from a GCash receipt as in-memory crops.

    Returns a dict mapping field_name → (crop_bgr_array, ocr_text). Fields
    that cannot be located are omitted from the dict.

    Fields extracted: name, phone_number, amount, total_amount,
    reference_number, date.
    """
    full_cv = _load_image(input_path)
    card_cv, card_bbox = extract_white_card(full_cv)

    card_pil = _cv2pil(card_cv)
    ocr_data = _get_ocr_data(card_pil)
    words = _words_with_boxes(ocr_data)

    card_x1, card_y1 = card_bbox[0], card_bbox[1]

    def _crop_field(bbox):
        """Convert card-relative bbox to full-image crop."""
        if bbox is None:
            return None
        bx1, by1, bx2, by2 = bbox
        fx1 = bx1 + card_x1
        fy1 = by1 + card_y1
        fx2 = bx2 + card_x1
        fy2 = by2 + card_y1
        return full_cv[fy1:fy2, fx1:fx2]

    fields = {}

    # Name
    bbox, text = extract_name(words, card_cv.shape)
    crop = _crop_field(bbox)
    if crop is not None:
        fields["name"] = (crop, text)

    # Phone number
    bbox, text = extract_phone(words, card_cv.shape)
    crop = _crop_field(bbox)
    if crop is not None:
        fields["phone_number"] = (crop, text)

    # Amount
    bbox, text = extract_amount(words, card_cv.shape)
    crop = _crop_field(bbox)
    if crop is not None:
        fields["amount"] = (crop, text)

    # Total amount
    bbox, text = extract_total_amount(words, card_cv.shape)
    crop = _crop_field(bbox)
    if crop is not None:
        fields["total_amount"] = (crop, text)

    # Reference number and date
    (ref_bbox, ref_text), (date_bbox, date_text) = \
        extract_ref_and_date(words, card_cv.shape, card_cv=card_cv)

    ref_crop = _crop_field(ref_bbox)
    if ref_crop is not None:
        fields["reference_number"] = (ref_crop, ref_text)

    date_crop = _crop_field(date_bbox)
    if date_crop is not None:
        fields["date"] = (date_crop, date_text)

    return fields
