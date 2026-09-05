---
name: configuration-workbook-authoring
description: "Author the Salesforce Configuration Workbook — the structured, reviewable handoff document an admin uses to execute a feature across Objects/Fields, Page Layouts, Profiles/PSGs, Sharing, Validation, Automation, List Views, Reports, Integrations, and Data. Triggers: 'salesforce configuration workbook', 'admin handoff document', 'implementation workbook'. NOT for object design itself (use admin/custom-field-creation, admin/lookup-and-relationship-design, agents/object-designer/AGENT.md), NOT for permission set design (use admin/permission-set-architecture, agents/permission-set-architect/AGENT.md), NOT for Flow construction (use skills/flow/* and agents/flow-builder/AGENT.md), and NOT for the deployment manifest (use skills/devops/metadata-api-retrieve-deploy). More triggers: workbook row schema, recommended_agent, recommended_skills, row_id, source_req_id, RTM linkage block, not-in-scope-this-release, descope ledger, version-lock the workbook, check_workbook.py."
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
  - "what columns does a Salesforce configuration workbook row need"
  - "workbook row says build the renewal automation and nobody knows what to build"
  - "my workbook row names two agents and neither picked it up"
  - "recommended_agent in my workbook is a deprecated auditor"
  - "workbook cites a skill path that does not exist"
  - "how do I record a descoped requirement in the workbook"
  - "should OWD go in the sharing section or the objects section of the workbook"
  - "row lists a Profile but we grant access with permission sets"
  - "check_workbook.py fails with duplicate row_id"
  - "turn approved stories into admin build rows without losing traceability"
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
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
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

Gather this context before authoring or revising a workbook. Without all five,
the rows you write cannot be reviewed or routed.

| Input | Why the workbook cannot start without it |
|---|---|
| Approved user stories | Every row carries `source_story_id`. A row without an upstream story is orphaned and cannot be reviewed. |
| Approved fit-gap rows, with their descope decisions | Every row carries `source_req_id` (the RTM `req_id`) so the workbook traces back to the RTM — and the descope list tells you which requirements must produce *no* row. |
| Target org alias | API names, existing record types and existing PSGs must reflect the live org, not a wishlist. Probe before writing a `target_value`. |
| Sprint / release identifier | The workbook is version-locked at sprint commit; mid-sprint change requests open new rows rather than editing existing ones in place. |
| Downstream agent roster | Every `recommended_agent` must resolve to a real `agents/<id>/AGENT.md` that is not deprecated (see `agents/_shared/SKILL_MAP.md` and `agents/_shared/AGENT_DISAMBIGUATION.md`). |

---

## Questions to Ask Before Configuring

Ask these before writing a single row. Each answer removes one failure mode
from `references/gotchas.md`; a workbook written without them looks complete
and routes to nobody.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which requirements did the steering committee descope, defer or escalate?" | A descoped story that reappears as a row is a refusal condition for `config-workbook-author`, not a nice-to-have; an escalated one needs an ADR before any row exists | The descope ledger — the record of the requirements that deliberately produced no row (Gotcha 4 in `references/worked-examples.md` Rule 7) |
| "Who, by name, is accountable for each section landing in the org?" | `owner` is a person, not a team alias. A section owned by "the admin team" is a section nobody signs off, including the empty ones | A named owner per section, including for `not-in-scope-this-release` rows |
| "Which agent executes this row, and is it still on the runtime roster?" | The fourteen Wave-3b auditors still have `AGENT.md` files on disk, so an existence check passes them and routes the row to a stub | One live agent id per row, with `--domain=` arguments where `audit-router` replaced a retired auditor (Gotcha 8) |
| "For every automation and sharing row, which decision-tree branch resolved the tool choice?" | An unrecorded choice cannot be disagreed with at review, and "it was obvious" is the decision that goes unrecorded | A `<tree>.md Q<n>` citation plus one clause of reason on every Section 4 and Section 6 row (Gotchas 12 and 13) |
| "Is access granted through permission sets, or is this org still profile-driven?" | A profile row is unverifiable after deploy: a retrieved profile only carries FLS for what else was in the same manifest, and a profile deploy overlays rather than replaces | Section 3 rows that name permission sets, with profiles reserved for the residue that has no `PermissionSet` equivalent (Gotcha 15) |
| "What is the org's current state for every `target_value` you are about to write?" | API names, existing rules and existing PSGs collide silently; "we'll figure out the API name later" rows become rework | A probe date in `notes` beside each new component, so the reviewer knows the row was checked against reality and when |
| "What does version-lock mean here — who tags the file, and where does it live?" | `status: committed` is a per-row label an in-place edit can rewrite; only the snapshot is the lock | A path (`docs/workbooks/<release>/cwb.md`) and a tag, agreed before the sprint, not improvised at commit (Gotcha 14) |

