import cv2
import numpy as np
import os

def check_targeted_typography(image_path, output_path):
    print(f"Executing Targeted Forensic Scan: {image_path}...\n")

    # 1. Load and Isolate Receipt Body
    img = cv2.imread(image_path)
    if img is None:
        return False

    gray_full = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, paper_thresh = cv2.threshold(gray_full, 220, 255, cv2.THRESH_BINARY)
    paper_contours, _ = cv2.findContours(paper_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if paper_contours:
        largest_paper = max(paper_contours, key=cv2.contourArea)
        px, py, pw, ph = cv2.boundingRect(largest_paper)
        img = img[py+5 : py+ph-5, px+5 : px+pw-5]

    # 2. Preprocessing for Character Detection
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 11, 2)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    raw_boxes = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if 10 < h < 100 and 2 < w < 80:
            raw_boxes.append((x, y, w, h))

    # 3. Line Segmentation
    raw_boxes = sorted(raw_boxes, key=lambda b: b[1])
    lines = []
    current_line = []
    for box in raw_boxes:
        if not current_line:
            current_line.append(box)
        else:
            avg_y = sum([b[1] for b in current_line]) / len(current_line)
            if abs(box[1] - avg_y) < (box[3] * 0.5):
                current_line.append(box)
            else:
                current_line = sorted(current_line, key=lambda b: b[0])
                if len(current_line) > 2: lines.append(current_line)
                current_line = [box]
    if current_line and len(current_line) > 2:
        lines.append(sorted(current_line, key=lambda b: b[0]))

    proof_img = img.copy()
    receipt_height = img.shape[0]

    for line_index, line_boxes in enumerate(lines):
        if len(line_boxes) < 4: continue

        line_y = min([b[1] for b in line_boxes])
        relative_y = line_y / receipt_height

        # Column Detection
        max_gap = 0
        split_index = -1
        for i in range(1, len(line_boxes)):
            gap = line_boxes[i][0] - (line_boxes[i-1][0] + line_boxes[i-1][2])
            if gap > max_gap:
                max_gap = gap
                split_index = i

        target_clusters = []
        zone_label = ""

        # --- HEURISTIC ZONING ---
        # Amount Fields (Middle section)
        if 0.20 <= relative_y <= 0.75 and max_gap > 30:
            zone_label = "AMOUNT FIELD"
            target_clusters.append(("Value Column", line_boxes[split_index:]))
            divider_x = line_boxes[split_index-1][0] + line_boxes[split_index-1][2] + int(max_gap/2)
            cv2.line(proof_img, (divider_x, 0), (divider_x, receipt_height), (0, 255, 255), 1)

        # Footer (Ref No & Time)
        elif relative_y > 0.75 and max_gap > 30:
            zone_label = "REF NO / TIME"
            left_part = line_boxes[:split_index]
            ref_val = []
            curr_w = [left_part[0]]
            for i in range(1, len(left_part)):
                if left_part[i][0] - (curr_w[-1][0] + curr_w[-1][2]) > 8:
                    ref_val = left_part[i:]
                    break
                curr_w.append(left_part[i])

            if ref_val: target_clusters.append(("Ref No Value", ref_val))
            target_clusters.append(("Time/Date", line_boxes[split_index:]))

        if not target_clusters: continue

        print(f"--- Processing {zone_label} ---")

        for cluster_name, boxes in target_clusters:
            # Calculate Gaps (Kerning)
            gaps = []
            for i in range(len(boxes) - 1):
                gap = boxes[i+1][0] - (boxes[i][0] + boxes[i][2])
                gaps.append(gap)

            # Calculate Aspect Ratios (Standard Chars Only)
            ratios = [round(b[2]/b[3], 2) for b in boxes if 0.4 <= (b[2]/b[3]) <= 1.1]

            # --- AUTOMATED VERDICT LOGIC ---
            fraud_flags = 0

            # Rule 1: Peso Gap Check (If Peso sign is present)
            if cluster_name == "Value Column" and len(gaps) > 0:
                if gaps[0] > 3:
                    fraud_flags += 1
                    print(f"  -> 🚨 Rule 1 Trip: Large Peso Gap ({gaps[0]}px)")

            if len(ratios) >= 3:
                var = max(ratios) - min(ratios)
                avg = sum(ratios) / len(ratios)

                # Rule 2: Variance Check (Consistency)
                if var > 0.05:
                    fraud_flags += 1
                    print(f"  -> 🚨 Rule 2 Trip: High Font Variance ({var:.2f})")

                # Rule 3: Baseline Check (GCash Standard)
                if avg < 0.70 or avg > 0.85:
                    fraud_flags += 1
                    print(f"  -> 🚨 Rule 3 Trip: Non-standard Baseline ({avg:.2f})")

            # Draw Visual Feedback
            color = (0, 0, 255) if fraud_flags > 0 else (255, 0, 0)
            for bx in boxes:
                cv2.rectangle(proof_img, (bx[0], bx[1]), (bx[0]+bx[2], bx[1]+bx[3]), color, 1)

            if fraud_flags > 0:
                x_s, y_s = boxes[0][0], min([b[1] for b in boxes])
                w_t = (boxes[-1][0] + boxes[-1][2]) - x_s
                h_m = max([b[3] for b in boxes])
                cv2.rectangle(proof_img, (x_s-3, y_s-3), (x_s+w_t+3, y_s+h_m+3), (0, 0, 255), 2)

    cv2.imwrite(output_path, proof_img)
    print(f"\nForensic Map saved to: {output_path}")
    return True

if __name__ == "__main__":
    target_image = "full_receipt.jpg"  # Drop an uncropped screenshot here
    output_image = "full_page_result.jpg"
    if os.path.exists(input_file):
        check_targeted_typography(input_file, output_file)
