# Requirements — {{feature_summary_short}}

> Run ID: `{{run_id}}`
> Generated: `{{generated_at}}` (UTC)
> Agent: `dev-skill-builder` v{{agent_version}}
> Inputs packet SHA256: `{{inputs_sha256}}`

Approval anchor for the new skill package.

---

## 1. Feature statement

{{feature_summary}}

## 2. Target skill

- **Skill slug:** `{{skill_slug}}`
- **Domain directory:** `skills/{{domain}}/{{skill_slug}}/`
- **Frontmatter category:** `{{skill_category}}`
- **API version:** `{{api_version}}`
- **Emitted inventory:**
{{skill_inventory_bullets}}

## 3. Grounding contract (Gate B)

{{grounding_symbols_bullets}}

## 4. Quality bar

- `SKILL.md` frontmatter carries every required key per `CLAUDE.md` Required Skill Frontmatter section.
- `## Recommended Workflow` has 3–7 numbered steps.
- `references/llm-anti-patterns.md` lists ≥5 items.

## 5. Explicit non-goals

- Does not regenerate `registry/`, `vector_index/`, or `docs/SKILLS.md` — operator runs `skill_sync.py` + `validate_repo.py` after Gate D.
- Does not push to GitHub. Does not modify existing skills.

## 6. Approval

By re-invoking `run_builder.py --stage ground --approved-requirements <this file>`, the caller affirms Sections 1–2.
