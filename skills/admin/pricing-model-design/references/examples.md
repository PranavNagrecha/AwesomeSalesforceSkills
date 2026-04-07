# Examples — Pricing Model Design

## Example 1: Selecting Range vs Slab for a Software License Volume Discount

**Context:** A software company sells a per-seat license at $100/seat list price. The pricing team wants to incentivize higher-volume purchases with tiered discounts: 1–10 seats at 0%, 11–25 seats at 10%, 26–100 seats at 20%.

**Problem:** The admin creates a `SBQQ__DiscountSchedule__c` with `SBQQ__Type__c = 'Range'` without confirming the intended behavior with the pricing team. At 25 seats the customer pays $100 × 25 × 0.90 = $2,250. At 26 seats the customer pays $100 × 26 × 0.80 = $2,080 — a total price *decrease* of $170 despite ordering one more unit. The cliff effect is present but was not expected by the business stakeholder who described wanting "each extra unit to be cheaper."

**Solution:**

```text
Step 1: Walk the stakeholder through a tier-boundary example.
  Ask: "If a customer orders 26 seats instead of 25, should their
  cost for all 26 seats drop to the 20% tier (Range), or should
  only the 26th seat get the 20% rate (Slab)?"

Step 2: If the answer is "only the 26th seat" — configure Slab:
  SBQQ__DiscountSchedule__c:
    SBQQ__Type__c = 'Slab'
    SBQQ__DiscountUnit__c = 'Percent'

  SBQQ__DiscountTier__c records:
    Tier 1: SBQQ__LowerBound__c = 1,  SBQQ__Discount__c = 0   (0%)
    Tier 2: SBQQ__LowerBound__c = 11, SBQQ__Discount__c = 10  (10%)
    Tier 3: SBQQ__LowerBound__c = 26, SBQQ__Discount__c = 20  (20%)

Step 3: Test at quantity 26:
  Units 1–10:  $100 × 10 × 1.00 = $1,000.00
  Units 11–25: $100 × 15 × 0.90 = $1,350.00
  Unit 26:     $100 ×  1 × 0.80 =    $80.00
  Total: $2,430.00  (vs Range: $2,080.00)
  Slab total is higher — confirming cliff effect is eliminated.
```

**Why it works:** The Slab type prices each unit at the rate for the bracket it falls into. Ordering more never makes the customer's cost for previously purchased units decrease. The key is confirming the intended behavior *before* configuring — Range and Slab use the same CPQ object with one field difference, and both pass validation.

---

## Example 2: Block Pricing for a Fixed-Fee Capacity Tier with No Discount Schedule

**Context:** A cloud infrastructure product is sold in three capacity tiers: Small (1–5 nodes) at $1,500 flat, Medium (6–20 nodes) at $4,000 flat, Enterprise (21–100 nodes) at $9,000 flat. The price does not change within a tier regardless of exact node count.

**Problem:** An admin attempts to implement this using a Range Discount Schedule off a $100/node list price. For the Small tier to produce $1,500 at 5 nodes, no discount is needed ($500 list × 5 nodes = $500 — this fails because $100 × 5 = $500, not $1,500). The admin tries to set the list price to $300/node and compute discounts from there, but the required percentages are different for each tier and recalculating them whenever pricing changes is a maintenance burden. The fundamental problem is that Discount Schedules modify a unit price by percentage — they cannot produce an absolute flat price for a range.

**Solution:**

