"""
Embeddings for Firm Brain RAG.

Primary backend: fastembed (local ONNX BGE-small, ~130MB, no API key, no
data leaves the machine, semantically aware). This is what you want in
production for real semantic search.

Fallback backend: scikit-learn TF-IDF -- kicks in automatically if the
fastembed model can't be downloaded (e.g. no internet / restricted network
on first run). This keeps the tool runnable everywhere. Tradeoff: TF-IDF
matches on keyword overlap, not semantic meaning, so paraphrased questions
retrieve less reliably than with fastembed -- worth knowing which backend
is active (printed at startup, also recorded in index/embedder_meta.pkl).
"""
import os
import pickle

import numpy as np


class Embedder:
    def __init__(self):
        self.backend = None
        self._fastembed_model = None
        self._tfidf = None

    def init_for_ingest(self):
        """Try fastembed first; fall back to TF-IDF if the model can't be
        fetched. Called once, during `ingest.py`.

        Set FIRM_BRAIN_EMBEDDING_BACKEND=tfidf to skip the fastembed
        attempt entirely (useful on a network that blocks huggingface.co,
        where fastembed's own retry/backoff otherwise takes ~40s before
        giving up)."""
        if os.environ.get("FIRM_BRAIN_EMBEDDING_BACKEND") == "tfidf":
            print("[embeddings] FIRM_BRAIN_EMBEDDING_BACKEND=tfidf set -- skipping fastembed, using TF-IDF.")
            self.backend = "tfidf"
            return
        try:
            from fastembed import TextEmbedding

            model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
            _ = list(model.embed(["connectivity smoke test"]))
            self._fastembed_model = model
            self.backend = "fastembed"
            print("[embeddings] Using fastembed (local ONNX BGE-small) -- semantic search enabled.")
        except Exception as e:
            print(f"[embeddings] fastembed unavailable ({type(e).__name__}: {e}).")
            print("[embeddings] Falling back to local TF-IDF embeddings (keyword-based, fully offline).")
            self.backend = "tfidf"

    def fit(self, texts):
        """Only meaningful for the tfidf backend -- fastembed needs no fitting."""
        if self.backend == "tfidf":
            from sklearn.feature_extraction.text import TfidfVectorizer

            self._tfidf = TfidfVectorizer(max_features=4096, stop_words="english")
            self._tfidf.fit(texts)

    def embed(self, texts):
        if self.backend == "fastembed":
            return np.array(list(self._fastembed_model.embed(texts)), dtype=np.float32)
        return self._tfidf.transform(texts).toarray().astype(np.float32)

    def embed_query(self, text):
        return self.embed([text])[0]

    def save(self, path):
        with open(os.path.join(path, "embedder_meta.pkl"), "wb") as f:
            pickle.dump({"backend": self.backend}, f)
        if self.backend == "tfidf":
            with open(os.path.join(path, "tfidf_vectorizer.pkl"), "wb") as f:
                pickle.dump(self._tfidf, f)

    def load(self, path):
        """Loads whichever backend was actually used at ingest time -- does
        NOT re-attempt fastembed if TF-IDF was the fallback, so query-time
        embedding always matches the space the index was built in."""
        with open(os.path.join(path, "embedder_meta.pkl"), "rb") as f:
            meta = pickle.load(f)
        self.backend = meta["backend"]
        if self.backend == "tfidf":
            with open(os.path.join(path, "tfidf_vectorizer.pkl"), "rb") as f:
                self._tfidf = pickle.load(f)
        else:
            from fastembed import TextEmbedding

            self._fastembed_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        print(f"[embeddings] Loaded index using '{self.backend}' backend.")
        return self
