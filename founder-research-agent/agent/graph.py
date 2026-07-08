"""
Founder Research Agent -- LangGraph pipeline.

Flow: plan_searches -> run_searches -> verify_founder -> compare_landscape -> synthesize_brief

This is the most "agentic" of the three tools: it has a real tool-use loop
(the planner decides what to search, then actual web searches are executed)
rather than a fixed linear pipeline over a static document set.

Every node appends a structured entry to state["log"] -- streamed in real
time by both the CLI and the FastAPI SSE endpoint, same pattern as the other
two tools.
"""
import time
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from agent.comparison import compare_landscape
from agent.planning import plan_searches
from agent.search import tavily_search
from agent.synthesis import synthesize_brief
from agent.verification import verify_founder


class GraphState(TypedDict):
    founder_name: str
    company_name: str
    plan: dict
    founder_search_results: dict
    landscape_search_results: dict
    verification: dict
    comparison: dict
    brief: str
    log: list[dict]


def _log(state: GraphState, step: str, detail: str, data: Any = None) -> None:
    entry = {"step": step, "detail": detail, "ts": time.time()}
    if data is not None:
        entry["data"] = data
    state["log"].append(entry)


def plan_node(state: GraphState) -> GraphState:
    _log(state, "plan", f"Planning research queries for {state['founder_name']} / {state['company_name']}")
    plan = plan_searches(state["founder_name"], state["company_name"])
    state["plan"] = plan.model_dump()
    _log(
        state,
        "plan",
        f"Planned {len(plan.queries)} search queries. Disambiguation risk: {plan.disambiguation_risk}",
        data={"queries": [q.model_dump() for q in plan.queries]},
    )
    return state


def search_node(state: GraphState) -> GraphState:
    from agent.schemas import SearchPlan

    plan = SearchPlan.model_validate(state["plan"])
    founder_results = {}
    landscape_results = {}
    for q in plan.queries:
        _log(state, "search", f"Searching: \"{q.query}\" ({q.purpose})")
        try:
            results = tavily_search(q.query, max_results=5)
        except Exception as e:
            results = []
            _log(state, "search", f"Search failed for \"{q.query}\": {type(e).__name__}: {e}")
        if "compet" in q.purpose.lower() or "us" in q.purpose.lower() or "india" in q.purpose.lower():
            landscape_results[q.query] = results
        else:
            founder_results[q.query] = results
        _log(state, "search", f"Got {len(results)} result(s) for \"{q.query}\"")
    state["founder_search_results"] = founder_results
    state["landscape_search_results"] = landscape_results
    return state


def verify_node(state: GraphState) -> GraphState:
    from agent.schemas import SearchPlan

    plan = SearchPlan.model_validate(state["plan"])
    _log(state, "verify", "Cross-checking founder/company claims against search results")
    result = verify_founder(
        state["founder_name"], state["company_name"], state["founder_search_results"], plan.disambiguation_risk
    )
    state["verification"] = result.model_dump()
    _log(
        state,
        "verify",
        f"Identity confidence: {result.identity_confidence}. Verified {len(result.verified_claims)} claim(s), "
        f"{len(result.open_questions)} open question(s)",
        data=result.model_dump(),
    )
    return state


def compare_node(state: GraphState) -> GraphState:
    _log(state, "compare", "Mapping US vs India competitive landscape from search results")
    result = compare_landscape(state["company_name"], state["company_name"], state["landscape_search_results"])
    state["comparison"] = result.model_dump()
    _log(
        state,
        "compare",
        f"Found {len(result.us_companies)} US and {len(result.india_companies)} India comparable(s)",
        data=result.model_dump(),
    )
    return state


def synthesize_node(state: GraphState) -> GraphState:
    from agent.schemas import ComparisonResult, FounderVerification

    _log(state, "synthesize", "Drafting founder-market-fit brief")
    verification = FounderVerification.model_validate(state["verification"])
    comparison = ComparisonResult.model_validate(state["comparison"])
    brief = synthesize_brief(state["founder_name"], state["company_name"], verification, comparison)
    state["brief"] = brief
    _log(state, "synthesize", "Brief generated", data={"brief_preview": brief[:150]})
    return state


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("plan_searches", plan_node)
    graph.add_node("run_searches", search_node)
    graph.add_node("verify_founder", verify_node)
    graph.add_node("compare_landscape", compare_node)
    graph.add_node("synthesize_brief", synthesize_node)
    graph.set_entry_point("plan_searches")
    graph.add_edge("plan_searches", "run_searches")
    graph.add_edge("run_searches", "verify_founder")
    graph.add_edge("verify_founder", "compare_landscape")
    graph.add_edge("compare_landscape", "synthesize_brief")
    graph.add_edge("synthesize_brief", END)
    return graph.compile()


def run_research(founder_name: str, company_name: str):
    """Runs the graph and yields each intermediate state after every node
    finishes -- same streaming pattern as the other two tools."""
    app = build_graph()
    init_state: GraphState = {
        "founder_name": founder_name,
        "company_name": company_name,
        "plan": {},
        "founder_search_results": {},
        "landscape_search_results": {},
        "verification": {},
        "comparison": {},
        "brief": "",
        "log": [],
    }
    last_log_len = 0
    for step_output in app.stream(init_state):
        for _node_name, node_state in step_output.items():
            new_entries = node_state["log"][last_log_len:]
            last_log_len = len(node_state["log"])
            for entry in new_entries:
                yield {"type": "log", **entry}
            if node_state.get("brief"):
                yield {
                    "type": "result",
                    "verification": node_state["verification"],
                    "comparison": node_state["comparison"],
                    "brief": node_state["brief"],
                }
