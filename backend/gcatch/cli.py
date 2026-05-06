"""Unified command-line interface for G-Catch forensic tools.

Usage:
    python -m gcatch.cli ela IMAGE [--output OUTPUT]
    python -m gcatch.cli typography IMAGE [--output OUTPUT]
    python -m gcatch.cli alignment IMAGE [--output OUTPUT]
    python -m gcatch.cli scan-receipt IMAGE [--output OUTPUT]
    python -m gcatch.cli calibrate --real DIR --ai DIR [--output DIR]
    python -m gcatch.cli process-screenshot IMAGE [--output DIR]
    python -m gcatch.cli verify IMAGE [--output DIR]
"""

import argparse
import os
import sys


def cmd_ela(args):
    from gcatch.detectors.ela import run_ela, detect_microscopic_noise
    from gcatch.utils.image import convert_to_jpeg

    ext = os.path.splitext(args.image)[1].lower()
    if ext in (".jpg", ".jpeg"):
        work_image = args.image
    else:
        work_image = convert_to_jpeg(args.image)

    ela_out = args.output or "ela_output.jpg"
    overlay_out = os.path.splitext(ela_out)[0] + "_overlay.jpg"

    run_ela(work_image, ela_out)
    result = detect_microscopic_noise(
        ela_out,
        original_image=args.image,
        output_path=overlay_out,
    )

    print(f"\n{'='*50}")
    print(f"  Receipt: {args.image}")
    print(f"{'='*50}")
    print(f"  AI Generated:       {result['is_ai_generated']}")
    print(f"  Noisy BG Ratio:     {result['noisy_patch_ratio']:.2%}")
    print(f"  Flagged / BG:       {result['flagged_patches']} / "
          f"{result['background_patches']} patches")
    print(f"  Total Patches:      {result['total_patches']}")
    if result['flagged_patches']:
        print(f"\n  Visual proof saved: {overlay_out}")


def cmd_typography(args):
    from gcatch.detectors.typography import analyze_typography

    output = args.output or "typography_result.jpg"
    result = analyze_typography(args.image, output)
    print(f"\nVerdict: {result['verdict']}")
    for r in result['reasons']:
        print(f"  - {r}")
    print(f"Proof saved: {output}")


def cmd_alignment(args):
    from gcatch.detectors.alignment import check_alignment

    output = args.output or "alignment_result.jpg"
    result = check_alignment(args.image, output)
    print(f"\nVerdict: {result['verdict']}")
    print(f"Drift: {result['drift_pixels']}px across {result['char_count']} chars")
    for r in result['reasons']:
        print(f"  - {r}")


def cmd_scan_receipt(args):
    from gcatch.pipeline.receipt_scanner import scan_receipt

    output = args.output or "forensic_result.jpg"
    result = scan_receipt(args.image, output)
    return result


def cmd_calibrate(args):
    from gcatch.utils.calibration import calibrate_ela_thresholds

    result = calibrate_ela_thresholds(
        real_dir=args.real,
        ai_dir=args.ai,
        output_dir=args.output,
        patch_size=args.patch_size,
    )
    print(f"\nELA outputs saved to: {result['ela_output_dir']}")


def cmd_process_screenshot(args):
    from gcatch.pipeline.screenshot_processor import ScreenshotProcessor

    processor = ScreenshotProcessor()
    output = args.output or "results"
    results = processor.process_full_screenshot(args.image, output)
    if results:
        print("\n" + "=" * 60)
        print("PROCESSING COMPLETE")
        print("=" * 60)
        print(f"Results saved to: {output}/")
        print(f"Check VERIFICATION_REPORT.txt for detailed analysis")
    else:
        print("Processing failed.")


def cmd_verify(args):
    from gcatch.pipeline.receipt_scanner import verify_receipt

    output = args.output or None
    result = verify_receipt(args.image, output_dir=output)

    print(f"\n{'='*50}")
    print(f"  Receipt Verification")
    print(f"  Image: {args.image}")
    print(f"{'='*50}")
    print(f"  Amount text:  {result['amount_text'] or 'NOT FOUND'}")
    print(f"  Verdict:      {result['verdict']}")
    print(f"  Score:        {result['score']:.0f}")

    if result['reasons']:
        print(f"\n  Findings:")
        for r in result['reasons']:
            print(f"    - {r}")

    if result['amount_crop_path']:
        print(f"\n  Amount crop:  {result['amount_crop_path']}")
    if result['proof_path']:
        print(f"  Proof image:  {result['proof_path']}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="G-Catch Receipt Forensics Toolkit",
        prog="gcatch",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_ela = sub.add_parser("ela", help="Run Error Level Analysis")
    p_ela.add_argument("image", help="Path to receipt image")
    p_ela.add_argument("--output", "-o", help="Output path for ELA heatmap")
    p_ela.set_defaults(func=cmd_ela)

    p_typ = sub.add_parser("typography", help="Run typography & kerning forensics")
    p_typ.add_argument("image", help="Path to amount-field image")
    p_typ.add_argument("--output", "-o", help="Output path for proof image")
    p_typ.set_defaults(func=cmd_typography)

    p_align = sub.add_parser("alignment", help="Run micro-alignment forensics")
    p_align.add_argument("image", help="Path to amount-field image")
    p_align.add_argument("--output", "-o", help="Output path for proof image")
    p_align.set_defaults(func=cmd_alignment)

    p_scan = sub.add_parser("scan-receipt", help="Full receipt forensic scan")
    p_scan.add_argument("image", help="Path to receipt image")
    p_scan.add_argument("--output", "-o", help="Output path for proof image")
    p_scan.set_defaults(func=cmd_scan_receipt)

    p_cal = sub.add_parser("calibrate", help="Calibrate ELA thresholds")
    p_cal.add_argument("--real", required=True, help="Directory of real receipts")
    p_cal.add_argument("--ai", required=True, help="Directory of AI-generated receipts")
    p_cal.add_argument("--output", "-o", help="Output directory")
    p_cal.add_argument("--patch-size", type=int, default=16,
                       help="Patch size for analysis (default: 16)")
    p_cal.set_defaults(func=cmd_calibrate)

    p_ss = sub.add_parser("process-screenshot", help="OCR-based screenshot pipeline")
    p_ss.add_argument("image", help="Path to screenshot/receipt image")
    p_ss.add_argument("--output", "-o", help="Output directory")
    p_ss.set_defaults(func=cmd_process_screenshot)

    p_verify = sub.add_parser("verify", help="Full receipt verification (amount extraction + typography)")
    p_verify.add_argument("image", help="Path to receipt image")
    p_verify.add_argument("--output", "-o", help="Output directory for crops and proof images")
    p_verify.set_defaults(func=cmd_verify)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
