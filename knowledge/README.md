# Knowledge Corpus

This directory is the canonical local knowledge layer for the repo-native retrieval system.

## What Belongs Here

- `topics/` for repo-native retrieval notes, authoring guidance, and framework-specific knowledge
- `imports/` for curated imported markdown copied from sibling or external local sources
- `sources.yaml` for the canonical manifest of retrievable local and official sources

## Rules

- Keep canonical knowledge text in Markdown.
- Do not store large raw PDFs here. Extract and curate them into Markdown first.
- Imported content must preserve provenance in the destination path or file header.
- Retrieval artifacts are generated into `vector_index/`, not stored here.
