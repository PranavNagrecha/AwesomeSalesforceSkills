# Eval Framework

This document defines the **golden eval** format used by
`evals/golden/<category>__<slug>.md` files and the pass criteria a skill must
meet to ship.

Evals are deliberately human-readable markdown. They are consumed by:

- **Humans** reviewing PRs against a skill.
- **LLMs** asked to grade an AI's output against the expected criteria.
- **`scripts/run_evals.py`** which performs structural checks and invokes a
  grader model per case.

---

## What a golden eval actually tests

Two distinct layers:

1. **Retrieval** — does the right SKILL get selected for a user query?
   This is already covered by `vector_index/query-fixtures.json`. Evals
   here **do not repeat** retrieval checks.
2. **Output quality** — given that the skill IS activated (and templates +
   decision trees are available), does the AI produce correct, safe,
   bulkified, production-grade output?

Golden evals focus on layer 2.

---

## File naming

`evals/golden/<category>__<slug>.md`

Examples:

- `evals/golden/apex__trigger-framework.md`
- `evals/golden/integration__bulk-api-2-patterns.md`
- `evals/golden/lwc__wire-service-patterns.md`

The double underscore `__` separates category from slug — mirroring the
convention already used in `registry/skills/`.

---

## File schema

Every eval file MUST contain, in this order:

```markdown
# Eval: <skill path, e.g. apex/trigger-framework>

- **Skill under test:** `skills/<category>/<slug>/SKILL.md`
- **Priority:** P0 | P1 | P2
- **Cases:** N
- **Last verified:** YYYY-MM-DD
- **Related templates:** `templates/...` (comma-separated)
- **Related decision trees:** `standards/decision-trees/...`

## Pass criteria

<short paragraph: what "passes" means for this skill specifically>

## Case 1 — <short descriptor>

**Priority:** P0 | P1 | P2

**User prompt:**

> "<verbatim user query>"

**Context provided (if any):**

- <bullet list of code / files / org-state the user supplied>

**Expected output MUST include:**

- <assertion 1>
- <assertion 2>
- ...

**Expected output MUST NOT include:**

- <anti-pattern 1>
- <anti-pattern 2>
- ...

**Rubric (grader scores each 0–5; 0=absent, 5=excellent):**

- **Correctness:** <what would count as correct for this case>
- **Completeness:** <what a complete answer covers>
- **Bulk safety:** <how the grader checks that no loop does SOQL/DML>
- **Security:** <FLS/CRUD/sharing expectations>
- **Citation of official docs:** <which docs should be linked>

**Reference answer (gold):**

<60–150 lines of the answer a 5/5 response would produce>

## Case 2 — ...
```

Missing sections cause `run_evals.py --structure` to fail.

---

## Priority levels

| Level | Meaning | Merge gate |
|---|---|---|
| **P0** | If this case fails, the skill is broken in production | Must score ≥4/5 on every rubric item |
| **P1** | Normal happy path; failure means degraded UX | Must score ≥3/5 on every rubric item; at least 80% of P1 cases pass |
| **P2** | Edge case / stretch scenario | Nice to have; informational only |

A skill SHIPS when:

- 100% of its P0 cases pass.
- ≥80% of its P1 cases pass.
- P2 failures are noted but not blocking.

---

## Scoring the rubric

Each rubric item is scored 0–5 by a grader (human or LLM):

| Score | Meaning |
|---|---|
| 0 | Completely absent or contradicts the expected answer |
| 1 | Mentioned but wrong |
| 2 | Correct direction, missing most detail |
| 3 | Correct, usable, missing 1–2 nuances |
| 4 | Correct and complete; minor wording issues only |
| 5 | Indistinguishable from the reference answer in quality |

Grader must cite specific lines of the AI's output when assigning a score <5.

---

## Adding a new eval

1. Copy `evals/golden/_template.md` (or the nearest existing file).
2. Fill in metadata block.
3. Write 3–5 cases. Prefer realistic user language over canned prompts.
4. Reference templates + decision trees in assertions where relevant.
5. Run `python3 scripts/validate_repo.py` to catch structural drift.
6. Run `python3 evals/scripts/run_evals.py --file evals/golden/<file>.md
   --dry-run` to sanity check format.

---

## When an eval fails

Order of operations (do not skip):

1. Is the **eval** wrong? (user intent ambiguous, rubric outdated for a new
   Salesforce release) → fix the eval, note in the "Last verified" field.
2. Is the **skill** wrong? → fix the SKILL.md and supporting files.
3. Is a **template** missing or broken? → fix the template.
4. Is the **decision tree** routing to the wrong skill? → fix the tree.

Never "retrain" prompts on eval cases — evals are the judge, not the
training set.

---

## Non-goals

- Evals are NOT retrieval tests. `query-fixtures.json` owns that.
- Evals are NOT unit tests for Apex/LWC code *inside* `templates/`.
  Those live next to the templates and run in a scratch org.
- Evals are NOT the single source of truth for a skill's correctness —
  the `standards/skill-content-contract.md` contract still applies.
