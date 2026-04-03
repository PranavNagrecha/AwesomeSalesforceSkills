# Framework Overview

## Purpose

This repository now treats skills as both human-authored guidance packages and machine-discoverable retrieval assets.

## Core Rules

- `SKILL.md` frontmatter is canonical metadata.
- Generated registry and retrieval files are never hand-edited.
- Lexical retrieval must always work even when embeddings are disabled.
- Every new skill must be synchronized through the repo pipeline before it is considered complete.

## Retrieval Priorities

1. Exact skill-name and tag matches
2. Strong lexical matches from skill content and references
3. Official source guidance related to the topic
4. Optional vector reranking when embeddings are enabled
