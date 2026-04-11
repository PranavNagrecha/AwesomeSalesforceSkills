# Well-Architected Notes — Data Cloud Data Streams

## Relevant Pillars

- **Trustworthy** — Identity resolution rulesets merge records based on explicit match rules. Incorrect or incomplete DMO mappings (e.g., missing Contact Point mappings) result in silently incomplete unified profiles, breaking downstream trust in segmentation and activation data. Every mapping decision must be auditable and documented.
- **Well-Integrated** — Data streams are the integration boundary between external systems and Data Cloud's harmonized data model. Integration design must account for connector type, ingestion mode (append vs. upsert), deletion handling gaps in the Ingestion API, and the hard limit of 2 identity resolution rulesets per org.
- **Adaptable** — Calculated Insights and DMO mappings must be designed to accommodate new data sources without breaking existing rulesets. The 2-ruleset limit creates a design constraint that forces deliberate planning: rulesets must be scoped broadly enough to serve future streams, not just current ones.

## Architectural Tradeoffs

**Ingestion API (real-time) vs. Connector (batch):** The Ingestion API delivers lower-latency data arrival but does not support deletions and requires a connected app OAuth setup. CRM and cloud storage connectors deliver data in scheduled batches but have richer built-in schema discovery and support full refresh semantics. Choose the Ingestion API only when latency is a stated business requirement, not by default.

**Single broad ruleset vs. multiple narrow rulesets:** The 2-ruleset limit forces a design choice. A single ruleset with multiple match rules (email + phone) covers more match scenarios but may produce more false-positive merges than two separate rulesets with single match rules each. For most implementations, a single ruleset with email as the primary match rule and phone as a secondary rule is the right balance of coverage and merge precision.

**Calculated Insights vs. real-time segment filters:** Calculated Insights add a batch-processing lag to segmentation. For time-sensitive use cases (e.g., "has opened an email in the last hour"), Streaming Insights via the SDK are required. For most marketing segmentation use cases (RFM scoring, lifetime value tiers), the batch lag of Calculated Insights is acceptable and simplifies the data model considerably.

## Anti-Patterns

1. **Mapping only to Individual DMO** — Connecting data streams without Contact Point or Party Identification DMO mappings leaves data in a half-integrated state: records appear in Data Cloud but cannot participate in identity resolution or produce Unified Individual profiles. This is the leading cause of "identity resolution is unavailable" support cases.

2. **Treating the Ingestion API as a full-featured ETL pipeline** — The Ingestion API is an append/upsert-only endpoint. Teams that use it as a two-way sync mechanism (expecting it to handle deletions) will accumulate stale records in their DLOs over time, corrupting metrics and segmentation counts. Any deletion requirement must be addressed via a separate mechanism.

3. **Ignoring the 2-ruleset org limit in multi-BU implementations** — Designing each BU's data architecture in isolation, with each BU expecting its own identity resolution ruleset, will result in blocked implementations when the third BU onboards. Identity resolution architecture must be planned at the org level, not the BU level.

## Official Sources Used

- Data Cloud Data Streams (Salesforce Help) — https://help.salesforce.com/s/articleView?id=sf.c360_a_data_streams.htm&type=5
- Data Cloud Limits and Guidelines (Salesforce Help) — https://help.salesforce.com/s/articleView?id=sf.c360_a_limits_and_guidelines.htm&type=5
- Data Cloud Real-Time Ingestion API Reference (Salesforce Developer) — https://developer.salesforce.com/docs/atlas.en-us.c360a_api.meta/c360a_api/c360a_api_ingestion_api.htm
- Data Cloud Data Model Object (DMO) Reference (Salesforce Developer) — https://developer.salesforce.com/docs/atlas.en-us.c360a_api.meta/c360a_api/c360a_api_data_model.htm
- Salesforce Well-Architected Framework — https://architect.salesforce.com/well-architected/overview
