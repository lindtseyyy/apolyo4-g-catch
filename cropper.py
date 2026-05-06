#!/usr/bin/env python3
"""
GCash Receipt Cropper
=====================
Accepts a GCash receipt image, saves the raw upload, then uses OCR + OpenCV to
crop and save each individual field as its own image:
  - name
  - phone_number
  - amount
  - total_amount
  - reference_number
  - date

Works across the different GCash receipt layout variants (full-screen, cropped,
two-line ref/date, etc.).

Usage:
    python gcash_cropper.py <input_image> [--out-dir <directory>]

Outputs:
    processed_receipts/full/    — full copy of the original upload
    processed_receipts/cropped/ — one PNG per extracted field
    <out-dir>/result.json   — JSON with the text values and crop file paths
"""

import os
import re
import sys
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime

import cv2
import numpy as np
import pytesseract
from PIL import Image

# Windows-specific Tesseract path setup
import platform
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Helper functions for loading, OCR, and box handling

def load_image(path: str):
    """Load with OpenCV + PIL (for Tesseract)."""
    cv_img = cv2.imread(path)
    if cv_img is None:
        raise FileNotFoundError(f"Cannot read image: {path}")
    pil_img = Image.open(path).convert("RGB")
    return cv_img, pil_img


def get_ocr_data(pil_img: Image.Image) -> dict:
    """Run Tesseract and return the data dict."""
    return pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT)


def words_with_boxes(ocr_data: dict) -> list[dict]:
    """Return list of {text, x, y, w, h, conf} for non-empty tokens."""
    rows = []
    for i, text in enumerate(ocr_data["text"]):
        t = text.strip()
        if not t:
            continue
        rows.append(
            dict(
                text=t,
                x=ocr_data["left"][i],
                y=ocr_data["top"][i],
                w=ocr_data["width"][i],
                h=ocr_data["height"][i],
                conf=int(ocr_data["conf"][i]),
            )
        )
    return rows


def find_word(words: list[dict], pattern: str, flags=re.IGNORECASE) -> dict | None:
    """Return first word whose text matches `pattern`."""
    rx = re.compile(pattern, flags)
    for w in words:
        if rx.search(w["text"]):
            return w
    return None


def find_words(words: list[dict], pattern: str, flags=re.IGNORECASE) -> list[dict]:
    rx = re.compile(pattern, flags)
    return [w for w in words if rx.search(w["text"])]


