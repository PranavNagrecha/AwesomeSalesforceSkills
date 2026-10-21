# Report Performance Tuning — Work Template

Use this template when diagnosing or resolving a slow, timing-out, or row-limited report or dashboard. Fill in every section before recommending a solution.

---

## Scope

**Skill:** `report-performance-tuning`

**Request summary:** (describe what the user reported — e.g., "Opportunity pipeline report times out on load")

---

## Context Gathered

Answer these before proceeding. Do not skip — the correct fix depends on the answers.

| Question | Answer |
|---|---|
| Primary object the report is built on | |
| Approximate record count on that object | |
| Active filters on the report (list each) | |
| Report type: standard or custom (CRT)? | |
| If CRT: how many objects does it span? | |
| Execution context: UI / subscription / dashboard / API | |
| Is API access available in this org? | |
| Edition (for dynamic dashboard limits) | |

**Most common wrong assumption:** that an API run returns more than 2,000 rows. The Reports and Dashboards REST API "returns up to the first 2,000 report rows", sync or async (REST API 262, Requirements and Limitations). Confirm whether the user needs more than 2,000 rows; if so, plan a Bulk API 2.0 query or filter-windowed runs.

---

## Root Cause Assessment

Check each item and mark the likely root cause:

- [ ] **No selective filter** — report has no date range, owner, or record type filter on a large object
- [ ] **CRT complexity** — custom report type spans 3–4 objects; outer joins may be inflating row counts
- [ ] **Dashboard component overload** — dashboard has more than 20 components (Help-only guidance, UNVERIFIED)
- [ ] **Row limit misunderstanding** — user needs all rows from a report or an API run (the API returns only the first 2,000)
- [ ] **Subscription timeout** — subscription fails at the subscriber's data scope (run-as behaviour UNVERIFIED)
- [ ] **Refresh schedule** — expected cadence vs what the org's scheduler allows (24-hour minimum UNVERIFIED)

---

## Approach

**Pattern selected:** (choose one)

- [ ] Selective Filter Layer — add date range / owner / record type filter
- [ ] Full extract — Bulk API 2.0 query job, or filter windows under 2,000 rows each
- [ ] Report Type Simplification — reduce CRT to fewer objects
- [ ] Dashboard Optimization — reduce components, adjust refresh schedule
- [ ] Combination of the above (describe below)

**Rationale:** (why this pattern fits the context gathered above)

---

## Filter Recommendation

| Filter Field | Operator | Value | Reason for Selection |
|---|---|---|---|
| | | | |
| | | | |

**Date range strategy:** (e.g., "THIS YEAR for active pipeline; separate saved report for LAST YEAR historical view")

---

## Report Type Assessment

| CRT Object | Fields Used in Report | Keep or Remove? |
|---|---|---|
| Object 1 | | |
| Object 2 | | |
| Object 3 | | |
| Object 4 | | |

**Join type audit:** (list any outer joins and whether they are required or can be changed to inner joins)

---

## Async API Pattern (if applicable — long runs, not more rows)

Each run still returns at most the first 2,000 report rows; size each filter window below that.

**Report ID:** (the 18-character Report ID from the URL)

**Request body (POST `/services/data/vXX.0/analytics/reports/{reportId}/instances`):**

```json
{
  "reportMetadata": {
    "reportFilters": [
      {
        "column": "CREATED_DATE",
        "operator": "greaterOrEqual",
        "value": "YYYY-MM-DD"
      }
    ]
  }
}
```

**Polling endpoint:** `GET /services/data/vXX.0/analytics/reports/{reportId}/instances/{instanceId}`

**Expected status flow:** `New` → `Running` → `Success` (or `Error` — add error handling)

**Row count validation:** (compare against a COUNT() query; a window that returns exactly 2,000 rows is truncated — split it)

---

## Dashboard Optimization Plan

| Item | Current State | Target State |
|---|---|---|
| Component count | | 20 or fewer (Help-only guidance) |
| Refresh schedule | | Off-peak window |
| Running user setting | | Confirm security intent |
| Split recommendation | | |

---

## Checklist

- [ ] At least one selective filter on an indexed field for every report on a large object (500K is a rule of thumb)
- [ ] Custom report type spans no more objects than needed by the active field set
- [ ] Requirements over 2,000 rows use a Bulk API 2.0 query or sub-2,000-row filter windows, not "the async API"
- [ ] Dashboard component count reviewed (20-component guidance is Help-only)
- [ ] Dashboard refresh scheduled during off-peak hours if automated
- [ ] Required filters documented in the report description
- [ ] Async API polling code handles `New`, `Running`, `Success` and `Error`
- [ ] Solution tested at subscriber's access level (not only as admin)

---

## Notes

(Record any deviations from the standard pattern, edge cases encountered, or decisions made with explicit stakeholder agreement — e.g., "Date filter intentionally set to ALL TIME per Finance team requirement; accepted timeout risk for monthly-only execution.")
