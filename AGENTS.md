# AGENTS.md

Repo-local agent instructions live in [AGENT_RULES.md](./AGENT_RULES.md).

Any coding agent working in this repository must:

1. Read `AGENT_RULES.md` before creating or materially revising a skill.
2. Treat `SKILL.md` frontmatter as the canonical skill metadata source.
3. Use `python3 scripts/search_knowledge.py` before creating a new skill or claiming a coverage gap.
4. Run `python3 scripts/skill_sync.py` and `python3 scripts/validate_repo.py` after skill changes.
5. Never hand-edit generated files in `registry/`, `vector_index/`, or `docs/SKILLS.md`.
