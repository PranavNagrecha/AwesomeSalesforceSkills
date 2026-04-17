# Devops Skill Builder — Gated Execution Protocol

Shares the five-gate protocol with all six skill-builder agents. Enforced by `scripts/run_builder.py` via `scripts/builder_plugins/skill_builder.py`. See `agents/dev-skill-builder/GATES.md` for the canonical contract — this agent differs only in valid `domain`/`category` (`admin`).

## Gate A — Input readiness
`skill_slug` (kebab-case), `domain=devops`, `skill_category=devops`, `feature_summary` (≥10 words), `api_version` required.

## Gate A.5 — Requirements document
Renders `REQUIREMENTS_TEMPLATE.md` with the target skill path.

## Gate B — Ground every symbol
Cites `CLAUDE.md` + `AGENT_RULES.md`. No org probes.

## Gate C — Build and self-test
Static-only (library mode). Checks: frontmatter required keys, category value, `## Recommended Workflow` (3–7 numbered steps), four `references/` files, `llm-anti-patterns.md` ≥5 items.

## Gate D — Envelope seal
Shared schema; deliverables kind `markdown`.
