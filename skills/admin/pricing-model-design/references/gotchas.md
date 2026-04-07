# Gotchas — Pricing Model Design

Non-obvious Salesforce CPQ platform behaviors that cause real production problems in this domain.

## Gotcha 1: Cost Plus Markup Accepts Any Numeric Value — Including Negative Markups

**What happens:** The CPQ engine accepts any numeric value for `SBQQ__Markup__c` on the quote line, including zero and negative numbers. A markup of -50 produces a net price that is 50% *below* cost. A markup of 10000 produces a net price 100 times the cost. CPQ does not validate the markup value or display a warning. The resulting price is written to the quote line and, if approved, flows to the contract and invoice.

**When it occurs:** Whenever a rep manually sets the markup on a Cost Plus Markup product during quote creation. Also occurs when a Price Rule sets `SBQQ__Markup__c` via a Price Action to a computed value that can go negative under certain input conditions (e.g., a discount formula that does not have a floor).

**How to avoid:** Add a validation rule on `SBQQ__QuoteLine__c` targeting `SBQQ__Markup__c` with a minimum and maximum threshold matching the business's allowed margin range. Alternatively, configure a CPQ Approvals rule that triggers when `SBQQ__Markup__c` is outside the approved range, requiring manager sign-off before the quote can be submitted. Neither mechanism is enabled by default — both must be built explicitly.

---

## Gotcha 2: Range Discount Schedule Cliff Effects Can Make Higher Quantities Cost Less in Total

**What happens:** With a Range (flat-tier) Discount Schedule, the discount rate for the tier the quantity lands in applies to the *entire* quantity, not just the incremental units. At a tier boundary, ordering one more unit drops the total price per unit for all units, which can cause the total price for a higher quantity to be less than for a lower quantity. For example: 25 units at 10% discount may cost more total than 26 units at 20% discount. This violates buyer expectations of monotonic pricing and can produce arbitrage behavior where reps deliberately quote higher quantities to reduce total price.

**When it occurs:** Any Range Discount Schedule where the percentage difference between adjacent tiers multiplied by the lower-bound quantity produces a dollar amount large enough to overcome the additional cost of the extra units at the new tier rate.

**How to avoid:** Before finalizing a Range schedule, calculate the total price at every tier boundary: `boundary_quantity × list_price × (1 - tier_discount)`. Verify that total at `upper_bound + 1` is not less than total at `upper_bound`. If cliff effects are present and unacceptable, switch to a Slab schedule. If Range is required by business policy, document the cliff behavior and ensure it is reviewed with Finance before deployment.

---

## Gotcha 3: Changing a Product's Pricing Method Mid-Pipeline Reprices Open Quotes on Next Recalculate

**What happens:** When `SBQQ__PricingMethod__c` is changed on a `Product2` record, all open CPQ quotes containing that product will use the new pricing method the next time the quote is recalculated or saved. The previously-saved price on the quote line is *not* locked or preserved automatically. If a rep opens an in-flight quote and triggers a recalculation (including auto-recalculation on save), the price changes without any visible warning.

**When it occurs:** Any time a Product2 pricing method is changed while open quotes for that product exist — including during the initial rollout of a CPQ pricing configuration and during post-go-live pricing model changes.

**How to avoid:** Before changing a Product2 pricing method in any org with active sales activity, query for open quotes containing the product (`SELECT Id FROM SBQQ__Quote__c WHERE SBQQ__Status__c NOT IN ('Closed Won','Closed Lost') AND Id IN (SELECT SBQQ__Quote__c FROM SBQQ__QuoteLine__c WHERE SBQQ__Product__c = :productId)`). Coordinate the change with the sales team, or make the change during a low-activity window. Consider using CPQ's "Price Protection" feature (if licensed) to lock prices on submitted quotes.

---

## Gotcha 4: Percent of Total Base Produces $0 if No Qualifying Lines Exist on the Quote

**What happens:** A product with `SBQQ__PricingMethod__c = 'Percent of Total'` and `SBQQ__PercentOfTotalBase__c = 'Regular'` prices at $0 when the quote has no Regular product lines — for example, if the only other lines on the quote are also Percent of Total products, or if no products have been added yet when the support product is first priced. CPQ does not raise an error; the line silently shows $0.

**When it occurs:** During quote creation when a rep adds the support/maintenance product before adding the software products. Also occurs if a quote is built using a template or automation that adds the Percent of Total product before the base products. If the quote is then saved without triggering a recalculation after all base products are added, the $0 price persists.

**How to avoid:** Configure a quote validation rule that warns or prevents submission if a Percent of Total line has a net price of $0 (indicating the base was empty when it was last calculated). Ensure reps know to trigger a manual recalculation after adding all Regular products when a Percent of Total product is already on the quote. Include this behavior in user training materials for the product type.

---

## Gotcha 5: Block Price Range Gaps and Overlaps Are Not Validated by CPQ

**What happens:** If `SBQQ__BlockPrice__c` records for a product have a gap between ranges (e.g., records cover 1–10 and 21–50 with no record for 11–20) or overlapping ranges (e.g., 1–15 and 10–25), CPQ does not raise a validation error at record creation time. For quantities in a gap, CPQ falls back to the product's pricebook entry list price for that quantity (effectively reverting to List pricing). For overlapping ranges, the behavior of which record is matched is undefined.

**When it occurs:** Most commonly during initial setup when Block Price records are created manually, especially if ranges are derived from a spreadsheet and entered one at a time without cross-checking. Also occurs when a new tier is inserted between existing tiers and the adjacent bounds are not updated.

**How to avoid:** After creating all Block Price records for a product, export them and verify: (1) contiguous ranges with no gaps (each record's lower bound equals the previous record's upper bound + 1), and (2) no overlapping bounds. The checker script in `scripts/check_pricing_model_design.py` can be run against a CSV export to detect gaps and overlaps automatically. Include this verification in the post-implementation checklist before any quote testing begins.
