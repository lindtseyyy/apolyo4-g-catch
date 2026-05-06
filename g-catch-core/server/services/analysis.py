import time
from typing import Any, Dict

from gcatch.detectors.ela import run_ela, calculate_noise_score, detect_microscopic_noise
from gcatch.utils.image import convert_to_jpeg

from server.config import ELA_THRESHOLDS
from server.storage import OUTPUT_DIR


class AnalysisService:
    """Orchestration layer between FastAPI routers and gcatch detectors.

    Normalizes return shapes, handles file I/O for intermediate outputs,
    and provides a registry for adding new detector types.
    """

    _analyzers: Dict[str, str] = {}

    @classmethod
    def register(cls, name: str):
        """Decorator to register an analysis function under a given name."""
        def decorator(func):
            cls._analyzers[name] = name
            return func
        return decorator

    @classmethod
    def available_analyzers(cls):
        """Return the list of registered analyzer names."""
        return sorted(cls._analyzers.keys())

    @staticmethod
    def run_ela_analysis(file_path: str) -> Dict[str, Any]:
        """Run full ELA pipeline on a receipt image.

        Thresholds are read from server/config.py.

        Steps:
          1. Convert to JPEG if needed (ELA requires JPEG compression baseline).
          2. Generate the ELA heatmap.
          3. Run noise-score analysis + generate visual overlay.

        Returns:
            Dict ready to pass to ELAAnalysisResponse(**result).
        """
        t0 = time.perf_counter()

        variance_threshold = ELA_THRESHOLDS["variance_threshold"]
        bright_threshold = ELA_THRESHOLDS["bright_threshold"]
        noisy_patch_ratio = ELA_THRESHOLDS["noisy_patch_ratio"]
        patch_size = ELA_THRESHOLDS["patch_size"]

        # Ensure JPEG for ELA
        ext = file_path.lower().rsplit(".", 1)[-1] if "." in file_path else ""
        if ext in ("jpg", "jpeg"):
            work_path = file_path
            converted = False
        else:
            work_path = convert_to_jpeg(file_path)
            converted = True

        # Step 1: ELA heatmap
        ela_output = str(OUTPUT_DIR / f"ela_{id(work_path)}.jpg")
        run_ela(work_path, ela_output)

        # Step 2: Noise scoring
        noise_result = calculate_noise_score(
            ela_output,
            variance_threshold=variance_threshold,
            bright_threshold=bright_threshold,
            noisy_patch_ratio=noisy_patch_ratio,
            patch_size=patch_size,
        )

        # Step 3: Generate visual proof overlay (red patches on original image)
        overlay_output = str(OUTPUT_DIR / f"overlay_{id(work_path)}.jpg")
        overlay_result = detect_microscopic_noise(
            ela_output,
            original_image=file_path,
            variance_threshold=variance_threshold,
            bright_threshold=bright_threshold,
            noisy_patch_ratio=noisy_patch_ratio,
            output_path=overlay_output,
            patch_size=patch_size,
        )

        duration_ms = round((time.perf_counter() - t0) * 1000, 1)

        verdict = "FORGED" if noise_result["is_ai_suspected"] else "AUTHENTIC"

        return {
            "verdict": verdict,
            "duration_ms": duration_ms,
            "is_ai_generated": noise_result["is_ai_suspected"],
            "noise_score": noise_result["noise_score"],
            "noisy_patch_ratio": noise_result["patch_stats"]["noisy_patch_ratio"],
            "flagged_patches": noise_result["patch_stats"]["flagged_patches"],
            "background_patches": noise_result["patch_stats"]["background_patches"],
            "total_patches": noise_result["patch_stats"]["total_patches"],
            "mean_brightness": noise_result["mean_brightness"],
            "std_brightness": noise_result["std_brightness"],
            "entropy": noise_result["entropy"],
            "noise_density_pct": noise_result["noise_density_pct"],
            "thresholds_used": {
                "variance_threshold": variance_threshold,
                "bright_threshold": bright_threshold,
                "noisy_patch_ratio": noisy_patch_ratio,
                "patch_size": patch_size,
            },
            "patch_stats": {
                "flagged_patches": noise_result["patch_stats"]["flagged_patches"],
                "background_patches": noise_result["patch_stats"]["background_patches"],
                "total_patches": noise_result["patch_stats"]["total_patches"],
                "noisy_patch_ratio": noise_result["patch_stats"]["noisy_patch_ratio"],
            },
            "proof_image_base64": None,  # filled by router
            "_overlay_path": overlay_output,
            "_ela_output": ela_output,
        }


# Register ELA so it shows up in available_analyzers()
AnalysisService.register("ela")(AnalysisService.run_ela_analysis)
