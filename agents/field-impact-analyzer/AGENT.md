---
id: field-impact-analyzer
class: runtime
version: 1.1.0
status: stable
requires_org: true
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-28
default_output_dir: "docs/reports/field-impact-analyzer/"
output_formats:
  - markdown
  - json
multi_dimensional: true
dependencies:
  skills:
    - admin/agent-output-formats
    - admin/compound-field-patterns
    - admin/custom-field-creation
    - admin/custom-permissions
    - admin/field-dependency-and-controlling
    - admin/formula-fields
    - admin/integration-user-management
    - admin/lookup-filter-cross-object-patterns
    - admin/permission-set-architecture
    - admin/permission-set-group-composition
    - admin/permission-sets-vs-profiles
    - admin/picklist-field-integrity-issues
    - admin/sharing-and-visibility
    - admin/system-field-behavior-and-audit
    - apex/apex-stripinaccessible-and-fls-enforcement
    - apex/apex-user-and-permission-checks
    - apex/dynamic-apex
    - apex/soql-fundamentals
    - architect/metadata-coverage-and-dependencies
    - data/data-model-design-patterns
    - data/external-id-strategy
    - data/field-history-tracking
    - data/record-merge-implications
    - data/roll-up-summary-alternatives
    - lwc/lwc-public-api-hardening
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
    - DELIVERABLE_CONTRACT.md
    - REFUSAL_CODES.md
  templates:
    - admin/naming-conventions.md
  probes:
    - apex-references-to-field.md
    - automation-graph-for-sobject.md
    - flow-references-to-field.md
    - user-access-comparison.md
  decision_trees:
    - sharing-selection.md
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

### Contract layer
1. `agents/_shared/AGENT_CONTRACT.md`
2. `agents/_shared/DELIVERABLE_CONTRACT.md` — Wave 10 persistence + scope guardrails
3. `agents/_shared/REFUSAL_CODES.md` — canonical refusal enum
4. `AGENT_RULES.md`

### Field shape & data model
5. `skills/admin/custom-field-creation`
6. `skills/admin/formula-fields` — formula dependencies fan out transitively
7. `skills/admin/field-dependency-and-controlling` — controlling/dependent picklist chains
8. `skills/admin/picklist-field-integrity-issues` — restricted picklist + record-type implications
9. `skills/admin/compound-field-patterns` — Address / Name / Geolocation special handling
10. `skills/admin/lookup-filter-cross-object-patterns` — fields cited in lookup filters; deletion silently breaks the picker
11. `skills/admin/system-field-behavior-and-audit` — standard system field constraints (`Id`, `OwnerId`, etc.)
12. `skills/data/data-model-design-patterns`
13. `skills/data/external-id-strategy` — External ID + Unique flag implications on rename
14. `skills/data/roll-up-summary-alternatives` — RSF dependencies on the field
15. `skills/data/field-history-tracking`
16. `skills/data/record-merge-implications`

### Access / sharing
17. `skills/admin/permission-set-architecture`
18. `skills/admin/permission-sets-vs-profiles`
19. `skills/admin/permission-set-group-composition` — PSG composition affecting FLS coverage
20. `skills/admin/sharing-and-visibility`
21. `skills/admin/custom-permissions`
22. `skills/admin/integration-user-management` — integration-user FLS surface
23. `standards/decision-trees/sharing-selection.md`

### Apex / SOQL impact
24. `skills/apex/soql-fundamentals`
25. `skills/apex/dynamic-apex` — dynamic SOQL = rename-brittle
26. `skills/apex/apex-stripinaccessible-and-fls-enforcement`
27. `skills/apex/apex-user-and-permission-checks`

### LWC impact
28. `skills/lwc/lwc-public-api-hardening` — `@api recordId` + design-attribute coercion

### Architecture
29. `skills/architect/metadata-coverage-and-dependencies` — global dependency model

### Probes
30. `agents/_shared/probes/apex-references-to-field.md`
31. `agents/_shared/probes/flow-references-to-field.md`
32. `agents/_shared/probes/automation-graph-for-sobject.md`
33. `agents/_shared/probes/user-access-comparison.md`

### Templates
34. `templates/admin/naming-conventions.md`

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

