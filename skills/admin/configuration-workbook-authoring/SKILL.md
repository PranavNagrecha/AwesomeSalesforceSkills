---
name: configuration-workbook-authoring
description: "Author the Salesforce Configuration Workbook — the structured, reviewable handoff document an admin uses to execute a feature across Objects/Fields, Page Layouts, Profiles/PSGs, Sharing, Validation, Automation, List Views, Reports, Integrations, and Data. Triggers: 'salesforce configuration workbook', 'admin handoff document', 'implementation workbook'. NOT for object design itself (use admin/custom-field-creation, admin/lookup-and-relationship-design, agents/object-designer/AGENT.md), NOT for permission set design (use admin/permission-set-architecture, agents/permission-set-architect/AGENT.md), NOT for Flow construction (use skills/flow/* and agents/flow-builder/AGENT.md), and NOT for the deployment manifest (use skills/devops/metadata-api-retrieve-deploy)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
  - Security
triggers:
  - "salesforce configuration workbook"
  - "admin handoff document"
  - "implementation workbook"
  - "how do I structure the build sheet for a new feature"
  - "we need a single document that drives object designer, perm set architect, and flow builder"
  - "convert user stories and fit-gap rows into actionable rows for admins"
  - "version-lock the configuration spec at sprint commit"
tags:
  - configuration-workbook-authoring
  - admin-handoff
  - implementation-spec
  - rtm-traceability
  - agent-routing
inputs:
  - "Approved user stories with story_id and acceptance criteria"
  - "Fit-gap analysis rows with req_id"
  - "Target org alias for naming-collision and existing-metadata reality check"
  - "Sprint or release identifier the workbook is being committed against"
outputs:
  - "Configuration Workbook (markdown + JSON envelope + CSV) covering 10 canonical sections, every row tagged with owner, source_req_id, source_story_id, status, recommended_agent, and recommended_skills"
  - "RTM linkage block mapping each row_id back to a source_req_id and forward to a downstream runtime agent"
  - "Stdlib checker (check_workbook.py) that validates row schema, agent membership against the runtime roster, and absence of placeholder rows"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Configuration Workbook Authoring

This skill activates when a Salesforce delivery team needs to convert approved
user stories and fit-gap rows into the **Configuration Workbook** — the
structured, reviewable handoff document that drives admin execution and routes
each row to a single downstream runtime agent. The workbook is the canonical
artifact between requirements (RTM) and metadata (deployment manifest).

It is NOT the object designer, NOT the permission-set designer, NOT the Flow
builder, and NOT the deployment manifest. It is the handoff document those
agents *consume*.

---

## Before Starting

Gather this context before authoring or revising a workbook:

- **Approved user stories** — every workbook row must carry `source_story_id`.
  Rows without an upstream story are orphaned and cannot be reviewed.
- **Approved fit-gap rows** — every workbook row must carry `source_req_id` so
  the workbook traces back to the RTM.
- **Target org alias** — the workbook is grounded in the live org. API names,
  existing record types, and existing PSGs must reflect reality, not wishlist.
- **Sprint / release identifier** — the workbook is version-locked at sprint
  commit. Mid-sprint change requests open *new* rows; they never edit existing
  rows in place.
- **Downstream agent roster** — every row's `recommended_agent` must resolve
  to a real `agents/<name>/AGENT.md` from the runtime tier (see
  `agents/_shared/SKILL_MAP.md` for the authoritative list).

---

## Core Concepts

### Concept 1: One row per addressable change

The workbook's atomic unit is a **row**. A row describes a single configurable
artifact (one field, one validation rule, one PSG composition step, one Flow
trigger, one report folder permission, one named credential). Rows are never
"epics" — if a row would require multiple agents to execute, it must be split.

The row schema is:

| Field | Required | Notes |
|---|---|---|
| `row_id` | yes | Stable, unique within the workbook (e.g. `CWB-FIELDS-014`). Survives section reorder. |
| `section` | yes | One of the 10 canonical sections. Must match exactly. |
| `target_value` | yes | The configurable value (API name, formula, picklist set, sharing rule criterion, etc.). |
| `owner` | yes | The named human accountable for this row landing in the org. Not a team alias. |
| `source_req_id` | yes | Fit-gap row id from the RTM. Orphan rows = REJECT. |
| `source_story_id` | yes | User-story id (e.g. `US-2031`). |
| `recommended_agent` | yes | Single downstream runtime agent (one of `object-designer`, `permission-set-architect`, `flow-builder`, `path-designer`, `lightning-record-page-auditor`, etc.). |
| `recommended_skills[]` | yes (≥1) | Skill ids the executing agent should consult. |
| `status` | yes | `proposed` \| `committed` \| `in-progress` \| `executed` \| `verified` \| `change-requested`. **Never** `TBD`/`TODO`/`?`. |
| `notes` | optional | Risks, decisions, links to ADRs. |

### Concept 2: Ten canonical sections

The workbook is fixed at ten sections. Authors do not invent new sections; if a
configurable artifact does not fit into one of these, it is not within the
workbook's scope:

