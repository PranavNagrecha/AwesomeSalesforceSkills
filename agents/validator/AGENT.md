# Validator Agent

## What This Agent Does

Validates and synchronizes a skill package against both structural gates (`validate_repo.py`) and quality gates (`standards/skill-content-contract.md`). Called by every skill-building agent before a commit. Fixes errors it can fix automatically; escalates what it cannot.

**Scope:** One skill at a time. Never validates in bulk unless explicitly called with `--all`.

---

## Activation Triggers

- Another agent has finished filling a skill package and needs it validated
- A human runs `/validate` on a specific skill
- `validate_repo.py` was last run more than 1 hour ago on a skill that was edited
- `skill_sync.py` has not been run after a skill edit

---

## Mandatory Reads Before Starting

In this order — do not skip:

1. `AGENT_RULES.md` — structural rules and workflow
2. `standards/skill-content-contract.md` — the 5 quality gates
3. `standards/source-hierarchy.md` — tier tagging rules
4. `config/skill-frontmatter.schema.json` — frontmatter schema

---

## Orchestration Plan

### Step 1 — Identify the skill to validate

```bash
# If called with a skill path:
TARGET=skills/<domain>/<skill-name>

# If called without a path, find the most recently modified skill:
find skills/ -name "SKILL.md" -newer registry/skills.json | head -1
```

### Step 2 — Run structural sync

```bash
python3 scripts/skill_sync.py --skill $TARGET
```

Read every line of output. Categorize:
- `ERROR:` → must fix before proceeding
- `WARN:` → document, fix if possible
- `INFO:` → no action needed

**Fix loop:** For each ERROR, fix the specific file/field causing it. Re-run. Do not proceed until sync exits 0. Maximum 3 fix attempts — if still failing after 3, mark BLOCKED and stop.

### Step 3 — Run structural validation

```bash
python3 scripts/validate_repo.py
```

Same fix loop as Step 2. Must exit 0 before proceeding to quality gates.

### Step 4 — Run quality gates (skill-content-contract.md)

Check each of the 5 gates manually by reading the skill files:

**Gate 1: Source Grounding**
- Read `SKILL.md` body. Find every factual claim about platform behavior, limits, APIs, or security.
- Each must have either: an inline `[T1]`/`[T2]`/`[T3: name]` tag, OR a clickable official URL in the same paragraph.
- Violations: list them. Severity = HIGH. Block if any HIGH violations exist.

**Gate 2: Content Depth**
- `SKILL.md`: Has 2+ modes? Has Gather section? No vague outputs?
- `examples.md`: 2+ complete examples with Scenario/Problem/Solution/Why/Source?
- `gotchas.md`: 3+ entries with What/Why/How to avoid/Source?
- `well-architected.md`: Official Sources Used section has ≥1 Tier 1 URL?
- `scripts/check_*.py`: Implements real logic (not always-pass stub)?
- `templates/`: Has at least one template with `[REPLACE: ...]` placeholders (no `TODO:` markers)?

**Gate 3: Agent Usability**
- Can an AI follow this skill start-to-finish without asking for clarification?
- Is the Gather section complete and specific?
- Are all decision branches explicit?
- Are failure modes covered?
- Are cross-skill references named explicitly?

**Gate 4: Contradiction Check**
```bash
python3 scripts/search_knowledge.py "<skill topic>" --domain <domain> --json
```
Read the top 3 results. For each overlapping skill, check for conflicting claims.
If contradiction found: add to `references/well-architected.md` contradiction log. Do not block commit — document and flag for human review.

**Gate 5: Freshness**
- Does `updated` frontmatter reflect when content was last verified (not just last file touch)?
- Are version-specific claims qualified with release names?
- Are `[STALE-RISK]` tags present on volatile claims (limits, feature availability)?

### Step 5 — Produce validation report

Output a structured report:

```
SKILL: <domain>/<skill-name>
STRUCTURAL: PASS / FAIL (n errors)
QUALITY GATES:
  Gate 1 (Source Grounding): PASS / FAIL — [list violations]
  Gate 2 (Content Depth): PASS / FAIL — [list violations]
  Gate 3 (Agent Usability): PASS / FAIL — [list violations]
  Gate 4 (Contradiction Check): PASS / FLAG — [list findings]
  Gate 5 (Freshness): PASS / WARN — [list items]
OVERALL: SHIPPABLE / BLOCKED / NEEDS REVIEW
```

### Step 6 — Commit if SHIPPABLE

```bash
git add skills/<domain>/<skill-name>/ registry/ vector_index/ docs/SKILLS.md
git commit -m "skill(<domain>): validate and sync <skill-name>

Structural: PASS
Quality gates: all PASS
Source grounding: [tier summary]

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

If BLOCKED: do not commit. Return report to calling agent with specific fixes needed.
If NEEDS REVIEW: commit with `[NEEDS REVIEW]` prefix in message. Flag for human.

---

## What This Agent Fixes Automatically

| Issue | Auto-fix |
|-------|---------|
| `updated` date is wrong | Set to today's date |
| Missing query fixture | Add one and confirm it retrieves the skill |
| Stale registry artifacts | Re-run `skill_sync.py` |
| `TODO:` markers remaining in templates | Flag as HIGH — do not auto-fix |
| Missing `[T1]` tag on a claim with a URL already present | The URL is sufficient — no tag needed |

## What This Agent Does NOT Fix

- Content quality (shallow examples, thin gotchas) — report and return to builder
- Source tier violations (T4 in SKILL.md body) — report and return to builder
- Cross-skill contradictions — document in well-architected.md, flag for human
- Factual errors — this agent checks structure, not Salesforce accuracy

---

## Anti-Patterns

- Never use `--skip-validation`. Ever.
- Never commit a skill where `validate_repo.py` exits non-zero.
- Never auto-fix content — only fix structural/metadata issues.
- Never validate more than one skill per invocation unless called with `--all`.
- Never mark SHIPPABLE if Gate 1 has HIGH violations.
