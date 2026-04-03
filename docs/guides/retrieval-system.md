# Retrieval System Guide

## Baseline

The baseline retrieval system is lexical and runs locally from `vector_index/lexical.sqlite`.

## Indexed Inputs

- skills
- references
- templates
- script docstrings
- repo-native knowledge topics
- imported knowledge
- official source manifest entries

## Optional Vectors

Embeddings are optional and controlled through `config/retrieval-config.yaml`.

If enabled, the retrieval pipeline writes `vector_index/embeddings.jsonl` and reranks lexical candidates using the configured backend.

## CLI

- `python3 scripts/build_index.py`
- `python3 scripts/search_knowledge.py "query"`
- `python3 scripts/search_knowledge.py "query" --json`

Search results are expected to surface ranked skills, supporting chunks, and related official-source context.
