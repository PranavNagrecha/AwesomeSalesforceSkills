---
name: field-dependency-and-controlling
description: "Dependent picklists in Salesforce: controlling field (picklist or checkbox), dependent picklist, valueSettings matrix in metadata, API behavior via SOAP/REST, LWC lightning-combobox with dependency. NOT for creating picklist fields or Global Value Sets and replacing retired values - use admin/picklist-and-value-sets. NOT for filtering picklist values per record type or layout - use admin/record-types-and-page-layouts. Keywords: controllingField, valueSettings, controllingFieldValue, valueName, checked/unchecked checkbox controller, RecordTypePicklistValue, isDependentPicklist, getController, validFor, controllerValues."
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
  - "data loader accepted an invalid controlling and dependent picklist combination"
  - "deploy removed a field dependency mapping but the pair is still enabled"
  - "fix checkbox controlling field valuesettings checked unchecked deploy error"
  - "dependent picklist value missing on a record type even though the matrix enables it"
inputs:
  - Controlling field (picklist or checkbox)
  - Dependent picklist
  - Mapping matrix (which dep values available for each controlling value)
outputs:
  - valueSettings metadata block
  - LWC / Aura pattern for dependent combobox
  - API insert behavior expectations
  - Validation rule that restates the matrix for non-UI writes
  - RecordType picklistValues entries covering the dependent values
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Field Dependency and Controlling

Activate when configuring dependent picklists — Salesforce's built-in mechanism for filtering a picklist's options based on another field's value. UI honors the matrix; the API does not enforce it the way users expect.

## Before Starting

- **Check controlling-field type.** Only picklist or checkbox. Multi-select picklists cannot be controlling fields.
- **Count values.** UNVERIFIED (2026-09-05): the commonly quoted 300-value ceilings for controlling and dependent picklists are not stated in the Metadata API guide, the Object Reference, or the Salesforce App Limits Cheat Sheet — the cheat sheet contains no picklist entry at all. The grounded ceiling nearby is the global value set: "up to 1,000 total values, including inactive values" (api_meta.txt:79363–79366). Treat 300 as a rule of thumb to confirm against Salesforce Help before quoting it.
- **Decide per record type.** Picklist dependencies are global for a field, but picklist values can be filtered further per Record Type.

## Questions to Ask Before Configuring

Ask these before opening Field Dependencies. Every one of them maps to a way this feature fails silently, and an assistant that skips them ships a matrix that looks correct in a demo org and leaks bad data in production.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which paths write these two fields — the record page only, or also Data Loader, an integration, or Apex?" | The filter is browser JavaScript that runs before the server sequence and nowhere else (Gotcha 6). Every other path saves anything. | The list of paths a validation rule or before-save must survive — or a documented decision that UI-only is genuinely the whole surface |
| "Is the controlling field a picklist or a checkbox?" | The matrix literals differ: value `fullName`s versus `checked`/`unchecked` (Gotcha 7). Getting it wrong ships an empty dropdown. | The exact `controllingFieldValue` strings, settled before any XML exists |
| "Does this matrix already exist in the target org, and does anything need to be **un**-mapped?" | Deploys add pairs and can never remove one (Gotcha 4). Un-mapping is a Setup task with its own change ticket. | A split of the work into a deploy and a Setup edit, instead of a deploy that silently does half of it |
| "Which profiles and permission sets can see the controlling field?" | A controlling field hidden by FLS drops out of `controllerValues` and the dependent picklist goes empty for exactly those users (Gotcha 1). | The FLS row for both fields together, and the partner/community profiles that need an explicit fallback |
| "Does the object have record types, and which of them should offer each dependent value?" | Availability is the intersection of record type and matrix, and Metadata API retrieval will not show you the gap (Gotcha 9). | The `RecordType.picklistValues` entries per record type, checked in Setup rather than in the repo |
| "How deep is the chain — two fields, or does the dependent field control a third?" | Each field sees only its immediate controller, and nothing clears a stale grandchild selection (Gotcha 2). | The deploy order, the number of wire calls, and the clear-on-change logic a custom component owes |
| "What do we do about rows that already hold a combination the new matrix forbids?" | Existing rows are untouched by a new matrix; they display blank in the UI while still returning a value in SOQL. | A count from the verification SOQL in `references/metadata-examples.md` §9 and a decision to backfill, report, or ship the rule inactive first |

