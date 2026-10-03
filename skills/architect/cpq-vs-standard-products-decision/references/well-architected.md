# Well-Architected Notes — CPQ vs Standard Products Decision

## Relevant Pillars

- **Scalability** — The choice between CPQ and standard Products directly affects how well the quoting process scales with catalog growth. Standard objects handle small catalogs efficiently but require increasing custom code as product complexity grows. CPQ provides a configuration-driven scaling model where new bundles and pricing rules are added declaratively rather than through code changes.

- **Reliability** — Pricing accuracy is a reliability concern. Custom pricing logic built on standard objects introduces risk of calculation errors as rules multiply. CPQ's tested pricing engine reduces the surface area for pricing bugs. However, CPQ's managed package dependency introduces a different reliability risk: package upgrades can break custom automations if not tested.

- **Operational Excellence** — The operational burden differs significantly between approaches. Standard objects with custom enhancements require developer involvement for pricing rule changes. CPQ allows business users (deal desk, revenue operations) to manage pricing rules, discount schedules, and approval chains without developer intervention, reducing time-to-change for pricing updates.

- **Security** — Both approaches inherit Salesforce's object-level and field-level security model. CPQ adds managed package objects that need their own permission set configuration. Organizations must ensure CPQ object permissions (SBQQ__Quote__c, SBQQ__QuoteLine__c) are properly restricted so that only authorized users can view or edit pricing, contracted rates, and discount schedules.

## Architectural Tradeoffs

The core tradeoff is **cost vs capability**: standard Products and Pricebooks are free but limited in native functionality, while CPQ adds significant per-user licensing cost but delivers configuration-driven pricing, bundling, and approval capabilities that are expensive to replicate in custom code.

A secondary tradeoff is **simplicity vs flexibility**: standard objects are simpler to understand, customize, and maintain for small catalogs, but CPQ provides a structured framework that prevents ad-hoc pricing logic from accumulating as technical debt.

A third tradeoff is **vendor dependency vs control**: CPQ ties the org to a managed package with its own release cycle, upgrade requirements, and potential breaking changes. Standard objects give the team full control but require them to build and maintain everything.

## Anti-Patterns

1. **Over-engineering standard objects to avoid CPQ licensing**: Building custom bundle logic, pricing calculators, and guided selling flows on standard objects when the requirements clearly call for CPQ. This creates fragile custom code that costs more to maintain than CPQ licensing within 12-18 months (UNVERIFIED (2026-10-03): practitioner estimate), violating the Operational Excellence pillar.

2. **Adopting CPQ without a requirements analysis** — Purchasing CPQ licenses because it is the "enterprise standard" without confirming that the quoting workflow actually needs CPQ-specific features. This wastes budget on unnecessary licensing and adds managed package complexity to the org, violating the Scalability pillar by introducing unneeded dependencies.

3. **Ignoring the data model split when migrating** — Starting with standard quoting and migrating to CPQ without planning for the object model change (Quote/QuoteLineItem to SBQQ__Quote__c/SBQQ__QuoteLine__c). This creates a split data architecture that degrades reporting reliability and integration consistency, violating the Reliability pillar.

## Official Sources Used

Read for this revision (2026-10-03):

- Salesforce CPQ Developer Guide, Version 67.0 (Summer '26): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/cpq_developer_guide.pdf. Chapter 1 lifecycle notice (available for existing customers, no new feature development, support for the contract term, licences can be added and subscriptions renewed, Revenue Cloud recommended); CPQ API models (`SBQQ__Quote__c`, `SBQQ__QuoteLine__c`); Generate Quote Document API; Disable CPQ Triggers in Apex; Advanced Approvals as a separate package.
- Salesforce Object Reference, Version 67.0: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf. PricebookEntry (standard price first, one entry per price and currency, `UseStandardPrice`); ProductRelatedComponent and ProductSellingModel access rules; Quote; QuoteLineItem; OpportunityLineItemSchedule.
- Navigating the Future of Salesforce CPQ: Product End of Sale (Not End of Life), salesforce.com, 10 July 2026: https://www.salesforce.com/sales/cpq/end-of-life/. End of sale, not end of life; no new licences for new customers; existing customers can add users, renew, and receive support; no forced migration; investment shifted to Revenue Cloud Advanced. States no end-of-sale date.
- Salesforce Well-Architected: Easy > Intentional: https://architect.salesforce.com/docs/architect/well-architected/guide/intentional.html (a direct fetch does not return the guide page; read via Wayback snapshot 2026-04-04). "Decision records show calculation for near- and long-term costs when choosing to build or buy solutions"; build-buy spectrum; prefer standard functionality.
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (Wayback snapshot 2026-06-16). Trusted, Easy, Adaptable framing.

Listed in the original version; Salesforce Help does not fetch, so these were not re-read and no claim in this revision rests on them alone:

- Salesforce CPQ Documentation — https://help.salesforce.com/s/articleView?id=sf.cpq_parent.htm
- Salesforce Products and Pricebooks — https://help.salesforce.com/s/articleView?id=sf.products_landing_page.htm
