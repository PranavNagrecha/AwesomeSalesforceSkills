"""Optional deterministic embedding backends for local reranking."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import math


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


def build_embeddings(chunks: list[dict], config: EmbeddingConfig) -> list[dict]:
    if not config.enabled:
        return []
    if config.backend != "hash":
        raise ValueError(f"Unsupported embedding backend `{config.backend}`")
    embeddings: list[dict] = []
    for chunk in chunks:
        vector = hash_embedding(chunk["text"], config.dimensions)
        embeddings.append(
            {
                "chunk_id": chunk["id"],
                "backend": config.backend,
                "dimension": config.dimensions,
                "vector": vector,
            }
        )
    return embeddings


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
    if config.backend != "hash":
        raise ValueError(f"Unsupported embedding backend `{config.backend}`")
    return hash_embedding(query, config.dimensions)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))
