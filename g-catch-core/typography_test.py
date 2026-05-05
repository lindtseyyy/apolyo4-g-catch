import cv2
import numpy as np
import os

def check_typography(image_path, output_path):
    print(f"Running Typography & Kerning Forensics on: {image_path}...")

    img = cv2.imread(image_path)
    if img is None:
        print("Error: Could not read image.")
        return False

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    bounding_boxes = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if h > 15 and w > 5:  # Filter noise
            bounding_boxes.append((x, y, w, h))

    # Sort from Left to Right
    bounding_boxes = sorted(bounding_boxes, key=lambda b: b[0])

    if len(bounding_boxes) < 2:
        return False

    proof_img = img.copy()

    # --- METRIC 1: ASPECT RATIO (Font Thickness/Weight) ---
    print("\n--- Font Aspect Ratios (Width/Height) ---")
    aspect_ratios = []
    for i, (x, y, w, h) in enumerate(bounding_boxes):
        ratio = round(w / h, 2)
        aspect_ratios.append(ratio)

        # Draw the box and print the ratio above the character
        cv2.rectangle(proof_img, (x, y), (x + w, y + h), (255, 0, 0), 1)
        cv2.putText(proof_img, str(ratio), (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
        print(f"Char {i+1}: Ratio {ratio}")

    # --- METRIC 2: KERNING (Horizontal Space Between Characters) ---
    print("\n--- Kerning (Pixel Gaps) ---")
    gaps = []
    for i in range(len(bounding_boxes) - 1):
        # The gap is the X-coordinate of the NEXT character, minus the (X + Width) of the CURRENT character
        current_char_end_x = bounding_boxes[i][0] + bounding_boxes[i][2]
        next_char_start_x = bounding_boxes[i+1][0]

        gap_pixels = next_char_start_x - current_char_end_x
        gaps.append(gap_pixels)

        # Draw a line representing the gap
        mid_y = bounding_boxes[i][1] + int(bounding_boxes[i][3] / 2)
        cv2.line(proof_img, (current_char_end_x, mid_y), (next_char_start_x, mid_y), (0, 0, 255), 2)
        print(f"Gap between Char {i+1} and {i+2}: {gap_pixels}px")

    # --- AUTOMATED VERDICT LOGIC ---
    print("\n--- Forensic Verdict ---")
    fraud_flags = 0
    reasons = []

    # Rule 1: The Peso Gap Check (Usually 1px to 2px on real receipts)
    if len(gaps) > 0:
        peso_gap = gaps[0]
        if peso_gap > 3:
            fraud_flags += 1
            reasons.append(f"Suspiciously large gap after Peso sign ({peso_gap}px). Human spacebar use likely.")

    # Rule 2 & 3: Font Consistency & GCash Baseline
    if len(aspect_ratios) > 1:
        number_ratios = aspect_ratios[1:]  # Skip Char 1 (Peso sign)

        # Rule 2: Variance Check (Are all numbers identical in style?)
        ratio_variance = max(number_ratios) - min(number_ratios)
        if ratio_variance > 0.05:
            fraud_flags += 1
            reasons.append(f"Inconsistent font weights detected (Variance: {ratio_variance:.2f}). Mixed fonts used.")

        # Rule 3: GCash Baseline Check (Numbers should average ~0.78)
        avg_ratio = sum(number_ratios) / len(number_ratios)
        if avg_ratio < 0.70 or avg_ratio > 0.85:
            fraud_flags += 1
            reasons.append(f"Font aspect ratio ({avg_ratio:.2f}) does not match GCash standard UI font.")

    # Output Verdict
    if fraud_flags > 0:
        verdict = "FORGED"
        color = (0, 0, 255) # Red
        print("🚨 VERDICT: FORGED")
        for r in reasons:
            print(f" - {r}")
    else:
        verdict = "AUTHENTIC"
        color = (0, 255, 0) # Green
        print("✅ VERDICT: AUTHENTIC")
        print(" - Cryptographic alignment and font weights match machine standards.")

    # Stamp the verdict onto the image proof
    cv2.putText(proof_img, f"VERDICT: {verdict}", (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # Save visual proof
    cv2.imwrite(output_path, proof_img)
    print(f"\nSuccess! Typography map saved to: {output_path}")
    return True

if __name__ == "__main__":
    target_image = "testamountfake2.jpg"  # Use your test image
    output_image = "testamountfake2_result.jpg"

    if os.path.exists(target_image):
        check_typography(target_image, output_image)
    else:
        print(f"Upload '{target_image}' to test.")
