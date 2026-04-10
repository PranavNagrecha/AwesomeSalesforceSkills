# Well-Architected Notes — CPQ Data Model

## Relevant Pillars

- **Security** — CPQ managed-package objects (`SBQQ__Quote__c`, `SBQQ__QuoteLine__c`, `SBQQ__Subscription__c`, etc.) are not covered by standard object permissions. Users must be assigned CPQ-specific permission sets (`SBQQ CPQ User`, `SBQQ CPQ Admin`) in addition to profile-level access. Field-level security applies independently to each SBQQ__ field. Integrations and Apex running in system context bypass FLS but must still respect the CPQ Quote API contract to avoid data corruption.
- **Reliability** — Pricing correctness depends on routing writes through the CPQ Quote API rather than direct DML. Any Apex trigger, Flow, or integration that bypasses the pricing engine introduces silent data corruption in quote totals and approval thresholds. The CPQ pricing engine itself is a synchronous operation vulnerable to CPU limits on large quotes; reliability requires scoping price rules and minimizing line count per quote.
- **Operational Excellence** — The SBQQ__ object graph spans 10+ managed-package objects. Operational health requires that teams document which objects are in use, monitor CPQ package version upgrades for deprecated API methods, and validate all custom automation against CPQ-specific test patterns (mocking `SBQQ.QuoteService`). Stale registry data (subscriptions not refreshed after amendments) causes renewal quote errors that are difficult to trace.
- **Performance** — The CPQ pricing engine runs synchronously during quote save. Price rules with broad conditions, discount schedules with many tiers, and large quote line counts multiply evaluation time. Architectural guidance: cap complex quotes at ~200 lines; scope all price rules to specific product families or quote fields; profile pricing passes using the CPQ calculator plugin interface.
- **Scalability** — `SBQQ__Subscription__c` record volume grows linearly with contracted quote lines across all customers. Reports, integrations, and renewal automations must use selective SOQL filters (`SBQQ__Contract__c`, `SBQQ__SubscriptionEndDate__c`) and avoid full-table scans. Bulk renewal automation should batch by contract to stay within SOQL and DML governor limits.

## Architectural Tradeoffs

**CPQ Quote API vs Direct DML:** The CPQ Quote API is the correct path for all programmatic writes. It is more complex (async callback pattern, JSON serialization) but guarantees pricing correctness. Direct DML is simpler but produces silent data corruption and is an architectural anti-pattern. The tradeoff is always in favor of the Quote API.

**Price Rules vs Apex Triggers for Pricing Logic:** CPQ Price Rules are the declarative, managed-package-supported mechanism for conditional pricing. Custom Apex triggers on `SBQQ__QuoteLine__c` that modify pricing fields bypass the pricing engine and conflict with the CPQ rule evaluation order. Platform design guidance favors price rules and discount schedules over custom triggers for pricing logic.

**Standard Quote Sync:** CPQ can optionally sync quote data to the standard `Quote` object for downstream integrations (e.g., order management systems that only read standard objects). Enabling sync adds save overhead and creates a second source of truth. Architecturally, the sync should be viewed as a one-way read interface for legacy systems, not a write path or a pricing source.

## Anti-Patterns

1. **Using standard Quote/QuoteLineItem as the CPQ pricing layer** — Treating the standard `Quote` object as the source of truth for pricing in a CPQ org. The standard Quote may not be synced, may be stale, or may not exist at all. All pricing data resides in `SBQQ__Quote__c` and `SBQQ__QuoteLine__c`. Any architecture that routes pricing decisions through the standard Quote in a CPQ org is incorrect by design.

2. **Bypassing the CPQ pricing engine with direct DML** — Writing to CPQ-managed price fields via Apex DML or Bulk API data loads without invoking the pricing engine. This pattern produces incorrect totals, fires approval rules against stale values, and is silently overwritten on the next CPQ save. It is not possible to maintain pricing integrity with this approach.

3. **Building custom subscription tracking outside SBQQ__Subscription__c** — Creating custom objects or using standard Asset to track CPQ-contracted recurring products. CPQ renewal and amendment flows are driven by `SBQQ__Subscription__c`. Custom tracking objects will not integrate with CPQ renewal automation, will not carry CPQ renewal pricing fields, and will duplicate data that the managed package already manages.

## Official Sources Used

- Salesforce CPQ Object Relationships — https://help.salesforce.com/s/articleView?id=sf.cpq_object_relationships.htm&type=5
- Salesforce CPQ Quote and Quote Line Fields — https://help.salesforce.com/s/articleView?id=sf.cpq_quote_fields.htm&type=5
- CPQ API QuoteModel / QuoteLineModel — https://developer.salesforce.com/docs/atlas.en-us.cpq_dev_guide.meta/cpq_dev_guide/cpq_dev_quote_api.htm
- Salesforce CPQ Subscription Fields — https://help.salesforce.com/s/articleView?id=sf.cpq_subscription_fields.htm&type=5
- Salesforce CPQ Price Rules — https://help.salesforce.com/s/articleView?id=sf.cpq_price_rules.htm&type=5
- Salesforce CPQ Discount Schedules — https://help.salesforce.com/s/articleView?id=sf.cpq_discount_schedules.htm&type=5
- Salesforce Well-Architected Framework — https://architect.salesforce.com/well-architected/overview
