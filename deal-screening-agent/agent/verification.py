from agent.llm import call_json
from agent.schemas import ExtractedClaims, VerificationResult

SYSTEM_PROMPT = """You are a skeptical VC diligence analyst. You cannot access the internet, so
you cannot confirm claims against outside sources -- your job is narrower: check the claims
extracted from a pitch deck for INTERNAL consistency, unsupported specificity, and common
red-flag patterns (e.g. a market-size number with no stated basis, traction metrics that are
arithmetically inconsistent with each other, vague team descriptions on a slide that should have
specifics, funding-ask/valuation mismatches). Do not assume a claim is false; flag it as a
concern to verify in the actual founder call, with a clear reason and severity."""


def verify_claims(claims: ExtractedClaims, raw_text: str) -> VerificationResult:
    user_prompt = f"""Extracted claims (JSON):
{claims.model_dump_json(indent=2)}

Original deck text (for cross-checking arithmetic/consistency):
---
{raw_text}
---

Return a JSON object with:
- flags: array of {{claim, concern, severity}} where severity is "low", "medium", or "high"
- overall_assessment: 1-2 sentence summary of how internally consistent this deck's claims are

Look specifically for: unsupported market-size figures (no basis given), traction numbers that
don't arithmetically add up (e.g. customer count x implied price != stated revenue), vague team
claims lacking specifics, and any claim that seems unusually strong for the stage/traction shown."""
    return call_json(SYSTEM_PROMPT, user_prompt, VerificationResult)
