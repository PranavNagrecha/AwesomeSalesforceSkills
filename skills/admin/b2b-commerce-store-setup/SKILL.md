---
name: b2b-commerce-store-setup
description: "Use this skill to configure a Salesforce B2B Commerce storefront: creating the WebStore, linking BuyerGroups, assigning CommerceEntitlementPolicies, and granting buyer contacts transactional access. Trigger keywords: B2B Commerce, WebStore, BuyerGroup, entitlement policy, buyer account, storefront access. NOT for B2C Commerce (LWR storefronts using Individual/Person Account models), CPQ quote configuration, or Order Management fulfillment flows."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Scalability
  - Reliability
triggers:
  - "contacts under a buyer account cannot see products or place orders on the storefront"
  - "storefront search returns no results for products that exist in the catalog"
  - "buyer group entitlement policy not showing products to the right customers"
  - "how do I set up a B2B Commerce store with buyer groups and entitlements"
  - "products appear in Commerce admin catalog but are missing from storefront search results"
  - "how to grant a contact access to transact on a B2B storefront"
tags:
  - b2b-commerce
  - webstore
  - buyer-group
  - entitlement-policy
  - buyer-account
  - commerce-setup
inputs:
  - "Salesforce org with B2B Commerce for Visualforce or B2B Commerce on Lightning enabled"
  - "Account records that will act as BuyerAccounts"
  - "Contact records that need storefront transactional access"
  - "Product2 catalog with pricing already configured"
  - "Desired product visibility segmentation (which buyer groups see which products)"
outputs:
  - "Configured WebStore linked to one or more BuyerGroups via WebStoreBuyerGroup junction records"
  - "CommerceEntitlementPolicy records linked to each BuyerGroup via CommerceEntitlementBuyerGroup"
  - "BuyerAccount records derived from Account, with contacts assigned Buyer or Buyer Manager roles"
  - "Verified storefront access: entitled contacts can search and transact; unauthorized contacts cannot"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

# B2B Commerce Store Setup

This skill activates when a practitioner needs to configure or troubleshoot buyer access on a Salesforce B2B Commerce storefront — including WebStore creation, BuyerGroup assignment, entitlement policy linking, and granting individual contacts the ability to transact.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether the org uses B2B Commerce for Visualforce (legacy) or B2B Commerce on Lightning Experience — the admin UI differs, but the underlying data model (WebStore, BuyerGroup, CommerceEntitlementPolicy) is the same.
- The most common wrong assumption: all contacts under a BuyerAccount automatically inherit storefront access. They do not. Only contacts explicitly assigned the **Buyer** or **Buyer Manager** role via a `BuyerAccountAccess` (contact-level role assignment) can log in and transact. Missing this step causes silent access failures that appear identical to entitlement misconfiguration.
- Hard platform limits that cannot be raised via support case:
  - Maximum **200 BuyerGroups per CommerceEntitlementPolicy**.
  - A product entitled across more than **2,000 BuyerGroups per store** is silently excluded from storefront search indexing beyond that cap — the product remains visible in Commerce admin but disappears from buyer-facing search.

---

## Core Concepts

### 1. The WebStore → BuyerGroup → EntitlementPolicy Access Chain

The complete access model is a chain of junction objects:

```
WebStore
  └─ WebStoreBuyerGroup (junction)
       └─ BuyerGroup
            └─ CommerceEntitlementBuyerGroup (junction)
                 └─ CommerceEntitlementPolicy
                      └─ Entitled Product2 records
```

In parallel, buyer membership flows through:

```
Account (converted to BuyerAccount)
  └─ BuyerGroupMember  → BuyerGroup
  └─ Contact (assigned Buyer or Buyer Manager role via buyer access record)
```

A buyer contact can only see and purchase products that are:
1. Part of a `CommerceEntitlementPolicy` linked to a `BuyerGroup`
2. Where that `BuyerGroup` is linked to the `WebStore` the contact is accessing
3. Where the `Account` is a member of that same `BuyerGroup` via `BuyerGroupMember`
4. Where the contact themselves has an explicit Buyer or Buyer Manager role assignment

All four conditions must hold. Missing any single link produces either a blank catalog or a login failure.

### 2. BuyerGroup Limits and Silent Search Indexing Failures

