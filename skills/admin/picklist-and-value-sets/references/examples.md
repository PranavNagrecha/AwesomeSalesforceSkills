# Examples — Picklist and Value Sets

## Example 1: Replacing a Renamed Product Line Value Across 12,000 Records

**Context:** A SaaS company rebranded their product lines. The Opportunity "Product Line" picklist has the value "Platform Basic" on 12,000 Opportunity records. The value needs to become "Core" to align with the new brand.

**Problem:** An admin manually edits the field and changes the label from "Platform Basic" to "Core" in the picklist value list. The UI lets you rename the label — but renaming a picklist label **does not update the API value stored on records**. The stored value remains the old internal key. Reports using SOQL filters or formula `ISPICKVAL(Product_Line__c, 'Platform Basic')` still match. However, the admin believes the rename fixed everything and no Replace job is run.

**Solution:**

1. First, add "Core" as a **new** picklist value (do not rename the old one yet)
2. Setup → Object Manager → Opportunity → Fields & Relationships → Product_Line__c → **Replace**
3. Select old value: "Platform Basic" → new value: "Core" → Replace
4. Wait for the background job to complete (verify via Setup → Apex Jobs or the replace confirmation page)
5. Spot-check 5–10 records to confirm the field now shows "Core"
6. Once all records are updated, **deactivate** "Platform Basic" (do not delete — deletion is irreversible)
7. Update any flows, validation rules, or Apex that reference `'Platform Basic'` by string

**Why it works:** The Replace job updates the stored value in the database. Simply renaming the label in the picklist edit screen changes only the display label, not the stored API value. Flows, Apex (`ISPICKVAL`), and SOQL string literals match against the stored value — so only a Replace job plus downstream code updates makes the change complete.

---

## Example 2: Setting Up Region as a Shared Global Value Set

**Context:** A B2B org has "Region" as a picklist on Account, Opportunity, and Lead. Until now each object had its own field with locally managed values. When someone added "APAC - India" to the Account picklist, they forgot to add it to Lead and Opportunity. Reports that join across objects now show mismatched region values.

**Problem:** Three separate object-local picklists drift out of sync. Adding a value to one field requires manually repeating the step for every other field. No process enforces consistency.

**Solution:**

1. Setup → Picklist Value Sets → New → Name: "Region" → API Name: `Region` → add all current region values
2. For each of the three existing region fields on Account, Opportunity, Lead:
   - Object Manager → [Object] → Fields & Relationships → [Region field] → Edit
   - Salesforce shows a "Promote to Global Value Set" option if the field is custom — click it and select the `Region` GVS
   - OR: if the field's current values differ from the GVS, create a new field pointing to the GVS and run a Replace on the old field to map values, then retire the old field
3. Verify: Adding a new value to Setup → Picklist Value Sets → Region instantly makes it available on all three objects

**Why it works:** The Global Value Set is a single metadata record. All fields pointing to it read their value list from one source. Admins manage values in one place; all objects stay synchronized automatically.

---

## Example 3: Controlling Picklist — Country Filters State/Province

**Context:** An org collects Billing Country and Billing State as custom picklist fields on Account. Without a dependency, users pick "France" as country and then "Texas" as state — which is invalid.

**Problem:** No validation rule exists to catch the mismatch. Data quality degrades because users can combine any country with any state.

**Solution:**

1. Create `Billing_Country__c` with all country values
2. Create `Billing_State__c` with all state/province values across all countries
3. Object Manager → Account → `Billing_State__c` → Field Dependencies → Edit
4. For each country column in the dependency matrix, check only the states that belong to that country
5. Use the "Include Values" button on each column to start with all selected, then uncheck non-applicable states — faster than checking individually for countries with many states
6. Save and test: select "France" as country → only French regions appear in the state field

**Note:** Load test via Data Loader with mismatched combinations — they will import without error, confirming that API enforcement is not provided. Add a Validation Rule as a supplementary check if data quality via API matters:
```
AND(
  NOT(ISBLANK(Billing_State__c)),
  Billing_Country__c = 'France',
  NOT(ISPICKVAL(Billing_State__c, 'Île-de-France')),
  NOT(ISPICKVAL(Billing_State__c, 'Provence-Alpes-Côte d\'Azur'))
  /* ... other valid French regions */
)
```
**Why it works:** The dependency matrix provides UI-level enforcement — most users follow it. The supplementary validation rule catches API-level violations for data integrity. Both layers together achieve reliable data quality.

---

## Anti-Pattern: Deleting Picklist Values to "Clean Up" an Old Org

**What practitioners do:** An admin inherits an org with 40 stale picklist values that haven't been used in years. To clean up, they delete all 40 values from the field. The UI asks for confirmation and the admin clicks through quickly.

**What goes wrong:** Deleting a picklist value immediately sets the field to null/blank on every record that had that value. There is no undo, no recycle bin for this operation. 8,000 Opportunity records that had stage "Approved - Legacy" now have a blank Stage field. Pipeline reports show gaps. Automated processes that required a Stage value to trigger break.

**Correct approach:**
1. Run a report to count how many records have each value before taking action
2. For values with records: use **Replace** to move records to an appropriate active value, OR **Deactivate** to preserve the value on records while hiding it from the UI
3. Only **Delete** a value after confirming zero records carry it (report count = 0)
4. When cleaning up Global Value Sets, confirm impact across ALL objects sharing the GVS before deactivating any value
