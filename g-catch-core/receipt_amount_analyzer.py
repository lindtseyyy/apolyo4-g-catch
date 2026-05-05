import cv2
import numpy as np
import os
import re
from typing import List, Tuple, Dict, Optional

def preprocess_image(image):
    """Preprocess image for better text detection."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(4, 4))
    enhanced = clahe.apply(gray)

    # For very small images, skip denoise to preserve features
    img_area = image.shape[0] * image.shape[1]
    if img_area < 50000:  # Skip denoise for very small images
        return enhanced, gray

    # Denoise for larger images
    denoised = cv2.fastNlMeansDenoising(enhanced, h=10)

    return denoised, gray


def find_text_regions(image):
    """
    Detect text regions using contour analysis.
    Returns list of bounding boxes for detected characters/segments.
    More sensitive for small images.
    """
    best_boxes = []

    # Try different threshold values
    for thresh_val in [100, 130, 150, 170]:
        _, thresh = cv2.threshold(image, thresh_val, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        bounding_boxes = []
        for c in contours:
            area = cv2.contourArea(c)
            if area > 1:  # Very relaxed - accept any contour with area > 1
                x, y, w, h = cv2.boundingRect(c)
                if h >= 2 and w >= 1:  # Very small minimum size
                    bounding_boxes.append((x, y, w, h))

        # Sort left to right
        bounding_boxes = sorted(bounding_boxes, key=lambda b: b[0])

        # Keep the threshold that gives the best results
        if len(bounding_boxes) > len(best_boxes):
            best_boxes = bounding_boxes

    return best_boxes


def cluster_regions_by_vertical_position(bounding_boxes: List[Tuple[int, int, int, int]],
                                        vertical_tolerance: int = 10) -> List[List[Tuple[int, int, int, int]]]:
    """
    Cluster text regions by vertical position (Y coordinate).
    Receipt items are aligned in rows - this groups them together.

    Args:
        bounding_boxes: List of (x, y, w, h) bounding boxes
        vertical_tolerance: Pixel tolerance for grouping regions in same row

    Returns:
        List of clusters, where each cluster is a list of boxes in same row
    """
    if not bounding_boxes:
        return []

    # Sort by Y position (vertical)
    sorted_boxes = sorted(bounding_boxes, key=lambda b: b[1])

    clusters = []
    current_cluster = [sorted_boxes[0]]
    current_y = sorted_boxes[0][1]

    for box in sorted_boxes[1:]:
        box_y = box[1]
        # If this box is within tolerance of current row, add to cluster
        if abs(box_y - current_y) <= vertical_tolerance:
            current_cluster.append(box)
        else:
            # Start new cluster
            clusters.append(current_cluster)
            current_cluster = [box]
            current_y = box_y

    # Add final cluster
    if current_cluster:
        clusters.append(current_cluster)

    return clusters


def calculate_region_metrics(bbox: Tuple[int, int, int, int]) -> Dict:
    """
    Calculate metrics for a bounding box region.

    Returns:
        Dict with area, aspect_ratio, width, height
    """
    x, y, w, h = bbox
    area = w * h
    aspect_ratio = w / h if h > 0 else 0

    return {
        'area': area,
        'aspect_ratio': aspect_ratio,
        'width': w,
        'height': h,
        'x': x,
        'y': y
    }


def detect_amount_field_advanced(image_path: str, output_dir: str = "output") -> Tuple[bool, str, Optional[str], Optional[np.ndarray]]:
    """
    Enhanced amount field detection using receipt structure recognition.

    Strategies:
    1. Cluster text regions by vertical position (receipt rows)
    2. Identify largest/boldest text (amount is typically larger)
    3. Prioritize bottom 40% of receipt (total amounts are usually near bottom)
    4. Filter by size heuristics (amounts are usually larger than item names)
    5. Return cropped region for further analysis

    Args:
        image_path: Path to the receipt/screenshot/amount field image
        output_dir: Directory to save debug outputs

    Returns:
        tuple: (success: bool, verdict: str, proof_image_path: str, amount_crop: np.ndarray)
    """
    print(f"\n{'='*60}")
    print(f"GCash Receipt Forensic Analysis (Enhanced)")
    print(f"{'='*60}")
    print(f"Processing: {image_path}")

    # Create output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Load image
    original_img = cv2.imread(image_path)
    if original_img is None:
        print("❌ Error: Could not read image.")
        return False, "ERROR", None, None

    print(f"✓ Image loaded: {original_img.shape[1]}x{original_img.shape[0]} pixels")

    # Check if image is already a cropped amount field (small)
    img_height, img_width = original_img.shape[0], original_img.shape[1]
    img_area = img_height * img_width
    is_small_crop = img_area < 100000  # Less than ~316x316 pixels

    if is_small_crop:
        print(f"✓ Detected as small cropped image (likely amount field)")
        amount_crop = original_img
        detected_text = "AMOUNT_FIELD"
    else:
        # For larger images, use advanced detection
        print(f"\nAnalyzing full receipt image...")
        processed, _ = preprocess_image(original_img)
        bounding_boxes = find_text_regions(processed)

        if not bounding_boxes:
            print("❌ No text regions detected in image.")
            return False, "NO_TEXT_FOUND", None, None

        print(f"  Found {len(bounding_boxes)} text regions")

        # Strategy 1: Cluster regions by vertical position
        print(f"\n  Grouping regions by row...")
        row_clusters = cluster_regions_by_vertical_position(bounding_boxes, vertical_tolerance=15)
        print(f"  Found {len(row_clusters)} text rows")

        # Strategy 2: Calculate metrics for each region
        region_metrics = [calculate_region_metrics(box) for box in bounding_boxes]

        # Strategy 3: Focus on bottom 40% of receipt (where totals usually are)
        bottom_threshold = img_height * 0.6  # Bottom 40%
        bottom_regions_indices = [i for i, metrics in enumerate(region_metrics)
                                  if metrics['y'] > bottom_threshold]

        print(f"  Regions in bottom 40%: {len(bottom_regions_indices)}")

        # Strategy 4: Filter by size - amounts are typically larger text
        if bottom_regions_indices:
            # Get sizes of bottom regions
            bottom_sizes = [region_metrics[i]['area'] for i in bottom_regions_indices]
            size_threshold = np.median(bottom_sizes) if bottom_sizes else 0

            # Find largest text in bottom area
            largest_bottom_idx = max(bottom_regions_indices,
                                    key=lambda i: region_metrics[i]['area'])
            selected_region_idx = largest_bottom_idx
            print(f"  Selected largest region in bottom area")
        else:
            # If no regions in bottom, find largest overall
            largest_idx = max(range(len(region_metrics)),
                            key=lambda i: region_metrics[i]['area'])
            selected_region_idx = largest_idx
            print(f"  No regions in bottom area, using largest overall")

        selected_region = bounding_boxes[selected_region_idx]
        selected_metrics = region_metrics[selected_region_idx]

        x, y, w, h = selected_region

        print(f"\n  Selected region:")
        print(f"    Position: ({x}, {y})")
        print(f"    Size: {w}x{h} pixels")
        print(f"    Area: {selected_metrics['area']} sq. pixels")

        # Expand region for context
        expand_x = max(int(w * 0.5), 20)
        expand_y = max(int(h * 0.5), 20)

        x1 = max(0, x - expand_x)
        y1 = max(0, y - expand_y)
        x2 = min(img_width, x + w + expand_x)
        y2 = min(img_height, y + h + expand_y)

        amount_crop = original_img[y1:y2, x1:x2]
        detected_text = f"Region({x},{y},{w},{h})"

        # Save debug visualization
        debug_img = original_img.copy()

        # Draw all detected regions (small)
        for i, bbox in enumerate(bounding_boxes):
            bx, by, bw, bh = bbox
            color = (0, 255, 0) if i == selected_region_idx else (200, 200, 200)
            thickness = 2 if i == selected_region_idx else 1
            cv2.rectangle(debug_img, (bx, by), (bx + bw, by + bh), color, thickness)

        # Draw selected region (large)
        cv2.rectangle(debug_img, (x, y), (x + w, y + h), (0, 255, 0), 3)
        cv2.putText(debug_img, "AMOUNT", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        # Draw expansion box
        cv2.rectangle(debug_img, (x1, y1), (x2, y2), (255, 0, 0), 2)

        debug_path = os.path.join(output_dir, "debug_region_detected.jpg")
        cv2.imwrite(debug_path, debug_img)
        print(f"  ✓ Debug image: {debug_path}")

    # Save extracted amount
    crop_path = os.path.join(output_dir, "extracted_amount_field.jpg")
    cv2.imwrite(crop_path, amount_crop)
    print(f"\n✓ Amount field extracted: {crop_path}")
    print(f"  Size: {amount_crop.shape[1]}x{amount_crop.shape[0]} pixels")

    # Run typography forensics
    result_path = os.path.join(output_dir, "forensic_verdict.jpg")
    forensics_result = run_typography_forensics(amount_crop, result_path)

    # Print verdict
    print(f"\n{'='*60}")
    print(f"FINAL VERDICT: {forensics_result['verdict']}")
    print(f"{'='*60}")

    if forensics_result['reasons']:
        print("\nFindings:")
        for reason in forensics_result['reasons']:
            print(f"  ⚠️  {reason}")
    else:
        print("\n✅ No fraud indicators detected.")

    print(f"\nCharacters analyzed: {forensics_result['char_count']}")
    print(f"Average aspect ratio: {forensics_result['avg_aspect_ratio']:.2f}")

    return True, forensics_result['verdict'], result_path, amount_crop


def run_typography_forensics(image, output_path=None):
    """
    Run typography & kerning forensics on an image.

    Args:
        image: The image to analyze (BGR format)
        output_path: Optional path to save verification result

    Returns:
        Dictionary with verification results and verdict
    """
    print(f"\n--- Typography & Kerning Forensics ---")

    # Preprocess
    processed, gray = preprocess_image(image)

    # Find text regions with debugging
    print(f"  Searching for text regions...")
    bounding_boxes = find_text_regions(processed)

    print(f"  Detected {len(bounding_boxes)} characters/segments")

    # Save debug intermediate
    if len(bounding_boxes) > 0:
        debug_marked = image.copy()
        for i, (x, y, w, h) in enumerate(bounding_boxes):
            cv2.rectangle(debug_marked, (x, y), (x + w, y + h), (0, 255, 0), 1)

    if len(bounding_boxes) < 1:
        print("  ⚠️  No characters detected - trying alternative detection...")
        # Fallback: try different approach
        _, thresh = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        for c in contours:
            if cv2.contourArea(c) > 0:
                x, y, w, h = cv2.boundingRect(c)
                if w > 0 and h > 0:
                    bounding_boxes.append((x, y, w, h))

        bounding_boxes = sorted(bounding_boxes, key=lambda b: b[0])
        print(f"  Fallback found {len(bounding_boxes)} regions")

    if len(bounding_boxes) < 1:
        print("  ❌ Still no characters detected")
        return {
            'verdict': 'INCONCLUSIVE',
            'reason': 'No characters detected',
            'flags': 0,
            'reasons': [],
            'char_count': 0,
            'avg_aspect_ratio': 0,
            'proof_image': image.copy()
        }

    proof_img = image.copy()

    # --- METRIC 1: ASPECT RATIO (Font Thickness/Weight) ---
    print("\n  Font Aspect Ratios (Width/Height):")
    aspect_ratios = []
    for i, (x, y, w, h) in enumerate(bounding_boxes):
        ratio = round(w / h, 2) if h > 0 else 0
        aspect_ratios.append(ratio)

        cv2.rectangle(proof_img, (x, y), (x + w, y + h), (255, 0, 0), 1)
        cv2.putText(proof_img, str(ratio), (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
        print(f"    Char {i+1}: Ratio {ratio}")

    # --- METRIC 2: KERNING (Horizontal Space Between Characters) ---
    print("\n  Kerning (Pixel Gaps):")
    gaps = []
    for i in range(len(bounding_boxes) - 1):
        current_char_end_x = bounding_boxes[i][0] + bounding_boxes[i][2]
        next_char_start_x = bounding_boxes[i+1][0]

        gap_pixels = next_char_start_x - current_char_end_x
        gaps.append(gap_pixels)

        if len(bounding_boxes) > 2:  # Only draw if multiple chars
            mid_y = bounding_boxes[i][1] + int(bounding_boxes[i][3] / 2)
            cv2.line(proof_img, (current_char_end_x, mid_y), (next_char_start_x, mid_y), (0, 0, 255), 2)
        print(f"    Gap {i+1}: {gap_pixels}px")

    # --- FRAUD DETECTION LOGIC ---
    print("\n  Forensic Analysis:")
    fraud_flags = 0
    reasons = []

    # Rule 1: Peso Gap Check (suspicious spacing after first character)
    if gaps:
        # Check for suspiciously large first gap
        for i, gap in enumerate(gaps):
            if gap > 5 and i == 0:  # Larger threshold for very small images
                fraud_flags += 1
                reasons.append(f"Suspiciously large gap at position {i+1} ({gap}px). Manual edit likely.")
                break

    # Rule 2: Font Consistency
    if len(aspect_ratios) > 1:
        ratio_variance = max(aspect_ratios) - min(aspect_ratios)
        if ratio_variance > 0.08:  # Slightly relaxed for noisy small images
            fraud_flags += 1
            reasons.append(f"Inconsistent font weights (Variance: {ratio_variance:.2f}). Mixed fonts detected.")

    # Rule 3: Aspect Ratio Range Check
    if aspect_ratios:
        avg_ratio = sum(aspect_ratios) / len(aspect_ratios)
        # Relaxed range for various fonts
        if avg_ratio < 0.40 or avg_ratio > 1.50:
            fraud_flags += 1
            reasons.append(f"Unusual font aspect ratio ({avg_ratio:.2f}). Possible font manipulation.")

    # Determine verdict
    verdict = "FORGED" if fraud_flags > 0 else "AUTHENTIC"
    color = (0, 0, 255) if verdict == "FORGED" else (0, 255, 0)  # Red or Green

    # Stamp verdict onto image
    font_scale = max(0.3, image.shape[0] / 100)  # Scale text to image size
    cv2.putText(proof_img, f"VERDICT: {verdict}", (5, max(20, int(image.shape[0] * 0.8))),
                cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 2)

    # Save proof image if path provided
    if output_path:
        cv2.imwrite(output_path, proof_img)
        print(f"\n  ✓ Proof image saved: {output_path}")

    return {
        'verdict': verdict,
        'fraud_flags': fraud_flags,
        'reasons': reasons,
        'avg_aspect_ratio': sum(aspect_ratios) / len(aspect_ratios) if aspect_ratios else 0,
        'gap_analysis': gaps,
        'char_count': len(bounding_boxes),
        'proof_image': proof_img
    }


if __name__ == "__main__":
    # Example usage
    target_image = "fullreceiptfake2.jpg"  # Your receipt/screenshot or cropped amount image

    if os.path.exists(target_image):
        success, verdict, result_path, amount_crop = detect_amount_field_advanced(target_image)
        if success:
            print(f"\n{'='*60}")
            print(f"✅ Analysis complete!")
            print(f"   Verdict: {verdict}")
            print(f"   Results saved to: output/")
            print(f"{'='*60}")
        else:
            print(f"\n❌ Analysis failed!")
    else:
        print(f"❌ Image '{target_image}' not found.")
        print("\nUsage:")
        print("  python receipt_amount_analyzer.py")
        print("\nOr import and use programmatically:")
        print("  from receipt_amount_analyzer import detect_amount_field_advanced")
        print("  success, verdict, result, crop = detect_amount_field_advanced('your_image.jpg')")
        print("\nNote: Works with OpenCV only - no Tesseract needed!")
        print("Designed for GCash receipt forensics - optimized for small amount fields and full receipts.")
