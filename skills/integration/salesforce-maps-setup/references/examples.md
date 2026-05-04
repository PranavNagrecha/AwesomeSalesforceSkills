# Examples — Salesforce Maps Setup

## Example 1: First-Time Maps Install For 80-Rep Outside Sales Team

**Context:** A B2B distributor licensed Salesforce Maps (base tier only — no Advanced, no Routing, no Live Tracking) for 80 outside sales reps who visit ~2,500 active accounts in the US. Reps want to "see my accounts on a map and filter by industry" from their phone.

**Problem:** The first-time admin installed the package in production directly, ran the geocode batch, and had 600 of 2,500 Accounts fail to plot. Reps reported "my map is missing accounts" on day 1.

**Solution:**

Install plan (sandbox first):

1. Sandbox install of Salesforce Maps base package. Validate licensing screen shows correct entitlement (base tier).
2. Configure geocoding for `Account`:
   - Address fields: `BillingStreet, BillingCity, BillingState, BillingPostalCode, BillingCountry`
   - Real-time geocoding: **ON** (so new accounts appear immediately)
   - Initial batch: schedule for 2 AM in a low-traffic window
3. Run initial batch geocode. Record success/failure rate. Investigate failures:
   - 380 records: missing `BillingState` — fix in source data, re-batch
   - 120 records: invalid `BillingCountry` codes (free-text "USA" instead of "US") — picklist standardization
   - 100 records: PO Box addresses with no street — these geocode to ZIP centroid, acceptable
4. Build `MapsLayer__c` named "My Active Accounts" filtered by `Owner = $User AND Status = 'Active'`.
5. Place Lightning Maps component on the Account home tab.
6. Assign `Salesforce Maps` permission set to the 80-rep cohort.
7. Day-1 training: 30 min hands-on with a sample rep (record the session).

After validation in sandbox: deploy to production with the same sequence. Production geocode failure rate at go-live: 4% (acceptable).

**Why it works:** Sandbox-first surfaces the address-quality issues before they're rep-visible. Real-time geocoding ensures new accounts plot immediately. Permission-set assignment is the manual step package install doesn't do — easy to forget.

---

## Example 2: Polygon Territory Plan Migration From MapAnything

**Context:** A pharmaceutical sales org has been on the legacy MapAnything package for 5 years with 240 polygon-defined territories. They're migrating to the modern Salesforce Maps managed package (post-rebrand) and want to preserve the polygons.

**Problem:** The MapAnything package and the Salesforce Maps package have **different namespaces** (`ma__` vs `maps__`). Polygon vertex data lives in package-internal records that cannot be selected via SOQL across the namespace boundary. A "lift and shift" via Data Loader fails because the receiving object structure differs.

**Solution:**

Two-package coexistence migration:

1. Install modern Salesforce Maps + Maps Advanced **alongside** MapAnything in a sandbox. Both packages can coexist temporarily.
2. Export polygon vertex coordinates from MapAnything via the package's "Export Territory" feature (if available) or via a one-time Apex job that reads `ma__Territory_Polygon__c.ma__Vertices__c` (or equivalent) and dumps to CSV.
3. For each MapAnything territory, create a corresponding `MapsTerritory__c` in the new package and import the vertex coordinates via the Maps Advanced "Import Polygon" UI or a custom Apex importer that posts to the `MapsTerritory__c.maps__Polygon__c` field.
4. Validate every polygon visually (overlay both packages' territory layers and confirm vertex-to-vertex parity for the 240 polygons; sample 20 for pixel-level checks).
5. Re-run the assignment batch under the new package. Validate Account-to-territory assignments match the legacy state.
6. Cutover: assign the new Maps permission sets, remove the MapAnything permission set, monitor for 7 days.
7. Uninstall MapAnything once telemetry is clean for 30 days.

**Why it works:** A two-package coexistence window lets you validate polygon parity before users lose access to the legacy data. Going single-package immediately invites territory-coverage gaps if any polygon import fails.

---

## Anti-Pattern: Confusing Maps Territories With FSL Service Territories

**What practitioners do:** A customer with both Field Service and outside-sales-on-Maps tries to "unify" by mapping `MapsTerritory__c` records to `ServiceTerritory` records 1:1, then deleting one of the two.

**What goes wrong:**
- FSL's optimization engine looks at `ServiceTerritory.Address` and `ServiceTerritoryMember` for dispatch decisions. Maps stores polygon vertices in its own package object. They are not interchangeable models.
- Permission-set licensing differs: FSL Resource license vs Maps user license. Removing one orphans users from the other.
- Reports break: any FSL dashboard sourced from `ServiceTerritory` is dead if you delete those records.

**Correct approach:** Run the two products in parallel for the use cases each is designed for. FSL handles dispatch of work-order resources to scheduled appointments. Maps handles "where are my accounts and how do I route my day" for outside reps. Document the personas and the object boundary in the org's architecture record.
