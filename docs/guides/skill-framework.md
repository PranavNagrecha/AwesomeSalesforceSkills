# Skill Framework Guide

## What This Framework Adds

- strict frontmatter metadata
- generated skill registry
- generated retrieval chunks and lexical index
- generated skill catalog docs
- local search CLI for skill discovery

## Canonical Flow

1. Search local coverage with `python3 scripts/search_knowledge.py "<topic>"`
2. Check the relevant official Salesforce docs
3. Edit a skill package in `skills/`
4. Run `python3 scripts/skill_sync.py --skill skills/<domain>/<skill-name>`
5. Run `python3 scripts/validate_repo.py`
6. Commit the skill and generated artifacts together

## Generated Areas

- `registry/`
- `vector_index/`
- `docs/SKILLS.md`

Do not edit those by hand.