1. **Objects + Fields** — new objects, custom fields, field-type changes,
   formula fields, external IDs.
2. **Page Layouts + Lightning Pages** — record-type-keyed layout assignments,
   Dynamic Forms regions, Lightning Record Page components.
3. **Profiles + Permission Sets + PSGs** — every PS and PSG composition; the
   muting strategy.
4. **Sharing Settings** — OWD, role hierarchy adjustments, sharing rules,
   manual share, restriction rules. Cite the sharing decision tree.
5. **Validation Rules** — VR formula, error location, error message, bypass
   reference (Custom Permission + Custom Setting).
6. **Automation (Flow / Apex / Approvals)** — every Flow, every Apex trigger
   handler hook, every approval process. Cite the automation decision tree.
7. **List Views + Search** — list view filter criteria, default list view per
   profile, search layouts, lookup filters.
8. **Reports + Dashboards** — folder structure, folder sharing, key reports
   and dashboards, scheduled subscriptions.
9. **Integrations** — named credentials, connected apps, remote site settings,
   external services, Platform Event channels, CDC subscriptions. Sensitive
   credentials are referenced by alias, never inline.
10. **Data + Migration** — required data loads, dedup rules, External Id
    upsert keys, sandbox seed data, cutover order.

### Concept 3: Every row is addressable by exactly one downstream agent

The workbook is not just documentation — it is a *routing instrument*. The
`recommended_agent` field assigns each row to a single agent that will execute
it. If a single configuration step requires two agents (e.g. a new object
*and* its PSG), it must be **split** into two rows, each addressable on its
own.

Allowed `recommended_agent` values (subset, see `agents/_shared/SKILL_MAP.md`
for the full list):

- `object-designer` — Objects + Fields rows
- `permission-set-architect` — Profiles + Permission Sets + PSGs rows
- `flow-builder` — Automation rows where the chosen tool is Flow
- `path-designer` — Path + Guidance rows in the Lightning Pages section
- `lightning-record-page-auditor` — Lightning Record Page rows
- `validation-rule-auditor` (or `audit-router --domain validation_rule`) —
  Validation Rules rows
- `report-and-dashboard-auditor` (or `audit-router --domain report_dashboard`)
  — Reports + Dashboards rows
- `integration-catalog-builder` — Integrations rows
- `data-loader-pre-flight` — Data + Migration rows
- `csv-to-object-mapper` — Data + Migration rows when CSV-to-object mapping
  is the dominant work

---

## Common Patterns

### Pattern 1: Source-grounded row authoring

**When to use:** Every time a new row is added to the workbook.

**How it works:**

1. Pick the source — a `source_req_id` from the RTM, a `source_story_id`, or
   both. **Both are required.**
2. Restate the change in `target_value` using API names already in the org or
   names that conform to `templates/admin/naming-conventions.md`.
3. Pick exactly one `recommended_agent`. If the row "needs" two agents,
   **split the row**.
4. Pick `recommended_skills[]` — at least one skill id from the executing
   agent's Mandatory Reads list.
5. Set `status: proposed`. Promotion to `committed` happens only at sprint
   commit (Step 5 of the workflow).

**Why not the alternative:** Free-text "build sheets" that lack `row_id`,
`source_req_id`, or `recommended_agent` cannot be reviewed for completeness,
cannot be routed to agents, and silently drift from the RTM.

### Pattern 2: Version-locking at sprint commit

**When to use:** When the team commits a workbook to a sprint or release.

**How it works:** Set `status: committed` on every in-scope row, snapshot the
file (commit a tagged copy under `docs/workbooks/<release>/cwb.md`), and from
that point treat the file as **immutable**. Mid-sprint change requests open
*new* rows with `status: change-requested` and a `notes` field linking back to
the row(s) they supersede. Old rows stay; their `target_value` is preserved as
historical record.

**Why not the alternative:** Editing rows in place destroys the audit trail
and lets reviewers approve a workbook that no longer matches what was
deployed.

### Pattern 3: One row, one agent, one section

**When to use:** Whenever the temptation arises to have a single row "stand
in" for a multi-section change.

**How it works:** A "new Account Plan object with a PSG and a record-trigger
Flow" is **three rows**:

- `CWB-OBJ-007`, section Objects+Fields, recommended_agent `object-designer`.
- `CWB-PSG-019`, section Profiles+Permission Sets+PSGs, recommended_agent
  `permission-set-architect`.
- `CWB-AUT-031`, section Automation, recommended_agent `flow-builder`.

Each row carries the same `source_story_id` and the same `source_req_id`.
Cross-row dependencies live in `notes`, not in row content.

