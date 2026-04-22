---
name: field-dependency-and-controlling
description: "Dependent picklists in Salesforce: controlling field (picklist or checkbox), dependent picklist, valueSettings matrix in metadata, API behavior via SOAP/REST, LWC lightning-combobox with dependency. NOT for record types (use admin/record-types). NOT for validation rules."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - User Experience
tags:
  - admin
  - picklist
  - dependent-picklist
  - controlling-field
  - valuesettings
triggers:
  - "salesforce dependent picklist controlling field configure"
  - "dependent picklist not filtering by controlling value"
  - "lightning combobox dependent picklist lwc dynamic"
  - "dependent picklist api insert value invalid"
  - "checkbox controlling field dependent picklist options"
  - "valuesettings metadata xml dependent picklist deploy"
inputs:
  - Controlling field (picklist or checkbox)
  - Dependent picklist
  - Mapping matrix (which dep values available for each controlling value)
outputs:
  - valueSettings metadata block
  - LWC / Aura pattern for dependent combobox
  - API insert behavior expectations
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-22
---

# Field Dependency and Controlling

Activate when configuring dependent picklists — Salesforce's built-in mechanism for filtering a picklist's options based on another field's value. UI honors the matrix; the API does not enforce it the way users expect.

## Before Starting

- **Check controlling-field type.** Only picklist or checkbox. Multi-select picklists cannot be controlling fields.
- **Count values.** Controlling picklist up to 300 values; dependent up to 300. Each controlling value can have up to 300 dependent values enabled.
- **Decide per record type.** Picklist dependencies are global for a field, but picklist values can be filtered further per Record Type.

## Core Concepts

### Controlling vs Dependent

A **controlling field** determines which values of a **dependent picklist** are available. The mapping is a matrix stored in the dependent picklist's `valueSettings`.

```xml
<fields>
    <fullName>Category__c</fullName>
    <type>Picklist</type>
    <valueSet>
        <controllingField>Parent_Category__c</controllingField>
        <valueSetDefinition>
            <value><fullName>Laptops</fullName></value>
            <value><fullName>Desktops</fullName></value>
        </valueSetDefinition>
        <valueSettings>
            <controllingFieldValue>Computers</controllingFieldValue>
            <valueName>Laptops</valueName>
        </valueSettings>
        <valueSettings>
            <controllingFieldValue>Computers</controllingFieldValue>
            <valueName>Desktops</valueName>
        </valueSettings>
    </valueSet>
</fields>
```

### UI vs API enforcement

- **UI (LEX, Aura, LWC standard components):** Enforces the matrix. Users see only valid combinations.
- **SOAP/REST API, Apex DML, Data Loader:** Does NOT enforce the matrix by default. You can insert `Parent=Computers, Category=Phones` via API and it succeeds.
- To enforce on API writes: add a Validation Rule or a Before-Save flow/trigger.

### Checkbox as controlling field

Checkbox has two "values": `true` and `false`. The matrix is a 2-column table.

### Global Value Sets

If either field uses a Global Value Set, dependencies are still per-field — the dependency metadata lives on the dependent field, not the GVS.

### Record Types add a second filter

`RecordType → picklistValues` further limits values. Order of filters: Record Type restricts first, then controlling field filters within that subset.

## Common Patterns

### Pattern: API validation rule for dependent picklist

```
AND(
  ISPICKVAL(Parent_Category__c, "Computers"),
  NOT(ISPICKVAL(Category__c, "Laptops")),
  NOT(ISPICKVAL(Category__c, "Desktops"))
)
```

Covers the case where API writes skip UI filtering.

### Pattern: LWC dependent combobox

```javascript
import { getPicklistValues } from 'lightning/uiObjectInfoApi';

@wire(getPicklistValues, {
    recordTypeId: '$recordTypeId',
    fieldApiName: PRODUCT_OBJECT.fieldApiName
})
picklistValues({ data }) {
    if (data) {
        this.controllerMap = data.controllerValues;
        this.valuesByController = data.values.reduce((acc, v) => {
            v.validFor.forEach(idx => {
                const key = Object.keys(this.controllerMap)[idx];
                (acc[key] = acc[key] ?? []).push({ label: v.label, value: v.value });
            });
            return acc;
        }, {});
    }
}
```

### Pattern: Deploying the matrix

`valueSettings` blocks must include every (controllingValue, dependentValue) pair that should be enabled. Omitted pairs are disabled.

## Decision Guidance

| Situation | Approach |
|---|---|
| Standard LEX form | Dependency matrix alone — UI enforces |
| Data Loader / API integrations | Dependency + Validation Rule |
| LWC custom component | `getPicklistValues` + build filter map client-side |
| Cascading 3+ levels | Multiple dependencies (each dep can be controlling for the next) |
| Different options per RecordType | Record Type picklist values + dependency matrix |
| Controlling by a non-picklist field | Use Flow/formula to set a picklist controller, or convert logic |

## Recommended Workflow

1. Confirm controlling field is picklist or checkbox (not multi-select, text, or number).
2. Build the matrix in Setup → Field Dependencies, or author valueSettings in XML.
3. For every integration path (API, Data Loader, Apex), add a Validation Rule or Before-Save automation to enforce the matrix.
4. For custom LWC, use `getPicklistValues` not hardcoded arrays.
5. Write a test inserting an invalid combination via Apex — assert the Validation Rule fires.
6. Document the matrix in the field description (help text is limited to 255 chars; use description).
7. Deploy as a unit — dependent picklist XML must include all valueSettings.

## Review Checklist

- [ ] Controlling field is picklist or checkbox
- [ ] valueSettings matrix covers all intended combinations
- [ ] Validation Rule OR Before-Save enforces matrix on API writes
- [ ] LWC custom components use `getPicklistValues`, not hardcoded values
- [ ] Record Type picklist assignment updated for new values
- [ ] Apex test covers invalid-combination insert via API

## Salesforce-Specific Gotchas

1. **API writes bypass dependency enforcement.** Without a Validation Rule, a bad combination inserts cleanly, and later breaks UI views ("invalid picklist value").
2. **Adding a new value to the controlling picklist does NOT automatically enable it** — you must edit valueSettings to enable the dependent values.
3. **Record Types filter first.** A value disabled at the Record Type level is unreachable regardless of dependency matrix.
4. **Multi-select picklist cannot be a controlling field.** Use a workaround with a normal picklist that captures the primary selection.
5. **Reporting filters don't respect dependencies** — a stale invalid combination shows up unless you filter explicitly.
6. **`getPicklistValues` wire adapter is recordType-aware** — passing master record type (012000000000000AAA) returns all values regardless of RT restrictions.

## Output Artifacts

| Artifact | Description |
|---|---|
| valueSettings metadata block | XML matrix for deployable dependency |
| API-side Validation Rule | Enforces matrix on API/DML writes |
| LWC dependent combobox | `getPicklistValues` + client-side filter map |

## Related Skills

- `admin/record-types` — RT-level picklist filtering layers on top
- `admin/validation-rules-patterns` — enforcing matrix via VR
- `lwc/lwc-wire-refresh-patterns` — `getPicklistValues` wire behavior
