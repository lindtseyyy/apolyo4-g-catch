from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks

from server.schemas.responses import PipelineAnalysisResponse, ErrorResponse
from server.services.analysis import AnalysisService
from server.storage import validate_upload, save_upload, cleanup, image_to_base64

router = APIRouter(prefix="/api/v1/analyze", tags=["analysis"])


@router.post(
    "/receipt",
    response_model=PipelineAnalysisResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file or parameters"},
        422: {"description": "Validation error"},
    },
    summary="Run full receipt verification pipeline (ELA + typography)",
    description=(
        "Uploads a receipt image and runs the complete forensic pipeline: "
        "Error Level Analysis (AI-generation detection) followed by "
        "typography & kerning forensics on the extracted amount field. "
        "Returns a combined verdict with individual detector details."
    ),
)
async def analyze_receipt(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Receipt image (JPEG, PNG, TIFF, BMP, WebP)"),
):
    content = await file.read()
    error = validate_upload(file.content_type or "application/octet-stream", len(content))
    if error:
        raise HTTPException(status_code=400, detail=error)

    saved_path = save_upload(content, file.filename or "upload.jpg")

    try:
        result = AnalysisService.run_pipeline_analysis(str(saved_path))

        ela_overlay = result.pop("_ela_overlay_path", None)
        ela_output = result.pop("_ela_output_path", None)
        amount_crop = result.pop("_amount_crop_path", None)
        typography_proof = result.pop("_typography_proof_path", None)

        # Use typography proof as primary; fall back to ELA overlay
        result["proof_image_base64"] = (
            image_to_base64(typography_proof) or image_to_base64(ela_overlay)
        )

        background_tasks.add_task(
            cleanup, saved_path, ela_overlay, ela_output, amount_crop, typography_proof
        )

        return result

    except ValueError as exc:
        cleanup(saved_path)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        cleanup(saved_path)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}")
