# Gotchas — Picklist and Value Sets

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Deactivating a Global Value Set Entry Affects Every Field That Uses It

**What happens:** An admin wants to retire the picklist value "Beta" from the Case Status field. The Status field uses a Global Value Set shared with Opportunity and Account. The admin deactivates "Beta" from the Global Value Set. Immediately, "Beta" disappears from the selection dropdown on Opportunity and Account too — not just Cases. Users across the org can no longer select "Beta" on any object, even though the intent was Case-only.

**When it occurs:** Any time you manage values at the Global Value Set level (Setup → Picklist Value Sets → Edit). Deactivation, deletion, and value label changes all propagate instantly to every field referencing that GVS.

**How to avoid:** Before deactivating or deleting any value in a GVS, audit all objects and fields that reference it (you can do this via Salesforce setup — check each relevant object's picklist fields for "Global Value Set: [Name]"). If the value needs to be retired on only one object, the correct approach is to convert that specific field from GVS-backed to object-local (not possible once saved as GVS — you'd need a new field). Consider using object-local picklists for fields where value sets diverge by object over time.

---

## Gotcha 2: Dependent Picklist Dependencies Are Silently Bypassed by the API and Data Loader

**What happens:** An admin configures a controlling/dependent relationship between "Product Category" (controlling) and "Product Type" (dependent). The dependency works perfectly in the Lightning UI. A developer then writes a Flow that sets both fields using `{!record.Product_Category__c}` and a hardcoded `Product_Type__c` value. The Flow inserts records with any `Product_Type__c` value regardless of the controlling value — no error, no validation failure. The same applies to records imported via Data Loader or API.

**When it occurs:** Any time records are created or updated via Apex, Flow (without user interaction), Data Loader, REST API, Bulk API, or SOAP API. The controlling/dependent relationship is only enforced in the UI layer (record create/edit pages in Lightning and Classic). This is not an access-mode effect: the dependency matrix filters which values the picklist *offers*, it is never a save-time check, so it is bypassed identically whichever mode the write runs in. In particular, the Summer '26 (API 67.0) change that makes Apex SOQL/SOSL/DML default to **user mode** does not close this gap — user mode enforces sharing rules, FLS, and object permissions, none of which are picklist dependencies. Canonical table: [`agents/_shared/AGENT_CONTRACT.md`](../../../../agents/_shared/AGENT_CONTRACT.md) § *Apex security idiom by API version*.

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

**The same trap in metadata form.** `fullName` on a `CustomValue` is the stored key; `label` is display and "defaults to the API name" when omitted (api_meta.txt:47527–47528). Editing `fullName` in a `.globalValueSet-meta.xml` and redeploying is not a rename — the old `fullName` is now missing from the definition, and "if picklist values are missing from a component definition, they get deactivated when deployed" (api_meta.txt:47482–47483). You get a new value plus a deactivated old one, and every record still carries the old key. The Object Reference says which one anything programmatic reads: "Always use the value when inserting or updating a field. The `query()` call always returns the value, not the label" (object_reference.txt:2372–2374).

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

The Metadata API Developer Guide states the same rule for deployed values, which is why a green deploy is not evidence that anyone can pick the value: "When setting `standardValue` on Record Types, including person account record types, new picklist values loaded into your organization through the Metadata API don't display in the picklist UI by default. For users to see the new values, go to the Record Types list for the object containing the picklist field, click Edit, and add the new value to the Selected Fields list" (api_meta.txt:130774–130779). The record-type side of this is `admin/record-types-and-page-layouts`.

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

---

## Gotcha 8: The Literal Value `"None"` Is Not Blank

**What happens:** A picklist includes an API value `None` (sometimes the default). Reports, validation (`ISPICKVAL(Status, '')`), and Flow `ISBLANK` treat it as **populated**. Funnels that filter "Status not blank" include every "None." Silent defaults write `None` on create so required-looking fields never look empty.

**When it occurs:** Imported spreadsheets; "please pick None if N/A"; controlling-field placeholders.

**How to avoid:** Blank is the unset state. If you need an explicit N/A, name it `Not_Applicable` and teach reports the difference. Never default to `None`. Never use `None` as a sentinel in SOQL (`= 'None'`) when you meant `= null`.

---

