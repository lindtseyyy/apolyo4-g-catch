from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/analyze", tags=["analysis"])


@router.post(
    "/typography",
    status_code=501,
    summary="Run typography & kerning forensics (coming soon)",
)
async def analyze_typography():
    return {
        "detail": "Typography analysis is not yet implemented. Check back soon.",
        "analysis_type": "typography",
    }
