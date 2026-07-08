"""
Together Fund's stated investment thesis, used as the scoring rubric for
stage 3 (thesis-fit scoring). Mirrors the thesis docs in the Firm Brain RAG
tool's synthetic corpus, kept here as a plain constant since this tool is
independently runnable and shouldn't depend on that tool's data.
"""

THESIS_TEXT = """
Together Fund invests in early-stage AI-native startups ($1M-$10M checks,
Seed/Series A), specializing in the US-India corridor.

What we look for:
1. AI-native, not AI-as-a-feature: the product's core value depends on AI,
   not a bolt-on feature to a conventional SaaS product.
2. Vertical AI agents over horizontal platforms: founders with direct,
   multi-year operating experience in the specific workflow being
   automated (not just general ML talent applied to a generic problem).
   We are cautious of horizontal, general-purpose tools competing directly
   with foundation-model providers' own roadmaps.
3. US-India corridor fit: ideally a US (or other global) market/buyer with
   an India-based (majority) founding or engineering team, OR a founder
   with credible experience operating in both contexts. Purely
   India-domestic-market companies can still be excellent businesses but
   are a weaker fit for our specific corridor thesis.
4. Real, validated traction: at least one paying or piloting customer,
   ideally with metrics that are independently verifiable rather than
   solely self-reported.
"""
