from agent.llm import call_json
from agent.schemas import ExtractedClaims, ThesisScore
from agent.thesis import THESIS_TEXT

SYSTEM_PROMPT = """You are a VC partner scoring a startup against a firm's stated investment
thesis. Score honestly and specifically -- do not default to the middle of the scale. Base scores
only on what's in the extracted claims, and say so explicitly in the rationale when something is
unclear or unstated."""


def score_thesis_fit(claims: ExtractedClaims) -> ThesisScore:
    user_prompt = f"""Our investment thesis:
{THESIS_TEXT}

Extracted claims about this company (JSON):
{claims.model_dump_json(indent=2)}

Score this company 1-5 (5 = excellent fit) on each of:
- ai_native_fit: is AI genuinely core to the product, or a bolt-on feature?
- vertical_agent_fit: is this a narrow, domain-expert-led vertical agent, or a horizontal/generic tool?
- us_india_corridor_fit: does this match our US-India corridor thesis (see above)?
- overall_score: your overall 1-5 conviction given all of the above

Return JSON with fields: ai_native_fit, vertical_agent_fit, us_india_corridor_fit,
overall_score (all integers 1-5), and rationale (2-4 sentences explaining the scores,
referencing specific claims)."""
    return call_json(SYSTEM_PROMPT, user_prompt, ThesisScore)
