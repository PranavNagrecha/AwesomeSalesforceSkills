# /new-skill — New Skill Workflow

Triggers the **skill-builder** agent.

## Usage

```
/new-skill
```

The agent checks local coverage first, asks targeted questions, then uses `new_skill.py` to scaffold a compliant package. Content is filled into the scaffold — the structure is never written from scratch.

## What Happens

### Step 1 — Coverage Check (do not skip)

```bash
python3 scripts/search_knowledge.py "<topic>" --domain <domain>
```

If `has_coverage: true` is returned, review the existing skill before creating a new one. Extend or differentiate — do not duplicate.

### Step 2 — Scaffold

```bash
python3 scripts/new_skill.py <domain> <skill-name>
```

This creates the full directory structure:

```
skills/<domain>/<skill-name>/
├── SKILL.md                         ← pre-filled with TODO markers (includes Recommended Workflow section)
├── references/
│   ├── examples.md                  ← pre-filled with TODO markers
│   ├── gotchas.md                   ← pre-filled with TODO markers
│   ├── well-architected.md          ← official sources PRE-SEEDED for domain
│   └── llm-anti-patterns.md         ← 5+ AI-specific mistakes to avoid
├── templates/<skill-name>-template.md
└── scripts/check_<noun>.py          ← stdlib-only checker stub
```

`new_skill.py` will warn if coverage already exists and ask for confirmation.

### Step 3 — Fill All TODOs

Every file created by the scaffold has `TODO:` markers. Fill them all:

- `SKILL.md` — description (must include "NOT for ..."), triggers (3+, 10+ chars each), tags, inputs, outputs, well-architected-pillars, full body (300+ words), and `## Recommended Workflow` (3–7 numbered agent steps)
- `references/examples.md` — real examples with context, problem, solution
- `references/gotchas.md` — non-obvious platform behaviors
- `references/well-architected.md` — WAF notes; official sources are pre-seeded, add usage context
- `references/llm-anti-patterns.md` — 5+ mistakes AI assistants make in this domain: wrong output, why it happens, correct pattern, detection hint
- `scripts/check_<noun>.py` — implement the actual checks (stdlib only)

**Apply the authoring style guide:** read `standards/skill-authoring-style.md` before filling SKILL.md. The guide defines voice (trust the model on Salesforce primitives, lead with the executable artifact), structural patterns (executable code, comparison tables, field-mapping tables, copy-paste metadata snippets), per-category expectations, and a 5-question pre-submit checklist. The 6 anti-patterns in § 6 of the guide are the most common shape mistakes to avoid.

### Step 4 — Sync (validates first, then writes)

```bash
python3 scripts/skill_sync.py --skill skills/<domain>/<skill-name>
```

Validation runs automatically before any artifact is written. If errors are reported, fix them and re-run. Sync will not produce artifacts from a broken skill.

### Step 5 — Add Query Fixture

Add an entry to `vector_index/query-fixtures.json`:

```json
{
  "query": "natural-language query a practitioner would type",
  "domain": "<domain>",
  "expected_skill": "<domain>/<skill-name>",
  "top_k": 3
}
```

Then verify:

```bash
python3 scripts/validate_repo.py
```

All fixture queries must pass retrieval. Skills without a fixture produce a WARN that fails CI.

### Step 6 — Wire the skill into the run-time agents that need it

Decide which run-time agents should cite this skill. A skill that no agent reads is only available to humans + lexical search. Read `agents/_shared/SKILL_MAP.md` and `agents/_shared/RUNTIME_VS_BUILD.md` to pick targets — usually 1–3 agents, rarely more.

Then patch each:

```bash
python3 scripts/patch_agent_skill.py <agent-id> <domain>/<skill-name> "<section-heading>" "<short description>"
```

The helper updates both the agent's YAML `dependencies.skills:` and its `## Mandatory Reads Before Starting` section, renumbering the bullet list correctly. Use `*end*` as the section heading when the agent's Mandatory Reads is a flat numbered list (no `### subsection` headings).

If the target agent has an entry in `agents/_shared/SKILL_MAP.md` (Wave A/B/C agents), add the skill to that entry too.

Skills authored as pure human reference (rare) may opt out by setting `runtime_orphan: true` in frontmatter — everything else is expected to be cited by at least one agent. `validate_repo.py` emits a WARN for orphan skills.

## Quality Gate

A skill is not complete unless:

- `python3 scripts/validate_repo.py` exits 0 with no errors.
- The skill is cited by at least one run-time agent (or marked `runtime_orphan: true`).

## Agent

See `agents/skill-builder/AGENT.md` for full orchestration plan.
