import time
from typing import Any, Dict

from gcatch.detectors.ela import (
    run_ela,
    calculate_noise_score,
    calculate_ela_integrity,
    detect_microscopic_noise,
)
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

        ela_integrity_score = calculate_ela_integrity(
            noise_result["patch_stats"]["noisy_patch_ratio"],
            noisy_patch_ratio,
        )

        return {
            "verdict": verdict,
            "duration_ms": duration_ms,
            "is_ai_generated": noise_result["is_ai_suspected"],
            "noise_score": noise_result["noise_score"],
            "ela_integrity_score": ela_integrity_score,
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


    @staticmethod
    def run_typography_analysis(file_path: str) -> Dict[str, Any]:
        """Run per-field typography forensics on a receipt image.

        Extracts all recognizable fields and runs the appropriate typography
        analysis on each crop (amount checker for ₱ fields, digit checker
        for ref#/phone, general checker for name/date).

        Returns:
            Dict ready to pass to TypographyAnalysisResponse(**result).
        """
        t0 = time.perf_counter()

        from gcatch.pipeline.receipt_scanner import verify_receipt

        result = verify_receipt(file_path)

        duration_ms = round((time.perf_counter() - t0) * 1000, 1)

        total_score = sum(
            f["score"] for f in result["fields"].values()
        )

        return {
            "verdict": result["verdict"],
            "duration_ms": duration_ms,
            "fraud_score": float(total_score),
            "reasons": result["reasons"],
            "char_count": None,
            "avg_aspect_ratio": None,
            "gap_analysis": [],
            "symbol_check": None,
            "proof_image_base64": None,
            "typography_integrity_score": result.get("typography_integrity_score", 100.0),
            "penalty_summary": result.get("penalty_summary", []),
            "_fields": result["fields"],
            "_forged_fields": result["forged_fields"],
            "_proof_paths": result.get("proof_paths", {}),
        }

    @staticmethod
    def run_pipeline_analysis(file_path: str) -> Dict[str, Any]:
        """Run combined ELA + typography pipeline on a receipt image.

        Steps:
          1. Run ELA analysis (noise detection).
          2. Run typography analysis on the extracted amount field.
          3. Combine verdicts.

        Returns:
            Dict ready to pass to PipelineAnalysisResponse(**result).
        """
        t0 = time.perf_counter()

        # Step 1: ELA
        ela_result = AnalysisService.run_ela_analysis(file_path)
        ela_overlay_path = ela_result.pop("_overlay_path", None)
        ela_output_path = ela_result.pop("_ela_output", None)

        # Step 2: Per-field typography
        typography_result = AnalysisService.run_typography_analysis(file_path)
        fields = typography_result.pop("_fields", {})
        forged_fields = typography_result.pop("_forged_fields", [])
        proof_paths = typography_result.pop("_proof_paths", {})
        typography_integrity_score = typography_result.get("typography_integrity_score", 100.0)
        penalty_summary = typography_result.get("penalty_summary", [])

        duration_ms = round((time.perf_counter() - t0) * 1000, 1)

        # Step 3: Combined verdict
        ela_forged = ela_result["verdict"] == "FORGED"
        typography_forged = typography_result["verdict"] == "FORGED"
        typography_inconclusive = typography_result["verdict"] == "INCONCLUSIVE"

        if ela_forged or typography_forged:
            combined_verdict = "FORGED"
        elif typography_inconclusive and not ela_forged:
            combined_verdict = "INCONCLUSIVE"
        else:
            combined_verdict = "AUTHENTIC"

        return {
            "analysis_type": "pipeline",
            "verdict": combined_verdict,
            "duration_ms": duration_ms,
            "ela_verdict": ela_result["verdict"],
            "ela_is_ai_generated": ela_result["is_ai_generated"],
            "ela_noise_score": ela_result["noise_score"],
            "ela_integrity_score": ela_result["ela_integrity_score"],
            "fields": fields,
            "forged_fields": forged_fields,
            "typography_reasons": typography_result["reasons"],
            "typography_integrity_score": typography_integrity_score,
            "penalty_summary": penalty_summary,
            "combined_verdict": combined_verdict,
            "proof_image_base64": None,
            "_ela_overlay_path": ela_overlay_path,
            "_ela_output_path": ela_output_path,
            "_typography_proof_paths": proof_paths,
        }


AnalysisService.register("pipeline")(AnalysisService.run_pipeline_analysis)
