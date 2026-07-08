from agent.llm import call_json
from agent.schemas import FounderVerification

SYSTEM_PROMPT = """You are a VC diligence analyst reviewing raw web search results about a
founder and their company. Your job: extract claims that are ACTUALLY SUPPORTED by the search
results (with a confidence level and the source URL), flag identity-disambiguation concerns if
results seem to reference more than one person with this name, and list open questions that
still need to be asked directly in a founder call because the web search couldn't resolve them.
Do not invent facts not present in the search results. If results are thin or conflicting, say so
plainly rather than overstating confidence."""


def verify_founder(founder_name: str, company_name: str, search_results: dict[str, list[dict]], disambiguation_risk: str) -> FounderVerification:
    results_text = ""
    for query, results in search_results.items():
        results_text += f"\n\nQuery: {query}\n"
        for r in results:
            results_text += f"- [{r['title']}]({r['url']}): {r['content']}\n"

    user_prompt = f"""Founder: {founder_name}
Company: {company_name}
Disambiguation risk noted by the search planner: {disambiguation_risk}

Raw search results:
{results_text}

Extract what can actually be verified about this founder and company from these results. Return
JSON with fields:
- identity_confidence: "high"/"medium"/"low" -- how confident are you these results are about
  the correct person, not a namesake
- identity_note: brief explanation of the identity_confidence call
- verified_claims: array of {{claim, confidence, sources}} -- confidence is "high"/"medium"/"low",
  sources is an array of the URLs supporting that specific claim
- open_questions: array of specific questions to ask in the actual founder call because the
  search results didn't resolve them"""
    return call_json(SYSTEM_PROMPT, user_prompt, FounderVerification)
