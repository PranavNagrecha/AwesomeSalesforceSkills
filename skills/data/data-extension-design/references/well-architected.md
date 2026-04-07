# Well-Architected Notes — Data Extension Design

## Relevant Pillars

- **Performance** — DE schema design directly controls query performance. Non-PK field access without indexes causes full table scans and Automation Studio timeouts. Column count above ~200 degrades all query operations. Performance must be designed upfront; retrofitting indexes requires a Support ticket.
- **Reliability** — Data retention misconfiguration (ResetRetentionPeriodOnImport defaulting off) causes silent data loss that only surfaces when a send audience is empty. Primary key immutability means a design error requires DE recreation — a recovery operation that risks data loss if not managed carefully.
- **Security** — Sendable DEs contain subscriber PII (email addresses, names, identifiers). Data retention settings control how long PII persists. Keeping data longer than necessary increases breach exposure surface. Retention settings should reflect the org's data minimization policy.
- **Scalability** — DEs designed with poor key selection or wide column counts become bottlenecks as data volume grows. Composite PKs that match the business key enable upsert-based import patterns that scale without row count explosion. Vertical DE decomposition keeps individual DEs lean.
- **Operational Excellence** — PK immutability, indexing constraints, and retention clock behavior create operational risk for teams that do not document their DE design decisions. A DE specification document (captured via the template) reduces recurring incidents caused by undocumented design choices.

## Architectural Tradeoffs

**Sendable DE — SubscriberKey vs. Email Address mapping:**
Mapping the Send Relationship to Email Address is simpler (no extra field needed if the DE already has EmailAddress) but causes subscriber resolution inconsistencies when subscribers have multiple addresses or change addresses. Mapping to SubscriberKey requires the DE to carry the SubscriberKey field but produces stable, deduplicated sends. Always prefer SubscriberKey unless the org's All Subscribers list was set up before SubscriberKey existed and migration has not occurred.

**Single-field PK vs. composite PK:**
A single surrogate PK (like a GUID from the source system) is simple but breaks upsert accuracy if the source regenerates GUIDs on re-export. A composite PK built from business keys (CustomerKey + ProductSKU + EventDate) is more complex but enables reliable upsert and prevents unbounded row growth. Choose the composite PK when the source system does not guarantee stable surrogate keys.

**Wide DE vs. decomposed DEs:**
A single wide DE simplifies AMPscript personalization (all attributes in one Lookup) but creates performance risk at scale and makes it harder to apply different retention policies to different data. Decomposed DEs (core identity, segment membership, product interests) allow fine-grained retention, better query performance, and independent lifecycle management. The tradeoff is more complex SQL JOINs in query activities.

**Row-based retention vs. period-based retention:**
Row-based retention is appropriate for DEs where individual rows have different ages (transactional or event data). Period-based retention is appropriate for DEs where all rows should be cleared on a schedule (e.g., a staging DE that is fully rebuilt each run). Mixing these incorrectly — using period-based on a transactional DE — deletes all data at once, which may empty the DE mid-automation.

## Anti-Patterns

1. **"Golden Record" Wide DE** — Consolidating all customer attributes into a single DE exceeding 200 columns. This creates a performance bottleneck that worsens as the org grows, cannot be resolved without recreating the DE, and forces a single retention policy on data with different business lifespans. Design for decomposition from day one.

2. **Ignoring Data Retention Until Go-Live** — Configuring data retention as an afterthought after the DE is already populated means the first retention sweep may delete data that is still needed. Data retention must be designed at DE creation time, with ResetRetentionPeriodOnImport explicitly set based on the import pattern.

3. **Relying on Email Address for Subscriber Identity** — Using EmailAddress as the PK or the Send Relationship mapping creates a fragile identity model. Email addresses change; subscribers appear in All Subscribers multiple times; suppression and preference data is split across duplicates. SubscriberKey is the platform-correct identity anchor.

## Official Sources Used

- Salesforce Help — Create a Data Extension: https://help.salesforce.com/s/articleView?id=sf.mc_es_create_data_extension.htm&type=5
- Salesforce Developer — Create a Sendable Data Extension: https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/creating-sendable-data-extensions.html
- Salesforce Help — Data Extension Relationships: https://help.salesforce.com/s/articleView?id=sf.mc_co_data_relationships.htm&type=5
- Salesforce Help — Data Extension Index: https://help.salesforce.com/s/articleView?id=sf.mc_es_data_extension_index.htm&type=5
- Salesforce Object Reference (Data Extension Object): https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/data-extension-object.html
- Salesforce Well-Architected Overview: https://architect.salesforce.com/well-architected/overview
