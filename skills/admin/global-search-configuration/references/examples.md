# Examples — Global Search Configuration

Concrete configurations and audit traces. Each example assumes the admin has the **Customize Application** permission and is operating against a sandbox before promoting to production.

---

## Example 1: Refresh Account Search Layouts for a Lightning Rollout

**Context:** A 4,000-user manufacturing org just migrated from Classic to Lightning. Sales users complain that global search results for Accounts show only the Account Name column. Reps are clicking into each result to disambiguate.

**Problem:** The org's `Account → Search Layouts → Default Layout (Lightning)` slot was empty — Lightning rendered the fallback (Name only). The Classic-era Search Results slot was populated, but Lightning does not read it.

**Solution:**

1. Audit current state via Metadata API:
   ```bash
   sf project retrieve start --metadata "CustomObject:Account" --target-org sandbox
   ```
   Open `force-app/main/default/objects/Account/Account.object-meta.xml` and locate the `<searchLayouts>` block.
2. Add a `<customSearchLayout>` entry with the chosen column set:
   ```xml
   <searchLayouts>
       <customSearchLayoutColumns>
           <field>NAME</field>
           <field>Industry</field>
           <field>BillingCity</field>
           <field>BillingState</field>
           <field>Phone</field>
           <field>Owner</field>
           <field>LastModifiedDate</field>
       </customSearchLayoutColumns>
   </searchLayouts>
   ```
   In the Object Manager UI, the equivalent path is: `Setup → Object Manager → Account → Search Layouts → Default Layout → Edit → move 6 fields from Available to Selected`.
3. Deploy:
   ```bash
   sf project deploy start --metadata "CustomObject:Account" --target-org sandbox
   ```
4. Validate: log in as a sales user (not a System Administrator — admin profiles have broad FLS that may mask FLS issues), run a global search for an account name, confirm all 7 columns render with values.
5. Wait ~15 minutes for the index, then promote to production via change set or pipeline.

**Why it works:** Each Search Layout slot is independent. Lightning global search reads only the Default Layout slot — populating it gives users a useful 7-column result row.

---

## Example 2: Add a Custom Synonym Group for Account Tier Vocabulary

**Context:** A B2B sales team uses the words "VIP", "Strategic", and "Priority" interchangeably to refer to top-tier accounts. The Account name fields contain a mix — some are "VIP Industries Ltd", some are "Priority Manufacturing Co." Reps search for "Priority" and miss VIP accounts (and vice versa).

**Problem:** Account names are not normalized; renaming records is out of scope (legal contracts reference the existing names). Global search needs to treat the four terms as equivalents at the search layer.

**Solution:**

1. Navigate to `Setup → User Interface → Synonyms → New Synonym Group`.
2. Enter the comma-separated list: `VIP, Strategic, Priority, Tier 1`.
3. Mark **Active**. Save.
4. Wait 15 minutes for the index to incorporate the group.
5. Validate: a global search for "Priority" should now return all accounts whose names contain VIP, Strategic, Priority, or Tier 1.

**Anti-Pattern to avoid:** A junior admin proposed renaming every "VIP" account to "Priority" to "fix the data". This would break Salesforce-to-ERP integrations that reference Account.Name, invalidate reports filtered on the literal text, and create audit gaps for any record with a contract referencing the old name. Synonyms operate at the search layer and leave the data model untouched.

**Why it works:** Synonym Groups are evaluated by the search index at query time. Adding a group does not modify any record. The org-wide cap is 2,000 active groups, well above what any single org needs.

---

## Example 3: Diagnose Why a Salesforce Connect External Object Is Missing from Global Search

**Context:** An admin set up Salesforce Connect with an OData 4.0 data source pointing at an inventory system. The external object `Inventory_Item__x` is visible on related lists, can be queried via SOQL, and renders in record pages — but it never appears in Lightning global search.

**Problem:** External Objects require three independent "Allow Search" gates to be open, plus an adapter that supports SOSL. Default is off for both flags.

**Solution sequence (run each step in order, stop at the first failing gate):**

1. `Setup → External Data Sources → Inventory System (OData)`:
   - Confirm the data source is Active.
   - Confirm **Allow Search** is checked. If unchecked, edit and save.
2. `Setup → External Objects → Inventory_Item__x → Edit`:
   - Confirm **Allow Search** is checked. If unchecked, edit and save.
3. Confirm adapter SOSL support. OData 2.0 / OData 4.0 support SOSL. Cross-Org and most custom Apex adapters do not. The OData 4.0 adapter here passes.
4. Validate via Developer Console with a SOSL probe:
   ```apex
   List<List<SObject>> results = [FIND 'widget' IN ALL FIELDS RETURNING Inventory_Item__x(Id, Name)];
   System.debug(results);
   ```
   If this returns rows, the search index is reachable.
5. If SOSL returns rows but global search results don't show the object: open `Setup → Object Manager → Inventory_Item__x → Search Layouts → Default Layout (Lightning)` and confirm at least one column is configured. An external object with no Search Layout renders as an invisible result.
6. Wait 15 minutes for re-indexing after enabling search. Re-test.

**Why it works:** Each gate (data source flag, object flag, adapter capability, Search Layout) is independent and must be opened separately. The platform error mode is silent — there is no banner that says "Allow Search is off"; the object simply does not appear in results.

**Common variation:** If the adapter is custom Apex and does not implement SOSL, no amount of configuration will make the external object searchable. Document the limitation and consider creating a custom Lightning Web Component for the inventory search use case.

---

## Anti-Pattern: Configuring Only Search Results and Forgetting the Lookup Dialog

**Context:** Admin updates `Account → Search Layouts → Default Layout` and `Search Results` to add Industry, Phone, Owner. Users still complain that the lookup picker on `Case.AccountId` only shows the Account name.

**Why this happens:** Search Results and Lookup Dialog are independent slots. A common assumption is that one drives the other — it does not. Configure all five Search Layout slots (Default Layout, Search Results, Lookup Dialog, Lookup Phone Dialog, Tab) per object, not just Search Results.

**Detection hint:** When validating any Search Layout change, test from at least two surfaces: global search bar AND an actual lookup picker on a related object. If only one surface shows the new columns, you missed a slot.
