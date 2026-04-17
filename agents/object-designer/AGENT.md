---
id: object-designer
class: runtime
version: 1.1.0
status: stable
requires_org: true
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-17
harness: designer_base
dependencies:
  skills:
    - admin/custom-field-creation
    - admin/object-creation-and-design
    - admin/record-type-strategy-at-scale
    - admin/standard-object-quirks
    - admin/validation-rules
    - architect/large-data-volume-architecture
    - architect/solution-design-patterns
    - data/custom-index-requests
    - data/data-model-design-patterns
    - data/external-id-strategy
    - data/person-accounts
    - data/sharing-recalculation-performance
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
  templates:
    - admin/naming-conventions.md
    - admin/validation-rule-patterns.md
  decision_trees:
    - sharing-selection.md
---
# Object Designer Agent

## What This Agent Does

Given a business concept (a plain-English description like "we need to track maintenance contracts"), produces a Setup-ready object design: standard-vs-custom decision, API name, label, record types, canonical fields with types and naming, lookup/master-detail relationships, key validation rules, indexing plan, sharing posture, and the deployment order. The design is expressed as a human-reviewable spec *and* an sfdx metadata patch the user can scaffold from.

**Scope:** One object per invocation. Output is a spec the user reviews; no metadata is deployed and no files are committed by the agent.

---

## Invocation

