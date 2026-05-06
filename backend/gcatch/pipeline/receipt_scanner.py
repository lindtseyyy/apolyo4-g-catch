import os

import cv2
import numpy as np

from gcatch.detectors.typography import analyze_typography
from gcatch.utils.image import (
    preprocess_image,
    find_text_regions,
    cluster_regions_by_vertical_position,
    calculate_region_metrics,
)


def find_peso_index(boxes):
    """Return the index of the ₱ box in a sorted cluster, or -1 if not found.

    Uses aspect ratio, height outlier, and gap-after-first heuristics.
    """
    if not boxes:
        return -1

    x0, y0, w0, h0 = boxes[0]
    aspect0 = round(w0 / h0, 2) if h0 > 0 else 1.0

    if aspect0 > 0.92:
        return 0

    heights = [h for (_, _, _, h) in boxes]
    median_h = np.median(heights)
    if median_h > 0 and (h0 / median_h) >= 1.05:
        return 0

    if len(boxes) > 2:
        gap_after_first = boxes[1][0] - (boxes[0][0] + boxes[0][2])
        remaining_gaps = [
            boxes[j][0] - (boxes[j - 1][0] + boxes[j - 1][2])
            for j in range(2, len(boxes))
        ]
        avg_gap = np.mean(remaining_gaps) if remaining_gaps else 0
        if avg_gap > 0 and gap_after_first > avg_gap * 1.8:
            return 0

    return -1