What a proper configuration adds over just building the matrix in Setup: the same constraint is enforced on every write path rather than only in a browser, the record types actually expose the values the matrix enables, existing bad rows are counted before the rule starts rejecting them, and the pairs that were meant to be removed are actually removed instead of merely deleted from source control.

---

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

The matrix is a 2-column table, and its two column keys are the literals `checked` and `unchecked` — not `true` and `false`. The guide fixes them on `controllingFieldValues`: "The values in the list depend on the field type: • Checkbox: `checked` or `unchecked`. • Picklist: The fullname of the picklist value in the controlling field" (api_meta.txt:79250–79258). The checkbox field itself still stores and reads `true`/`false` everywhere else — in `<defaultValue>`, in SOQL, in Apex, in formulas. Only `controllingFieldValue` uses the other pair. See `references/gotchas.md` Gotcha 7.

### Global Value Sets

Dependencies are per-field. `GlobalValueSet` "isn't a field itself" (api_meta.txt:79344–79347) and has no `controllingField` element — `controllingField` and `valueSettings` are elements of each consuming field's own `ValueSet`, so two fields sharing one GVS need two separately maintained matrices.

A GVS-backed field as the **controlling** side is unambiguous: the controller is referenced by name only. Whether a GVS-backed field may be the **dependent** side is UNVERIFIED (2026-09-05) — the Metadata API guide neither permits nor forbids it (`controllingField`, `valueSetName` and `valueSettings` are peer elements of `ValueSet`, api_meta.txt:45843–45858), while `admin/picklist-and-value-sets` Gotcha 6 records from field experience that Setup does not offer GVS-backed fields in the dependent-field list. Until that is settled, model the dependent side with a local `valueSetDefinition`. See `references/metadata-examples.md` §5.

### Record Types add a second filter

`RecordType.picklistValues` is an independent second filter: each value it lists "is available in the record type that contains this component" (api_meta.txt:45051–45052). Availability is the **intersection** — a value must be listed on the record's record type *and* enabled for the selected controlling value. UNVERIFIED (2026-09-05): the guides do not state an evaluation *order* between the two filters, and for the observable outcome it does not matter; treat "record type restricts first" as a mental model, not a documented rule. See `references/metadata-examples.md` §6 and `admin/record-types-and-page-layouts`.

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

1. **Answer the seven questions above**, then run `python3 scripts/search_knowledge.py "dependent picklist controlling field"` and read `references/gotchas.md` end to end. Gotchas 4, 6, 7 and 9 each change what you write, not just how you review it.
2. **Write the matrix as a table before writing XML** — dependent values down the side, controlling values across the top, one tick per enabled pair. Copy the shape from `templates/field-dependency-and-controlling-template.md`; it is the artifact the validation rule and the record types are both derived from.
3. **Author the field files** from `references/metadata-examples.md` — §2 for a picklist controller, §3 for a checkbox controller (`checked`/`unchecked`), §4 for a chain, §6 for the `RecordType.picklistValues` entries. Retrieve the fields first; never assemble a picklist field file from scratch (Gotcha 8).
4. **Restate the matrix as a validation rule** (§7) for every non-UI write path the answers in step 1 identified. Skip this only where the answer was genuinely "record page only", and write that down.
5. **Run the checker** — `python3 skills/admin/field-dependency-and-controlling/scripts/check_field_dependency_and_controlling.py --manifest-dir force-app/main/default`. It resolves every `controllingField` to a real picklist or checkbox on the object, rejects `controllingFieldValue`s that are not in the controller's value set (including `true`/`false` on a checkbox controller), reports dependent values no controlling value enables, and flags dependent values missing from a record type that lists the field.
6. **Deploy in the order in §8** — controlling fields, dependent fields innermost-last, record types, validation rules — and use `sf project deploy validate` against production first.
7. **Verify in the org, not in the diff** (§9): assert `isDependentPicklist()` and `getController()` from Apex (see `references/examples.md` Example 3), run the invalid-combination SOQL to size the existing backlog, and read the pair count off the Setup Field Dependencies grid. A green deploy is not evidence a pair was removed.

