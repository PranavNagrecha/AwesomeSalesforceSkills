---
name: requirements-traceability-matrix
description: "Use this skill when building or maintaining a Requirements Traceability Matrix (RTM) on a Salesforce project: one row per requirement, columns for source, user-story id(s), test-case id(s), defect id(s), sprint, release, and status. Covers forward traceability (req → story → code → test) and backward traceability (test → req). Trigger keywords: RTM, requirements traceability matrix, audit trail for salesforce delivery, traceability for steerco, deferred requirement tracking, regulatory traceability. NOT for eliciting the requirements in the first place — use admin/requirements-gathering-for-sf. NOT for user-story authoring — use admin/user-story-writing-for-salesforce. NOT for UAT test design — use admin/uat-test-case-design. NOT for Apex test design — use apex/test-class-standards. NOT for backlog prioritization — use admin/moscow-prioritization-for-sf-backlog. More triggers: traceability.md, build-layer traceability, REQ-XXX and FG-XXX id mapping, artefact-to-requirement orphan report, coverage-gap report, check_rtm.py --manifest-dir, owning run-time agent column, design decision ref column, metadata API name in a traceability row."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "how do I build an RTM for a Salesforce implementation"
  - "requirements traceability matrix template for a Salesforce project"
  - "audit trail for Salesforce delivery linking requirements to user stories and tests"
  - "how do I trace test cases back to original requirements for Steerco reporting"
  - "what columns should a Salesforce RTM have for a regulated industry project"
  - "how to track deferred or dropped requirements in a Salesforce delivery RTM"
  - "forward and backward traceability between requirements user stories and defects"
  - "find requirements with no artefact and artefacts with no requirement"
  - "rtm rows no longer match the metadata we actually deployed"
  - "map requirement ids to Salesforce metadata API names and test case ids"
  - "auditor asked which test proves this requirement was delivered"
  - "lint a traceability matrix CSV before the release gate"
  - "what format should traceability.md use in the build orchestration layer"
  - "keep FG fit-gap ids and REQ requirement ids in the same traceability matrix"
  - "add the owning run-time agent and design decision to each traceability row"
tags:
  - requirements-traceability
  - rtm
  - audit
  - delivery-governance
  - business-analysis
inputs:
  - "Approved requirement list with stable IDs (REQ-XXX) from elicitation phase"
  - "User story backlog with story IDs (US-XXX) from the agile tool (Jira, Azure DevOps, GUS)"
  - "UAT test case inventory with case IDs (TC-XXX) from the test management tool"
  - "Defect log from UAT and post-release hypercare with defect IDs (DEF-XXX or BUG-XXX)"
  - "Release / sprint calendar mapping each story to a target sprint and release"
outputs:
  - "Single-source-of-truth RTM (CSV + markdown rendering) with one row per requirement"
  - "Coverage report: requirements with no stories, stories with no tests, tests with no requirement"
  - "Status rollup by source (interview / SOW / regulatory / change request) for Steerco"
  - "Audit packet: per-requirement evidence chain (req → story → test → defect → release)"
  - "Deferred / dropped requirements log with rationale and decision owner"
dependencies: []
version: 1.1.5
author: Pranav Nagrecha
updated: 2026-09-12
---

# Requirements Traceability Matrix (RTM) for Salesforce

This skill activates when a Business Analyst, delivery lead, or admin needs to build or maintain the artifact that ties every approved requirement to its user story, code, test, defect, and release on a Salesforce project. It is the single document every audit and every Steerco demands: forward traceability proves that scope was delivered, backward traceability proves that no surprise scope was added.

---

## Before Starting

Gather this context before opening the RTM:

- **Are requirement IDs already assigned?** If the elicitation phase did not produce stable `REQ-XXX` IDs — or, on a fit-gap-led project, stable `FG-XXX` IDs (see § REQ-XXX ⇄ FG-XXX) — stop and assign them first. RTM rows are keyed on requirement ID — using titles or descriptions as the key creates duplicates and breaks every downstream join.
- **What is the agile tool of record?** Jira, Azure DevOps, Salesforce DevOps Center, or GUS each store user-story IDs in their own format. The RTM mirrors the source system; it does not invent its own story IDs.
- **What is the regulatory or audit posture?** A regulated project (HIPAA, SOX, GxP, FedRAMP) needs a `source` column that distinguishes regulatory requirements from elicited ones, plus a per-row evidence link. A non-regulated greenfield project can ship a lighter RTM.
- **Who owns RTM updates?** RTM rot is the most common failure mode — assign a single owner (usually the lead BA) and a cadence (end of every sprint and at every release gate).

