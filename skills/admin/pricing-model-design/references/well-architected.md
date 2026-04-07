# Well-Architected Notes — Pricing Model Design

## Relevant Pillars

### Operational Excellence

The most significant Well-Architected risk in pricing model design is complexity accumulation. Every Price Rule added as a workaround for a requirement that a native Pricing Method should handle is a maintenance liability — it requires documentation, testing, and ongoing updates when products change. Operational Excellence in CPQ pricing means preferring native mechanisms (Block Pricing, Percent of Total, Discount Schedules) over bespoke Price Rules wherever possible, and producing a documented Pricing Model Design artifact before configuration begins so that future admins can understand the system's intent without reverse-engineering it from active records.

The Pricing Model Design document produced by this skill is the primary Operational Excellence output. Without it, every pricing change in the future becomes a discovery task.

### Reliability

Reliability risks in CPQ pricing model design fall into three categories:

1. **Silent wrong prices:** Range vs Slab misconfiguration, Block Pricing with an attached Discount Schedule, and Percent of Total on a quote with no qualifying base lines all produce prices that CPQ considers valid. No error is raised. Reliability depends on design-time verification (boundary tests, interaction checks) not just UAT.

2. **Mid-pipeline repricing:** Changing a Product2 Pricing Method while open quotes exist reprices those quotes silently on next recalculation. A reliable deployment process for pricing changes includes a pre-change audit of open quotes containing affected products.

3. **Markup without controls:** Cost Plus Markup with no validation or approval rules is an unreliable pricing surface — individual reps can produce arbitrarily high or low prices. Reliability requires explicit enforcement of markup bounds.

### Performance

CPQ quote recalculation time is affected by the number of active Pricing Methods and how many price waterfall stages execute per line. Over-use of Price Rules (especially with Lookup Queries against large datasets) increases calculation time. Choosing native Pricing Methods (Block, Percent of Total, Cost Plus Markup) where they are semantically correct reduces the Price Rule count and keeps calculation performance bounded.

### Scalability

Discount Schedule tiers scale well — adding a new tier breakpoint is a single record insert that immediately applies to all new calculations without deployment. Block Price records scale similarly. Both are preferable to Price Rules for volume pricing logic because Price Rules require Conditions and Actions that grow in complexity as pricing model complexity grows.

Cost Plus Markup does not scale to scenarios where costs vary by account or geography — it uses a single `SBQQ__Cost__c` on the Product2 record. If cost varies by context, a Price Rule or custom cost lookup must be used instead.

### Security

CPQ pricing data — particularly Cost Plus Markup cost fields (`SBQQ__Cost__c`) and Contracted Prices — is sensitive. Object-level security and field-level security should restrict access to:

- `Product2.SBQQ__Cost__c` — typically internal finance only; reps should not see cost
- `Product2.SBQQ__DefaultMarkup__c` — internal only
- `SBQQ__ContractedPrice__c` — account-specific rates are commercially sensitive; limit to account teams and finance

Block Price records and Discount Schedule records are generally less sensitive (they describe public pricing tiers) but should still be read-only for reps.

---

## Architectural Tradeoffs

### Native Pricing Method vs Price Rule Overlay

The primary tradeoff in CPQ pricing model design is between native Pricing Methods (simpler, no rule logic, but constrained to the four built-in behaviors) and Price Rules (flexible, conditional, but adds waterfall complexity and maintenance overhead).

**Default to native Pricing Methods.** Add a Price Rule only when the native mechanism demonstrably cannot meet the requirement. A Price Rule that replicates what Percent of Total would do natively is always worse: it is harder to understand, requires more testing, and is more likely to fail under edge cases.

### Range vs Slab: Simplicity vs Buyer Fairness

Range schedules are simpler to configure and explain to buyers in a quote summary ("all units get the tier rate"). Slab schedules are more equitable — ordering more never costs more total — but the line-item breakdown is harder to explain.

The tradeoff is between simplicity (Range) and fairness/predictability (Slab). The correct choice is determined by the business's pricing philosophy, not by technical preference.

### Block Pricing: Strict Tier Fences vs Granular Unit Pricing

Block Pricing is operationally simple and resists gaming (the price is fixed regardless of exact count within the range) but creates discontinuities at tier upper bounds — a customer at the top of one tier pays the same as a customer at the bottom, which can feel unfair at the boundary. Granular per-unit pricing with a Range schedule creates cliff effects at boundaries. Neither is universally superior — the design choice depends on whether the business prioritizes simplicity or continuous fairness.

---

## Anti-Patterns

1. **Building Price Rules to replicate native Pricing Method behavior** — Using a Price Rule with a Lookup Query to compute a support product's price as a percentage of other lines, when `SBQQ__PricingMethod__c = 'Percent of Total'` covers the requirement natively. This creates a rule dependency that must be maintained, tested, and documented, and is more likely to fail under edge cases than the native mechanism. Always audit whether a native Pricing Method covers the requirement before designing a Price Rule.

2. **Mixing Block Pricing and Discount Schedules without explicit documentation** — Attaching a Discount Schedule to a Block-priced product is technically valid in CPQ but almost always unintentional. It produces a combined discount (block price further reduced by the schedule percentage) that neither the pricing team nor the sales team expects. If stacking is truly required, it must be documented explicitly in the Pricing Model Design document with a rationale and a test case at each block tier.

3. **Skipping the Range vs Slab stakeholder confirmation step** — Configuring a Discount Schedule type based on an assumption about the business intent, without walking through a tier-boundary example with the pricing stakeholder. Because both types use the same CPQ object with one field difference, this error passes all functional validation and is only detected in user acceptance testing — often after reps have already seen prices they consider incorrect.

---

## Official Sources Used

- Salesforce CPQ Pricing Methods Help — https://help.salesforce.com/s/articleView?id=sf.cpq_pricing_methods.htm
- Salesforce CPQ Discount Schedules Help — https://help.salesforce.com/s/articleView?id=sf.cpq_discount_schedules.htm
- Salesforce CPQ Block Pricing Help — https://help.salesforce.com/s/articleView?id=sf.cpq_block_pricing.htm
- Salesforce CPQ Quote Calculation Stages — https://help.salesforce.com/s/articleView?id=sf.cpq_quote_calculator_stages.htm
- Salesforce CPQ Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.cpq_dev_guide.meta/cpq_dev_guide/cpq_dev_guide_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
