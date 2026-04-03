# Agent Rules

This file is the canonical rulebook for any coding agent working in this repository, including Claude, Codex, and GPT-based tooling.

## Core Rule

No new skill or skill update is complete until the repository metadata, retrieval artifacts, and generated docs are synchronized — and `validate_repo.py` exits clean.

## Authoritative Sources

- `SKILL.md` frontmatter is the canonical metadata source for every skill.
- `standards/official-salesforce-sources.md` is the canonical official-doc source map.
- `knowledge/sources.yaml` is the canonical retrieval source manifest.
- `registry/` and `vector_index/` are generated artifacts. Do not edit them manually.

## Required Workflow For Any New Skill

### Step 1 — Check Coverage First (mandatory)

```bash
python3 scripts/search_knowledge.py "<topic>" --domain <domain>
```

If `has_coverage: true` is returned, a skill already exists. Extend it — do not create a duplicate.

### Step 2 — Scaffold (never write from scratch)

```bash
python3 scripts/new_skill.py <domain> <skill-name>
```

This creates the full package with pre-filled TODO markers and pre-seeded official sources. You fill the TODOs — you do not design the structure.

### Step 3 — Fill All TODOs

Every file created by the scaffold contains `TODO:` markers. Every marker must be replaced with real content before sync will succeed. Specifically:

- `SKILL.md` — description (must include "NOT for ..."), triggers (3+, natural-language symptom phrases, 10+ chars each), tags, inputs, outputs, well-architected-pillars, body (300+ words)
- `references/examples.md` — real examples with context, problem, solution
- `references/gotchas.md` — non-obvious platform behaviors
- `references/well-architected.md` — WAF notes; official sources are pre-seeded, add usage context
- `scripts/check_<noun>.py` — implement actual checks, stdlib only

### Step 4 — Sync (validates first, hard stop on errors)

```bash
python3 scripts/skill_sync.py --skill skills/<domain>/<skill-name>
```

Validation runs before any artifact is written. If errors are reported, fix them and re-run. Sync will not produce artifacts from a broken skill. Do not use `--skip-validation`.

### Step 5 — Add Query Fixture and Validate

Add an entry to `vector_index/query-fixtures.json`:

```json
{
  "query": "natural-language query a practitioner would type",
  "domain": "<domain>",
  "expected_skill": "<domain>/<skill-name>",
  "top_k": 3
}
```

Then run:

```bash
python3 scripts/validate_repo.py
```

This must exit 0. Fix all errors before committing.

### Step 6 — Commit

Commit all of:

- the skill package under `skills/`
- generated files in `registry/`
- generated files in `vector_index/`
- generated `docs/SKILLS.md`

---

## Architect Domain

Architect skills live in `skills/architect/` with `category: architect`.
They do NOT go in `skills/admin/`.

When routing a task for the Architect role:
- Domain folder: `architect`
- `category` frontmatter: `architect`
- Scaffold: `python3 scripts/new_skill.py architect <skill-name>`

This is enforced by `validate_repo.py` — `category` must match the parent folder name.

---

## Supporting Scripts (use these — they exist)

Beyond the required workflow scripts, the following are available:

| Script | Purpose | Usage |
|--------|---------|-------|
| `scripts/skill_graph.py` | Related-skill navigator — finds skills connected by shared tags, domain, or trigger overlap | `python3 scripts/skill_graph.py <domain/skill-name>` |
| `scripts/search_skills.py` | Registry-level search across all skill metadata (faster than knowledge search for skill-ID lookups) | `python3 scripts/search_skills.py "<query>"` |
| `scripts/export_skills.py` | Exports skill registry to CSV or JSON for external tooling | `python3 scripts/export_skills.py --format json` |

Use `skill_graph.py` when writing cross-skill references in `references/well-architected.md`.
Use `search_skills.py` for duplicate checking before scaffold (faster than full knowledge search).

---

## Retrieval Rules

- Always use `python3 scripts/search_knowledge.py "<query>"` before claiming that a new skill does not already exist or that a topic has no local coverage.
- Lexical retrieval is the required baseline and must remain functional with no API keys or cloud services.
- Embeddings are optional and must never be required for normal authoring, validation, or review flows.

