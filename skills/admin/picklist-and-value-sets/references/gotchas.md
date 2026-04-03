# Gotchas — Picklist and Value Sets

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Deactivating a Global Value Set Entry Affects Every Field That Uses It

**What happens:** An admin wants to retire the picklist value "Beta" from the Case Status field. The Status field uses a Global Value Set shared with Opportunity and Account. The admin deactivates "Beta" from the Global Value Set. Immediately, "Beta" disappears from the selection dropdown on Opportunity and Account too — not just Cases. Users across the org can no longer select "Beta" on any object, even though the intent was Case-only.

**When it occurs:** Any time you manage values at the Global Value Set level (Setup → Picklist Value Sets → Edit). Deactivation, deletion, and value label changes all propagate instantly to every field referencing that GVS.

**How to avoid:** Before deactivating or deleting any value in a GVS, audit all objects and fields that reference it (you can do this via Salesforce setup — check each relevant object's picklist fields for "Global Value Set: [Name]"). If the value needs to be retired on only one object, the correct approach is to convert that specific field from GVS-backed to object-local (not possible once saved as GVS — you'd need a new field). Consider using object-local picklists for fields where value sets diverge by object over time.

---

## Gotcha 2: Dependent Picklist Dependencies Are Silently Bypassed by the API and Data Loader

**What happens:** An admin configures a controlling/dependent relationship between "Product Category" (controlling) and "Product Type" (dependent). The dependency works perfectly in the Lightning UI. A developer then writes a Flow that sets both fields using `{!record.Product_Category__c}` and a hardcoded `Product_Type__c` value. The Flow runs in system context and inserts records with any `Product_Type__c` value regardless of the controlling value — no error, no validation failure. The same applies to records imported via Data Loader or API.

**When it occurs:** Any time records are created or updated via Apex, Flow (without user interaction), Data Loader, REST API, Bulk API, or SOAP API. The controlling/dependent relationship is only enforced in the UI layer (record create/edit pages in Lightning and Classic).

**How to avoid:** If data integrity matters for dependent picklist combinations, add a **Validation Rule** that checks the combination in addition to the field dependency. For example:
```
AND(
  ISPICKVAL(Product_Category__c, 'Hardware'),
  NOT(OR(
    ISPICKVAL(Product_Type__c, 'Server'),
    ISPICKVAL(Product_Type__c, 'Laptop'),
    ISPICKVAL(Product_Type__c, 'Monitor')
  ))
)
```
Validation rules run on all save operations including API inserts, providing the enforcement layer the dependency matrix lacks.

---

## Gotcha 3: Renaming a Picklist Value Label Does Not Update Stored Data

**What happens:** An admin renames the picklist value "Tier 1" to "Gold" by editing the label in the field definition. The UI accepts the change instantly. The admin assumes all records now show "Gold". But when a developer queries records using `WHERE Support_Tier__c = 'Gold'`, no records are returned. Old records still store the internal value as "Tier 1". Reports built with filter "Support Tier = Gold" show zero results. Flows checking `{!record.Support_Tier__c} == 'Gold'` never fire.

**When it occurs:** When any admin renames a picklist value's label in Setup → Object Manager → [Field] → Edit → change the label text. Salesforce picklist values have two components: the stored API value (the key written to records) and the display label. The UI renames only the label, not the stored value. Existing records are not updated.

**How to avoid:** To rename a value in a way that also updates all existing records:
1. Add the new value as a new entry (e.g. "Gold")
2. Use the **Replace** function (Object Manager → [Field] → Replace) to bulk-update all records from "Tier 1" to "Gold"
3. After the Replace job completes and is verified, deactivate "Tier 1"
4. Update all downstream references (validation rules, flows, Apex, SOQL) from 'Tier 1' to 'Gold'

Note: For new fields where no records exist yet, renaming labels before any data is entered is safe and does not require a Replace job.

---

## Gotcha 4: Deleting a Picklist Value Immediately Nulls All Records With That Value — No Undo

**What happens:** An admin deletes a picklist value (not deactivates — deletes). Salesforce prompts "Replace the deleted value with [blank]?" and the admin clicks OK. Within seconds, every record that had that value now has a blank/null field. There is no recycle bin, no undo, no background job to cancel. The change is immediate and permanent in the database.

**When it occurs:** Choosing "Delete" from the picklist value action menu in the field edit UI, or deleting a value from a Global Value Set.

**How to avoid:** Default to **Deactivate** for any value that might be on existing records. Only use Delete after running a report confirming zero records carry that value. If a mass cleanup is needed, use Replace to move records to a new value first, then confirm the count is zero, then delete.

---

## Gotcha 5: Adding a New Value Does Not Automatically Add It to Existing Record Types

**What happens:** An admin adds a new value "Strategic" to the Account Rating picklist. Users immediately report that "Strategic" is not appearing in the dropdown when creating or editing Account records. The admin confirms the value is active in the field definition. The cause: every existing record type has its own "Picklists Available for Editing" configuration that is a manually curated subset of the master value list. New master values are **not automatically added** to any existing record type's available set.

**When it occurs:** Every time a new value is added to a picklist field (or GVS) that is used by records with a record type. The only exception is when a brand new record type is created fresh — it receives all current master values by default.

**How to avoid:** After adding any new picklist value, go to Setup → Object Manager → [Object] → Record Types → for each record type → Picklists Available for Editing → find the field → edit → add the new value. If the org has many record types, this step is easy to miss. Establish a checklist: "after adding picklist value X, update record types: [list them]."

---

## Gotcha 6: GVS-Backed Fields Cannot Be Dependent Fields

**What happens:** An admin creates a "Region" Global Value Set shared across Account and Opportunity. They then try to configure a dependency where "Country" (local picklist) controls "Region" (GVS-backed). The Field Dependencies configuration does not show "Region" as an available dependent field. There is no error message — "Region" simply doesn't appear in the dependent field list.

**When it occurs:** Any attempt to make a GVS-backed picklist field the dependent side of a controlling/dependent relationship. GVS-backed fields can only be the **controlling** side.

**How to avoid:** If you need Region to be a dependent field, it must be an object-local picklist (not GVS-backed). If Region values need to stay in sync across objects AND it needs to be a dependent field somewhere, you need separate object-local fields for the dependency use case. This is an architectural constraint to identify during field design — changing a field from GVS-backed to object-local requires deleting and recreating the field.

---

## Gotcha 7: Multi-Select Picklist Values Are Stored as Semicolon-Delimited Strings

**What happens:** An admin creates a multi-select picklist "Interests" with values Red, Blue, Green. A user selects Red and Blue. The stored value is `"Red;Blue"`. A developer writes a Validation Rule `ISPICKVAL(Interests__c, 'Red')` expecting to detect if Red is selected — but this returns false because ISPICKVAL() does exact-match comparison and the stored string is `"Red;Blue"`, not `"Red"`.

**When it occurs:** Any SOQL WHERE clause, validation rule, or formula that uses exact string matching on a multi-select picklist field.

**How to avoid:** For multi-select picklists:
- In SOQL: use `INCLUDES('Red')` operator rather than `= 'Red'`
- In Validation Rules and formulas: use `INCLUDES(Interests__c, 'Red')` instead of `ISPICKVAL(Interests__c, 'Red')`
- In Apex: use `String.valueOf(record.Interests__c).contains('Red')` carefully, or better, split on `;` and check the list
- Avoid multi-select picklists in reporting group-by clauses — each combination of selected values becomes its own bucket, making reports very hard to aggregate
