# Requirements Gathering — Salesforce Project Template

Use this template to document requirements for a Salesforce feature or project.
Fill in each section before handing off to the build team.

The machine-lintable requirements catalogue lives beside this file in
`requirements-catalogue.yaml` — this document is the human narrative around it. Lint the catalogue
with `python3 scripts/check_requirements_catalogue.py --file requirements-catalogue.yaml` before any
handoff. A filled example of both is in `references/worked-examples.md`.

---

## Project Context

**Feature / Project Name:**
**Salesforce Cloud(s) in scope:**
**Requesting stakeholder(s):**
**Primary end users (personas):**
**Target delivery date:**

---

## Stakeholder Interview Summary

| Stakeholder | Role | Key Requirements Raised | Unresolved Conflicts |
|---|---|---|---|
| | | | |
| | | | |

---

## As-Is Process

**Current process name:**

**Step-by-step description** (tag every step keep / drop / replace as you capture it — an untagged
step migrates the workaround along with the process):

| # | Actor | What happens today | keep / drop / replace | Pain point | `REQ-` generated |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |

**Known pain points:**
-
-

**Tools currently used (spreadsheet, legacy CRM, email, etc.):**

**Data currently tracked (field names and types from legacy system):**

---

## To-Be Process (Salesforce)

**Step-by-step description with Salesforce feature mapping:**

| Step | Who Does It | Salesforce Feature | Notes |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |

**Transition state** (how the org and the team operate between cutover and steady state — which
records stay in the old system, which automation is bypassed for the backfill, and for how long):

---

## Non-Functional Requirements (Salesforce)

One row per NFR class. The bounding platform fact is not optional: it is what stops the requirement
being promised beyond what the platform does. Sources for the standard facts are in
`references/well-architected.md`; the filled version is section 3 of `references/worked-examples.md`.

| NFR class | Requirement + measure (a number with a unit) | Bounding platform fact | Consequence for design |
|---|---|---|---|
| Record volume | | Per-transaction limits shared by Flow and Apex (App Limits, Per-Transaction Apex Limits) | |
| Data movement | | The 2,000-record line between bulkified synchronous calls and Bulk API 2.0 (App Limits, Bulk API section) | |
| Integration | | Total API calls per 24 h = 100,000 + (licences × calls per licence type) + add-ons in EE (App Limits, API Request Limits) | |
| Sharing / visibility | | The seven ordered layers in `standards/decision-trees/sharing-selection.md` | |
| Reporting | | Four-object ceiling and outer-join ordering (Metadata API Developer Guide, `ObjectRelationship`) | |
| Licence / persona | | API calls per licence per 24 h differ by an order of magnitude between internal and community licences (App Limits, API Request Limits) | |
| Storage | | Not in the Developer Limits quick reference — read the org's Storage Usage page | |
| Mobile / offline | | Confirm against the org's own mobile configuration before promising offline entry | |

---

## User Stories

Use this format for each story. Copy the block as needed.

---

### Story [#]: [Short Name]

**As a** [persona + Salesforce profile/permission set],
**I want** [specific Salesforce capability — name object/field/automation],
**So that** [business outcome].

**Acceptance Criteria:**
- [ ]
- [ ]
- [ ]

**Fit Classification:** Standard Fit / Configuration Gap / Customization Gap / Process Gap

**Volume / Frequency:** (How many records? How often?)

**Integration Dependency:** (Does this require data from an external system?)

---

## Fit-Gap Summary

| Requirement | Standard Salesforce Feature | Fit Type | Effort Est. | Notes |
|---|---|---|---|---|
| | | Standard Fit | | |
| | | Configuration Gap | | |
| | | Customization Gap | | |
| | | Process Gap | | |

**Total Standard Fit:** ___
**Total Configuration Gap:** ___
**Total Customization Gap:** ___
**Total Process Gap (requires stakeholder decision):** ___

---

## Handoff Map

Every catalogue row has exactly one primary target. A row with no target is a dropped requirement.

| Target | What it reads | `REQ-` rows | Why this target |
|---|---|---|---|
| `agents/story-drafter/AGENT.md` (`/draft-stories`) | the catalogue as `requirements-list` | | Confirmed functional rows with an object and a persona |
| `agents/fit-gap-analyzer/AGENT.md` (`/run-fit-gap`) | the drafted stories + a `target_org_alias` | | Rows whose feasibility depends on the actual org |
| `agents/process-flow-mapper/AGENT.md` (`/map-process-flow`) | the As-Is/To-Be tables above | | Owns the swim lanes; this document supplies the step table |
| `agents/config-workbook-author/AGENT.md` (`/author-config-workbook`) | confirmed rows grouped by workbook section | | The 10-section admin handoff |
| `admin/report-type-strategy` | base object + join chain | | Prove the chain before the report is promised |
| `architect/license-optimization-strategy` | `licence_implication` values | | Licence type and count is a costing decision |
| `admin/requirements-traceability-matrix` | every `id` | | Forward traceability to story, test and defect ids |

---

## Open Issues and Conflicts

| # | Issue Description | Stakeholders Involved | Decision Needed By |
|---|---|---|---|
| | | | |

---

## Out-of-Scope

Document items explicitly excluded from this project to prevent scope creep:

-
-