`CommerceEntitlementPolicy` has a hard cap of **200 BuyerGroups** per policy. This limit cannot be increased via a support case; it is enforced at the platform level (B2B Commerce Developer Guide — Entitlement Data Limits).

A separate, less-documented limit applies at the store level: when a single `Product2` record is entitled across more than **2,000 BuyerGroups within one WebStore**, the Commerce search indexing engine silently stops indexing that product for buyer groups beyond the 2,000th. The product appears correctly in Salesforce admin and in the Commerce product catalog, but buyers in the affected groups see zero results in storefront search. There is no error log, warning email, or visible indicator in the UI that this cap has been breached.

### 3. Contact Roles: Buyer vs. Buyer Manager

Adding a contact to a BuyerAccount's associated Account record does not grant storefront access. Two explicit roles exist:

- **Buyer** — can browse, add to cart, and place orders on behalf of the account.
- **Buyer Manager** — can do everything a Buyer can, plus manage other buyers on the account (approve orders, manage address book, invite additional contacts depending on org configuration).

Role assignment is stored as a relationship record. If the role assignment record is missing, the contact can authenticate (if they have a Community or Experience Cloud user) but receives a "you are not authorized" error or an empty storefront with no cart access.

### 4. WebStore Configuration Checklist Before Linking Buyers

Before attaching BuyerGroups, the WebStore itself must have:
- A published **Commerce Experience Cloud site** associated with it.
- At least one active **price book** associated via `WebStorePricebook`.
- Search indexing enabled and at least one initial index run completed.

Skipping these steps means BuyerGroup and entitlement wiring looks correct in data but the storefront remains non-functional.

---

## Common Patterns

### Pattern A: Single BuyerGroup, Single Entitlement Policy

**When to use:** Most straightforward setups — all buyers on the store see the same product catalog and pricing tier.

**How it works:**
1. Create one `BuyerGroup` record (e.g., "Standard Buyers").
2. Create `WebStoreBuyerGroup` with `WebStoreId` = your store and `BuyerGroupId` = the new group.
3. Create one `CommerceEntitlementPolicy` (e.g., "Standard Entitlement").
4. Create `CommerceEntitlementBuyerGroup` linking the policy to the group.
5. Add `CommerceEntitlementProduct` records linking each `Product2` to the policy.
6. Convert each customer `Account` to a `BuyerAccount` (set `IsBuyer = true` on the Account, or use the Commerce admin UI).
7. Create `BuyerGroupMember` records for each BuyerAccount.
8. Assign Buyer roles to the relevant contacts.

**Why not skip buyer group:** Without a `BuyerGroup`, the entitlement policy has no path to the store. Products remain unentitled even if the `CommerceEntitlementPolicy` and `BuyerAccount` exist.

### Pattern B: Segmented Catalog via Multiple BuyerGroups

**When to use:** Different customer tiers need different product visibility (e.g., distributors see all SKUs, retail partners see a curated subset).

**How it works:**
1. Create one `BuyerGroup` per tier (e.g., "Distributor Buyers", "Retail Buyers").
2. Link both groups to the same `WebStore` via separate `WebStoreBuyerGroup` records.
3. Create one `CommerceEntitlementPolicy` per tier with the appropriate product set.
4. Link each policy to its corresponding `BuyerGroup` via `CommerceEntitlementBuyerGroup`.
5. Assign each `BuyerAccount` to the correct group via `BuyerGroupMember`.
6. Monitor total BuyerGroup count per policy — must stay under 200.

