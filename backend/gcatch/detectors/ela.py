import cv2
import numpy as np
import os
from skimage.measure import shannon_entropy

DEFAULT_PATCH_SIZE = 16


def run_ela(image_path, output_path, quality=90):
    """Run Error Level Analysis on an image.

    Encodes the image at a known JPEG quality in memory, decodes it back,
    and computes the absolute difference. The result is an enhanced
    error-level map.

    Uses an in-memory buffer instead of a temp file so it works on
    read-only filesystems (e.g. Vercel serverless).
    """
    original = cv2.imread(image_path)
    if original is None:
        raise ValueError(f"Could not read image: {image_path}")

    # In-memory JPEG round-trip (no temp file needed)
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 95]
    success, buf = cv2.imencode('.jpg', original, encode_param)
    if not success:
        raise ValueError("JPEG encoding failed during ELA")
    compressed = cv2.imdecode(buf, cv2.IMREAD_COLOR)

    diff = cv2.absdiff(original, compressed)
    gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    enhanced_map = cv2.convertScaleAbs(gray_diff, alpha=8.0)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    cv2.imwrite(output_path, enhanced_map)

    return True


def detect_microscopic_noise(
    ela_heatmap,
    original_image=None,
    variance_threshold=0.5,
    bright_threshold=10,
    noisy_patch_ratio=0.2147,
    output_path=None,
    patch_size=None,
):
    """Microscopic Patch-Based Variance Analysis for AI receipt detection.

    Divides the ELA heatmap into NxN patches (default 16×16), isolates
    background (low-mean) patches, and flags any with abnormally high pixel
    variance. AI-generated receipts show microscopic grain in flat areas
    that legitimate screenshots do not.

    Args:
        ela_heatmap: ELA output — numpy array (BGR or grayscale) or file path.
        original_image: Optional original receipt for visual proof overlay.
        variance_threshold: Std-dev cutoff for flagging a background patch.
        bright_threshold: Mean brightness above which a patch is considered
            content rather than background.
        noisy_patch_ratio: Fraction of background patches that must be noisy
            to trigger is_ai_generated.
        output_path: If set, saves the visual proof image to this path.
        patch_size: Side length of the square analysis patch in pixels
            (default: DEFAULT_PATCH_SIZE = 16).

    Returns:
        dict with keys: is_ai_generated, noisy_patch_ratio, total_patches,
        background_patches, flagged_patches, flagged_patch_coords,
        visual_proof, thresholds.
    """
    if patch_size is None:
        patch_size = DEFAULT_PATCH_SIZE
    if isinstance(ela_heatmap, str):
        ela_img = cv2.imread(ela_heatmap, cv2.IMREAD_UNCHANGED)
        if ela_img is None:
            raise ValueError(f"Could not read ELA image: {ela_heatmap}")
    else:
        ela_img = ela_heatmap.copy()

    if len(ela_img.shape) == 3:
        gray = cv2.cvtColor(ela_img, cv2.COLOR_BGR2GRAY)
    else:
        gray = ela_img

    visual_proof = None
    if original_image is not None:
        if isinstance(original_image, str):
            visual_proof = cv2.imread(original_image)
            if visual_proof is None:
                raise ValueError(f"Could not read original image: {original_image}")
        else:
            visual_proof = original_image.copy()

    ps = patch_size
    h, w = gray.shape
    h_trim = (h // ps) * ps
    w_trim = (w // ps) * ps
    gray_trim = gray[:h_trim, :w_trim]

    if h_trim == 0 or w_trim == 0:
        return {
            "is_ai_generated": False,
            "noisy_patch_ratio": 0.0,
            "total_patches": 0,
            "background_patches": 0,
            "flagged_patches": 0,
            "flagged_patch_coords": [],
            "visual_proof": visual_proof,
            "thresholds": {
                "variance_threshold": variance_threshold,
                "bright_threshold": bright_threshold,
                "noisy_patch_ratio": noisy_patch_ratio,
            },
        }

    n_rows = h_trim // ps
    n_cols = w_trim // ps
    patches = gray_trim.reshape(n_rows, ps, n_cols, ps).transpose(0, 2, 1, 3)

    patch_means = patches.mean(axis=(2, 3))
    patch_stds = patches.std(axis=(2, 3))

    background_mask = patch_means <= bright_threshold
    total_background = int(background_mask.sum())

    noisy_mask = background_mask & (patch_stds > variance_threshold)
    flagged_count = int(noisy_mask.sum())

    total_patches = n_rows * n_cols
    ratio = flagged_count / max(total_background, 1)

    is_ai_generated = bool(ratio > noisy_patch_ratio)

    flagged_rows, flagged_cols = np.where(noisy_mask)
    flagged_coords = [(int(c) * ps, int(r) * ps)
                      for r, c in zip(flagged_rows, flagged_cols)]

    if visual_proof is not None:
        if visual_proof.shape[:2] != (h_trim, w_trim):
            visual_proof = visual_proof[:h_trim, :w_trim]

        overlay = visual_proof.copy()
        for x, y in flagged_coords:
            cv2.rectangle(overlay, (x, y), (x + ps, y + ps), (0, 0, 255), -1)

        alpha = 0.35
        visual_proof = cv2.addWeighted(overlay, alpha, visual_proof, 1 - alpha, 0)

        if output_path is not None:
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            cv2.imwrite(output_path, visual_proof)

    return {
        "is_ai_generated": is_ai_generated,
        "noisy_patch_ratio": round(ratio, 4),
        "total_patches": total_patches,
        "background_patches": total_background,
        "flagged_patches": flagged_count,
        "flagged_patch_coords": flagged_coords,
        "visual_proof": visual_proof,
        "thresholds": {
            "variance_threshold": variance_threshold,
            "bright_threshold": bright_threshold,
            "noisy_patch_ratio": noisy_patch_ratio,
            "patch_size": patch_size,
        },
    }


def calculate_ela_integrity(raw_score, threshold):
    """Normalize raw noisy-patch ratio into a user-facing 0-100 % integrity score.

    Dual-zone linear mapping anchored to the detection threshold:

      * Clean Floor (raw_score <= 0.02)         → 100 % integrity
      * Threshold   (raw_score == threshold)    →  75 % integrity  ("Passing Grade")
      * Max Noise   (raw_score >= thresh * 4.0) →   0 % integrity

    Zone A  [0.02 … threshold]      100 % → 75 %   (tolerates Messenger compression)
    Zone B  (threshold … thresh*4.0)  75 % →  0 %   (forgery / artifact region)
    """
    CLEAN_FLOOR = 0.02
    max_noise = threshold * 4.0

    if raw_score <= CLEAN_FLOOR:
        return 100.0
    if raw_score >= max_noise:
        return 0.0

    if raw_score <= threshold:
        integrity = 100.0 - (raw_score - CLEAN_FLOOR) / (threshold - CLEAN_FLOOR) * 25.0
    else:
        integrity = 75.0 - (raw_score - threshold) / (max_noise - threshold) * 75.0

    return round(max(0.0, min(100.0, integrity)), 1)


def calculate_noise_score(
    ela_image,
    mean_threshold=5.0,
    entropy_threshold=2.5,
    noise_floor=10,
    variance_threshold=0.5,
    bright_threshold=10,
    noisy_patch_ratio=0.2147,
    patch_size=None,
):
    """Quantify noise in an ELA heatmap and detect AI-generated receipts.

    Returns a composite 0–100 noise_score along with per-patch breakdown
    and global statistics.
    """
    if isinstance(ela_image, str):
        ela_image = cv2.imread(ela_image)
        if ela_image is None:
            raise ValueError(f"Could not read image from path: {ela_image}")

    if len(ela_image.shape) == 3:
        gray = cv2.cvtColor(ela_image, cv2.COLOR_BGR2GRAY)
    else:
        gray = ela_image.copy()

    mean_val = float(np.mean(gray))
    std_val = float(np.std(gray))
    entropy = float(shannon_entropy(gray))

    total_pixels = gray.size
    noisy_pixels = np.count_nonzero(gray > noise_floor)
    noise_density = (noisy_pixels / total_pixels) * 100.0

    patch_result = detect_microscopic_noise(
        ela_image,
        variance_threshold=variance_threshold,
        bright_threshold=bright_threshold,
        noisy_patch_ratio=noisy_patch_ratio,
        patch_size=patch_size,
    )

    noise_score = round(patch_result["noisy_patch_ratio"] * 100.0, 1)

    return {
        "noise_score": noise_score,
        "is_ai_suspected": patch_result["is_ai_generated"],
        "mean_brightness": round(mean_val, 2),
        "std_brightness": round(std_val, 2),
        "entropy": round(entropy, 4),
        "noise_density_pct": round(noise_density, 2),
        "patch_stats": {
            "flagged_patches": patch_result["flagged_patches"],
            "background_patches": patch_result["background_patches"],
            "total_patches": patch_result["total_patches"],
            "noisy_patch_ratio": patch_result["noisy_patch_ratio"],
        },
        "thresholds": {
            "variance_threshold": variance_threshold,
            "bright_threshold": bright_threshold,
            "noisy_patch_ratio": noisy_patch_ratio,
            "noise_floor": noise_floor,
            "patch_size": patch_size if patch_size is not None else DEFAULT_PATCH_SIZE,
        },
    }
