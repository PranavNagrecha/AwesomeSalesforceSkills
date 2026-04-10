# LLM Anti-Patterns — Commerce Pricing and Promotions

Common mistakes AI coding assistants make when generating or advising on Commerce pricing and promotions. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Assigning Pricebooks via Account.Pricebook2Id

**What the LLM generates:** Advice to set `Account.Pricebook2Id` to a `Pricebook2.Id` to control which pricebook a buyer sees in the Commerce store. Sometimes generates Apex or Flow steps that update this field as part of a buyer onboarding process.

**Why it happens:** `Account.Pricebook2Id` is the correct field for Sales Cloud Opportunity pricing. LLMs trained on broad Salesforce documentation conflate the two pricing models because both involve `Pricebook2` and `Account` records.

**Correct pattern:**

```soql
-- Correct: assign pricebook via BuyerGroupPricebook junction
INSERT INTO BuyerGroupPricebook (BuyerGroupId, Pricebook2Id, Priority)
VALUES ('<BuyerGroup.Id>', '<Pricebook2.Id>', 10)

-- Verify assignment
SELECT Id, BuyerGroupId, Pricebook2Id, Priority
FROM BuyerGroupPricebook
WHERE BuyerGroupId = '<BuyerGroup.Id>'
```

The Commerce pricing engine reads `BuyerGroupPricebook` and `WebStorePricebook`. `Account.Pricebook2Id` is ignored by Commerce and should not be used for this purpose.

**Detection hint:** Flag any output that references `Account.Pricebook2Id` in a Commerce pricing context. Also flag any Apex or Flow that updates `Account.Pricebook2Id` as part of a buyer group setup flow.

---

## Anti-Pattern 2: Assuming Promotion Activation Alone Applies Discounts

**What the LLM generates:** Instructions to create a `Promotion` record, set `IsActive = true`, and expect discounts to appear at checkout without any mention of the checkout flow. Sometimes generates a complete `Promotion` + `PromotionSegmentSalesStore` setup guide that omits the `PromotionsCartCalculator` step entirely.

**Why it happens:** The data model for promotions looks complete once the records are created and active. The runtime dependency on a specific Flow element is not discoverable from the data model alone, and LLMs rarely have specific knowledge about the PromotionsCartCalculator subflow requirement.

**Correct pattern:**

```
// After creating Promotion + PromotionSegmentSalesStore records:
// 1. Open Flow Builder
// 2. Open the active checkout flow for the store
// 3. Confirm the PromotionsCartCalculator element is present
//    in the cart calculation sequence
// 4. If absent, add it before the cart totals step and reactivate the flow
// Without this element, zero promotions fire — no error is raised
```

**Detection hint:** Any guide that sets up promotions without explicitly mentioning the checkout flow or `PromotionsCartCalculator` is incomplete. Flag responses that claim promotion setup is complete after only creating data records.

---

## Anti-Pattern 3: Ignoring the 25-Pricebook Resolution Limit

**What the LLM generates:** Pricebook assignment advice that adds `BuyerGroupPricebook` records without any mention of the 25-pricebook-per-resolution-call limit. Often generates scripts that bulk-assign many pricebooks across BuyerGroups in an org without checking total visibility per buyer.

**Why it happens:** The limit is not obvious from the object model and is documented in a limits reference page that LLMs may not prioritize. The 5-per-store limit on `WebStorePricebook` is more prominent; the 25-per-call evaluation limit is less well-known.

**Correct pattern:**

```soql
-- Audit total pricebooks visible to a buyer in BuyerGroup X
-- (includes all BuyerGroups the buyer belongs to)
SELECT COUNT(DISTINCT Pricebook2Id)
FROM BuyerGroupPricebook
WHERE BuyerGroupId IN (
  SELECT BuyerGroupId
  FROM BuyerGroupMember
  WHERE BuyerId = '<Account.Id>'
)
-- Result must be 25 or fewer; extras are silently excluded at resolution time
```

**Detection hint:** Flag any bulk pricebook assignment script that does not include a count check or mention the 25-pricebook evaluation limit.

---

## Anti-Pattern 4: Creating PriceAdjustmentTier Records with Gaps Between Bounds

