# Examples — Global Search Configuration

Concrete configurations and audit traces. Each example assumes the admin has the **Customize Application** permission (UNVERIFIED (2026-10-20): that search-layout editing requires it; synonyms need "Manage Synonyms", api_meta 264 L136378) and is operating against a sandbox before promoting to production.

---

## Example 1: Refresh Account Search Layouts for a Lightning Rollout

**Context:** A 4,000-user manufacturing org just migrated from Classic to Lightning. Sales users complain that global search results for Accounts show only the Account Name column. Reps are clicking into each result to disambiguate.

**Problem:** The org's `Account` `searchResultsAdditionalFields` list was empty, so search results rendered the mandatory Name column only (api_meta 264 L47509). Metadata API holds one default search-results list per object plus per-profile `profileSearchLayouts` overrides (L47265-47266) — not separate Lightning and Classic lists.

**Solution:**

1. Audit current state via Metadata API:
   ```bash
   sf project retrieve start --metadata "CustomObject:Account" --target-org sandbox
   ```
   Open `force-app/main/default/objects/Account/Account.object-meta.xml` and locate the `<searchLayouts>` block.
2. Add repeated `searchResultsAdditionalFields` entries (one field per element; Name is implicit and "isn't returned" in the list, L47509-47510). Standard-field tokens below are copied from the guide's own sample (L47299-47312); custom fields use their API names (L47514-47515):
   ```xml
   <CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
       <!-- excerpt: only the searchLayouts block of Account.object-meta.xml -->
       <searchLayouts>
           <searchResultsAdditionalFields>ACCOUNT.SITE</searchResultsAdditionalFields>
           <searchResultsAdditionalFields>ACCOUNT.PHONE1</searchResultsAdditionalFields>
           <searchResultsAdditionalFields>ACCOUNT.ADDRESS2_CITY</searchResultsAdditionalFields>
           <searchResultsAdditionalFields>CORE.USERS.ALIAS</searchResultsAdditionalFields>
           <searchResultsAdditionalFields>Region__c</searchResultsAdditionalFields>
       </searchLayouts>
   </CustomObject>
   ```
   In the Object Manager UI, the equivalent path is: `Setup → Object Manager → Account → Search Layouts → Default Layout → Edit → move the fields from Available to Selected` (UNVERIFIED (2026-10-20): Setup UI path).
3. Deploy:
   ```bash
   sf project deploy start --metadata "CustomObject:Account" --target-org sandbox
   ```
4. Validate: log in as a sales user (not a System Administrator — admin profiles have broad FLS that may mask FLS issues), run a global search for an account name, confirm Name plus the 5 columns render with values. Check whether the user's profile has its own `profileSearchLayouts` entry, which wins over the default.
5. Promote to production via change set or pipeline.

**Why it works:** `searchResultsAdditionalFields` is the default search results layout for every profile without its own entry (L47265-47266); populating it gives users a useful 6-column result row.

---

## Example 2: Add a Custom Synonym Group for Account Tier Vocabulary

**Context:** A B2B sales team uses the words "VIP", "Strategic", and "Priority" interchangeably to refer to top-tier accounts. The Account name fields contain a mix — some are "VIP Industries Ltd", some are "Priority Manufacturing Co." Reps search for "Priority" and miss VIP accounts (and vice versa).

**Problem:** Account names are not normalized; renaming records is out of scope (legal contracts reference the existing names). Global search needs to treat the four terms as equivalents at the search layer.

**Solution:**

