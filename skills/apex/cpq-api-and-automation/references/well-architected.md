# Well-Architected Notes — CPQ API and Automation

## Relevant Pillars

- **Performance** — The CPQ pricing engine is computationally expensive. Synchronous calculate is the primary performance bottleneck for API-driven quoting. Quote line count directly determines whether sync or async calculate is appropriate. Large Quote Mode and `calculateInBackground` exist specifically to address this. Every ServiceRouter call in a transaction adds CPU, SOQL, and heap consumption on top of the CPQ package's own overhead.

- **Reliability** — Async calculation via `CalculateCallback` introduces silent failure modes. The CPQ API's error surfaces are inconsistent: some errors throw exceptions, others return empty models, and errors inside callbacks are swallowed entirely. Reliable implementations must instrument every ServiceRouter call with try/catch and explicit failure logging.

- **Operational Excellence** — The ServiceRouter model JSON schema is internal to the CPQ package and changes across versions. API-driven automation that hardcodes model structure is brittle across upgrades. Well-operated implementations stay in the lane of reading a model, making minimal targeted modifications, and saving — never constructing models from scratch.

- **Security** — ServiceRouter calls run in the context of the calling user. Running as a system user (without sharing) gives the API broader access than an end user would have in the CPQ UI. Automation that creates or amends quotes programmatically must ensure field-level security, object permissions, and CPQ permission sets are appropriate for the running user context.

- **Scalability** — Batch or integration workloads that programmatically calculate many quotes simultaneously can saturate CPQ's queueable capacity. Async calculate jobs compete for queueable slots. High-volume automation must implement backoff, monitoring, and throttling to avoid queueable queue saturation.

---

## Architectural Tradeoffs

**Sync vs. Async Calculation**

Synchronous `QuoteCalculator` is simpler to implement (linear code, immediate result) but is constrained by the 10-second CPU governor limit. Async calculation via `calculateInBackground` removes the CPU constraint but introduces callback complexity, silent failure risk, and eventual-consistency semantics (the quote is not calculated when the calling method returns). Choose sync for small quotes in interactive contexts; choose async for batch, integration, and high-line-count scenarios.

**ServiceRouter Abstraction vs. Direct SOQL/DML**

The CPQ API deliberately abstracts away the underlying schema. This is a tradeoff: you get pricing engine correctness in exchange for opacity. Developers accustomed to direct SOQL + DML patterns find the model-based API unfamiliar. The temptation to shortcut to DML is high but always incorrect for CPQ-owned pricing fields. Architectural guidance must make this constraint explicit in team standards and code review checklists.

**REST vs. Apex Invocation**

Both surfaces expose the same ServiceRouter capabilities. REST (`POST /services/apexrest/SBQQ/ServiceRouter`) is appropriate for external system integrations. Apex is appropriate for server-side automation within Salesforce. There is no functional difference in what operations are available; the choice is purely about where the calling code lives.

---

## Anti-Patterns

1. **Direct DML on CPQ pricing fields** — Updating `SBQQ__Discount__c`, `SBQQ__NetPrice__c`, or any other CPQ-calculated field directly via Apex DML or REST bypasses the pricing engine and produces financially inconsistent records. This is the single most common API anti-pattern in CPQ implementations. The correct path is always ServiceRouter → QuoteCalculator → QuoteSaver.

2. **Constructing ServiceRouter model JSON from scratch** — Manually building the model payload (rather than reading and modifying a model from `ServiceRouter.read()`) depends on an internal schema that is not versioned or documented as a public API. Such code is fragile across CPQ upgrades and may silently produce incorrect quote data. Always start from a read response.

3. **Ignoring async callback failure modes** — Implementing `SBQQ.CalculateCallback` without error handling in `onCalculated` leaves the system in an undetectable broken state when calculation jobs fail. In a high-volume integration, silent failures accumulate until a downstream process (renewal, invoicing, reporting) discovers the data inconsistency. Every `onCalculated` implementation must log failures explicitly.

---

## Official Sources Used

- Salesforce CPQ Developer Guide: Get Started with CPQ API — https://developer.salesforce.com/docs/atlas.en-us.cpq_dev_guide.meta/cpq_dev_guide/cpq_api_get_started.htm
- Salesforce CPQ Developer Guide: Calculate Quote API — https://developer.salesforce.com/docs/atlas.en-us.cpq_dev_guide.meta/cpq_dev_guide/cpq_api_calculate_quote.htm
- Salesforce CPQ Developer Guide: Contract Amender API — https://developer.salesforce.com/docs/atlas.en-us.cpq_dev_guide.meta/cpq_dev_guide/cpq_api_contract_amender.htm
- Salesforce CPQ Developer Guide: Contract Renewer API — https://developer.salesforce.com/docs/atlas.en-us.cpq_dev_guide.meta/cpq_dev_guide/cpq_api_contract_renewer.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