---

## Questions to Ask Before Configuring

Ask these before the first row is written. A matrix built without them looks complete and joins to
nothing.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which id is this project's requirement key — the elicitation `REQ-XXX` or the fit-gap `FG-XXX`?" | The workbook's `source_req_id` column carries whichever the project actually uses — `admin/configuration-workbook-authoring` → `references/examples.md` puts `FG-014` there — and a matrix keyed on one while the workbook is keyed on the other joins to nothing | One key, plus the mapping table for the other prefix, before any row exists (gotchas 3 and 11) |
| "Is this the audit RTM, the build layer's `traceability.md`, or both?" | The build-layer file carries `step_id`, `artefact`, `agent` and `test_type` columns the audit RTM does not; maintained as two files they disagree within one sprint | One file and one schema, or a stated generation direction from one to the other (gotcha 12) |
| "For each requirement, which run-time agent owns the step that builds it?" | `standards/build-orchestration.md` § 4 gives every step exactly one owning agent from the roster; a row with no agent has nobody to fail at the gate | An executable matrix instead of a wish list, and an early signal that no agent covers the topic (gotcha 13) |
| "Which requirements land in components the Metadata API cannot retrieve or deploy?" | Those rows have no file for an artefact cross-check to resolve against, so they are reported unresolved on every run and the team learns to ignore the report | A `setup-only` marker per affected row instead of a permanent false alarm (gotcha 14) |
| "Who signs the waiver for a dropped or deferred requirement, and where is it stored?" | A deleted row is invisible at audit; a `Dropped` row with no decision record is the same finding one step later | The decision-log entry the gate reads, with owner and date (gotcha 5) |
| "How is the matrix checked, and at which gate does a failure stop the release?" | Hand-reviewing 200 rows finds nothing; the coverage-gap and orphan views are the only two outputs a gate can act on | A `check_rtm.py` invocation in CI, bound to a named gate (gotcha 4) |
| "Does the org already own the artefact a row points at, or does this release create it?" | An artefact that already exists is a *modification* row — its drop is a destructive change, not a no-op — and that changes the rollback plan | The create/modify split that tells the release manager which rows are reversible (gotcha 15) |

What a proper configuration adds over just keeping a list of requirements: the matrix answers "which
deployed component satisfies this requirement, who built it, which decision produced it, and which
test proved it" as a lookup rather than an investigation — and its two derived views turn the
question "are we done?" into a gate a machine can fail.

---

## Core Concepts

### Canonical Column Set

The minimum viable RTM has these columns. Every row is one requirement. Multi-valued cells (e.g., several user stories implementing one requirement) are pipe-delimited so the file stays diff-friendly in Git.

| Column | Type | Notes |
|---|---|---|
| `req_id` | string, unique | `REQ-001`, `REQ-002`. Stable across the project lifetime. Never reuse an ID. |
| `source` | enum | `interview` / `sow` / `regulatory` / `change-request` / `defect-driven`. Critical for audit. |
| `description` | string | One-sentence requirement statement. Full text lives in the requirements doc. |
| `priority` | enum | `must` / `should` / `could` / `wont` (MoSCoW) — links to backlog. |
| `story_ids` | string, multi | Pipe-delimited story IDs: `US-101 \| US-102`. Empty = orphan requirement. |
| `test_case_ids` | string, multi | Pipe-delimited UAT/Apex test IDs: `TC-201 \| TC-202`. |
| `defect_ids` | string, multi | Pipe-delimited defect IDs raised against this requirement during UAT or hypercare. |
| `sprint` | string | The sprint the implementing story landed in (last sprint if multi-sprint). |
| `release` | string | The release tag the requirement shipped in: `R1.0`, `R1.1`. Empty until deploy. |
| `status` | enum | `Draft` / `In Build` / `In UAT` / `Released` / `Deferred` / `Dropped`. |

Optional columns for regulated projects: `compliance_control_id` (e.g., `HIPAA-164.312(a)(1)`), `evidence_link` (URL to test result, signed approval, or audit log).

### The Build-Layer RTM: `traceability.md`

