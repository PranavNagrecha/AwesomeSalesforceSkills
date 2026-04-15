# Well-Architected Notes — Data Cloud Calculated Insights

## Relevant Pillars

- **Performance** — Calculated Insight SQL runs against DMO data on every refresh cycle. Unoptimized queries (missing WHERE filters, full-table scans on large fact DMOs, unnecessary cross-joins) slow execution toward the 2-hour timeout and delay segment freshness downstream. SQL must be written with execution cost in mind, not just correctness.

- **Reliability** — The immutability of measure API names and data types after creation means a design mistake creates an operational incident: the insight must be deleted and recreated. Reliability in this domain is achieved through upfront design rigor, not runtime error handling. Additionally, insights that time out leave downstream segments stale without surfacing an obvious alert — monitoring run status is part of operational reliability.

- **Adaptability** — Because only additive changes are allowed post-creation, insight schemas must be designed to accommodate likely future metric needs. Adding new measures to an existing insight is safe; changing existing ones is not. Designing with future extensibility reduces the number of delete-and-recreate cycles an org will need over its lifecycle.

---

## Architectural Tradeoffs

**Calculated Insights vs. Segment Filter Conditions**

Segment filter conditions evaluated at run time (directly against DMO data) are more flexible — they can be changed without creating a schema artifact. But they do not persist as named metrics, cannot be referenced across multiple segments without duplicating the logic, and cannot be activated as fields on the Unified Profile. Calculated Insights introduce scheduling lag but produce persistent, reusable, activatable metric fields. For any metric that will be used in more than one segment, or that needs to appear as an activation field, a Calculated Insight is the right choice.

**Calculated Insights vs. Streaming Insights**

Streaming Insights offer near-real-time latency for supported sources (Mobile/Web SDK, MCP Personalization). But they cannot aggregate historical data, cannot join Unified Profiles, and cannot feed the Segment Builder. Calculated Insights are less fresh (minimum 6-hour cadence) but are the only mechanism for persistent, profile-attached, segment-filterable metrics. Most production Data Cloud orgs need both: Streaming Insights for real-time triggers, Calculated Insights for audience-building metrics. They should not be treated as alternatives to each other — they serve different pipeline stages.

**Insight Governance at Scale**

The 300-insight org limit creates a finite shared resource. Without governance, orgs accumulate stale insights that consume capacity. The Well-Architected principle of operational excellence requires a lifecycle policy: insights tied to campaigns should be decommissioned at campaign end, insights should be named to encode their owning team or campaign, and an insight count threshold (e.g., alert at 250) should trigger a governance review before the limit is reached.

---

## Anti-Patterns

1. **Creating Insights Without a Finalized API Name Design** — Saving a Calculated Insight with a placeholder, test, or incorrectly typed measure API name requires a full delete-and-recreate to fix. This is not a cosmetic issue: it destroys historical data and breaks any downstream segment or activation that references the old name. The correct pattern is to complete a written design review of all API names, types, and rollup behaviors before the insight is saved for the first time.

2. **Using Streaming Insights for Audience Segmentation** — Streaming Insights are not available in Segment Builder. Building a personalization strategy that assumes Streaming Insights can feed batch audience segments creates a broken architecture that requires a full rebuild when the constraint is discovered. The correct pattern is to use Calculated Insights for all metrics that will be used as segment filter conditions, and to restrict Streaming Insights to real-time trigger scenarios only.

3. **Scheduling All Insights at 24 Hours Without Freshness Analysis** — Defaulting every insight to a 24-hour schedule without analyzing the downstream freshness requirement produces segments that can be up to 48 hours stale in the worst case. For active campaign use cases, this creates audience lag that undermines campaign effectiveness. The correct pattern is to match the schedule cadence to the downstream SLA: 6h for same-day campaigns, 12h for daily batch activations, 24h for weekly reporting metrics.

---

## Official Sources Used

- Calculated Insights (Salesforce Help) — https://help.salesforce.com/s/articleView?id=sf.c360_a_calculated_insights.htm
- Create a Calculated Insight Using SQL (Salesforce Help) — https://help.salesforce.com/s/articleView?id=sf.c360_a_get_started_with_calculated_insights.htm
- Calculated Insights Processing and Retention Times (Salesforce Help) — https://help.salesforce.com/s/articleView?id=sf.c360_a_processing_calculated_insights.htm
- Streaming Insights and Limits (Salesforce Help) — https://help.salesforce.com/s/articleView?id=sf.c360_a_streaming_insight_data_action_limits.htm
- How Are Calculated, Streaming, and Real-Time Insights Different (Salesforce Help) — https://help.salesforce.com/s/articleView?id=sf.c360_a_differences_between_calculated_streaming_insights.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
