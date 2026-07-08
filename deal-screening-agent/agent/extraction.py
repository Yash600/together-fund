from agent.llm import call_json
from agent.schemas import ExtractedClaims

SYSTEM_PROMPT = """You are a VC analyst assistant. Extract structured claims from a startup
pitch deck's raw text. Be literal -- only extract what the deck actually states, do not infer
or fabricate numbers. If a field isn't present in the deck, omit it or leave it empty."""


def extract_claims(deck_text: str) -> ExtractedClaims:
    user_prompt = f"""Extract the following from this pitch deck text into the required JSON
schema: company_name, sector, stage, market_size_claim (the exact TAM/market-size figure
claimed, if any), market_size_basis (what source or reasoning was given for that figure, if
any -- note if none was given), traction_metrics (list of specific traction numbers stated),
team_summary (brief summary of founder/team background as stated), funding_ask, key_differentiators
(list), and notable_claims (any other specific, checkable claims worth flagging for review).

JSON schema fields required: company_name, sector, stage, market_size_claim,
market_size_basis, traction_metrics (array), team_summary, funding_ask,
key_differentiators (array), notable_claims (array).

Pitch deck text:
---
{deck_text}
---"""
    return call_json(SYSTEM_PROMPT, user_prompt, ExtractedClaims)