What a proper configuration adds over just writing a build sheet: every
deployed component traces back to an approved requirement and forward to the
agent that built it, every technology choice carries the branch that decided
it, and the requirements that deliberately produced nothing are as visible as
the ones that produced rows.

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
| `source_req_id` | yes | The RTM `req_id` — `REQ-XXX`, immutable and never reused, per `admin/requirements-traceability-matrix` § ID Conventions. Orphan rows = REJECT. |
| `source_story_id` | yes | User-story id (e.g. `US-2031`). |
| `recommended_agent` | yes | Exactly ONE runtime agent id, optionally followed by `--flag` arguments (`audit-router --domain=sharing`). Must resolve to `agents/<id>/AGENT.md` **and** carry a frontmatter `status` that is not `deprecated`. |
| `recommended_skills[]` | yes (≥1) | Skill ids the executing agent must consult, `;`-delimited. Every entry resolves on disk: `<domain>/<slug>` → `skills/<domain>/<slug>/SKILL.md`, `<domain>/<slug> → references/<file>.md`, or a repo-relative `templates/…` / `standards/…` path. |
| `status` | yes | `proposed` \| `committed` \| `in-progress` \| `executed` \| `verified` \| `change-requested`. **Never** a placeholder — `check_workbook.py` rejects `TBD`, `WIP`, `DOING`, `NEXT`, `?`, a bare to-do marker, and empty (see `PLACEHOLDER_STATUS_TOKENS`). |
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

The default `recommended_agent` per section. `agents/_shared/SKILL_MAP.md`
is the authoritative roster; a row may name a different live agent when the
artefact warrants it, but never one that is absent from disk or deprecated.

| Section | `recommended_agent` |
|---|---|
| 1 — Objects + Fields | `object-designer` |
| 2 — Page Layouts + Lightning Pages | `audit-router --domain=lightning_record_page`; `path-designer` for Path + Guidance rows |
| 3 — Profiles + Permission Sets + PSGs | `permission-set-architect`; `profile-to-permset-migrator` when the row decomposes a profile |
| 4 — Sharing Settings | `audit-router --domain=sharing` |
| 5 — Validation Rules | `audit-router --domain=validation_rule` |
| 6 — Automation | `flow-builder` (net-new Flow), `apex-builder` (net-new Apex), `apex-refactorer` (existing class), `flow-analyzer` (object already carries automation), `assignment-and-auto-response-rules-designer` (Lead/Case ownership routing) |
| 7 — List Views + Search | `audit-router --domain=list_view_search_layout` |
| 8 — Reports + Dashboards | `audit-router --domain=report_dashboard` |
| 9 — Integrations | `integration-catalog-builder` |
| 10 — Data + Migration | `data-loader-pre-flight`; `csv-to-object-mapper` when CSV-to-object mapping is the dominant work; `duplicate-rule-designer` for dup-rule rows |

The five `audit-router --domain=…` entries are not stylistic. The
single-mode auditors they replaced (`sharing-audit-agent`,
`validation-rule-auditor`, `lightning-record-page-auditor`,
`list-view-and-search-layout-auditor`, `report-and-dashboard-auditor`) still
have `AGENT.md` files on disk carrying `status: deprecated` and
`deprecated_in_favor_of: audit-router`, so a row that names one passes an
existence check and routes to a stub. `agents/_shared/AGENT_DISAMBIGUATION.md`
holds the full old-name → `--domain=` mapping; `scripts/check_workbook.py`
reads the frontmatter and reports the row.

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

1. **Intake and the descope ledger.** Pull the approved stories and the
   fit-gap rows *including their descope decisions*. Confirm every story maps
   to a `req_id` and vice versa. Write the descope / defer / escalate ledger
   first (`references/worked-examples.md` Rule 7) — before any row exists, so
   a descoped requirement cannot quietly acquire one.
