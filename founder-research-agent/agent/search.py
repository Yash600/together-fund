"""
Tavily web search -- the actual "tool use" in this agent. Plain REST call
via httpx rather than the tavily-python package, to keep dependencies
minimal and the request/response shape fully visible.
"""
import os

import httpx

TAVILY_URL = "https://api.tavily.com/search"


def tavily_search(query: str, max_results: int = 5) -> list[dict]:
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY is not set. Copy .env.example to .env and add your key "
                            "(free at tavily.com, ~1000 searches/month).")
    resp = httpx.post(
        TAVILY_URL,
        json={
            "api_key": api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
        },
        timeout=20.0,
    )
    resp.raise_for_status()
    data = resp.json()
    results = []
    for r in data.get("results", []):
        results.append(
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", "")[:600],  # trim -- keeps LLM context lean
            }
        )
    return results
