"""Embedding backends.

Primary: Sentence Transformers (all-MiniLM-L6-v2 by default).
Fallback (model unavailable / offline): stateless hashed TF-IDF vectors, so the app still runs.
Both return L2-normalised vectors, so cosine similarity == dot product.
"""
import logging
import os
import re

import numpy as np

log = logging.getLogger(__name__)

_state = {"model": None, "name": None, "failed": False}

# Calibration: map raw cosine -> 0..1 (SBERT cosine of related docs is rarely above ~0.75).
CALIBRATION = {"sbert": (0.15, 0.70), "hashing": (0.02, 0.35)}


def _model_name():
    try:
        from django.conf import settings
        return settings.EMBEDDING_MODEL
    except Exception:
        return os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")


def _load_sbert():
    if _state["model"] is not None or _state["failed"]:
        return _state["model"]
    if os.getenv("FORCE_FALLBACK_EMBEDDINGS") == "1":
        _state["failed"] = True
        return None
    try:
        from sentence_transformers import SentenceTransformer
        _state["name"] = _model_name()
        _state["model"] = SentenceTransformer(_state["name"])
    except Exception as exc:
        log.warning("Sentence Transformers unavailable (%s); using TF-IDF fallback.", exc)
        _state["failed"] = True
    return _state["model"]


def backend_name() -> str:
    return f"sbert:{_state['name']}" if _load_sbert() is not None else "hashing"


def _kind(backend: str) -> str:
    return "sbert" if backend.startswith("sbert") else "hashing"


def _chunk(text: str, words=120, overlap=20):
    toks = text.split()
    if len(toks) <= words:
        return [text]
    step = words - overlap
    return [" ".join(toks[i:i + words]) for i in range(0, len(toks), step)]


def _hashing_encode(texts):
    from sklearn.feature_extraction.text import HashingVectorizer
    hv = HashingVectorizer(n_features=2 ** 13, ngram_range=(1, 2), alternate_sign=False, norm="l2",
                           stop_words="english", token_pattern=r"(?u)\b[\w+#.]{2,}\b", lowercase=True)
    return hv.transform(texts).toarray()


def _normalize(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.where(n == 0, 1, n)


def encode(texts, backend=None):
    """Encode short strings (skill names, sentences) -> (n, d) normalised array."""
    model = _load_sbert()
    if model is not None and (backend is None or backend.startswith("sbert")):
        return _normalize(np.asarray(model.encode(list(texts), show_progress_bar=False)))
    return _normalize(_hashing_encode(list(texts)))


def embed_document(text: str) -> np.ndarray:
    """Embed a long document by chunking, encoding each chunk and mean-pooling (SBERT truncates ~256 tokens)."""
    text = re.sub(r"\s+", " ", text or "").strip() or " "
    chunks = _chunk(text)
    vecs = encode(chunks)
    return _normalize(vecs.mean(axis=0, keepdims=True))[0]


def cosine(a, b) -> float:
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1.0
    return float(np.dot(a, b) / denom)


def calibrate(cos: float, backend: str) -> float:
    """Raw cosine -> 0..100 semantic score."""
    lo, hi = CALIBRATION[_kind(backend)]
    return float(np.clip((cos - lo) / (hi - lo), 0, 1) * 100)
