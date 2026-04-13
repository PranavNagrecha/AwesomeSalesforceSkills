# Well-Architected Notes — Industries Communications Setup

## Relevant Pillars

- **Security** — Communications Cloud permission sets gate access to EPC configuration screens and catalog record visibility. A misconfigured permission set model results in catalog data being readable by unauthorized users or, conversely, configuration screens being inaccessible to implementing admins. Every org should enforce least-privilege permission set assignment: `Vlocity_Communications_User` for subscribers, `Vlocity_Communications_Admin` only for implementing admins. OmniStudio permission sets for order capture UIs must also be scoped to the correct user populations.

- **Operational Excellence** — The setup sequence for Communications Cloud is strictly ordered: package install → permission set assignment → EPC catalog configuration → order decomposition rules → contract lifecycle setup. Deviating from this sequence (e.g., configuring order decomposition rules before EPC catalog is complete) produces silent failures that are difficult to trace. Well-Architected implementations document the setup sequence, gate each phase on explicit validation steps, and use the check script (`check_industries_communications_setup.py`) to validate each layer before proceeding.

- **Reliability** — Order decomposition is the highest-reliability requirement in Communications Cloud. A failed decomposition means a subscriber places an order that records as successful but never reaches the provisioning system. Reliable implementations add explicit decomposition outcome monitoring: check for commercial orders with no corresponding technical order records within a time window and alert on any gaps. The Account RecordType hierarchy also contributes to reliability — unfiltered Account queries produce intermittent incorrect behavior that is hard to reproduce and trace.

- **Scalability** — EPC catalog structure has a direct impact on scalability. Deeply nested bundle hierarchies (bundles within bundles with many child items) increase decomposition processing time and can hit governor limits for complex orders. Flat catalog designs — where bundles reference atomic Product Offerings directly without intermediate bundle layers — decompose faster and are easier to maintain. Product Specification reuse (one Specification, many Offerings) also reduces catalog size and simplifies updates when service terms change.

- **Performance** — The most common performance issue in Communications Cloud setups is unfiltered Account queries in order processing logic. A query without `RecordType.DeveloperName` filtering returns all account subtypes, producing unnecessarily large result sets and incorrect processing. SOQL-level filtering (not Apex-level filtering after retrieval) is required to keep query performance within limits at high subscriber volumes.

## Architectural Tradeoffs

**EPC bundle depth vs. decomposition performance:** Deeply nested bundles (bundle contains a sub-bundle which contains atomic offerings) map more naturally to complex telecom product hierarchies but increase decomposition processing time. Flat bundles (bundle directly references atomic offerings) are faster to decompose but require more explicit bundle definitions. At scale, prefer flat bundles and use Product Specification reuse to manage catalog complexity.

**Person Accounts vs. Consumer Account RecordType for B2C:** For consumer (B2C) subscribers, Communications Cloud supports two models: Person Accounts (where Account and Contact are merged) or standard Account with `Consumer_Account` RecordType. Person Accounts simplify some subscriber identity modeling but add complexity to all Apex, SOQL, and Flow logic that assumes separate Account and Contact objects. Standard Account with Consumer RecordType is the more architecturally predictable choice unless there is a specific requirement for Person Accounts from another installed product.

**Industries Order Management scope vs. external fulfillment systems:** Communications Cloud's Industries Order Management is designed to generate technical orders and trigger provisioning. For orgs with existing external fulfillment systems (e.g., legacy OSS/BSS), a common decision is whether to use Industries Order Management as the orchestration layer calling external systems via integration, or to use it only for commercial order capture and delegate all technical order processing to the external system. The former gives more visibility; the latter may reduce implementation complexity if the external system is already the provisioning authority.

## Anti-Patterns

1. **Treating Communications Cloud as a standard CRM with Industries add-ons** — Organizations that configure Communications Cloud like a standard Salesforce Sales Cloud org (direct Product2 use, standard Contract workflow, unfiltered Account queries) will encounter silent failures at every integration point. The EPC, Industries Order Management decomposition engine, and contract lifecycle flows are all mandatory layers, not optional enhancements. A well-architected Communications Cloud implementation treats the EPC as the canonical source for all product data and the Industries Order Management as the mandatory order processing layer.

2. **Bypassing EPC for speed during early implementation** — Implementation teams under time pressure often create test products directly in Product2, intending to "add EPC later." In practice, EPC configuration cannot be retrofitted onto existing orders or product records without data migration. Any order placed against a non-EPC product cannot be decomposed after the fact. Well-Architected implementations configure at least a minimal EPC catalog before placing any orders, even in sandbox environments.

3. **Conflating Industries Order Management with Salesforce Order Management** — These are separate platforms with separate object models. Using Commerce Order Management APIs or objects in a Communications Cloud integration produces errors that are difficult to diagnose because the failure mode is "object not found" rather than "wrong platform." Architecture reviews for Communications Cloud integrations must explicitly confirm which order management platform is in scope and which APIs and objects apply.

## Official Sources Used

- Industries Data Models for Communications — https://help.salesforce.com/s/articleView?id=ind.communications_data_model.htm
- Communications Cloud Data Model Gallery — https://help.salesforce.com/s/articleView?id=ind.communications_data_model_gallery.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
