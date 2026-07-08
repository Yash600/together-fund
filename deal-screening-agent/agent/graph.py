"""
Deal Screening Agent -- LangGraph pipeline.

Flow: parse -> extract_claims -> verify_consistency -> score_thesis -> generate_memo

Each node appends a structured entry to state["log"] (the "visible reasoning"
requirement) -- streamed in real time by both the CLI and the FastAPI SSE
endpoint.
"""
import time
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from agent.extraction import extract_claims
from agent.memo import generate_memo
from agent.scoring import score_thesis_fit
from agent.verification import verify_claims


class GraphState(TypedDict):
    raw_text: str
    claims: dict
    verification: dict
    score: dict
    memo: str
    log: list[dict]


def _log(state: GraphState, step: str, detail: str, data: Any = None) -> None:
    entry = {"step": step, "detail": detail, "ts": time.time()}
    if data is not None:
        entry["data"] = data
    state["log"].append(entry)


def extract_node(state: GraphState) -> GraphState:
    _log(state, "extract", "Extracting structured claims from deck text (market size, traction, team, ask)")
    claims = extract_claims(state["raw_text"])
    state["claims"] = claims.model_dump()
    _log(
        state,
        "extract",
        f"Extracted claims for {claims.company_name} ({claims.sector})",
        data={"traction_metrics": claims.traction_metrics, "notable_claims": claims.notable_claims},
    )
    return state


def verify_node(state: GraphState) -> GraphState:
    from agent.schemas import ExtractedClaims

    _log(state, "verify", "Checking claims for internal consistency and unsupported specificity")
    claims = ExtractedClaims.model_validate(state["claims"])
    result = verify_claims(claims, state["raw_text"])
    state["verification"] = result.model_dump()
    _log(
        state,
        "verify",
        f"Found {len(result.flags)} flag(s) to verify in founder call",
        data={"flags": [f.model_dump() for f in result.flags]},
    )
    return state


def score_node(state: GraphState) -> GraphState:
    from agent.schemas import ExtractedClaims

    _log(state, "score", "Scoring thesis fit (AI-native, vertical-agent, US-India corridor)")
    claims = ExtractedClaims.model_validate(state["claims"])
    score = score_thesis_fit(claims)
    state["score"] = score.model_dump()
    _log(
        state,
        "score",
        f"Overall thesis-fit score: {score.overall_score}/5",
        data=score.model_dump(),
    )
    return state


def memo_node(state: GraphState) -> GraphState:
    from agent.schemas import ExtractedClaims, ThesisScore, VerificationResult

    _log(state, "memo", "Drafting screening memo from claims + verification + score")
    claims = ExtractedClaims.model_validate(state["claims"])
    verification = VerificationResult.model_validate(state["verification"])
    score = ThesisScore.model_validate(state["score"])
    memo_text = generate_memo(claims, verification, score)
    state["memo"] = memo_text
    _log(state, "memo", "Memo generated", data={"memo_preview": memo_text[:150]})
    return state


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("extract", extract_node)
    graph.add_node("verify", verify_node)
    graph.add_node("score_thesis", score_node)
    graph.add_node("draft_memo", memo_node)
    graph.set_entry_point("extract")
    graph.add_edge("extract", "verify")
    graph.add_edge("verify", "score_thesis")
    graph.add_edge("score_thesis", "draft_memo")
    graph.add_edge("draft_memo", END)
    return graph.compile()


def run_screening(raw_text: str):
    """Runs the graph and yields each intermediate state after every node
    finishes, same streaming pattern as the Firm Brain RAG tool."""
    app = build_graph()
    init_state: GraphState = {
        "raw_text": raw_text,
        "claims": {},
        "verification": {},
        "score": {},
        "memo": "",
        "log": [],
    }
    last_log_len = 0
    for step_output in app.stream(init_state):
        for _node_name, node_state in step_output.items():
            new_entries = node_state["log"][last_log_len:]
            last_log_len = len(node_state["log"])
            for entry in new_entries:
                yield {"type": "log", **entry}
            if node_state.get("memo"):
                yield {
                    "type": "result",
                    "claims": node_state["claims"],
                    "verification": node_state["verification"],
                    "score": node_state["score"],
                    "memo": node_state["memo"],
                }
