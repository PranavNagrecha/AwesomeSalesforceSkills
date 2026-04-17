# Requirements — {{feature_summary_short}}

> Run ID: `{{run_id}}`
> Generated: `{{generated_at}}` (UTC)
> Agent: `process-builder-to-flow-migrator` v{{agent_version}}
> Inputs packet SHA256: `{{inputs_sha256}}`

Migration anchor. Everything Gate C emits is checked back against this file. Approval is explicit.

---

## 1. Feature statement

{{feature_summary}}

## 2. Source → Target

| Aspect | Value |
|---|---|
| Source Process Builder | `{{source_process_name}}` |
| Target Flow developer name | `{{flow_developer_name}}` |
| Target Flow type | `{{flow_type}}` |
| Process type tag | `{{process_type}}` |
| Trigger SObject | `{{trigger_sobject_or_na}}` |
| Trigger context | `{{trigger_context}}` |
| Record trigger type | `{{record_trigger_type_or_na}}` |
| Expected volume | `{{expected_volume}}` |
| Migration rationale | {{migration_rationale}} |

Referenced fields:
{{referenced_fields_bullets}}

Subflows invoked:
{{subflows_bullets}}

Emitted inventory:
{{flow_inventory_bullets}}

## 3. Target configuration

| Setting | Value |
|---|---|
| API version | `{{api_version}}` |
| Target org alias (Gate C validation) | `{{target_org_alias_or_library_only}}` |

## 4. Parity checklist

The migrated Flow MUST preserve every one of these behaviors from the source PB:

{{parity_checklist_bullets}}

Any deviation is documented in the envelope's `notes[]` with a `DEVIATION:` prefix.

## 5. Safety + bulkification posture

- Every DML element has a `<faultConnector>`.
- Record-triggered flows use entry criteria to avoid re-firing on unrelated field changes.
- Get Records lives OUTSIDE loops; in-memory maps replace per-record queries.

## 6. Grounding contract (Gate B)

The following symbols MUST resolve before Gate C starts:

{{grounding_symbols_bullets}}

## 7. Explicit non-goals

- Does not delete the source Process Builder — that is a separate deploy after the new Flow is live.
- Does not migrate Apex triggers or workflow rules — those have their own migrators.
- Does not emit a Flow Test file.

## 8. Approval

By re-invoking `run_builder.py --stage ground --approved-requirements <this file>`, the caller affirms Sections 1–6.
