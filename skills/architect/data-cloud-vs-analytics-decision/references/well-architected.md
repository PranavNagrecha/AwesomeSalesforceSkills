# Well-Architected Notes — Data Cloud vs CRM Analytics Decision

## Relevant Pillars

- **Performance** — End-to-end freshness is determined by the slowest hop across ingestion, harmonization, identity resolution, and CRM Analytics consumption. Architecture decisions must state acceptable lag per persona, not assume “real time” because a UI refreshes quickly.
- **Scalability** — Data Cloud is built to absorb high-volume, multi-source streams and grow with additional DMO mappings and segments. CRM Analytics capacity planning focuses on licensed users, dataset cardinality, and query concurrency. Splitting concerns keeps each product scaled on its own dimension.
- **Operational Excellence** — Two operational teams often emerge: a data platform team for Data Cloud pipelines and identity, and an insights team for CRM Analytics content. The decision record should name owners, runbooks, and monitoring for each layer instead of collapsing them.
- **Security** — Both products honor Salesforce administration patterns, but cross-cloud harmonization introduces new sensitivity classes (behavioral events, hashed identifiers). Decisions should state which layer enforces consent and row-level access for each dataset class.

## Architectural Tradeoffs

- **Single-vendor simplicity vs best-of-breed BI** — Staying on CRM Analytics plus Data Cloud reduces integration sprawl for Salesforce-centric orgs; adding external BI may still be valid for enterprise standards—see `architect/crm-analytics-vs-tableau-decision` for that fork.
- **Harmonize first vs report first** — Reporting first on CRM objects is faster but encodes assumptions that are expensive to unwind when external channels arrive. Harmonize first when activation or cross-channel truth is on the roadmap within two release cycles.
- **Centralized identity vs federated analytics** — Centralizing identity in Data Cloud improves segment quality but concentrates operational risk; document backup reconciliation processes and manual run limits from platform guidance.

## Anti-Patterns

1. **Duplicate golden record** — Maintaining one “customer truth” in Data Cloud and another in CRM Analytics datasets without synchronization guarantees conflicting KPIs and compliance exposure.
2. **Analytics-led ingestion** — Using CRM Analytics recipes as the primary tool to pull large external volumes into Salesforce-shaped tables instead of modeling in Data Cloud overloads CRM storage and sidesteps native harmonization.
3. **Implicit DMO readiness** — Connecting CRM Analytics to Data Cloud entities before Contact Point and Party Identification mappings are validated yields attractive dashboards with hollow coverage on real individuals.

## Official Sources Used

- Salesforce Well-Architected Overview — architecture quality framing for tradeoff documentation
- Data 360 Architecture (Salesforce Architects) — customer data platform layering and Data Cloud role in Data 360
- Data 360 Integration Patterns and Practices (Salesforce Architects) — integration boundaries between Salesforce clouds and external systems
- Connect CRM Analytics to Salesforce Data Cloud (Salesforce Help) — Direct Data connectivity concepts for analytics on Data Cloud
- Integration Patterns (Salesforce Architects) — synchronization vs remote integration vocabulary for documenting data movement contracts

Full URLs (for authors and reviewers):

- https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- https://architect.salesforce.com/docs/architect/fundamentals/guide/data-360-architecture
- https://architect.salesforce.com/docs/architect/fundamentals/guide/data360_integration_patterns_and_practices
- https://help.salesforce.com/s/articleView?id=sf.bi_direct_data_for_cdp.htm&type=5
- https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
