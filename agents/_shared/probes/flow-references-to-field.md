# Probe: flow-references-to-field

## Purpose

Enumerate active Flows whose metadata XML references a given `<sObject>.<Field>` API name, and classify each reference as `read` vs `write`. Used by any agent computing the blast radius of a field change or looking for automation dependencies on a field.

## Arguments

| Arg | Type | Required | Notes |
|---|---|---|---|
| `object` | string | yes | sObject API name |
| `field` | string | yes | Field API name |
| `active_only` | boolean | no (default `true`) | Skip inactive/obsolete flow versions |

## Query

Two steps — list then fetch.

Step 1 — list candidate flows targeting the object:

```sql
SELECT Id, ApiName, ActiveVersionId, LatestVersionId, TriggerType
FROM FlowDefinitionView
WHERE (ProcessType = 'AutoLaunchedFlow'
    OR ProcessType = 'Flow'
    OR ProcessType = 'Workflow')
LIMIT 2000
```

`FlowDefinitionView.ApiName` — NOT `DeveloperName`. The camelCase flow developer name surfaces on this view object as `ApiName`.

(Agents that already know the object's automation context may use `list_flows_on_object(object_name)` directly.)

Step 2 — for each flow id, fetch the metadata:

```sql
SELECT Id, DefinitionId, Metadata, Status
FROM Flow
WHERE DefinitionId = '<id>'
  AND (Status = 'Active' OR Status = 'Obsolete')
```

## Post-processing

Within each `Metadata` XML blob, text-search for these anchors:

- `<objectType>...<field>` or `<stringValue>` that exactly matches `<Object>.<Field>`
- `<leftValueReference>...<field>`
- `<rightValueReference>...<field>`
- `<assignToReference>...<field>` (write)
- `<field>...<value>` inside `<recordCreates>` or `<recordUpdates>` (write)
- `<fields>...<field>` inside `<recordLookups>` (read)

Classification:

- `write` — match inside `<recordCreates>`, `<recordUpdates>`, or `<assignToReference>`.
- `read` — match inside `<recordLookups>`, `<decisions>`, `<formulas>`, or any `*Reference` element not listed above as write.

## Pagination

Step 1 loops with OFFSET until exhausted. Step 2 is per-flow and does not paginate (Metadata column is a single blob).

## False-positive filters

- Strip `<description>` and `<label>` text before scanning — human-written labels frequently mention field names without being real references.
- Ignore references inside `<pausedStates>` unless the agent explicitly needs them.
- Inactive flow versions are excluded when `active_only == true`.

## Returns

Array of records:

```json
{
  "flow_developer_name": "Account_Enrichment",
  "flow_id": "301...",
  "version_id": "301...",
  "active": true,
  "trigger_type": "RecordBeforeSave",
  "access_type": "read | write",
  "evidence_xml_snippet": "<recordUpdates name=\"UpdateIndustry\">...<field>Industry</field>..."
}
```

## Consumed by

- `field-impact-analyzer`
- `validation-rule-auditor` — VRs that fire on fields changed by flows
- `picklist-governor` — picklist rename impact
- `workflow-and-pb-migrator` — understanding what automation already references the field