def check_amount_cluster(boxes, proof_img, label="Amount"):
    """Forensic check on an amount cluster with a ₱ sign at index 0."""
    if len(boxes) < 2:
        return {"verdict": "SKIPPED", "flags": 0, "reasons": []}

    boxes = sorted(boxes, key=lambda b: b[0])

    aspect_ratios = []
    for (x, y, w, h) in boxes:
        ratio = round(w / h, 2)
        aspect_ratios.append(ratio)
        cv2.rectangle(proof_img, (x, y), (x + w, y + h), (255, 0, 0), 1)
        cv2.putText(proof_img, str(ratio), (x, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)

    gaps = []
    for i in range(len(boxes) - 1):
        curr_end = boxes[i][0] + boxes[i][2]
        next_start = boxes[i + 1][0]
        gap = next_start - curr_end
        gaps.append(gap)
        mid_y = boxes[i][1] + int(boxes[i][3] / 2)
        cv2.line(proof_img, (curr_end, mid_y), (next_start, mid_y), (0, 0, 255), 2)

    fraud_flags = 0
    reasons = []

    if len(gaps) > 0:
        peso_gap = gaps[0]
        if peso_gap > 3:
            fraud_flags += 1
            reasons.append(
                f"{label}: Large gap after ₱ sign ({peso_gap}px) — spacebar use likely."
            )

    if len(aspect_ratios) > 1:
        number_ratios = aspect_ratios[1:]
        ratio_variance = max(number_ratios) - min(number_ratios)
        if ratio_variance > 0.05:
            fraud_flags += 1
            reasons.append(
                f"{label}: Inconsistent font weights (variance: {ratio_variance:.2f}). "
                f"Mixed fonts detected."
            )
        avg_ratio = sum(number_ratios) / len(number_ratios)
        if avg_ratio < 0.70 or avg_ratio > 0.85:
            fraud_flags += 1
            reasons.append(
                f"{label}: Font aspect ratio ({avg_ratio:.2f}) does not match "
                f"GCash standard UI font (expected 0.70-0.85)."
            )

    verdict = "FORGED" if fraud_flags > 0 else "AUTHENTIC"
    return {"verdict": verdict, "flags": fraud_flags, "reasons": reasons}


def check_amount_cluster_no_peso(boxes, proof_img, label="Amount"):
    """Forensic check on an amount cluster without a ₱ sign (digits only)."""
    if len(boxes) < 2:
        return {"verdict": "SKIPPED", "flags": 0, "reasons": []}

    boxes = sorted(boxes, key=lambda b: b[0])

    aspect_ratios = []
    gaps = []

    for (x, y, w, h) in boxes:
        ratio = round(w / h, 2)
        aspect_ratios.append(ratio)
        cv2.rectangle(proof_img, (x, y), (x + w, y + h), (255, 0, 0), 1)
        cv2.putText(proof_img, str(ratio), (x, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)

    for i in range(len(boxes) - 1):
        curr_end = boxes[i][0] + boxes[i][2]
        next_start = boxes[i + 1][0]
        gaps.append(next_start - curr_end)
        mid_y = boxes[i][1] + int(boxes[i][3] / 2)
        cv2.line(proof_img, (curr_end, mid_y), (next_start, mid_y), (0, 0, 255), 2)

    fraud_flags = 0
    reasons = []

    ratio_variance = max(aspect_ratios) - min(aspect_ratios)
    if ratio_variance > 0.05:
        fraud_flags += 1
        reasons.append(
            f"{label}: Inconsistent font weights (variance: {ratio_variance:.2f}). "
            f"Mixed fonts detected."
        )

    avg_ratio = sum(aspect_ratios) / len(aspect_ratios)
    if avg_ratio < 0.70 or avg_ratio > 0.85:
        fraud_flags += 1
        reasons.append(
            f"{label}: Font aspect ratio ({avg_ratio:.2f}) does not match "
            f"GCash standard UI font (expected 0.70-0.85)."
        )

    verdict = "FORGED" if fraud_flags > 0 else "AUTHENTIC"
    return {"verdict": verdict, "flags": fraud_flags, "reasons": reasons}


def scan_receipt(image_path, output_path=None):
    """Full receipt forensic scanner.

    Isolates the receipt region, segments text lines, identifies amount
    clusters in the middle zone, and runs typography checks on each.
    """
    print(f"\n{'='*55}")
    print(f"  GCash Receipt Forensic Scanner")
    print(f"  Target: {image_path}")
    print(f"{'='*55}\n")

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")

    gray_full = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, paper_thresh = cv2.threshold(gray_full, 220, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(paper_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        largest = max(contours, key=cv2.contourArea)
        rx, ry, rw, rh = cv2.boundingRect(largest)
        img = img[ry + 5:ry + rh - 5, rx + 5:rx + rw - 5]
        print(f"[+] Receipt isolated: {rw}x{rh}px")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 11, 2,
    )
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if 10 < h < 100 and 2 < w < 80:
            boxes.append((x, y, w, h))

    boxes = sorted(boxes, key=lambda b: b[1])
    lines = []
    current = []

    for b in boxes:
        if not current:
            current.append(b)
        else:
            avg_y = np.mean([c[1] for c in current])
            if abs(b[1] - avg_y) < b[3] * 0.5:
                current.append(b)
            else:
                if len(current) > 2:
                    lines.append(sorted(current, key=lambda c: c[0]))
                current = [b]

    if current and len(current) > 2:
        lines.append(sorted(current, key=lambda c: c[0]))

    print(f"[+] {len(lines)} text lines detected\n")

    proof_img = img.copy()
    receipt_h = img.shape[0]
    overall_flags = 0
    all_reasons = []

    for i, line in enumerate(lines):
        if len(line) < 4:
            continue

        y_top = min(b[1] for b in line)
        rel_y = y_top / receipt_h

        max_gap = 0
        split_idx = -1
        for j in range(1, len(line)):
            gap = line[j][0] - (line[j - 1][0] + line[j - 1][2])
            if gap > max_gap:
                max_gap = gap
                split_idx = j

        if not (0.20 <= rel_y <= 0.75 and max_gap > 30):
            continue

        cluster = sorted(line[split_idx:], key=lambda b: b[0])

        if len(cluster) < 2:
            continue

        peso_idx = find_peso_index(cluster)

        if peso_idx >= 0:
            print(f"  [Line {i + 1}] Amount ({len(cluster)} chars, ₱ detected at [{peso_idx}])")
            result = check_amount_cluster(cluster, proof_img, "Amount")
        else:
            print(f"  [Line {i + 1}] Amount ({len(cluster)} chars, no ₱ — digits only)")
            result = check_amount_cluster_no_peso(cluster, proof_img, "Amount")

        print(f"         → {result['verdict']}")

        if result["flags"] > 0:
            overall_flags += result["flags"]
            all_reasons.extend(result["reasons"])
            for r in result["reasons"]:
                print(f"           ! {r}")

            xs = [b[0] for b in cluster]
            ys = [b[1] for b in cluster]
            x1 = min(xs)
            y1 = min(ys)
            x2 = max(cluster[k][0] + cluster[k][2] for k in range(len(cluster)))
            y2 = max(cluster[k][1] + cluster[k][3] for k in range(len(cluster)))
            cv2.rectangle(proof_img, (x1 - 3, y1 - 3), (x2 + 3, y2 + 3), (0, 0, 255), 2)

    print(f"\n{'='*55}")
    final = "FORGED" if overall_flags > 0 else "AUTHENTIC"
    color = (0, 0, 255) if final == "FORGED" else (0, 255, 0)

    if final == "FORGED":
        print(f"  FINAL VERDICT: FORGED ({overall_flags} flag(s))")
        for r in all_reasons:
            print(f"   - {r}")
    else:
        print(f"  FINAL VERDICT: AUTHENTIC")
        print(f"   - Font weights and kerning match GCash machine standards.")

    print(f"{'='*55}\n")

    cv2.putText(proof_img, f"FINAL: {final}", (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    if output_path:
        cv2.imwrite(output_path, proof_img)
        print(f"[+] Proof saved → {output_path}")

    return {
        "verdict": final,
        "flags": overall_flags,
        "reasons": all_reasons,
        "proof_image": proof_img,
    }


def detect_amount_field_advanced(image_path, output_dir="output"):
    """Detect and extract the amount field from a receipt, then run typography forensics.

    For small crops, runs typography directly. For full receipts, locates
    the largest text region in the bottom 40% and extracts it.
    """
    print(f"\n{'='*60}")
    print(f"GCash Receipt Forensic Analysis (Enhanced)")
    print(f"{'='*60}")
    print(f"Processing: {image_path}")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    original_img = cv2.imread(image_path)
    if original_img is None:
        print("Error: Could not read image.")
        return False, "ERROR", None, None

    print(f"Image loaded: {original_img.shape[1]}x{original_img.shape[0]} pixels")

    img_height, img_width = original_img.shape[0], original_img.shape[1]
    img_area = img_height * img_width
    is_small_crop = img_area < 100000

    if is_small_crop:
        print("Detected as small cropped image (likely amount field)")
        amount_crop = original_img
    else:
        print("\nAnalyzing full receipt image...")
        processed, _ = preprocess_image(original_img)
        bounding_boxes = find_text_regions(processed)

        if not bounding_boxes:
            print("No text regions detected in image.")
            return False, "NO_TEXT_FOUND", None, None

        print(f"  Found {len(bounding_boxes)} text regions")

        row_clusters = cluster_regions_by_vertical_position(bounding_boxes, vertical_tolerance=15)
        print(f"  Found {len(row_clusters)} text rows")

        region_metrics = [calculate_region_metrics(box) for box in bounding_boxes]

        bottom_threshold = img_height * 0.6
        bottom_regions_indices = [i for i, metrics in enumerate(region_metrics)
                                  if metrics['y'] > bottom_threshold]

        print(f"  Regions in bottom 40%: {len(bottom_regions_indices)}")

        if bottom_regions_indices:
            largest_bottom_idx = max(bottom_regions_indices,
                                     key=lambda i: region_metrics[i]['area'])
            selected_region_idx = largest_bottom_idx
            print("  Selected largest region in bottom area")
        else:
            largest_idx = max(range(len(region_metrics)),
                              key=lambda i: region_metrics[i]['area'])
            selected_region_idx = largest_idx
            print("  No regions in bottom area, using largest overall")

        selected_region = bounding_boxes[selected_region_idx]
        selected_metrics = region_metrics[selected_region_idx]

        x, y, w, h = selected_region

        print(f"\n  Selected region:")
        print(f"    Position: ({x}, {y})")
        print(f"    Size: {w}x{h} pixels")
        print(f"    Area: {selected_metrics['area']} sq. pixels")

        expand_x = max(int(w * 0.5), 20)
        expand_y = max(int(h * 0.5), 20)

        x1 = max(0, x - expand_x)
        y1 = max(0, y - expand_y)
        x2 = min(img_width, x + w + expand_x)
        y2 = min(img_height, y + h + expand_y)

        amount_crop = original_img[y1:y2, x1:x2]

        debug_img = original_img.copy()
        for i, bbox in enumerate(bounding_boxes):
            bx, by, bw, bh = bbox
            color = (0, 255, 0) if i == selected_region_idx else (200, 200, 200)
            thickness = 2 if i == selected_region_idx else 1
            cv2.rectangle(debug_img, (bx, by), (bx + bw, by + bh), color, thickness)

        cv2.rectangle(debug_img, (x, y), (x + w, y + h), (0, 255, 0), 3)
        cv2.putText(debug_img, "AMOUNT", (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.rectangle(debug_img, (x1, y1), (x2, y2), (255, 0, 0), 2)

        debug_path = os.path.join(output_dir, "debug_region_detected.jpg")
        cv2.imwrite(debug_path, debug_img)
        print(f"  Debug image: {debug_path}")

    crop_path = os.path.join(output_dir, "extracted_amount_field.jpg")
    cv2.imwrite(crop_path, amount_crop)
    print(f"\nAmount field extracted: {crop_path}")
    print(f"  Size: {amount_crop.shape[1]}x{amount_crop.shape[0]} pixels")

    result_path = os.path.join(output_dir, "forensic_verdict.jpg")
    forensics_result = analyze_typography(amount_crop, result_path)

    print(f"\n{'='*60}")
    print(f"FINAL VERDICT: {forensics_result['verdict']}")
    print(f"{'='*60}")

    if forensics_result['reasons']:
        print("\nFindings:")
        for reason in forensics_result['reasons']:
            print(f"  {reason}")
    else:
        print("\nNo fraud indicators detected.")

    print(f"\nCharacters analyzed: {forensics_result['char_count']}")
    print(f"Average aspect ratio: {forensics_result['avg_aspect_ratio']:.2f}")

    return True, forensics_result['verdict'], result_path, amount_crop
