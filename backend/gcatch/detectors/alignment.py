import cv2


def check_alignment(image_path, output_path=None):
    """Run micro-alignment forensics on a cropped amount-field image.

    Detects whether characters share a consistent baseline. Manually
    pasted/edited digits typically drift by more than 2 pixels from the
    machine-aligned baseline.

    Args:
        image_path: Path to the cropped amount-field image.
        output_path: Optional path to save the annotated proof image.

    Returns:
        dict with keys: verdict, drift_pixels, char_count, bottom_y_coords,
        proof_image, or None if insufficient characters are found.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    bounding_boxes = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if h > 15 and w > 5:
            bounding_boxes.append((x, y, w, h))

    bounding_boxes = sorted(bounding_boxes, key=lambda b: b[0])

    if len(bounding_boxes) < 2:
        return {
            'verdict': 'INCONCLUSIVE',
            'drift_pixels': 0,
            'char_count': len(bounding_boxes),
            'bottom_y_coords': [],
            'proof_image': img,
            'reasons': ['Insufficient characters for alignment analysis'],
        }

    bottom_y_coords = [y + h for x, y, w, h in bounding_boxes]
    y_variance = max(bottom_y_coords) - min(bottom_y_coords)

    proof_img = img.copy()
    baseline_y = bottom_y_coords[0]
    width = proof_img.shape[1]
    cv2.line(proof_img, (0, baseline_y), (width, baseline_y), (255, 0, 0), 1)

    for x, y, w, h in bounding_boxes:
        cv2.rectangle(proof_img, (x, y), (x + w, y + h), (0, 255, 0), 1)
        cv2.circle(proof_img, (x + int(w / 2), y + h), 2, (0, 0, 255), -1)

    if y_variance > 2:
        verdict = "FORGED"
        reasons = [f"{y_variance}px baseline drift — human misalignment detected"]
    else:
        verdict = "AUTHENTIC"
        reasons = []

    cv2.putText(proof_img, f"{verdict}: {y_variance}px Drift", (5, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                (0, 0, 255) if verdict == "FORGED" else (0, 255, 0), 2)

    if output_path:
        cv2.imwrite(output_path, proof_img)

    return {
        'verdict': verdict,
        'drift_pixels': y_variance,
        'char_count': len(bounding_boxes),
        'bottom_y_coords': bottom_y_coords,
        'proof_image': proof_img,
        'reasons': reasons,
    }
