# CPQ Pricing Rules — Work Template

Use this template when working on a CPQ pricing configuration task in this area.

## Scope

**Skill:** `cpq-pricing-rules`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- CPQ managed package installed and licensed: Yes / No
- Pricing mechanisms required: (Discount Schedules / Block Pricing / Percent of Total / Contracted Prices / Price Rules — circle all that apply)
- Products affected: (list product names or product families)
- Accounts with contracted pricing: (list if applicable, or "N/A")
- Existing Price Rules and their current Evaluation Orders: (list or attach screen capture)
- Known waterfall interactions or conflicts: (describe)

## Waterfall Design

Document the intended price waterfall for this implementation:

| Step | Mechanism | Products/Conditions | Expected Outcome |
|---|---|---|---|
| 1 | List Price | All products | Base pricebook price |
| 2 | Contracted Price | [Account / Product combinations] | [Override price or discount] |
| 3 | Block Pricing | [Product names] | [Fixed price for quantity range] |
| 4 | Discount Schedules | [Product names] | [Tier discount applied] |
| 5 | Price Rules | [Rule names and EO values] | [Field set, value applied] |

## Price Rule Inventory

For each Price Rule being created or modified:

| Rule Name | Evaluation Order | Active | Conditions (summary) | Action Field | Action Source |
|---|---|---|---|---|---|
| [Rule 1 name] | [10] | Yes | [e.g., Product Family = Implementation] | SBQQ__SpecialPrice__c | [Lookup result / static value] |
| [Rule 2 name] | [20] | Yes | [e.g., Quote.Account_Tier__c = Enterprise] | SBQQ__Discount__c | [Field / lookup] |

## Discount Schedule Inventory

For each Discount Schedule being created or modified:

| Schedule Name | Type | Products Attached | Tier Breakpoints |
|---|---|---|---|
| [Schedule name] | Range / Term | [Product names] | [e.g., 1–10: 0%, 11–25: 10%, 26+: 20%] |

## Block Price Inventory

For each product using Block Pricing:

| Product | Pricebook | Lower Bound | Upper Bound | Block Price | Discount Schedule? (must be none) |
|---|---|---|---|---|---|
| [Product name] | [Pricebook name] | [1] | [10] | [$400] | None |

## Contracted Price Notes

- Contract activation enabled in CPQ Settings: Yes / No
- Contracted Price records to create or verify: (list Account + Product combinations)
- Component-level contracted prices verified for bundles: Yes / No / N/A

## Approach

Which pattern from SKILL.md applies and why:

- [ ] Volume Discount via Discount Schedule
- [ ] Conditional Price Rule with Lookup Matrix
- [ ] Account Contracted Pricing
- [ ] Block Pricing for fixed-fee tiers
- [ ] Percent of Total product pricing
- [ ] Custom combination (describe below)

Notes on approach:

## Test Scenarios

Before marking complete, test the following scenarios in a sandbox:

| Scenario | Product | Quantity | Account | Expected Price | Actual Price | Pass? |
|---|---|---|---|---|---|---|
| No discount threshold | [Product] | 5 | [Standard] | $[list price] | | |
| Volume tier fires | [Product] | 15 | [Standard] | $[expected after tier] | | |
| Contracted account rate | [Product] | 1 | [Contracted account] | $[contracted rate] | | |
| Block price tier | [Product] | 8 | [Any] | $[block price] | | |
| Multiple rules interact | [Product] | [qty] | [Account] | $[combined result] | | |

## Checklist

Copy the review checklist from SKILL.md and tick items as completed:

- [ ] All active Price Rules have unique Evaluation Order values
- [ ] Each Price Rule has at least one Price Condition and at least one Price Action
- [ ] Price Actions reference valid field API names on the Quote or Quote Line
- [ ] Discount Schedules have at least one Discount Tier with a defined lower bound and discount
- [ ] Block Price records have non-overlapping quantity ranges for each product/pricebook combination
- [ ] Contracted Price records are linked to correct Account and Product
- [ ] Percent of Total products have correct pricing method and base field
- [ ] Waterfall tested end to end with a real quote in sandbox
- [ ] Evaluation Order and field targets for all Price Rules are documented

## Notes

Record any deviations from the standard pattern and why.
