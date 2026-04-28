---
name: uat-test-case-design
description: "Use this skill when designing the human-executable UAT test cases that prove a Salesforce feature works for a specific persona — the per-persona scripts with preconditions, data setup, permission setup, ordered steps, and pass/fail evidence that close out an RTM row. Trigger keywords: UAT test case salesforce, user acceptance test script salesforce, manual test salesforce feature, UAT script per persona, UAT precondition data setup, UAT permission set assignment for testing, negative path UAT case. NOT for high-level UAT planning, defect classification, regression strategy, or sign-off (use admin/uat-and-acceptance-criteria). NOT for the Given/When/Then technique used to write the AC the case is derived from (use admin/acceptance-criteria-given-when-then). NOT for Apex test method generation (use agents/test-generator). NOT for test data factory patterns (use templates/apex/tests/TestDataFactory.cls). NOT for performance or load testing."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - User Experience
triggers:
  - "how do I write a UAT test case salesforce per persona"
  - "user acceptance test script salesforce template precondition steps"
  - "manual test salesforce feature with permission set and data setup"
  - "how do I write a negative path UAT case for a Salesforce story"
  - "UAT script schema with story id and AC id traceability"
  - "what permissions should a UAT tester have before running the script"
  - "how do I capture pass fail evidence from a UAT run"
tags:
  - uat
  - test-case
  - testing
  - business-analysis
  - traceability
inputs:
  - "User story with story_id and acceptance criteria block (ideally Given/When/Then)"
  - "Persona definition — the profile or permission set group that runs the case"
  - "Sandbox name and environment configuration where the case will execute"
  - "Permission set group (PSG) the persona is assigned for the feature under test"
  - "Reference data shape — records or imports the case depends on"
outputs:
  - "Per-persona UAT test case in the canonical schema (case_id, story_id, ac_id, persona, precondition, data_setup, permission_setup, steps, expected_result, actual_result, pass_fail, evidence_url, tester, executed_at)"
  - "Negative-path UAT case for at least one failure mode per story"
  - "Data-setup checklist the tester runs before the script"
  - "Permission-setup checklist (PSG to assign, profile NOT to test as)"
  - "RTM-ready evidence row linking the case back to story_id + ac_id"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# UAT Test Case Design

This skill activates when a Business Analyst, QA lead, or admin needs to convert acceptance criteria into the per-persona, human-executable UAT scripts that prove a Salesforce feature works in the UI. It is the script-authoring layer beneath the broader UAT plan — it does not own sign-off, defect taxonomy, or regression strategy.

---

## Before Starting

Gather this context before writing a single case:

- **Is the AC block testable?** Cases derive 1-to-1 (or 1-to-N) from acceptance criteria scenarios. If the AC is vague ("the page should be intuitive"), stop and route the work back to `admin/acceptance-criteria-given-when-then` before authoring scripts.
- **Who is the persona?** A UAT case is meaningless without a persona. Capture the profile + permission set group the tester will be assigned. Never test as System Administrator — that posture invalidates the FLS, sharing, and CRUD checks the case is supposed to prove.
- **What sandbox is the build deployed in?** Cases must reference the sandbox by name. A case that ran in a developer sandbox with no production-like data is not the same evidence as a case run in a Full sandbox.
- **What data state is required?** A case that fails because a parent Account did not exist is a setup failure, not a feature failure. Data setup must be explicit before the steps begin.
- **Is there a negative path?** Every story needs at least one UAT case that proves the feature blocks the wrong action — invalid input, wrong persona, missing required field. Happy-path-only UAT lets P1 security and validation defects through.

---

## Core Concepts

### The Canonical UAT Case Schema

A UAT test case is a structured artifact, not a paragraph. The canonical schema this skill enforces:

| Field | Type | Required | Notes |
|---|---|---|---|
| `case_id` | string | yes | Unique within release, e.g. `UAT-OPP-001` |
| `story_id` | string | yes | Source user story — required for RTM traceability |
| `ac_id` | string | yes | Source acceptance criterion — exactly one AC scenario per case |
| `persona` | string | yes | Profile or permission set group name, never "Admin" |
| `negative_path` | boolean | yes | Default false; ≥1 case per story must be true |
| `precondition` | string | yes | Human-readable starting state |
| `data_setup` | array | yes | Ordered list of records / imports to seed before steps |
| `permission_setup` | array | yes | PSGs to assign to tester user before steps |
| `steps` | array | yes | Ordered click-level steps; ≥2 entries |
| `expected_result` | string | yes | Verbatim from the AC's `then` clause |
| `actual_result` | string | filled at run | What the tester actually saw |
| `pass_fail` | enum | filled at run | `Pass` / `Fail` / `Blocked` / `Not Run` |
| `evidence_url` | string | filled at run | Link to screenshot or recording — never inline |
| `tester` | string | filled at run | Username of the human who ran it |
| `executed_at` | datetime | filled at run | UTC timestamp |

