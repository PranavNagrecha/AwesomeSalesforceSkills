# Pricing Model Design — Work Template

Use this template when designing the CPQ pricing model for a new product or revising an existing one. Complete all sections before beginning configuration.

## Scope

**Skill:** `pricing-model-design`

**Request summary:** (describe the pricing requirement — product name, pricing mechanism, business context)

**Related skill for implementation:** `cpq-pricing-rules` (if Price Rules are required)

---

## Context Gathered

Record answers to the Before Starting questions before proceeding.

- **CPQ managed package confirmed installed?** Yes / No
- **Products being designed:** (list each product requiring a pricing model decision)
- **Business stakeholder who confirmed requirements:** (name/role)
- **Discount schedule behavior confirmed at tier boundary?** Yes / No / N/A

---

## Product Pricing Method Decisions

For each product, record the chosen Pricing Method and the reason.

| Product Name | SBQQ__PricingMethod__c Value | Reason |
|---|---|---|
| [Product A] | List / Cost Plus Markup / Block / Percent of Total | [Reason] |
| [Product B] | List / Cost Plus Markup / Block / Percent of Total | [Reason] |

---

## Discount Schedule Design

Complete for each product that requires a volume discount.

### Product: [Product Name]

- **Discount Schedule Type:** Range (all units get tier rate) / Slab (incremental brackets)
- **Stakeholder confirmation of type:** (describe the tier-boundary example walked through and the answer given)
- **Discount Unit:** Percent / Amount

| Tier # | Lower Bound (Qty) | Upper Bound (Qty) | Discount % |
|---|---|---|---|
| 1 | 1 | [X] | [0%] |
| 2 | [X+1] | [Y] | [N%] |
| 3 | [Y+1] | [Z] | [M%] |

- **Cliff effect check (Range only):** Total at tier upper bound > Total at upper bound + 1? Yes (document) / No / N/A

---

## Block Pricing Design

Complete for each product with `SBQQ__PricingMethod__c = 'Block'`.

### Product: [Product Name]

| Tier # | Lower Bound (Qty) | Upper Bound (Qty) | Flat Price |
|---|---|---|---|
| 1 | 1 | [X] | $[amount] |
| 2 | [X+1] | [Y] | $[amount] |
| 3 | [Y+1] | [Z] | $[amount] |

- **Ranges contiguous (no gaps)?** Yes / No (fix before implementation)
- **Ranges non-overlapping?** Yes / No (fix before implementation)
- **Discount Schedule attached to this product?** No / Yes — if Yes, stacking is intentional: [rationale]

---

## Cost Plus Markup Configuration

Complete for each product with `SBQQ__PricingMethod__c = 'Cost Plus Markup'`.

### Product: [Product Name]

- **SBQQ__Cost__c populated on Product2?** Yes / No (required — pricing will fail without it)
- **SBQQ__DefaultMarkup__c value:** [%]
- **Markup controls required?** No / Yes
  - If Yes, enforcement mechanism: Validation Rule / Approval Rule / Price Rule
  - Markup ceiling: [%]
  - Markup floor: [%]

---

## Percent of Total Configuration

Complete for each product with `SBQQ__PricingMethod__c = 'Percent of Total'`.

### Product: [Product Name]

- **SBQQ__PercentOfTotalBase__c value:** Regular / All / [Category Name]
- **SBQQ__DefaultPercentage__c:** [%]
- **$0 base risk identified?** (describe what happens if no qualifying base lines exist)
- **Validation rule to catch $0 Percent of Total at submission?** Yes / No / Planned

---

## Pricing Method + Discount Schedule Interaction Matrix

For each product, record whether a Discount Schedule is attached and whether stacking with the Pricing Method is intentional.

| Product | Pricing Method | Discount Schedule Attached? | Stacking Intentional? | Notes |
|---|---|---|---|---|
| [Product A] | Block | No | N/A | — |
| [Product B] | List | Yes — [Schedule Name] | Yes | Volume discount per Range schedule |
| [Product C] | Percent of Total | No | N/A | — |

---

## Price Rule Overlay Requirements

List only the conditional pricing requirements that cannot be met by the native Pricing Method alone. Each item in this list becomes an implementation task in the `cpq-pricing-rules` skill.

| Requirement | Why Native Method Is Insufficient | Price Rule Approach |
|---|---|---|
| [e.g., Markup ceiling enforcement] | CPQ has no native markup ceiling | Approval Rule on SBQQ__Markup__c > 500% |
| [e.g., Conditional % override for strategic accounts] | Contracted Price handles fixed rates; variable % by account needs rule | Price Rule + Account condition + Lookup |

---

## Edge Case Validation Plan

List the boundary cases to verify for each pricing decision before UAT begins.

| Product | Test Case | Expected Result |
|---|---|---|
| [Product A] | Quantity at top of Block Tier 1 | Flat price = Tier 1 amount |
| [Product A] | Quantity at bottom of Block Tier 2 | Flat price = Tier 2 amount |
| [Product B] | Quantity crossing Range/Slab tier boundary | [Expected total per tier type] |
| [Product C] | Quote with no Regular products | Percent of Total line = $0; validation fires |
| [Product D] | Markup set to -1% | Validation rule fires / approval triggered |

---

## Review Checklist

Before handing off to implementation:

- [ ] Every product has an explicit `SBQQ__PricingMethod__c` decision with a documented reason
- [ ] All Discount Schedule types (Range vs Slab) confirmed at a tier-boundary example with the business stakeholder
- [ ] Block-priced products have no Discount Schedule attached, or stacking is explicitly documented
- [ ] Cost Plus Markup products have `SBQQ__Cost__c` populated and markup controls are specified
- [ ] Percent of Total products have `SBQQ__PercentOfTotalBase__c` value and $0-base risk mitigation
- [ ] Interaction matrix completed for all products
- [ ] Price Rule overlay list contains only requirements that native Pricing Methods cannot address
- [ ] Edge case validation plan completed and will be run before UAT
- [ ] Pricing Model Design document reviewed and signed off by business stakeholder

---

## Notes and Deviations

Record any deviations from the standard patterns in SKILL.md and the reason for each.

- (note 1)
- (note 2)
