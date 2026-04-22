# LLM Anti-Patterns — Field Dependency and Controlling

Common mistakes AI coding assistants make with dependent picklists.

## Anti-Pattern 1: Assuming API enforces the dependency matrix

**What the LLM generates:** Code that inserts a record with a controlling + dependent value combo without validation, asserting "the dependency matrix prevents bad combinations."

**Why it happens:** Model conflates UI enforcement with API enforcement.

**Correct pattern:**

```
The dependency matrix is enforced by the Lightning UI only. Apex
DML, SOAP, REST, Bulk API, Data Loader all bypass it.

To guarantee data integrity, add a Validation Rule:

AND(
  ISPICKVAL(Parent__c, "Computers"),
  NOT(OR(
    ISPICKVAL(Category__c, "Laptops"),
    ISPICKVAL(Category__c, "Desktops")
  ))
)

Or a Before-Save flow, or @Trigger logic. Otherwise integrations
silently write invalid combinations.
```

**Detection hint:** Dependency configured with no accompanying Validation Rule or Before-Save automation, combined with any API-based write path.

---

## Anti-Pattern 2: Hardcoding the dependency matrix in LWC

**What the LLM generates:**

```javascript
const CATEGORIES = {
    Computers: ['Laptops', 'Desktops'],
    Phones: ['Android', 'iOS']
};
```

**Why it happens:** Model treats LWC like a greenfield web app.

**Correct pattern:**

```
Fetch from the platform so admin changes don't require a code
redeploy:

import { getPicklistValues } from 'lightning/uiObjectInfoApi';

@wire(getPicklistValues, {
    recordTypeId: '$recordTypeId',
    fieldApiName: CATEGORY_FIELD
})
wiredValues;

The wire returns { controllerValues, values[].validFor } which
encodes the matrix. Build the filter map from data, not code.

Hardcoding makes the LWC drift every time an admin edits the
picklist.
```

**Detection hint:** A constant object literal in LWC keyed by picklist-looking strings with arrays of strings as values.

---

## Anti-Pattern 3: Multi-select picklist as controlling field

**What the LLM generates:** Config instructions that set a multi-select picklist as the controlling field.

**Why it happens:** Model doesn't know the platform restriction.

**Correct pattern:**

```
Multi-select picklists CANNOT be controlling fields. Options:

1. Add a computed normal picklist that captures the primary value:
   Primary_Category__c (picklist) set by Before-Save flow =
   MID(Categories_Multi__c, 1, FIND(";", Categories_Multi__c) - 1)

2. Redesign: split the multi-select into checkboxes or a child
   object with a one-to-many relationship.

3. Use Flow logic in screen flow to filter dependent options
   manually.
```

**Detection hint:** Setup instructions or metadata XML naming a `MultiselectPicklist` field as `controllingField`.

---

## Anti-Pattern 4: Forgetting to enable new controlling values

**What the LLM generates:** Instructions that add a new value to the controlling picklist and "the dependent picklist will just work."

**Why it happens:** Model doesn't know enablement is per-cell.

**Correct pattern:**

```
Adding a new value to the controlling picklist makes it available,
but all dependent values are DISABLED for that new controlling value
until explicitly enabled.

Either:
- Setup → Field Dependencies → edit the matrix → click each dep value
  you want enabled under the new controlling value
- Or add valueSettings entries in metadata:

<valueSettings>
  <controllingFieldValue>NewValue</controllingFieldValue>
  <valueName>ExistingDepValue</valueName>
</valueSettings>

Deploy the updated dependent field XML together with the controlling
field XML.
```

**Detection hint:** A change request adding a picklist value without a matching valueSettings update on dependent fields.

---

## Anti-Pattern 5: Record Type filter forgotten

**What the LLM generates:** Configures a dependency matrix but leaves the Record Type's dependent-field picklist assignment at default.

**Why it happens:** Model treats Record Types and dependencies as independent layers.

**Correct pattern:**

```
Record Types filter picklist values BEFORE the dependency matrix
applies. If the Record Type excludes a dependent value, no amount
of controlling-field selection surfaces it.

Checklist when configuring a dependent picklist that also has
record types:
1. Assign all desired dependent values to the Record Type
2. Configure the matrix in Field Dependencies
3. Test in a record using each Record Type

A common "the dropdown is empty" bug is a Record Type assignment
missing the intended values.
```

**Detection hint:** Dependency matrix updated without a corresponding Record Type picklist-value assignment review.
