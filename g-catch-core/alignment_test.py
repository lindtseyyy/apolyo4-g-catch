import cv2
import numpy as np
import os

def check_alignment(image_path, output_path):
    print(f"Running Micro-Alignment Forensics on: {image_path}...")

    # 1. Load the cropped image of the amount
    img = cv2.imread(image_path)
    if img is None:
        print("Error: Could not read image. Check the file path.")
        return False

    # 2. Preprocess: Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 3. Preprocess: Binary Thresholding (Inverted)
    # OpenCV's findContours looks for WHITE objects on a BLACK background.
    # Receipts are black text on white, so we must invert it.
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

    # 4. Execute Contour Detection
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 5. Extract and Filter Bounding Boxes
    bounding_boxes = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        # FILTER: Ignore tiny specs of dust or periods. We only want numbers/symbols.
        if h > 15 and w > 5:
            bounding_boxes.append((x, y, w, h))

    # 6. Sort boxes from Left to Right (Reading order)
    bounding_boxes = sorted(bounding_boxes, key=lambda b: b[0])

    if len(bounding_boxes) < 2:
        print("Error: Not enough distinct characters found to calculate alignment.")
        return False

    # 7. THE MATH: Calculate the "Human Hand" Variance
    # The bottom of a character is its Y-coordinate plus its Height (y + h)
    bottom_y_coords = [y + h for x, y, w, h in bounding_boxes]

    max_y = max(bottom_y_coords)
    min_y = min(bottom_y_coords)
    y_variance = max_y - min_y  # The maximum pixel drift

    # 8. Generate the Visual Proof for the Judges
    proof_img = img.copy()

    # Draw the perfect "Machine Baseline" based on the first character
    baseline_y = bottom_y_coords[0]
    width = proof_img.shape[1]
    cv2.line(proof_img, (0, baseline_y), (width, baseline_y), (255, 0, 0), 1) # Blue line

    for x, y, w, h in bounding_boxes:
        # Draw a tight green box around every character
        cv2.rectangle(proof_img, (x, y), (x + w, y + h), (0, 255, 0), 1)
        # Draw a red dot at the exact bottom coordinate of the character
        cv2.circle(proof_img, (x + int(w/2), y + h), 2, (0, 0, 255), -1)

    # 9. The Logic Verdict
    print(f"Calculated Bottom Y-Coordinates: {bottom_y_coords}")
    print(f"Maximum Pixel Drift: {y_variance} pixels")

    # If the drift is greater than 2 pixels, a human manually dragged a number.
    if y_variance > 2:
        print("🚨 VERDICT: FORGED (Human Misalignment Detected)")
        # Stamp the visual proof
        cv2.putText(proof_img, f"FORGED: {y_variance}px Drift", (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    else:
        print("✅ VERDICT: AUTHENTIC (Machine Alignment Perfect)")
        cv2.putText(proof_img, f"AUTH: {y_variance}px Drift", (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Save the proof
    cv2.imwrite(output_path, proof_img)
    print(f"Success! Visual proof saved to: {output_path}")
    return True

if __name__ == "__main__":
    target_image = "test_amount.jpg"
    output_image = "alignment_result.jpg"

    if os.path.exists(target_image):
        check_alignment(target_image, output_image)
    else:
        print(f"Waiting for test data: Please upload a cropped image named '{target_image}' to this folder.")
