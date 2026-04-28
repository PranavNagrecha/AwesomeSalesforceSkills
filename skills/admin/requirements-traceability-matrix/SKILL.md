---
name: requirements-traceability-matrix
description: "Use this skill when building or maintaining a Requirements Traceability Matrix (RTM) on a Salesforce project: one row per requirement, columns for source, user-story id(s), test-case id(s), defect id(s), sprint, release, and status. Covers forward traceability (req → story → code → test) and backward traceability (test → req). Trigger keywords: RTM, requirements traceability matrix, audit trail for salesforce delivery, traceability for steerco, deferred requirement tracking, regulatory traceability. NOT for requirements elicitation (use requirements-gathering-for-sf). NOT for user-story authoring (use user-story-writing-for-salesforce). NOT for UAT test design (use uat-test-case-design). NOT for Apex test design (use agents/test-generator/AGENT.md). NOT for backlog prioritization (use moscow-prioritization-for-sf-backlog)."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Requirements Traceability Matrix (RTM) for Salesforce

This skill activates when a Business Analyst, delivery lead, or admin needs to build or maintain the artifact that ties every approved requirement to its user story, code, test, defect, and release on a Salesforce project. It is the single document every audit and every Steerco demands: forward traceability proves that scope was delivered, backward traceability proves that no surprise scope was added.

---

## Before Starting

Gather this context before opening the RTM:

- **Are requirement IDs already assigned?** If the elicitation phase did not produce stable `REQ-XXX` IDs, stop and assign them first. RTM rows are keyed on requirement ID — using titles or descriptions as the key creates duplicates and breaks every downstream join.
- **What is the agile tool of record?** Jira, Azure DevOps, Salesforce DevOps Center, or GUS each store user-story IDs in their own format. The RTM mirrors the source system; it does not invent its own story IDs.
- **What is the regulatory or audit posture?** A regulated project (HIPAA, SOX, GxP, FedRAMP) needs a `source` column that distinguishes regulatory requirements from elicited ones, plus a per-row evidence link. A non-regulated greenfield project can ship a lighter RTM.
- **Who owns RTM updates?** RTM rot is the most common failure mode — assign a single owner (usually the lead BA) and a cadence (end of every sprint and at every release gate).

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

Step-by-step instructions for an AI agent or BA activating this skill:

1. **Define the column set** — confirm the canonical columns above and decide whether the project needs the regulated-project optional columns. Lock the schema before any rows are added.
2. **Assign IDs** — confirm every requirement, story, and test case has a stable ID under the `REQ-XXX → US-XXX → TC-XXX` convention. If IDs are missing, stop and assign them in the source-of-truth tool first.
3. **Populate forward traces during planning** — for each requirement, fill `req_id`, `source`, `description`, `priority`, `story_ids`, and `sprint`. Set status to `Draft` or `In Build`.
4. **Populate test traces during build/UAT** — as UAT and Apex test cases are authored, mirror their IDs into the matching requirement row's `test_case_ids` cell. Move status to `In UAT`.
5. **Capture defect linkage during UAT/hypercare** — when a defect is raised, add its ID to the originating requirement's `defect_ids` cell. Defects must trace to a requirement, not just a story.
6. **Stamp the release column at deploy** — when a release deploys, fill `release` for every requirement that landed and move status to `Released`. Coordinate with the deployment-risk-scorer agent so the same release tag appears in both artifacts.
7. **Run the post-release audit pass** — execute the five-step audit pass (coverage, status, drop, backward, source) and produce the Steerco rollup. Hand off to `agents/audit-router/AGENT.md` for archival.

---

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
| `governance/rtm.csv` | Canonical CSV with one row per requirement, all columns from the canonical set |
| `governance/rtm.md` | Generated markdown rendering for Steerco distribution |
| `governance/rtm-coverage-report.md` | Coverage gaps: orphan requirements, orphan tests, status mismatches |
| `governance/rtm-source-rollup.md` | Status counts grouped by `source` for Steerco summary |
| `governance/dropped-requirements.md` | Per-requirement decision log: owner, date, rationale for `Deferred` or `Dropped` rows |
| Audit packet (per-requirement evidence chain) | Compiled at release gate: req → story commits → test results → defect closures → release tag |

---

## Related Skills

- requirements-gathering-for-sf — use first to elicit and ID requirements before they enter the RTM
- user-story-writing-for-salesforce — use to author the user stories whose IDs populate the `story_ids` column
- uat-test-case-design — use to author the UAT cases whose IDs populate the `test_case_ids` column
- moscow-prioritization-for-sf-backlog — use to populate the `priority` column with `must / should / could / wont`
- agents/deployment-risk-scorer/AGENT.md — consumes the RTM at release gate; share the same release tag
- agents/audit-router/AGENT.md — consumes the RTM at audit time; needs the per-row evidence chain
- agents/orchestrator/AGENT.md — consumes the RTM for multi-phase tracking across releases