## Review Checklist

- [ ] Controlling field is picklist or checkbox
- [ ] valueSettings matrix covers all intended combinations
- [ ] Validation Rule OR Before-Save enforces matrix on API writes
- [ ] LWC custom components use `getPicklistValues`, not hardcoded values
- [ ] Record Type picklist assignment updated for new values
- [ ] Apex test covers invalid-combination insert via API
- [ ] Checkbox controllers use `checked` / `unchecked`, never `true` / `false`
- [ ] Every dependent value appears on every record type that should offer it
- [ ] Any pair meant to be removed was removed in Setup, not just deleted from source
- [ ] `check_field_dependency_and_controlling.py --manifest-dir …` exits 0

## Salesforce-Specific Gotchas

1. **API writes bypass dependency enforcement.** Without a Validation Rule, a bad combination inserts cleanly, and later breaks UI views ("invalid picklist value").
2. **Adding a new value to the controlling picklist does NOT automatically enable it** — you must edit valueSettings to enable the dependent values.
3. **Record Types filter first.** A value disabled at the Record Type level is unreachable regardless of dependency matrix.
4. **Multi-select picklist cannot be a controlling field.** Use a workaround with a normal picklist that captures the primary selection.
5. **Reporting filters don't respect dependencies** — a stale invalid combination shows up unless you filter explicitly.
6. **`getPicklistValues` wire adapter is recordType-aware** — passing the master record type returns all values regardless of record-type restrictions, which is why a component tested on Master and shipped to a record-typed page shows different options. UNVERIFIED (2026-09-05): the literal master record type id `012000000000000AAA` is not stated in the Metadata API guide, the Object Reference, or the Apex guides; read it from `getRecordTypeInfosByName().get('Master')` rather than hard-coding it.

## Output Artifacts

| Artifact | Description |
|---|---|
| valueSettings metadata block | XML matrix for deployable dependency |
| API-side Validation Rule | Enforces matrix on API/DML writes |
| LWC dependent combobox | `getPicklistValues` + client-side filter map |
| RecordType `picklistValues` block | Record-type availability for every dependent value |
| Matrix worksheet | The signed-off table the XML, the rule, and the record types all derive from |

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing or reviewing the deployable XML — the matrix, a checkbox controller, a chain, record types, package.xml, deploy order, verification |
| `references/gotchas.md` | Ten platform behaviours that break dependent picklists, including the add-only deploy and the browser-only filter |
| `references/examples.md` | Building the LWC side, or writing the Apex test that proves the dependency is still wired |
| `references/well-architected.md` | Weighing the matrix against a validation rule, chain depth, or a shared global value set — and for the source list |
| `references/llm-anti-patterns.md` | Reviewing AI-generated dependency configuration or LWC combobox code |
| `templates/field-dependency-and-controlling-template.md` | Capturing the matrix, the answers to the questions above, and the deploy/verify record |
| `scripts/check_field_dependency_and_controlling.py` | Validating a manifest directory before deploy |

---

## Related Skills

- `admin/picklist-and-value-sets` — authoring the value sets themselves, global value sets, the `__gvs` suffix, and retiring values
- `admin/picklist-data-integrity` — cleaning up the rows a matrix-less period left behind
- `admin/record-types-and-page-layouts` — the record-type filter that intersects with the matrix
- `admin/custom-field-creation` — the rest of the `CustomField` element surface
- `admin/validation-rules` — the rule that enforces the matrix on every non-UI write path
- `lwc/lwc-wire-refresh-patterns` — `getPicklistValues` wire behaviour and re-wiring on controller change
