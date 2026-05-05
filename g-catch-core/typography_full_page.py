import cv2
import numpy as np
import os


# ================================
# PROVEN AMOUNT ENGINE (Script 5 logic — untouched)
# Feed this ONLY clean clusters where box[0] IS the ₱ sign.
# ================================
def check_amount_cluster(boxes, proof_img, label="Amount"):
    """
    Exact forensic logic from the proven single-amount script.
    Expects boxes sorted left→right, ₱ sign at index 0.
    """
    if len(boxes) < 2:
        return {"verdict": "SKIPPED", "flags": 0, "reasons": []}

    boxes = sorted(boxes, key=lambda b: b[0])

    # --- METRIC 1: Aspect Ratios ---
    aspect_ratios = []
    for (x, y, w, h) in boxes:
        ratio = round(w / h, 2)
        aspect_ratios.append(ratio)
        cv2.rectangle(proof_img, (x, y), (x + w, y + h), (255, 0, 0), 1)
        cv2.putText(proof_img, str(ratio), (x, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)

    # --- METRIC 2: Kerning ---
    gaps = []
    for i in range(len(boxes) - 1):
        curr_end = boxes[i][0] + boxes[i][2]
        next_start = boxes[i + 1][0]
        gap = next_start - curr_end
        gaps.append(gap)
        mid_y = boxes[i][1] + int(boxes[i][3] / 2)
        cv2.line(proof_img, (curr_end, mid_y), (next_start, mid_y), (0, 0, 255), 2)

    # --- FORENSIC RULES (Script 5 exact) ---
    fraud_flags = 0
    reasons = []

    # Rule 1: Peso gap check (real receipts = 1-2px)
    if len(gaps) > 0:
        peso_gap = gaps[0]
        if peso_gap > 3:
            fraud_flags += 1
            reasons.append(
                f"{label}: Large gap after ₱ sign ({peso_gap}px) — spacebar use likely."
            )

    # Rules 2 & 3: Digits only — skip index 0 (₱ sign)
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


# ================================
# VARIANT: no ₱ skip (when ₱ was already stripped by column splitter)
# Same rules applied to all boxes since they are all digits.
# ================================
def check_amount_cluster_no_peso(boxes, proof_img, label="Amount"):
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

    # No Rule 1 — no ₱ sign in cluster
    # Rule 2
    ratio_variance = max(aspect_ratios) - min(aspect_ratios)
    if ratio_variance > 0.05:
        fraud_flags += 1
        reasons.append(
            f"{label}: Inconsistent font weights (variance: {ratio_variance:.2f}). "
            f"Mixed fonts detected."
        )

    # Rule 3
    avg_ratio = sum(aspect_ratios) / len(aspect_ratios)
    if avg_ratio < 0.70 or avg_ratio > 0.85:
        fraud_flags += 1
        reasons.append(
            f"{label}: Font aspect ratio ({avg_ratio:.2f}) does not match "
            f"GCash standard UI font (expected 0.70-0.85)."
        )

    verdict = "FORGED" if fraud_flags > 0 else "AUTHENTIC"
    return {"verdict": verdict, "flags": fraud_flags, "reasons": reasons}


# ================================
# PESO SIGN DETECTOR
# ================================
def find_peso_index(boxes):
    """
    Returns index of the ₱ box in a sorted cluster, or -1 if not found.
    ₱ is always leftmost. Detection uses aspect ratio as primary signal.
    """
    if not boxes:
        return -1

    x0, y0, w0, h0 = boxes[0]
    aspect0 = round(w0 / h0, 2) if h0 > 0 else 1.0

    # Primary: ₱ glyph aspect ratio is 0.92+ (wider than any digit)
    if aspect0 > 0.92:
        return 0

    # Secondary: slight height outlier
    heights = [h for (_, _, _, h) in boxes]
    median_h = np.median(heights)
    if median_h > 0 and (h0 / median_h) >= 1.05:
        return 0

    # Tertiary: gap after first char larger than inter-digit average
    if len(boxes) > 2:
        gap_after_first = boxes[1][0] - (boxes[0][0] + boxes[0][2])
        remaining_gaps = [
            boxes[j][0] - (boxes[j-1][0] + boxes[j-1][2])
            for j in range(2, len(boxes))
        ]
        avg_gap = np.mean(remaining_gaps) if remaining_gaps else 0
        if avg_gap > 0 and gap_after_first > avg_gap * 1.8:
            return 0

    return -1


# ================================
# MAIN FULL RECEIPT SCANNER
# ================================
def scan_receipt(image_path, output_path):
    print(f"\n{'='*55}")
    print(f"  GCash Receipt Forensic Scanner")
    print(f"  Target: {image_path}")
    print(f"{'='*55}\n")

    img = cv2.imread(image_path)
    if img is None:
        print("Error: Could not read image.")
        return False

    # --- 1. AUTO-CROP RECEIPT ---
    gray_full = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, paper_thresh = cv2.threshold(gray_full, 220, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(paper_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        largest = max(contours, key=cv2.contourArea)
        rx, ry, rw, rh = cv2.boundingRect(largest)
        img = img[ry + 5:ry + rh - 5, rx + 5:rx + rw - 5]
        print(f"[+] Receipt isolated: {rw}x{rh}px")

    # --- 2. TEXT DETECTION ---
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        11, 2
    )
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if 10 < h < 100 and 2 < w < 80:
            boxes.append((x, y, w, h))

    # --- 3. LINE SEGMENTATION ---
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

    # --- 4. ZONE, EXTRACT, FEED ---
    for i, line in enumerate(lines):
        if len(line) < 4:
            continue

        y_top = min(b[1] for b in line)
        rel_y = y_top / receipt_h

        # Find label | value column split (largest gap)
        max_gap = 0
        split_idx = -1
        for j in range(1, len(line)):
            gap = line[j][0] - (line[j-1][0] + line[j-1][2])
            if gap > max_gap:
                max_gap = gap
                split_idx = j

        # Amount zone only — middle of receipt, right cluster
        if not (0.20 <= rel_y <= 0.75 and max_gap > 30):
            continue

        cluster = sorted(line[split_idx:], key=lambda b: b[0])

        if len(cluster) < 2:
            continue

        # Route to correct engine based on whether ₱ is present
        peso_idx = find_peso_index(cluster)

        if peso_idx >= 0:
            print(f"  [Line {i+1}] Amount ({len(cluster)} chars, ₱ detected at [{peso_idx}])")
            result = check_amount_cluster(cluster, proof_img, "Amount")
        else:
            print(f"  [Line {i+1}] Amount ({len(cluster)} chars, no ₱ — digits only)")
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
            cv2.rectangle(proof_img, (x1-3, y1-3), (x2+3, y2+3), (0, 0, 255), 2)

    # --- 5. FINAL VERDICT ---
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
    cv2.imwrite(output_path, proof_img)
    print(f"[+] Proof saved → {output_path}")
    return True


# ================================
# RUN
# ================================
if __name__ == "__main__":
    input_file = "full_receipt.jpg"
    output_file = "forensic_result.jpg"

    if os.path.exists(input_file):
        scan_receipt(input_file, output_file)
    else:
        print(f"Image not found: '{input_file}'")
        print("Rename your receipt image to 'full_receipt.jpg' and re-run.")
