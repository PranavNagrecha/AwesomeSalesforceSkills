# Well-Architected Notes — Commerce Analytics Data

## Relevant Pillars

- **Reliability** — Commerce analytics must be sourced from the correct authoritative system for each platform. B2C Commerce data from Business Manager is the system of record for storefront metrics; using the wrong surface produces missing or misleading data. Data freshness expectations (15–60 min lag in Business Manager) must be documented so stakeholders don't act on stale metrics.
- **Operational Excellence** — Analytics workflows should be repeatable and documented. Metric definitions (conversion rate numerator/denominator, abandonment threshold) must be agreed and recorded. Export processes for high-volume data (SFTP feed path) must be configured and tested before they are needed for operational reporting.
- **Security** — Business Manager access is role-controlled. Analysts should be granted read-only Business Manager roles (not Administrator roles) to access Reports & Dashboards. For B2B Commerce SOQL, ensure that profiles querying WebCart and CartItem have appropriate Field-Level Security and do not expose buyer PII beyond the minimum needed for the analytics task.

## Architectural Tradeoffs

**B2C Commerce: Business Manager Dashboards vs. Custom Data Pipeline**

Business Manager dashboards are zero-configuration and always available, but they are capped at 1,000 rows per export and cannot be extended or customized. For organizations with large catalogs or advanced analytics needs, the investment in an SFTP feed pipeline to a warehouse provides full row-level data at the cost of infrastructure setup and maintenance. The decision point is catalog/traffic size and whether the business needs row-level granularity beyond what the dashboard UI provides.

**B2B Commerce: SOQL vs. CRM Analytics Template**

SOQL queries against WebCart and CartItem are free (no additional license), flexible, and can be scheduled via Apex or Flow. However, they require developer effort to build, maintain, and surface via reports or dashboards. The CRM Analytics B2B Commerce template (`bi_template_b2bcommerce`) provides pre-built, productized dashboards with minimal setup — but requires a CRM Analytics license that may add significant cost. For organizations with straightforward abandonment or order metrics, SOQL is sufficient. For organizations wanting interactive, drill-down analytics across buyer behavior, CRM Analytics is the better investment.

## Anti-Patterns

1. **Using Standard Salesforce Reports for B2C Commerce Metrics** — B2C Commerce data is not in the CRM database. Building standard reports against Order, Account, or custom commerce objects will produce empty results. The correct surface is Business Manager Reports & Dashboards. This anti-pattern wastes developer time and creates a false belief that the integration is broken.

2. **Treating CSV Export as the B2C Data Feed** — Relying on manual CSV exports from Business Manager for operational reporting is fragile (manual process), limited (1,000 row cap), and unscalable. For any recurring analytics workflow, the SFTP Data Feed should be configured so that data is delivered automatically to the downstream system.

3. **Not Defining Abandonment Threshold Before Querying** — Writing a B2B WebCart abandonment query without first confirming the time threshold with the business produces a number that cannot be acted on. "Abandoned" means different things to different teams (24h for high-intent B2C; 7 days for long-cycle B2B). Agreeing on the definition before querying prevents rework and stakeholder confusion.

## Related Skills

Based on skill graph analysis:

- `architect/b2b-vs-b2c-architecture` — covers the platform selection decision; this skill handles analytics once the platform is in production
- `admin/crm-analytics-app-creation` — covers CRM Analytics app and dataset provisioning, relevant when the B2B Commerce CRM Analytics template needs setup
- `data/analytics-external-data` — covers the External Data API path for pushing SFTP feed data into CRM Analytics datasets

## Official Sources Used

- B2C Commerce Reports and Dashboards App — Trailhead: https://trailhead.salesforce.com/content/learn/modules/b2c-commerce-analytics
- B2C Commerce Historical Reports: Conversion — https://documentation.b2c.commercecloud.salesforce.com/DOC3/topic/com.demandware.dochelp/content/b2c_commerce/topics/site_development/b2c_conversion_reports.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- B2B Commerce on Core Object Reference (WebCart) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_webcart.htm
- CRM Analytics B2B Commerce Template — https://help.salesforce.com/s/articleView?id=sf.bi_integrate_b2bcommerce.htm&type=5
