import os
import sys
import tempfile
from pathlib import Path

import numpy as np

from gcatch.detectors.ela import run_ela, detect_microscopic_noise
from gcatch.utils.image import convert_to_jpeg


_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}


def calibrate_ela_thresholds(
    real_dir,
    ai_dir,
    output_dir=None,
    variance_threshold=1.5,
    bright_threshold=30,
    ratio_margin=0.03,
    jpeg_quality=95,
    ela_alpha=8.0,
    patch_size=16,
):
    """Batch-process real and AI-generated receipts to find optimal thresholds.

    Workflow for each image:
      1. Convert to JPEG if the source is not already a JPEG.
      2. Run Error Level Analysis.
      3. Call detect_microscopic_noise() on the ELA output.
      4. Sweep variance_threshold values to maximise real/AI separation.
      5. Recommend a noisy_patch_ratio threshold with safety margin.

    Args:
        real_dir: Directory of gold-standard legitimate receipts.
        ai_dir: Directory of known AI-generated receipts.
        output_dir: Where ELA output images land (None = system temp dir).
        variance_threshold: Starting std-dev cutoff (default 1.5).
        bright_threshold: Mean brightness for content vs background.
        ratio_margin: Safety margin above max real noisy_patch_ratio.
        jpeg_quality: Quality for convert_to_jpeg.
        ela_alpha: ELA enhancement multiplier.

    Returns:
        dict with: recommended_thresholds, real_results, ai_results,
        real_summary, ai_summary, ela_output_dir.
    """
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="ela_calibrate_")

    os.makedirs(output_dir, exist_ok=True)

    real_ela_items = _generate_ela_batch(
        real_dir, output_dir, "real", jpeg_quality, ela_alpha,
    )
    ai_ela_items = _generate_ela_batch(
        ai_dir, output_dir, "ai", jpeg_quality, ela_alpha,
    )

    if not real_ela_items:
        raise RuntimeError(f"No processable images found in real_dir: {real_dir}")
    if not ai_ela_items:
        print("WARNING: No processable images found in ai_dir — "
              "thresholds will be one-sided.", file=sys.stderr)

    sweep_range = [0.5, 0.8, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
    best_vt = variance_threshold
    best_gap = -1.0

    for vt in sweep_range:
        real_max_r = 0.0
        ai_min_r = 1.0
        for item in real_ela_items:
            patch = detect_microscopic_noise(
                item["ela_output"], variance_threshold=vt,
                bright_threshold=bright_threshold,
                patch_size=patch_size,
            )
            real_max_r = max(real_max_r, patch["noisy_patch_ratio"])
        for item in ai_ela_items:
            patch = detect_microscopic_noise(
                item["ela_output"], variance_threshold=vt,
                bright_threshold=bright_threshold,
                patch_size=patch_size,
            )
            ai_min_r = min(ai_min_r, patch["noisy_patch_ratio"])
        gap = ai_min_r - real_max_r
        if gap > best_gap:
            best_gap = gap
            best_vt = vt

    real_results = _score_ela_batch(real_ela_items, best_vt, bright_threshold, patch_size)
    ai_results = _score_ela_batch(ai_ela_items, best_vt, bright_threshold, patch_size)

    max_real_ratio = max(r["noisy_patch_ratio"] for r in real_results)

    recommended = {
        "variance_threshold": best_vt,
        "bright_threshold": bright_threshold,
        "noisy_patch_ratio": round(min(max_real_ratio + ratio_margin, 1.0), 4),
        "separation_gap": round(best_gap, 4),
        "patch_size": patch_size,
    }

    real_ratios = [r["noisy_patch_ratio"] for r in real_results]
    real_flagged = [r["flagged_patches"] for r in real_results]
    real_bg = [r["background_patches"] for r in real_results]
    real_total = [r["total_patches"] for r in real_results]

    real_summary = {
        "count": len(real_results),
        "noisy_patch_ratio": {
            "min": min(real_ratios), "max": max_real_ratio,
            "avg": round(np.mean(real_ratios), 4),
        },
        "flagged_patches": {
            "min": min(real_flagged), "max": max(real_flagged),
            "avg": round(np.mean(real_flagged), 1),
        },
        "background_patches": {
            "min": min(real_bg), "max": max(real_bg),
            "avg": round(np.mean(real_bg), 1),
        },
        "total_patches": {
            "min": min(real_total), "max": max(real_total),
        },
    }

    ai_summary = {}
    if ai_results:
        ai_ratios = [r["noisy_patch_ratio"] for r in ai_results]
        ai_flagged = [r["flagged_patches"] for r in ai_results]
        ai_bg = [r["background_patches"] for r in ai_results]
        ai_total = [r["total_patches"] for r in ai_results]
        ai_summary = {
            "count": len(ai_results),
            "noisy_patch_ratio": {
                "min": min(ai_ratios), "max": max(ai_ratios),
                "avg": round(np.mean(ai_ratios), 4),
            },
            "flagged_patches": {
                "min": min(ai_flagged), "max": max(ai_flagged),
                "avg": round(np.mean(ai_flagged), 1),
            },
            "background_patches": {
                "min": min(ai_bg), "max": max(ai_bg),
                "avg": round(np.mean(ai_bg), 1),
            },
            "total_patches": {
                "min": min(ai_total), "max": max(ai_total),
            },
        }

    _print_report(real_results, ai_results, real_summary, ai_summary, recommended)

    return {
        "recommended_thresholds": recommended,
        "real_results": real_results,
        "ai_results": ai_results,
        "real_summary": real_summary,
        "ai_summary": ai_summary,
        "ela_output_dir": output_dir,
    }


def _is_image(filepath):
    return os.path.splitext(filepath)[1].lower() in _IMAGE_EXTENSIONS


def _generate_ela_batch(image_dir, output_dir, label, jpeg_quality, ela_alpha):
    items = []
    image_dir = str(image_dir)

    files = sorted(
        f for f in os.listdir(image_dir)
        if _is_image(f) and not f.startswith(".")
    )

    for filename in files:
        src_path = os.path.join(image_dir, filename)
        stem = Path(filename).stem
        ela_path = os.path.join(output_dir, f"ela_{label}_{stem}.jpg")

        try:
            ext = os.path.splitext(filename)[1].lower()
            converted = False
            if ext in (".jpg", ".jpeg"):
                work_path = src_path
            else:
                work_path = convert_to_jpeg(src_path, quality=jpeg_quality)
                converted = True

            run_ela(work_path, ela_path)

            items.append({
                "filename": filename,
                "converted": converted,
                "original_path": src_path,
                "ela_output": ela_path,
            })

        except Exception as exc:
            print(f"  SKIP {filename}: {exc}", file=sys.stderr)

        finally:
            if converted and os.path.exists(work_path):
                os.remove(work_path)

    return items


def _score_ela_batch(ela_items, variance_threshold, bright_threshold, patch_size=16):
    results = []
    for item in ela_items:
        dirname = os.path.dirname(item["ela_output"])
        basename = os.path.basename(item["ela_output"]).replace("ela_", "overlay_", 1)
        overlay_path = os.path.join(dirname, basename)
        patch = detect_microscopic_noise(
            item["ela_output"],
            original_image=item["original_path"],
            variance_threshold=variance_threshold,
            bright_threshold=bright_threshold,
            output_path=overlay_path,
            patch_size=patch_size,
        )
        results.append({
            "filename": item["filename"],
            "converted": item["converted"],
            "ela_output": item["ela_output"],
            "overlay_output": overlay_path,
            "is_ai_generated": patch["is_ai_generated"],
            "noisy_patch_ratio": patch["noisy_patch_ratio"],
            "flagged_patches": patch["flagged_patches"],
            "background_patches": patch["background_patches"],
            "total_patches": patch["total_patches"],
        })
    return results


def _print_report(real_results, ai_results, real_summary, ai_summary, recommended):
    def header(text):
        print(f"\n{'=' * 72}")
        print(f"  {text}")
        print(f"{'=' * 72}")

    def row(filename, converted, ratio, flagged, bg, total):
        flag = " *" if converted else ""
        pct = f"{ratio * 100:.1f}%"
        print(f"  {filename:<28s} {pct:>6s}  {flagged:>5d}/{bg:<5d}  "
              f"{total:>6d}{flag}")

    header("REAL RECEIPTS (Gold Standard)")
    print(f"  {'File':<28s} {'Ratio':>6s}  {'Flagged/Bg':>11s}  "
          f"{'Patches':>6s}")
    print(f"  {'-' * 66}")
    for r in real_results:
        row(r["filename"], r["converted"], r["noisy_patch_ratio"],
            r["flagged_patches"], r["background_patches"], r["total_patches"])

    header("AI-GENERATED RECEIPTS")
    print(f"  {'File':<28s} {'Ratio':>6s}  {'Flagged/Bg':>11s}  "
          f"{'Patches':>6s}")
    print(f"  {'-' * 66}")
    for r in ai_results:
        row(r["filename"], r["converted"], r["noisy_patch_ratio"],
            r["flagged_patches"], r["background_patches"], r["total_patches"])

    header("SUMMARY")
    print(f"  Real receipts processed:  {real_summary['count']}")
    print(f"  AI receipts processed:    {ai_summary.get('count', 0)}")
    print()
    print(f"  Real noisy patch ratio range:  "
          f"{real_summary['noisy_patch_ratio']['min']:.2%} – "
          f"{real_summary['noisy_patch_ratio']['max']:.2%}  "
          f"(avg {real_summary['noisy_patch_ratio']['avg']:.2%})")
    print(f"  Real flagged / bg patches:     "
          f"{real_summary['flagged_patches']['min']:.0f} – "
          f"{real_summary['flagged_patches']['max']:.0f} / "
          f"{real_summary['background_patches']['min']:.0f} – "
          f"{real_summary['background_patches']['max']:.0f}")

    if ai_summary:
        print()
        print(f"  AI noisy patch ratio range:    "
              f"{ai_summary['noisy_patch_ratio']['min']:.2%} – "
              f"{ai_summary['noisy_patch_ratio']['max']:.2%}  "
              f"(avg {ai_summary['noisy_patch_ratio']['avg']:.2%})")
        print(f"  AI flagged / bg patches:       "
              f"{ai_summary['flagged_patches']['min']:.0f} – "
              f"{ai_summary['flagged_patches']['max']:.0f} / "
              f"{ai_summary['background_patches']['min']:.0f} – "
              f"{ai_summary['background_patches']['max']:.0f}")

    header("RECOMMENDED THRESHOLDS")
    print(f"  variance_threshold  = {recommended['variance_threshold']:.2f}")
    print(f"  bright_threshold    = {recommended['bright_threshold']}")
    print(f"  noisy_patch_ratio   = {recommended['noisy_patch_ratio']:.4f} "
          f"({recommended['noisy_patch_ratio']*100:.1f}%)")
    print()
    print(f"  Usage:")
    print(f"    result = detect_microscopic_noise(")
    print(f"        ela_heatmap,")
    print(f"        variance_threshold={recommended['variance_threshold']:.2f},")
    print(f"        bright_threshold={recommended['bright_threshold']},")
    print(f"        noisy_patch_ratio={recommended['noisy_patch_ratio']:.4f},")
    print(f"        output_path='overlay.jpg',")
    print(f"    )")
    print()
