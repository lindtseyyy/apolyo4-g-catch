from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/analyze", tags=["analysis"])


@router.post(
    "/receipt",
    status_code=501,
    summary="Run combined receipt forensics pipeline (coming soon)",
)
async def analyze_receipt():
    return {
        "detail": "Full receipt pipeline is not yet implemented. Check back soon.",
        "analysis_type": "pipeline",
    }
