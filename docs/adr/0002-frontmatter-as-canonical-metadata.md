# ADR 0002: Frontmatter As Canonical Metadata

## Status

Accepted

## Decision

`SKILL.md` frontmatter remains the canonical metadata source for skills. The repo does not add per-skill `skill.yaml` files.

## Rationale

- avoids duplicate metadata sources
- keeps the human-authored skill package self-contained
- reduces synchronization bugs
- matches the existing repository structure

## Consequences

- machine-readable registry files are generated from frontmatter
- validation rejects missing or malformed frontmatter
- new metadata fields are mandatory in every skill