2. **Outline.** Copy `templates/config-workbook.md` to
   `docs/workbooks/<release>/cwb.md`. All ten sections, in canonical order,
   numbered — the checker verifies the numbering, because Sections 4 and 6
   are cited by number. Empty sections keep a `not-in-scope-this-release` row
   with a named owner.
3. **Populate.** One row per configurable artefact, per Patterns 1 and 3.
   Copy the shape from `references/worked-examples.md` Rules 1–6:
   `target_value` names a metadata component (never a Setup path), exactly
   one live `recommended_agent`, at least one `recommended_skills` entry you
   have opened, `status: proposed`, and — on every Section 4 and Section 6
   row — the `<tree>.md Q<n>` branch that resolved the tool choice.
4. **Check.** `python3 scripts/check_workbook.py --workbook
   docs/workbooks/<release>/cwb.md`. It resolves every agent (including
   `status: deprecated`), resolves every skill path against disk, enforces
   `row_id` uniqueness, the status enum, the tree citations, one-agent-per-row
   and the Section 3 profile rule. Exit code 1 fails a hook or CI step. Do
   **not** pass `--allow-empty-section` from here on.
5. **Review.** Walk `## Review Checklist` with the admin team and the BA. The
   checker proves the schema; the review is where `target_value` is checked
   against the org probe and the tree citation is argued with.
6. **Version-lock.** Set every in-scope row to `committed`, snapshot the file
   at `docs/workbooks/<release>/cwb.md`, and **tag it**. Both actions, or it
   is not locked (`references/gotchas.md` Gotcha 14). From here the file is
   append-only.
7. **Hand off and close out.** Give each downstream agent
   `(row_id, recommended_agent, recommended_skills, target_value,
   source_req_id)`. Assemble the deployment manifest from the committed rows
   (`references/worked-examples.md` Rule 8), then set each row to `executed`
   with the metadata path it produced, so the release report can show every
   `req_id` → `row_id` → metadata file.

---

## Review Checklist

Before declaring the workbook ready for sprint commit:

- [ ] Every row has a unique `row_id`
- [ ] Every row has both `source_req_id` and `source_story_id`
- [ ] Every row has exactly one `recommended_agent` from the runtime roster
- [ ] Every row has at least one entry in `recommended_skills[]`
- [ ] No row has a placeholder `status` — `TBD`, `WIP`, `DOING`, `NEXT`, `?`, a bare to-do marker, or empty
- [ ] All 10 canonical sections exist (empty sections carry a
      `not-in-scope-this-release` note)
- [ ] No row carries an inline credential, password, or token
- [ ] Every `recommended_agent` resolves to a non-deprecated `agents/<id>/AGENT.md`
- [ ] Every `recommended_skills` entry resolves to a file that exists on disk
- [ ] No `target_value` is a Setup navigation path
- [ ] Every Section 4 row cites `sharing-selection.md` and its `Q<n>` branch
- [ ] Every Section 6 row cites `automation-selection.md` and its `Q<n>` branch
- [ ] No Section 3 row grants access through a Profile (residue only)
- [ ] The descope / defer / escalate ledger exists and no descoped `req_id` has a row
- [ ] `python3 scripts/check_workbook.py --workbook <path>` exits 0 (no `--allow-empty-section`)

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
4. **Section-boundary confusion between OWD and sharing rules** — the org-wide
   default is the `sharingModel` element on the object file (Section 1); the
   `SharingRules` container is a different file (Section 4).
5. **Deprecated agents that still exist on disk** — a row naming
   `sharing-audit-agent` or `validation-rule-auditor` passes an existence
   check and routes to a stub; route to `audit-router --domain=<x>`.
6. **Profile rows that cannot be verified after deploy** — a retrieved profile
   only carries FLS for what else was in the same manifest, and a profile
   deploy overlays rather than replaces.

