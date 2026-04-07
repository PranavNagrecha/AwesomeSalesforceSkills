# Gotchas — B2B Commerce Store Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Contact Role Assignment Is Mandatory — Account Membership Is Not Sufficient

**What happens:** A contact under a correctly configured BuyerAccount can authenticate to the Experience Cloud storefront but sees an empty catalog, no cart, and cannot place orders. Entitlement policies, BuyerGroup membership, and WebStore linkage all check out as correct.

**When it occurs:** Every time a new contact is added to a BuyerAccount without explicitly receiving a Buyer or Buyer Manager role assignment. The platform does not grant transactional access based on Account relationship alone. The contact's Community or Experience Cloud user license allows login; the Buyer role governs what Commerce capabilities they can exercise.

**How to avoid:** Treat Buyer role assignment as a mandatory provisioning step separate from Account setup. After converting an Account to a BuyerAccount, navigate to the account's contact list in Commerce admin and assign the Buyer or Buyer Manager role to each transacting contact before signoff. Add this as a line item in any deployment checklist.

---

## Gotcha 2: Entitlement Changes Do Not Automatically Re-Index Search

**What happens:** Products added to a `CommerceEntitlementPolicy` appear immediately in the Commerce admin product catalog but do not appear in buyer-facing storefront search results. Buyers searching for the new SKU get zero results. The product is correctly entitled and the BuyerGroup linkage is correct.

**When it occurs:** Any time `CommerceEntitlementProduct` records are added, removed, or modified — including new product launches, seasonal catalog updates, and entitlement policy restructuring. The Commerce search index is a snapshot built at index-build time; it does not subscribe to entitlement data changes in real time.

**How to avoid:** After every entitlement change, manually trigger a search index rebuild from Commerce Admin → Store → Search → Indexes → Rebuild. For high-frequency catalog changes, configure a scheduled nightly index rebuild job. Always validate storefront search with a buyer test login after any catalog or entitlement update, not just an admin-side product list review.

---

## Gotcha 3: 200 BuyerGroups Per EntitlementPolicy Is a Hard Platform Limit

**What happens:** Attempting to create a `CommerceEntitlementBuyerGroup` record that would bring a policy's BuyerGroup count above 200 results in a platform error. The error message is not always intuitive — it may surface as a generic DML error or a validation rule failure depending on whether the operation is done via UI or API.

**When it occurs:** Multi-tenant B2B platforms or large wholesale distributors that model each customer account as its own BuyerGroup. This anti-pattern of one-group-per-account hits the limit quickly and cannot be resolved by contacting Salesforce Support — the limit is enforced at the platform level and is not adjustable.

**How to avoid:** Design BuyerGroups around product entitlement tiers, not around individual accounts. Accounts with identical product visibility requirements should share a single BuyerGroup. Only create separate BuyerGroups when the product set or pricing tier genuinely differs. Review the B2B Commerce Developer Guide — Buyer Group Data Limits and Entitlement Data Limits before finalizing the group model.

---

## Gotcha 4: 2,000 BuyerGroups Per Product Causes Silent Search Exclusion

**What happens:** A product entitled across more than 2,000 BuyerGroups within a single WebStore is silently dropped from search index results for all BuyerGroups beyond the 2,000th. No error is raised, no email notification is sent, and no UI indicator shows the product has been excluded. The product continues to appear correctly in Commerce admin, in the product catalog, and even in the entitlement policy's product list. Buyers in the overflow groups get zero search results for that product.

**When it occurs:** Only in very large multi-group deployments where a broadly available product (e.g., a standard catalog item sold to all customers) is explicitly linked to thousands of BuyerGroups. This is distinct from the 200-groups-per-policy limit — both limits can be hit independently.

**How to avoid:** Before deploying a model with hundreds of BuyerGroups, calculate the maximum number of groups any single product will be entitled across. If that number approaches 2,000, restructure using fewer, broader groups. Monitor for this during load or scale testing by logging in as a buyer in a high-numbered group and checking search results for widely-entitled products. Document the limit in your team's data model design review checklist.

---

## Gotcha 5: WebStoreBuyerGroup Is Bi-Directional but Not Automatic

**What happens:** A BuyerGroup with a correctly configured EntitlementPolicy and BuyerGroupMembers is created, but buyers still cannot access any products on the store. All entitlement and membership records look correct.

**When it occurs:** When the `WebStoreBuyerGroup` junction record linking the BuyerGroup to the specific WebStore is missing. Creating a BuyerGroup does not automatically attach it to any store — that link must be created explicitly. If an org has multiple WebStores (e.g., a test store and a production store), a BuyerGroup could be attached to the wrong store.

**How to avoid:** After creating any new BuyerGroup, immediately create the corresponding `WebStoreBuyerGroup` record and confirm `WebStoreId` points to the intended store. When cloning a store or migrating between environments, verify that all `WebStoreBuyerGroup` records are re-created for the target store's ID.
