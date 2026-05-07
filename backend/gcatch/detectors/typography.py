import cv2
import numpy as np

from gcatch.utils.image import preprocess_image, find_text_regions


# ---------------------------------------------------------------------------
# General-purpose typography forensics
# ---------------------------------------------------------------------------

def analyze_typography(image, output_path=None):
    """Run typography & kerning forensics on an image.

    Accepts a file path (str) or an in-memory BGR numpy array. Detects
    individual character regions and checks font consistency (aspect ratio
    variance), kerning gaps, and whether aspect ratios match expected GCash
    UI font ranges.

    Args:
        image: File path (str) or numpy array (BGR).
        output_path: Optional path to save the annotated proof image.

    Returns:
        dict with keys: verdict, fraud_flags, reasons, avg_aspect_ratio,
        gap_analysis, char_count, proof_image.
    """
    if isinstance(image, str):
        img = cv2.imread(image)
        if img is None:
            raise ValueError(f"Could not read image: {image}")
    else:
        img = image.copy()

    processed, gray = preprocess_image(img)
    bounding_boxes = find_text_regions(processed)

    if len(bounding_boxes) < 1:
        _, thresh = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            if cv2.contourArea(c) > 0:
                x, y, w, h = cv2.boundingRect(c)
                if w > 0 and h > 0:
                    bounding_boxes.append((x, y, w, h))
        bounding_boxes = sorted(bounding_boxes, key=lambda b: b[0])

    if len(bounding_boxes) < 1:
        return {
            'verdict': 'INCONCLUSIVE',
            'fraud_flags': 0,
            'reasons': ['No characters detected'],
            'avg_aspect_ratio': 0,
            'gap_analysis': [],
            'char_count': 0,
            'proof_image': img.copy(),
        }

    proof_img = img.copy()

    aspect_ratios = []
    for x, y, w, h in bounding_boxes:
        ratio = round(w / h, 2) if h > 0 else 0
        aspect_ratios.append(ratio)
        cv2.rectangle(proof_img, (x, y), (x + w, y + h), (255, 0, 0), 1)
        cv2.putText(proof_img, str(ratio), (x, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)

    gaps = []
    for i in range(len(bounding_boxes) - 1):
        curr_end = bounding_boxes[i][0] + bounding_boxes[i][2]
        next_start = bounding_boxes[i + 1][0]
        gap = next_start - curr_end
        gaps.append(gap)
        if len(bounding_boxes) > 2:
            mid_y = bounding_boxes[i][1] + int(bounding_boxes[i][3] / 2)
            cv2.line(proof_img, (curr_end, mid_y), (next_start, mid_y),
                     (0, 0, 255), 2)

    fraud_flags = 0
    reasons = []

    if gaps:
        for i, gap in enumerate(gaps):
            if gap > 5 and i == 0:
                fraud_flags += 1
                reasons.append(
                    f"Suspiciously large gap at position {i + 1} ({gap}px). "
                    f"Manual edit likely."
                )
                break

    if len(aspect_ratios) > 1:
        ratio_variance = max(aspect_ratios) - min(aspect_ratios)
        if ratio_variance > 0.08:
            fraud_flags += 1
            reasons.append(
                f"Inconsistent font weights (Variance: {ratio_variance:.2f}). "
                f"Mixed fonts detected."
            )

    if aspect_ratios:
        avg_ratio = sum(aspect_ratios) / len(aspect_ratios)
        if avg_ratio < 0.40 or avg_ratio > 1.50:
            fraud_flags += 1
            reasons.append(
                f"Unusual font aspect ratio ({avg_ratio:.2f}). "
                f"Possible font manipulation."
            )

    verdict = "FORGED" if fraud_flags > 0 else "AUTHENTIC"
    color = (0, 0, 255) if verdict == "FORGED" else (0, 255, 0)

    font_scale = max(0.3, img.shape[0] / 100)
    cv2.putText(proof_img, f"VERDICT: {verdict}",
                (5, max(20, int(img.shape[0] * 0.8))),
                cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 2)

    if output_path:
        cv2.imwrite(output_path, proof_img)

    return {
        'verdict': verdict,
        'fraud_flags': fraud_flags,
        'reasons': reasons,
        'avg_aspect_ratio': sum(aspect_ratios) / len(aspect_ratios) if aspect_ratios else 0,
        'gap_analysis': gaps,
        'char_count': len(bounding_boxes),
        'proof_image': proof_img,
    }


# ---------------------------------------------------------------------------
# Advanced amount-field typography forensics
# ---------------------------------------------------------------------------

WEIGHT_HEIGHT_OUTLIER = 30
WEIGHT_RATIO_OUTLIER = 20
WEIGHT_GAP_OUTLIER = 30
WEIGHT_Y_OUTLIER = 25
WEIGHT_HEIGHT_STD = 20
WEIGHT_RATIO_STD = 25
WEIGHT_Y_STD = 30
WEIGHT_SYMBOL_WIDE = 50
WEIGHT_SYMBOL_RATIO = 40
FAKE_THRESHOLD = 35


def analyze_inconsistencies(bounding_boxes):
    """Statistical analysis of character bounding boxes for inconsistencies.

    Computes per-character metrics (height, aspect ratio, kerning gaps,
    y-position) and flags statistical outliers. Accounts for structural gaps
    (thousands separators, decimal point) that are expected to be larger.

    Args:
        bounding_boxes: List of (x, y, w, h) tuples sorted left-to-right.

    Returns:
        dict with heights, ratios, gaps, y_pos arrays and per-metric flag
        arrays, means, and std deviations.
    """
    if len(bounding_boxes) < 2:
        return {}

    heights = np.array([h for _, _, _, h in bounding_boxes], dtype=float)
    widths = np.array([w for _, _, w, _ in bounding_boxes], dtype=float)
    y_pos = np.array([y for _, y, _, _ in bounding_boxes], dtype=float)
    ratios = widths / heights

    raw_gaps = np.array(
        [bounding_boxes[i][0] - (bounding_boxes[i - 1][0] + bounding_boxes[i - 1][2])
         for i in range(1, len(bounding_boxes))],
        dtype=float
    )

    structural_gap_indices = []
    decimal_gap_idx = None

    if len(raw_gaps) >= 2:
        decimal_gap_idx = len(raw_gaps) - 2
        structural_gap_indices.append(decimal_gap_idx)

        idx = len(raw_gaps) - 5
        while idx >= 0:
            structural_gap_indices.append(idx)
            idx -= 3

    analysis_gaps = np.delete(raw_gaps, structural_gap_indices) if structural_gap_indices else raw_gaps

    digits_before_decimal = (
        decimal_gap_idx + 1 if decimal_gap_idx is not None else len(bounding_boxes)
    )

    def _outlier_mask(values, n_std=2.0):
        mean, std = values.mean(), values.std()
        if std > 0:
            mask = np.abs(values - mean) > n_std * std
        else:
            mask = np.zeros(len(values), dtype=bool)
        return mask, mean, std

    height_flags_raw, h_mean, h_std = _outlier_mask(heights)
    height_flags = height_flags_raw.copy()
    ratio_flags, r_mean, r_std = _outlier_mask(ratios)

    if digits_before_decimal <= 4:
        height_flags[0] = False
        ratio_flags[0] = False

    gap_flags = np.zeros(len(raw_gaps), dtype=bool)

    if len(analysis_gaps) > 0:
        median_gap = float(np.median(analysis_gaps))
        median_width = float(np.median(widths))

        for i in range(len(raw_gaps)):
            gap = raw_gaps[i]
            if i in structural_gap_indices:
                if gap > median_width * 0.8:
                    gap_flags[i] = True
            else:
                if abs(gap - median_gap) > max(2.0, median_gap * 0.5) or gap > median_width * 0.25:
                    gap_flags[i] = True

        g_mean, g_std = analysis_gaps.mean(), analysis_gaps.std()
    else:
        g_mean, g_std = 0.0, 0.0

    bottom_pos = np.array([y + h for _, y, _, h in bounding_boxes], dtype=float)
    median_y = np.median(y_pos)
    median_bottom = np.median(bottom_pos)

    y_flags = (np.abs(y_pos - median_y) >= 1.0) | (np.abs(bottom_pos - median_bottom) >= 2.0)

    y_mean, y_std = y_pos.mean(), y_pos.std()

    y_diffs = np.diff(y_pos)
    monotonic_drift = (
        (np.all(y_diffs <= 0) or np.all(y_diffs >= 0))
        and y_std > 0.5
    )

    return dict(
        heights=heights, ratios=ratios, gaps=raw_gaps, y_pos=y_pos,
        height_flags=height_flags, ratio_flags=ratio_flags,
        gap_flags=gap_flags, y_flags=y_flags,
        h_mean=h_mean, h_std=h_std,
        r_mean=r_mean, r_std=r_std,
        g_mean=g_mean, g_std=g_std,
        y_mean=y_mean, y_std=y_std,
        decimal_gap_idx=decimal_gap_idx,
        digits_before_decimal=digits_before_decimal,
        monotonic_drift=monotonic_drift,
    )


def check_symbol_width(currency_box, digit_boxes):
    """Check if the currency symbol (₱) is abnormally wide.

    A wide symbol suggests a digit may have been merged into it during
    editing, e.g. changing ₱500 to ₱1500 by editing the '1' into the ₱ glyph.

    Args:
        currency_box: (x, y, w, h) of the first (currency) box.
        digit_boxes: List of (x, y, w, h) for the remaining boxes.

    Returns:
        (is_suspicious, details_dict)
    """
    if not digit_boxes:
        return False, {}

    sx, sy, sw, sh = currency_box
    sym_ratio = sw / sh if sh > 0 else 0

    avg_digit_w = float(np.mean([w for _, _, w, _ in digit_boxes]))
    sym_vs_digit = sw / avg_digit_w if avg_digit_w > 0 else 0

    wide_by_ratio = sym_ratio > 1.3
    wide_by_digits = sym_vs_digit > 1.8

    is_suspicious = wide_by_ratio or wide_by_digits

    return is_suspicious, dict(
        sym_w=sw, sym_h=sh,
        sym_ratio=sym_ratio,
        avg_digit_w=avg_digit_w,
        sym_vs_digit=sym_vs_digit,
        wide_by_ratio=wide_by_ratio,
        wide_by_digits=wide_by_digits,
    )


def compute_verdict(stats, symbol_check=None):
    """Compute a weighted fraud score from inconsistency statistics.

    Args:
        stats: Dict from analyze_inconsistencies.
        symbol_check: Optional (is_suspicious, details) tuple from
            check_symbol_width.

    Returns:
        (verdict_string, score, reasons_list)
    """
    score = 0
    reasons = []

    if symbol_check and symbol_check[0]:
        det = symbol_check[1]
        contrib = 0
        sub = []
        if det["wide_by_ratio"]:
            contrib += WEIGHT_SYMBOL_RATIO
            sub.append(f"w/h={det['sym_ratio']:.3f}>1.3 (+{WEIGHT_SYMBOL_RATIO} pts)")
        if det["wide_by_digits"]:
            contrib += WEIGHT_SYMBOL_WIDE
            sub.append(f"sym/digit={det['sym_vs_digit']:.2f}>1.8 (+{WEIGHT_SYMBOL_WIDE} pts)")
        score += contrib
        reasons.append(
            f"P SYMBOL TOO WIDE — digit likely merged in: {', '.join(sub)}"
        )
    elif symbol_check:
        det = symbol_check[1]
        reasons.append(
            f"P symbol width normal (w/h={det['sym_ratio']:.3f})"
        )

    if not stats:
        reasons.append("Too few digit boxes to analyse further.")
        verdict = "FAIL: FAKE" if score >= FAKE_THRESHOLD else "PASS: REAL"
        return verdict, score, reasons

    h_std_contrib = stats["h_std"] * WEIGHT_HEIGHT_STD
    score += h_std_contrib
    reasons.append(f"Height std = {stats['h_std']:.2f}px (+{h_std_contrib:.0f} pts)")

    y_std_contrib = stats["y_std"] * WEIGHT_Y_STD
    score += y_std_contrib
    reasons.append(f"Y std = {stats['y_std']:.2f}px (+{y_std_contrib:.0f} pts)")

    r_std_contrib = stats["r_std"] * WEIGHT_RATIO_STD
    score += r_std_contrib
    reasons.append(f"Ratio std = {stats['r_std']:.3f} (+{r_std_contrib:.0f} pts)")

    score += np.sum(stats["height_flags"]) * WEIGHT_HEIGHT_OUTLIER
    score += np.sum(stats["ratio_flags"]) * WEIGHT_RATIO_OUTLIER
    score += np.sum(stats["gap_flags"]) * WEIGHT_GAP_OUTLIER
    score += np.sum(stats["y_flags"]) * WEIGHT_Y_OUTLIER

    if stats.get("monotonic_drift"):
        score += 20

    verdict = "FAIL: FAKE" if score >= FAKE_THRESHOLD else "PASS: REAL"
    return verdict, score, reasons


def analyze_amount_typography(image, output_path=None):
    """Run amount-field-specific typography forensics.

    Designed for cropped amount fields from GCash receipts. Assumes the
    first character is the ₱ currency symbol and the rest are digits.
    Uses weighted multi-dimensional scoring for higher accuracy than the
    general-purpose analyze_typography.

    Args:
        image: File path (str) or in-memory BGR numpy array.
        output_path: Optional path to save the annotated proof image.

    Returns:
        dict with keys: verdict, score, reasons, stats, symbol_check, proof_image.
    """
    if isinstance(image, str):
        img = cv2.imread(image)
        if img is None:
            raise ValueError(f"Could not read image: {image}")
    else:
        img = image.copy()

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    bounding_boxes = sorted(
        [(x, y, w, h) for c in contours
         for x, y, w, h in [cv2.boundingRect(c)] if h > 15 and w > 5],
        key=lambda b: b[0]
    )

    if not bounding_boxes:
        # Fallback: try tree contours with looser size thresholds.
        # The ₱ symbol can fragment into inner contours that RETR_EXTERNAL
        # discards, even after morphological closing.
        tree_contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        bounding_boxes = sorted(
            [(x, y, w, h) for c in tree_contours
             for x, y, w, h in [cv2.boundingRect(c)] if h > 8 and w > 3],
            key=lambda b: b[0]
        )

    if not bounding_boxes:
        return {
            'verdict': 'INCONCLUSIVE',
            'score': 0,
            'reasons': ['No characters detected in amount field'],
            'stats': {},
            'symbol_check': None,
            'proof_image': img,
        }

    currency_box = bounding_boxes[0]
    digit_boxes = bounding_boxes[1:]

    symbol_check = check_symbol_width(currency_box, digit_boxes)
    stats = analyze_inconsistencies(digit_boxes)
    verdict, score, reasons = compute_verdict(stats, symbol_check=symbol_check)

    proof_img = img.copy()

    for x, y, w, h in bounding_boxes:
        cv2.rectangle(proof_img, (x, y), (x + w, y + h), (255, 0, 0), 1)

    color = (0, 0, 255) if "FAIL" in verdict else (0, 255, 0)
    font_scale = max(0.35, img.shape[0] / 120)
    cv2.putText(proof_img, f"{verdict} (score: {score:.0f})",
                (5, max(20, int(img.shape[0] * 0.9))),
                cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 2)

    if output_path:
        cv2.imwrite(str(output_path), proof_img)

    return {
        'verdict': verdict,
        'score': score,
        'reasons': reasons,
        'stats': {k: v.tolist() if isinstance(v, np.ndarray) else v
                  for k, v in stats.items()},
        'symbol_check': symbol_check[1] if symbol_check else None,
        'proof_image': proof_img,
    }


def analyze_digit_typography(image, output_path=None):
    """Run typography forensics on a digit-only field (no currency symbol).

    Designed for cropped reference numbers, phone numbers, and other
    digit-string fields from GCash receipts. Uses the same statistical
    inconsistency engine as analyze_amount_typography but treats all
    characters as digits without a symbol-width check.

    Args:
        image: File path (str) or in-memory BGR numpy array.
        output_path: Optional path to save the annotated proof image.

    Returns:
        dict with keys: verdict, score, reasons, stats, proof_image.
    """
    if isinstance(image, str):
        img = cv2.imread(image)
        if img is None:
            raise ValueError(f"Could not read image: {image}")
    else:
        img = image.copy()

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    bounding_boxes = sorted(
        [(x, y, w, h) for c in contours
         for x, y, w, h in [cv2.boundingRect(c)] if h > 15 and w > 5],
        key=lambda b: b[0]
    )

    if not bounding_boxes:
        tree_contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        bounding_boxes = sorted(
            [(x, y, w, h) for c in tree_contours
             for x, y, w, h in [cv2.boundingRect(c)] if h > 8 and w > 3],
            key=lambda b: b[0]
        )

    if not bounding_boxes:
        return {
            'verdict': 'INCONCLUSIVE',
            'score': 0,
            'reasons': ['Too few characters detected in field'],
            'stats': {},
            'proof_image': img,
        }

    stats = analyze_inconsistencies(bounding_boxes)
    verdict, score, reasons = compute_verdict(stats, symbol_check=None)

    proof_img = img.copy()

    for x, y, w, h in bounding_boxes:
        cv2.rectangle(proof_img, (x, y), (x + w, y + h), (255, 0, 0), 1)

    color = (0, 0, 255) if "FAIL" in verdict else (0, 255, 0)
    font_scale = max(0.35, img.shape[0] / 120)
    cv2.putText(proof_img, f"{verdict} (score: {score:.0f})",
                (5, max(20, int(img.shape[0] * 0.9))),
                cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 2)

    if output_path:
        cv2.imwrite(str(output_path), proof_img)

    return {
        'verdict': verdict,
        'score': score,
        'reasons': reasons,
        'stats': {k: v.tolist() if isinstance(v, np.ndarray) else v
                  for k, v in stats.items()},
        'proof_image': proof_img,
    }


def analyze_reference_number(image, output_path=None):
    """Check a reference-number crop for editing via digit consistency.

    Designed for GCash reference numbers which appear in two formats:
      - Continuous:  "0040027019913" (single line, 13 digits, kerning 1-3 px)
      - Spaced:      "1039 879 183868" (groups separated by spaces, may be
                      multi-line on narrow receipt panels)

    Thresholds are calibrated from 9 real GCash receipts:
      - Baseline: 0 px deviation on single-line ref#s (pixel-perfect render)
      - Height:   ≤ 6 % deviation from median
      - Width:    ≤ 43 % deviation (digit '1' is narrow, '8' is wide)
      - Kerning:  1-3 px between digits in a group

    Requires multiple independent indicators before flagging FORGED.

    Args:
        image: File path (str) or in-memory BGR numpy array.
        output_path: Optional path to save the annotated proof image.

    Returns:
        dict with keys: verdict, score, reasons, proof_image.
    """
    if isinstance(image, str):
        img = cv2.imread(image)
        if img is None:
            raise ValueError(f"Could not read image: {image}")
    else:
        img = image.copy()

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = sorted(
        [(x, y, w, h) for c in contours
         for x, y, w, h in [cv2.boundingRect(c)] if h > 8 and w > 3],
        key=lambda b: b[0]
    )

    proof_img = img.copy()

    if len(boxes) < 4:
        return {
            'verdict': 'INCONCLUSIVE',
            'score': 0,
            'reasons': ['Too few characters detected in reference number'],
            'proof_image': proof_img,
        }

    heights = np.array([b[3] for b in boxes], dtype=float)
    widths = np.array([b[2] for b in boxes], dtype=float)
    baselines = np.array([b[1] + b[3] for b in boxes], dtype=float)

    gaps = np.array([
        boxes[i + 1][0] - (boxes[i][0] + boxes[i][2])
        for i in range(len(boxes) - 1)
    ], dtype=float)

    median_h = np.median(heights)
    median_w = np.median(widths)

    # Detect multi-line layout: if baseline range exceeds median height,
    # digits are split across rows. Split and check each row independently.
    base_range = float(np.max(baselines) - np.min(baselines))
    multi_line = base_range > median_h * 0.8 and len(boxes) >= 6

    if multi_line:
        return _check_ref_rows(boxes, proof_img, median_h, output_path)

    # --- Single-line reference number ---
    return _check_ref_single_row(
        boxes, heights, widths, baselines, gaps,
        median_h, median_w, proof_img, output_path,
    )


def _check_ref_rows(boxes, proof_img, median_h, output_path):
    """Check a multi-line reference number by splitting into rows."""
    # Cluster by baseline proximity
    baselines = np.array([b[1] + b[3] for b in boxes], dtype=float)
    rows = []
    used = set()

    for i in range(len(boxes)):
        if i in used:
            continue
        bi = baselines[i]
        row = [boxes[i]]
        used.add(i)
        for j in range(i + 1, len(boxes)):
            if j in used:
                continue
            if abs(baselines[j] - bi) < median_h * 0.6:
                row.append(boxes[j])
                used.add(j)
        row = sorted(row, key=lambda b: b[0])
        if len(row) >= 2:
            rows.append(row)

    if not rows:
        return {
            'verdict': 'INCONCLUSIVE',
            'score': 0,
            'reasons': ['Could not parse multi-line reference number rows'],
            'proof_image': proof_img,
        }

    total_flags = 0
    all_reasons = []

    for row_idx, row_boxes in enumerate(rows):
        row_heights = np.array([b[3] for b in row_boxes], dtype=float)
        row_widths = np.array([b[2] for b in row_boxes], dtype=float)
        row_bases = np.array([b[1] + b[3] for b in row_boxes], dtype=float)
        row_gaps = np.array([
            row_boxes[i + 1][0] - (row_boxes[i][0] + row_boxes[i][2])
            for i in range(len(row_boxes) - 1)
        ], dtype=float)

        median_h_row = np.median(row_heights)
        median_w_row = np.median(row_widths)

        result = _check_ref_single_row(
            row_boxes, row_heights, row_widths, row_bases, row_gaps,
            median_h_row, median_w_row, proof_img, None,
        )
        total_flags += result['score']
        all_reasons.extend(f"Row {row_idx + 1}: {r}" for r in result['reasons'])

        # Draw row separator
        top = min(b[1] for b in row_boxes)
        bottom = max(b[1] + b[3] for b in row_boxes)
        cv2.line(proof_img, (row_boxes[0][0] - 3, top - 2),
                 (row_boxes[-1][0] + row_boxes[-1][2] + 3, top - 2),
                 (255, 255, 0), 1)

    verdict = "FAIL: FAKE" if total_flags >= 2 else "PASS: REAL"
    color = (0, 0, 255) if "FAIL" in verdict else (0, 255, 0)
    font_scale = max(0.35, proof_img.shape[0] / 120)
    cv2.putText(proof_img, f"Ref#: {verdict} ({total_flags}f/{len(rows)}r)",
                (5, max(20, int(proof_img.shape[0] * 0.9))),
                cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 2)

    if output_path:
        cv2.imwrite(str(output_path), proof_img)

    return {
        'verdict': verdict,
        'score': total_flags,
        'reasons': all_reasons,
        'proof_image': proof_img,
    }


def _check_ref_single_row(boxes, heights, widths, baselines, gaps,
                          median_h, median_w, proof_img, output_path):
    """Core single-row reference number check with calibrated thresholds."""
    flags = 0
    reasons = []

    median_base = np.median(baselines)

    # --- Baseline (calibrated: real ref#s have 0 px deviation) ---
    base_devs = np.abs(baselines - median_base)
    base_outliers = np.where(base_devs > 1.0)[0]
    extreme_base = np.any(base_devs > 2.5)

    if extreme_base:
        flags += 2
        worst = int(np.argmax(base_devs))
        reasons.append(
            f"Char {worst + 1}: baseline shifted {base_devs[worst]:.1f}px "
            f"— severe misalignment"
        )
    elif len(base_outliers) > 0:
        flags += 1
        reasons.append(
            f"Baseline drift: {len(base_outliers)} char(s) off "
            f"by >1px from median"
        )

    # Baseline line on proof
    base_y = int(median_base)
    cv2.line(proof_img, (boxes[0][0] - 3, base_y),
             (boxes[-1][0] + boxes[-1][2] + 3, base_y), (0, 255, 255), 1)

    # --- Height (calibrated: ≤ 6 %, threshold at 15 %) ---
    h_devs = np.abs(heights - median_h) / max(median_h, 1)
    h_outliers = np.where(h_devs > 0.15)[0]
    if len(h_outliers) > 0:
        flags += 1
        reasons.append(
            f"Height anomaly: {len(h_outliers)} char(s) deviate "
            f">15% from median ({median_h:.0f}px)"
        )

    # --- Width (calibrated: ≤ 43 %, threshold at 50 %) ---
    w_devs = np.abs(widths - median_w) / max(median_w, 1)
    w_outliers = np.where(w_devs > 0.50)[0]
    if len(w_outliers) > 0:
        flags += 1
        reasons.append(
            f"Width anomaly: {len(w_outliers)} char(s) deviate "
            f">50% from median ({median_w:.0f}px)"
        )

    # --- Kerning: separate structural gaps (spaces between groups) ---
    # Structural = gap > 5× median kerning gap (≈ 10 px vs typical 2 px)
    if len(gaps) > 0:
        kerning_mask = np.ones(len(gaps), dtype=bool)
        if len(gaps) >= 2:
            # Find the typical kerning gap (most gaps are 1-3 px)
            small_gaps = gaps[gaps < np.median(gaps) * 3.0]
            if len(small_gaps) > 0:
                typical_kerning = float(np.median(small_gaps))
                kerning_mask = gaps <= typical_kerning * 5.0

        kerning_gaps = gaps[kerning_mask]
        if len(kerning_gaps) > 0:
            median_kerning = float(np.median(kerning_gaps))
            kerning_devs = np.abs(kerning_gaps - median_kerning)
            # Flag outliers > 4 px from median (calibrated: kerning range is 1-3 px)
            bad_kerning = np.where(kerning_devs > 4.0)[0]
            if len(bad_kerning) > 0:
                flags += 1
                reasons.append(
                    f"Irregular spacing in {len(bad_kerning)} gap(s) "
                    f"(expected ~{median_kerning:.0f}px)"
                )

    # --- Draw boxes ---
    outlier_indices = set(base_outliers) | set(h_outliers) | set(w_outliers)
    for i, (x, y, w, h) in enumerate(boxes):
        color = (0, 0, 255) if i in outlier_indices else (0, 255, 0)
        cv2.rectangle(proof_img, (x, y), (x + w, y + h), color, 1)

    # --- Verdict ---
    verdict = "FAIL: FAKE" if flags >= 2 else "PASS: REAL"

    color = (0, 0, 255) if "FAIL" in verdict else (0, 255, 0)
    font_scale = max(0.35, proof_img.shape[0] / 120)
    cv2.putText(proof_img, f"Ref#: {verdict} ({flags}f)",
                (5, max(20, int(proof_img.shape[0] * 0.9))),
                cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 2)

    if output_path:
        cv2.imwrite(str(output_path), proof_img)

    return {
        'verdict': verdict,
        'score': flags,
        'reasons': reasons,
        'proof_image': proof_img,
    }


def analyze_date(image, output_path=None):
    """Check a date-field crop for editing.

    Designed for GCash date stamps in the format:
        "Mon DD, YYYY H:MM AM"  (e.g. "Apr 21, 2026 11:24 PM")

    Dates are mixed-content — letters, digits, punctuation — so natural
    variance is higher than pure-digit fields. Calibrated from 9 real
    receipts:
      - Baseline: ≤ 4 px deviation (comma sits higher, descenders vary)
      - Height:   ≤ 30 % within non-punctuation characters
      - Width:    ≤ 70 % (letters vary more than digits)
      - Spaces:   6-11 px between date components

    Punctuation (comma, colon) is excluded from baseline/height checks
    since it is naturally much smaller than letters and digits.
    """
    if isinstance(image, str):
        img = cv2.imread(image)
        if img is None:
            raise ValueError(f"Could not read image: {image}")
    else:
        img = image.copy()

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = sorted(
        [(x, y, w, h) for c in contours
         for x, y, w, h in [cv2.boundingRect(c)] if h > 4 and w > 2],
        key=lambda b: b[0]
    )

    proof_img = img.copy()

    if len(boxes) < 6:
        return {
            'verdict': 'INCONCLUSIVE',
            'score': 0,
            'reasons': ['Too few characters in date field'],
            'proof_image': proof_img,
        }

    heights = np.array([b[3] for b in boxes], dtype=float)
    widths = np.array([b[2] for b in boxes], dtype=float)
    baselines = np.array([b[1] + b[3] for b in boxes], dtype=float)

    median_h = np.median(heights)

    # Separate punctuation (comma, colon — much shorter than letters/digits)
    is_punct = heights < median_h * 0.5
    is_char = ~is_punct

    char_indices = np.where(is_char)[0]
    punct_indices = np.where(is_punct)[0]

    if len(char_indices) < 4:
        return {
            'verdict': 'INCONCLUSIVE',
            'score': 0,
            'reasons': ['Too few non-punctuation characters in date'],
            'proof_image': proof_img,
        }

    char_heights = heights[char_indices]
    char_widths = widths[char_indices]
    char_bases = baselines[char_indices]
    median_char_h = np.median(char_heights)
    median_char_w = np.median(char_widths)

    # Multi-line detection on character boxes only
    base_range = float(np.max(char_bases) - np.min(char_bases))
    multi_line = base_range > median_char_h * 0.8 and len(char_indices) >= 8

    if multi_line:
        return _check_date_rows(
            boxes, char_indices, punct_indices, proof_img, median_char_h, output_path
        )

    return _check_date_single_row(
        boxes, char_indices, punct_indices, char_heights, char_widths,
        char_bases, median_char_h, median_char_w, proof_img, output_path,
    )


def _check_date_rows(boxes, char_indices, punct_indices, proof_img,
                     median_h, output_path):
    """Check a multi-line date by splitting into rows."""
    char_bases = np.array([boxes[i][1] + boxes[i][3] for i in char_indices], dtype=float)

    rows = []
    used = set()
    for idx_i, i in enumerate(char_indices):
        if i in used:
            continue
        bi = char_bases[idx_i]
        row_chars = [i]
        row_punct = []
        used.add(i)
        for idx_j, j in enumerate(char_indices):
            if j in used:
                continue
            if abs(char_bases[idx_j] - bi) < median_h * 0.6:
                row_chars.append(j)
                used.add(j)
        for p in punct_indices:
            if p in used:
                continue
            p_base = boxes[p][1] + boxes[p][3]
            if abs(p_base - bi) < median_h * 0.8:
                row_punct.append(p)
                used.add(p)
        row_chars = sorted(row_chars)
        if len(row_chars) >= 2:
            rows.append((row_chars, row_punct))

    if not rows:
        return {
            'verdict': 'INCONCLUSIVE',
            'score': 0,
            'reasons': ['Could not parse multi-line date rows'],
            'proof_image': proof_img,
        }

    total_flags = 0
    all_reasons = []
    for row_idx, (row_chars, row_punct) in enumerate(rows):
        row_heights = np.array([boxes[i][3] for i in row_chars], dtype=float)
        row_widths = np.array([boxes[i][2] for i in row_chars], dtype=float)
        row_bases = np.array([boxes[i][1] + boxes[i][3] for i in row_chars], dtype=float)
        result = _check_date_single_row(
            boxes, row_chars, row_punct, row_heights, row_widths,
            row_bases, np.median(row_heights), np.median(row_widths),
            proof_img, None,
        )
        total_flags += result['score']
        all_reasons.extend(f"Row {row_idx + 1}: {r}" for r in result['reasons'])

    verdict = "FAIL: FAKE" if total_flags >= 2 else "PASS: REAL"
    color = (0, 0, 255) if "FAIL" in verdict else (0, 255, 0)
    fs = max(0.35, proof_img.shape[0] / 120)
    cv2.putText(proof_img, f"Date: {verdict} ({total_flags}f/{len(rows)}r)",
                (5, max(20, int(proof_img.shape[0] * 0.9))),
                cv2.FONT_HERSHEY_SIMPLEX, fs, color, 2)
    if output_path:
        cv2.imwrite(str(output_path), proof_img)
    return {
        'verdict': verdict,
        'score': total_flags,
        'reasons': all_reasons,
        'proof_image': proof_img,
    }


def _check_date_single_row(boxes, char_indices, punct_indices, char_heights,
                           char_widths, char_bases, median_h, median_w,
                           proof_img, output_path):
    """Core single-row date check with calibrated thresholds."""
    flags = 0
    reasons = []

    # --- Baseline (calibrated: real dates have ≤ 4 px deviation) ---
    median_base = np.median(char_bases)
    base_devs = np.abs(char_bases - median_base)
    base_outliers_local = np.where(base_devs > 5.0)[0]

    if len(base_outliers_local) > 0:
        flags += 1
        devs = base_devs[base_outliers_local]
        reasons.append(
            f"Date baseline shift: {len(base_outliers_local)} char(s) "
            f"off by up to {devs.max():.0f}px from row median"
        )

    # Baseline line
    base_y = int(median_base)
    all_xs = [boxes[i][0] for i in char_indices] + [boxes[i][0] + boxes[i][2] for i in char_indices]
    cv2.line(proof_img, (min(all_xs) - 3, base_y),
             (max(all_xs) + 3, base_y), (0, 255, 255), 1)

    # --- Height (calibrated: ≤ 30 % for chars, threshold at 35 %) ---
    h_devs = np.abs(char_heights - median_h) / max(median_h, 1)
    h_outliers_local = np.where(h_devs > 0.35)[0]
    if len(h_outliers_local) > 0:
        flags += 1
        reasons.append(
            f"Date height anomaly: {len(h_outliers_local)} char(s) "
            f">35% from median ({median_h:.0f}px)"
        )

    # --- Width (calibrated: ≤ 70 %, flag at 75 %) ---
    w_devs = np.abs(char_widths - median_w) / max(median_w, 1)
    w_outliers_local = np.where(w_devs > 0.75)[0]
    if len(w_outliers_local) > 0:
        flags += 1
        reasons.append(
            f"Date width anomaly: {len(w_outliers_local)} char(s) "
            f">75% from median ({median_w:.0f}px)"
        )

    # --- Spacing: flag only extreme gaps ---
    all_indices = sorted(list(char_indices) + list(punct_indices))
    if len(all_indices) >= 2:
        gaps = []
        gap_pairs = []
        for k in range(len(all_indices) - 1):
            a, b = all_indices[k], all_indices[k + 1]
            gap = boxes[b][0] - (boxes[a][0] + boxes[a][2])
            gaps.append(gap)
            gap_pairs.append((a, b))

        gaps = np.array(gaps)
        # Spaces between components are 6-11 px on real receipts.
        # Flag negative gaps (overlapping boxes) or gaps > 20 px.
        bad = np.where((gaps < -2) | (gaps > 20))[0]
        if len(bad) > 0:
            flags += 1
            details = ", ".join(
                f"{gap_pairs[i][0]}-{gap_pairs[i][1]} ({gaps[i]:.0f}px)"
                for i in bad
            )
            reasons.append(f"Date irregular spacing: {details}")

    # --- Draw boxes ---
    outlier_set = set()
    for idx in base_outliers_local:
        outlier_set.add(char_indices[idx])
    for idx in h_outliers_local:
        outlier_set.add(char_indices[idx])
    for idx in w_outliers_local:
        outlier_set.add(char_indices[idx])

    for i, (x, y, w, h) in enumerate(boxes):
        if i in punct_indices:
            color = (255, 255, 0)
        elif i in outlier_set:
            color = (0, 0, 255)
        else:
            color = (0, 255, 0)
        cv2.rectangle(proof_img, (x, y), (x + w, y + h), color, 1)

    # --- Verdict ---
    verdict = "FAIL: FAKE" if flags >= 2 else "PASS: REAL"

    color = (0, 0, 255) if "FAIL" in verdict else (0, 255, 0)
    fs = max(0.35, proof_img.shape[0] / 120)
    cv2.putText(proof_img, f"Date: {verdict} ({flags}f)",
                (5, max(20, int(proof_img.shape[0] * 0.9))),
                cv2.FONT_HERSHEY_SIMPLEX, fs, color, 2)

    if output_path:
        cv2.imwrite(str(output_path), proof_img)

    return {
        'verdict': verdict,
        'score': flags,
        'reasons': reasons,
        'proof_image': proof_img,
    }


def analyze_phone_number(image, output_path=None):
    """Check a phone-number crop for editing.

    Designed for GCash phone numbers in two formats:
      - Full:    "+63 926 699 2655" (13 chars, 3 group spaces)
      - Masked:  "+63 9** *** 7556" (bullets replace middle digits)

    Calibrated from 9 real receipts:
      - + sign:   wider aspect ratio, slightly lower baseline
      - Digits:   18-25 px tall, baseline ≤ 1 px deviation
      - Bullets:  9x9 px (38 % of digit height), lower baseline
      - Kerning:  1-3 px within a digit group
      - Spaces:   11-14 px between groups (3 groups after +63)

    Bullets and the + sign are excluded from digit consistency checks.
    Group-separator spaces are recognized and not flagged.
    """
    if isinstance(image, str):
        img = cv2.imread(image)
        if img is None:
            raise ValueError(f"Could not read image: {image}")
    else:
        img = image.copy()

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = sorted(
        [(x, y, w, h) for c in contours
         for x, y, w, h in [cv2.boundingRect(c)] if h > 4 and w > 2],
        key=lambda b: b[0]
    )

    proof_img = img.copy()

    if len(boxes) < 6:
        return {
            'verdict': 'INCONCLUSIVE',
            'score': 0,
            'reasons': ['Too few characters in phone number'],
            'proof_image': proof_img,
        }

    heights = np.array([b[3] for b in boxes], dtype=float)
    widths = np.array([b[2] for b in boxes], dtype=float)
    baselines = np.array([b[1] + b[3] for b in boxes], dtype=float)

    median_h = np.median(heights)

    # Bullets: < 50 % of median height (9 px vs 24 px digits)
    is_bullet = heights < median_h * 0.50
    # + sign: first 1-2 boxes, wider than tall (w/h > 0.85)
    is_plus = np.zeros(len(boxes), dtype=bool)
    for i in range(min(2, len(boxes))):
        if widths[i] > heights[i] * 0.85:
            is_plus[i] = True
    is_digit = ~(is_bullet | is_plus)

    digit_indices = np.where(is_digit)[0]
    bullet_indices = np.where(is_bullet)[0]

    if len(digit_indices) < 3:
        return {
            'verdict': 'INCONCLUSIVE',
            'score': 0,
            'reasons': ['Too few visible digits in phone number'],
            'proof_image': proof_img,
        }

    digit_heights = heights[digit_indices]
    digit_widths = widths[digit_indices]
    digit_bases = baselines[digit_indices]
    median_digit_h = np.median(digit_heights)
    median_digit_w = np.median(digit_widths)

    flags = 0
    reasons = []

    # Baseline (calibrated: digits ≤ 1 px deviation)
    median_digit_base = np.median(digit_bases)
    base_devs = np.abs(digit_bases - median_digit_base)
    base_outliers = np.where(base_devs > 1.5)[0]
    extreme_base = np.any(base_devs > 3.0)

    if extreme_base:
        flags += 2
        worst = int(np.argmax(base_devs))
        reasons.append(
            f"Phone digit {worst + 1}: baseline shifted "
            f"{base_devs[worst]:.1f}px — severe misalignment"
        )
    elif len(base_outliers) > 0:
        flags += 1
        reasons.append(
            f"Phone baseline drift: {len(base_outliers)} digit(s) "
            f"off by >1.5px from median"
        )

    base_y = int(median_digit_base)
    all_digit_xs = [boxes[i][0] for i in digit_indices] + \
                   [boxes[i][0] + boxes[i][2] for i in digit_indices]
    cv2.line(proof_img, (min(all_digit_xs) - 3, base_y),
             (max(all_digit_xs) + 3, base_y), (0, 255, 255), 1)

    # Height (calibrated: ≤ 30 %)
    h_devs = np.abs(digit_heights - median_digit_h) / max(median_digit_h, 1)
    h_outliers = np.where(h_devs > 0.30)[0]
    if len(h_outliers) > 0:
        flags += 1
        reasons.append(
            f"Phone height anomaly: {len(h_outliers)} digit(s) "
            f">30% from median ({median_digit_h:.0f}px)"
        )

    # Width (calibrated: ≤ 42 %, threshold at 45 %)
    w_devs = np.abs(digit_widths - median_digit_w) / max(median_digit_w, 1)
    w_outliers = np.where(w_devs > 0.45)[0]
    if len(w_outliers) > 0:
        flags += 1
        reasons.append(
            f"Phone width anomaly: {len(w_outliers)} digit(s) "
            f">45% from median ({median_digit_w:.0f}px)"
        )

    # Kerning: detect group structure
    all_indices = sorted(list(digit_indices) + list(bullet_indices) +
                         list(np.where(is_plus)[0]))
    if len(all_indices) >= 2:
        gaps = np.array([
            boxes[all_indices[k + 1]][0] -
            (boxes[all_indices[k]][0] + boxes[all_indices[k]][2])
            for k in range(len(all_indices) - 1)
        ], dtype=float)

        small_gaps = gaps[gaps < median_digit_w * 0.5]
        typical_kerning = float(np.median(small_gaps)) if len(small_gaps) > 0 else 2.0

        kerning_mask = gaps <= typical_kerning * 5.0
        kerning_gaps = gaps[kerning_mask]

        if len(kerning_gaps) > 0:
            med_kerning = float(np.median(kerning_gaps))
            bad_kerning = np.where(np.abs(kerning_gaps - med_kerning) > 4.0)[0]
            if len(bad_kerning) > 0:
                flags += 1
                reasons.append(
                    f"Phone irregular spacing: {len(bad_kerning)} gap(s) "
                    f"deviate from ~{med_kerning:.0f}px kerning"
                )

    # Draw boxes
    outlier_digit_set = set()
    for idx in base_outliers:
        outlier_digit_set.add(digit_indices[idx])
    for idx in h_outliers:
        outlier_digit_set.add(digit_indices[idx])
    for idx in w_outliers:
        outlier_digit_set.add(digit_indices[idx])

    for i, (x, y, w, h) in enumerate(boxes):
        if i in bullet_indices:
            color = (255, 200, 0)
        elif is_plus[i]:
            color = (255, 255, 0)
        elif i in outlier_digit_set:
            color = (0, 0, 255)
        else:
            color = (0, 255, 0)
        cv2.rectangle(proof_img, (x, y), (x + w, y + h), color, 1)

    verdict = "FAIL: FAKE" if flags >= 2 else "PASS: REAL"
    has_bullets = "masked" if len(bullet_indices) > 0 else "full"
    color = (0, 0, 255) if "FAIL" in verdict else (0, 255, 0)
    fs = max(0.35, proof_img.shape[0] / 120)
    cv2.putText(proof_img, f"Phone({has_bullets}): {verdict} ({flags}f)",
                (5, max(20, int(proof_img.shape[0] * 0.9))),
                cv2.FONT_HERSHEY_SIMPLEX, fs, color, 2)

    if output_path:
        cv2.imwrite(str(output_path), proof_img)

    return {
        'verdict': verdict,
        'score': flags,
        'reasons': reasons,
        'proof_image': proof_img,
    }


def analyze_name(image, output_path=None):
    """Check a name-field crop for editing.

    Designed for GCash masked names in the format:
        "JO*N CE**R A"  or  "F**Z CH****D G."

    Names use bullets to mask most characters — typically only the
    first name is partially visible and the last name is an initial.
    Calibrated from 9 real receipts.

    Key characteristics:
      - Large letters: 29-37 px tall (visible capital letters)
      - Bullets:       ~10 px (masked characters, consistent per receipt)
      - Periods:       ~7 px (after initials)
      - Word spaces:   14-21 px between first/middle/last name parts
      - Kerning:       1-6 px within a word

    Only large visible letters are checked. Bullets and periods are
    excluded — they are generated by the GCash app for masking.
    """
    if isinstance(image, str):
        img = cv2.imread(image)
        if img is None:
            raise ValueError(f"Could not read image: {image}")
    else:
        img = image.copy()

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = sorted(
        [(x, y, w, h) for c in contours
         for x, y, w, h in [cv2.boundingRect(c)] if h > 3 and w > 2],
        key=lambda b: b[0]
    )

    if len(boxes) < 4:
        tree_contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        boxes = sorted(
            [(x, y, w, h) for c in tree_contours
             for x, y, w, h in [cv2.boundingRect(c)] if h > 2 and w > 1],
            key=lambda b: b[0]
        )

    proof_img = img.copy()

    if len(boxes) < 4:
        return {
            'verdict': 'INCONCLUSIVE',
            'score': 0,
            'reasons': ['Too few characters in name field'],
            'proof_image': proof_img,
        }

    heights = np.array([b[3] for b in boxes], dtype=float)
    widths = np.array([b[2] for b in boxes], dtype=float)
    baselines = np.array([b[1] + b[3] for b in boxes], dtype=float)

    # --- Natural-break clustering on heights ---
    # Letters are ~29-37 px, bullets ~10 px, periods ~7 px.
    # The largest gap between sorted heights splits letters from non-letters.
    # A second gap (among the non-letter heights) splits bullets from periods.
    sorted_h = np.sort(heights)
    gaps = np.diff(sorted_h)

    if len(gaps) >= 1 and np.max(gaps) >= 4:
        split1 = int(np.argmax(gaps))
        letter_cutoff = sorted_h[split1] + gaps[split1] / 2

        below = gaps[:split1]
        if len(below) >= 1 and np.max(below) >= 1.5:
            split2 = int(np.argmax(below))
            bullet_cutoff = sorted_h[split2] + below[split2] / 2
        else:
            bullet_cutoff = letter_cutoff * 0.45

        is_letter_h = heights >= letter_cutoff
        is_bullet_h = (heights >= bullet_cutoff) & ~is_letter_h
        is_period_h = heights < bullet_cutoff
    else:
        # No clear break — all contours are likely the same class
        is_letter_h = np.ones(len(heights), dtype=bool)
        is_bullet_h = np.zeros(len(heights), dtype=bool)
        is_period_h = np.zeros(len(heights), dtype=bool)

    # --- Aspect-ratio refinement ---
    # Capital letters are taller than wide (w/h < 1.0). Bullets are round
    # (w/h ≈ 1.0). A noise blob with tall height but square ratio gets
    # reclassified as a bullet so it doesn't skew the letter statistics.
    ratios = widths / np.maximum(heights, 1)
    letter_ratio_ok = ratios < 1.0

    is_letter = is_letter_h & letter_ratio_ok
    is_bullet = is_bullet_h | (is_letter_h & ~letter_ratio_ok)
    is_period = is_period_h

    # Reverse check: bullets with letter-like aspect ratio (w/h < 0.85)
    # are suspicious — could be pasted text that fell into the bullet cluster.
    bullet_ratios = ratios
    bullet_looks_like_letter = is_bullet & (bullet_ratios < 0.85)

    letter_indices = np.where(is_letter)[0]
    bullet_indices = np.where(is_bullet)[0]
    period_indices = np.where(is_period)[0]
    suspicious_bullet_indices = np.where(bullet_looks_like_letter)[0]

    if len(letter_indices) < 2:
        return {
            'verdict': 'INCONCLUSIVE',
            'score': 0,
            'reasons': ['Too few visible letters in name'],
            'proof_image': proof_img,
        }

    letter_heights = heights[letter_indices]
    letter_widths = widths[letter_indices]
    letter_bases = baselines[letter_indices]
    median_letter_h = np.median(letter_heights)
    median_letter_w = np.median(letter_widths)

    flags = 0
    reasons = []

    # --- Suspicious bullets ---
    # Bullets with letter-like aspect ratio may be pasted text that fell
    # into the wrong height cluster.
    if len(suspicious_bullet_indices) > 0:
        flags += 1
        reasons.append(
            f"Name suspicious masking: {len(suspicious_bullet_indices)} "
            f"bullet(s) with letter-like proportions"
        )

    # --- Baseline (calibrated: within-word ≤ 3 px, across-word ≤ 6 px) ---
    median_letter_base = np.median(letter_bases)
    base_devs = np.abs(letter_bases - median_letter_base)
    base_outliers = np.where(base_devs > 3.0)[0]
    extreme_base = np.any(base_devs > 6.0)

    if extreme_base:
        flags += 2
        worst = int(np.argmax(base_devs))
        reasons.append(
            f"Name baseline shift: letter off by "
            f"{base_devs[worst]:.0f}px — severe misalignment"
        )
    elif len(base_outliers) > 0:
        flags += 1
        reasons.append(
            f"Name baseline drift: {len(base_outliers)} letter(s) "
            f"off by >3px from median"
        )

    base_y = int(median_letter_base)
    all_letter_xs = [boxes[i][0] for i in letter_indices] + \
                    [boxes[i][0] + boxes[i][2] for i in letter_indices]
    cv2.line(proof_img, (min(all_letter_xs) - 3, base_y),
             (max(all_letter_xs) + 3, base_y), (0, 255, 255), 1)

    # --- Height (calibrated: large letters within 20 % of median) ---
    h_devs = np.abs(letter_heights - median_letter_h) / max(median_letter_h, 1)
    h_outliers = np.where(h_devs > 0.20)[0]
    if len(h_outliers) > 0:
        flags += 1
        reasons.append(
            f"Name height anomaly: {len(h_outliers)} letter(s) "
            f">20% from median ({median_letter_h:.0f}px)"
        )

    # --- Width (calibrated: letters vary up to 70 %, threshold at 75 %) ---
    w_devs = np.abs(letter_widths - median_letter_w) / max(median_letter_w, 1)
    w_outliers = np.where(w_devs > 0.75)[0]
    if len(w_outliers) > 0:
        flags += 1
        reasons.append(
            f"Name width anomaly: {len(w_outliers)} letter(s) "
            f">75% from median ({median_letter_w:.0f}px)"
        )

    # --- Spacing: flag only extreme gaps ---
    all_indices = sorted(list(letter_indices) + list(bullet_indices) +
                         list(period_indices))
    if len(all_indices) >= 2:
        gaps = np.array([
            boxes[all_indices[k + 1]][0] -
            (boxes[all_indices[k]][0] + boxes[all_indices[k]][2])
            for k in range(len(all_indices) - 1)
        ], dtype=float)

        # Word spaces 14-21 px, kerning 1-6 px. Flag < -2 or > 25 px.
        bad = np.where((gaps < -2) | (gaps > 25))[0]
        if len(bad) > 0:
            flags += 1
            pairs = [(all_indices[i], all_indices[i + 1]) for i in bad]
            details = ", ".join(
                f"{a}-{b} ({gaps[i]:.0f}px)" for i, (a, b) in zip(bad, pairs)
            )
            reasons.append(f"Name irregular spacing: {details}")

    # --- Draw boxes ---
    outlier_set = set()
    for idx in base_outliers:
        outlier_set.add(letter_indices[idx])
    for idx in h_outliers:
        outlier_set.add(letter_indices[idx])
    for idx in w_outliers:
        outlier_set.add(letter_indices[idx])

    for i, (x, y, w, h) in enumerate(boxes):
        if i in period_indices:
            color = (200, 200, 200)
        elif i in bullet_indices:
            color = (255, 200, 0)
        elif i in outlier_set:
            color = (0, 0, 255)
        else:
            color = (0, 255, 0)
        cv2.rectangle(proof_img, (x, y), (x + w, y + h), color, 1)

    # --- Verdict ---
    verdict = "FAIL: FAKE" if flags >= 1 else "PASS: REAL"

    n_bullets = len(bullet_indices)
    n_suspicious = len(suspicious_bullet_indices)
    color = (0, 0, 255) if "FAIL" in verdict else (0, 255, 0)
    fs = max(0.35, proof_img.shape[0] / 120)
    cv2.putText(proof_img, f"Name: {verdict} ({flags}f, {n_bullets}b, {n_suspicious}s)",
                (5, max(20, int(proof_img.shape[0] * 0.9))),
                cv2.FONT_HERSHEY_SIMPLEX, fs, color, 2)

    if output_path:
        cv2.imwrite(str(output_path), proof_img)

    return {
        'verdict': verdict,
        'score': flags,
        'reasons': reasons,
        'proof_image': proof_img,
    }
