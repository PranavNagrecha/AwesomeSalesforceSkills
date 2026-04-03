"""Knowledge source manifest and document discovery helpers."""

from __future__ import annotations

from pathlib import Path
import yaml


def load_sources_manifest(root: Path) -> list[dict]:
    data = yaml.safe_load((root / "knowledge" / "sources.yaml").read_text(encoding="utf-8")) or {}
    return data.get("sources", [])


def discover_knowledge_documents(root: Path, source_entries: list[dict]) -> list[dict]:
    documents: list[dict] = []
    for entry in source_entries:
        source_type = entry["type"]
        if source_type == "local-file":
            path = root / entry["path"]
            if path.exists():
                documents.append(
                    {
                        "id": entry["id"],
                        "title": entry["title"],
                        "path": str(path.relative_to(root)).replace("\\", "/"),
                        "domain": primary_domain(entry["domains"]),
                        "text": path.read_text(encoding="utf-8"),
                        "chunk_kind": "knowledge-file",
                        "source_trust": entry["trust"],
                        "official_source_ids": [],
                        "skill_id": None,
                        "tags": entry["tags"],
                    }
                )
        elif source_type == "local-directory":
            directory = root / entry["path"]
            if not directory.exists():
                continue
            for path in sorted(directory.rglob("*.md")):
                relative_path = str(path.relative_to(directory)).replace("\\", "/")
                documents.append(
                    {
                        "id": f"{entry['id']}::{relative_path}",
                        "title": path.stem.replace("-", " ").title(),
                        "path": str(path.relative_to(root)).replace("\\", "/"),
                        "domain": primary_domain(entry["domains"]),
                        "text": path.read_text(encoding="utf-8"),
                        "chunk_kind": "knowledge-file",
                        "source_trust": entry["trust"],
                        "official_source_ids": [],
                        "skill_id": None,
                        "tags": entry["tags"],
                    }
                )
        elif source_type == "official-doc":
            documents.append(
                {
                    "id": entry["id"],
                    "title": entry["title"],
                    "path": entry["url"],
                    "domain": primary_domain(entry["domains"]),
                    "text": synthesize_official_source_text(entry),
                    "chunk_kind": "official-source",
                    "source_trust": entry["trust"],
                    "official_source_ids": [entry["id"]],
                    "skill_id": None,
                    "tags": entry["tags"],
                }
            )
    return documents


def synthesize_official_source_text(entry: dict) -> str:
    summary = entry.get("summary") or entry.get("notes") or ""
    domains = ", ".join(entry.get("domains", []))
    tags = ", ".join(entry.get("tags", []))
    return "\n".join(
        [
            entry["title"],
            summary,
            f"Domains: {domains}",
            f"Tags: {tags}",
            f"URL: {entry.get('url', '')}",
        ]
    ).strip()


def primary_domain(domains: list[str]) -> str | None:
    return domains[0] if domains else None
