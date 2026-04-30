"""Optional embedding backends for semantic reranking.

Two backends are supported:

- ``hash`` — deterministic token-hashing scheme. Stdlib-only, no model
  weights, dimensions configurable. Useful for tests and as a no-op default.
  Not a semantic embedding model — adds little reranking signal.
- ``fastembed`` — real semantic embeddings via `fastembed` (ONNX runtime).
  Default model `BAAI/bge-small-en-v1.5` (384-dim, MIT, ~130 MB on first
  download, runs on CPU). The model is loaded lazily and cached as a
  module-level singleton so per-query overhead is one ONNX inference.

Caching: ``build_embeddings`` accepts ``existing_path`` to reuse vectors
keyed by chunk content hash. Re-runs only encode chunks whose text has
changed — turning the 120K-chunk repo build from ~4 minutes into seconds.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path


FASTEMBED_MODEL_NAME = "BAAI/bge-small-en-v1.5"
FASTEMBED_DIMENSIONS = 384

_FASTEMBED_MODEL = None  # module-level singleton


@dataclass(frozen=True)
class EmbeddingConfig:
    enabled: bool
    backend: str
    dimensions: int


def parse_embedding_config(config: dict) -> EmbeddingConfig:
    embeddings = config.get("embeddings", {})
    return EmbeddingConfig(
        enabled=bool(embeddings.get("enabled", False)),
        backend=str(embeddings.get("backend", "hash")),
        dimensions=int(embeddings.get("dimensions", 64)),
    )


def _content_hash(text: str) -> str:
    """Stable 16-char content hash for embedding cache keys."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _get_fastembed_model():
    """Lazy-load the fastembed model. First call downloads ~130 MB (cached
    by huggingface_hub afterwards). Subsequent calls in the same process
    return the cached singleton."""
    global _FASTEMBED_MODEL
    if _FASTEMBED_MODEL is None:
        from fastembed import TextEmbedding

        _FASTEMBED_MODEL = TextEmbedding(model_name=FASTEMBED_MODEL_NAME)
    return _FASTEMBED_MODEL


def build_embeddings(
    chunks: list[dict],
    config: EmbeddingConfig,
    *,
    existing_path: Path | None = None,
) -> list[dict]:
    """Embed every chunk under the configured backend.

    ``existing_path`` enables the content-hash cache: if a chunk's text
    hash matches an existing record at that path, the vector is reused
    rather than recomputed. Pass None to force full recompute.
    """
    if not config.enabled:
        return []
    if config.backend == "hash":
        return [_hash_record(chunk, config.dimensions) for chunk in chunks]
    if config.backend == "fastembed":
        return _build_fastembed_embeddings(chunks, existing_path)
    raise ValueError(f"Unsupported embedding backend `{config.backend}`")


def _hash_record(chunk: dict, dimensions: int) -> dict:
    return {
        "chunk_id": chunk["id"],
        "backend": "hash",
        "dimension": dimensions,
        "content_hash": _content_hash(chunk["text"]),
        "vector": hash_embedding(chunk["text"], dimensions),
    }


def _build_fastembed_embeddings(
    chunks: list[dict],
    existing_path: Path | None,
) -> list[dict]:
    cache: dict[tuple[str, str], dict] = {}
    if existing_path and existing_path.exists():
        for line in existing_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if item.get("backend") != "fastembed":
                continue
            ch = item.get("content_hash")
            cid = item.get("chunk_id")
            if ch and cid:
                cache[(cid, ch)] = item

    embeddings: list[dict | None] = [None] * len(chunks)
    to_encode_indices: list[int] = []
    to_encode_texts: list[str] = []

    for i, chunk in enumerate(chunks):
        ch = _content_hash(chunk["text"])
        cached = cache.get((chunk["id"], ch))
        if cached is not None:
            embeddings[i] = cached
        else:
            to_encode_indices.append(i)
            to_encode_texts.append(chunk["text"])

    if to_encode_texts:
        model = _get_fastembed_model()
        # fastembed.embed yields a generator of np.ndarray; convert to lists.
        for slot_index, vector in zip(to_encode_indices, model.embed(to_encode_texts)):
            chunk = chunks[slot_index]
            embeddings[slot_index] = {
                "chunk_id": chunk["id"],
                "backend": "fastembed",
                "dimension": FASTEMBED_DIMENSIONS,
                "content_hash": _content_hash(chunk["text"]),
                # Round to 6 sig figs — float32 only carries ~7, so this is
                # lossless for our retrieval signal but cuts JSON size ~30%.
                "vector": [round(float(v), 6) for v in vector],
            }

    return embeddings  # type: ignore[return-value]


def hash_embedding(text: str, dimensions: int) -> list[float]:
    buckets = [0.0] * dimensions
    tokens = [token.lower() for token in text.split() if token.strip()]
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        buckets[index] += sign
    norm = math.sqrt(sum(value * value for value in buckets)) or 1.0
    return [value / norm for value in buckets]


def write_embeddings(path: Path, embeddings: list[dict]) -> None:
    if not embeddings:
        if path.exists():
            path.unlink()
        return
    lines = [json.dumps(item, sort_keys=True) for item in embeddings]
    content = "\n".join(lines) + "\n"
    path.write_text(content, encoding="utf-8")


def load_embeddings(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    payload = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        payload[item["chunk_id"]] = item
    return payload


def embed_query(query: str, config: EmbeddingConfig) -> list[float] | None:
    if not config.enabled:
        return None
    if config.backend == "hash":
        return hash_embedding(query, config.dimensions)
    if config.backend == "fastembed":
        model = _get_fastembed_model()
        vector = next(iter(model.embed([query])))
        return [float(v) for v in vector]
    raise ValueError(f"Unsupported embedding backend `{config.backend}`")


def cosine_similarity(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))
