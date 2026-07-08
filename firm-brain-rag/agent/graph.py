"""
Firm Brain RAG - LangGraph pipeline.

Flow: classify_query -> retrieve -> synthesize

Each node appends a structured entry to state["log"] describing what it did
(the "visible reasoning" requirement) -- these entries are what both the CLI
and the FastAPI SSE endpoint stream back in real time.
"""
import json
import os
import time
from typing import Any, Literal, TypedDict

from groq import Groq
from langgraph.graph import END, StateGraph

from agent.embeddings import Embedder
from agent.store import VectorStore

GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

QUERY_TYPES = ["lookup", "compare", "summarize", "thesis", "general"]


class GraphState(TypedDict):
    query: str
    query_type: str
    retrieved: list[dict]
    answer: str
    log: list[dict]


def _client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set. Copy .env.example to .env and add your key.")
    return Groq(api_key=api_key)


def _log(state: GraphState, step: str, detail: str, data: Any = None) -> None:
    entry = {"step": step, "detail": detail, "ts": time.time()}
    if data is not None:
        entry["data"] = data
    state["log"].append(entry)


def make_classify_node():
    def classify_node(state: GraphState) -> GraphState:
        _log(state, "classify", f"Classifying query intent: \"{state['query']}\"")
        prompt = f"""Classify the intent of this question a VC partner is asking an internal
knowledge base about past deals, portfolio companies, and firm thesis notes.

Question: "{state['query']}"

Reply with exactly one word from this list: {", ".join(QUERY_TYPES)}
- lookup: asking about a specific fact/company/deal
- compare: asking to compare two or more companies/deals
- summarize: asking for a summary or digest across multiple docs
- thesis: asking about firm-level thesis, strategy, or "what do we believe about X"
- general: anything else

Reply with only the single word, nothing else."""
        resp = _client().chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=10,
        )
        raw = resp.choices[0].message.content.strip().lower()
        query_type = raw if raw in QUERY_TYPES else "general"
        state["query_type"] = query_type
        _log(state, "classify", f"Classified as '{query_type}'", data={"query_type": query_type})
        return state

    return classify_node


def make_retrieve_node(store: VectorStore, embedder: Embedder):
    def retrieve_node(state: GraphState) -> GraphState:
        top_k = 8 if state["query_type"] in ("compare", "summarize") else 7
        _log(state, "retrieve", f"Embedding query and searching vector store (top_k={top_k}, backend={embedder.backend})")
        qvec = embedder.embed_query(state["query"])
        results = store.search(qvec, top_k=top_k)
        state["retrieved"] = results
        summary = [
            {
                "company": r["metadata"].get("company", "N/A"),
                "doc_type": r["metadata"].get("doc_type", "N/A"),
                "section": r["metadata"].get("section", ""),
                "score": round(r["score"], 3),
            }
            for r in results
        ]
        _log(
            state,
            "retrieve",
            f"Retrieved {len(results)} chunks from the knowledge base",
            data={"chunks": summary},
        )
        return state

    return retrieve_node


def make_synthesize_node():
    def synthesize_node(state: GraphState) -> GraphState:
        _log(state, "synthesize", "Generating answer from retrieved context")
        context_blocks = []
        for i, r in enumerate(state["retrieved"]):
            meta = r["metadata"]
            tag = f"[{i+1}] {meta.get('company', 'N/A')} - {meta.get('doc_type', 'N/A')} ({meta.get('date', 'n/a')}) - {meta.get('section', '')}"
            context_blocks.append(f"{tag}\n{r['text']}")
        context = "\n\n---\n\n".join(context_blocks) if context_blocks else "(no relevant documents found)"

        # Note: context blocks above are still internally tagged [1], [2]... so
        # the retrieved-chunks log (not shown to the end user) stays traceable,
        # but the model is explicitly told not to surface those markers in the
        # answer text itself -- the user just wants a plain, readable answer.
        system_prompt = """You are Firm Brain, an internal knowledge assistant for Together Fund,
a VC firm. Answer the partner's question using ONLY the provided context blocks below, in plain,
readable prose. Do NOT include bracketed citation markers, footnote numbers, or any [n]-style
references anywhere in your answer. If the context does not contain enough information to answer,
say so explicitly rather than guessing. Be concise and direct."""

        user_prompt = f"""Question: {state['query']}
Query type: {state['query_type']}

Context:
{context}

Answer the question in plain prose. Do not include bracketed citation markers, footnote numbers,
or [n]-style references anywhere in the answer."""

        resp = _client().chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=700,
        )
        answer = resp.choices[0].message.content
        state["answer"] = answer
        _log(state, "synthesize", "Answer generated", data={"answer_preview": answer[:120]})
        return state

    return synthesize_node


def build_graph(store: VectorStore, embedder: Embedder):
    graph = StateGraph(GraphState)
    graph.add_node("classify", make_classify_node())
    graph.add_node("retrieve", make_retrieve_node(store, embedder))
    graph.add_node("synthesize", make_synthesize_node())
    graph.set_entry_point("classify")
    graph.add_edge("classify", "retrieve")
    graph.add_edge("retrieve", "synthesize")
    graph.add_edge("synthesize", END)
    return graph.compile()


def run_query(store: VectorStore, embedder: Embedder, query: str):
    """Runs the graph and yields each intermediate state after every node
    finishes -- used by both the CLI and the SSE endpoint to stream reasoning
    steps as they happen instead of returning everything at the end."""
    app = build_graph(store, embedder)
    init_state: GraphState = {"query": query, "query_type": "", "retrieved": [], "answer": "", "log": []}
    last_log_len = 0
    for step_output in app.stream(init_state):
        for _node_name, node_state in step_output.items():
            new_entries = node_state["log"][last_log_len:]
            last_log_len = len(node_state["log"])
            for entry in new_entries:
                yield {"type": "log", **entry}
            if node_state.get("answer"):
                yield {"type": "answer", "answer": node_state["answer"], "retrieved": node_state["retrieved"]}