All fifteen, with the platform behaviour behind each, are in
`references/gotchas.md`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `cwb.md` | The 10-section markdown workbook authored from `templates/config-workbook.md`. The committed sprint copy lives at `docs/workbooks/<release>/cwb.md`. |
| `cwb.json` | Machine-readable JSON envelope of the rows for downstream agents. |
| `cwb.csv` | Flat CSV export with one row per workbook row; useful for review in spreadsheets. |
| RTM linkage block | A short markdown table mapping `row_id → source_req_id → source_story_id → recommended_agent → status`. Lives at the top of `cwb.md`. |
| Descope / defer / escalate ledger | The requirements that deliberately produced no row, with the decision, the rationale, who decided and when. Sits after Section 10. Without it a missing row is invisible. |
| `package.xml` | The deployment manifest assembled from the committed rows at hand-off. Shape and worked example in `references/worked-examples.md` Rule 8; the deploy itself belongs to `devops/metadata-api-retrieve-deploy`. |

---

## Official Sources Used

Canonical list, with the claim each source supports:
`references/well-architected.md` § Official Sources Used.

---

## Reference Files

| File | Read it when |
|---|---|
| `references/worked-examples.md` | You are about to write rows. Carries the nine format rules applied end to end to one small feature: the per-row schema, agent + skill resolution, the RTM linkage block, decision-tree citation, empty sections, the descope ledger, the `package.xml` the committed rows produce, and a real checker run. |
| `references/gotchas.md` | A row looks fine and something downstream refuses it, or you are reviewing someone else's workbook. Fifteen failure modes with the platform behaviour behind each. |
| `references/examples.md` | You want short excerpts of the row schema for a different domain (greenfield objects, PSG composition, multi-Flow automation) rather than the full format walk-through. |
| `references/llm-anti-patterns.md` | An assistant produced the workbook. Seven ways LLMs break the schema, with a detection hint for each. |
| `references/well-architected.md` | You need the pillar mapping, the tradeoffs behind the schema rigour, or the sources every platform claim in this package rests on (`## Official Sources Used` is canonical here). |
| `templates/config-workbook.md` | You are starting a workbook. The canonical ten-section skeleton, JSON envelope, CSV schema and hand-off block. |
| `templates/configuration-workbook-authoring-template.md` | You are planning the authoring task itself — scope, context gathered, which pattern applies, the authoring checklist. |
| `scripts/check_workbook.py` | Before sprint commit, and in CI on every PR touching a workbook. |
| `skills/admin/case-management-setup/references/worked-example-case-intake.md` | You want a full ten-section workbook for a real solution, not a format walk-through. |

---

## Related Skills

Upstream — what the workbook consumes:

- `admin/requirements-gathering-for-sf` — produces the raw requirements the RTM ids point at.
- `admin/user-story-writing-for-salesforce` — produces `source_story_id` and the story envelope's `recommended_agents[]` / `recommended_skills[]`.
- `admin/fit-gap-analysis-against-org` — produces `source_req_id`, the fit tiers, and the descope decisions Step 1 must honour.
- `admin/requirements-traceability-matrix` — owns the `req_id` convention and the forward/backward traceability the RTM linkage block serves.

Downstream — what a workbook row hands off to:

- `admin/object-creation-and-design`, `admin/custom-field-creation` — Section 1.
- `admin/lightning-app-builder-advanced` — Section 2.
- `admin/permission-set-architecture`, `admin/permission-sets-vs-profiles` — Section 3.
- `admin/sharing-and-visibility` — Section 4.
- `admin/validation-rules`, `admin/custom-permissions` — Section 5.
- `admin/assignment-rules`, `flow/record-triggered-flow-patterns` — Section 6.
- `admin/reports-and-dashboards` — Section 8.
- `data/external-id-strategy`, `data/data-loader-and-tools` — Section 10.
- `admin/change-management-and-deployment` — the release window and cutover the Section 10 deploy order feeds.
- `devops/metadata-api-retrieve-deploy` — the manifest and deploy the committed rows produce.

Routing authorities every row is bound to:

- `standards/decision-trees/automation-selection.md` — cited by every Section 6 row.
- `standards/decision-trees/sharing-selection.md` — cited by every Section 4 row.
- `agents/config-workbook-author/AGENT.md` — the agent that compiles a workbook from a backlog and a fit-gap report. This skill defines the format and the rules; that agent applies them. Its Step 3 (descope) and Step 6 (agent resolution) are the two behaviours `scripts/check_workbook.py` enforces.
- `agents/_shared/SKILL_MAP.md`, `agents/_shared/AGENT_DISAMBIGUATION.md` — the runtime roster and the deprecated-name mapping every `recommended_agent` is checked against.