```text
Step 1: Set SBQQ__PricingMethod__c = 'Block' on the Product2 record.

Step 2: Create SBQQ__BlockPrice__c records:
  Record 1:
    SBQQ__Product__c    = [Product Id]
    SBQQ__Pricebook__c  = [Pricebook Id]
    SBQQ__LowerBound__c = 1
    SBQQ__UpperBound__c = 5
    SBQQ__Price__c      = 1500.00

  Record 2:
    SBQQ__Product__c    = [Product Id]
    SBQQ__Pricebook__c  = [Pricebook Id]
    SBQQ__LowerBound__c = 6
    SBQQ__UpperBound__c = 20
    SBQQ__Price__c      = 4000.00

  Record 3:
    SBQQ__Product__c    = [Product Id]
    SBQQ__Pricebook__c  = [Pricebook Id]
    SBQQ__LowerBound__c = 21
    SBQQ__UpperBound__c = 100
    SBQQ__Price__c      = 9000.00

Step 3: Confirm no SBQQ__DiscountSchedule__c is attached to this
  product. If one exists, remove it — otherwise the schedule's
  percentage discount will apply to the block price, reducing it
  below the intended flat fee.

Step 4: Test at quantities 3, 5, 6, and 20. Confirm the line total
  equals the block price for the matched tier, not a unit-price
  calculation.
```

**Why it works:** Block Pricing replaces per-unit math entirely. CPQ looks up which `SBQQ__BlockPrice__c` record's lower/upper bound contains the quantity on the quote line and returns that record's `SBQQ__Price__c` as the line total. The unit price field on the pricebook entry is irrelevant while Block Pricing is active. Tier boundaries are clean, maintenance is limited to updating block price records, and no percentage calculation is required.

---

## Example 3: Percent of Total for Annual Support Priced as 18% of Software Net

**Context:** An annual support product should always be priced at 18% of the net price of all "Regular" software products on the same CPQ quote.

**Problem:** A consultant builds a Price Rule with a Lookup Query that sums the net prices of other lines and then applies 18% via a Price Action. The rule works in testing but fails intermittently in production when the Percent of Total line is added to the quote after the software lines and the recalculation does not always re-fire the rule correctly. The Price Rule approach also requires ongoing maintenance whenever the product mix changes.

**Solution:**

```text
Step 1: Set SBQQ__PricingMethod__c = 'Percent of Total'
  on the Support Product2 record.

Step 2: Set SBQQ__PercentOfTotalBase__c = 'Regular'
  (includes all lines with SBQQ__ProductType__c = 'Regular';
   excludes other Percent of Total lines).

Step 3: Set SBQQ__DefaultPercentage__c = 18 on the Product2,
  or allow reps to set SBQQ__PercentOfTotal__c = 18 on the
  quote line at quote time.

Step 4: Remove the Price Rule that was previously handling this.
  The native Pricing Method handles it without rule overhead.

Step 5: Test with a quote containing two software products and
  the support product. Confirm support line total equals
  (sum of Regular line net prices) × 0.18.
  Also test with a quote that has zero Regular lines — the
  support product should price at $0 (base is empty).
```

**Why it works:** The `Percent of Total` Pricing Method is CPQ's native mechanism for this requirement. It runs during the pricing method phase of the CPQ calculation engine and recalculates correctly on every save and recalculation. The Price Rule approach adds unnecessary complexity and has edge-case firing issues that the native method avoids.

---

## Anti-Pattern: Using a Range Discount Schedule to Implement Block Pricing

**What practitioners do:** Facing a requirement for flat-fee capacity tiers, an admin sets the list price to an arbitrary per-unit amount and then creates a Range Discount Schedule where the discount percentage at each tier produces approximately the intended flat fee. For example: list price $200/unit; at 1–5 units, 0% discount (total $200–$1,000); at 6–20 units, 66.7% discount to approximate $4,000 at 20 units.

**What goes wrong:** The discount percentage that produces the correct total at the *maximum* quantity of a tier produces the wrong total at any other quantity within that tier (because a percentage of a varying quantity × list price is not a constant). A customer ordering 6 nodes at a 66.7% discount pays $200 × 6 × 0.333 = $400, not $4,000. The approach fundamentally cannot produce a flat price using a percentage mechanism. Additionally, any list price change requires recalculating all tier discount percentages.

**Correct approach:** Use Block Pricing (`SBQQ__PricingMethod__c = 'Block'` + `SBQQ__BlockPrice__c` records). Block Pricing is the only native CPQ mechanism that returns a flat absolute price for a quantity range, independent of the list price and the specific quantity within the range.
