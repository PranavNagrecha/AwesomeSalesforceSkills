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

Read for this revision (2026-10-03):

- Data Cloud Developer Guide, Data 360 Architecture: https://developer.salesforce.com/docs/data/data-cloud-dev/guide/dc-architecture.html. DLO to DMO mapping on the C360 Data Model; identity resolution (match and reconciliation rules, link tables, unified profile); segmentation; calculated insights (batch and streaming); activations; Data Shares; zero copy connectors; reporting through Tableau, Power BI, and the Data 360 JDBC driver; SOQL, SQL, and vector or hybrid query; digital wallet credit consumption.
- Data Cloud Developer Guide, Data 360 Features Brief Overview: https://developer.salesforce.com/docs/data/data-cloud-dev/guide/dc-features-overview.html. Harmonization and identity purpose; capabilities available "if you have purchased Segmentation and Activation".
- Salesforce Architects, Data 360 Architecture: https://architect.salesforce.com/docs/architect/fundamentals/guide/data-360-architecture. Zero Copy federation with Snowflake, Databricks, BigQuery, and Redshift; federated data represented as DLOs; incremental batch processing that reduces resource consumption; batch and streaming calculated insights; data spaces as isolation containers. (Fetched directly on 2026-10-03; the earlier note that architect.salesforce.com returns 403 applies to browser-style fetches only.)
- Data Cloud Integration Guide (navigation): https://developer.salesforce.com/docs/data/data-cloud-int/guide. Data federation setup pages for Snowflake, Databricks, and Redshift.
- SOQL and SOSL Reference, Version 66.0 (Spring '26), SOQL Object Limits and Limitations, Data 360 Objects: local corpus `knowledge/imports/salesforce-soql-sosl.md`. 12 MB result limit; no currency fields in aggregate queries; calculated insight objects not queryable; Id restrictions.
- CRM Analytics REST API Developer Guide (Spring '26): local corpus `knowledge/imports/salesforce-analytics-rest-api.md`. "Convert Data 360 data model objects to datasets"; replicated datasets (connected objects) are caches that cannot be visualized directly; schedules for dataflows, recipes, and connection syncs.
- Salesforce Well-Architected: Easy > Intentional: https://architect.salesforce.com/docs/architect/well-architected/guide/intentional.html (a direct fetch does not return the guide page; read via Wayback snapshot 2026-04-04). Use prebuilt data models so capabilities are "defined only once" with "a single source of truth"; decision records with near- and long-term costs.

Listed in the original version and not re-read for this revision (Salesforce Help does not fetch; the remaining Architects pages were not opened); no claim in this revision rests on them alone:

- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (read via Wayback snapshot 2026-06-16)
- Data 360 Integration Patterns and Practices (Salesforce Architects): https://architect.salesforce.com/docs/architect/fundamentals/guide/data360_integration_patterns_and_practices
- Connect CRM Analytics to Salesforce Data Cloud (Salesforce Help): https://help.salesforce.com/s/articleView?id=sf.bi_direct_data_for_cdp.htm&type=5
- Integration Patterns (Salesforce Architects): https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
