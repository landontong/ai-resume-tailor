from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class TailorRequest(BaseModel):
    resume_latex: str = Field(..., description="Full LaTeX resume source")
    job_description: str = Field(..., description="Target job description text")
    role_title: Optional[str] = Field(default=None, description="Optional role title")
    company: Optional[str] = Field(default=None, description="Optional company name")

    # Feedback loop knobs
    min_signal_density: float = Field(default=7.6, ge=0.0, le=10.0)
    min_keyword_alignment: float = Field(default=82.0, ge=0.0, le=100.0)
    max_passes: int = Field(default=2, ge=1, le=3)


class Metrics(BaseModel):
    signal_density: float
    technical_specificity: str  # Low/Med/High
    keyword_alignment: float    # %
    redundancy: str             # Low/Med/High

    # Helpful debugging/UX extras
    matched_keywords: List[str]
    missing_keywords: List[str]
    bullet_count: int
    avg_bullet_length: float


class TailorResult(BaseModel):
    pass_index: int
    mode: str
    tailored_resume_latex: str
    metrics: Metrics


class TailorResponse(BaseModel):
    best: TailorResult
    all_passes: List[TailorResult]
    decision: Dict[str, Any]
