"""
Minimal local vector store: embeddings persisted as a .npy matrix + chunk
metadata as .json. Cosine similarity search via numpy, no external DB needed.

This is a deliberate simplification for local/demo runnability -- in
production this would swap for Postgres + pgvector (see writeup), which is
a one-file change since `search()` is the only method the rest of the app
depends on.
"""
import json
import os

import numpy as np


class VectorStore:
    def __init__(self):
        self.vectors: np.ndarray | None = None
        self.chunks: list[dict] = []

    def build(self, chunks: list, vectors: np.ndarray):
        self.chunks = [{"chunk_id": c.chunk_id, "text": c.text, "metadata": c.metadata} for c in chunks]
        # normalize for cosine similarity via dot product
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1e-9
        self.vectors = vectors / norms

    def add(self, chunks: list, vectors: np.ndarray):
        """Appends newly-embedded chunks to an already-built/loaded index --
        used for live document uploads so they become queryable immediately
        without rebuilding the whole index from scratch."""
        new_chunks = [{"chunk_id": c.chunk_id, "text": c.text, "metadata": c.metadata} for c in chunks]
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1e-9
        new_vectors = vectors / norms
        if self.vectors is None or len(self.chunks) == 0:
            self.chunks = new_chunks
            self.vectors = new_vectors
        else:
            self.chunks = self.chunks + new_chunks
            self.vectors = np.vstack([self.vectors, new_vectors])

    def save(self, path: str):
        os.makedirs(path, exist_ok=True)
        np.save(os.path.join(path, "vectors.npy"), self.vectors)
        with open(os.path.join(path, "chunks.json"), "w") as f:
            json.dump(self.chunks, f, default=str)

    def load(self, path: str):
        self.vectors = np.load(os.path.join(path, "vectors.npy"))
        with open(os.path.join(path, "chunks.json")) as f:
            self.chunks = json.load(f)
        return self

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> list[dict]:
        if self.vectors is None or len(self.chunks) == 0:
            return []
        q = query_vector / (np.linalg.norm(query_vector) + 1e-9)
        scores = self.vectors @ q
        top_idx = np.argsort(-scores)[:top_k]
        results = []
        for idx in top_idx:
            item = dict(self.chunks[int(idx)])
            item["score"] = float(scores[int(idx)])
            results.append(item)
        return results
