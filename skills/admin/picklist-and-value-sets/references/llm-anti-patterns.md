# LLM Anti-Patterns — Picklist and Value Sets

Common mistakes AI coding assistants make when generating or advising on Salesforce picklists and Global Value Sets.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Global Value Sets when values are object-specific

**What the LLM generates:** "Create a Global Value Set for your picklist so it is reusable across objects."

**Why it happens:** LLMs default to the "more advanced" option. Global Value Sets are appropriate when the exact same values are needed on multiple objects. If the values are unique to one object (e.g., Case Status values are specific to Case), a Global Value Set adds unnecessary coupling. Changing the GVS affects all objects that use it.

**Correct pattern:**

```
Decision guide:
- Same values on 2+ objects → Global Value Set.
  Example: Industry values used on Account AND Lead.
- Values unique to one object → Object-level picklist.
  Example: Case Status values only apply to Case.

Global Value Set risks:
- Adding/removing a value affects ALL fields using the GVS.
- You cannot have object-specific values within a GVS.
- Record type picklist filtering still works, but the base value
  set is shared.
```

**Detection hint:** If the output creates a Global Value Set for a picklist used on only one object, the GVS is unnecessary overhead. Check how many objects will use the value set.

---

## Anti-Pattern 2: Deleting picklist values instead of deactivating them

**What the LLM generates:** "Delete the old picklist value 'Legacy' from the picklist. It is no longer needed."

**Why it happens:** LLMs suggest deletion for cleanup. Deleting a picklist value removes it from the field definition, but existing records that had that value retain it as a text string. The value becomes unselectable but still appears on old records as an "inactive" value. Deactivating is the safer approach.

**Correct pattern:**

```
Deactivate vs Delete:
- Deactivate: value no longer appears in the picklist dropdown for new
  records, but existing records retain the value. Reports can still filter
  by the deactivated value. This is the safe approach.
- Delete: removes the value from the definition. Existing records keep
  the value as a text string, but it may cause issues with:
  - Validation rules that reference the value.
  - Flows or code that check for the value.
  - Report filters that depend on the value.
- Replace: use Setup → Replace Picklist Values to change existing records
  from the old value to a new value BEFORE deactivating.

Recommended workflow:
1. Replace existing data: old value → new value.
2. Deactivate the old value (do NOT delete).
3. Update validation rules, flows, and code that reference the old value.
```

**Detection hint:** If the output says "delete" a picklist value without mentioning deactivation or data replacement, existing records may be orphaned. Search for `deactivate` or `Replace Picklist Values` as alternatives to deletion.

---

## Anti-Pattern 3: Ignoring the controlling-dependent field type restrictions

**What the LLM generates:** "Set up a dependent picklist where the Record Type controls the Country picklist and Country controls the State picklist."

**Why it happens:** LLMs freely compose controlling-dependent chains. Salesforce has specific restrictions: the controlling field must be a picklist or checkbox. Standard fields can be controllers but not all standard fields support it. Multi-select picklists cannot be controlling fields. And dependency chains are limited to one level (A controls B, but B cannot control C in a native dependent picklist).

**Correct pattern:**

```
Controlling-dependent field restrictions:
- Controller can be: standard picklist, custom picklist, or checkbox.
- Controller CANNOT be: multi-select picklist, formula, text, or number.
- Dependent field can be: custom picklist or multi-select picklist.
- Chain depth: ONE level only (A → B). B cannot natively control C.
  For A → B → C, you need:
  - Dynamic Forms with visibility rules, or
  - A Screen Flow with conditional picklist population.
- Record Type acts as a built-in controller for picklist value filtering
  (separate from the controlling-dependent mechanism).
```

**Detection hint:** If the output chains dependent picklists beyond one level or uses a non-picklist field as a controller, the configuration will not work. Check the controlling field type and chain depth.

---

## Anti-Pattern 4: Not handling picklist value replacement in existing data records

**What the LLM generates:** "Rename the picklist value from 'In Progress' to 'Active'. The change will apply automatically."

**Why it happens:** LLMs assume renaming a picklist value updates existing records. Renaming the value's label changes what users see in the dropdown, but the API value (used by code, integrations, and stored data) may or may not change depending on whether you modify the API name. Existing records are NOT automatically updated unless you use the Replace function.

**Correct pattern:**

```
Picklist value renaming:
1. If you change only the LABEL (display name):
   - Existing records keep the old API value.
   - The dropdown shows the new label.
   - Reports and SOQL filter by API value, which did not change.
2. If you need to change the API VALUE:
   - You cannot directly rename API values.
   - Add the new value, use "Replace Picklist Values" to migrate data,
     then deactivate the old value.
3. After any value change:
   - Update validation rules, flows, and Apex code that reference
     the old API value.
   - Update reports with filters on the changed value.
   - Test integrations that read or write the picklist field.
```

**Detection hint:** If the output says renaming a picklist value "automatically updates" existing records, the data migration step is missing. Search for `Replace Picklist Values` or `data migration` in the renaming instructions.

---

## Anti-Pattern 5: Creating unrestricted picklists when restricted picklists are appropriate

**What the LLM generates:** "Create a picklist field for Status. Users and integrations can enter any value."

**Why it happens:** LLMs default to unrestricted picklists (the Salesforce default). Unrestricted picklists allow API and Data Loader to insert any string value, not just the defined picklist values. This creates data quality issues. Restricted picklists enforce that only defined values can be stored.

**Correct pattern:**

```
Restricted vs Unrestricted picklists:
- Restricted: only defined values can be stored (UI and API).
  API inserts/updates with invalid values are rejected.
  Recommended for: Status fields, Stage fields, any field where
  data quality is critical.
- Unrestricted (default): defined values appear in the dropdown,
  but API can insert any string value.
  May be acceptable for: low-criticality fields where integrations
  may send values not yet in the picklist.

To restrict a picklist:
  Setup → Object Manager → [Object] → Fields → [Field] → Edit.
  Check "Restrict picklist to the values defined in the value set."

Note: Global Value Sets are restricted by default.
```

**Detection hint:** If the output creates a picklist without mentioning the restricted vs unrestricted choice, the field may accept invalid API values. Search for `Restrict picklist` or `restricted` in the picklist configuration.
