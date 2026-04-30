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

### Step 6 — Check whether any existing agent should cite this skill

This is a **judgment** step, not a sweep. Walk the existing run-time agent roster and decide, for each plausible candidate, whether this skill genuinely belongs in its `Mandatory Reads`. The bar is high: an agent should cite a skill only when reading it would meaningfully change the agent's output for a real invocation. If you cannot answer "in which scenario would this agent's output be wrong without reading this skill?", the skill does not belong in that agent.

How to walk the roster:

1. Read `agents/_shared/RUNTIME_VS_BUILD.md` (full roster) and `agents/_shared/SKILL_MAP.md` (Wave A/B/C citations).
2. Generate a shortlist of 3–6 candidate agents whose domain overlaps the skill.
3. For each candidate, ask: would an agent ignoring this skill produce a worse answer in a real scenario? Be specific — name the scenario.
4. Wire only the candidates that pass. Zero is a valid outcome — some skills are pure human / lexical-retrieval reference and don't fit any current agent. Don't dilute an agent's `Mandatory Reads` with skills it would never reach for.

Wire the agents that pass:

```bash
python3 scripts/patch_agent_skill.py <agent-id> <domain>/<skill-name> "<section-heading>" "<short description>"
```

The helper updates both the agent's YAML `dependencies.skills:` and its `## Mandatory Reads Before Starting` section, renumbering correctly. Use `*end*` for flat numbered lists.

If a wired agent has an entry in `agents/_shared/SKILL_MAP.md` (Wave A/B/C agents), update that entry too.

If you found zero fits, do nothing. Future agents may pick the skill up. The orphan WARN is a flag, not a gate — `validate_repo.py` still passes. If the skill is *intentionally* human-reference (rare), set `runtime_orphan: true` in frontmatter to silence the WARN with explicit intent.

## Quality Gate

A skill is not complete unless `python3 scripts/validate_repo.py` exits 0 with no errors. Orphan-skill warnings are advisory, not blocking — they signal "consider wiring," not "must wire."

## Agent

See `agents/skill-builder/AGENT.md` for full orchestration plan.
