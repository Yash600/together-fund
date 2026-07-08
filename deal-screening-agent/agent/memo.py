from agent.llm import call_text
from agent.schemas import ExtractedClaims, ThesisScore, VerificationResult

SYSTEM_PROMPT = """You are a VC associate drafting a first-pass screening memo for a partner.
Write in the same terse, direct style as an internal investment memo -- no fluff, no hedging
disclaimers repeated line after line. Use markdown with clear section headers."""


def generate_memo(claims: ExtractedClaims, verification: VerificationResult, score: ThesisScore) -> str:
    user_prompt = f"""Draft a first-pass screening memo from the following structured data.

Extracted claims:
{claims.model_dump_json(indent=2)}

Consistency/verification findings:
{verification.model_dump_json(indent=2)}

Thesis-fit score:
{score.model_dump_json(indent=2)}

Structure the memo with these markdown sections:
## {claims.company_name} -- Screening Memo
### Summary  (2-3 sentences)
### Thesis Fit  (state the 4 scores plainly, then the rationale)
### Traction  (list the stated metrics)
### Team
### Flags to Verify in Founder Call  (turn each verification flag into a specific question to ask)
### Recommendation  (one of: "Advance to founder call", "Advance with reservations", "Pass" --
    and 1-2 sentences of reasoning tied to the scores and flags above)

Be specific and reference actual numbers/claims -- do not write generic filler."""
    return call_text(SYSTEM_PROMPT, user_prompt, temperature=0.3, max_tokens=1200)
