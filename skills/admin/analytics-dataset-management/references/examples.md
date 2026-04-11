# Examples — Analytics Dataset Management

## Example 1: Nightly Opportunity Dataset Silently Serving Stale Data

**Context:** A sales operations team has a CRM Analytics dashboard showing pipeline by close date. The org has twelve active dataflows: seven from managed packages (Revenue Intelligence, Service Analytics, Einstein Activity Capture) and five custom flows built by the admin team. All twelve are scheduled to run between 01:00 and 03:00 UTC.

**Problem:** The custom Opportunity dataflow starts at 02:30 UTC but is frequently not running. The dataset shows data from two or three days ago. No error email is sent. The admin checks the dataflow in Data Manager and sees "Last run: 3 days ago — Queued." The quota of 60 runs per 24-hour period is being exhausted by the managed-package flows and earlier custom flows before the Opportunity dataflow gets a chance to execute.

**Solution:**

1. Audit all dataflows and their scheduled frequency:

```
Managed packages (nightly):          7 flows × 1 run = 7 runs/day
Custom analytics (every 4 hours):    4 flows × 6 runs = 24 runs/day
Opportunity flow (nightly):          1 flow  × 1 run =  1 run/day
                                     ----------------------
                                     Total scheduled:   32 runs/day
```

2. Combine the four custom analytics flows that target related objects into a single multi-object dataflow. This reduces 24 runs/day to 6 runs/day.

3. Reschedule the combined flow and the Opportunity flow to 03:30 UTC — after the managed-package window has cleared.

4. Configure failure alerting in CRM Analytics Studio > Data Manager > Notification Settings.

**Why it works:** The combined flow uses `augment` to merge objects in a single pass, consuming one quota slot instead of four. Moving the schedule later ensures the remaining quota is available. The alert means the team finds out about failures the same morning instead of days later.

---

## Example 2: Close Date Appearing as Text — Timeseries Charts Return No Data

**Context:** An admin builds a new Opportunity pipeline dataflow from scratch using the CRM Analytics UI. The `sfdcDigest` node pulls CloseDate, Amount, StageName, and OwnerId. The dataflow runs successfully and the dataset appears in Data Manager. A dashboard developer then builds a timeseries chart grouped by CloseDate and gets zero data rows, even though the Opportunity object has hundreds of records.

**Problem:** The `sfdcDigest` node brings `CloseDate` into the dataset with type `Text` because no explicit schema node was added to declare it as a Date type. SAQL `timeseries` expressions require a column of type Date. A Text column is silently skipped, returning no data rather than an error.

**Solution:**

Add a `schema` transformation node between the `sfdcDigest` and `register` nodes in the dataflow JSON:

```json
{
  "schema_Opportunities": {
    "action": "schema",
    "parameters": {
      "fields": [
        {
          "name": "CloseDate",
          "newName": "CloseDate",
          "type": "Date",
          "format": "yyyy-MM-dd",
          "fiscalMonthOffset": 0
        },
        {
          "name": "CreatedDate",
          "newName": "CreatedDate",
          "type": "Date",
          "format": "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'",
          "fiscalMonthOffset": 0
        }
      ],
      "source": "digest_Opportunities"
    }
  },
  "register_Opportunities": {
    "action": "sfdcRegister",
    "parameters": {
      "name": "Opportunities",
      "alias": "Opportunities",
      "source": "schema_Opportunities"
    }
  }
}
```

After re-running the dataflow, confirm the column type in Data Manager shows `Date` not `Text`. Re-run the timeseries SAQL query to verify data returns correctly.

**Why it works:** CRM Analytics resolves column types at write time, not at query time. The `schema` node is the supported mechanism to cast a field from its default (Text) to Date before the `register` step writes it to the dataset. The SAQL engine can then apply `timeseries`, date range filters, and `date_to_epoch` to the column correctly.

---

## Anti-Pattern: One Dataflow Per Object, All Scheduled Hourly

**What practitioners do:** When asked to "keep the pipeline dataset fresh," some admins create a separate dataflow for every source object (Opportunity, Account, Lead, Contact) and schedule each to run every two hours throughout the day to maximize freshness.

**What goes wrong:** Four objects × 12 runs each = 48 runs per day from custom flows alone. Add managed-package flows (commonly 5–10 in orgs with Revenue Intelligence or Service Analytics) and the org can hit the 60-run ceiling by mid-day. The later dataflows in the day queue and never execute. Datasets for Account and Contact show yesterday's data while the Opportunity dataset — first in the schedule — stays current. Inconsistencies across related datasets cause join mismatches in dashboards.

**Correct approach:** Combine related objects into a single multi-object dataflow and evaluate whether hourly refresh is actually required for the business decision the dashboard supports. Most pipeline dashboards are acted on once per day; a single nightly run is usually sufficient and consumes one quota slot instead of twelve.