`standards/build-orchestration.md` § 2 gives every build a
`.sfskills/builds/<build-id>/traceability.md` that maps **REQ / clarification id → step → artefact
path → test result**, written by `agents/build-doc-keeper/AGENT.md` after each step is tested.
**That file is this skill's format** — the build layer does not define a second one. The audit RTM
above and `traceability.md` are the same matrix at two altitudes: the audit RTM is keyed on the
requirement and rolls up to a release; the build-layer RTM adds the columns a build needs
(`step_id`, `artefact`, `agent`, `decision_ref`, `test_type`) and drops the ones only a multi-release
programme has.

| Column | Type | Notes |
|---|---|---|
| `req_id` | string, unique | `REQ-XXX` or `FG-XXX`. Same key as the audit RTM and the workbook's `source_req_id`. |
| `source` | string | The clarification id (`Q1`, `Q2`, … per `agents/_shared/schemas/build-plan.schema.json` `clarifications[].id`) or the stakeholder who raised it. |
| `requirement` | string | One sentence. Full text lives in `requirement.md`. |
| `step_id` | string | `M<n>-S<nn>` — the plan step that produced the artefact. `—` for a row that produces nothing. |
| `artefact` | string | `<MetadataType>:<ApiName>`, e.g. `CustomField:Account.Region__c`. The API name, not the UI label. |
| `agent` | string | The step's owning run-time agent id. Must exist as `agents/<id>/AGENT.md` with `class: runtime`. |
| `decision_ref` | string | `D<n>` from `plan.json.decisions[]`, which carries the decision-tree branch that resolved it. |
| `test_id` | string | The acceptance test or UAT case that proves the row. |
| `test_type` | enum | `checker` / `xml` / `manifest` / `command` / `manual` — the five runners in build-orchestration § 5. |
| `status` | enum | Same enum as the audit RTM: `Draft` / `In Build` / `In UAT` / `Released` / `Deferred` / `Dropped`. |

`step_id`, `decision_ref` and `test_type` are what make the row *executable*: a gate can re-run the
test, re-read the decision, and re-run the step. `story_ids`, `defect_ids`, `sprint` and `release`
stay in the audit RTM — a build has one release by definition. Worked end to end in
`references/worked-examples.md`.

Two views are derived from the matrix and are the only things a gate reads: **coverage gaps**
(requirements with no artefact or no test) and **orphans** (artefacts with no requirement).

### REQ-XXX ⇄ FG-XXX: Which Prefix Is the Key

Two id families reach the same column. `admin/requirements-gathering-for-sf` mints `REQ-XXX` at
elicitation. `admin/fit-gap-analysis-against-org` mints `FG-XXX` per gap row, and
`admin/configuration-workbook-authoring` → `references/examples.md` shows `FG-014` sitting in the
workbook's `source_req_id` column — so on a fit-gap-led project the workbook's key is `FG-`, not
`REQ-`. Both are legal RTM keys. The mapping rule:

| Situation | Key to use | Rule |
|---|---|---|
| Requirements elicited first, fit-gap run against them | `REQ-XXX` | The `FG-XXX` id goes in a `fit_gap_ref` column, not the key column |
| Fit-gap run against an existing org, requirements derived from the gaps | `FG-XXX` | The `FG-` id **is** the `req_id`; do not mint a parallel `REQ-` id for the same gap |
| Both exist for the same need (common on a re-platform) | `REQ-XXX` | Record the pair once in a mapping table; never carry two rows |
| A gap produces no requirement (accepted as-is) | `FG-XXX` | Row exists with status `Dropped` and a waiver — the descope ledger, not a deleted row |

Two rows for one need is the failure this rule prevents: coverage counts double, and the gate cannot
tell which of the two is authoritative. `scripts/check_rtm.py` accepts either prefix and errors on a
key that matches neither.

### Forward vs Backward Traceability

- **Forward traceability** (`req → story → code → test → release`) proves that every approved requirement was actually delivered. Used at release gate review.
- **Backward traceability** (`test → req`) proves that every test case maps to an approved requirement — i.e., no scope crept in without an approval trail. Used at audit time.

A complete RTM supports both directions. The most common gap is backward — tests get written against stories that drifted from the original requirement, and nobody updates the matrix.

### ID Conventions

