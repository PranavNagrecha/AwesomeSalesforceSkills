"""Registry builders for skills and knowledge maps."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import json

from .frontmatter import parse_markdown_with_frontmatter, stable_hash_for_files


def discover_skill_dirs(root: Path) -> list[Path]:
    return sorted(path.parent for path in root.glob("skills/*/*/SKILL.md"))


def read_official_sources(skill_dir: Path) -> list[str]:
    path = skill_dir / "references" / "well-architected.md"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    marker = "## Official Sources Used"
    if marker not in text:
        return []
    section = text.split(marker, 1)[1]
    sources = []
    for line in section.splitlines():
        line = line.strip()
        if line.startswith("- "):
            sources.append(line[2:].strip())
        elif line.startswith("## "):
            break
    return sources


def list_relative_files(root: Path, directory: Path) -> list[str]:
    return sorted(str(path.relative_to(root)).replace("\\", "/") for path in directory.rglob("*") if path.is_file())


def build_skill_record(root: Path, skill_dir: Path, chunk_ids: list[str], vector_embedding: dict | None = None) -> dict:
    parsed = parse_markdown_with_frontmatter(skill_dir / "SKILL.md")
    metadata = parsed.metadata
    record = {
        "id": f"{metadata['category']}/{metadata['name']}",
        "name": metadata["name"],
        "description": metadata["description"],
        "category": metadata["category"],
        "tags": metadata["tags"],
        "inputs": metadata["inputs"],
        "outputs": metadata["outputs"],
        "dependencies": metadata["dependencies"],
        "file_location": str(skill_dir.relative_to(root)).replace("\\", "/"),
        "version": metadata["version"],
        "updated": metadata["updated"],
        "official_sources": read_official_sources(skill_dir),
        "references": list_relative_files(root, skill_dir / "references"),
        "templates": list_relative_files(root, skill_dir / "templates"),
        "scripts": list_relative_files(root, skill_dir / "scripts"),
        "chunk_ids": chunk_ids,
        "vector_embedding": vector_embedding,
        "content_hash": stable_hash_for_files([path for path in skill_dir.rglob("*") if path.is_file()]),
    }
    return record


def build_master_registry(records: list[dict]) -> dict:
    domain_counts = Counter(record["category"] for record in records)
    payload = {
        "schema_version": 1,
        "generated_from_hash": stable_registry_hash(records),
        "skill_count": len(records),
        "domain_counts": dict(sorted(domain_counts.items())),
        "skills": sorted(records, key=lambda item: item["id"]),
    }
    return payload


def stable_registry_hash(records: list[dict]) -> str:
    encoded = json.dumps(sorted(records, key=lambda item: item["id"]), sort_keys=True, separators=(",", ":")).encode("utf-8")
    from hashlib import sha256

    return sha256(encoded).hexdigest()


def build_knowledge_map(records: list[dict], source_entries: list[dict]) -> dict:
    skills_by_domain: dict[str, list[str]] = defaultdict(list)
    skills_by_tag: dict[str, list[str]] = defaultdict(list)
    for record in records:
        skills_by_domain[record["category"]].append(record["id"])
        for tag in record["tags"]:
            skills_by_tag[tag].append(record["id"])

    return {
        "schema_version": 1,
        "skills_by_domain": {key: sorted(value) for key, value in sorted(skills_by_domain.items())},
        "skills_by_tag": {key: sorted(value) for key, value in sorted(skills_by_tag.items())},
        "sources": [
            {
                "id": entry["id"],
                "title": entry["title"],
                "type": entry["type"],
                "trust": entry["trust"],
                "domains": entry["domains"],
                "tags": entry["tags"],
            }
            for entry in source_entries
        ],
    }