1. Navigate to `Setup → User Interface → Synonyms → New Synonym Group` (UNVERIFIED (2026-10-20): Setup path; the metadata form is `SynonymDictionary`, api_meta 264 L136361-136410).
2. Enter the terms `VIP`, `Strategic`, `Priority`, `Tier 1` (UNVERIFIED (2026-10-20): the page's comma-separated entry form).
3. Save (UNVERIFIED (2026-10-20): any Active toggle — `SynonymGroup` has no active field, api_meta 264 L136400-136410).
4. Retest after an index wait if a term does not match yet (UNVERIFIED (2026-10-20): whether a synonym change waits on the ~15-minute record index lag).
5. Validate: a global search for "Priority" should now return all accounts whose names contain VIP, Strategic, Priority, or Tier 1.

**Anti-Pattern to avoid:** A junior admin proposed renaming every "VIP" account to "Priority" to "fix the data". This would break Salesforce-to-ERP integrations that reference Account.Name, invalidate reports filtered on the literal text, and create audit gaps for any record with a contract referencing the old name. Synonyms operate at the search layer and leave the data model untouched.

**Why it works:** Synonym groups are symmetric — a search for one term matches the others (api_meta 264 L136411-136413) — and adding a group does not modify any record. UNVERIFIED (2026-10-20): query-time evaluation and a 2,000-active-group org cap.

---

## Example 3: Diagnose Why a Salesforce Connect External Object Is Missing from Global Search

**Context:** An admin set up Salesforce Connect with an OData 4.0 data source pointing at an inventory system. The external object `Inventory_Item__x` is visible on related lists, can be queried via SOQL, and renders in record pages — but it never appears in Lightning global search.

**Problem:** External Objects need search on at the data source (Enable Search) and at the object (Allow Search); new external objects start with search off (api_meta 264 L44352).

**Solution sequence (run each step in order, stop at the first failing gate):**

1. `Setup → External Data Sources → Inventory System (OData)`:
   - Confirm the data source is Active.
   - Confirm **Enable Search** (`searchEnabled` in `customConfiguration`, L13830-13850) is on. If not, edit and save.
2. `Setup → External Objects → Inventory_Item__x → Edit`:
   - Confirm **Allow Search** is checked. If unchecked, edit and save.
3. Confirm adapter search support. OData 2.0/4.0 and Cross-Org adapters both carry the Enable Search parameter (api_meta 264 L13818-13850); a custom Apex adapter must declare the `SEARCH` capability (apexref 262 L151747-151751). The OData 4.0 adapter here passes.
4. Validate via Developer Console with a SOSL probe:
   ```apex
   List<List<SObject>> results = [FIND 'widget' IN ALL FIELDS RETURNING Inventory_Item__x(Id, Name)];
   System.debug(results);
   ```
   If this returns rows, the search index is reachable.
5. If SOSL returns rows but global search results don't show the object: open `Setup → Object Manager → Inventory_Item__x → Search Layouts` and confirm `searchResultsAdditionalFields` has at least one column (UNVERIFIED (2026-10-20): that an empty layout hides an external object's results).
6. Re-test; only text, text area, and long text area fields on external objects are searched (apexref 262 L151752).

**Why it works:** Each gate (data source flag, object flag, adapter capability, Search Layout) must be opened; a sync resets the object flag to the data source's (api_meta 264 L44352-44354). The platform error mode is silent — there is no banner that says "Allow Search is off"; the object simply does not appear in results.

**Common variation:** If the adapter is custom Apex and does not declare the `SEARCH` capability, no amount of configuration will make the external object searchable. Document the limitation and consider creating a custom Lightning Web Component for the inventory search use case.

---

## Anti-Pattern: Configuring Only Search Results and Forgetting the Lookup Dialog

**Context:** Admin updates the Account search results layout to add Industry, Phone, Owner. Users still complain that the lookup picker on `Case.AccountId` only shows the Account name.

**Why this happens:** `searchResultsAdditionalFields` and `lookupDialogsAdditionalFields` are separate fields of `SearchLayouts` (api_meta 264 L47528, L47580). A common assumption is that one drives the other — it does not. Configure each list you need per object, not just search results.

**Detection hint:** When validating any Search Layout change, test from at least two surfaces: global search bar AND an actual lookup picker on a related object. If only one surface shows the new columns, you missed a slot.
