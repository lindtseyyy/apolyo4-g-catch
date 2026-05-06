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


class FieldResult(BaseModel):
    """Per-field typography analysis result."""

    verdict: str = Field(description="Field-level verdict: PASS: REAL, FAIL: FAKE, AUTHENTIC, FORGED, or INCONCLUSIVE.")
    score: float = Field(description="Fraud score for this field.")
    reasons: list[str] = Field(default_factory=list, description="Findings specific to this field.")
    text: Optional[str] = Field(default=None, description="OCR-extracted text for this field.")


class TypographyAnalysisResponse(BaseAnalysisResponse):
    """Typography-specific analysis result for amount-field forensics."""

    analysis_type: str = "typography"
    fraud_score: float = Field(description="Weighted fraud score from multi-dimensional analysis.")
    reasons: list[str] = Field(default_factory=list, description="List of findings/reasons for the verdict.")
    char_count: int = Field(description="Number of character boxes detected.")
    avg_aspect_ratio: Optional[float] = Field(default=None, description="Average w/h ratio of digit boxes.")
    gap_analysis: list[float] = Field(default_factory=list, description="Kerning gaps between characters (px).")
    symbol_check: Optional[dict] = Field(default=None, description="Currency symbol width check details.")


class PipelineAnalysisResponse(BaseAnalysisResponse):
    """Combined receipt verification pipeline result (ELA + per-field typography)."""

    analysis_type: str = "pipeline"
    ela_verdict: str = Field(description="ELA verdict: AUTHENTIC or FORGED.")
    ela_is_ai_generated: bool = Field(description="Whether ELA suspects AI generation.")
    ela_noise_score: float = Field(description="ELA composite noise score (0-100).")
    fields: dict[str, FieldResult] = Field(
        default_factory=dict,
        description="Per-field typography results keyed by field name (name, phone_number, amount, total_amount, reference_number, date).",
    )
    forged_fields: list[str] = Field(
        default_factory=list,
        description="List of field names that failed typography checks.",
    )
    typography_reasons: list[str] = Field(
        default_factory=list, description="All typography findings across fields."
    )
    combined_verdict: str = Field(
        description="Final verdict combining ELA and typography results."
    )


class ErrorResponse(BaseModel):
    detail: str
    error_code: str
