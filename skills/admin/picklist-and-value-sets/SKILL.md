---
name: picklist-and-value-sets
description: "Use when creating or managing picklist fields: choosing between Global Value Sets and object-local picklists, configuring controlling and dependent field relationships, managing picklist values, and replacing values in existing data records. NOT for formula fields that reference picklists (use formula-fields), NOT for record type picklist filtering (use record-types-and-page-layouts), NOT for picklist fields in Flow (use the appropriate flow skill)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
tags:
  - picklist
  - global-value-set
  - dependent-picklist
  - controlling-field
  - picklist-values
triggers:
  - "how do I create a global picklist value set that multiple objects share"
  - "my picklist is showing wrong values or old values I retired"
  - "how do I set up a dependent picklist where one field controls another"
  - "I need to replace an old picklist value with a new one across all existing records"
  - "what is the difference between a global value set and an object-local picklist"
  - "how do I deactivate a picklist value without losing historical data"
  - "users can still see deactivated picklist values on old records"
inputs:
  - "Object and field names for the picklist field(s) involved"
  - "Whether values need to be shared across multiple objects or are object-specific"
  - "Whether a controlling/dependent relationship is needed and which field is the controller"
  - "List of values to add, retire, replace, or reorder"
outputs:
  - "Decision recommendation: Global Value Set vs object-local picklist"
  - "Step-by-step configuration guide for the picklist or dependent picklist relationship"
  - "Data replacement plan for existing records when renaming/retiring values"
  - "Picklist design document using the provided template"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-03
---

# Picklist and Value Sets

Use this skill when an admin needs to create, configure, or manage picklist fields in a Salesforce org — including the decision between Global Value Sets and object-local picklists, setting up controlling and dependent relationships, and replacing stale values in data records.

---

## Before Starting

Gather this context before working on anything in this area:

- **Where is the field used?** Is the same set of values needed on more than one object? If yes, a Global Value Set is appropriate.
- **Is there a controlling/dependent requirement?** Which field controls which? Is the controlling field a standard picklist, custom picklist, or checkbox?
- **How many existing records carry the old value?** Mass replacement via Setup creates a background job — plan for data volume.
- **Are there dependent flows, validation rules, or Apex logic** that check specific picklist values by string? These must be updated when renaming or retiring values.

---

## Core Concepts

### Global Value Sets vs Object-Local Picklists

A **Global Value Set** (metadata type `GlobalValueSet`) is a shared library of picklist values managed centrally under Setup > Picklist Value Sets. Multiple custom picklist fields across multiple objects can reference the same Global Value Set, so adding a value in one place adds it everywhere.

An **object-local picklist** is a value set defined within a single custom field. Its values are independent; changing them does not affect any other field.

**Standard picklist fields** (e.g. `Lead.LeadSource`, `Opportunity.StageName`) have their own built-in value management under Setup > Object Manager and cannot be converted to Global Value Sets. However, standard picklists CAN act as controlling fields for dependent custom picklists.

**Key behavioral differences:**

| Behavior | Global Value Set | Object-Local Picklist |
|---|---|---|
| Value scope | All fields sharing the GVS | This field only |
| Add/remove values | At GVS level; affects all fields | At field level; isolated |
| Deactivate a value | Deactivates on all fields using GVS | Deactivates on this field only |
| Promote to GVS later | Not possible once field is saved as local | Can promote via UI (one-time, irreversible) |
| Metadata type | `GlobalValueSet` | `CustomField` value set |

**Limits:**
- Standard and custom picklists: up to **1,000 total values** (active + inactive combined); each value label has a max of **255 characters**; total characters across all values in a field is capped at **15,000**
- Multi-select picklists: **150 active values** by default (raisable via Salesforce Support); maximum **100 values selected simultaneously** on a single record
- Global Value Sets: max **500 Global Value Sets per org**; same 1,000 value limit applies per GVS; GVS fields are **always restricted** (API writes of arbitrary text fail with `INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST`)

### Controlling and Dependent Picklists

A **controlling field** determines which values are available in a **dependent picklist**. The user selects a value in the controlling field, and the dependent field automatically filters its available values to the mapped subset.