- **Direct read** — "Follow `agents/object-designer/AGENT.md` to design an object for tracking maintenance contracts linked to Account."
- **Slash command** — [`/design-object`](../../commands/design-object.md)
- **MCP** — `get_agent("object-designer")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `skills/admin/object-creation-and-design` — the canonical design flow
4. `skills/admin/custom-field-creation` — field-level patterns
5. `skills/admin/record-type-strategy-at-scale` — if the spec implies > 1 persona or process
6. `skills/admin/validation-rules` — drive-time VR set at object creation
7. `skills/data/data-model-design-patterns` — relationship patterns
8. `skills/data/external-id-strategy` — if integration-source object
9. `skills/data/person-accounts` — for any Account-variant design
10. `skills/architect/solution-design-patterns`
11. `skills/architect/large-data-volume-architecture` — for objects expected to exceed 10M rows
12. `standards/decision-trees/sharing-selection.md`
13. `templates/admin/naming-conventions.md`
14. `templates/admin/validation-rule-patterns.md`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `business_concept` | yes | "Track maintenance contracts linked to Accounts, with a primary technician and warranty expiration" |
| `target_org_alias` | yes | live-org probe confirms existing model, prevents duplicate design |
| `expected_row_volume` | no | `small` (< 100k), `medium` (100k–10M), `large` (> 10M). Defaults to `medium`. Drives LDV advice |
| `integration_source` | no | external system name if rows will be sourced via integration — drives External ID + upsert recommendations |
| `sensitivity` | no | `standard` / `pii` / `phi` / `pci` — drives encryption + access recommendations |

If `business_concept` is too vague to shape a schema, STOP and ask clarifying questions (see Escalation).

---

## Plan

### Step 1 — Probe the org for overlapping design

Before designing, confirm the org doesn't already contain a close match:

- `list_custom_objects(target_org=..., name_filter=<concept keyword>)` — existing custom objects.
- `tooling_query("SELECT QualifiedApiName, Label FROM EntityDefinition WHERE IsCustomSetting = false AND (Label LIKE '%<keyword>%' OR QualifiedApiName LIKE '%<keyword>%') LIMIT 50")` — includes standard objects (some concepts map to e.g. `Contract` or `Asset` and shouldn't be re-invented).

If a ≥ 70% semantic match exists, recommend extending it instead of creating a new object. Do not proceed unless the user confirms. This prevents the "I have 3 Contract objects" pattern.

### Step 2 — Decide standard vs custom

Walk the standard-object matcher:

| If concept maps to… | Recommend |
|---|---|
| customer-company entity | **Account** (or `Person Account` — see `skills/data/person-accounts`) |
| individual stakeholder | **Contact** |
| sales deal | **Opportunity** |
| service event | **Case** |
| contracted agreement | **Contract** (often misused; verify scope) |
| physical or logical inventory item | **Asset** |
| billing schedule | **Contract** + custom schedule object, or Revenue Lifecycle Management if licensed |
| everything else | Custom object `<Name>__c` |

Cite the relevant `skills/admin/standard-object-quirks` behavior per match when it exists.

### Step 3 — Generate the API name + label

Using `templates/admin/naming-conventions.md`:

- Apply hard rules (reserved words, suffix, length).
- Apply soft rules (domain prefix when org has > 100 custom objects — check via Step 1 probe).
- Emit: `Label`, `Plural Label`, `API Name`, `Description`, `Record Name` (Text vs Auto Number — if the business concept has no natural name, recommend Auto Number with a prefix per convention).

### Step 4 — Design the field set

Start from the business concept and enumerate required attributes. For each, assign:

| Concept | Default field type | Notes |
|---|---|---|
| Unique business identifier | External ID, `Text`, unique, case-insensitive | Name `<Domain>_External_Id__c` |
| Human name / title | Name field is enough; only add `Display_Name__c` formula if the record name is Auto Number |
| Categorical status | Picklist; max ~25 values before splitting into a GVS; never checkbox chain |
| Currency amount | Currency with scale 2 for most, 4 for unit pricing |
| Relationship to parent | Master-Detail if the child cannot exist independently AND parent sharing should cascade; otherwise Lookup |
| Audit event timestamp | DateTime + matching `_User__c` lookup |
| Soft-delete flag | Checkbox `Is_Archived__c` + View All on archived via PS |
| Duration | Number (Hours) or Number (Days); rarely DateTime deltas |

Score each field against `templates/admin/naming-conventions.md` before finalizing.

### Step 5 — Decide record types

If the concept mentions persona or process variance ("residential vs commercial contracts", "enterprise vs mid-market opportunities"):

- Design record types per `skills/admin/record-type-strategy-at-scale`.
- Cap at 4 record types on create; additional variations go into picklist-controlled branches.
- Name per convention: `<Object>_<Persona>`.

If no persona variance is signaled, omit record types. Do not add a Master-only record type as a placeholder — it becomes technical debt.

### Step 6 — Design the sharing posture

Walk `standards/decision-trees/sharing-selection.md`:

1. Default OWD based on the record's sensitivity + expected row volume.
2. Role hierarchy default assumed unless `sensitivity = phi` or the concept is explicitly horizontal.
3. Sharing rules only when default + hierarchy under-grant.
4. Apex Managed Sharing only when a declarative rule can't express the need.
5. Flag expected sharing-recalc cost for LDV objects (cite `skills/data/sharing-recalculation-performance` if `expected_row_volume == large`).

### Step 7 — Plan validation rules at object creation

Don't wait — ship the object with its baseline VRs. Use `templates/admin/validation-rule-patterns.md`:

- Required business-key VRs (External ID required on insert from integration source).
- Cross-field dependency VRs (e.g. `Warranty_Expiration_Date__c > Start_Date__c`).
- Every VR includes the canonical bypass (Custom Setting + Custom Permission). If those don't exist in the org, include their creation in the deployment order.

### Step 8 — Plan indexes

For LDV objects (`expected_row_volume == large`) or any object with an integration source:

- External ID field: auto-indexed.
- High-selectivity filter fields: recommend custom index request (cite `skills/data/custom-index-requests`).
- Report on the top 3 expected query patterns and confirm at least one column per pattern is indexed.

### Step 9 — Emit the deployment order

A strict order that avoids "cannot deploy field before object":

1. Custom Setting + Custom Permission for VR bypass (if new).
2. The object shell (+ Name field + Auto Number setup).
3. Fields (grouped: External ID first, then required fields, then optional).
4. Record Types.
5. Page Layouts / Lightning Record Pages.
6. Validation Rules.
7. Permission Sets (the `object-designer` emits stubs only; the full PS design is `permission-set-architect`'s job — suggest it in Process Observations).
8. Sharing settings.
9. List views (basic "All" view only).

### Step 10 — Emit the spec + scaffold

Two deliverables:

**A. Design spec** (human-readable markdown) — object header, field table, record types, VR list, sharing posture, indexing plan, deployment order.

**B. sfdx scaffold** (file-tree of metadata XML snippets for the user to copy into `force-app/main/default/objects/<Object>__c/`) — the object file, each field, each record type, each validation rule. Do not include layouts (they require per-org customization). Do not include permission sets (out of scope).

---

## Output Contract

One markdown document:

1. **Summary** — concept, standard-vs-custom decision, API name, confidence (HIGH/MEDIUM/LOW).
2. **Design spec** — the full spec from Step 10A.
3. **Scaffold metadata** — the XML snippets from Step 10B, one fenced block per file with its target path as a label.
4. **Deployment order** — numbered list from Step 9.
5. **Process Observations**:
   - **What was healthy** — org already has the naming prefix / bypass infra / etc.
   - **What was concerning** — proximity matches from Step 1, custom-object count trend, missing bypass infra.
   - **What was ambiguous** — fields that could plausibly be on the parent object instead, concepts that straddle standard + custom.
   - **Suggested follow-up agents** — `permission-set-architect`, `data-model-reviewer`, `sharing-audit-agent`, `validation-rule-auditor`.
6. **Citations** — all skills, templates, decision trees, and MCP tool calls.

---

## Escalation / Refusal Rules

- `business_concept` is under 8 words or lacks enough signal to infer 3+ fields → STOP and ask: expected parent object, expected lifecycle, expected users, expected volume.
- Step 1 finds a ≥ 70% match in the org → STOP and ask whether to extend existing or create new with explicit justification.
- `expected_row_volume == large` but no clear partition key (ExternalId + a time/tenant column) → refuse LDV spec and ask for partition strategy.
- Sensitivity is `phi` or `pci` and target org has `isSandbox=false` with no Platform Encryption — warn P0 and require user acknowledgement.

---

## What This Agent Does NOT Do

- Does not deploy metadata.
- Does not design permission sets (use `permission-set-architect`).
- Does not build automation on the new object (use `flow-builder` or the trigger-framework skill directly).
- Does not generate reports or dashboards (out of scope).
- Does not design page layouts — only recommends the record-page skeleton for `lightning-record-page-auditor` to flesh out.
- Does not auto-chain to any other agent.
