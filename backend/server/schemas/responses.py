from typing import Optional

from pydantic import BaseModel, Field


class BaseAnalysisResponse(BaseModel):
    """Common fields returned by every forensic analysis endpoint."""

    analysis_type: str = Field(description="The detector used, e.g. 'ela', 'typography', 'alignment'.")
    verdict: str = Field(description="Overall verdict: AUTHENTIC, FORGED, or INCONCLUSIVE.")
    duration_ms: float = Field(description="Wall-clock time the analysis took, in milliseconds.")
    proof_image_base64: Optional[str] = Field(
        default=None,
        description="Annotated proof image as a base64-encoded data URI (JPEG).",
    )


class ThresholdsUsed(BaseModel):
    """The threshold values actually applied for this analysis run."""

    variance_threshold: float
    bright_threshold: float
    noisy_patch_ratio: float
    patch_size: int


class PatchStats(BaseModel):
    """Per-patch breakdown from microscopic noise detection."""

    flagged_patches: int
    background_patches: int
    total_patches: int
    noisy_patch_ratio: float


class ELAAnalysisResponse(BaseAnalysisResponse):
    """ELA-specific analysis result."""

    analysis_type: str = "ela"
    is_ai_generated: bool = Field(description="Whether the receipt appears AI-generated.")
    noise_score: float = Field(description="Composite 0–100 noise score.")
    noisy_patch_ratio: float = Field(description="Fraction of background patches flagged as noisy.")
    flagged_patches: int
    background_patches: int
    total_patches: int
    mean_brightness: float
    std_brightness: float
    entropy: float
    noise_density_pct: float
    thresholds_used: ThresholdsUsed
    patch_stats: PatchStats


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"


class ErrorResponse(BaseModel):
    detail: str
    error_code: str
