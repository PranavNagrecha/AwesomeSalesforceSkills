"""End-to-end sync engine for registry, knowledge, retrieval, and generated docs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import tempfile
import yaml

from .chunker import chunk_markdown
from .docs_generator import generate_skills_catalog
from .embedding_backends import build_embeddings, parse_embedding_config, write_embeddings
from .frontmatter import parse_markdown_with_frontmatter
from .knowledge_builder import discover_knowledge_documents, load_sources_manifest
from .lexical_index import build_lexical_index, read_source_hash
from .registry_builder import build_knowledge_map, build_master_registry, build_skill_record, discover_skill_dirs


@dataclass(frozen=True)
class SyncState:
    registry_payload: dict
    registry_records: list[dict]
    knowledge_map: dict
    chunks: list[dict]
    docs_catalog: str
    embeddings: list[dict]
    manifest: dict
    source_entries: list[dict]


def load_retrieval_config(root: Path) -> dict:
    return yaml.safe_load((root / "config" / "retrieval-config.yaml").read_text(encoding="utf-8")) or {}


def build_state(root: Path) -> SyncState:
    source_entries = load_sources_manifest(root)
    skill_dirs = discover_skill_dirs(root)

    skill_documents: list[dict] = []
    initial_records: list[dict] = []
    for skill_dir in skill_dirs:
        parsed = parse_markdown_with_frontmatter(skill_dir / "SKILL.md")
        metadata = parsed.metadata
        skill_id = f"{metadata['category']}/{metadata['name']}"
        initial_records.append(
            {
                "id": skill_id,
                "name": metadata["name"],
                "category": metadata["category"],
                "tags": metadata["tags"],
                "path": str(skill_dir.relative_to(root)).replace("\\", "/"),
            }
        )

        triggers = metadata.get("triggers", [])
        triggers_section = (
            "\n\n## Trigger Scenarios\n" + "\n".join(f"- {t}" for t in triggers)
            if triggers else ""
        )
        skill_documents.append(
            {
                "source_id": f"{skill_id}::skill-md",
                "title": metadata["name"],
                "path": str((skill_dir / "SKILL.md").relative_to(root)).replace("\\", "/"),
                "domain": metadata["category"],
                "chunk_kind": "skill-main",
                "source_trust": "repo-local",
                "official_source_ids": [],
                "skill_id": skill_id,
                "tags": metadata["tags"],
                "text": parsed.body + triggers_section,
            }
        )

        for reference_path in sorted((skill_dir / "references").glob("*.md")):
            skill_documents.append(
                {
                    "source_id": f"{skill_id}::{reference_path.stem}",
                    "title": reference_path.stem.replace("-", " ").title(),
                    "path": str(reference_path.relative_to(root)).replace("\\", "/"),
                    "domain": metadata["category"],
                    "chunk_kind": f"skill-reference:{reference_path.stem}",
                    "source_trust": "repo-local",
                    "official_source_ids": [],
                    "skill_id": skill_id,
                    "tags": metadata["tags"],
                    "text": reference_path.read_text(encoding="utf-8"),
                }
            )

        for template_path in sorted((skill_dir / "templates").rglob("*")):
            if template_path.is_file():
                skill_documents.append(
                    {
                        "source_id": f"{skill_id}::template::{template_path.name}",
                        "title": template_path.name,
                        "path": str(template_path.relative_to(root)).replace("\\", "/"),
                        "domain": metadata["category"],
                        "chunk_kind": "skill-template",
                        "source_trust": "repo-local",
                        "official_source_ids": [],
                        "skill_id": skill_id,
                        "tags": metadata["tags"],
                        "text": template_path.read_text(encoding="utf-8", errors="ignore"),
                    }
                )

        for script_path in sorted((skill_dir / "scripts").glob("*.py")):
            skill_documents.append(
                {
                    "source_id": f"{skill_id}::script::{script_path.stem}",
                    "title": script_path.stem,
                    "path": str(script_path.relative_to(root)).replace("\\", "/"),
                    "domain": metadata["category"],
                    "chunk_kind": "skill-script",
                    "source_trust": "repo-local",
                    "official_source_ids": [],
                    "skill_id": skill_id,
                    "tags": metadata["tags"],
                    "text": script_path.read_text(encoding="utf-8", errors="ignore"),
                }
            )

    knowledge_documents = discover_knowledge_documents(root, source_entries)

    chunks: list[dict] = []
    for document in skill_documents + knowledge_documents:
        source_id = document["source_id"] if "source_id" in document else document["id"]
        chunks.extend(
            chunk_markdown(
                source_id=source_id,
                title=document["title"],
                path=document["path"],
                domain=document["domain"],
                chunk_kind=document["chunk_kind"],
                source_trust=document["source_trust"],
                official_source_ids=document["official_source_ids"],
                skill_id=document["skill_id"],
                tags=document["tags"],
                text=document["text"],
            )
        )

    chunk_ids_by_skill: dict[str, list[str]] = {}
    for chunk in chunks:
        skill_id = chunk.get("skill_id")
        if not skill_id:
            continue
        chunk_ids_by_skill.setdefault(skill_id, []).append(chunk["id"])

    config = load_retrieval_config(root)
    embedding_config = parse_embedding_config(config)
    embeddings = build_embeddings(chunks, embedding_config)
    embedding_lookup = {item["chunk_id"]: item for item in embeddings}

    records = []
    for skill_dir in skill_dirs:
        parsed = parse_markdown_with_frontmatter(skill_dir / "SKILL.md")
        metadata = parsed.metadata
        skill_id = f"{metadata['category']}/{metadata['name']}"
        vector_embedding = None
        if embeddings:
            vector_embedding = {
                "backend": embedding_config.backend,
                "vector_id": skill_id,
                "dimension": embedding_config.dimensions,
                "updated": metadata["updated"],
            }
        records.append(
            build_skill_record(
                root=root,
                skill_dir=skill_dir,
                chunk_ids=sorted(chunk_ids_by_skill.get(skill_id, [])),
                vector_embedding=vector_embedding,
            )
        )

    registry_payload = build_master_registry(records)
    knowledge_map = build_knowledge_map(records, source_entries)
    docs_catalog = generate_skills_catalog(registry_payload)
    manifest = build_manifest(registry_payload, knowledge_map, chunks, embedding_config, embeddings)
    return SyncState(
        registry_payload=registry_payload,
        registry_records=records,
        knowledge_map=knowledge_map,
        chunks=chunks,
        docs_catalog=docs_catalog,
        embeddings=embeddings,
        manifest=manifest,
        source_entries=source_entries,
    )


def build_manifest(registry_payload: dict, knowledge_map: dict, chunks: list[dict], embedding_config, embeddings: list[dict]) -> dict:
    chunk_bytes = build_chunks_jsonl(chunks).encode("utf-8")
    return {
        "schema_version": 1,
        "skill_count": registry_payload["skill_count"],
        "chunk_count": len(chunks),
        "knowledge_source_count": len(knowledge_map["sources"]),
        "generated_from_hash": registry_payload["generated_from_hash"],
        "chunks_hash": hashlib.sha256(chunk_bytes).hexdigest(),
        "embeddings_enabled": embedding_config.enabled,
        "embedding_backend": embedding_config.backend if embedding_config.enabled else None,
        "embedding_count": len(embeddings),
    }


def build_chunks_jsonl(chunks: list[dict]) -> str:
    lines = [json.dumps(chunk, sort_keys=True) for chunk in chunks]
    return "\n".join(lines).rstrip() + "\n"


def expected_files(root: Path) -> list[Path]:
    return [
        root / "registry" / "skills.json",
        root / "registry" / "knowledge-map.json",
        root / "docs" / "SKILLS.md",
        root / "vector_index" / "chunks.jsonl",
        root / "vector_index" / "manifest.json",
        root / "vector_index" / "lexical.sqlite",
    ]


def write_state(root: Path, state: SyncState) -> list[str]:
    changed: list[str] = []
    (root / "registry" / "skills").mkdir(parents=True, exist_ok=True)
    (root / "vector_index").mkdir(parents=True, exist_ok=True)

    changed.extend(write_text_if_changed(root, root / "registry" / "skills.json", json.dumps(state.registry_payload, indent=2, sort_keys=True) + "\n"))
    changed.extend(write_text_if_changed(root, root / "registry" / "knowledge-map.json", json.dumps(state.knowledge_map, indent=2, sort_keys=True) + "\n"))
    changed.extend(write_text_if_changed(root, root / "docs" / "SKILLS.md", state.docs_catalog))
    changed.extend(write_text_if_changed(root, root / "vector_index" / "chunks.jsonl", build_chunks_jsonl(state.chunks)))
    changed.extend(write_text_if_changed(root, root / "vector_index" / "manifest.json", json.dumps(state.manifest, indent=2, sort_keys=True) + "\n"))

    for record in state.registry_records:
        filename = f"{record['category']}__{record['name']}.json"
        changed.extend(write_text_if_changed(root, root / "registry" / "skills" / filename, json.dumps(record, indent=2, sort_keys=True) + "\n"))

    chunks_hash = state.manifest["chunks_hash"]
    lexical_path = root / "vector_index" / "lexical.sqlite"
    before_hash = read_source_hash(lexical_path)
    build_lexical_index(lexical_path, state.chunks, chunks_hash)
    after_hash = read_source_hash(lexical_path)
    if before_hash != after_hash:
        changed.append(str(lexical_path.relative_to(root)).replace("\\", "/"))

    write_embeddings(root / "vector_index" / "embeddings.jsonl", state.embeddings)
    if state.embeddings:
        changed.append("vector_index/embeddings.jsonl")
    elif (root / "vector_index" / "embeddings.jsonl").exists():
        changed.append("vector_index/embeddings.jsonl")
    return sorted(set(changed))


def write_text_if_changed(root: Path, path: Path, content: str) -> list[str]:
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return []
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return [str(path.relative_to(root)).replace("\\", "/")]


def diff_state(root: Path, state: SyncState) -> list[str]:
    diffs: list[str] = []
    expected_texts = {
        root / "registry" / "skills.json": json.dumps(state.registry_payload, indent=2, sort_keys=True) + "\n",
        root / "registry" / "knowledge-map.json": json.dumps(state.knowledge_map, indent=2, sort_keys=True) + "\n",
        root / "docs" / "SKILLS.md": state.docs_catalog,
        root / "vector_index" / "chunks.jsonl": build_chunks_jsonl(state.chunks),
        root / "vector_index" / "manifest.json": json.dumps(state.manifest, indent=2, sort_keys=True) + "\n",
    }
    for path, expected in expected_texts.items():
        if not path.exists() or path.read_text(encoding="utf-8") != expected:
            diffs.append(str(path.relative_to(root)).replace("\\", "/"))

    for record in state.registry_records:
        filename = f"{record['category']}__{record['name']}.json"
        path = root / "registry" / "skills" / filename
        expected = json.dumps(record, indent=2, sort_keys=True) + "\n"
        if not path.exists() or path.read_text(encoding="utf-8") != expected:
            diffs.append(str(path.relative_to(root)).replace("\\", "/"))

    lexical_path = root / "vector_index" / "lexical.sqlite"
    if read_source_hash(lexical_path) != state.manifest["chunks_hash"]:
        diffs.append("vector_index/lexical.sqlite")

    embeddings_path = root / "vector_index" / "embeddings.jsonl"
    if state.embeddings:
        expected_embeddings = "\n".join(json.dumps(item, sort_keys=True) for item in state.embeddings) + "\n"
        if not embeddings_path.exists() or embeddings_path.read_text(encoding="utf-8") != expected_embeddings:
            diffs.append("vector_index/embeddings.jsonl")
    elif embeddings_path.exists():
        diffs.append("vector_index/embeddings.jsonl")
    return sorted(set(diffs))
