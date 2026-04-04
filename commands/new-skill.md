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

## Quality Gate

A skill is not complete unless `python3 scripts/validate_repo.py` exits 0 with no errors.

## Agent

See `agents/skill-builder/AGENT.md` for full orchestration plan.
