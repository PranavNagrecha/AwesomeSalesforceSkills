# LLM Anti-Patterns — Data Cloud Calculated Insights

Common mistakes AI coding assistants make when generating or advising on Data Cloud Calculated Insights.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating Streaming Insights as Equivalent to Calculated Insights for Segmentation

**What the LLM generates:** Advice such as "Use a Streaming Insight to compute total lifetime spend so it's always up to date, then filter your segment on `total_lifetime_spend > 500`." Or a configuration that sets up a Streaming Insight with an aggregate measure and references it in a Segment Builder filter.

**Why it happens:** Both features have "insight" in their name and both involve computing metrics from Data Cloud data. LLMs trained on general Salesforce content conflate the two. The functional difference (batch vs. real-time; segment-filterable vs. Data Action only) is not prominent in surface-level documentation summaries.

**Correct pattern:**
```
Streaming Insights → real-time Data Action triggers only (not available in Segment Builder)
Calculated Insights → persistent, segment-filterable measures (minimum 6h cadence)

For any metric used as a Segment Builder filter: use a Calculated Insight, not a Streaming Insight.
```

**Detection hint:** Look for phrases like "Streaming Insight" combined with "segment filter," "audience," or "Segment Builder." Any such combination is incorrect.

---

## Anti-Pattern 2: Not Designing Dimension and Measure API Names Before Creation

**What the LLM generates:** Step-by-step instructions that say "you can always rename the measure later if needed" or a workflow that creates an insight with placeholder names like `metric1`, `metric2`, intending to rename them in a follow-up step.

**Why it happens:** Most platform objects in Salesforce allow API name changes after creation (custom fields, custom objects, etc.). LLMs trained on general Salesforce metadata patterns assume Calculated Insights follow the same model.

**Correct pattern:**
```
Calculated Insight dimension names, measure API names, measure data types,
and rollup behaviors are IMMUTABLE after creation.
No rename is possible. The only fix for a naming mistake is to delete the insight
(destroying all historical values) and recreate it.

Always design and review all API names BEFORE saving the insight.
```

**Detection hint:** Watch for phrases like "rename the measure," "update the API name," or "we can adjust that later." All are incorrect for Calculated Insights.

---

## Anti-Pattern 3: Recommending Hourly or On-Demand Calculated Insight Scheduling

**What the LLM generates:** Instructions like "Schedule the insight to refresh every hour to keep segments current" or "Trigger a refresh after each batch load completes using the scheduler."

**Why it happens:** LLMs are familiar with cron-style schedulers that support arbitrary intervals. The constraint that Data Cloud Calculated Insights only support 6h, 12h, and 24h cadences is a platform-specific limit not present in most scheduling systems, so LLMs default to flexible scheduling language.

**Correct pattern:**
```
Calculated Insights support exactly three schedule cadences:
  - Every 6 hours
  - Every 12 hours
  - Every 24 hours

There is no hourly option, no custom cron expression, and no UI-triggered on-demand run.
(A manual refresh is available via the Data Cloud REST API, but not via the standard UI scheduler.)
```

**Detection hint:** Look for "every hour," "hourly refresh," "on-demand trigger," or specific non-6/12/24-hour interval suggestions. All are incorrect.

---

## Anti-Pattern 4: Assuming Streaming Insights Support Any Event Source

**What the LLM generates:** A Streaming Insight configuration that uses a batch data stream, a CRM connector, an S3 connector, or an Ingestion API source — "Since it's real-time data, use a Streaming Insight."

**Why it happens:** The term "streaming" implies continuous data flow, and many Data Cloud ingestion paths do provide continuous or frequent data. LLMs incorrectly generalize that any continuously-ingested data can power a Streaming Insight.

**Correct pattern:**
```
Streaming Insights support ONLY two source types:
  1. Mobile/Web SDK (Salesforce Interaction Studio / Data Cloud Web SDK)
  2. Marketing Cloud Personalization (formerly Interaction Studio)

All other source types — Ingestion API, CRM Connector, S3, MuleSoft, partner connectors —
are incompatible with Streaming Insights.
For these sources, use Calculated Insights (batch SQL).
```

**Detection hint:** Look for Streaming Insight configurations paired with Ingestion API, S3, MuleSoft, or CRM Connector sources. All are invalid.

---

## Anti-Pattern 5: Using a Single Insight for Both Lifetime and Windowed Metrics Without Checking Timeout Risk

**What the LLM generates:** A single Calculated Insight SQL that computes ten or more measures (lifetime totals, multiple date windows, complex conditional aggregates) across three or more large DMOs using multiple JOINs, with no WHERE clause limiting the data scanned.

**Why it happens:** Combining all metrics into one insight is efficient from an org-limit perspective (uses only 1 of the 300 insight slots). LLMs optimize for this without considering execution cost. The 2-hour execution timeout is not a commonly cited constraint in general analytics documentation.

**Correct pattern:**
```sql
-- Always add a WHERE clause to limit the scan window to a relevant period.
-- For lifetime metrics, partition by a meaningful cutoff (e.g., last 3 years of data)
-- rather than scanning all-time data unless the business explicitly requires it.
WHERE event_date__c >= DATEADD(YEAR, -3, CURRENT_DATE)

-- For very complex multi-DMO insights, split into two insights:
-- one for lifetime totals (24h schedule, broad scan),
-- one for short-window metrics (6h schedule, narrow date filter).
```

**Detection hint:** Calculated Insight SQL with no WHERE clause or with JOINs across 3+ large DMOs and 8+ aggregation measures should be reviewed for timeout risk. Look for "all-time," "no date filter," or "full history" in the requirements.

---

## Anti-Pattern 6: Conflating the 300 Insight Limit with Only Calculated Insights

**What the LLM generates:** "You can create up to 300 Calculated Insights per org" — stating the limit applies only to Calculated Insights rather than to the combined total of Calculated + Streaming Insights.

**Why it happens:** Documentation sometimes refers to the 300-insight limit in the context of Calculated Insights examples, and LLMs drop the qualifier that Streaming Insights also count toward the same cap.

**Correct pattern:**
```
Org limit: 300 total insights — Calculated Insights + Streaming Insights combined.
Streaming Insights additional limit: 20 per org (subset of the 300 total).

Example: an org with 285 Calculated Insights and 15 Streaming Insights
has used 300 of its 300 total insight slots and cannot create any more of either type.
```

**Detection hint:** Any statement that quotes "300 Calculated Insights" without mentioning the combined cap, or that quotes the Streaming Insight limit without referencing the combined 300 ceiling, should be corrected.