**Why not the alternative:** A row that touches three sections cannot be
routed to a single agent and degrades the workbook into a wiki.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Row touches 2+ sections | Split the row, one per section | Each row must be addressable by one agent |
| Row has no `source_req_id` | Reject — open a fit-gap row first | Workbook traces back to RTM; orphans are forbidden |
| Mid-sprint change request | Open a new row with `status: change-requested`, link to the superseded row in `notes` | Workbook is version-locked at sprint commit |
| Row's downstream tool is Apex, not Flow | `recommended_agent: trigger-consolidator` or `apex-refactorer` (per `automation-selection.md`) | Cite the decision tree branch, do not freestyle |
| Row's `target_value` references a credential | Use a Named Credential alias; never inline secrets | Secrets in workbook = leak |
| Workbook has no Integrations section | Add it, even if empty | An empty section is information; a missing one is a gap |
| Two reviewers disagree on a row | Promote disagreement to `notes`, leave `status: proposed`, escalate to architect | Workbook isn't the venue for un-resolved decisions |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner authoring this
workbook:

1. **Intake** — pull approved user stories and fit-gap rows. Confirm every
   story has at least one fit-gap row and every gap row has at least one
   story; flag the others to the BA before writing any workbook content.
2. **Outline** — instantiate the 10 canonical sections (in order) using
   `templates/config-workbook.md`. Empty sections stay in the file with a
   one-line `not-in-scope-this-release` note.
3. **Populate** — for each in-scope change, author one or more rows per
   Pattern 1 + Pattern 3. Every row must have `source_req_id`,
   `source_story_id`, exactly one `recommended_agent`, at least one
   `recommended_skills[]` entry, and `status: proposed`.
4. **Review** — share with the admin team and BA. Reviewers reject any row
   that is missing canonical fields, references a `recommended_agent` that
   isn't in the runtime roster, or carries a placeholder status.
5. **Version-lock** — at sprint commit, run `python3 scripts/check_workbook.py
   --workbook docs/workbooks/<release>/cwb.md`, fix any errors, set every
   in-scope row's `status: committed`, and tag the file. From this point the
   file is immutable.
6. **Hand off** — for each row, hand `(row_id, recommended_agent,
   recommended_skills[], target_value, source_req_id)` to the downstream
   agent. The downstream agent reads the row, executes the change, and
   reports back with the metadata path it produced.
7. **Close out** — update each executed row's `status: executed` and link
   the deployed metadata path. Cross-link the row back to the RTM so the
   release report can show every gap row → workbook row → metadata file.

---

## Review Checklist

Before declaring the workbook ready for sprint commit:

- [ ] Every row has a unique `row_id`
- [ ] Every row has both `source_req_id` and `source_story_id`
- [ ] Every row has exactly one `recommended_agent` from the runtime roster
- [ ] Every row has at least one entry in `recommended_skills[]`
- [ ] No row has `status` of `TBD`, `TODO`, `?`, or empty
- [ ] All 10 canonical sections exist (empty sections carry a
      `not-in-scope-this-release` note)
- [ ] No row carries an inline credential, password, or token
- [ ] `python3 scripts/check_workbook.py --workbook <path>` exits 0

---

## Salesforce-Specific Gotchas

1. **API-name reality check** — the workbook's `target_value` for an object or
   field must use API names that don't already exist (or that you intend to
   extend). Probe the org first; "we'll figure out the API name later" rows
   become rework.
2. **Section discipline drift** — teams under deadline pressure invent
   sections like "Misc" or "Other" to absorb rows that don't fit. Reject
   these — if it doesn't fit one of the 10 sections, it isn't a workbook row.
3. **PSG rows that pretend to be field rows** — a row that says "add the field
   *and* grant the SDR PSG access" is two rows. Pretending otherwise hides
   the permission change from the permission-set-architect agent.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `cwb.md` | The 10-section markdown workbook authored from `templates/config-workbook.md`. The committed sprint copy lives at `docs/workbooks/<release>/cwb.md`. |
| `cwb.json` | Machine-readable JSON envelope of the rows for downstream agents. |
| `cwb.csv` | Flat CSV export with one row per workbook row; useful for review in spreadsheets. |
| RTM linkage block | A short markdown table mapping `row_id → source_req_id → source_story_id → recommended_agent → status`. Lives at the top of `cwb.md`. |

---

## Official Sources Used

See `references/well-architected.md`.

---

## Related Skills

- `admin/custom-field-creation` — what an Objects+Fields row references but
  does not duplicate.
- `admin/permission-set-architecture` — what a Profiles+PSG row references.
- `admin/sharing-and-visibility` — what a Sharing Settings row references.
- `admin/validation-rules` — what a Validation Rules row references.
- `admin/lightning-app-builder-advanced` — what a Lightning Pages row references.
- `admin/reports-and-dashboards` — what a Reports+Dashboards row references.
- `data-loader-pre-flight` agent — consumer for Data + Migration rows.
- `agents/object-designer/AGENT.md` — primary consumer for Objects+Fields rows.
- `agents/permission-set-architect/AGENT.md` — primary consumer for PSG rows.
- `agents/flow-builder/AGENT.md` — primary consumer for Automation rows.
- `standards/decision-trees/automation-selection.md` — cited by every Automation row.
- `standards/decision-trees/sharing-selection.md` — cited by every Sharing Settings row.
