# Gotchas — Data Cloud Calculated Insights

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Measure API Names Are Immutable After Creation

**What happens:** Once a Calculated Insight is saved, the API name of every measure (and dimension) is permanently locked. There is no rename operation. The only way to change a measure's API name is to delete the entire insight and recreate it from scratch — which also destroys all historical metric values stored in that insight.

**When it occurs:** Any time a practitioner saves a Calculated Insight with a placeholder name, a typo, or a name that conflicts with the org naming convention. Also occurs when business requirements change and a measure that was named `purchase_count_30d` needs to become `purchase_count_90d` because the window changed.

**How to avoid:** Treat insight creation as a schema migration, not a configuration step. Complete a written design review with final API names, data types, and rollup behaviors before opening the UI. Use the pre-creation design checklist in this skill. For staging orgs, delete all test insights immediately after validation so that their API names do not persist and create false confidence that a name is "safe."

---

## Gotcha 2: Streaming Insights Are Incompatible with Segment Builder

**What happens:** Streaming Insights do not appear as filterable fields in the Data Cloud Segment Builder. A team that creates a Streaming Insight expecting to build a batch audience segment on its value will find the metric completely absent from the segment filter picklist, with no error or explanation in the UI.

**When it occurs:** When the business use case is described as "real-time" but the actual goal is segmentation (audience-building for a batch activation). Practitioners hear "real-time" and reach for Streaming Insights, which are architecturally separate from the batch segmentation pipeline.

**How to avoid:** Clarify the downstream use: if the result is needed as a segment filter condition, use a Calculated Insight regardless of freshness requirements. If the result is needed to fire a near-real-time trigger (Data Action, push notification), use a Streaming Insight. The two features serve different pipeline stages and are not interchangeable.

---

## Gotcha 3: Scheduling Only at 6h, 12h, or 24h — No Sub-Hour Option

**What happens:** The Calculated Insights scheduler offers exactly three cadence options: every 6 hours, every 12 hours, or every 24 hours. There is no hourly, every-30-minutes, or custom cron option. Practitioners expecting flexible scheduling discover this constraint only when configuring the insight.

**When it occurs:** When a use case has a stated freshness requirement of "within 1–2 hours" (e.g., for same-day email personalization). The business signs off on "6 hours" as acceptable, but teams that assumed finer granularity was available are caught off guard.

**How to avoid:** Set freshness expectations with stakeholders during discovery using the actual available cadences. For sub-6-hour freshness requirements, either redesign the use case to tolerate 6-hour lag or evaluate Streaming Insights if the source is Mobile/Web SDK or MCP Personalization.

---

## Gotcha 4: Streaming Insights Are Capped at 20 Per Org — No Exceptions

**What happens:** An org can have a maximum of 20 Streaming Insights regardless of license tier or contract. The UI blocks creation of a 21st Streaming Insight with no option to increase the limit.

**When it occurs:** In large enterprise orgs with many real-time personalization use cases across multiple business units sharing a single Data Cloud instance. Teams building separate real-time triggers for each product line or campaign can exhaust this limit quickly if there is no governance.

**How to avoid:** Inventory Streaming Insights as a shared resource. Implement a lifecycle process: decommission Streaming Insights tied to completed campaigns. Combine related event conditions into a single Streaming Insight where possible (using OR conditions in the filter logic) to reduce total count.

---

## Gotcha 5: 2-Hour SQL Execution Timeout Terminates Long-Running Insights

**What happens:** If the Calculated Insight SQL takes longer than 2 hours to execute, the run is terminated and marked as failed. The insight is not partially updated — the previous run's values remain in place. Downstream segments using the insight continue to reflect the prior (stale) run until the next successful execution.

**When it occurs:** With complex multi-DMO JOINs, large fact tables without date filters, or orgs with very high data volumes that have not been tested at scale before deploying a new insight.

**How to avoid:** Apply a WHERE clause to limit the date range scanned (e.g., restrict to records updated in the last 18 months rather than scanning all-time data). Test the SQL on a representative data volume in a lower environment before deploying to production. Monitor the first several production runs using the Calculated Insights run history view to confirm execution times are well below the 2-hour ceiling.

---

## Gotcha 6: The 300-Insight Org Limit Applies to Calculated and Streaming Combined

**What happens:** The total org limit of 300 insights counts both Calculated Insights and Streaming Insights together. An org with 295 Calculated Insights and 5 Streaming Insights has reached the combined cap and cannot create any new insights — Calculated or Streaming.

**When it occurs:** In orgs where insights have been created ad hoc over multiple campaign cycles without any lifecycle management. Old, inactive insights accumulate and approach the ceiling before anyone realizes it.

**How to avoid:** Track insight count as an operational metric. Establish a governance rule: any insight tied to a time-limited campaign must be scheduled for deletion when the campaign ends. Regularly audit the Calculated Insights list and remove insights that have not been referenced by any active segment in the last 90 days.
