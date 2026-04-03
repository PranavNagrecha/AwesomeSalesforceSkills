# Retrieval Guidelines

## Canonical Inputs

The retrieval system indexes:

- skill frontmatter
- `SKILL.md` narrative content
- reference markdown
- template comments and headings
- skill script docstrings and help text
- repo-native knowledge topics
- curated imported markdown
- official source manifest summaries

## Ranking Goals

- favor exact and near-exact skill matches
- surface the most directly relevant chunks first
- keep official sources visible when a result makes factual platform claims
- avoid requiring embeddings for baseline usefulness
