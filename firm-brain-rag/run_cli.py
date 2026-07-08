"""
Standalone CLI entry point -- proves this tool runs completely on its own,
with no frontend, no pre-built index, and no other tool required. Ingests
ONE document live (same chunking/embedding path the web upload uses) and
answers ONE question against just that document.

Usage:
    python run_cli.py <path_to_document.md_or_.txt_or_.pdf> "your question here"
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from agent.chunking import chunk_uploaded_text
from agent.embeddings import Embedder
from agent.graph import run_query
from agent.store import VectorStore


def _read_document(path: str) -> str:
    if path.lower().endswith(".pdf"):
        import fitz  # PyMuPDF

        doc = fitz.open(path)
        text = "\n\n".join(page.get_text() for page in doc)
        doc.close()
        return text
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def main():
    if len(sys.argv) < 3:
        print('Usage: python run_cli.py <path_to_document> "your question here"')
        sys.exit(1)
    doc_path = sys.argv[1]
    query = " ".join(sys.argv[2:])

    if not os.path.exists(doc_path):
        print(f"[error] File not found: {doc_path}")
        sys.exit(1)

    print("\n=== Firm Brain RAG (standalone, single-document mode) ===")
    print(f"Document: {doc_path}")
    print(f"Query: {query}\n")

    print("[ingest] Extracting and chunking document...")
    text = _read_document(doc_path)
    chunks = chunk_uploaded_text(os.path.basename(doc_path), text)
    print(f"[ingest] Split into {len(chunks)} chunk(s)")

    embedder = Embedder()
    embedder.init_for_ingest()
    texts = [c.text for c in chunks]
    if embedder.backend == "tfidf":
        embedder.fit(texts)
    vectors = embedder.embed(texts)

    store = VectorStore()
    store.build(chunks, vectors)
    print(f"[ingest] Embedded with '{embedder.backend}' backend\n")

    print("--- reasoning trace ---")
    final_answer = None
    for event in run_query(store, embedder, query):
        if event["type"] == "log":
            data_str = f"  {event['data']}" if "data" in event else ""
            print(f"[{event['step']}] {event['detail']}{data_str}")
        elif event["type"] == "answer":
            final_answer = event["answer"]

    print("\n--- answer ---")
    print(final_answer)
    print()


if __name__ == "__main__":
    main()