- `REQ-XXX` — requirement ID, assigned during elicitation, immutable.
- `US-XXX` — user story ID, mirrored from the agile tool.
- `TC-XXX` — test case ID, mirrored from the test management tool.
- `DEF-XXX` or `BUG-XXX` — defect ID, mirrored from the defect tracker.
- Use a project-prefix (e.g., `ACME-REQ-001`) when running multiple programs in the same agile tool to prevent collision.

### One-to-Many Cardinality

The relationships are not 1:1:

- **1 requirement : N stories** — a requirement like "agents can triage cases" splits into multiple stories (queue setup, assignment rule, escalation, SLA timer). The RTM lists all story IDs in the `story_ids` cell.
- **1 story : N test cases** — UAT typically has happy path, validation, and exception cases per story.
- **N stories : 1 requirement** is the rule — never split a requirement across rows. Keep the requirement on one row and pipe-delimit its stories.
- **1 test case : 1+ requirements** — a regression test can validate multiple requirements. Mirror the test ID into each requirement row it covers.

### The Audit Pass

At every release gate and at audit time, run a pass over the RTM:

1. **Coverage check** — every requirement with status `Released` must have at least one `story_ids` and one `test_case_ids` value. Empty cells are coverage gaps.
2. **Status check** — every requirement with status `In UAT` must have at least one `test_case_ids` value. `In Build` must have at least one `story_ids`.
3. **Drop check** — every requirement with status `Deferred` or `Dropped` has a documented decision (owner + date + rationale) in the requirements doc or a decision log.
4. **Backward check** — sample 10% of `test_case_ids` and confirm each one appears in some `req_id` row (no orphan tests).
5. **Source check** — count rows by `source`. Regulatory requirements with status `Dropped` are an audit red flag and need an explicit waiver document.

---

## Common Patterns

### Pattern: RTM as Single Source of Truth (CSV-in-Git)

**When to use:** Any Salesforce project where the BA team owns delivery governance and wants version control over the matrix.

**How it works:**
1. Store the RTM as a CSV in the project repo at a known path (e.g., `governance/rtm.csv`).
2. The CSV columns match the canonical column set above.
3. Every requirement update is a Git commit with a message linking the change request or decision.
4. A nightly or per-PR CI job runs `scripts/check_rtm.py` against the CSV and flags orphans, duplicates, and invalid statuses.
5. A markdown rendering of the CSV is generated for Steerco distribution — never hand-maintain the markdown.

**Why not a spreadsheet:** Spreadsheet RTMs decay because nobody can audit who changed what. CSV-in-Git gives blame, history, and review.

### Pattern: Two-Phase Population

**When to use:** Greenfield Salesforce projects with a discrete planning and build phase.

**How it works:**
1. **Planning pass (forward traces):** As stories are written, populate `req_id`, `source`, `description`, `priority`, `story_ids`, `sprint`, and set status to `Draft` or `In Build`.
2. **Build/UAT pass (test traces):** As UAT cases are authored, populate `test_case_ids`. Move status to `In UAT`.
3. **Hypercare pass (defect traces):** As defects are raised against released requirements, populate `defect_ids`. Defects raised against a non-released requirement are escalated to scope, not silently absorbed.
4. **Release pass:** When a release deploys, populate `release` for every requirement that landed and move status to `Released`.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| One requirement maps to multiple stories | Keep one RTM row, pipe-delimit story IDs | Splitting the requirement across rows breaks the unique key on `req_id` |
| One test case validates multiple requirements | Mirror the test ID into every requirement row it covers | Backward traceability needs every test to be reachable from every requirement it validates |
| Stakeholder drops a requirement mid-sprint | Set status to `Dropped`, keep the row | Deleting the row destroys the audit trail; dropped requirements are themselves an audit artifact |
| New requirement added via change request | Add a row with `source: change-request` and a CR ID in description | Distinguishes baseline scope from change scope at audit time |
| Requirement has no stories yet | Leave `story_ids` blank, status `Draft` | Empty cells are intentional; checker flags them at gate review |
| Defect raised against an unreleased requirement | Escalate to scope review, not the RTM | Defects are post-release; pre-release issues are scope/build issues |
| Regulated project | Add `compliance_control_id` and `evidence_link` columns | Auditors expect a per-row evidence chain, not a project-level summary |

---

## Recommended Workflow

