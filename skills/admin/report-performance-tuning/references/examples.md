# Examples — Report Performance Tuning

## Example 1: Opportunity Pipeline Report Timing Out in Enterprise Org

**Context:** An enterprise org has 8 million Opportunity records spanning 6 years of sales history. The sales ops team built an "All Pipeline" report with no date filter and shared it on the executive dashboard. After the org grew past 5M records, the report began timing out intermittently, and the dashboard started showing "Report data unavailable."

**Problem:** Without a date range filter, the report engine scans all 8M Opportunity rows on every execution. The system eventually hits the query timeout before returning results. The dashboard component shows an error rather than stale data.

**Solution:**

```
Report filters applied:
  - Close Date: equals NEXT 90 DAYS (for pipeline view)
  - OR: Close Date: equals LAST 30 DAYS (for recent closes)

Additional selective filter (recommended for additional safety):
  - Forecast Category: NOT EQUAL TO Omitted

Dashboard configuration:
  - Split "Active Pipeline" and "Historical Pipeline" into two separate reports
  - Active Pipeline: Close Date = THIS QUARTER, NEXT QUARTER
  - Historical Pipeline (for trend): run via async Analytics API nightly, cache results
```

**Why it works:** Close Date on Opportunity is indexed by default in Salesforce. Adding a relative date range filter converts a full 8M-row scan into a targeted range scan, typically dropping query time from 60+ seconds to under 5 seconds. Splitting historical queries to async execution removes them from the interactive dashboard path entirely.

---

## Example 2: Full Result Export Using Analytics API Async Execution

**Context:** A data team needs a daily extract of all closed Opportunities created in the current fiscal year — approximately 120,000 rows. They built a report in the UI but the exported CSV always stops at 2,000 rows. They incorrectly concluded the org "only has 2,000 records."

**Problem:** The Salesforce report UI and the synchronous Analytics API endpoint both display a maximum of 2,000 detail rows. The export button in the UI exports only the displayed rows. The underlying data is complete, but neither the UI nor the synchronous API surface it.

**Solution:**

```http
# Step 1: Submit async report instance
POST /services/data/v60.0/analytics/reports/{reportId}/instances
Content-Type: application/json
Authorization: Bearer {accessToken}

{
  "reportMetadata": {
    "reportFilters": [
      {
        "column": "CLOSE_DATE",
        "operator": "greaterOrEqual",
        "value": "2025-02-01"
      }
    ]
  },
  "includeDetails": true
}

# Step 2: Poll for completion
GET /services/data/v60.0/analytics/reports/{reportId}/instances/{instanceId}

# Response when complete:
# { "attributes": { "status": "Success" }, "factMap": { ... } }
```

**Why it works:** The async Analytics API endpoint (`POST .../instances`) bypasses the 2,000-row display limit. The `includeDetails: true` parameter includes row-level detail in the `factMap`. Polling continues until `status` is `Success`, then the caller processes the full result set. For very large exports (>2M rows), the date filter in `reportMetadata.reportFilters` is chunked across multiple requests.

---

## Example 3: Custom Report Type with 4 Objects Replaced by Standard Type

**Context:** An admin built a custom report type spanning Account → Contact → Opportunity → OpportunityContactRole to report on "contacts involved in deals." The CRT was built 3 years ago when standard types did not serve the need. Now the report takes 45 seconds to load on a filtered dataset of 50,000 Opportunities.

**Problem:** The CRT uses outer joins at each level ("Account with or without Contact, Contact with or without Opportunity"). The outer join on OpportunityContactRole forces the engine to evaluate every role row for every Opportunity row. With 50,000 Opportunities and an average of 3 contact roles each, that's 150,000 join evaluations just at the last level.

**Solution:**

```
1. Audit fields used in the report:
   - Account Name (from Account)
   - Contact Name (from Contact)
   - Opportunity Name, Close Date, Amount (from Opportunity)
   - Role (from OpportunityContactRole)

2. Check standard report types:
   - "Opportunities with Contact Roles" standard CRT covers
     Opportunity + OpportunityContactRole + Contact
   - Account Name is available via Opportunity.AccountId relationship

3. Rebuild on standard "Opportunities with Contact Roles" report type
   - Remove the top-level Account object from the custom CRT path
   - All required fields remain available through the standard type

4. Result: query time dropped from 45s to 8s on the same filtered dataset
```

**Why it works:** Standard report types are pre-optimized by Salesforce. The join paths are tuned at the platform level. The Account Name field is accessible via the Opportunity's AccountId lookup without requiring a separate Account join level in the CRT. Removing one join level from a 4-object CRT eliminates the most expensive outer join tier.

---

## Anti-Pattern: Exporting Reports via UI to Work Around Row Limit

**What practitioners do:** A user needs 50,000 rows from a report. They click "Export" in the Lightning Report UI, choosing CSV format, expecting to get all rows.

**What goes wrong:** The UI export respects the same 2,000-row display cap. The downloaded CSV contains at most 2,000 rows. The user receives a file that appears complete but is missing 96% of the data. This is particularly dangerous when the exported data feeds a downstream process or calculation.

**Correct approach:** Use the Analytics API async execution pattern (`POST /analytics/reports/{id}/instances` with `includeDetails: true`). For very large exports, filter by time windows and merge the resulting payloads. Alternatively, if the data is needed regularly, expose the underlying object via a Connected App and export directly from the API (`/query` or bulk API), bypassing the report layer entirely.
