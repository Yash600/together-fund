"""
Structured output schemas for each pipeline stage.
"""
from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    query: str
    purpose: str  # why this query, e.g. "founder background", "prior startups", "US competitors"


class SearchPlan(BaseModel):
    queries: list[SearchQuery]
    disambiguation_risk: str = Field(
        description="Note on whether this founder's name is common enough that search results "
        "might refer to a different person, and how to tell them apart"
    )


class VerifiedClaim(BaseModel):
    claim: str
    confidence: str  # "high" | "medium" | "low"
    sources: list[str] = Field(default_factory=list)


class FounderVerification(BaseModel):
    identity_confidence: str  # "high" | "medium" | "low"
    identity_note: str
    verified_claims: list[VerifiedClaim] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


class ComparableCompany(BaseModel):
    name: str
    country: str  # "US" | "India" | "Other"
    description: str
    source_url: str | None = None


class ComparisonResult(BaseModel):
    us_companies: list[ComparableCompany] = Field(default_factory=list)
    india_companies: list[ComparableCompany] = Field(default_factory=list)
    summary: str
