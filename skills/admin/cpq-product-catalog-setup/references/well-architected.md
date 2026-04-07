# Well-Architected Notes — CPQ Product Catalog Setup

## Relevant Pillars

- **Operational Excellence** — CPQ product catalog configuration is a high-maintenance surface. Product rules, bundle structures, and configuration attributes must be documented so future admins can understand and modify the catalog without breaking existing quote logic. Undocumented sequence numbers and unexplained rule conditions become technical debt that blocks catalog evolution.
- **Performance Efficiency** — Deep bundle nesting and large unconstrained option lists directly degrade CPQ configurator performance. Filter rules reduce the option set rendered at configurator open, lowering page load time. Performance must be validated with realistic data volume before go-live.
- **Security** — CPQ product access is controlled via standard Salesforce object permissions on `SBQQ__Product2__c`, `SBQQ__ProductOption__c`, and `SBQQ__ProductRule__c`. Ensure CPQ permission sets are correctly applied so non-admin users cannot modify product rule records. Product catalog changes should go through a change management process, not be made directly in production.
- **Scalability** — Catalog design decisions made early (nesting depth, option count per bundle, rule count) become structural constraints. Over-bundling (creating one mega-bundle rather than smaller targeted bundles) creates a catalog that is slow to open and difficult to maintain. Prefer smaller, focused bundles composable by reps over one large universal bundle.
- **Reliability** — Validation rules provide deterministic quote-save behavior. Selection rules can introduce non-determinism if sequencing is incorrect or if rule conditions overlap. Test all rule permutations with a written test matrix before release.

## Architectural Tradeoffs

### Bundle Granularity vs. Configuration Flexibility

Smaller, focused bundles are faster to configure and easier to maintain. However, if every product combination requires a separate bundle, catalog maintenance becomes expensive. Configuration Attributes with Filter rules allow a single bundle to behave differently based on header choices, reducing bundle count while preserving flexibility. The tradeoff: filter-rule-driven bundles are more complex to test and debug than simple bundles with fixed option sets.

### Validation Rules vs. Required Product Options

Validation rules are flexible (they can evaluate complex multi-field conditions) but add server-side overhead on every save attempt and surface errors only post-interaction. Required Product Options enforce constraints at the UI layer before save, providing a better rep experience. Use Required options for simple "always include" constraints; reserve Validation rules for complex cross-option logic.

### API-Driven Quote Construction vs. Configurator-Driven Quoting

Teams using the SBQQ QuoteAPI to build quotes programmatically bypass Filter rule evaluation. If the business requires both UI-configured and API-configured quotes, Validation rules must be duplicated to cover both paths. Designing for API compatibility from the start avoids retrofitting Validation rules later.

## Anti-Patterns

1. **Over-relying on Validation Rules for Required Components** — Using Validation rules to enforce options that should simply be marked Required on the Product Option record adds unnecessary processing on every save and provides a worse rep experience (error appears only after save, not during selection). Set `SBQQ__Required__c = true` on the Product Option instead.

2. **Deep Bundle Nesting Without Performance Testing** — Building 4-level nested bundles without testing configurator load time with realistic data volumes leads to production performance crises. CPQ's SOQL cost at configurator open scales with nesting depth and catalog size. Always load-test with representative data before go-live.

3. **Undocumented Product Rule Sequences** — Product Rules that have unexplained sequence numbers and no documentation of their intended interaction with other rules become unmaintainable. When the catalog evolves and new rules are added, undocumented sequences lead to rule conflicts or silent logic failures.

## Official Sources Used

- Salesforce CPQ Product Bundles — https://help.salesforce.com/s/articleView?id=sf.cpq_product_bundles.htm
- Salesforce CPQ Product Rules — https://help.salesforce.com/s/articleView?id=sf.cpq_product_rules.htm
- Salesforce CPQ Product Rule Guidelines — https://help.salesforce.com/s/articleView?id=sf.cpq_product_rule_guidelines.htm
- Salesforce CPQ Configuration Attributes — https://help.salesforce.com/s/articleView?id=sf.cpq_configuration_attributes.htm
- Salesforce CPQ Filter Rules and Dynamic Bundles — https://help.salesforce.com/s/articleView?id=sf.cpq_filter_rules.htm
- Salesforce CPQ Developer Guide — Configure Product Bundles — https://developer.salesforce.com/docs/atlas.en-us.cpq_dev_guide.meta/cpq_dev_guide/cpq_api_configure_product_bundles.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
