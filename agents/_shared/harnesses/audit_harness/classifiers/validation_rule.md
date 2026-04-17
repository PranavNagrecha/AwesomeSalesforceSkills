# Classifier: validation_rule

## Purpose

Audit Validation Rules on a target sObject for the six canonical pattern categories (data integrity, cross-field dependency, stage-gate, write-time audit, bulk-unsafe prevention, formula invariant), plus the bypass contract (`$Setup.Integration_Bypass__c` + `$Permission.Bypass_Validation_<Domain>`), VR-vs-before-save-flow conflicts, and error-message quality. Not for designing new VRs (that's `validation-rule-designer` when added) or for executing the fix (this classifier emits patches; humans deploy).

## Replaces

`validation-rule-auditor` (now a deprecation stub pointing at `audit-router --domain validation_rule`).

## Inputs

| Input | Required | Example |
|---|---|---|
| `object_name` | yes | `Opportunity` |
| `active_only` | no | default `false` — inactive rules are still reported |
| `intent` | no | `full` (default) \| `bypass-only` \| `conflict-only` |

## Inventory Probe

1. `list_validation_rules(object_name, active_only=<input>)` — MCP tool. Returns name, active flag, error message, error display field.
2. For each returned rule: `tooling_query("SELECT Id, ValidationName, Active, Description, ErrorMessage, ErrorDisplayField, ErrorConditionFormula FROM ValidationRule WHERE EntityDefinition.QualifiedApiName = '<object>' AND ValidationName = '<name>'")` — fetches the formula body (the bulk list tool doesn't include it).
3. `list_flows_on_object(object_name, active_only=True)` — used for Step-5 conflict check.
4. `list_record_types(object_name)` — used for Step-4 record-type relevance gate.

Inventory columns (beyond id/name/active):
`error_message`, `error_display_field`, `intent_class` (filled in Step 2 below), `bypass_state`.

## Rule Table

| code | severity | check | evidence_shape | suggested_fix |
|---|---|---|---|---|
| `VR_MISSING_BYPASS` | P0 | `ErrorConditionFormula` references neither `$Setup.Integration_Bypass__c` nor `$Permission.Bypass_Validation_<Domain>` | rule metadata path + matched formula excerpt | See `Patches` — inject the canonical inverted-AND bypass prefix |
| `VR_MISSING_CS_BYPASS` | P1 | Has Custom Permission bypass but no Custom Setting bypass | rule metadata path + formula | Add `$Setup.Integration_Bypass__c.Disable_Validation__c` to the prefix |
| `VR_MISSING_CP_BYPASS` | P2 | Has Custom Setting bypass but no Custom Permission bypass | rule metadata path + formula | Add `$Permission.Bypass_Validation_<Domain>` to the prefix |
| `VR_BYPASS_NOT_FIRST` | P2 | Bypass logic exists but is nested inside the formula rather than inverted-AND at the top | formula excerpt with nesting level | Refactor to inverted-AND prefix pattern per `templates/admin/validation-rule-patterns.md` |
| `VR_WRONG_TOOL` | P1 | Rule computes a value / enforces approval / checks external data (should be formula field, approval process, or flow with callout) | formula + intent_class classification | Recommend migration to the correct tool; no mechanical patch |
| `VR_MISSING_RT_SCOPE` | P1 | Object has > 1 active record type AND formula has no `RecordType.DeveloperName` check AND rule should not apply to all RTs | formula excerpt + RT inventory | Add `AND $RecordType.DeveloperName = 'X'` or use Wrong-Tool escalation |
| `VR_ISCHANGED_ON_INSERT` | P1 | Formula uses `ISCHANGED(Field)` without `NOT(ISNEW())` guard | formula excerpt | Wrap with `NOT(ISNEW()) && ISCHANGED(Field)` |
| `VR_ISBLANK_ON_FORMULA` | P2 | `ISBLANK(FormulaField)` is unreliable for compiled formula fields | formula excerpt + field type | Use the direct underlying expression or a flag field |
| `VR_PRIORVALUE_ON_FORMULA` | P1 | `PRIORVALUE(FormulaField)` — PRIORVALUE is unreliable on formula fields | formula excerpt | Materialize the prior value in a real field or remove the check |
| `VR_FLOW_CONFLICT` | P1 | Rule references a field written by an active before-save flow on the same save context | VR formula excerpt + conflicting flow name + field | Resolve ownership: either remove the VR check or move the write out of the flow |
| `VR_FIELD_NOT_FOUND` | P0 | Formula references a field that doesn't exist in the org | formula excerpt + missing field API name | Escalate to `field-impact-analyzer`; stop patching until resolved |
| `VR_MESSAGE_MISSING` | P1 | `ErrorMessage` is empty | rule row | Author a user-actionable error message; keep under 255 chars |
| `VR_MESSAGE_SHORT` | P2 | `ErrorMessage` under 10 chars | error message text | Rewrite with concrete user action |
| `VR_MESSAGE_SHOUTS` | P2 | `ErrorMessage` starts with "Error:" or ALL CAPS | error message text | Rewrite in neutral tone |
| `VR_MESSAGE_API_NAME` | P2 | `ErrorMessage` references a field by API name instead of label | error message text | Replace API name with field label |
| `VR_MESSAGE_HTML` | P2 | `ErrorMessage` contains HTML, internal IDs, or raw tokens | error message text | Strip to plain user-friendly copy |

Intent classification (feeds `VR_WRONG_TOOL`): per `templates/admin/validation-rule-patterns.md`, classify each rule into one of the 6 valid use cases or flag as Wrong-Tool. The classification is inventory metadata; Wrong-Tool is the finding.

## Patches

### VR_MISSING_BYPASS patch template

Cites `templates/admin/validation-rule-patterns.md` (the canonical inverted-AND bypass prefix).

```xml
<!-- target: force-app/main/default/objects/{Object}/validationRules/{RuleName}.validationRule-meta.xml -->
<!-- addresses: VR_MISSING_BYPASS on {Object}.{RuleName} -->
<!-- cites: templates/admin/validation-rule-patterns.md -->
<?xml version="1.0" encoding="UTF-8"?>
<ValidationRule xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>{RuleName}</fullName>
    <active>{active}</active>
    <description>{description}</description>
    <errorConditionFormula>AND(
  NOT($Setup.Integration_Bypass__c.Disable_Validation__c),
  NOT($Permission.Bypass_Validation_{Domain}),
  /* original condition below */
  {ORIGINAL_FORMULA}
)</errorConditionFormula>
    <errorMessage>{errorMessage}</errorMessage>
</ValidationRule>
```

### VR_MISSING_CS_BYPASS patch template

Same template as `VR_MISSING_BYPASS` but only the `NOT($Setup.Integration_Bypass__c.Disable_Validation__c)` line is prepended (the CP line already exists).

### VR_MISSING_CP_BYPASS patch template

Same template as `VR_MISSING_BYPASS` but only the `NOT($Permission.Bypass_Validation_{Domain})` line is prepended.

### VR_ISCHANGED_ON_INSERT patch template

```xml
<!-- target: force-app/main/default/objects/{Object}/validationRules/{RuleName}.validationRule-meta.xml -->
<!-- addresses: VR_ISCHANGED_ON_INSERT on {Object}.{RuleName} -->
<!-- cites: skills/admin/validation-rules -->
<errorConditionFormula>AND(
  NOT(ISNEW()),
  ISCHANGED({Field}),
  {REMAINING_ORIGINAL}
)</errorConditionFormula>
```

## Mandatory Reads

- `skills/admin/validation-rules`
- `skills/admin/formula-fields`
- `skills/admin/picklist-field-integrity-issues`
- `skills/data/data-quality-and-governance`
- `templates/admin/validation-rule-patterns.md`

## Escalation / Refusal Rules

- Object has > 100 VRs → return top-20 by severity, appendix the rest without patches. `REFUSAL_OVER_SCOPE_LIMIT`.
- Formula references a field that doesn't exist (`VR_FIELD_NOT_FOUND`) → stop patching; recommend `field-impact-analyzer`. `REFUSAL_FIELD_NOT_FOUND` per refusal codes.
- Formula nesting depth > 5 → refuse to patch (risk of semantic change); flag for manual refactor. `REFUSAL_NEEDS_HUMAN_REVIEW`.
- Required bypass Custom Setting / Custom Permission does not exist in the org → include stubs in the Patches block; note the user must deploy those BEFORE any patched VR activates.

## What This Classifier Does NOT Do

- Does not deactivate or modify VRs in the live org.
- Does not deploy the patch metadata.
- Does not convert Wrong-Tool VRs into flows or formulas — recommends the migration in Process Observations and links `automation-migration-router` / `flow-builder`.
- Does not audit VRs across multiple objects in one dispatch — one object per invocation.
