---
id: field-impact-analyzer
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
    - admin/custom-field-creation
    - admin/formula-fields
    - admin/picklist-and-value-sets
    - architect/metadata-coverage-and-dependencies
    - data/field-history-tracking
    - data/record-merge-implications
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
  templates:
    - admin/naming-conventions.md
---
# Field Impact Analyzer Agent

## What This Agent Does

Given a field on an sObject, produces a blast-radius report: every Apex class, trigger, Flow, LWC, report, dashboard, formula, validation rule, workflow field update, approval process, email template, record type, page layout, permission set, and integration endpoint that references the field, together with a classification of each reference (read / write / metadata-only) and a deletion/rename risk score. Used before any "can I rename this field?" or "can I delete this field?" decision.

**Scope:** One field per invocation. Output is a markdown report with a single P0/P1/P2 risk score. The agent never writes to the org and never generates a rename patch on its own — it hands the caller an evidence pack so a human makes the go/no-go call.

---

## Invocation

- **Direct read** — "Follow `agents/field-impact-analyzer/AGENT.md` on `Account.Industry`"
- **Slash command** — [`/analyze-field-impact`](../../commands/analyze-field-impact.md)
- **MCP** — `get_agent("field-impact-analyzer")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `skills/admin/custom-field-creation` — via `get_skill`
4. `skills/admin/formula-fields` — formula dependencies fan out
5. `skills/admin/picklist-and-value-sets` — picklist dependencies
6. `skills/data/field-history-tracking` — tracking implications for audited fields
7. `skills/data/record-merge-implications` — merge-time field behavior
8. `skills/architect/metadata-coverage-and-dependencies` — global dependency model
9. `templates/admin/naming-conventions.md`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `object_name` | yes | `Account` |
| `field_name` | yes | `Industry` (or `Industry__c` for custom) |
| `target_org_alias` | yes | `prod`, `uat`, `mydevsandbox` |
| `repo_path` | no | path to the sfdx project root; default `force-app/main/default` |
| `intent` | no | `rename` / `delete` / `audit` — changes severity thresholds |

If `target_org_alias` is missing, STOP and ask — live-org metadata is required for an honest score.

---

## Plan

### Step 1 — Confirm the field exists and capture its type

- `describe_org(target_org=...)` — confirm connection.
- `tooling_query("SELECT QualifiedApiName, DataType, Length, Custom, InlineHelpText, ExternalId, Unique FROM FieldDefinition WHERE EntityDefinition.QualifiedApiName = '<object>' AND QualifiedApiName = '<object>.<field>' LIMIT 1")`.
- If the row is absent, STOP with a clear error. Never fabricate the field.

### Step 2 — Enumerate repo references

Scan `repo_path` (default `force-app/main/default`) for the field. Distinguish:

| Match type | Treatment |
|---|---|
| Apex class / trigger — `<Object>.<Field>` or `SObjectType.<Object>.fields.<Field>` | Classify as **read** if only inside a SELECT or a getter; **write** if assigned or in DML payload |
| SOQL string literal (including dynamic) | Classify as **read**. Dynamic SOQL flagged at P1 (rename-brittle) |
| LWC — `@wire` field list, `.js` references, `.html` bindings | **read** unless the template is in an `<lightning-record-edit-form>` with `field-name=...` (then **write**) |
| Aura — same treatment as LWC |
| Flow XML — `<field>` / `<objectType>` / `<leftValue>` / `<rightValue>` | **write** if in an assignment / update; **read** if in a decision or getValue |
| Validation Rule XML | **read** (references field in formula) |
| Formula field XML | **read** — transitive formulas follow |
| Page layout XML / compact layout / Lightning record page XML | **metadata-only** |
| Report / Dashboard / Folder XML | **read** |
| Email template / quickAction XML | **read** or **metadata-only** |
| Permission Set / Profile XML | **metadata-only** (FLS grant) |

For every reference, capture file path + line number for citation. No string-fingerprinting shortcuts; match by exact API name with word boundaries.

### Step 3 — Enumerate org references

Use MCP tools against the target org:

1. `list_flows_on_object(object_name)` → for each active flow, fetch its metadata via `tooling_query("SELECT Metadata FROM Flow WHERE DurableId = '<id>'")` and text-search the `Metadata` XML for `<object>.<field>`.
2. `list_validation_rules(object_name)` → for each rule, check `ErrorConditionFormula` + `ErrorDisplayField` for the field.
3. `tooling_query("SELECT Id, Name, Body FROM ApexClass WHERE Body LIKE '%<field>%' AND NamespacePrefix = null LIMIT 200")` (then in-memory filter for real references — avoids false positives from substring matches).
4. `tooling_query("SELECT Id, DeveloperName, Body FROM ApexTrigger WHERE TableEnumOrId = '<object>' LIMIT 200")` and scan `Body` for the field.
5. `tooling_query("SELECT DeveloperName, Metadata FROM CustomField WHERE EntityDefinitionId IN (SELECT DurableId FROM EntityDefinition WHERE QualifiedApiName = '<object>') LIMIT 500")` — for formula fields on the same object, scan their metadata for the target field.
6. `tooling_query("SELECT DeveloperName, Body FROM AuraDefinition WHERE Body LIKE '%<field>%' LIMIT 200")` and `LightningComponentResource` for LWC.
7. `tooling_query("SELECT Id, Name, DeveloperName FROM Report WHERE Format != 'Deprecated' AND Report.DeveloperName LIKE '%' LIMIT 500")` + description scan for the field (reports don't expose column metadata via Tooling for free — flag this as LOW confidence if not covered by the repo scan).

Every reference recorded with: source system, artifact id, artifact name, access type, and evidence string (an excerpt around the match).

### Step 4 — Compute the risk score

Derive a score per `intent`:

| Scenario | P0 | P1 | P2 |
|---|---|---|---|
| **Rename** | Any integration user (identified via `list_permission_sets`) has `PermissionsEdit` on the field AND any Apex class uses dynamic SOQL referencing the field | Apex / Flow write references found; formula fields depend on the field | Only page-layout / permission-set / report references |
| **Delete** | Any active Flow or Apex class writes to the field | Active VRs / approval steps reference the field; field is an External ID or `Unique`; field feeds a roll-up summary on the same object | Only read-only references remain |
| **Audit** | Field history tracking enabled + field is PII-classified — heightened scrutiny needed | Field is used by integrations but undocumented | Informational only |

Set a single overall confidence:
- **HIGH** — repo + org probes both completed with no pagination errors.
- **MEDIUM** — one probe paginated or partially failed.
- **LOW** — org access failed or repo path was missing.

### Step 5 — Suggested mitigation

Based on `intent`:

- **rename** → propose a phased path: create new field with canonical name per `templates/admin/naming-conventions.md`, dual-write for N days, migrate consumers, deprecate old field. Do NOT auto-generate the migration patch — the PR is a human judgment call.
- **delete** → propose a pre-delete checklist (clone field into a soft-archive object, backfill audit, validate against a sandbox first) and reference `skills/data/record-merge-implications`.
- **audit** → no action; report only.

---

## Output Contract

One markdown document:

1. **Summary** — field API name, data type, overall risk (P0/P1/P2), confidence (HIGH/MEDIUM/LOW).
2. **Reference inventory** — table grouped by system (Apex, Flow, LWC, VR, Formula, Reports, Layouts, Perms, Integrations). Each row: artifact, access type, evidence excerpt, citation link.
3. **Risk breakdown** — the specific rules from Step 4 that triggered, each with a one-line justification.
4. **Mitigation plan** — phased steps specific to `intent`, no auto-patch.
5. **Process Observations** — per `AGENT_CONTRACT.md`:
   - **What was healthy** — naming convention adherence, FLS hygiene, tracked vs untracked.
   - **What was concerning** — sibling fields with overlapping semantics, dynamic SOQL anywhere in the repo, fields with no help text.
   - **What was ambiguous** — reports not probeable by Tooling, managed-package fields colliding with name.
   - **Suggested follow-up agents** — `object-designer` for model-level redesign, `permission-set-architect` for FLS tidy-up, `data-loader-pre-flight` if the field is referenced by upcoming loads.
6. **Citations** — every skill, template, and MCP tool invocation the agent used.

---

## Escalation / Refusal Rules

- No `target_org_alias` → refuse.
- Field does not exist in the target org → refuse with the queried payload.
- Over 100 referencing Apex classes → return partial results with a clear "truncated at 100" note and recommend running `org-drift-detector` first to scope the blast.
- Field is a standard system field (`Id`, `Name`, `OwnerId`, etc.) → refuse. Standard system fields cannot be renamed or deleted; report the fact and stop.
- Field is on a managed-package object (`NamespacePrefix` is non-null) → refuse rename/delete analysis; audit is still allowed but warn that package upgrades may add references.

---

## What This Agent Does NOT Do

- Does not rename or delete the field.
- Does not modify the repo or the org.
- Does not produce a migration PR — mitigation is advisory.
- Does not analyze cross-object dependencies beyond formula and relationship fans (cross-object impact is the `data-model-reviewer` agent's job — suggest it in Process Observations if the field is a lookup/external-id).
- Does not auto-chain to any other agent.