**Supported controlling field types:**
- Standard picklist fields (e.g. `LeadSource`, `Type`)
- Custom picklist fields (standard or global-value-set backed)
- Checkbox fields (controls a dependent picklist with two branches: checked/unchecked)

**Not supported as controlling fields:**
- Multi-select picklists cannot be controlling fields
- Formula fields, lookup fields, text fields — not supported
- Certain Activity standard fields (Call Type, Subject, Task Type) cannot be controlling fields

**Supported dependent field types:**
- Custom picklist fields (object-local value set)
- Custom multi-select picklist fields

**Not supported as dependent fields:**
- Standard picklist fields — standard picklists cannot be on the dependent side
- Fields backed by a Global Value Set — GVS-backed fields can be **controlling** but **cannot be dependent**

**Dependency enforcement:** Filtering is enforced in the Salesforce Lightning UI and Classic UI when a user creates or edits a record. **Dependencies are NOT enforced via API, Data Loader, or record import.** Records loaded through the API can have any value regardless of the dependency configuration. This is a known platform behavior, not a bug.

**Configuration steps:**
1. Setup > Object Manager > [Object] > Fields & Relationships
2. Click on the dependent field → Field Dependencies → Edit
3. For each controlling value column, check the boxes for the dependent values that should be available
4. Save — dependency is active immediately; no deployment needed in same org

**Limit:** A controlling picklist field may have at most **300 values**. If a picklist exceeds 300 values it cannot be used as a controlling field. This limit can be raised via Salesforce Support. Large dependency matrices are difficult to maintain in the UI — prefer simpler value sets for controlling fields.

**Zero-mapping gotcha:** If no dependent values are checked for a given controlling value in the matrix, the dependent picklist shows **all** available values when that controlling value is selected — not zero values. This is the opposite of what most admins expect. Always confirm every controlling value has at least one mapped dependent value.

### Picklist Value Management (Add, Retire, Replace)

**Adding a value:**
- Object Manager > [Object] > [Field] > Edit > Add picklist values
- Or for a Global Value Set: Setup > Picklist Value Sets > [GVS Name] > Edit

**Deactivating (retiring) a value:**
- Deactivated values remain on existing records and appear in reports — they just cannot be selected on new or edited records
- Records carrying a deactivated value still display it (labeled as inactive in some views)
- For Global Value Sets: deactivation applies across **all** fields sharing that GVS

**Replacing values in existing data (mass update):**
- Setup > Object Manager > [Object] > Fields & Relationships > [Field] > **Replace**
- Choose the old value and the replacement value (or blank to clear)
- Salesforce creates a background job to update all records — completion time scales with record volume
- You can replace with a blank/null value (effectively clearing the field on old records)
- **This does not apply to records in the Recycle Bin** — deleted records retain their original value
- After replacement, the old value remains in the field's value list as inactive unless you explicitly deactivate or delete it

### Global Value Set: Promote an Existing Field

If a custom picklist field was created as object-local and you later decide the values should be shared, you can **promote** it to a Global Value Set:
- Object Manager > [Object] > [Field] > Edit → there is a "Promote to Global Value Set" option if the field is custom
- This is **one-way and irreversible** — once promoted, the field's values are managed at the GVS level
- The values are not duplicated — existing values become the initial GVS values
- All other fields wanting to share these values must be created or modified to reference the new GVS

---

## Common Patterns

### Pattern 1: Shared Industry/Region Values Across Multiple Objects

**When to use:** You have a "Region" picklist needed on Account, Opportunity, and Contact. Values must stay in sync — adding a new region should appear everywhere.

**How it works:**
1. Setup > Picklist Value Sets > New → create `Region__gvs` with all region values
2. Create each field as Type = Picklist → in the value set section, select "Use Global Value Set" → choose `Region__gvs`
3. To add a new region: Setup > Picklist Value Sets > `Region__gvs` > Add value — it immediately appears on all three fields

**Why not object-local:** Managing separate value lists on three fields guarantees drift — one admin adds "Pacific Northwest" to Account but forgets Contact, causing report inconsistencies.

### Pattern 2: Controlling Picklist — Product Category → Product Type

**When to use:** A "Product Category" picklist should filter the available "Product Type" values so that selecting "Hardware" shows only hardware types, not software types.

