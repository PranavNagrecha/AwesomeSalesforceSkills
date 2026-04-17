# Classifier: record_type_layout

## Purpose

Audit the Record Type + Page Layout surface on a target sObject: RT count vs persona count, page-layout assignment coverage, picklist value set per RT, master-default-RT drift, and the relationship between RTs and Lightning Record Pages. Surfaces the three common failure patterns — record-type proliferation, Master Layout as primary, and orphan RTs. Not for designing new RTs (surface the need via `suggested_fix`; the design itself is a business decision).

## Replaces

`record-type-and-layout-auditor` (now a deprecation stub pointing at `audit-router --domain record_type_layout`).

## Inputs

| Input | Required | Example |
|---|---|---|
| `object_name` | yes | `Case` |

## Inventory Probe

1. `list_record_types(object_name)` — MCP tool.
2. Per RT: `tooling_query("SELECT Id, DeveloperName, Metadata FROM RecordType WHERE Id = '<id>'")` — metadata exposes business process + picklist value mappings.
3. `tooling_query("SELECT Id, Name, SobjectType, LayoutType, CreatedDate, LastModifiedDate FROM Layout WHERE EntityDefinition.QualifiedApiName = '<object>'")` — via Tooling.
4. `tooling_query` on `ProfileLayout` + `FlexiPageRegionAssignment` + `ProfilePageAssignment` — profile/PS → RT → Layout and RT → LRP maps. Fall back to `--metadata Profile` export if Tooling API lacks coverage.
5. Cross-reference: `list_flows_on_object(object_name, active_only=True)` + `list_validation_rules(object_name)` for Step-4 "inactive RT still referenced" check.

Inventory columns (beyond id/name/active):
`business_process_name`, `default_layout_name`, `lightning_record_page_name`, `assigned_profile_count`, `assigned_user_count` (via PS → user rollup), `is_master`, `description`.

## Rule Table

| code | severity | check | evidence_shape | suggested_fix |
|---|---|---|---|---|
| `RT_INACTIVE_REFERENCED` | P0 | Inactive RT is still referenced by an active Flow or Validation Rule | RT id + referencing artifact + reference type | Activate RT OR remove references; route via `flow-analyzer` if flow-sourced |
| `RT_PROLIFERATION` | P1 | Object has > 6 active RTs | RT count + naming cluster | Consolidation candidate per `skills/admin/record-type-strategy-at-scale` |
| `RT_MASTER_LAYOUT_PRIMARY` | P1 | Any active persona has Master Layout assigned as its primary | persona/profile + Master assignment | Create or assign a persona-appropriate layout |
| `RT_ORPHAN` | P1 | RT has no active users assigned | RT id + 0 assignments | Retire RT on next cleanup window |
| `RT_DESCRIPTION_BLANK` | P2 | RT description is empty | RT id | Document intent in description |
| `RT_PICKLIST_VAL_DIVERGENCE` | P2 | Picklist value sets diverge widely across RTs on the same field | field API name + divergence matrix | Consider GVS with RT-level filter (cross-ref `picklist` classifier) |
| `RT_MISSING_LRP` | P2 | Persona-specific RT has no dedicated Lightning Record Page (defaults to generic) | RT id + LRP assignment=default | Create RT-specific LRP per `skills/admin/dynamic-forms-and-actions` |
| `RT_BUSINESS_PROCESS_INACTIVE` | P1 | RT's `BusinessProcess` points at an inactive Sales Process / Support Process | RT id + BP name + BP active flag | Switch to active BP or retire RT |

## Patches

None. RT + Layout mechanical patches have a narrow patch-ability window: most changes need human review because they affect which users see which fields on which records. Findings stay advisory; deployment is a user decision.

## Mandatory Reads

- `skills/admin/record-type-strategy-at-scale`
- `skills/admin/record-types-and-page-layouts`
- `skills/admin/picklist-and-value-sets`
- `skills/admin/picklist-field-integrity-issues`

## Escalation / Refusal Rules

- Object has > 20 record types → sample top-8 by assignment volume; flag total count as `RT_PROLIFERATION` P1. `REFUSAL_OVER_SCOPE_LIMIT`.
- Inactive RT referenced by active flows → P0 escalation; recommend `flow-analyzer` before any further change.
- Managed-package RT → report but do not emit recommendations; `REFUSAL_MANAGED_PACKAGE`.

## What This Classifier Does NOT Do

- Does not activate / deactivate RTs.
- Does not modify layouts or Lightning Record Pages.
- Does not redesign picklist values (`picklist` classifier's scope).
- Does not design new RTs — surfacing the need is this classifier's scope; the design is a business discussion.
