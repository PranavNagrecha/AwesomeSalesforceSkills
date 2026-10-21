# Examples — Report Performance Tuning

UNVERIFIED (2026-10-21), applies to this file: the timings (60+ s → under 5 s, 45 s → 8 s), the "Opportunities with Contact Roles" report type, the claim that standard report types are pre-optimized, and the "Report data unavailable" dashboard error and error-instead-of-stale-data behaviour in Example 1 are illustrative or Help-only. Grounded: the Reports and Dashboards REST API "returns up to the first 2,000 report rows" sync or async (REST API 262, Requirements and Limitations); fields indexed by default include Id, Name, OwnerId, CreatedDate, SystemModstamp and RecordType (ldv 264 L308-309).

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
  - Historical Pipeline (for trend): summarized onto a parent/summary object nightly
```

**Why it works:** A selective date range lets the optimizer avoid a full scan — provided the date field is indexed (ldv 264 L305-309). UNVERIFIED (2026-10-21): that Close Date is indexed by default (CreatedDate is, ldv 264 L308-309); if it is not, ask Support for a custom index or filter on CreatedDate. Storing summarized history "on the parent record for the report ... is more efficient than having the report summarize the child records" (ldv 264 L799-801).

---

## Example 2: Full Result Export — Bulk API 2.0, Not the Analytics API

**Context:** A data team needs a daily extract of all closed Opportunities created in the current fiscal year — approximately 120,000 rows. Their report-based pipeline always stops at 2,000 rows, and they concluded the org "only has 2,000 records."

**Problem:** The Reports and Dashboards REST API "returns up to the first 2,000 report rows" — synchronous and asynchronous runs alike (REST API 262, Requirements and Limitations). An async `POST .../analytics/reports/{reportId}/instances` run avoids the 2-minute API timeout and keeps results 24 hours (Run Reports Synchronously or Asynchronously), but it does not return row 2,001. Earlier versions of this example claimed it did.

**Solution:** query the object with a Bulk API 2.0 query job (api_asynch 264 L1055-1069):

```http
# Step 1: Create the query job
POST /services/data/v68.0/jobs/query
Content-Type: application/json
Authorization: Bearer {accessToken}

{
  "operation": "query",
  "query": "SELECT Id, Name, Amount, CloseDate FROM Opportunity WHERE IsClosed = true AND CreatedDate = THIS_FISCAL_YEAR"
}

# Step 2: Poll the job until state is JobComplete
GET /services/data/v68.0/jobs/query/{queryJobId}

# Step 3: Download the CSV results
GET /services/data/v68.0/jobs/query/{queryJobId}/results
```

**Why it works:** Bulk API 2.0 exists "to perform bulk queries on your org data" (api_asynch 264 L136-137) and has no 2,000-row report cap. The job and results URLs are the guide's own (api_asynch 264 L1093, L1126); `JobComplete` means "The job was processed" (L281). If the output must keep report formatting, split the report run into date windows that each return fewer than 2,000 rows.

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

**What goes wrong:** UNVERIFIED (2026-10-21): that the UI export stops at the 2,000-row display cap — Help-only. Either way, a report export is the wrong tool for a downstream process that must be complete, and the Analytics API is no escape hatch: it returns only the first 2,000 report rows, sync or async (REST API 262, Requirements and Limitations).

**Correct approach:** Export directly from the object with a Bulk API 2.0 query job (Example 2; api_asynch 264 L136-137), bypassing the report layer. If report formatting is required, run the report in filter windows that each return fewer than 2,000 rows and merge the results.
