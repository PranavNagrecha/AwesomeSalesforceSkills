"""Frontmatter parsing utilities for SKILL.md files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import datetime as _dt
import hashlib
import re

import yaml


FRONTMATTER_BOUNDARY = re.compile(r"^---\s*$", re.MULTILINE)


@dataclass(frozen=True)
class ParsedMarkdown:
    metadata: dict
    body: str


def parse_markdown_with_frontmatter(path: Path) -> ParsedMarkdown:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{path} is missing YAML frontmatter")

    closing_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing_index = index
            break
    if closing_index is None:
        raise ValueError(f"{path} has an unterminated YAML frontmatter block")

    metadata_text = "\n".join(lines[1:closing_index])
    body = "\n".join(lines[closing_index + 1 :]).lstrip()
    metadata = yaml.safe_load(metadata_text) or {}
    if not isinstance(metadata, dict):
        raise ValueError(f"{path} frontmatter must parse to an object")
    metadata = normalize_metadata(metadata)
    return ParsedMarkdown(metadata=metadata, body=body)


def normalize_metadata(metadata: dict) -> dict:
    normalized = {}
    for key, value in metadata.items():
        if isinstance(value, _dt.date):
            normalized[key] = value.isoformat()
        else:
            normalized[key] = value
    return normalized


def stable_hash_for_files(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda value: str(value).replace("\\", "/")):
        digest.update(str(path).replace("\\", "/").encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()
