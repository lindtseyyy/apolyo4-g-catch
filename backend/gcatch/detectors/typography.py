import cv2
import numpy as np

from gcatch.utils.image import preprocess_image, find_text_regions


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