## Gotcha 9: A Retrieve of an Unrestricted Local Picklist Silently Omits Its Inactive Values

**What happens:** An admin retrieves a custom picklist field to source control, edits one label, and deploys the file back. Every value that was inactive in the org before the retrieve is now… still inactive, but it has also vanished from the field definition, and any downstream org that receives this package never gets those values at all. Reports in the target org that filtered on a retired value return nothing, and a Replace job that was meant to move records off it has nothing to move them to.

**When it occurs:** Any retrieve of a picklist that is **both** non-global **and** unrestricted. The guide draws the line explicitly: "An API retrieve operation for global picklist values returns all active and inactive values in the picklist. But retrieving the values of a non-global, unrestricted picklist returns only the active values" (api_meta.txt:47521–47526). A global value set retrieves complete. A restricted local picklist is not covered by that sentence — **UNVERIFIED (2026-09-04):** the guide's asymmetry statement names only the non-global *unrestricted* case, and whether a restricted local picklist retrieves its inactive values was not confirmed against a live org.

**How to avoid:** Treat a retrieved unrestricted local picklist as a partial file, not a snapshot. Before deploying it anywhere, list the org's real value set with `getPicklistValues()` plus an inactive check, or promote the values to a global value set where retrieve is documented to be complete. Never diff two orgs' unrestricted local picklists and conclude the shorter one is missing values.

---

## Gotcha 10: Deploying a Value Set File Deactivates Every Value It Does Not Mention

**What happens:** An engineer needs to add one stage to `OpportunityStage`. They write a small `standardValueSet-meta.xml` containing just the new stage — the smallest possible change — and deploy. The deploy succeeds. Every other stage in the org is now inactive. Open pipeline reports empty out; the stage picklist offers exactly one choice.

**When it occurs:** Every deploy of `GlobalValueSet`, `StandardValueSet`, or a `CustomField` with a `valueSetDefinition`. The rule is stated twice in the guide: "If picklist values are missing from a component definition, they get deactivated when deployed. Deactivation occurs for picklist values of both standard and custom fields" (api_meta.txt:47482–47483), and again under `CustomValue` as the documented *mechanism* for deactivating — "invoke an `update()` call on … GlobalValueSet … with the value omitted, or with the value's `isActive` field set to false" (api_meta.txt:47478–47480). Omission is not "no opinion"; omission is the deactivate instruction.

**How to avoid:** Never author one of these files. `sf project retrieve start` the existing set first, add your value to the retrieved file, deploy the whole file. Where the retrieve itself is lossy (Gotcha 9), reconcile against `getPicklistValues()` before deploying. Deactivate deliberately with `<isActive>false</isActive>`, which leaves the value in the file and in the diff, rather than by deletion from the file, which leaves no trace of what you turned off.

---

## Gotcha 11: `StandardValueSet` Takes No Wildcard, and Four Standard Sets Are Partly or Wholly Off-Limits

**What happens:** A team builds a "retrieve the whole org" manifest with `<members>*</members>` for every type. `GlobalValueSet` comes back. `StandardValueSet` comes back empty — no error, no warning, just no standard picklists in the repo. Six months later a sandbox refresh loses every customised Case Status and Lead Status because they were never in source control.

**When it occurs:** Any manifest that relies on the wildcard for standard picklists. The two types are documented in opposite directions: `GlobalValueSet` "supports the wildcard character `*` (asterisk) in the package.xml manifest file" (api_meta.txt:79424–79426); `StandardValueSet` "doesn't support the wildcard character `*` (asterisk)" (api_meta.txt:130826–130828). Every standard value set must be named, using the Appendix C name rather than the field name — `Opportunity.StageName` is `OpportunityStage`, `Case.Status` is `CaseStatus` (api_meta.txt:142674, 141982) — and "the names of standard value sets and picklist fields are case-sensitive" (api_meta.txt:141686).

**How to avoid:** Enumerate the standard value sets your org actually customises and pin them in `package.xml` by name. Then check them against Appendix C's footnotes before promising a deploy will work: footnote 2 marks sets where "you can only update the label … You can't insert or delete picklist values" (api_meta.txt:143150) — `ForecastingItemCategory`, `RoleInTerritory`; footnote 3 marks sets where "you can't read or update this standard value set or picklist field" (api_meta.txt:143152) — `IdeaCategory`, `QuestionOrigin`. A footnote-3 member in a manifest is a retrieve that comes back empty and a deploy that changes nothing.

