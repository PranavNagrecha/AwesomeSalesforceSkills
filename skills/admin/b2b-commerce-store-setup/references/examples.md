# Examples — B2B Commerce Store Setup

## Example 1: Granting a New Distributor Contact Storefront Access

**Context:** A manufacturing company has set up a B2B Commerce store. A new distributor account has been created in Salesforce, and the account executive asks why the distributor's purchasing contact cannot log in and see any products.

**Problem:** The Account was converted to a BuyerAccount and the contact has an Experience Cloud login, but no Buyer role was assigned to the contact, and the Account was never added to a BuyerGroup.

**Solution:**

```text
Step 1 — Verify Account is a BuyerAccount:
  Account record → IsBuyer = true
  (In Commerce Admin: Accounts → mark as Buyer)

Step 2 — Add BuyerAccount to the correct BuyerGroup:
  Create BuyerGroupMember:
    BuyerGroupId = <Distributor BuyerGroup Id>
    BuyerId      = <Account Id>

Step 3 — Assign Buyer role to the contact:
  Navigate to: BuyerAccount → Contacts → [Contact Name]
  Set Role = Buyer
  (Underlying record: creates a buyer access assignment record)

Step 4 — Rebuild Commerce search index.
Step 5 — Log in as the contact and verify catalog.
```

**Why it works:** The `BuyerGroupMember` record gives the Account access to the products entitled via the BuyerGroup's `CommerceEntitlementPolicy`. The Buyer role assignment gives the specific contact permission to transact. Both are required independently — the platform does not infer one from the other.

---

## Example 2: Products Visible in Admin but Missing from Storefront Search

**Context:** A B2B Commerce store has been running for six months. The catalog team added 50 new product SKUs, linked them to the existing `CommerceEntitlementPolicy`, and published the catalog. Buyers report that the new products do not appear in storefront search, but an admin can see them in the Commerce product list.

**Problem:** The search index was not rebuilt after the entitlement policy was updated. Entitlement changes are not automatically reflected in Commerce search until a re-index is triggered.

**Solution:**

```text
Step 1 — In Commerce Admin, navigate to: Store → Search → Indexes.
Step 2 — Select the relevant search index (typically the default catalog index).
Step 3 — Click "Rebuild" and wait for the index status to return to Active.
Step 4 — Log in as a buyer contact and search for one of the newly added SKUs.
Step 5 — Confirm the product appears in results with correct pricing.
```

**Why it works:** Commerce maintains a separate search index that is built from the entitled product set at index-build time. Updating `CommerceEntitlementProduct` records modifies the entitlement data model but does not automatically write to the search index. A manual rebuild (or a scheduled rebuild job) is required to surface the change to buyers.

---

## Example 3: Segmented Catalog for Distributor vs. Retail Buyer Tiers

**Context:** A wholesale supplier wants distributors to see all 3,000 SKUs but retail partners to see only 800 approved resale SKUs. Both buyer types use the same WebStore.

**Problem:** If a single BuyerGroup and EntitlementPolicy are used, there is no way to restrict the retail partners to a subset — Commerce entitlements are additive, not subtractive. A contact in the distributor group seeing the full catalog cannot be restricted by adding them to an additional group.

**Solution:**

```text
BuyerGroup: "Distributor Buyers"
  CommerceEntitlementPolicy: "Distributor Policy"
    → 3,000 CommerceEntitlementProduct records

BuyerGroup: "Retail Buyers"
  CommerceEntitlementPolicy: "Retail Policy"
    → 800 CommerceEntitlementProduct records (curated subset)

Both BuyerGroups linked to WebStore via WebStoreBuyerGroup records.

Each BuyerAccount assigned to exactly one group via BuyerGroupMember.
Contacts in each account assigned Buyer roles independently.
```

**Why it works:** Separate policies per tier enforce hard product-level segmentation. Retail buyer contacts only belong to the Retail group, so they can only see products entitled in the Retail policy. Distributor contacts belong only to the Distributor group. If a contact belonged to both groups, they would see the union of both catalogs — which is why account-to-group membership must be managed carefully.

---

## Anti-Pattern: Assuming Account Membership Equals Contact Access

**What practitioners do:** After converting an Account to a BuyerAccount and adding it to a BuyerGroup, the practitioner assumes all contacts under that Account can automatically log in and transact. They skip explicit Buyer role assignment for individual contacts.

**What goes wrong:** Contacts authenticate successfully via the Experience Cloud login page but land on a storefront with no products, no cart, and no ability to check out. The error may appear as an entitlement problem, leading to hours of debugging entitlement policies and BuyerGroup membership — which are all correctly configured. The actual cause is the missing per-contact role assignment.

**Correct approach:** After every new BuyerAccount setup, explicitly navigate to the BuyerAccount's contact list and assign the Buyer or Buyer Manager role to each contact who should be able to transact. Treat this as a mandatory provisioning step, not an optional one.
