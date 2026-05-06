"""GCash receipt forensic scanner.

Pipeline: extract all fields from the receipt using OCR-based cropping,
then run per-field typography forensics to detect tampering.
"""

import os

import cv2

from gcatch.detectors.typography import (
    analyze_amount_typography,
    analyze_digit_typography,
    analyze_reference_number,
    analyze_typography,
)
from gcatch.pipeline.receipt_cropper import extract_all_field_crops

# Map each field to the appropriate typography checker.
FIELD_CHECKERS = {
    "name": analyze_typography,
    "phone_number": analyze_digit_typography,
    "amount": analyze_amount_typography,
    "total_amount": analyze_amount_typography,
    "reference_number": analyze_reference_number,
    "date": analyze_typography,
}


def verify_receipt(image_path, output_dir=None):
    """Full receipt verification pipeline — checks every field.

    Steps:
        1. Extract all recognizable fields from the receipt using white-card
           detection + OCR label matching.
        2. Run the appropriate typography analysis on each field crop.
        3. Aggregate per-field results into a combined verdict.

    Args:
        image_path: Path to the receipt image.
        output_dir: Optional directory for saving field crops and proof
            images. If None, no files are written.

    Returns:
        dict with keys: verdict, fields, forged_fields, proof_paths.
    """
    field_crops = extract_all_field_crops(image_path)

    if not field_crops:
        return {
            "verdict": "INCONCLUSIVE",
            "fields": {},
            "forged_fields": [],
            "reasons": ["No fields could be extracted from the receipt"],
        }

    field_results = {}
    forged_fields = []
    all_reasons = []

    proof_paths = {}

    for field_name, (crop, ocr_text) in field_crops.items():
        checker = FIELD_CHECKERS.get(field_name, analyze_typography)

        proof_path = None
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            stem = os.path.splitext(os.path.basename(image_path))[0]
            proof_path = os.path.join(
                output_dir, f"{stem}__{field_name}_proof.jpg"
            )
            proof_paths[field_name] = proof_path

        result = checker(crop, proof_path)

        verdict = result["verdict"]
        score = result.get("score", result.get("fraud_flags", 0))
        reasons = result.get("reasons", [])

        field_results[field_name] = {
            "verdict": verdict,
            "score": score,
            "reasons": reasons,
            "text": ocr_text,
        }

        if "FAIL" in verdict or verdict == "FORGED":
            forged_fields.append(field_name)
            all_reasons.extend(
                f"[{field_name}] {r}" for r in reasons
            )

    if not forged_fields:
        combined_verdict = "AUTHENTIC"
    else:
        combined_verdict = "FORGED"

    return {
        "verdict": combined_verdict,
        "fields": field_results,
        "forged_fields": forged_fields,
        "reasons": all_reasons,
        "proof_paths": proof_paths if output_dir else {},
    }


def scan_receipt(image_path, output_path=None):
    """Run the receipt verification pipeline and return a flat result.

    Thin wrapper around verify_receipt for CLI and backward compatibility.
    """
    output_dir = os.path.dirname(output_path) if output_path else None
    result = verify_receipt(image_path, output_dir=output_dir)

    total_flags = sum(
        f["score"] for f in result["fields"].values()
        if "FAIL" in f["verdict"] or f["verdict"] == "FORGED"
    )

    return {
        "verdict": result["verdict"],
        "flags": total_flags,
        "reasons": result["reasons"],
        "fields": result["fields"],
        "forged_fields": result["forged_fields"],
        "proof_image_path": output_path,
    }