**What the LLM generates:** Tiered pricing configuration where tiers are defined independently with gaps between `UpperBound` of one tier and `LowerBound` of the next. For example: Tier 1 LowerBound=1, UpperBound=9 and Tier 2 LowerBound=11 (gap at quantity=10).

**Why it happens:** LLMs often generate tier examples using round numbers or human-friendly ranges without considering that the bounds must be contiguous. The silent fallback behavior (base price for gap quantities) is not intuitive and is easy to miss in testing if the gap range is rarely ordered.

**Correct pattern:**

```json
// Contiguous tiers — no gaps
{ "LowerBound": 1,  "UpperBound": 9,    "AdjustmentValue": 0  }
{ "LowerBound": 10, "UpperBound": 49,   "AdjustmentValue": 10 }
{ "LowerBound": 50, "UpperBound": null, "AdjustmentValue": 18 }

// WRONG — gap at quantity 10
{ "LowerBound": 1,  "UpperBound": 9,  "AdjustmentValue": 0  }
{ "LowerBound": 11, "UpperBound": 49, "AdjustmentValue": 10 }
```

**Detection hint:** For any set of `PriceAdjustmentTier` records, verify that `LowerBound[n+1] == UpperBound[n] + 1` for all consecutive tiers. Flag any sequence where this equality does not hold.

---

## Anti-Pattern 5: Generating Tiered Pricing with PricebookEntry.IsActive = false

**What the LLM generates:** Tiered pricing setup scripts that create `PriceAdjustmentSchedule` linked to a `PricebookEntry` that is inactive (`IsActive = false`). The schedule and tiers are created without errors, but the tiers never apply at runtime.

**Why it happens:** LLMs rarely check the `IsActive` status of referenced records when generating relationship-based setups. The `PricebookEntry` `IsActive` field is easy to overlook because inactive entries can still be queried and have related records created against them.

**Correct pattern:**

```soql
-- Verify PricebookEntry is active before creating PriceAdjustmentSchedule
SELECT Id, IsActive, UnitPrice, Pricebook2.Name, Product2.ProductCode
FROM PricebookEntry
WHERE Id = '<target PricebookEntry Id>'
-- IsActive must be true; if false, activate the entry first
```

After confirming `IsActive = true`, create the `PriceAdjustmentSchedule` and `PriceAdjustmentTier` records.

**Detection hint:** Any tiered pricing setup that does not include a `PricebookEntry.IsActive` check is incomplete. Flag responses that skip this verification step.

---

## Anti-Pattern 6: Scoping Promotions to BuyerGroup Without PromotionSegmentSalesStore

**What the LLM generates:** A promotion setup that creates `PromotionSegmentBuyerGroup` to scope a discount to a specific buyer group, but omits the required `PromotionSegmentSalesStore` record. The promotion record exists and is active but never fires.

**Why it happens:** `PromotionSegmentBuyerGroup` looks like sufficient scoping on its own. The requirement that `PromotionSegmentSalesStore` must also exist (to connect the promotion to a specific store) is a conjunction constraint that LLMs frequently miss.

**Correct pattern:**

```soql
-- Both records are required for a BuyerGroup-scoped promotion
-- 1. PromotionSegmentSalesStore — connects promotion to the store (required)
INSERT INTO PromotionSegmentSalesStore (PromotionId, SalesStoreId)
VALUES ('<Promotion.Id>', '<WebStore.Id>')

-- 2. PromotionSegmentBuyerGroup — further scopes to a BuyerGroup (optional filter)
INSERT INTO PromotionSegmentBuyerGroup (PromotionId, BuyerGroupId)
VALUES ('<Promotion.Id>', '<BuyerGroup.Id>')

-- Verify both exist
SELECT Id, PromotionId, SalesStoreId FROM PromotionSegmentSalesStore
WHERE PromotionId = '<Promotion.Id>'

SELECT Id, PromotionId, BuyerGroupId FROM PromotionSegmentBuyerGroup
WHERE PromotionId = '<Promotion.Id>'
```

**Detection hint:** Any promotion setup that includes `PromotionSegmentBuyerGroup` without a corresponding `PromotionSegmentSalesStore` is incomplete. Flag any guide that treats BuyerGroup scoping as a standalone step without mentioning the store junction requirement.
