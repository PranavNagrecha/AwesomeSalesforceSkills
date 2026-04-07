# Gotchas — CPQ Pricing Rules

Non-obvious Salesforce CPQ pricing behaviors that cause real production problems.

## Gotcha 1: Duplicate Evaluation Order Values Produce Undefined Pricing Results

**What happens:** Two or more active Price Rules with the same `SBQQ__EvaluationOrder__c` value do not execute in a predictable sequence. The CPQ calculation engine does not specify a tiebreaker. Quotes saved in different sessions or by different users may produce different net prices even with identical inputs.

**When it occurs:** When an admin creates a new Price Rule and assigns an Evaluation Order value that already exists on another active rule — especially common when rules are copied or imported without renumbering.

**How to avoid:** Assign unique Evaluation Order values using a spaced numbering scheme (e.g., 10, 20, 30, 40). Maintain a pricing design document that lists all active rules and their evaluation orders. Before creating a new rule, verify no existing rule uses that order value. Use the CPQ Price Rules list view sorted by Evaluation Order to spot duplicates.

---

## Gotcha 2: Block Pricing and Discount Schedules Stack on the Same Product

**What happens:** If a product has both a `SBQQ__BlockPrice__c` record matching the quoted quantity and a `SBQQ__DiscountSchedule__c` attached, both apply during the price waterfall. Block pricing fires first and returns the fixed tier price. Then the discount schedule phase applies the tier percentage to that block price. The result is a lower-than-intended net price — a silent double discount.

**When it occurs:** When admins configure Block Pricing for a product that previously had a Discount Schedule, or when a Discount Schedule is applied broadly across a product family and not removed from products that were later given block prices.

**How to avoid:** When adding Block Pricing to a product, explicitly check for and remove any Discount Schedule attachment (`SBQQ__DiscountSchedule__c` on Product2). If intentional stacking is needed for a specific business case, document the combined effect and verify the final price mathematically before releasing to production.

---

## Gotcha 3: Price Rules Do Not Fire on Opportunity Products — Only on CPQ Quotes

**What happens:** Price Rules, Discount Schedules, Contracted Prices, and Block Pricing are all evaluated by the CPQ calculation engine, which runs on `SBQQ__Quote__c` save or recalculation. They have no effect on standard Opportunity Products (`OpportunityLineItem`) or standard Pricebook entries. If an org uses both CPQ Quotes and standard opportunity line items, the pricing diverges silently.

**When it occurs:** When a sales process allows reps to add products directly to an Opportunity (not through a CPQ quote), or when integrations sync opportunity products without going through CPQ quote creation. The rep may see one price in the CPQ quote and a different price on the Opportunity.

**How to avoid:** Enforce that all pricing goes through CPQ Quotes. Use a Validation Rule or Flow on OpportunityLineItem to prevent direct product adds if the org uses CPQ. Communicate to reps and integrations that all pricing must be driven from a CPQ quote, and that standard pricebook entries on the opportunity are not subject to CPQ pricing logic.

---

## Gotcha 4: Contracted Prices on Bundle Parents Do Not Apply to Bundle Components

**What happens:** A `SBQQ__ContractedPrice__c` record for Account A on the bundle parent product does not cascade to child Product Option records. Each component that needs a contracted rate requires its own `SBQQ__ContractedPrice__c` record. Without this, component lines calculate at list price even when the parent is contracted.

**When it occurs:** After contract activation generates contracted prices, if the contracted product was a bundle parent and the business expected all components to receive the contracted discount. This causes subtle undercharging or overcharging on renewal quotes.

**How to avoid:** After contract activation or manual contracted price creation, verify `SBQQ__ContractedPrice__c` records exist for each component that requires a contract rate. Automate this with a Flow or Apex trigger on contract activation if your bundle structure is deep or frequently renewed.

---

## Gotcha 5: Price Actions Targeting Early Waterfall Fields Are Silently Overwritten

**What happens:** A Price Action that sets `SBQQ__ListPrice__c` or `SBQQ__RegularPrice__c` appears to work in testing but its effect disappears on later recalculations. Later waterfall steps recalculate fields lower in the stack using the targeted field as an input, so the Price Action's value is overwritten before it reaches the net price.

**When it occurs:** When practitioners choose a Price Action target field without checking where it sits in the CPQ price waterfall. Targeting `SBQQ__ListPrice__c` on a rule with Evaluation Order 10 is immediately overwritten if a rule with Order 20 also reads list price to compute a discount.

**How to avoid:** For rules intended to produce a final pricing outcome, target `SBQQ__SpecialPrice__c` (which sits at the bottom of the price waterfall and drives the final net price) rather than intermediate fields like `SBQQ__ListPrice__c` or `SBQQ__RegularPrice__c`. Review the CPQ price field waterfall documentation before assigning Price Action targets. Use CPQ Calculator debug mode to confirm which field holds the final value after all rules fire.