### Interpreting Search Results

The JSON output of `search_knowledge.py` includes a `has_coverage` boolean:

- **`has_coverage: true`** — at least one skill scored above the confidence threshold. Use the top skill(s) to guide your response.
- **`has_coverage: false`** — no skill is confident enough. Do NOT present low-scoring skills as answers. Instead:
  1. Tell the user the repo has no skill for this topic yet.
  2. Surface `official_sources` from the result — these are always returned regardless of coverage.
  3. If this came up during a `/new-skill` flow, treat it as a confirmed gap and proceed with skill creation.

Never present a skill to the user when `has_coverage` is false. The score threshold exists precisely to prevent confidently wrong answers.

---

## Skill Identity Rules

These are enforced by `validate_repo.py` and `skill_sync.py` — they cause a hard failure:

- The `name` frontmatter field **must exactly match** the skill's folder name (e.g. folder `soql-security` → `name: soql-security`).
- The `category` frontmatter field **must exactly match** the parent domain folder (e.g. folder `skills/apex/` → `category: apex`).
- The `description` field **must include an explicit scope exclusion** — at least one "NOT for ..." clause. This is what keeps the skill from activating on unrelated queries.
- The SKILL.md body must have at least 300 words. Do not commit stub skills.
- `## Official Sources Used` in `references/well-architected.md` must have at least one source listed under the heading — not just the heading itself. Official sources are pre-seeded by `new_skill.py`; do not delete them.

---

## Query Fixture Requirement

Every skill must have at least one entry in `vector_index/query-fixtures.json`. When you create or rename a skill:

1. Choose a natural-language query a practitioner would actually type for this skill's topic.
2. Run `python3 scripts/search_knowledge.py "<query>" --domain <domain> --json` and confirm the skill appears in the top 3 results.
3. Add an entry to `vector_index/query-fixtures.json`:
   ```json
   {
     "query": "your query here",
     "domain": "apex",
     "expected_skill": "apex/skill-name",
     "top_k": 3
   }
   ```
4. Run `python3 scripts/validate_repo.py` — the fixture must pass retrieval, not just exist.

Skills with no fixture will produce a WARN during validation. WARNs are advisory — they print but do not fail the exit code. Only ERRORs cause a non-zero exit.

---

## Rejection Conditions

A skill must be rejected (do not sync, do not commit) if any of the following is true:

- frontmatter is missing required keys
- `name` does not match folder name
- `category` does not match parent domain folder
- `description` has no scope exclusion ("NOT for ...")
- SKILL.md body is under 300 words
- required skill package files are missing
- `## Official Sources Used` section is absent or empty
- generated registry/docs/index outputs are stale
- the skill has no query fixture entry
- the skill duplicates an existing skill without a clear disambiguation
- skill-local checker scripts require pip dependencies without explicit documentation
- `skill_sync.py` exits non-zero for this skill

---

## Official Sources Policy

Every skill must be grounded in official Salesforce documentation. When writing skill content:

1. Check `standards/official-salesforce-sources.md` for authoritative sources in the skill's domain.
2. Official sources for the domain are pre-seeded in `references/well-architected.md` by `new_skill.py`.
3. Do not make factual claims about Salesforce platform behavior, limits, or APIs without an official source.
4. Local knowledge sharpens guidance — it does not override official behavior claims.
5. When `has_coverage: false`, always surface `official_sources` from the search result before saying there is no guidance.

---

## Rules For Editing Generated Artifacts

- Do not hand-edit files in `registry/`, `vector_index/`, or `docs/SKILLS.md`.
- Regenerate them through `python3 scripts/skill_sync.py --all`.

---

## Rules For Repo-Wide Changes

When changing standards, retrieval behavior, or authoring workflow:

1. Update the relevant source docs:
   - `AGENT_RULES.md`
   - `CLAUDE.md`
   - `commands/new-skill.md`
   - relevant agent definitions
2. Re-run `python3 scripts/skill_sync.py --all`
3. Re-run `python3 scripts/validate_repo.py`

---

## Rule Of Simplicity

Prefer deterministic local scripts, generated JSON, and committed artifacts over hidden state, cloud dependencies, or one-off manual exceptions.
