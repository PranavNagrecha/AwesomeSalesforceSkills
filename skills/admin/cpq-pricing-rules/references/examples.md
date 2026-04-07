# Examples — CPQ Pricing Rules

## Example 1: Volume Discount Tiers Using a Discount Schedule

**Context:** A software company sells a cloud platform product. Pricing is per-seat and discount levels increase as the ordered quantity grows: 1–10 seats: no discount, 11–25 seats: 10%, 26–100 seats: 20%, 101+: 30%. Sales reps should not have to manually enter discounts.

**Problem:** Without a Discount Schedule, reps either manually enter discount percentages (inconsistent and prone to error) or a Price Rule must encode every tier as a separate condition — creating a maintenance burden each time tiers change.

**Solution:**

```text
Object: SBQQ__DiscountSchedule__c
  Name: Cloud Platform Volume Schedule
  SBQQ__Type__c: Range
  SBQQ__DiscountUnit__c: Percent

Tiers (SBQQ__DiscountTier__c):
  Tier 1: SBQQ__LowerBound__c = 1,   SBQQ__Discount__c = 0
  Tier 2: SBQQ__LowerBound__c = 11,  SBQQ__Discount__c = 10
  Tier 3: SBQQ__LowerBound__c = 26,  SBQQ__Discount__c = 20
  Tier 4: SBQQ__LowerBound__c = 101, SBQQ__Discount__c = 30

Product2 setup:
  SBQQ__DiscountSchedule__c = [lookup to Cloud Platform Volume Schedule]
```

**Why it works:** The CPQ calculation engine reads the Discount Schedule during the discount schedule phase of the price waterfall. The tier whose lower bound is closest to (but not above) the line quantity is applied. No rule logic is required, and adding new tiers only requires adding Discount Tier records, not changing rule conditions.

---

## Example 2: Matrix Pricing via Price Rule and Lookup Object

**Context:** An enterprise software vendor prices professional services at an hourly rate that depends on two factors: the service type (Implementation, Training, Support) and the contract tier (Standard, Premium, Enterprise). Rates are stored in a pricing matrix agreed by the finance team.

**Problem:** Without a Lookup Object, encoding a 3x3 matrix requires 9 separate Price Rules (one per combination) or complex nested conditions. Adding a new service type requires creating new rule records rather than adding rows to a data table.

**Solution:**

```text
Step 1 — Create Lookup Object records (SBQQ__LookupData__c)
  Column mapping (custom fields on SBQQ__LookupData__c):
    Services_Type__c    (Text)   — input: matches Quote Line product family
    Contract_Tier__c    (Text)   — input: matches Quote field for account tier
    Hourly_Rate__c      (Currency) — output: price to apply

  Sample data rows:
    Implementation | Standard  | 250
    Implementation | Premium   | 220
    Implementation | Enterprise| 195
    Training       | Standard  | 175
    ... (full matrix)

Step 2 — Create Lookup Query (SBQQ__LookupQuery__c)
  SBQQ__LookupObject__c: [Lookup Object API name]
  Input field mappings:
    Quote Line SBQQ__ProductFamily__c → Services_Type__c
    Quote SBQQ__ContractTier__c       → Contract_Tier__c
  Result field: Hourly_Rate__c

Step 3 — Create Price Rule (SBQQ__PriceRule__c)
  SBQQ__Active__c: true
  SBQQ__EvaluationOrder__c: 10
  SBQQ__LookupQuery__c: [lookup query from step 2]

  Price Condition:
    Source: Quote Line field SBQQ__ProductFamily__c
    Operator: equals
    Value: [leave open to fire for all services — or add specific product family conditions]

  Price Action:
    Target field: SBQQ__SpecialPrice__c
    Source: Lookup result field Hourly_Rate__c
```

**Why it works:** The Lookup Object externalizes the matrix. Finance can update rates by editing data records without touching rule configuration. The Lookup Query performs a SOQL-equivalent match during calculation and passes the result field to the Price Action. Adding a new service type requires only new Lookup Object rows.

---

## Example 3: Block Pricing for Seat-Tier Software Licensing

**Context:** A company sells a security scanning product with a fixed-fee pricing model: 1–5 devices costs $400 flat, 6–20 devices costs $800 flat, 21–50 devices costs $1,400 flat. The price is not per-device — it is the total for the tier.

**Problem:** Using a Discount Schedule on a per-unit price cannot replicate fixed-fee tiers because the engine multiplies the unit price by quantity. A Price Rule could override the net price but requires additional conditions. Block Pricing is the correct mechanism.

**Solution:**

```text
Object: SBQQ__BlockPrice__c (one record per tier per pricebook)

Record 1:
  SBQQ__Product__c:    [Security Scanner product]
  SBQQ__Pricebook__c:  [Standard Price Book]
  SBQQ__LowerBound__c: 1
  SBQQ__UpperBound__c: 5
  SBQQ__Price__c:      400

Record 2:
  SBQQ__LowerBound__c: 6
  SBQQ__UpperBound__c: 20
  SBQQ__Price__c:      800

Record 3:
  SBQQ__LowerBound__c: 21
  SBQQ__UpperBound__c: 50
  SBQQ__Price__c:      1400
```

**Why it works:** When the quote line quantity falls within a block price range, CPQ returns the block price directly and disables per-unit math. No formula or price rule is required. Ensure there is no Discount Schedule on this product — the schedule would apply a percentage reduction on top of the block price, double-discounting the total.

---

## Anti-Pattern: Using Multiple Price Rules to Replicate Discount Schedule Tiers

**What practitioners do:** Create a separate Price Rule for each quantity tier — Rule 1: "if quantity >= 11 AND quantity < 25, set discount to 10%", Rule 2: "if quantity >= 26 AND quantity < 100, set discount to 20%", etc. — instead of using a Discount Schedule.

**What goes wrong:** As tiers change, each rule must be individually updated. If two rules overlap or share the same Evaluation Order, the results are inconsistent. The rules are invisible in the CPQ pricing UI that shows Discount Schedules and tiers. Governance is harder because rules are not obviously tier-related to future admins.

**Correct approach:** Use a Discount Schedule with `SBQQ__DiscountTier__c` records. Discount Schedules are the first-class CPQ mechanism for quantity-based tiers, have a dedicated UI in Setup, and are easier to audit and update. Reserve Price Rules for conditional logic that cannot be expressed as a tier (e.g., account-attribute-based pricing that also needs a lookup).
