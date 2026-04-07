# Well-Architected Notes — CPQ Guided Selling

## Relevant Pillars

- **Operational Excellence** — Guided Selling configuration is a product catalog governance concern. Quote Process and ProcessInput records represent a contract between the rep experience and the product data model. The operational risk is configuration that becomes stale when classification fields or picklist values change on Product2 but are not updated on the corresponding ProcessInput mirror fields or wizard questions. Well-architected guided selling documents the field mapping explicitly, treats mirror field creation as a deployment artifact (not a one-time task), and includes guided selling validation in the CPQ change management process whenever the Product2 schema changes.

- **Reliability** — Silent filtering failure is the primary reliability risk for guided selling. When a mirror field is missing, the wizard continues to function without surfacing any error — reps receive incorrect (unfiltered) product lists, leading to wrong products on quotes and downstream pricing or fulfillment issues. Reliable guided selling requires validation at setup time (confirming mirror fields exist), at change time (confirming changes to Product2 fields are reflected on ProcessInput), and through automated checks that can be run as part of deployment verification.

- **Performance** — The guided selling filter executes a SOQL query against `Product2` on every wizard submission. Large product catalogs (thousands of active products) with multiple ProcessInput filters applied can produce slow results if classification fields are not indexed. Custom search (SBQQ.ProductSearchPlugin) implementations introduce Apex execution time on top of the SOQL cost. Well-architected guided selling uses indexed fields for filter targets, limits the number of active ProcessInput questions to the minimum necessary, and benchmarks Custom search Apex against representative catalog sizes in a sandbox before production deployment.

- **Security** — `SBQQ__QuoteProcess__c` and `SBQQ__ProcessInput__c` are CPQ-managed objects that require field-level security configuration via CPQ permission sets. The mirror custom fields added to `SBQQ__ProcessInput__c` for classification filtering are custom fields and must be explicitly included in permission set field access grants for any user profile that runs the guided selling wizard. Omitting FLS on the mirror fields can cause read errors at runtime or silently prevent the answer from being written — which presents as the same symptom as a missing mirror field.

## Architectural Tradeoffs

**Standard vs. Enhanced vs. Custom search:** Standard search is the lowest-complexity option and handles the majority of use cases where each question maps to a single product classification dimension. Enhanced search adds the ability for reps to select multiple values per question (OR matching) at the cost of slightly more complex picklist field management. Custom search (Apex plugin) provides maximum flexibility — including external lookups, scoring, and complex eligibility rules — but introduces a developer dependency, Apex test coverage requirements, and upgrade risk with CPQ managed package updates. The decision should start with Standard, move to Enhanced only when multi-value eligibility is a genuine business requirement, and escalate to Custom only when Standard and Enhanced cannot express the required logic.

**Org-wide default Quote Process vs. pricebook-specific:** Setting a single Quote Process as the org-wide default is simpler to maintain — one wizard, one configuration. Pricebook-specific Quote Processes allow different wizard experiences for different sales contexts (e.g., a different set of questions for direct sales vs. partner sales, each with their own pricebook). The tradeoff: pricebook-specific configuration multiplies the number of Quote Processes and ProcessInput sets to maintain, and changes to shared classification fields require updates across multiple configurations.

**Native guided selling vs. Flow/OmniStudio product selection:** CPQ Guided Selling is integrated into the CPQ quote lifecycle — answers filter products that are then added through the CPQ configurator, respecting product rules, pricing, and bundle configuration. Flow or OmniStudio-based product selection bypasses this integration. The tradeoff is development flexibility vs. integration reliability. For any quote that will flow through CPQ approval, contracting, or revenue recognition, native guided selling is the architecturally correct choice.

## Anti-Patterns

1. **Skipping mirror field creation and relying on the wizard to surface errors** — When a ProcessInput's `SBQQ__SearchField__c` points to a field that does not exist on `SBQQ__ProcessInput__c`, CPQ does not raise a configuration error at setup time or at wizard runtime. The admin who skips mirror field creation will not discover the problem until reps report receiving unfiltered product lists. Fix: treat mirror field creation as the first and mandatory step in any guided selling setup involving custom Product2 fields.

2. **Using OmniStudio or custom LWC for product selection on CPQ quotes** — Building a custom product selection experience outside CPQ and then injecting products into a CPQ quote bypasses the CPQ calculation engine, product rules, bundle configurator, and pricing waterfall. The resulting quote lines are incomplete and cannot reliably pass through CPQ approval, contracting, or invoice generation. Fix: use `SBQQ__QuoteProcess__c` and `SBQQ__ProcessInput__c` for any guided product selection that feeds a CPQ-managed quote.

3. **Enabling Auto Select Product without validating pricebook coverage for all possible single-match products** — Auto Select fires silently when exactly one product matches. If that product lacks a pricebook entry in the quote's active pricebook, the auto-add generates a runtime error that the rep sees as an unexplained failure. Fix: confirm complete pricebook coverage for every product that could be the sole guided selling result before enabling Auto Select.

## Official Sources Used

- Salesforce CPQ Guided Selling Help — https://help.salesforce.com/s/articleView?id=sf.cpq_guided_selling.htm
- Create a Quote Process for Guided Selling — https://help.salesforce.com/s/articleView?id=sf.cpq_quote_process.htm
- CPQ Developer Guide: Product Configuration Initializer — https://developer.salesforce.com/docs/atlas.en-us.cpq_dev_guide.meta/cpq_dev_guide/cpq_dev_product_config_initializer.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
