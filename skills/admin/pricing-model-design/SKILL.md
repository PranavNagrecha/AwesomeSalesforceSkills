---
name: pricing-model-design
description: "Use this skill when selecting or designing the correct Salesforce CPQ pricing model for a product or product line — choosing among the four native Pricing Methods (List, Cost Plus Markup, Block, Percent of Total), deciding between Range and Slab Discount Schedule types, and mapping business pricing requirements to the correct CPQ mechanism before any configuration begins. Trigger keywords: CPQ pricing method, SBQQ__PricingMethod__c, Cost Plus Markup, Block Pricing design, Percent of Total design, discount schedule type, Range vs Slab discount, pricing model strategy, which CPQ pricing mechanism to use. NOT for CPQ implementation of Price Rule objects (use cpq-pricing-rules), NOT for standard Salesforce pricing without CPQ (use products-and-pricebooks), NOT for CPQ product catalog or bundle setup."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "which CPQ pricing method should I use for this product — list price, block, cost plus markup, or percent of total"
  - "customer needs volume discounts that work like tax brackets where each unit is priced at its own tier rate"
  - "support or maintenance product should be priced as a percentage of the software products on the same quote"
  - "need a flat fixed price for a quantity range rather than multiplying a unit price by quantity"
  - "product cost is known and price should be derived from a markup percentage rather than a list price entry"
  - "discount schedule not behaving correctly — entire quantity is getting the highest tier discount instead of incremental bracketing"
tags:
  - cpq
  - pricing-method
  - block-pricing
  - discount-schedule
  - percent-of-total
  - cost-plus-markup
  - pricing-design
  - range-vs-slab
inputs:
  - "Business pricing model description: how the price for each product type is calculated"
  - "Whether volume discounts are all-or-nothing at a tier (Range) or incremental like tax brackets (Slab)"
  - "List of products requiring non-standard pricing: flat-fee quantity ranges, cost-derived prices, or support-as-percentage products"
  - "Whether a markup ceiling or floor needs to be enforced for Cost Plus Markup products"
  - "Any products that require conditional price overrides on top of the base pricing method"
outputs:
  - "Pricing method decision for each product (SBQQ__PricingMethod__c value)"
  - "Discount Schedule type decision (Range vs Slab) with rationale"
  - "Documented interaction matrix between chosen pricing methods and Discount Schedules or Price Rules"
  - "Completed pricing model design checklist ready for implementation handoff"
dependencies:
  - cpq-product-catalog-setup
  - products-and-pricebooks
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

# Pricing Model Design

Use this skill when the task is to decide *which* Salesforce CPQ pricing mechanism best fits a business pricing requirement — before touching any configuration. This skill covers the four native CPQ Pricing Methods (`SBQQ__PricingMethod__c`), the two Discount Schedule types (Range vs Slab), and how these mechanisms interact. It does not cover the implementation of Price Rule objects or standard Salesforce pricebook-only pricing.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm Salesforce CPQ (managed package `SBQQ__`) is installed. All four Pricing Methods are CPQ-only fields on `Product2`. Standard Salesforce has no equivalent.
- Understand that the Pricing Method is set *per product* on `Product2.SBQQ__PricingMethod__c`. The wrong method cannot be corrected at the quote level — it must be fixed at the product level and will re-evaluate on the next quote calculation.
- Identify whether volume discount behavior should be all-or-nothing at a tier (Range / flat-tier) or incremental-bracket (Slab). This is the most commonly misunderstood design choice and the one most likely to produce incorrect pricing in production if not confirmed with the business stakeholder before configuration begins.
- Determine which products require a Price Rule layer on top of the base pricing method. Price Rules operate after all Pricing Methods in the CPQ price waterfall — they can override or further modify any price, but they add complexity and should be avoided when a native Pricing Method covers the requirement.
- Establish whether Cost Plus Markup products need a price ceiling or floor. CPQ does not enforce markup limits natively — approval rules or validation logic must be added separately if business controls are required.

---

## Core Concepts