**Why not one policy with visibility rules:** The entitlement model is additive; a contact with access to multiple groups sees the union of entitled products. Separate policies per group is the only way to enforce hard product-level segmentation.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| All buyers need the same catalog | Single BuyerGroup + Single EntitlementPolicy | Simplest model; easiest to maintain |
| Different buyers need different product sets | One BuyerGroup + EntitlementPolicy per tier | Only model that enforces hard catalog segmentation |
| Products missing from storefront search but visible in admin | Check 2,000 BuyerGroup-per-product indexing limit | Platform silently drops search indexing beyond cap |
| Contact can log in but sees empty catalog or no cart | Verify contact has explicit Buyer or Buyer Manager role | Account membership alone is insufficient |
| EntitlementPolicy limit error when adding BuyerGroup | Split groups across multiple policies | Hard cap of 200 BuyerGroups per policy; cannot be raised |
| Store search returns zero results after setup | Confirm search index has been rebuilt after entitlement changes | Entitlement changes do not automatically trigger re-index |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify org prerequisites** — confirm B2B Commerce is enabled, a Commerce Experience Cloud site exists and is published, and at least one active price book is associated with the WebStore via `WebStorePricebook`.
2. **Model the buyer segmentation** — determine how many BuyerGroups are needed. If more than one tier is required, plan one `CommerceEntitlementPolicy` per tier. Verify the total number of groups per policy will not exceed 200.
3. **Create BuyerGroups and link to WebStore** — create each `BuyerGroup` record, then create the corresponding `WebStoreBuyerGroup` junction records tying each group to the `WebStore`.
4. **Create EntitlementPolicies and link products** — create each `CommerceEntitlementPolicy`, add `CommerceEntitlementProduct` records for the entitled `Product2` records, then create `CommerceEntitlementBuyerGroup` junction records linking each policy to its BuyerGroup. Verify total BuyerGroup-per-product count stays under 2,000 across the store.
5. **Convert Accounts to BuyerAccounts and add to groups** — set `IsBuyer = true` on each customer Account (or use Commerce admin), then create `BuyerGroupMember` records assigning each BuyerAccount to the correct BuyerGroup.
6. **Assign Buyer or Buyer Manager roles to contacts** — explicitly assign each transacting contact the Buyer or Buyer Manager role. Do not assume account membership grants access.
7. **Rebuild search index and validate** — trigger a Commerce search index rebuild, then log in as a test buyer contact and confirm: (a) entitled products appear in search, (b) cart is accessible, (c) non-entitled products are absent.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] WebStore has an associated published Experience Cloud site
- [ ] Each BuyerGroup is linked to the WebStore via a `WebStoreBuyerGroup` record
- [ ] Each `CommerceEntitlementPolicy` is linked to its BuyerGroup via `CommerceEntitlementBuyerGroup`
- [ ] No single policy exceeds 200 BuyerGroups
- [ ] No single product is entitled across more than 2,000 BuyerGroups in this store
- [ ] Each customer Account has `IsBuyer = true` and a `BuyerGroupMember` record
- [ ] Each transacting contact has an explicit Buyer or Buyer Manager role assignment
- [ ] Commerce search index has been rebuilt after entitlement changes
- [ ] End-to-end test: buyer contact can search entitled products and add to cart

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Contact role assignment is mandatory, not inferred** — Adding a contact to the Account that was converted to a BuyerAccount does not grant any storefront access. Only contacts with an explicit Buyer or Buyer Manager role assignment can transact. The failure mode is silent: the contact authenticates successfully but sees an empty storefront or receives an authorization error. This is the single most common misconfiguration in new B2B Commerce setups.

2. **Entitlement changes do not auto-trigger search re-indexing** — When you add or remove products from a `CommerceEntitlementPolicy` or add a new BuyerGroup, Commerce does not automatically rebuild the search index. The catalog admin reflects the change immediately, but buyers see stale search results until a manual or scheduled index rebuild completes. Always rebuild the index after any entitlement change and verify via a buyer-facing search before signoff.

3. **Silent search exclusion above 2,000 BuyerGroups per product** — If a `Product2` is entitled across more than 2,000 BuyerGroups within a single WebStore, the search indexer silently stops including that product for groups beyond the 2,000th. No error is raised, no warning email is sent, and the product still appears correctly in the Commerce admin catalog. The only symptom is that buyers in the overflow groups see no search results for that product. This limit is documented in the B2B Commerce Developer Guide (Entitlement Data Limits) but is easy to miss in high-scale multi-group deployments.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| WebStoreBuyerGroup records | Junction records linking each BuyerGroup to the WebStore |
| CommerceEntitlementBuyerGroup records | Junction records linking each EntitlementPolicy to its BuyerGroup |
| BuyerGroupMember records | Records assigning each BuyerAccount to one or more BuyerGroups |
| Contact role assignments | Buyer or Buyer Manager role records for each transacting contact |
| Rebuilt search index | Post-setup index confirming all entitled products are searchable |

---

## Related Skills

- admin/experience-cloud-site-setup — required prerequisite; the Commerce storefront runs on an Experience Cloud site that must be published before buyer access works
- admin/cpq-pricing-rules — if dynamic pricing per buyer group is needed, CPQ pricing rules interact with Commerce price books
