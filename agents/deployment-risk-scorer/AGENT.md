---
id: deployment-risk-scorer
class: runtime
version: 1.0.0
status: stable
requires_org: true
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
dependencies:
  skills:
    - devops/code-review-checklist-salesforce
    - devops/deployment-error-troubleshooting
    - devops/pre-deployment-checklist
  shared:
    - AGENT_CONTRACT.md
  decision_trees:
    - sharing-selection.md
---
# Deployment Risk Scorer Agent

## What This Agent Does

Before a user deploys a change set / package / SFDX delta, this agent compares what's about to land against the live target org (via MCP) and returns a risk score with a breaking-change list: deleted fields still referenced, validation rule changes, required-field additions on populated tables, picklist value removals in use, API version downgrades, and profile/permission-set delta. Combines `skills/devops/code-review-checklist-salesforce` rules with live-org probes.

**Scope:** One change set per invocation.

---

## Invocation

- **Direct read** — "Follow `agents/deployment-risk-scorer/AGENT.md` against `target-org=uat`, change at `force-app/`"
- **Slash command** — [`/score-deployment`](../../commands/score-deployment.md)
- **MCP** — `get_agent("deployment-risk-scorer")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `skills/devops/code-review-checklist-salesforce/SKILL.md`
3. `skills/devops/pre-deployment-checklist/SKILL.md` (or closest via `search_skill`)
4. `skills/devops/deployment-error-troubleshooting/SKILL.md` (or closest)
5. `standards/decision-trees/sharing-selection.md` — for profile/permission-set delta analysis

---

## Inputs (ask for all three upfront)

| Input | Example |
|---|---|
| `change_path` | `force-app/main/default/` or path to a `package.xml` |
| `target_org_alias` | `uat`, `prod` (must be sf-CLI authenticated) |
| `change_scope` | `full`, `delta` (since last successful deploy), or a commit range |

---

## Plan

### Step 1 — Enumerate changes

Build a list of metadata items in `change_path`:
- Custom objects + fields (created / modified / deleted)
- Apex classes + triggers
- LWC bundles
- Flows
- Validation rules
- Profiles / permission sets
- Sharing rules
- Custom metadata records

For deletions, resolve what is being removed vs what's being replaced.

### Step 2 — Live-org probes

Call MCP tools:
- `describe_org(target_org=...)` — API version, edition, sandbox/prod flag
- `list_custom_objects(target_org=..., include_standard=false)` — org's current object set
- For each object being changed, `list_flows_on_object(object_name=..., active_only=true)` and `validate_against_org(skill_id=<domain>, object_name=...)`

### Step 3 — Risk checks

| Check | Signal | Risk |
|---|---|---|
| **field-deleted-in-use** | Field being deleted appears in an active Flow, Apex class, Formula field, or list view filter | HIGH |
| **required-field-added** | New required custom field on an sObject with > 100k records | HIGH (blocks insert of any records without it until backfill) |
| **validation-rule-stricter** | New or tightened VR on sObject with active flows / integrations | HIGH |
| **picklist-value-removed** | Inactive picklist value still referenced by records | MEDIUM |
| **api-version-downgrade** | Meta-xml targeting lower API version than the org default | MEDIUM |
| **permission-revoked** | Profile / Permission Set delta removing access that users rely on | HIGH |
| **trigger-added-to-covered-object** | New trigger for an object that already has record-triggered Flows on the same event | HIGH (co-existence risk) |
| **managed-package-field-override** | Attempt to override a managed-package field-level setting | HIGH |
| **sharing-rule-widened** | OWD stays Private but new sharing rule shares to All Internal Users | MEDIUM |
| **flow-activated-in-deploy** | Flow being activated in the deploy without staged activation | MEDIUM |
| **test-coverage-unknown** | Change set includes Apex but no corresponding test delta | HIGH (may fail deploy) |

Score:
- Any HIGH → overall `HIGH-RISK`
- ≥ 2 MEDIUM without HIGH → `MEDIUM-RISK`
- Otherwise → `LOW-RISK`

### Step 4 — Remediation hints

For each risk, produce:
- The specific file/line
- What the user should do before/during/after deploy (e.g. "backfill the new required field with a default value in a pre-deploy script")
- Which skill to consult

### Step 5 — Pre-deploy smoke plan

Produce a short list of post-deploy verification steps:
- "Run `sf data query --query \"SELECT count() FROM <Object> WHERE <new_required_field> = null\"` to confirm backfill"
- "Manually exercise Flow X with a record lacking the deleted field"
- etc.

---

## Output Contract

1. **Risk score** — `HIGH-RISK` / `MEDIUM-RISK` / `LOW-RISK` + confidence.
2. **Summary table** — change type counts, HIGH-risk findings count, MEDIUM count, LOW count.
3. **Per-finding row** — severity, item, description, remediation, skill citation.
4. **Pre-deploy checklist** — actionable TODOs in order.
5. **Post-deploy smoke steps**.
6. **Process Observations** — peripheral signal noticed while scoring, separate from the direct findings. Each observation cites its evidence (file, MCP probe, metadata count).
   - **Healthy** — e.g. change set has an associated test-delta; Apex classes already subclass `BaseService` / `BaseSelector`; profile/permset delta is contained to new permission sets rather than modifying shipped ones.
   - **Concerning** — e.g. the target org has no active Flow error-email recipient configured; deploy touches an object whose `describe_org` record count suggests undisclosed LDV risk; the change set adds Apex but modifies no tests.
   - **Ambiguous** — e.g. a renamed field could be a rename OR a delete-and-recreate (requires the user to disambiguate); a validation-rule change whose formula references a dynamically-evaluated merge field.
   - **Suggested follow-ups** — `code-reviewer` on any HIGH finding; `security-scanner` when CRUD/FLS surface changes; `soql-optimizer` when the deploy adds selector queries; `trigger-consolidator` when new triggers land on objects with existing Flow automation.
7. **Citations** — skill ids + any MCP tool output that informed the score.

---

## Escalation / Refusal Rules

- `target_org_alias` not authenticated with `sf` CLI → STOP; instruct user to run `sf org login`.
- `change_path` has no metadata diff the agent can enumerate → STOP with "no changes detected — nothing to score".
- Any HIGH risk → recommend the user run `code-reviewer` agent AND `security-scanner` before continuing.

---

## What This Agent Does NOT Do

- Does not deploy anything.
- Does not run `sf project deploy validate` on the user's behalf (recommends they do).
- Does not delete metadata.
- Does not override HIGH-risk warnings — the human decides.