def words_in_row(words: list[dict], anchor_y: int, tolerance: int = 20) -> list[dict]:
    """Return words whose vertical centre is within `tolerance` px of anchor_y."""
    return [
        w for w in words
        if abs((w["y"] + w["h"] // 2) - anchor_y) <= tolerance
    ]


def words_below(words: list[dict], y_min: int, y_max: int) -> list[dict]:
    return [w for w in words if y_min <= w["y"] <= y_max]


def bbox_of(word_list: list[dict]) -> tuple[int, int, int, int]:
    """Return (x, y, x2, y2) bounding box covering all words."""
    xs = [w["x"] for w in word_list]
    ys = [w["y"] for w in word_list]
    x2s = [w["x"] + w["w"] for w in word_list]
    y2s = [w["y"] + w["h"] for w in word_list]
    return min(xs), min(ys), max(x2s), max(y2s)


def pad_bbox(bbox: tuple, pad: int, img_shape: tuple) -> tuple:
    """Expand bbox by `pad` pixels, clamped to image bounds."""
    h, w = img_shape[:2]
    x1, y1, x2, y2 = bbox
    return (
        max(0, x1 - pad),
        max(0, y1 - pad),
        min(w, x2 + pad),
        min(h, y2 + pad),
    )


def crop_and_save(cv_img, bbox: tuple, path: str):
    """Crop region from cv_img and save to path."""
    x1, y1, x2, y2 = bbox
    crop = cv_img[y1:y2, x1:x2]
    cv2.imwrite(path, crop)
    return path


def joined_text(word_list: list[dict]) -> str:
    return " ".join(w["text"] for w in sorted(word_list, key=lambda w: w["x"]))

# Find the white receipt card area so later crops are relative to it

def find_receipt_card(cv_img) -> tuple[int, int, int, int]:
    """
    Detect the white receipt card area.
    Returns (x1, y1, x2, y2) or the full image bounds on failure.
    """
    h, w = cv_img.shape[:2]
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 230, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    best = None
    best_area = 0
    for cnt in contours:
        x, y, cw, ch = cv2.boundingRect(cnt)
        area = cw * ch
        # Must cover a reasonable chunk of the image width
        if cw > w * 0.5 and ch > h * 0.2 and area > best_area:
            best = (x, y, x + cw, y + ch)
            best_area = area
    return best if best else (0, 0, w, h)


# Field extraction helpers for the different receipt values

def extract_name(words: list[dict], img_shape, card_bbox: tuple) -> tuple[dict | None, str]:
    """
    Name is the bold text near the top of the receipt card, above the phone number.
    It often looks like: FA••H MA•••••E O.  /  RI····D P.  /  DU··E H.
    Strategy: find the phone number anchor (+63…) then grab text 1–3 rows above.
    """
    phone = find_word(words, r"\+63")
    if phone is None:
        return None, ""

    phone_cy = phone["y"] + phone["h"] // 2
    # Name is typically 30–120 px above the phone row
    name_candidates = [
        w for w in words
        if (phone["y"] - 130) < w["y"] < (phone["y"] - 10)
        and w["x"] > card_bbox[0]  # inside the card
    ]
    if not name_candidates:
        return None, ""

    # Group by row (within 15 px)
    rows_by_y: dict[int, list] = {}
    for w in name_candidates:
        cy = w["y"] + w["h"] // 2
        placed = False
        for key in rows_by_y:
            if abs(cy - key) <= 15:
                rows_by_y[key].append(w)
                placed = True
                break
        if not placed:
            rows_by_y[cy] = [w]

    # Pick the row closest to the phone line (largest y)
    best_row = max(rows_by_y.keys())
    name_words = rows_by_y[best_row]
    bbox = pad_bbox(bbox_of(name_words), 6, img_shape)
    text = joined_text(name_words)
    return bbox, text


def extract_phone(words: list[dict], img_shape) -> tuple[dict | None, str]:
    """Phone number: +63 XXX XXX XXXX (may be split across tokens)."""
    # Find the +63 token
    token = find_word(words, r"^\+63$")
    if token is None:
        # Sometimes OCR reads it as +63XXXXXXXXXX together
        token = find_word(words, r"\+63\d")
        if token:
            bbox = pad_bbox((token["x"], token["y"], token["x"] + token["w"], token["y"] + token["h"]), 6, img_shape)
            return bbox, token["text"]
        return None, ""

    # Collect all tokens on the same row
    row = words_in_row(words, token["y"] + token["h"] // 2, tolerance=18)
    # Filter only phone-like tokens
    phone_parts = [w for w in row if re.search(r"[\d\+\.\·•·]", w["text"])]
    if not phone_parts:
        phone_parts = [token]
    bbox = pad_bbox(bbox_of(phone_parts), 6, img_shape)
    text = joined_text(phone_parts)
    return bbox, text


def extract_amount(words: list[dict], img_shape) -> tuple[dict | None, str]:
    """
    'Amount' label row — grab the numeric value on the same row (right side).
    Avoid the 'Total Amount Sent' row.
    """
    amount_labels = find_words(words, r"^Amount$")
    # We want the one that is NOT preceded by 'Total' nearby
    target_label = None
    for lbl in amount_labels:
        # Check if 'Total' exists within 100px to the left on the same row
        row = words_in_row(words, lbl["y"] + lbl["h"] // 2, tolerance=20)
        has_total = any(re.search(r"Total", w["text"], re.I) for w in row)
        if not has_total:
            target_label = lbl
            break

    if target_label is None:
        return None, ""

    row = words_in_row(words, target_label["y"] + target_label["h"] // 2, tolerance=20)
    # Amount value is to the right of the label
    value_words = [w for w in row if w["x"] > target_label["x"] + target_label["w"]
                   and re.search(r"[\d,\.]+", w["text"])]
    if not value_words:
        return None, ""

    bbox = pad_bbox(bbox_of(value_words), 6, img_shape)
    text = joined_text(value_words)
    return bbox, text


def extract_total_amount(words: list[dict], img_shape) -> tuple[dict | None, str]:
    """
    'Total Amount Sent' row — grab the ₱XXXXX value.
    The peso sign may be read as P, ₱, or P4, etc.
    """
    total_lbl = find_word(words, r"^Total$")
    if total_lbl is None:
        return None, ""

    total_cy = total_lbl["y"] + total_lbl["h"] // 2

    # The value may span the same row or be 1 line below (wrap in narrow screens)
    # Search ±40 px from the Total label centre
    candidate_words = [
        w for w in words
        if abs((w["y"] + w["h"] // 2) - total_cy) <= 40
        and w["x"] > total_lbl["x"] + 50  # to the right
        and re.search(r"[\d,\.₱P]", w["text"])
    ]
    if not candidate_words:
        # Try a wider band (some layouts wrap)
        candidate_words = [
            w for w in words
            if total_lbl["y"] <= w["y"] <= total_lbl["y"] + 80
            and re.search(r"[₱P]\d|^\d{2,}", w["text"])
        ]

    if not candidate_words:
        return None, ""

    bbox = pad_bbox(bbox_of(candidate_words), 8, img_shape)
    text = joined_text(candidate_words)
    return bbox, text


def extract_ref_and_date(words: list[dict], img_shape) -> tuple:
    """
    Reference number + date.  These may be on the same line or split across
    two lines (narrow phone screenshots).
    Returns ((ref_bbox, ref_text), (date_bbox, date_text))
    """
    ref_label = find_word(words, r"^Ref$|^Ref\.$|^Ref\s*No")
    if ref_label is None:
        return (None, ""), (None, "")

    ref_cy = ref_label["y"] + ref_label["h"] // 2

    # All words within ±30 px vertically of the Ref label
    ref_row = words_in_row(words, ref_cy, tolerance=30)

    # Reference number: one long digit OR multiple shorter tokens (e.g. "1039 879 183868")
    def is_ref_token(w):
        t = w["text"]
        if not re.search(r"^\d{3,}$", t):
            return False
        # Exclude 4-digit year-like numbers (1900-2099)
        if re.match(r"^(19|20)\d{2}$", t):
            return False
        return True

    ref_number_words = [
        w for w in ref_row
        if is_ref_token(w) and w["x"] > ref_label["x"]
    ]
    # Also check 1-2 rows below ref label (two-line layout)
    if not ref_number_words:
        look_y_max = ref_label["y"] + ref_label["h"] + 70
        below_ref = words_below(words, ref_label["y"] + 5, look_y_max)
        ref_number_words = [w for w in below_ref if is_ref_token(w) and w["x"] > ref_label["x"]]

    # date parsing: look for month names / day / year rather than raw digit strings
    month_abbrs = r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
    # A date token is: month name, day number (1-2 digits optionally followed by comma),
    # 4-digit year, time like 9:14, or AM/PM
    date_token_pattern = re.compile(
        rf"^({month_abbrs}|\d{{1,2}},?$|\d{{4}}|\d{{1,2}}:\d{{2}}|AM|PM)$",
        re.IGNORECASE,
    )

    def is_date_token(w):
        return bool(date_token_pattern.match(w["text"])) and not re.match(r"^\d{6,}$", w["text"])

    date_words_same_row = [w for w in ref_row if is_date_token(w)]

    # If no date on same row (two-line layout), check 1–3 rows below ref label
    if not date_words_same_row:
        look_below_y_max = ref_label["y"] + ref_label["h"] + 70
        below = words_below(words, ref_label["y"] + 5, look_below_y_max)
        date_words_same_row = [w for w in below if is_date_token(w)]

    ref_bbox, ref_text = None, ""
    date_bbox, date_text = None, ""

    if ref_number_words:
        ref_bbox = pad_bbox(bbox_of(ref_number_words), 6, img_shape)
        ref_text = joined_text(ref_number_words)

    if date_words_same_row:
        date_bbox = pad_bbox(bbox_of(date_words_same_row), 6, img_shape)
        date_text = joined_text(date_words_same_row)

    return (ref_bbox, ref_text), (date_bbox, date_text)


# Main pipeline for processing one receipt image

def process_receipt(input_path: str, out_dir: str) -> dict:
    out_dir = Path(out_dir)
    raw_dir = out_dir / "full"
    fields_dir = out_dir / "cropped"
    raw_dir.mkdir(parents=True, exist_ok=True)
    fields_dir.mkdir(parents=True, exist_ok=True)

    # save a raw copy of the upload before modifying anything
    raw_dest = raw_dir / Path(input_path).name
    shutil.copy2(input_path, raw_dest)
    print(f"[✓] Raw receipt saved → {raw_dest}")

    # load the image and run OCR to get word boxes
    cv_img, pil_img = load_image(input_path)
    ocr_data = get_ocr_data(pil_img)
    words = words_with_boxes(ocr_data)
    card_bbox = find_receipt_card(cv_img)
    print(f"[✓] OCR complete — {len(words)} tokens detected")
    print(f"[✓] Receipt card region: {card_bbox}")

    stem = Path(input_path).stem
    result = {
        "source_file": str(input_path),
        "raw_copy": str(raw_dest),
        "processed_at": datetime.now().isoformat(),
        "fields": {},
    }

    def save_field(name: str, bbox, text: str):
        if bbox is None:
            print(f"[!] Could not locate field: {name}")
            result["fields"][name] = {"text": text or "NOT_FOUND", "crop": None}
            return
        crop_path = str(fields_dir / f"{stem}__{name}.png")
        crop_and_save(cv_img, bbox, crop_path)
        print(f"[✓] {name:20s}: {text!r:35s} → {crop_path}")
        result["fields"][name] = {"text": text, "crop": crop_path}

    # extract all known fields from OCR words
    name_bbox, name_text = extract_name(words, cv_img.shape, card_bbox)
    # Fallback: if name not found via OCR (blue-on-blue header), crop the region
    # just above the "Amount" label as a best-effort visual crop
    if name_bbox is None:
        amount_lbl = find_word(words, r"^Amount$")
        if amount_lbl:
            # Crop from top of card to just above Amount label
            cx1 = card_bbox[0]
            cy1 = card_bbox[1]
            cx2 = card_bbox[2]
            cy2 = amount_lbl["y"] - 10
            if cy2 > cy1:
                name_bbox = pad_bbox((cx1, cy1, cx2, cy2), 0, cv_img.shape)
                name_text = "SEE_CROP"
    save_field("name", name_bbox, name_text)

    phone_bbox, phone_text = extract_phone(words, cv_img.shape)
    # Fallback for phone: crop header region centred around y=600-700 if not found
    if phone_bbox is None:
        amount_lbl = find_word(words, r"^Amount$")
        if amount_lbl:
            mid_y = (card_bbox[1] + amount_lbl["y"]) // 2
            phone_bbox = pad_bbox((card_bbox[0], mid_y - 50, card_bbox[2], mid_y + 50), 0, cv_img.shape)
            phone_text = "SEE_CROP"
    save_field("phone_number", phone_bbox, phone_text)

    amount_bbox, amount_text = extract_amount(words, cv_img.shape)
    save_field("amount", amount_bbox, amount_text)

    total_bbox, total_text = extract_total_amount(words, cv_img.shape)
    save_field("total_amount", total_bbox, total_text)

    (ref_bbox, ref_text), (date_bbox, date_text) = extract_ref_and_date(words, cv_img.shape)
    save_field("reference_number", ref_bbox, ref_text)
    save_field("date", date_bbox, date_text)

    # write the result metadata and crop paths to JSON
    json_path = out_dir / f"{stem}__result.json"
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"[✓] JSON result → {json_path}")

    return result


# Helper for batch processing multiple receipt images

def process_batch(input_paths: list[str], out_dir: str) -> list[dict]:
    results = []
    for p in input_paths:
        print(f"\n{'='*60}")
        print(f"Processing: {p}")
        print('='*60)
        try:
            r = process_receipt(p, out_dir)
            results.append(r)
        except Exception as e:
            print(f"[ERROR] {p}: {e}")
    return results


# Command-line interface setup

def main():
    parser = argparse.ArgumentParser(
        description="Crop individual fields from GCash receipt images."
    )
    parser.add_argument(
        "images",
        nargs="+",
        help="Path(s) to GCash receipt image(s)",
    )
    parser.add_argument(
        "--out-dir",
        default="processed_receipts",
        help="Directory to write outputs (default: ./processed_receipts)",
    )
    args = parser.parse_args()
    process_batch(args.images, args.out_dir)


if __name__ == "__main__":
    main()