---

## Gotcha 12: An Opportunity Stage Deploys Fine Without a Forecast Category and Breaks Forecasting

**What happens:** A new stage `Legal Review` is added to `OpportunityStage` with a label and nothing else. The deploy is green and the stage appears in the picklist. Reps start using it. The forecast does not move: opportunities in `Legal Review` are not counted in Pipeline, Best Case, or Commit, and Amount-weighted pipeline reports show them at 0%.

**When it occurs:** Whenever a stage is created without both `forecastCategory` and `probability`. Both are documented as "only relevant for the standard Stage field in opportunities" and neither is required by the schema (api_meta.txt:47578–47586, 47593–47596), so nothing in the deploy pipeline objects. `forecastCategory` is a closed enum with exactly five members — `Omitted`, `Pipeline`, `BestCase`, `Forecast`, `Closed` (api_meta.txt:47581–47585) — so a plausible-looking value such as `Commit` or `Closed Won` fails the deploy, while simply omitting the element does not.

**How to avoid:** Every `standardValue` on `OpportunityStage` carries `forecastCategory`, `probability`, `won` and `closed` explicitly, as in `references/metadata-examples.md` §3. `scripts/check_picklist_and_value_sets.py` treats a stage missing `probability` or `forecastCategory` as an ERROR for exactly this reason. Note the trap in the mapping: `Closed Lost` belongs in `Omitted`, not in `Closed` — `Closed` is the bucket for booked revenue. The stage design itself is `/design-sales-stages`.

---

## Gotcha 13: Dependency Matrix Entries Added Through the Metadata API Cannot Be Removed Through It

**What happens:** A dependent picklist's matrix was deployed with `Prius` available under both `Toyota` and `Honda` — a copy-paste error. The engineer deletes the wrong `valueSettings` element, redeploys, and the deploy succeeds. `Prius` is still offered under `Honda`. Repeating the deploy, forcing a full deploy, and deleting the whole `valueSettings` block all change nothing.

**When it occurs:** Any attempt to narrow an existing dependency matrix via metadata. The `ValueSettings` documentation states the asymmetry twice in one sentence: "A list of values in the controlling or parent picklist (that the custom picklist values depend on). **You can add field dependency values via the Metadata API but not remove them**" (api_meta.txt:45873–45875, repeated at 45855–45860). Combined with Gotcha 10 this is genuinely one-directional: omitting a picklist *value* deactivates it, but omitting a *dependency mapping* does nothing.

**How to avoid:** Get the matrix right before the first deploy — a wrong mapping is a Setup task to undo, not a revert. Where a mapping must be removed, do it in Setup (Object Manager → field → Field Dependencies → Edit), then re-retrieve so source control matches the org. Design the matrix in `admin/field-dependency-and-controlling` before writing any `valueSettings`.

---

## Gotcha 14: Global Value Sets Created in API 57.0+ Carry a `__gvs` Suffix You Must Type Everywhere

**What happens:** An admin creates a value set in Setup and names it `Renewal Risk Band`. An engineer writes `<members>Renewal_Risk_Band</members>` in `package.xml` and `<valueSetName>Renewal Risk Band</valueSetName>` on the field. The retrieve returns nothing for that member and the field deploy fails on an unresolvable value set — while the set is plainly visible in Setup.

**When it occurs:** Any org where the set was created recently. "Any global value set created in API version 57.0 or later automatically has the `__gvs` suffix appended to the developer name. When you make any CRUD-based call with the GlobalValueSet type, you must append the suffix to the `fullName` field when you reference the type" (api_meta.txt:79419–79421). Older sets in the same org do not have it, so two value sets side by side in Setup need different strings in metadata. Compounding it, three names are in play for one set: the Setup label, the `masterLabel` inside the file ("a global value set's name … Appears as Label in the user interface", api_meta.txt:79371–79373), and the developer name in the file name and manifest.

**How to avoid:** Never type a global value set name from what Setup displays. Retrieve with the wildcard — `sf project retrieve start --metadata "GlobalValueSet" --target-org <org>` — and read the developer name off the file names that land in `globalValueSets/`. Use that exact string in `package.xml` and in the field's `valueSetName`.
