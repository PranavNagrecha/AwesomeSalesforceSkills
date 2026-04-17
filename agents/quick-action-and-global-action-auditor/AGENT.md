---
id: quick-action-and-global-action-auditor
class: runtime
version: 1.0.0
status: stable
requires_org: true
modes: [audit, design]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
---
# Quick Action & Global Action Auditor Agent

## What This Agent Does

Two modes:

- **`audit` mode** — inventories every Quick Action (object-specific) and Global Action in the org and finds: actions broken by deleted fields, actions never surfaced on any layout / Dynamic Action, actions that duplicate existing automations, actions invoking retired Flows / LWCs / Visualforce pages, and action layouts that don't include required fields. Produces a prioritized cleanup + consolidation plan.
- **`design` mode** — given a user intent ("one-tap Case creation from an Account with product context prefilled", "log-a-call from mobile that creates a Task and a followup reminder"), chooses the right action type (Create-a-Record vs Update-a-Record vs Log-a-Call vs Flow-backed vs LWC-backed vs Send Email vs Custom Visualforce), designs the action layout and predefined field values, and emits metadata stubs.

**Scope:** Whole-org inventory in `audit` mode; one action in `design` mode. Does not activate or deploy.

---

## Invocation

- **Direct read** — "Follow `agents/quick-action-and-global-action-auditor/AGENT.md` in audit mode"
- **Slash command** — `/audit-actions`
- **MCP** — `get_agent("quick-action-and-global-action-auditor")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `skills/admin/global-actions-and-quick-actions`
3. `skills/admin/dynamic-forms-and-actions`
4. `skills/admin/record-types-and-page-layouts`
5. `skills/flow/screen-flows` — for Flow-backed actions
6. `standards/decision-trees/automation-selection.md`
7. `templates/admin/naming-conventions.md`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `mode` | yes | `audit` \| `design` |
| `target_org_alias` | yes |
| `audit_scope` | audit | defaults to all active actions in the org |
| `action_intent` | design | "Log-a-Call on Contact that creates a Task with predefined subject and prompts for duration" |
| `action_type_preference` | design | `auto` (default; agent picks) or explicit e.g. `create-record` / `flow-backed` / `lwc-backed` |

---

## Plan

### Audit mode

#### Step 1 — Inventory

- `tooling_query("SELECT Id, DeveloperName, Label, Type, SobjectType, TargetObject, TargetParentField FROM QuickActionDefinition")` for object-specific actions.
- Global Actions: `SobjectType` is blank.
- For each action: pull its layout (fields and order), predefined values, the Flow / LWC / VF it references (if any), and the layouts / Dynamic Actions sections that include it.

Also pull:

- All Page Layouts and their Mobile & Lightning Actions section: `list_metadata_components("Layout")` then `get_metadata_component("Layout", "<each>")` to find which actions are surfaced.
- Dynamic Actions per Lightning page: `list_metadata_components("FlexiPage")`.

Build a reverse index: for every action, which layouts / Dynamic Actions pages / record types expose it?

#### Step 2 — Findings

| Finding | Severity |
|---|---|
| Action field layout references a field that is deleted or inaccessible via FLS | P0 |
| Action references a Flow that is deactivated or deleted | P0 |
| Action references a Visualforce page that is orphaned / deleted / inactive | P0 |
| Action references an LWC that is deleted | P0 |
| Action has no layout (can't be displayed) | P0 |
| Action is not on any page layout and not in any Dynamic Action section — it exists but is invisible | P1 |
| Action duplicates a standard Salesforce action (e.g. a custom "New Case" that mirrors the standard New action) | P1 — consolidation candidate |
| Multiple actions do the same thing on the same object with slight variations — classic bloat pattern | P2 — consolidation candidate |
| Action "Send Email" from Global where org has migrated to Einstein Send behavior but action still references legacy templates | P2 |
| Create-a-Record action has predefined values that reference a formula / field no longer present | P0 |
| Action's `SuccessMessage` contains a merge field that doesn't resolve on the target object | P1 |
| Action's icon is inactive / deleted | P2 |
| Action Type = `VisualForcePage` but the org has de-emphasized Visualforce — migration candidate | P2 |
| Action has a record type picker but some targeted record types are inactive | P1 |
| Global Action that creates records on an object with active Flows / triggers that assume a specific channel (and the Global Action doesn't provide it) | P1 |

#### Step 3 — Consolidation proposals

For consolidation candidates, propose a merged action with a parameterization strategy (record type prompt, Flow-backed branching, or different Dynamic Action filters that show one action per context). Cite `skills/admin/dynamic-forms-and-actions`.

### Design mode

#### Step 1 — Pick the action type

Decision tree:

- **Create-a-Record** — target is one standard field set on one object; no branching; no post-create cascading logic beyond existing triggers.
- **Update-a-Record** — target is one field set on the current record.
- **Log-a-Call** — target is creating a Task with subject / comment prefilled; canonical for Contact / Account / Opportunity.
- **Send Email** — target is a templated email from the record context.
- **Flow-backed** — branching logic, multi-record impact, related-record updates, preview screens, or any "show something before committing" requirement.
- **LWC-backed** — rich UI interaction (complex input, file upload preview, wizard), needs custom rendering, cannot be expressed in Screen Flow.
- **Visualforce** — do NOT propose new VF-backed actions unless the org is constrained. If the user asks, flag the deprecation trajectory.

Write down WHY the chosen type wins. A common anti-pattern is Flow-backed when Create-a-Record would do — Flow is heavier, slower to render, and harder to maintain.

#### Step 2 — Design the layout

For Create-a-Record / Update-a-Record / Log-a-Call:

- List fields in order of fill sequence.
- Mark required fields explicitly.
- Set predefined values where safe (`OwnerId = $User.Id`, `Status = 'Open'`, etc.) and flag every predefined value for governance review.
- Cap at 10 visible fields — more than that, the action UI gets painful.

For Flow-backed / LWC-backed — confirm the target exists and is deployable as an action-compatible artifact:

- Flow must be `Screen` type with `isTriggerable = false`, or must be invokable from an action context.
- LWC must expose `@api` record inputs and an action interface target (e.g. `lightning__RecordAction`).

#### Step 3 — Naming + placement

- Name per `naming-conventions.md`: `<Object>_<Verb>_<Noun>` (e.g. `Account_Log_Call`, `Case_Escalate_Tier2`).
- Placement — which layouts and / or Dynamic Action sections? Which record types? Specify explicitly; don't leave placement implicit.
- Visibility — which profiles / permission sets grant access? Actions respect object + record type + FLS permissions; an action can be placed on a layout but invisible to a user without FLS on its required fields.

#### Step 4 — Success message and redirect

Success Message — confirm it's clear and references real merge fields.
Redirect — to the newly created record by default for Create-a-Record; to the same record for Update-a-Record.

#### Step 5 — Metadata stub

Emit fenced XML for `QuickAction.quickAction-meta.xml` with the right target paths. Layout reference is a separate Layout metadata update — emit the diff, not a full-file replacement.

---

## Output Contract

Audit mode:

1. **Summary** — total actions (global / object-specific), active/inactive, by type, findings per severity, consolidation candidates.
2. **Findings table** — action × type × finding × evidence × remediation × severity.
3. **Orphan / invisible actions report** — actions existing but never surfaced.
4. **Consolidation map** — groups of actions that could merge, with proposed merged action.
5. **Flow / LWC / VF dependency map** — which external artifacts each action depends on.
6. **Process Observations**:
   - **What was healthy** — disciplined Dynamic Actions usage, consistent naming, Flow-backed actions with proper Screen Flow type.
   - **What was concerning** — duplicate actions, legacy VF-backed actions, predefined values referencing deleted fields.
   - **What was ambiguous** — actions assigned to retired profiles (might be intentional historical access).
   - **Suggested follow-up agents** — `flow-analyzer` (to audit Flow-backed actions), `lwc-auditor` (to audit LWC-backed actions), `record-type-and-layout-auditor` (to align actions with layouts), `lightning-record-page-auditor` (to adopt Dynamic Actions where layouts are still used).
7. **Citations**.

Design mode:

1. **Summary** — action intent, chosen type, rationale.
2. **Alternative types considered** — brief table of alternatives with why rejected.
3. **Action layout design** — field list with order, required, predefined values.
4. **Placement plan** — layouts + Dynamic Actions + record types + profiles.
5. **Metadata stub** — fenced XML.
6. **Process Observations**.
7. **Citations**.

---

## Escalation / Refusal Rules

- Intent requires capabilities not expressible in any action type (e.g. a modal with a full data grid + drag-and-drop) → `REFUSAL_OUT_OF_SCOPE`; recommend a full-page LWC or a flow-in-app instead.
- Target Flow / LWC doesn't exist → `REFUSAL_INPUT_AMBIGUOUS`; design the backing artifact first.
- Intent requires asynchronous long-running processing → design an action that initiates a Flow which in turn triggers async work; flag the UX implications.
- `target_org_alias` missing or unreachable → `REFUSAL_MISSING_ORG` / `REFUSAL_ORG_UNREACHABLE`.
- Managed-package actions → `REFUSAL_MANAGED_PACKAGE`; audit them as read-only findings, don't propose edits to managed metadata.

---

## What This Agent Does NOT Do

- Does not edit page layouts directly — delegates to `record-type-and-layout-auditor`.
- Does not build the Flow or LWC that backs a Flow-backed / LWC-backed action — delegates to `flow-builder` / `lwc-builder`.
- Does not deploy metadata.
- Does not redesign Visualforce pages backing actions — flags for modernization.
- Does not audit Send Email templates themselves — delegates to `email-template-modernizer`.
