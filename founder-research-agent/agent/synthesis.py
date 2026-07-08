from agent.llm import call_text
from agent.schemas import ComparisonResult, FounderVerification

SYSTEM_PROMPT = """You are a VC associate drafting a founder-market-fit research brief for a
partner ahead of a founder call. Write tersely and specifically, citing sources inline as
[Title](URL) markdown links wherever a claim came from a specific source. Do not repeat
disclaimers -- state confidence levels once per claim, not as a running caveat."""


def synthesize_brief(founder_name: str, company_name: str, verification: FounderVerification, comparison: ComparisonResult) -> str:
    user_prompt = f"""Founder: {founder_name}
Company: {company_name}

Founder/company verification findings:
{verification.model_dump_json(indent=2)}

US-India competitive landscape findings:
{comparison.model_dump_json(indent=2)}

Draft a markdown research brief with these sections:
## {founder_name} / {company_name} -- Founder-Market-Fit Brief
### Identity Confidence  (state the confidence level and note plainly)
### Verified Background  (list each verified claim with its confidence and cited source link)
### US-India Competitive Landscape  (US companies, India companies, and the summary)
### Open Questions for the Founder Call  (from the verification step's open_questions)
### Overall Read  (2-3 sentences: how strong is founder-market fit given what's verifiable, and
    what's the single most important thing to confirm directly with the founder)

Be specific -- reference actual companies, claims, and sources found. If verification was thin,
say so plainly rather than padding with generic text."""
    return call_text(SYSTEM_PROMPT, user_prompt, temperature=0.3, max_tokens=1400)
