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

**Most common wrong assumption:** Practitioners often believe the 2,000-row limit is a data limit, not a display limit. Confirm whether the user needs more than 2,000 rows before recommending the async API path.

---

## Root Cause Assessment

Check each item and mark the likely root cause:

- [ ] **No selective filter** — report has no date range, owner, or record type filter on a large object
- [ ] **CRT complexity** — custom report type spans 3–4 objects; outer joins may be inflating row counts
- [ ] **Dashboard component overload** — dashboard has more than 20 components, multiplying refresh queries
- [ ] **Row limit misunderstanding** — user needs all rows but is exporting via UI (2,000-row cap applies)
- [ ] **Subscription timeout** — subscription fails because report times out at subscriber's sharing scope
- [ ] **Refresh schedule** — dashboard scheduled refresh is less than 24 hours (platform minimum is 24hr)

---

## Approach

**Pattern selected:** (choose one)

- [ ] Selective Filter Layer — add date range / owner / record type filter
- [ ] Async Analytics API — provide polling pattern for full result set
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

## Async API Pattern (if applicable)

**Report ID:** (the 18-character Report ID from the URL)

**Request body:**

```json
{
  "includeDetails": true,
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

**Polling endpoint:** `GET /services/data/v60.0/analytics/reports/{reportId}/instances/{instanceId}`

**Expected status flow:** `Running` → `Success` (or `Error` — add error handling)

**Row count validation:** (compare against a COUNT summary report before processing)

---

## Dashboard Optimization Plan

| Item | Current State | Target State |
|---|---|---|
| Component count | | 20 or fewer |
| Refresh schedule | | Off-peak window |
| Running user setting | | Confirm security intent |
| Split recommendation | | |

---

## Checklist

- [ ] At least one selective filter applied to every report on an object with more than 500K records
- [ ] Custom report type spans no more objects than needed by the active field set
- [ ] Reports requiring more than 2,000 rows use Analytics API async execution
- [ ] Dashboard component count is 20 or fewer per dashboard
- [ ] Dashboard refresh scheduled during off-peak hours if automated
- [ ] Required filters documented in the report description
- [ ] Async API polling code includes error handling for `Error` and `Running` states
- [ ] Solution tested at subscriber's access level (not only as admin)

---

## Notes

(Record any deviations from the standard pattern, edge cases encountered, or decisions made with explicit stakeholder agreement — e.g., "Date filter intentionally set to ALL TIME per Finance team requirement; accepted timeout risk for monthly-only execution.")