The first ten fields are authored before execution. The last five are filled at run time and become the evidence row that closes an RTM cell.

### One AC Scenario → One UAT Case (or More)

A common failure mode is "one case per click" or "one case per story." Both miss the AC granularity. The correct decomposition:

1. Each AC scenario (`Given/When/Then` block) maps to **at least one** UAT case.
2. If the AC scenario applies to multiple personas with different expected outcomes, split into one case per persona.
3. If the AC scenario has multiple boundary values (e.g. credit limit at 0, at threshold, at threshold+1), split into one case per boundary.

This guarantees the UAT cases collectively prove every AC, which is the contract the RTM relies on.

### Data Setup Discipline

The case body must not silently assume records exist. If the case requires "an Account with Type = Customer and credit limit > 50000," that requirement lives in the `data_setup` array. Two acceptable seeding approaches:

- **Manual UI seed** — for small, story-specific records the tester creates in the sandbox before running steps.
- **Apex factory seed** — for bulk or relationship-heavy seeds, reference `templates/apex/tests/TestDataFactory.cls` and invoke from anonymous Apex. UAT cases that depend on >5 records per run should use the factory.

Never seed in production. UAT runs in a sandbox.

### Permission Setup Discipline

The single largest UAT antipattern is testing as System Administrator. The Sys Admin profile bypasses FLS, sharing rules, validation behavior tied to permissions, and most CRUD restrictions. A case that passes as Sys Admin proves nothing about the persona.

Permission setup rules:

1. The tester user runs with the persona's standard profile (often a Minimum Access / read-only baseline) plus the **PSG that grants the feature**.
2. The PSG to assign is named explicitly in `permission_setup` — not "the right perms," not "the dev's profile."
3. If the feature is gated by a permission set (not a PSG), the case must still cite that permission set.
4. If the case's intent is to prove the feature is **denied** to a persona, the persona is set up **without** the PSG and the expected_result is the deny.

### Negative-Path Coverage

Every story needs at least one case where `negative_path: true`. Examples:

- Required field omitted → save fails with the validation rule's error message
- Wrong persona attempts the action → permission error, not silent success
- Boundary value just past the limit → block, not allow
- Stage skip (e.g. Closed Won without a Close Date) → validation rejects

Without a negative-path case, the UAT run only proves the feature works when used correctly. It does not prove the feature is safe.

---

## Common Patterns

### Pattern: Decompose an AC Block into UAT Cases

**When to use:** A story arrives with a Given/When/Then AC block from `admin/acceptance-criteria-given-when-then`. You need the UAT scripts.

**How it works:**

1. Read each `Scenario:` in the AC block. Each scenario produces ≥1 case.
2. For each scenario, identify which personas it applies to. Split per persona where outcomes differ.
3. Capture the persona's PSG into `permission_setup`. If the persona name is "Sales Rep — Pipeline Edition," the PSG is the one named in the security model, not "Sales Profile."
4. Translate the `Given` clause into `precondition` + `data_setup`. Records are seeded; user state is precondition.
5. Translate the `When` clause into ordered `steps` at click-level detail.
6. Copy the `Then` clause verbatim into `expected_result`.
7. Add `negative_path: true` cases for the AC's failure scenarios. Most AC blocks have at least one — extract them, do not invent new ones.

**Why not the alternative:** Writing cases freehand from the story description (without the AC block) drifts from what was contracted. Cases must be evidence that the AC was met, not evidence that "something works."

### Pattern: UAT Case for a Bulk Data Loader Run

**When to use:** The feature under test is a data import, dedupe rule, or matching rule, executed via Data Loader rather than the standard UI.

**How it works:**

1. Treat the Data Loader run as a UI action — the persona is the user running Data Loader, not the integration user.
2. `data_setup` includes the source CSV file with row counts and the field mapping.
3. `permission_setup` includes the PSG that grants the API + Bulk API permissions to the loader user, plus object CRUD on the target.
4. Steps include the loader configuration: object, operation, mapping file, batch size.
5. `expected_result` covers both the success count and the failure count (e.g. "47 inserted, 3 rejected by duplicate rule").
6. Negative-path companion case: load a CSV with a known duplicate to prove the dup rule fires.

### Pattern: UAT Case for a Lightning Record Page

**When to use:** The feature is a Lightning page layout change for a specific record type + persona combination.

**How it works:**