1. **Fix the schema and the key first.** Choose the audit schema (`templates/rtm.md` § CSV Schema)
   or the build-layer schema (§ The Build-Layer RTM above, worked in
   `references/worked-examples.md`). Apply the REQ-XXX ⇄ FG-XXX rule and write the mapping table if
   both prefixes are in play. Locking this before row 1 is the whole job — every later fix is a
   migration.
2. **Seed one row per requirement from the clarifications, not the backlog.** In a build, the row
   set comes from `plan.json.clarifications[]` and `requirement.md`; `source` carries the `Q<n>` id.
   Seeding from the backlog inverts the direction and guarantees the orphan view is empty by
   construction, which is the failure gotcha 2 describes.
3. **Fill `step_id`, `artefact`, `agent` and `decision_ref` as the plan is written.** The artefact is
   the Metadata API name (`CustomField:Account.Region__c`), never the UI label — see gotcha 10. Mark
   the rows whose components the Metadata API cannot carry as `setup-only` now, not after the first
   false alarm (gotcha 14).
4. **Fill `test_id` and `test_type` as the tester runs, one of the five runners** from
   `standards/build-orchestration.md` § 5 (`checker` / `xml` / `manifest` / `command` / `manual`).
   A row that reaches `In UAT` with an empty `test_id` is a coverage gap, not a formatting problem.
5. **Run the checker at every gate**, not at the end:
   `python3 scripts/check_rtm.py --manifest-dir .sfskills/builds/<build-id> --repo-root <repo>`.
   It fails the gate (exit 1) on a duplicate or malformed id, a row with no artefact or no test, an
   agent id that does not resolve to `agents/<id>/AGENT.md`, and — under `--strict` — an artefact
   API name it cannot find in the manifest. Add `--self-check` to prove the rules still fire.
6. **Publish the two derived views the gate reads** — the coverage-gap report and the orphan report
   (`references/worked-examples.md` §§ 5–6). Every coverage gap is either closed or waived with an
   owner and a date; every orphan is either given a requirement or listed as a destructive change.
7. **Re-run steps 3–6 after every milestone gate** and diff the matrix against the previous
   milestone. A row whose `artefact` changed without its `decision_ref` changing is drift — the
   thing gotcha 1 is about — and it is only visible in the diff.

## Review Checklist

Run through these before handing the RTM to Steerco or audit:

- [ ] Every row has a unique `req_id`; no duplicates
- [ ] Every requirement with status `Released` has at least one `story_ids` and one `test_case_ids` value
- [ ] Every requirement with status `In UAT` has at least one `test_case_ids` value
- [ ] Every requirement with status `Deferred` or `Dropped` has a documented decision (owner + date + rationale)
- [ ] Every status value is in the enum: `Draft / In Build / In UAT / Released / Deferred / Dropped`
- [ ] Every `source` value is in the enum: `interview / sow / regulatory / change-request / defect-driven`
- [ ] No requirement IDs reused across the project lifetime (e.g., REQ-042 means the same thing in R1.0 and R2.0)
- [ ] A 10% sample of test cases trace back to a requirement (backward traceability sample)
- [ ] Multi-valued cells use the pipe `|` delimiter — no commas, no semicolons
- [ ] Markdown rendering is generated, not hand-edited
- [ ] Regulated rows (if applicable) have populated `compliance_control_id` and `evidence_link`

---

## Salesforce-Specific Gotchas

Non-obvious delivery realities that cause real audit findings:

1. **Bidirectional drift** — A requirement is updated mid-flight (often via a verbal change in a workshop), but the linked story is not updated. The RTM still says story `US-101` implements requirement `REQ-007`, but the story now delivers a different behavior. Always update both sides of the link in the same change.

2. **RTM in a spreadsheet that nobody maintains** — The most common failure mode. The RTM lives in a SharePoint or Google Sheet, gets populated at project start, and is never updated. By release, it is fiction. CSV-in-Git with a per-PR check is the only durable fix.

3. **IDs reused across phases** — Phase 1 ships REQ-001 through REQ-050. Phase 2 starts a new RTM and reuses REQ-001. Now defects raised in Phase 2 reference an ambiguous requirement. Always continue the numbering or use a phase prefix.

4. **Missing the deferred/dropped column** — Teams delete dropped requirements to keep the matrix clean. Auditors then ask "you scoped 200 requirements, you delivered 150 — where are the other 50?" and there is no answer. Dropped requirements are first-class rows.

