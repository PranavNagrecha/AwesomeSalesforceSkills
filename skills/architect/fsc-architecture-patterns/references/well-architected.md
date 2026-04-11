# Well-Architected Notes — FSC Architecture Patterns

## Relevant Pillars

- **Security** — The dominant pillar for FSC architecture. Compliant Data Sharing exists specifically to enforce the financial services principle of minimum necessary access — advisors see only the financial records where they have a documented client relationship. OWD configuration, CDS activation state, and external-user sharing must each be validated independently. Over-sharing financial account data is not just a Salesforce misconfiguration; it is a regulatory compliance failure under FINRA, SEC, and similar frameworks.

- **Scalability** — FSC orgs accumulate `FinancialAccount`, `FinancialHolding`, and `FinancialGoal` records that grow with client acquisition and product expansion. The household rollup batch, SOQL queries on the book-of-business page, and CDS sharing recalculations all have volume-sensitive performance characteristics. Architecture must plan for 3–5 year record volume growth, not just current state.

- **Reliability** — FSC orgs integrate with core banking systems, market data feeds, and document management platforms that have independent availability profiles. Architecture must ensure that unavailability of any external system does not block advisors from reading FSC data or completing client service tasks. Event-driven integration patterns (Platform Events, CDC) and circuit-breaker patterns for synchronous callouts are reliability requirements, not optional enhancements.

- **Operational Excellence** — Compliance teams need to audit CDS configurations, rollup batch results, and integration feed health without developer involvement. Operational runbooks for rollup batch monitoring, CDS audit queries, and integration failure alerting are first-class architecture deliverables, not post-go-live additions.

---

## Architectural Tradeoffs

**Managed-package FSC vs. platform-native FSC:** Managed-package provides a stable, tested object model for orgs that implemented FSC before Winter '23 and have significant existing data. Migration to platform-native is a formal data migration project, not an in-place upgrade. For greenfield implementations after Winter '23, platform-native eliminates namespace overhead and CI/CD friction at no functional cost.

**Compliant Data Sharing vs. criteria-based sharing rules:** CDS provides relationship-driven access control with an audit trail (`FinancialAccountRole` as the relationship record). Criteria-based sharing rules are simpler to configure but cannot model advisor-client relationships as first-class entities and do not automatically revoke access when relationships end. For any regulated FSC org, CDS is the architecturally correct choice despite its higher initial setup cost.

**Real-time core banking integration vs. batch feeds:** Real-time synchronous callouts from Salesforce to core banking systems are architecturally fragile: callout limits, banking system latency, and availability coupling all make them unsuitable for page-load or record-save integration patterns. Batch or event-driven feeds trade data freshness for reliability and are the correct architecture for all but the most specific real-time requirements (e.g., payment initiation confirmation).

---

## Anti-Patterns

1. **Broad CDS share sets that replicate over-sharing** — Configuring a CDS share set that grants all users at a branch visibility to all `FinancialAccount` records assigned to that branch replicates the same over-sharing problem that criteria-based rules produce. CDS is intended to enforce advisor-relationship-based access, not branch-level access. A share set that grants access at the branch or team level rather than the individual advisor-client relationship level defeats the compliance purpose of CDS.

2. **Synchronous callouts from FSC record save events to core banking** — Placing a synchronous callout to a core banking API inside an Apex trigger `after insert` or `after update` on `FinancialAccount` couples the Salesforce save transaction to external system availability and latency. If the banking system is slow or unavailable, every Salesforce record save that touches a financial account fails or hangs. Decouple these integrations using Platform Events published from the trigger with an asynchronous subscriber handling the callout.

3. **Deferring the managed-package vs. platform-native decision** — Treating the data model selection as a detail to be resolved later rather than a Day 1 architecture decision creates a design debt that grows with every sprint. Integration field mappings, CI/CD pipeline configuration, Apex classes, Flows, and LWC components all branch on this decision. Resolving it after significant development is underway requires retroactive rework of every artifact that references `FinServ__` objects.

---

## Official Sources Used

- Financial Services Cloud Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.financial_services_cloud_object_reference.meta/financial_services_cloud_object_reference/intro.htm
- Compliant Data Sharing — Financial Services Cloud Help (Salesforce Help) — https://help.salesforce.com/s/articleView?id=sf.fsc_compliant_data_sharing.htm
- Financial Services Cloud Data Model Gallery — https://architect.salesforce.com/diagrams/framework/financial-services-cloud-data-model
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Integration Patterns — Salesforce Architects — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
