import cv2
import numpy as np
import os
import sys


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

    def outlier_mask(values, n_std=2.0):
        mean, std = values.mean(), values.std()
        mask = (np.abs(values - mean) > n_std * std
                if std > 0 else np.zeros(len(values), dtype=bool))
        return mask, mean, std

    height_flags_raw, h_mean, h_std = outlier_mask(heights)
    height_flags = height_flags_raw.copy()
    ratio_flags, r_mean, r_std = outlier_mask(ratios)

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
        reasons.append(f"  [FAIL] P SYMBOL TOO WIDE — digit likely merged in: {', '.join(sub)}")
    else:
        if symbol_check:
            det = symbol_check[1]
            reasons.append(f"  [OK] P symbol width normal (w/h={det['sym_ratio']:.3f})")

    if not stats:
        reasons.append("  [INFO] Too few digit boxes to analyse further.")
        verdict = "FAIL: FAKE" if score >= FAKE_THRESHOLD else "PASS: REAL"
        return verdict, score, reasons

    h_std_contrib = stats["h_std"] * WEIGHT_HEIGHT_STD
    score += h_std_contrib
    reasons.append(f"  Height std = {stats['h_std']:.2f}px (+{h_std_contrib:.0f} pts)")

    y_std_contrib = stats["y_std"] * WEIGHT_Y_STD
    score += y_std_contrib
    reasons.append(f"  Y std = {stats['y_std']:.2f}px (+{y_std_contrib:.0f} pts)")

    r_std_contrib = stats["r_std"] * WEIGHT_RATIO_STD
    score += r_std_contrib
    reasons.append(f"  Ratio std = {stats['r_std']:.3f} (+{r_std_contrib:.0f} pts)")

    score += np.sum(stats["height_flags"]) * WEIGHT_HEIGHT_OUTLIER
    score += np.sum(stats["ratio_flags"]) * WEIGHT_RATIO_OUTLIER
    score += np.sum(stats["gap_flags"]) * WEIGHT_GAP_OUTLIER
    score += np.sum(stats["y_flags"]) * WEIGHT_Y_OUTLIER

    if stats.get("monotonic_drift"):
        score += 20

    verdict = "FAIL: FAKE" if score >= FAKE_THRESHOLD else "PASS: REAL"
    return verdict, score, reasons


def draw_verdict_on_image(proof_img, verdict, score, reasons):
    line_h = 18
    padding = 8
    n_lines = len(reasons) + 2
    banner_h = n_lines * line_h + padding * 2

    h, w = proof_img.shape[:2]
    extended = np.zeros((h + banner_h, w, 3), dtype=np.uint8)
    extended[:h] = proof_img

    banner_color = (30, 0, 0) if "FAIL" in verdict else (0, 30, 0)
    extended[h:] = banner_color

    font = cv2.FONT_HERSHEY_SIMPLEX
    header = f"{verdict} (score: {score:.0f})"

    cv2.putText(extended, header, (padding, h + padding + line_h),
                font, 0.45, (255, 255, 255), 1)

    return extended


def process_image(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return None, "Error: Could not read image.", 0, []

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    bounding_boxes = sorted(
        [(x, y, w, h) for c in contours
         for x, y, w, h in [cv2.boundingRect(c)] if h > 15 and w > 5],
        key=lambda b: b[0]
    )

    if not bounding_boxes:
        return None, "Error: No characters detected.", 0, []

    currency_box = bounding_boxes[0]
    digit_boxes = bounding_boxes[1:]

    symbol_check = check_symbol_width(currency_box, digit_boxes)
    stats = analyze_inconsistencies(digit_boxes)
    verdict, score, reasons = compute_verdict(stats, symbol_check=symbol_check)

    proof_img = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

    final_img = draw_verdict_on_image(proof_img, verdict, score, reasons)

    return final_img, verdict, score, reasons


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <image_path>")
        sys.exit()

    image_path = sys.argv[1]
    output_path = "result.png"

    img, verdict, score, reasons = process_image(image_path)

    if img is None:
        print(verdict)
        sys.exit()

    cv2.imwrite(output_path, img)

    print("\n=== RESULT ===")
    print("Verdict:", verdict)
    print("Score:", score)
    for r in reasons:
        print(r)

    print(f"\nSaved to: {output_path}")