5. **Backlog churn outpaces RTM** — In aggressive sprint teams, stories are split, merged, and renamed weekly. If the BA only updates the RTM at release gates, the matrix is months stale. Update at end of every sprint or use a CI job that diffs the agile tool against the RTM.

6. **Salesforce-specific platform constraints not surfaced as requirements** — A requirement like "agents can update 1M cases" implicitly demands Bulk API or Batch Apex. If that platform constraint is not captured as a sub-requirement, the RTM looks complete while the system is unsupportable. Surface platform constraints as their own REQ rows linked to the parent.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `.sfskills/builds/<build-id>/traceability.md` | The build-layer RTM: REQ / clarification id → step → artefact → test, per `standards/build-orchestration.md` § 2. Written by `agents/build-doc-keeper/AGENT.md`; never hand-edited |
| `governance/rtm.csv` | Canonical CSV with one row per requirement, all columns from the canonical set |
| `governance/rtm.md` | Generated markdown rendering for Steerco distribution |
| `governance/rtm-coverage-report.md` | Derived view 1 — requirements with no artefact or no test, each closed or waived with owner and date |
| `governance/rtm-orphan-report.md` | Derived view 2 — artefacts in the manifest with no requirement, each given a requirement or listed as a destructive change |
| `governance/rtm-source-rollup.md` | Status counts grouped by `source` for Steerco summary |
| `governance/dropped-requirements.md` | Per-requirement decision log: owner, date, rationale for `Deferred` or `Dropped` rows |
| Audit packet (per-requirement evidence chain) | Compiled at release gate: req → story commits → test results → defect closures → release tag |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/worked-examples.md` | You need the matrix filled in — a 17-row build-layer RTM for the Acme case-intake build, as CSV and as a markdown table, with the coverage-gap and orphan views and the decision table the `decision_ref` column points at |
| `references/examples.md` | You need the audit-RTM shape instead: greenfield, HIPAA-regulated, and hypercare-defect variants of the canonical column set |
| `references/gotchas.md` | Before promising the matrix is complete — 15 ways an RTM becomes fiction, including the platform behaviours that make an artefact name unresolvable |
| `references/llm-anti-patterns.md` | When an assistant generated the matrix — seven failure shapes with a detection hint each |
| `references/well-architected.md` | For the spreadsheet-vs-Git and lightweight-vs-regulated tradeoffs, and the source list |
| `templates/rtm.md` | You are creating the file — CSV schema, markdown skeleton, and the JSON envelope for tool-to-tool handoff |
| `templates/requirements-traceability-matrix-template.md` | You are running the engagement — the context and checklist form to fill in per project |
| `scripts/check_rtm.py` | At every gate — the linter for both schemas, with `--manifest-dir`, `--repo-root`, and the two derived reports |

---

## Related Skills

- `admin/requirements-gathering-for-sf` — use first to elicit and mint the `REQ-XXX` ids the matrix is keyed on
- `admin/fit-gap-analysis-against-org` — mints the `FG-XXX` ids; read it before applying the REQ ⇄ FG mapping rule
- `admin/user-story-writing-for-salesforce` — authors the stories whose ids populate `story_ids` in the audit schema
- `admin/uat-test-case-design` — the per-case field schema behind the `test_id` column
- `admin/uat-and-acceptance-criteria` — runs the programme that produces the `manual` test results this matrix records
- `admin/acceptance-criteria-given-when-then` — the AC form a `manual` test id resolves to
- `admin/configuration-workbook-authoring` — consumes `req_id` as `source_req_id`; its RTM linkage block is the workbook-side half of this matrix
- `admin/moscow-prioritization-for-sf-backlog` — populates `priority` in the audit schema
- `admin/case-management-setup` — supplies the build worked in `references/worked-examples.md`
- `devops/metadata-api-retrieve-deploy` — the retrieve/deploy mechanics behind the artefact column and the destructive-change path for a dropped row
- `standards/build-orchestration.md` — defines `traceability.md`, the step ids, and the five test types this matrix uses
- `agents/build-doc-keeper/AGENT.md` — writes `traceability.md` after every tested step
- `agents/milestone-verifier/AGENT.md` — reads the two derived views at the milestone gate
- `agents/deployment-risk-scorer/AGENT.md` — consumes the matrix at release gate; share the same release tag
- `agents/audit-router/AGENT.md` — consumes the matrix at audit time; needs the per-row evidence chain
