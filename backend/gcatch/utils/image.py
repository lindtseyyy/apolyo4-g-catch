import cv2
import os
import tempfile
from pathlib import Path
from typing import List, Tuple, Dict


def preprocess_image(image):
    """Preprocess image for better text detection.

    Applies CLAHE for contrast enhancement. Skips denoising for very small
    images to preserve fine features.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(4, 4))
    enhanced = clahe.apply(gray)

    img_area = image.shape[0] * image.shape[1]
    if img_area < 50000:
        return enhanced, gray

    denoised = cv2.fastNlMeansDenoising(enhanced, h=10)
    return denoised, gray


def find_text_regions(image):
    """Detect text regions using contour analysis.

    Tries multiple threshold values and returns the set that yields the
    most bounding boxes. Returns boxes sorted left-to-right.
    """
    best_boxes = []

    for thresh_val in [100, 130, 150, 170]:
        _, thresh = cv2.threshold(image, thresh_val, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        bounding_boxes = []
        for c in contours:
            area = cv2.contourArea(c)
            if area > 1:
                x, y, w, h = cv2.boundingRect(c)
                if h >= 2 and w >= 1:
                    bounding_boxes.append((x, y, w, h))

        bounding_boxes = sorted(bounding_boxes, key=lambda b: b[0])

        if len(bounding_boxes) > len(best_boxes):
            best_boxes = bounding_boxes

    return best_boxes


def cluster_regions_by_vertical_position(
    bounding_boxes: List[Tuple[int, int, int, int]],
    vertical_tolerance: int = 10,
) -> List[List[Tuple[int, int, int, int]]]:
    """Cluster text regions by vertical position (row grouping).

    Receipt items are aligned in rows — this groups bounding boxes that
    share roughly the same Y coordinate.
    """
    if not bounding_boxes:
        return []

    sorted_boxes = sorted(bounding_boxes, key=lambda b: b[1])
    clusters = []
    current_cluster = [sorted_boxes[0]]
    current_y = sorted_boxes[0][1]

    for box in sorted_boxes[1:]:
        box_y = box[1]
        if abs(box_y - current_y) <= vertical_tolerance:
            current_cluster.append(box)
        else:
            clusters.append(current_cluster)
            current_cluster = [box]
            current_y = box_y

    if current_cluster:
        clusters.append(current_cluster)

    return clusters


def calculate_region_metrics(bbox: Tuple[int, int, int, int]) -> Dict:
    """Calculate metrics for a bounding box region."""
    x, y, w, h = bbox
    area = w * h
    aspect_ratio = w / h if h > 0 else 0

    return {
        'area': area,
        'aspect_ratio': aspect_ratio,
        'width': w,
        'height': h,
        'x': x,
        'y': y,
    }


def convert_to_jpeg(input_image, output_path=None, quality=95):
    """Convert any image to JPEG format for ELA compatibility.

    Handles alpha-channel stripping (RGBA / BGRA → BGR). Accepts a file
    path (str / Path) or an in-memory numpy array.

    Returns:
        Absolute path to the saved JPEG file.
    """
    if isinstance(input_image, (str, Path)):
        img = cv2.imread(str(input_image), cv2.IMREAD_UNCHANGED)
        if img is None:
            raise ValueError(f"Could not read image: {input_image}")
    else:
        img = input_image.copy()

    if len(img.shape) == 3 and img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix=".jpg", prefix="ela_convert_")
        os.close(fd)

    output_path = str(output_path)
    if not output_path.lower().endswith((".jpg", ".jpeg")):
        output_path += ".jpg"

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    cv2.imwrite(output_path, img, [cv2.IMWRITE_JPEG_QUALITY, int(quality)])
    return os.path.abspath(output_path)
