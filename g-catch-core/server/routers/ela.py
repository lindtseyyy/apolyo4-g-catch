from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks

from server.schemas.responses import ELAAnalysisResponse, ErrorResponse
from server.services.analysis import AnalysisService
from server.storage import validate_upload, save_upload, cleanup, image_to_base64

router = APIRouter(prefix="/api/v1/analyze", tags=["analysis"])


@router.post(
    "/ela",
    response_model=ELAAnalysisResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file or parameters"},
        422: {"description": "Validation error"},
    },
    summary="Run Error Level Analysis on a receipt image",
    description=(
        "Uploads a receipt image, runs Error Level Analysis (ELA), and returns "
        "a verdict on whether the receipt appears AI-generated based on "
        "microscopic patch-based noise detection."
    ),
)
async def analyze_ela(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Receipt image (JPEG, PNG, TIFF, BMP, WebP)"),
):
    # Validate the uploaded file
    content = await file.read()
    error = validate_upload(file.content_type or "application/octet-stream", len(content))
    if error:
        raise HTTPException(status_code=400, detail=error)

    # Save to disk
    saved_path = save_upload(content, file.filename or "upload.jpg")

    try:
        # Run the analysis (thresholds are configured in server/config.py)
        result = AnalysisService.run_ela_analysis(str(saved_path))

        # Encode the visual proof overlay as base64 (red-highlighted on original)
        overlay_path = result.pop("_overlay_path", None)
        ela_output = result.pop("_ela_output", None)
        result["proof_image_base64"] = image_to_base64(overlay_path)

        # Schedule cleanup of temp files
        background_tasks.add_task(cleanup, saved_path, ela_output, overlay_path)

        return result

    except ValueError as exc:
        cleanup(saved_path)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        cleanup(saved_path)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}")
