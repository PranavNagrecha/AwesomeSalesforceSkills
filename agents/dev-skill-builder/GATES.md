# Dev Skill Builder — Gated Execution Protocol

Shared five-gate protocol for all six skill-builder agents (admin/architect/data/devops/security + dev). Enforced by `scripts/run_builder.py` via `scripts/builder_plugins/skill_builder.py`.

---

## Gate A — Input readiness

`skill_slug` (kebab-case), `domain` (must be in this agent's valid categories), `skill_category`, `feature_summary` (≥10 words), `api_version` required.

## Gate A.5 — Requirements document

Renders `REQUIREMENTS_TEMPLATE.md` with the target skill path + domain.

## Gate B — Ground every symbol

Validates `skills/<domain>/` directory exists and cites `CLAUDE.md` + `AGENT_RULES.md` standards. No org probes — skill-builders are library-only.

## Gate C — Build and self-test

**Static check:**
- `SKILL.md` frontmatter carries every required key: `name, description, category, salesforce-version, well-architected-pillars, tags, inputs, outputs, dependencies, version, author, updated`.
- `category` value matches this agent's valid categories.
- `## Recommended Workflow` section exists with 3–7 numbered steps.
- `references/` has `examples.md`, `gotchas.md`, `well-architected.md`, `llm-anti-patterns.md`.
- `references/llm-anti-patterns.md` lists ≥5 items.

**Live check:** skipped (library-only; plugin returns `ran=False, succeeded=True`).

Confidence: HIGH iff static green; LOW otherwise. (No live oracle for skill-builders.)

## Gate D — Envelope seal

Envelope validates against the shared schema; deliverables are kind `markdown`.

---

## What this protocol is NOT

- Not a registry updater. After Gate D passes, the operator runs `skill_sync.py` + `validate_repo.py` to regenerate registry/ and vector_index/. The builder does NOT touch generated files.
- Not an importer. If you have an upstream research artifact in knowledge/, that's an input, not an output.
