# Classifier: picklist

## Purpose

Audit picklist hygiene across an sObject (or the full org, sampled): Global Value Set adoption vs inline picklists, inactive-value drift, label/API drift, translation coverage, dependent picklist chains, picklist usage by formulas / flows / integrations, and the "picklist chain" anti-pattern. Emits findings plus a consolidation plan for inline-to-GVS migrations. Not for redesigning the picklist vocabulary itself — that's a business decision the audit surfaces.

## Replaces

`picklist-governor` (now a deprecation stub pointing at `audit-router --domain picklist`).

## Inputs

| Input | Required | Example |
|---|---|---|
| `scope` | yes | `object:<ApiName>` \| `org` |
| `include_inactive` | no | default `true` — inactive values are part of the audit |

## Inventory Probe

1. Per object: `tooling_query("SELECT QualifiedApiName, DataType, ValueSet FROM FieldDefinition WHERE EntityDefinition.QualifiedApiName = '<object>' AND DataType IN ('Picklist','MultiselectPicklist')")`. `ValueSet` JSON is the source of truth for values, restricted flag, GVS reference.
2. `tooling_query("SELECT DeveloperName, MasterLabel, IsActive, ValueSet FROM GlobalValueSet")` — org-wide GVS inventory.
3. `tooling_query("SELECT IsoCode FROM Language WHERE IsActive = true")` — multi-language detection.
4. Dependency probe: `tooling_query` on CustomField metadata + the describe API for `PicklistDependency` records (best-effort; Tooling API coverage is uneven).
5. Usage probes: `list_validation_rules(object_name)`, `list_flows_on_object(object_name)` + flow XML text search, probe_apex_references (Wave-2 MCP tool).

Inventory columns (beyond id/name/active):
`data_type`, `is_restricted`, `gvs_ref` (or null), `value_count`, `inactive_value_count`, `is_dependent`, `controlling_field` (for dependent picklists).

## Rule Table

| code | severity | check | evidence_shape | suggested_fix |
|---|---|---|---|---|
| `PICKLIST_GVS_ELIGIBLE` | P1 | Inline picklist values exactly match an existing GVS | field API name + matching GVS developer name | See `Patches` — switch to GVS reference |
| `PICKLIST_NOT_RESTRICTED` | P1 | Unrestricted picklist on a persona-facing field | field API name + IsRestricted=false | Set restricted flag in metadata |
| `PICKLIST_INACTIVE_DRIFT` | P2 | > 10% of the picklist's values are inactive | value count / inactive count | Retire inactive values or merge into active set |
| `PICKLIST_LABEL_API_DRIFT` | P2 | API name and label diverge meaningfully | field API name + label | Rename either API (breaking) or label (non-breaking) for clarity |
| `PICKLIST_NO_TRANSLATION` | P1 | Org has > 1 active language AND picklist lacks translations | field API name + active-language count | Add translations via Translation Workbench |
| `PICKLIST_DEEP_DEPENDENCY` | P1 | Dependency chain depth > 2 (e.g. A → B → C → D) | chain visualization | Flatten by removing a level or promoting to a Record Type filter |
| `PICKLIST_ORPHAN_GVS` | P2 | GVS exists but is referenced by zero fields | GVS developer name | Retire the GVS or document its reserved purpose |
| `PICKLIST_UNUSED_VALUE` | P2 | Value is active but zero records hold it (sampled) | field + value + sample count | Deactivate or document |
| `PICKLIST_INTEGRATION_HARDCODE` | P1 | Value label referenced in a NamedCredential endpoint or Apex string literal (heuristic) | API name + Apex class id | Migrate integration to reference value by API name, not label |

## Patches

### PICKLIST_GVS_ELIGIBLE patch template

Cites `skills/admin/picklist-and-value-sets`.

```xml
<!-- target: force-app/main/default/objects/{Object}/fields/{Field}.field-meta.xml -->
<!-- addresses: PICKLIST_GVS_ELIGIBLE on {Object}.{Field} -->
<!-- cites: skills/admin/picklist-and-value-sets -->
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>{Field}</fullName>
    <label>{Label}</label>
    <type>Picklist</type>
    <valueSet>
        <valueSetName>{GVS_DeveloperName}</valueSetName>
        <restricted>true</restricted>
    </valueSet>
</CustomField>
```

### PICKLIST_NOT_RESTRICTED patch template

```xml
<!-- target: force-app/main/default/objects/{Object}/fields/{Field}.field-meta.xml -->
<!-- addresses: PICKLIST_NOT_RESTRICTED on {Object}.{Field} -->
<!-- cites: skills/admin/picklist-field-integrity-issues -->
<valueSet>
    <restricted>true</restricted>
    <valueSetDefinition>
        <!-- preserve existing values here -->
    </valueSetDefinition>
</valueSet>
```

## Mandatory Reads

- `skills/admin/picklist-and-value-sets`
- `skills/admin/picklist-field-integrity-issues`
- `skills/admin/multi-language-and-translation`

## Escalation / Refusal Rules

- Picklist has > 500 values → refuse per-value audit for that field; recommend split into GVS + controlled vocabulary. `REFUSAL_OVER_SCOPE_LIMIT`.
- Multi-language org with 0% translation coverage → org-level `PICKLIST_NO_TRANSLATION` escalated to Process Observations as P0; suggest `skills/admin/multi-language-and-translation` as the first step.
- Managed-package picklist → report but do not emit patches; `REFUSAL_MANAGED_PACKAGE`.

## What This Classifier Does NOT Do

- Does not modify picklist values in the org.
- Does not deploy GVS migrations.
- Does not clean data rows that hold invalid (now-inactive) picklist values — that's a separate data-fix project.
- Does not redesign the picklist vocabulary — decisions about which values to keep are business decisions.
