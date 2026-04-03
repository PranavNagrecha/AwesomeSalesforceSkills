"""Deterministic chunking utilities for markdown and text sources."""

from __future__ import annotations

from pathlib import Path
import hashlib
import re


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
MAX_CHUNK_CHARS = 1200


def chunk_markdown(source_id: str, title: str, path: str, domain: str | None, chunk_kind: str, source_trust: str, official_source_ids: list[str], skill_id: str | None, tags: list[str], text: str) -> list[dict]:
    sections = split_markdown_sections(text)
    chunks: list[dict] = []
    for index, (section_title, section_text) in enumerate(sections):
        for piece_index, piece in enumerate(split_large_text(section_text)):
            chunk_id = stable_chunk_id(source_id, section_title, index, piece_index)
            chunks.append(
                {
                    "id": chunk_id,
                    "source_id": source_id,
                    "title": section_title or title,
                    "path": path,
                    "domain": domain,
                    "chunk_kind": chunk_kind,
                    "source_trust": source_trust,
                    "official_source_ids": official_source_ids,
                    "skill_id": skill_id,
                    "text": piece.strip(),
                    "tags": tags,
                }
            )
    return chunks


def split_markdown_sections(text: str) -> list[tuple[str, str]]:
    lines = text.splitlines()
    sections: list[tuple[str, list[str]]] = []
    # Empty title means "use the document title" when no heading has been seen yet.
    current_title = ""
    current_lines: list[str] = []

    for line in lines:
        match = HEADING_RE.match(line)
        if match:
            if current_lines:
                sections.append((current_title, current_lines))
            current_title = match.group(2).strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_title, current_lines))

    return [(title, "\n".join(section_lines).strip()) for title, section_lines in sections if "\n".join(section_lines).strip()]


def split_large_text(text: str) -> list[str]:
    if len(text) <= MAX_CHUNK_CHARS:
        return [text]
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    pieces: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= MAX_CHUNK_CHARS:
            current = candidate
        else:
            if current:
                pieces.append(current)
            if len(paragraph) <= MAX_CHUNK_CHARS:
                current = paragraph
            else:
                for start in range(0, len(paragraph), MAX_CHUNK_CHARS):
                    pieces.append(paragraph[start : start + MAX_CHUNK_CHARS])
                current = ""
    if current:
        pieces.append(current)
    return pieces


def stable_chunk_id(source_id: str, section_title: str, index: int, piece_index: int) -> str:
    raw = f"{source_id}::{section_title}::{index}::{piece_index}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:20]
