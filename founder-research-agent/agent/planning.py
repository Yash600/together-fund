from agent.llm import call_json
from agent.schemas import SearchPlan

SYSTEM_PROMPT = """You are a VC diligence research planner. Given a founder's name and their
company, plan a small set of targeted web searches to research: (1) the founder's real
background and prior experience, (2) the company itself, (3) comparable/competing companies in
the US, and (4) comparable/competing companies in India -- since we specifically care about the
US-India competitive landscape for this sector. Also flag if the founder's name is common enough
that search results could easily refer to a different person, and note what detail (company
name, location, prior employer) should be used to disambiguate."""


def plan_searches(founder_name: str, company_name: str) -> SearchPlan:
    user_prompt = f"""Founder: {founder_name}
Company: {company_name}

Plan 4-6 search queries covering: founder background/prior experience, the company itself and
its traction/press, competing companies in the US, and competing companies in India. Each query
should be a realistic web search string (not a question), plus a short "purpose" for why it's
included. Also include a disambiguation_risk note about how easily this founder could be
confused with someone else of the same or similar name.

Return JSON with fields: queries (array of {{query, purpose}}), disambiguation_risk (string)."""
    return call_json(SYSTEM_PROMPT, user_prompt, SearchPlan)
