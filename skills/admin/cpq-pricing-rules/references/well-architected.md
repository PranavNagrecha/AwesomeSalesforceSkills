# Well-Architected Notes — CPQ Pricing Rules

## Relevant Pillars

- **Operational Excellence** — Pricing configuration is a high-change area. Discount tiers, contracted rates, and price rules change with business cycles. The operational risk is configuration that is hard to audit, test, or update. Well-architected CPQ pricing externalizes data (Discount Schedules, Lookup Objects) from logic (Price Rules), uses documented Evaluation Orders, and maintains a pricing design document that lets any admin understand the full waterfall without examining every rule.

- **Performance** — The CPQ calculation engine runs synchronously on quote save. Price Rules with Lookup Queries execute SOQL against the Lookup Object during calculation. Poorly indexed Lookup Objects or a large number of active Price Rules can cause quote save timeout errors. Performance consideration: minimize the number of active rules, index Lookup Object input fields, and prefer Discount Schedules over equivalent Price Rules.

- **Reliability** — Pricing bugs are business-critical. Duplicate Evaluation Order values, incorrect Price Action targets, and Block Pricing stacked with Discount Schedules can all silently produce incorrect prices that reach customer proposals. Reliable CPQ pricing requires sandbox testing against a matrix of scenarios before production deployment, and a rollback plan (deactivating rules without deletion) for pricing changes.

- **Security** — CPQ pricing objects (`SBQQ__PriceRule__c`, `SBQQ__ContractedPrice__c`, `SBQQ__DiscountSchedule__c`) require explicit object and field-level security (FLS) configuration via CPQ permission sets. Contracted Prices contain account-specific rate information — access should be restricted to admin and finance roles. Reps should not have edit access to Contracted Price records. Price Rules should not be editable by general sales users.

## Architectural Tradeoffs

**Price Rules vs. Discount Schedules for volume tiers:** Discount Schedules are the correct mechanism for quantity-based tiers. Price Rules can replicate the behavior but create maintenance overhead and are harder to audit. The tradeoff: Price Rules are more flexible (can reference quote attributes), but Discount Schedules are self-documenting and UI-visible. Prefer Discount Schedules for tier logic and Price Rules for conditional logic that Discount Schedules cannot express.

**Contracted Prices vs. Price Rules for account-specific rates:** Contracted Prices are data-driven (one record per account/product combination) and scale without rule changes. Price Rules with account conditions are logic-driven and require rule updates as accounts change. The tradeoff: Contracted Prices require a process to create and maintain them (contract activation or manual creation); Price Rules are easier to prototype but do not scale to large account lists.

**Lookup Objects vs. hardcoded conditions for matrices:** Lookup Objects externalize pricing data and allow non-admin updates to rate tables. Hardcoded conditions inside Price Rules are faster to set up but create a rule management burden. The tradeoff: Lookup Objects add initial setup complexity; they pay off when the matrix has more than ~4 cells or changes frequently.

## Anti-Patterns

1. **Duplicate Evaluation Order values across active Price Rules** — Rules with the same Evaluation Order produce undefined execution sequence. The CPQ engine does not enforce uniqueness. The business impact is inconsistent quote prices across sessions. Fix: assign unique, spaced Evaluation Order values and maintain a pricing design document listing them.

2. **Using Price Rules to replicate Discount Schedule tiers** — Creating one Price Rule per quantity tier (with conditions like "quantity >= 11") duplicates a built-in CPQ mechanism. The result is rules that are harder to maintain, not visible in the discount schedule UI, and prone to gaps or overlaps. Fix: use Discount Schedule and Discount Tier records.

3. **Leaving Discount Schedules attached to Block-Priced products** — When both mechanisms are active on the same product, both apply during the waterfall, producing an unintended double discount. Fix: remove the Discount Schedule from any product using Block Pricing, unless deliberate stacking has been explicitly designed and validated.

## Official Sources Used

- Salesforce CPQ Price Rules Help — https://help.salesforce.com/s/articleView?id=sf.cpq_price_rules.htm
- Salesforce CPQ Price Rule Considerations — https://help.salesforce.com/s/articleView?id=sf.cpq_price_rule_considerations.htm
- Salesforce CPQ Block Pricing Help — https://help.salesforce.com/s/articleView?id=sf.cpq_block_pricing.htm
- Salesforce CPQ Contracted Pricing Help — https://help.salesforce.com/s/articleView?id=sf.cpq_contracted_pricing.htm
- Salesforce CPQ Quote Calculation Stages — https://help.salesforce.com/s/articleView?id=sf.cpq_quote_calc_stages.htm
- Salesforce CPQ Discount Schedules Help — https://help.salesforce.com/s/articleView?id=sf.cpq_discount_schedules.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