### The Four CPQ Pricing Methods

Every `Product2` record in CPQ has a `SBQQ__PricingMethod__c` field that controls how the engine calculates the starting price for a quote line. The four values are:

**List** — The default. The engine reads the standard pricebook entry price (`PricebookEntry.UnitPrice`) and multiplies by quantity. All CPQ discounting mechanisms (Discount Schedules, Price Rules, Contracted Prices) layer on top of this. Use List when the product has a fixed catalog price and discounts are applied separately.

**Cost Plus Markup** — The engine reads the unit cost from `Product2.SBQQ__Cost__c` and applies a markup percentage (`SBQQ__DefaultMarkup__c` or the quote line's `SBQQ__Markup__c`). The resulting price replaces what would otherwise be the list price. Use this for products where the sales team derives price from cost — typically services or resale hardware with variable acquisition cost. **Critical:** CPQ imposes no upper or lower limit on the markup value. A rep entering a negative markup is valid from CPQ's perspective. If markup controls are required, enforce them through an approval process or a validation rule on `SBQQ__QuoteLine__c.SBQQ__Markup__c`.

**Block** — The engine replaces per-unit pricing entirely with a flat price for the quantity range the ordered quantity falls into. Block Price records (`SBQQ__BlockPrice__c`) define each range (lower bound, upper bound, price). The total for the line is the flat block price — CPQ does not multiply by quantity. Use this for seat-tier or capacity-tier licensing where "1–10 seats = $500 flat, 11–25 seats = $900 flat." Block Pricing and Discount Schedules are *not* interchangeable: Discount Schedules apply percentage discounts to a unit price, while Block Pricing replaces the unit price altogether.

**Percent of Total** — The engine prices this line as a percentage of other quote lines' net amounts, as specified by `SBQQ__PercentOfTotalBase__c` (options: Regular, All, or a specific product category). Use this for support, maintenance, or professional services that should always be a calculated percentage of the software being sold — not a fixed price. No Discount Schedule or Price Rule is needed for the basic use case; the percentage itself is the product's price.

### Range vs Slab Discount Schedules

A Discount Schedule (`SBQQ__DiscountSchedule__c`) applies volume-based percentage discounts on top of any Pricing Method except Block Pricing (where it creates a double-discount risk). The `SBQQ__Type__c` field has two values with fundamentally different behavior:

**Range (flat-tier)** — The entire quantity on the line receives the discount percentage for the tier the quantity falls into. If tiers are 1–10: 0%, 11–25: 10%, 26–100: 20%, then a quantity of 25 receives 10% on all 25 units. Jumping from 25 to 26 drops the price further because the full 26 units now receive 20%. This creates "cliff" effects at tier boundaries. Use Range when pricing tiers are clean and the business wants simplicity.

**Slab (incremental-bracket)** — Each unit is priced at the rate for the bracket it falls into, like income tax brackets. With the same tiers, a quantity of 25 receives 0% on units 1–10, then 10% on units 11–25. A quantity of 30 receives 0% on 1–10, 10% on 11–25, and 20% on 26–30. There are no cliff effects — adding one more unit never makes the previous units more expensive. Use Slab when the business requirement is that the customer always pays less-or-equal as they increase quantity, and when the discount model resembles progressive rate application.

**Choosing between them:** Confirm with the business stakeholder by walking through a concrete example at a tier boundary. If "buying 26 instead of 25 changes the cost of all 26 units," that is Range. If "buying 26 instead of 25 only changes the cost of the 26th unit," that is Slab. Developers and admins regularly configure Range when Slab was intended (or vice versa) because both use the same object and the difference is a single field value.

### Pricing Methods and Discount Schedule Interactions

Discount Schedules can coexist with List and Cost Plus Markup pricing methods — the schedule's percentage discount is applied after the base price is established. However, there are two interaction risks to design for:

1. **Block Pricing + Discount Schedule double-discount:** When Block Pricing is in effect, the CPQ engine uses the block price as the base. If a Discount Schedule is also attached to the product, the schedule's percentage discount applies to the block price, reducing it further. This is almost never the intended behavior. Remove Discount Schedules from Block-priced products unless stacking is explicitly required.

2. **Percent of Total + Discount Schedule:** A Discount Schedule on a Percent of Total product is technically valid but semantically unusual — the percentage-of-total calculation produces the base price, and then the schedule applies an additional percentage discount on top. This pattern is rarely intentional. Document explicitly if it is used.

### Price Rules as an Optional Overlay Layer

Price Rules (`SBQQ__PriceRule__c`) fire after all Pricing Methods in the CPQ price waterfall. They can modify any price field on the quote or quote line, regardless of which Pricing Method the product uses. Design constraint: always assign the base Pricing Method to cover the standard case, then add Price Rules only for conditional exceptions. Starting with a Price Rule for every pricing scenario creates unnecessary complexity and makes the waterfall hard to audit.

---

## Common Patterns

### Pattern: Flat-Tier Volume Discount (Range Schedule)

**When to use:** The product has a list price and customers who order more should receive larger discounts, with each tier applying uniformly to the full quantity — and "cliff" effects at tier boundaries are acceptable.

**How it works:**
1. Set `SBQQ__PricingMethod__c = 'List'` on the product.
2. Create a `SBQQ__DiscountSchedule__c` with `SBQQ__Type__c = 'Range'` and `SBQQ__DiscountUnit__c = 'Percent'`.
3. Create `SBQQ__DiscountTier__c` records for each breakpoint: lower bound and discount percentage.
4. Attach the schedule to `Product2.SBQQ__DiscountSchedule__c`.
5. Test with quantities at, below, and above each tier boundary to confirm the correct tier fires and the full quantity receives that tier's discount.

**Why not Slab:** If the business requirement is that only the incremental units beyond a breakpoint receive the higher discount, Range is incorrect. Walk through a tier-boundary example with the stakeholder before building.

### Pattern: Incremental-Bracket Volume Discount (Slab Schedule)

**When to use:** Volume discounts should work like tax brackets — each unit is priced at the rate for the range it falls into, with no cliff effects at tier boundaries.

**How it works:**
1. Set `SBQQ__PricingMethod__c = 'List'` on the product.
2. Create a `SBQQ__DiscountSchedule__c` with `SBQQ__Type__c = 'Slab'` and `SBQQ__DiscountUnit__c = 'Percent'`.
3. Create `SBQQ__DiscountTier__c` records for each breakpoint with the discount rate for that bracket.
4. Attach to `Product2.SBQQ__DiscountSchedule__c`.
5. Test with a quantity that spans multiple brackets and verify the line total equals the sum of each bracket's contribution.

**Why not Range:** Range gives a single discount rate to the entire quantity, which can make the total cost jump down as quantity increases past a tier boundary (a customer ordering 26 pays less total than one ordering 25). Slab eliminates this discontinuity.

### Pattern: Fixed-Tier Licensing with Block Pricing

**When to use:** Product licensing is sold in capacity tiers where 1–10 seats cost $500, 11–25 cost $900, and 26–50 cost $1,400 — regardless of how many seats within the range are ordered.

**How it works:**
1. Set `SBQQ__PricingMethod__c = 'Block'` on the product.
2. Create `SBQQ__BlockPrice__c` records for each tier: `SBQQ__LowerBound__c`, `SBQQ__UpperBound__c`, `SBQQ__Price__c` (the flat price), `SBQQ__Product__c`, and `SBQQ__Pricebook__c`.
3. Ensure ranges are contiguous and non-overlapping — gaps or overlaps in bounds produce unpredictable tier matching.
4. Verify no Discount Schedule is attached to this product (unless intentional stacking is documented).

**Why not a Range Discount Schedule:** A Discount Schedule reduces the unit price by a percentage. Block Pricing replaces the unit price with a fixed amount. These are fundamentally different pricing structures — using a Discount Schedule for this use case requires computing what percentage discount of the list price equals the intended block price at each quantity, which breaks whenever the list price changes.

### Pattern: Support or Maintenance as Percent of Total

**When to use:** A support or maintenance product should always be priced at a percentage (e.g., 18%) of the net price of other products on the same quote.

**How it works:**
1. Set `SBQQ__PricingMethod__c = 'Percent of Total'` on the support product.
2. Set `SBQQ__PercentOfTotalBase__c` to `'Regular'` (to include regular products only) or `'All'` (to include all lines including other Percent of Total lines). For category-specific base, set to the product category value.
3. Set `SBQQ__DefaultPercentage__c` or let the rep set the percentage at quote time via `SBQQ__PercentOfTotal__c` on the quote line.
4. No Discount Schedule or Price Rule is needed for the base case.

**Why not a Price Rule:** A Price Rule that computes a percentage of total is possible using a Lookup Query, but it requires building and maintaining logic that CPQ already handles natively via this Pricing Method. Use the Pricing Method unless the percentage calculation requires conditions that the native mechanism cannot support.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Standard product with catalog list price | `SBQQ__PricingMethod__c = 'List'` | Default; all other mechanisms layer on top |
| Product where price = cost + markup % | `SBQQ__PricingMethod__c = 'Cost Plus Markup'` + `SBQQ__Cost__c` | First-class cost-derived pricing; no Price Rule needed |
| Fixed flat fee for a quantity range (seat tiers) | `SBQQ__PricingMethod__c = 'Block'` + Block Price records | Replaces per-unit math with flat tier price |
| Maintenance/support priced as % of other lines | `SBQQ__PricingMethod__c = 'Percent of Total'` | Native mechanism; no Price Rule overhead |
| Volume discount where all units get same tier rate | Range Discount Schedule | Simpler; appropriate when cliff effects are acceptable |
| Volume discount where each unit priced at its bracket | Slab Discount Schedule | Eliminates cliff effects; correct for tax-bracket-style pricing |
| Block-priced product needs additional volume discount | Remove Discount Schedule (or add Price Rule carefully) | Block + Schedule double-discounts; remove unless stacking is explicit |
| Cost Plus Markup needs a ceiling on markup % | Price Rule or Approval Process on `SBQQ__Markup__c` | CPQ has no native markup ceiling; must be enforced externally |
| Conditional price override on top of any Pricing Method | Price Rule (fires after all Pricing Methods) | Price Rules are the correct overlay layer |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Elicit the pricing model for every product before touching configuration.** For each product, determine: Is the price list-derived, cost-derived, a fixed block amount, or a percentage of other lines? Document the pricing method for each product before any CPQ fields are set.
2. **Identify all volume discount requirements and classify them as Range or Slab.** For each product with tiered discounts, walk through a concrete tier-boundary example with the business stakeholder. Ask: "If a customer orders one more unit and crosses a tier boundary, should their cost for *all* units drop (Range), or only the additional units be priced at the higher discount (Slab)?" Record the answer before creating any Discount Schedule.
3. **Check for Pricing Method and Discount Schedule interaction risks.** For each Block-priced product, confirm no Discount Schedule is attached. For each Percent of Total product, confirm no unintentional Discount Schedule stacking. Document any intentional stacking with an explicit rationale.
4. **Assess whether Cost Plus Markup products need markup controls.** If CPQ admins or reps set the markup, confirm whether a markup ceiling, floor, or approval rule is required. Plan the enforcement mechanism (approval process, validation rule, or Price Rule) before implementation.
5. **Identify which requirements need Price Rules as an overlay.** After confirming Pricing Methods and Discount Schedules cover all standard cases, list only the conditional exceptions that require a Price Rule. Hand this list to the implementation phase (cpq-pricing-rules skill) rather than collapsing design and implementation.
6. **Produce a Pricing Model Design document.** Record the chosen `SBQQ__PricingMethod__c` value for each product, the Discount Schedule type and tier breakpoints for each volume-priced product, and any Price Rule overlay requirements. This document is the handoff artifact for implementation and the primary reference for future pricing changes.
7. **Validate against edge cases before sign-off.** For each pricing model decision, construct at least one edge case: the maximum quantity tier, a cost value that would generate an extreme markup, a quote with only Percent of Total products and no Regular products as the base. Confirm the design handles these correctly before handing off to implementation.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every product has an explicit `SBQQ__PricingMethod__c` decision documented — no "default to List" assumptions
- [ ] All volume discount requirements are classified as Range or Slab, confirmed with a tier-boundary example walkthrough
- [ ] Block-priced products do not have Discount Schedules attached unless intentional stacking is documented
- [ ] Cost Plus Markup products have `SBQQ__Cost__c` populated on Product2 and markup control requirements are identified
- [ ] Percent of Total products have the correct `SBQQ__PercentOfTotalBase__c` value documented
- [ ] Price Rule overlay requirements are listed separately from Pricing Method decisions
- [ ] Pricing Model Design document is produced and reviewed by a business stakeholder before implementation begins
- [ ] Edge cases for each pricing mechanism are documented and validated in design (not deferred to UAT)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Cost Plus Markup has no native ceiling — negative or extreme markups are silently accepted** — CPQ will accept any numeric value in `SBQQ__Markup__c`, including negative values (which produce a price below cost) or values above 1000%. This does not trigger an error or warning. If left uncontrolled, reps can quote products at prices that violate margin requirements. Enforce ceiling/floor constraints via a validation rule on `SBQQ__QuoteLine__c.SBQQ__Markup__c` or configure an approval rule that triggers on out-of-range markup values.
2. **Range and Slab schedules use the same object — the only difference is `SBQQ__Type__c`** — Admins frequently create a Discount Schedule with the wrong type because the UI label ("Type") gives no behavioral explanation. A Range schedule where Slab was intended passes all validation and silently produces incorrect totals that are difficult to detect without a specific tier-boundary test case. Always test with a quantity at a tier boundary and verify both that the total is correct and that the pricing logic matches the intended model.
3. **Block Pricing and Discount Schedules both apply during the CPQ waterfall — they are NOT mutually exclusive** — The CPQ engine does not prevent attaching a Discount Schedule to a Block-priced product. If both exist, the block price is treated as the base and the schedule's percentage discount reduces it further. This produces a combined discount that is rarely intended and can be hard to detect without examining both the product's Pricing Method and its Discount Schedule reference simultaneously.
4. **Percent of Total base includes only lines calculated before the Percent of Total product** — CPQ calculates quote lines in a specific sequence. If a Percent of Total product appears before the products it should be based on in the calculation order, the base amount may be zero or incomplete. The `SBQQ__PercentOfTotalBase__c` field controls *which* lines are included, but the calculation order of lines within the quote also matters. Test with quotes where the Percent of Total line is in different positions.
5. **Changing `SBQQ__PricingMethod__c` on a Product2 affects all existing open quotes containing that product** — When a product's Pricing Method is changed, the next recalculation of any open quote containing that product uses the new method. Existing saved prices are not locked unless the quote is in a terminal status. This can cause pricing on in-flight quotes to change unexpectedly after a product configuration change. Plan Pricing Method changes during low-activity periods and communicate the impact to the sales team.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Pricing Model Design document | Per-product pricing method decisions, Discount Schedule type choices, interaction matrix, and Price Rule overlay list |
| `SBQQ__PricingMethod__c` assignment list | Table of Product2 records and their chosen pricing method value, ready for implementation |
| Discount Schedule type decisions | Range vs Slab decision per product with tier breakpoints and stakeholder sign-off |
| Edge case validation plan | List of boundary cases to test per pricing mechanism before UAT |

---

## Related Skills

- cpq-pricing-rules — Use for implementing Price Rule objects, Price Conditions, Price Actions, and Lookup Queries after the pricing model design is complete
- cpq-product-catalog-setup — Use to configure Product2 records, product bundles, and product options before setting pricing methods
- products-and-pricebooks — Use for standard Pricebook and PricebookEntry setup that CPQ List pricing builds on top of