**How it works:**
1. Create `Product_Category__c` (picklist) and `Product_Type__c` (picklist) on the object
2. Add all category values to `Product_Category__c`
3. Add all type values to `Product_Type__c`
4. Object Manager > [Field] `Product_Type__c` > Field Dependencies > Edit
5. In the matrix, for each `Product_Category__c` column, check the applicable `Product_Type__c` rows
6. Save — filtering is live on the UI

**Important:** On the field dependency matrix, the "Include Values" button selects all values for a column; use it to start from "all" and deselect the few that don't apply, rather than checking hundreds of boxes manually.

### Pattern 3: Retiring a Value Without Losing Historical Reporting

**When to use:** A picklist value is no longer valid (e.g. a product line was discontinued) but historical records must still show the value in reports.

**How it works:**
1. Do NOT delete the value — deleting replaces it with null on all records
2. Instead: Object Manager > [Field] > Edit → find the value → **Deactivate** it
3. Existing records retain the value and it appears in reports; it is simply hidden from the selection UI for new/edited records
4. If you want to rebrand the value (e.g. "Widget v1" → "Widget (Legacy)"), use **Replace** first to bulk-update all records, then deactivate the old label

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Same values needed on 2+ objects | Global Value Set | Single source of truth; avoids value drift |
| Values are unique to one object/field | Object-local picklist | Simpler; no unintended cross-object impact |
| Field already exists as object-local, now needs sharing | Promote to GVS (one-time) | Preserves existing values; consolidates management |
| Retiring a picklist value, keep history | Deactivate the value | Records keep value; UI hides from selection |
| Retiring a value, clean up old data too | Replace then Deactivate | Bulk-update records first, then deactivate |
| Need one field to filter another field's options | Controlling + Dependent picklist | Built-in platform feature; no Apex needed |
| Values differ between orgs/sandboxes | Object-local or GVS with changeset | GVS is metadata and deploys via Changesets/SFDX |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking picklist work complete:

- [ ] Global Value Set chosen for any value set used on 2+ fields/objects
- [ ] All values entered correctly (label matches API value intent; no trailing spaces)
- [ ] Inactive/deleted values checked — no data cleanup gap (use Replace if needed)
- [ ] For dependent picklists: dependency matrix is complete and tested in UI
- [ ] Downstream impacts verified: validation rules, flows, Apex (ISPICKVAL), reports, dashboards
- [ ] If Global Value Set: confirm deactivation of a value won't break other objects unexpectedly
- [ ] Replace job completed and verified on sample records before marking work done
- [ ] Field-Level Security (FLS) confirmed on new fields for all relevant profiles/permission sets

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Deactivating a GVS value deactivates it everywhere** — When you deactivate a value in a Global Value Set, it is hidden from the selection UI on every field that references that GVS, across all objects. There is no per-field deactivation for GVS values. Admins who expect to deactivate "On Hold" only on Cases — without affecting Opportunities that also use the same GVS — will be surprised.

2. **Dependent picklist dependencies are not enforced via API** — Data Loader, REST API, SOAP API, Bulk API, and Flow (when running in system context without UI interaction) all bypass the controlling/dependent relationship. Records can have any value regardless of the controlling field value. This means data imports and programmatic inserts can violate the intended dependency silently. Only the Lightning and Classic UIs enforce the filter.

3. **Deleting a picklist value replaces it with null on all records** — When you choose to delete (not deactivate) a picklist value, Salesforce immediately sets the field to null/blank on every record that had that value. This cannot be undone. Always use Deactivate or Replace first unless you intentionally want to blank out all records. For large orgs, even a Deactivate before Delete does not give you a rollback window.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Picklist Design Document | Filled template documenting value set choices, GVS vs local decision, dependent picklist matrix, and replacement plan |
| Data Replacement Job Plan | List of Replace jobs to run, their order, and verification steps |

---

## Related Skills

- `custom-field-creation` — use when the field itself needs to be created (type selection, FLS, layout); this skill handles picklist-specific design and value management
- `record-types-and-page-layouts` — use when record type determines which picklist values a user sees (per-record-type picklist value filtering is configured on the Record Type, not the field dependency)
- `formula-fields` — use when a field's value is computed from a picklist using `ISPICKVAL()` or `TEXT()`