1. The persona's PSG controls the page-layout assignment indirectly via the profile + record type matrix. `permission_setup` cites both.
2. `precondition` names the exact record type and the record ID (or seeds one).
3. Steps walk through render, edit, sharing visibility, and any quick action present on the page.
4. Expected_result names every field/section that should be visible — not "page renders correctly."

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| AC arrives in narrative form, not Given/When/Then | Reject and route to `admin/acceptance-criteria-given-when-then` first | Narrative AC produces ambiguous cases; split-per-scenario is impossible without a structured AC |
| Persona is "Admin" or "Internal User" | Reject — get the specific profile/PSG name | Generic personas hide FLS and CRUD bugs |
| Story has only happy-path AC | Add a negative-path case and flag the AC as incomplete | Happy-path-only UAT lets P1 security defects through |
| Data setup requires >5 related records | Reference `templates/apex/tests/TestDataFactory.cls` from anonymous Apex | Manual seeding for >5 records is error-prone and slow |
| Tester proposes running as System Admin "to save time" | Refuse and require the persona's PSG | A Sys Admin run proves nothing about persona behavior |
| Same AC scenario, two personas, different expected results | Two cases — one per persona | Single case cannot record divergent outcomes |
| Feature is automated time-based (scheduled flow) | Document the time advancement step in `data_setup`; do not silently wait | Sandboxes do not advance scheduled jobs by waiting |
| Feature is in beta — UI element labels may shift | Cite the element by `data-id` or developer name where possible, not visible label | Beta UI churn invalidates cases otherwise |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Intake the story + AC + persona.** Confirm the AC block is in Given/When/Then form (per `admin/acceptance-criteria-given-when-then`) and the persona has a named profile + PSG. Reject if not.
2. **Decompose AC scenarios into UAT cases.** Each scenario → ≥1 case. Split per persona and per boundary where outcomes diverge. Mark at least one case `negative_path: true`.
3. **Define data setup per case.** List records/imports in order. For >5 records, cite `templates/apex/tests/TestDataFactory.cls`. Sandbox only.
4. **Define permission setup per persona.** Name the PSG to assign. Never "Sys Admin." Include a "do not assign" note for negative deny-cases.
5. **Write step-by-step + expected.** Click-level steps (≥2). Expected_result copied verbatim from the AC's `then` clause. Use developer names for UI elements when possible.
6. **Execute + capture pass/fail evidence.** Tester runs, records `actual_result`, sets `pass_fail` from the enum {Pass, Fail, Blocked, Not Run}, attaches `evidence_url` (screenshot or recording link).
7. **Link results back to RTM.** Write the `case_id` + `pass_fail` + `evidence_url` into the RTM row keyed by `story_id` + `ac_id`. The RTM cell is closed when at least one case per AC scenario passes and at least one negative-path case per story passes.

---

## Review Checklist

Run through these before declaring the case set ready for execution:

- [ ] Every case has `story_id`, `ac_id`, and a named persona (not "Admin")
- [ ] Every story has at least one case with `negative_path: true`
- [ ] Every case has a non-empty `data_setup` array (or an explicit "no setup needed" note if truly stateless)
- [ ] Every case has a non-empty `permission_setup` array citing the PSG by name
- [ ] Every case has ≥2 steps
- [ ] Every case's `expected_result` quotes the AC's `then` clause verbatim
- [ ] Every AC scenario in the source story is covered by ≥1 case
- [ ] No case lists "System Administrator" as persona
- [ ] Sandbox name is captured at the script-set level
- [ ] `pass_fail` values use the enum {Pass, Fail, Blocked, Not Run} only

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Page-layout assignment is profile + record type, not PSG.** Adding a permission set to a tester does NOT change which page layout they see. Permission setup that ignores the page layout matrix produces cases that pass for the wrong reason. Confirm the tester's profile + record type combination is mapped to the right layout in Setup before the run.

2. **Bulk API runs do not fire all UI validation.** A UAT case that proves a validation rule fires in the UI does NOT prove it fires under a Data Loader bulk insert. If the feature includes a Data Loader path, write a separate case that runs the loader.

3. **Permission set group recalculation is asynchronous.** After assigning a PSG, the tester may need to log out and back in, and the entitlements may take a moment to propagate. A case that runs immediately after assignment can fail for setup reasons. Build a "wait + reauth" step into the precondition.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Per-persona UAT case (markdown or JSON) | The full canonical schema, authored fields populated; `actual_result`, `pass_fail`, `evidence_url`, `tester`, `executed_at` filled at run time |
| Negative-path companion case | One per story, marked `negative_path: true`, proves the feature blocks the wrong action |
| Data setup checklist | Ordered list of records and imports the tester runs before steps; cites `TestDataFactory` if Apex factory is faster |
| Permission setup checklist | PSG(s) to assign, plus an explicit "do not test as System Administrator" note |
| RTM evidence row | `case_id` + `pass_fail` + `evidence_url` keyed by `story_id` + `ac_id`, closing the RTM cell |

---

## Official Sources Used

See `references/well-architected.md` for the official Salesforce sources backing the permission, sandbox, and metadata claims in this skill.

---

## Related Skills

- `admin/uat-and-acceptance-criteria` — high-level UAT plan, defect classification, regression strategy, sign-off. Activates around this skill, not under it.
- `admin/acceptance-criteria-given-when-then` — the technique that produces the AC block this skill consumes. Always run that skill first.
- `templates/apex/tests/TestDataFactory.cls` — canonical factory referenced from `data_setup` when manual seeding is too slow.
- `agents/test-generator/AGENT.md` — generates Apex test methods. Distinct from this skill — these are human UI scripts.
