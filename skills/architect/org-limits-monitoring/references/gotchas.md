# Gotchas -- org-limits-monitoring

## Gotcha 1: OrgLimits.getAll() Does Not Return Every Limit the REST Resource Exposes

The Apex `OrgLimits.getAll()` method returns a curated subset of org limits, not the complete set. Limits like `DailyBulkV2QueryJobs`, `DailyBulkV2QueryFileStorageMB`, `SingleEmail`, and several streaming-specific limits are available through `GET /services/data/vXX.0/limits` but are absent from the Apex class. If you build a monitoring solution exclusively on `OrgLimits.getAll()`, you will have blind spots.

Workaround: For limits that only appear in the REST resource, use a Scheduled Apex job that makes an HTTP callout to your own org's REST Limits endpoint via a Named Credential. This consumes one API call per invocation but provides access to the full limit set. Alternatively, accept the blind spot and use the REST endpoint only for periodic manual audits or external monitoring tools.

---

## Gotcha 2: The REST Limits Resource Itself Consumes an API Call

Every `GET /services/data/vXX.0/limits` request counts as one API call against the `DailyApiRequests` allocation. If you poll this endpoint every 5 minutes from an external monitoring tool, that is 288 API calls per day consumed just for monitoring. For orgs where API budget is the primary concern, this creates a paradox: monitoring the limit consumes the limit.

Mitigation: Use the Apex `OrgLimits.getAll()` method for internal monitoring (it does not consume an API call). Reserve the REST endpoint for external tools that need the full limit set, and poll at a reasonable frequency (hourly or less). If you must poll from external systems, factor the monitoring overhead into your API budget calculations.

---

## Gotcha 3: Platform Event Publish Limits Reset Hourly on Clock Boundaries, Not Rolling Windows

The `HourlyPublishedPlatformEvents` limit resets at the top of each clock hour (e.g., 2:00 PM, 3:00 PM), not on a rolling 60-minute window. This means if you publish 4,900 events between 2:50 PM and 2:59 PM, the limit resets at 3:00 PM and you get a fresh allocation. Conversely, if you publish 4,900 events at 2:01 PM, you are stuck at that consumption level until 3:00 PM.

Practical impact: Monitoring jobs that run "every hour" may consistently fire at the same minute and miss consumption spikes that happen in different parts of the hour. Schedule event limit monitoring at 15-minute intervals to catch mid-hour spikes before the ceiling is reached.

---

## Gotcha 4: DailyApiRequests Allocation Varies by License Type and Add-On Purchases

The `DailyApiRequests` limit shown by `OrgLimits.getAll()` or the REST resource reflects the org's total allocation, which is calculated from a formula: base allocation per edition + (number of licenses x per-license add-on) + any purchased API call add-on packs. This means the limit value can change when licenses are added, removed, or when add-on subscriptions renew or expire.

A monitoring job that stores thresholds as absolute numbers (e.g., "alert at 800,000 calls") will silently become wrong if the allocation changes. Always compute thresholds as percentages of the current `.getLimit()` value rather than hard-coding absolute consumption numbers.

---

## Gotcha 5: Storage Limits Reported by the API May Not Match Setup UI Exactly

The `DataStorageMB` and `FileStorageMB` values returned by `OrgLimits.getAll()` and the REST Limits resource report the contractual allocation and current consumption. However, the Setup > Storage Usage page may show slightly different numbers because it includes additional granularity (e.g., breakdown by object, recycle bin consumption, big object storage reported separately). Additionally, storage consumption is not updated in real-time -- there can be a lag of up to 24 hours between a large data operation and the storage numbers reflecting the change.

For monitoring purposes, treat the API-reported values as directionally accurate but do not expect exact byte-level agreement with the Setup UI. Set thresholds conservatively (e.g., alert at 75% rather than 90%) to account for the reporting lag.

---

## Gotcha 6: Scheduled Apex Has a Maximum of 100 Scheduled Jobs Per Org

If you create a dedicated Scheduled Apex job for limit monitoring, it consumes one of the 100 available scheduled job slots. In orgs that already have many scheduled jobs (common in mature orgs with nightly batch chains), this can be a scarce resource. Furthermore, if the scheduled job is accidentally deleted or aborted, monitoring silently stops with no alert.

Mitigation: Combine all limit monitoring into a single scheduled job rather than creating separate jobs per limit category. Use the `System.schedule()` method with a CRON expression and implement a "watchdog" pattern: have the monitoring job's `execute()` method re-schedule itself if it detects its future scheduled instance has been removed.
