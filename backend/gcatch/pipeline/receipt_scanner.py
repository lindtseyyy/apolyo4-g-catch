"""GCash receipt forensic scanner.

Pipeline: extract the total-amount field from the receipt using OCR-based
cropping, then run typography forensics on that crop to detect tampering.
"""

import os

import cv2

from gcatch.detectors.typography import analyze_amount_typography
from gcatch.pipeline.receipt_cropper import extract_total_amount_field_from_receipt


def verify_receipt(image_path, output_dir=None):
    """Full receipt verification pipeline.

    Steps:
        1. Extract the Total Amount field from the receipt using white-card
           detection + OCR label matching.
        2. Run advanced amount typography analysis on the crop.
        3. Return combined results.

    Args:
        image_path: Path to the receipt image.
        output_dir: Optional directory for saving the amount crop and proof
            image. If None, no files are written.

    Returns:
        dict with keys: verdict, score, reasons, amount_text,
        amount_crop_path, proof_path, typography_result.
    """
    total_crop, total_text = extract_total_amount_field_from_receipt(image_path)

    if total_crop is None:
        return {
            "verdict": "INCONCLUSIVE",
            "score": 0,
            "reasons": ["Could not locate Total Amount field in receipt"],
            "amount_text": None,
            "amount_crop_path": None,
            "proof_path": None,
            "typography_result": None,
        }

    amount_crop_path = None
    proof_path = None

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        stem = os.path.splitext(os.path.basename(image_path))[0]
        amount_crop_path = os.path.join(output_dir, f"{stem}__total_amount.jpg")
        cv2.imwrite(amount_crop_path, total_crop)
        proof_path = os.path.join(output_dir, f"{stem}__typography_proof.jpg")

    typography_result = analyze_amount_typography(total_crop, proof_path)

    return {
        "verdict": typography_result["verdict"],
        "score": typography_result["score"],
        "reasons": typography_result["reasons"],
        "amount_text": total_text,
        "amount_crop_path": amount_crop_path,
        "proof_path": proof_path,
        "typography_result": typography_result,
    }


def scan_receipt(image_path, output_path=None):
    """Run the receipt verification pipeline and return a flat result.

    Thin wrapper around verify_receipt for CLI and backward compatibility.
    """
    output_dir = os.path.dirname(output_path) if output_path else None
    result = verify_receipt(image_path, output_dir=output_dir)

    flags = result["score"] if result["verdict"] != "INCONCLUSIVE" else 0

    return {
        "verdict": result["verdict"],
        "flags": flags,
        "reasons": result["reasons"],
        "proof_image_path": result["proof_path"],
    }
