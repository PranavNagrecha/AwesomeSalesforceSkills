# ADR 0001: Local Retrieval Framework

## Status

Accepted

## Decision

The repository uses a local-first retrieval framework built from committed Markdown, generated registry records, deterministic chunks, and a SQLite lexical index.

## Rationale

- no hosted infrastructure required
- deterministic committed artifacts for coding agents
- simpler contributor workflow than a server-backed vector stack
- optional vector reranking can be added without breaking baseline retrieval

## Consequences

- lexical retrieval is mandatory
- embeddings are optional
- generated artifacts are part of the normal authoring workflow
