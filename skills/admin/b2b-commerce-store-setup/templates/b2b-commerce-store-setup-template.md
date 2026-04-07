# B2B Commerce Store Setup — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `b2b-commerce-store-setup`

**Request summary:** (fill in what the user asked for)

---

## Context Gathered

Answer all of the following before proceeding:

- **WebStore name / ID:**
- **B2B Commerce edition:** (Lightning or Visualforce)
- **Experience Cloud site associated with this store:** (name + status: Published / Draft)
- **Number of distinct buyer tiers / product catalog segments:**
- **Approximate number of customer accounts to onboard initially:**
- **Approximate account count at 12 months:**
- **Are products broadly available to all buyers, or does each tier get a distinct product set?**
- **Known constraints (e.g., approaching 200-group limit, large SKU count):**
- **Has a Commerce search index rebuild been run recently?**

---

## BuyerGroup Model

Document the planned group structure before creating any records:

| BuyerGroup Name | Entitlement Policy Name | Products In Scope | Accounts to Assign |
|---|---|---|---|
| (e.g., Distributor Buyers) | (e.g., Distributor Policy) | (e.g., All 3,000 SKUs) | (e.g., 12 distributor accounts) |
| | | | |
| | | | |

**Limit checks:**
- [ ] No single CommerceEntitlementPolicy will exceed 200 BuyerGroups
- [ ] No single product will be entitled across more than 2,000 BuyerGroups in this store

---

## Setup Checklist

Work through these in order. Do not skip ahead.

### Phase 1: WebStore Prerequisites
- [ ] WebStore record exists and is the correct target
- [ ] Experience Cloud site is published and associated with this WebStore
- [ ] At least one active price book linked via `WebStorePricebook`
- [ ] Initial Commerce search index build has completed

### Phase 2: BuyerGroup and Entitlement Wiring
- [ ] BuyerGroup records created (one per catalog tier)
- [ ] `WebStoreBuyerGroup` junction records created for each BuyerGroup → WebStore pairing
- [ ] `CommerceEntitlementPolicy` records created (one per tier)
- [ ] `CommerceEntitlementProduct` records created for each entitled Product2
- [ ] `CommerceEntitlementBuyerGroup` junction records created linking each policy to its group

### Phase 3: Account and Contact Provisioning
- [ ] Each customer Account has `IsBuyer = true` (converted to BuyerAccount)
- [ ] `BuyerGroupMember` records created for each BuyerAccount → BuyerGroup assignment
- [ ] Each transacting contact has an explicit **Buyer** or **Buyer Manager** role assignment
- [ ] No contact is relying on account membership alone for storefront access

### Phase 4: Search Index and Validation
- [ ] Commerce search index rebuild triggered after entitlement setup
- [ ] Index status returned to Active before testing
- [ ] End-to-end test: buyer contact logged in and confirmed entitled products appear in search
- [ ] End-to-end test: buyer contact confirmed able to add items to cart and proceed to checkout
- [ ] End-to-end test: non-entitled products confirmed absent from buyer search results

---

## SOQL Validation Queries

Use these to verify record wiring before testing buyer access:

```soql
-- Confirm BuyerGroup is linked to the WebStore
SELECT Id, WebStoreId, BuyerGroupId, BuyerGroup.Name
FROM WebStoreBuyerGroup
WHERE WebStoreId = '<WebStore Id>'

-- Confirm EntitlementPolicy is linked to the BuyerGroup
SELECT Id, CommerceEntitlementPolicyId, BuyerGroupId
FROM CommerceEntitlementBuyerGroup
WHERE BuyerGroupId IN (SELECT BuyerGroupId FROM WebStoreBuyerGroup WHERE WebStoreId = '<WebStore Id>')

-- Confirm BuyerAccount is a member of a BuyerGroup
SELECT Id, BuyerId, BuyerGroupId, BuyerGroup.Name
FROM BuyerGroupMember
WHERE BuyerId = '<Account Id>'

-- Confirm contact has Buyer role (adjust object name to your org's implementation)
-- Navigate to BuyerAccount → Contacts in Commerce Admin to verify role in UI
```

---

## Approach Notes

Which pattern from SKILL.md applies?
- [ ] Pattern A — Single BuyerGroup, Single EntitlementPolicy (all buyers see same catalog)
- [ ] Pattern B — Segmented Catalog via Multiple BuyerGroups (different tiers, different product sets)

Why this pattern was chosen: (fill in)

---

## Deviations and Notes

Record any deviations from the standard pattern and the reason:

- (e.g., "Used two EntitlementPolicies per BuyerGroup to split physical vs. digital products — reason: catalog team manages them separately")