1. `list_flows_on_object(object_name)` → for each active flow, fetch its metadata via `tooling_query("SELECT Metadata FROM Flow WHERE DurableId = '<id>'")` and text-search the `Metadata` XML for `<object>.<field>`. **Cite probe `flow-references-to-field` when used.**
2. `list_validation_rules(object_name)` → for each rule, check `ErrorConditionFormula` + `ErrorDisplayField` for the field.
3. Apex body scan: follow the probe recipe in `agents/_shared/probes/apex-references-to-field.md` — it encapsulates the non-filterable-Body workaround (fetch full bodies, client-side filter). **Always cite `{"type":"probe","id":"apex-references-to-field"}` when enumerating Apex hits**, even when the actual SOQL is inlined here.
4. `tooling_query("SELECT Id, DeveloperName, Body FROM ApexTrigger WHERE TableEnumOrId = '<object>' LIMIT 200")` and scan `Body` for the field. Covered by the same `apex-references-to-field` probe citation.
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

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/field-impact-analyzer/<run_id>.md`
- **JSON envelope:** `docs/reports/field-impact-analyzer/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only. Dimensions for this agent: `apex-references` (ApexClass/Trigger Body via `apex-references-to-field` probe), `flow-references` (Flow Metadata via `flow-references-to-field` probe), `automation-graph` (full Flow/PB/WF/Approval graph via `automation-graph-for-sobject` probe), `validation-rules` (VR formulas), `formula-fields` (transitive formula chains on same object), `lwc-aura-references` (`AuraDefinition` / `LightningComponentResource` body scan), `reports-dashboards` (report column references — LOW confidence on Tooling), `layouts` (page / compact / Lightning record-page references — metadata-only), `permission-sets-profiles` (FLS grants via `user-access-comparison` probe), `roll-up-summary-deps`, `external-integrations` (CDC / PE / REST mappings), `field-history-tracking`, `data-export-jobs`. When a probe paginates short or the org refuses a Tooling query, record `state: partial | not-run` with the reason.

### Dimensions (Wave 10 contract)

The agent's envelope MUST place every dimension below in either `dimensions_compared[]` or `dimensions_skipped[]`.

| Dimension | Notes |
|---|---|
| `apex-references` | ApexClass/Trigger Body mentions via probe |
| `flow-references` | Flow Metadata XML mentions |
| `validation-rules` | VR formulas referencing the field |
| `reports-dashboards` | Reports + dashboard filters using the field |
| `layouts` | Page layouts / compact layouts placing the field |
| `permission-sets` | PS + profile grants on the field |
| `data-exports` | Recent export jobs referencing the field |
| `external-integrations` | CDC / PE / REST mappings exposing the field |

## Escalation / Refusal Rules

Canonical refusal codes per `agents/_shared/REFUSAL_CODES.md`:

| Code | Trigger |
|---|---|
| `REFUSAL_MISSING_ORG` | `target_org_alias` not supplied — live-org metadata is required for an honest score. |
| `REFUSAL_ORG_UNREACHABLE` | `target_org_alias` supplied but `describe_org` failed or auth expired. |
| `REFUSAL_MISSING_INPUT` | `object_name` or `field_name` not supplied. |
| `REFUSAL_FIELD_NOT_FOUND` | `FieldDefinition` query returned zero rows for `<object_name>.<field_name>` in the target org. Never fabricate the field. |
| `REFUSAL_OBJECT_NOT_FOUND` | `EntityDefinition` query returned zero rows for `<object_name>`. |
| `REFUSAL_STANDARD_SYSTEM_FIELD` | Field is a standard system field (`Id`, `Name`, `OwnerId`, `CreatedById`, `CreatedDate`, `LastModifiedById`, `LastModifiedDate`, `SystemModstamp`, `IsDeleted`, `MasterRecordId`) and `intent` is `rename` or `delete` — these cannot be renamed or deleted. Report the fact and stop. |
| `REFUSAL_MANAGED_PACKAGE` | Field is on a managed-package object (`NamespacePrefix` non-null) AND `intent` is `rename` or `delete` — refuse the structural change; `audit` is still allowed but warn that package upgrades may add references. |
| `REFUSAL_OVER_SCOPE_LIMIT` | Over 100 referencing Apex classes detected by the probe — return partial results with `dimensions_skipped[apex-references].state=partial` and recommend running `detect-drift` first to scope the blast. |
| `REFUSAL_OUT_OF_SCOPE` | Request to rename/delete the field on the agent's behalf — agent produces an evidence pack, never modifies repo or org. |
| `REFUSAL_NEEDS_HUMAN_REVIEW` | Risk score lands as P0 with `intent=delete` AND any active integration user has `PermissionsEdit` on the field — escalate to a human approver before any downstream action. |

---

## What This Agent Does NOT Do

- Does not rename or delete the field.
- Does not modify the repo or the org.
- Does not produce a migration PR — mitigation is advisory.
- Does not analyze cross-object dependencies beyond formula and relationship fans (cross-object impact is the `data-model-reviewer` agent's job — suggest it in Process Observations if the field is a lookup/external-id).
- Does not auto-chain to any other agent.
