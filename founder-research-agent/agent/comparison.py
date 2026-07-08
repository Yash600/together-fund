from agent.llm import call_json
from agent.schemas import ComparisonResult

SYSTEM_PROMPT = """You are a VC analyst mapping the competitive landscape for a startup across
the US and India specifically -- Together Fund's corridor thesis requires knowing who else is
building in this space on both sides. Extract only companies actually mentioned in the search
results, tagging each with its country if determinable. Do not invent competitors not present in
the results.

IMPORTANT on country tagging: judge each company's actual headquarters/origin country using
your own knowledge, NOT just which list or webpage section it happened to appear under in the
search results. Source pages (e.g. a "startups in India" directory) sometimes lump in companies
that merely have an India office, a job posting, or a reseller presence -- that is not the same
as being an India-headquartered company. If you are not confident of a company's actual country,
tag it "Other" or say so in the description rather than guessing."""


def compare_landscape(company_name: str, sector_hint: str, search_results: dict[str, list[dict]]) -> ComparisonResult:
    results_text = ""
    for query, results in search_results.items():
        results_text += f"\n\nQuery: {query}\n"
        for r in results:
            results_text += f"- [{r['title']}]({r['url']}): {r['content']}\n"

    user_prompt = f"""Company being evaluated: {company_name} (sector: {sector_hint})

Raw search results from US and India competitor searches:
{results_text}

Extract companies that appear to compete with or resemble {company_name}, split by country (US
vs India vs Other if unclear). Return JSON with fields:
- us_companies: array of {{name, country: "US", description, source_url}}
- india_companies: array of {{name, country: "India", description, source_url}}
- summary: 2-3 sentence summary of how crowded/differentiated the landscape looks on each side

Remember: only tag a company "US" or "India" if you are actually confident that's where it's
headquartered, based on your own knowledge of the company -- not merely which source list
mentioned it. When unsure, use "Other" and note the uncertainty in the description."""
    return call_json(SYSTEM_PROMPT, user_prompt, ComparisonResult)
