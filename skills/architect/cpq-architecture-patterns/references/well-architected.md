# Well-Architected Notes — CPQ Architecture Patterns

## Relevant Pillars

- **Performance** — CPQ pricing engine performance is the dominant architectural constraint. The QLE synchronous calculation model creates a hard ceiling at 200–300 quote lines. Bundle depth multiplies SOQL per calculation. QCP JavaScript complexity adds overhead to every pricing event. Every architectural decision in CPQ has a performance dimension.

- **Reliability** — Pricing engine correctness depends on using the right integration path (ServiceRouter, not direct DML). Silent failures — truncated QCP, bypassed pricing engine, stale exchange rates — are the reliability risks unique to CPQ. Reliable CPQ implementations treat the pricing engine as a transactional system with defined entry points.

- **Scalability** — Quote line count scalability, concurrent user scalability (QLE is browser-rendered), and integration throughput scalability (ServiceRouter has API rate limits) all require explicit architectural decisions. Large Quote Mode is the primary scalability lever for line count; it trades UX for scale.

- **Security** — Integration users calling ServiceRouter must have appropriate CPQ permission set assignments. QCP code runs in the CPQ managed package context but can access any Salesforce data visible to the running user — QCP code review is part of security review. Static Resource QCP code is readable by any authenticated user — do not embed credentials or business logic that reveals sensitive pricing strategy.

- **Operational Excellence** — CPQ pricing logic is notoriously difficult to debug in production. Operational excellence requires enabling CPQ Calculation Logs during development and UAT, maintaining QCP code in source control (not manually pasted), and documenting the pricing waterfall configuration as a living architecture artifact.

---

## Architectural Tradeoffs

**Bundle Depth vs. Product Model Fidelity**
Flat bundles are performant but may not reflect the product's genuine hierarchical structure. Nested bundles model the product accurately but create calculation overhead. The tradeoff is performance vs. product model integrity. Resolution: use 2-level nesting as the default limit; model hierarchy using `SBQQ__FeatureName__c` grouping within a flat bundle where additional visual grouping is needed.

**Large Quote Mode: Scale vs. UX**
Enabling Large Quote Mode removes the QLE line count reliability ceiling but eliminates real-time price feedback. This is a direct trade between scale and user experience. The decision must involve sales leadership, not just technical architecture — the UX change affects rep workflow for all quotes on the account.

**ServiceRouter vs. Platform Events for Integration**
ServiceRouter provides synchronous, pricing-engine-aware quote CRUD. Platform Events with a CPQ subscriber provide asynchronous, near-real-time integration but require careful idempotency design and do not replace ServiceRouter for write operations. Use Platform Events for event notification (quote activated, order created); use ServiceRouter for data writes.

**Inline QCP vs. Static Resource QCP**
Inline QCP is simpler to set up and does not require a deployment pipeline for changes. Static Resource QCP is harder to bootstrap but is the only viable architecture for plugins exceeding ~80K characters, and is the only architecture that supports version-controlled, peer-reviewed plugin code. Start with Static Resource if the plugin has any complexity — retrofitting it later requires a deployment freeze during migration.

---

## Anti-Patterns

1. **Direct API DML for CPQ Data Writes** — Writing to SBQQ objects via standard REST/SOAP API bypasses the pricing engine entirely, producing corrupt quote state with zero prices and missing field values. All write operations must use ServiceRouter. This is the most consequential CPQ anti-pattern because its failure mode is silent and the damage is invisible until quotes are reviewed.

2. **Treating QCP as Unlimited Code Storage** — Developers add features to the QCP incrementally without monitoring `SBQQ__Code__c` size. When the 131,072-character limit is silently crossed, the plugin executes broken JavaScript without error. The Static Resource loader pattern must be adopted before hitting the limit, not after.

3. **Assuming CPQ Respects Standard Apex Governor Limits as a Warning** — CPQ managed package code shares the Salesforce execution context. Deep bundle nesting, complex Price Rules, and QCP code all consume the same Apex CPU and SOQL limits as custom code. Architects who treat CPQ as an isolated managed black box that manages its own limits will encounter production timeouts on realistic quote configurations.

4. **Designing Multi-Stage Discounting Without Acknowledging the Fixed Waterfall** — The pricing waterfall sequence is not configurable. Architectures that require Price Rules to run before Discount Schedules (or vice versa) will produce incorrect prices. All multi-stage discount logic must be designed around the fixed sequence: List → Contracted → Block → Discount Schedules → Price Rules → Net.

---

## Official Sources Used

- CPQ Quote Calculation Sequence — https://help.salesforce.com/s/articleView?id=sf.cpq_quote_calc_sequence.htm
- Guidelines for Multi-Currency CPQ — https://help.salesforce.com/s/articleView?id=sf.cpq_multi_currency.htm
- CPQ Configuration API (ServiceRouter) — https://developer.salesforce.com/docs/atlas.en-us.cpq_dev_api.meta/cpq_dev_api/cpq_api_overview.htm
- CPQ Object Relationships — https://help.salesforce.com/s/articleView?id=sf.cpq_object_relationships.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
