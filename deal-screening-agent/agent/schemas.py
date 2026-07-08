"""
Structured output schemas for each pipeline stage. The LLM is instructed to
return JSON matching these shapes; Pydantic validates/parses the response so
downstream stages get typed data instead of free text.
"""
from pydantic import BaseModel, Field


class ExtractedClaims(BaseModel):
    company_name: str
    sector: str
    stage: str | None = None
    market_size_claim: str | None = None
    market_size_basis: str | None = Field(
        default=None, description="How the market size claim was justified, if at all"
    )
    traction_metrics: list[str] = Field(default_factory=list)
    team_summary: str | None = None
    funding_ask: str | None = None
    key_differentiators: list[str] = Field(default_factory=list)
    notable_claims: list[str] = Field(
        default_factory=list, description="Any other specific, checkable claims worth flagging"
    )


class ClaimFlag(BaseModel):
    claim: str
    concern: str
    severity: str  # "low" | "medium" | "high"


class VerificationResult(BaseModel):
    flags: list[ClaimFlag] = Field(default_factory=list)
    overall_assessment: str


class ThesisScore(BaseModel):
    ai_native_fit: int = Field(ge=1, le=5)
    vertical_agent_fit: int = Field(ge=1, le=5)
    us_india_corridor_fit: int = Field(ge=1, le=5)
    overall_score: int = Field(ge=1, le=5)
    rationale: str
