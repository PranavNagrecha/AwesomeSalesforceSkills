# Examples -- org-limits-monitoring

## Example 1: Integration-Heavy Org Exhausting Daily API Calls

### Scenario

A manufacturing company runs 14 integrations through MuleSoft that collectively make 800,000 API calls per day against an Enterprise Edition org with a 1,000,000 daily API call allocation (base + purchased add-on). Over three months, two new integrations were added without updating the API budget analysis. On a high-volume Monday, a bulk order sync pushed consumption to 1,020,000 calls, causing all integrations to fail with `REQUEST_LIMIT_EXCEEDED` from 2:00 PM until midnight when the 24-hour window rolled over.

### Problem

No monitoring was in place. The only visibility was the Setup > Company Information page, which no one checked proactively. The team discovered the exhaustion only when downstream systems reported missing data.

### Solution

1. **Deployed a Scheduled Apex monitoring job** that runs every hour. The job calls `OrgLimits.getAll()` and reads the `DailyApiRequests` entry. It compares `getValue()` (consumed) against `getLimit()` (total allocation) to compute a consumption percentage.

2. **Created a `Limit_Monitor_Config__mdt` Custom Metadata Type** with records for each monitored limit. The `DailyApiRequests` record has `Warning_Threshold__c = 70` and `Critical_Threshold__c = 85`.

3. **Configured multi-channel alerting.** At 70% consumption, the job sends an email to the integration team distribution list. At 85%, it fires an HTTP callout to PagerDuty to create an incident. The callout uses a Named Credential to authenticate.

4. **Built a Lightning Dashboard** with a gauge chart showing current API consumption percentage, refreshed every 30 minutes via a dashboard subscription.

### Why This Works

The hourly monitoring cadence means the team gets a 70% warning when approximately 700,000 calls have been made -- typically by early afternoon on high-volume days. This gives 4-6 hours to investigate and throttle non-critical integrations before the 85% critical threshold. The PagerDuty integration at 85% ensures on-call engineers are paged even outside business hours.

---

## Example 2: Data Storage Creep Causing Record Creation Failures

### Scenario

A healthcare org with Unlimited Edition has 20 GB of data storage allocation. Over 18 months, a combination of audit trail logging to a custom object (`Audit_Log__c`) and historical case attachments grew storage to 19.2 GB (96%). A scheduled data enrichment job that creates 50,000 staging records failed with `STORAGE_LIMIT_EXCEEDED`, blocking a critical patient data migration.

### Problem

The org had no storage monitoring. The data team assumed Unlimited Edition meant unlimited storage (a common misconception -- Unlimited Edition has higher but still finite allocations). The failure occurred on a Saturday during a planned migration window, delaying the go-live by a week.

### Solution

1. **Immediate triage.** Ran `GET /services/data/v60.0/limits` to confirm `DataStorageMB` showed `Max: 20480` and `Remaining: 1280` (93.75% consumed). Identified `Audit_Log__c` as the largest consumer via a SOQL `SELECT COUNT() FROM Audit_Log__c` (12 million records, approximately 12 GB).

2. **Deployed archival.** Moved Audit_Log__c records older than 13 months to a Big Object (`Audit_Log_Archive__b`) using Batch Apex, freeing 8 GB of data storage.

3. **Implemented proactive monitoring.** Created a Scheduled Apex class that checks `DataStorageMB` and `FileStorageMB` from `OrgLimits.getAll()` daily at 6:00 AM. Warning threshold at 75%, critical at 85%. Alerts route to the data governance team via Custom Notification and email.

4. **Added a storage trend report.** The monitoring job writes daily consumption snapshots to a custom object (`Org_Limit_Snapshot__c`) with fields for limit name, date, consumed value, and total allocation. A CRM Analytics dashboard plots the 90-day trend line and projects the date storage will reach 85% at the current growth rate.

### Why This Works

Daily storage monitoring catches gradual creep long before it causes failures. The trend projection gives the data governance team weeks of lead time to plan archival or request additional storage allocation. The Big Object archival pattern removes data from the storage limit while keeping it queryable for compliance.

---

## Example 3: Platform Event Hourly Limit Causing Silent Data Loss

### Scenario

A retail org uses Platform Events to synchronize order data between Salesforce and an external order management system. The org publishes approximately 4,000 events per hour during normal operations against an hourly limit of 5,000. During a flash sale, order volume tripled, pushing event publication to 12,000 per hour. Events beyond the 5,000 limit were silently dropped -- no error was thrown to the publishing Apex code, and no alert was generated.

### Problem

Platform Event hourly limits behave differently from API limits. When the hourly publication limit is exceeded, additional `EventBus.publish()` calls succeed from the Apex perspective (no exception is thrown), but the events are not delivered to subscribers. This silent failure mode makes it invisible to standard error handling.

### Solution

1. **Added `HourlyPublishedPlatformEvents` to the monitoring job** with a 60% warning threshold (3,000 events/hour) and 80% critical threshold (4,000 events/hour). Because this limit resets hourly, the monitoring job runs every 15 minutes specifically for event limits.

2. **Implemented publish result checking.** Modified the Apex publishing code to inspect `Database.SaveResult` objects returned by `EventBus.publish()`. While this does not catch the silent drop scenario directly, it catches publish failures from other causes.

3. **Added subscriber-side reconciliation.** The external OMS runs a nightly reconciliation job that queries Salesforce for orders created in the last 24 hours and compares against received events. Missing events trigger a re-sync via the REST API.

### Why This Works

The 15-minute monitoring cadence for event limits provides early warning before the hourly ceiling is reached. The subscriber-side reconciliation acts as a safety net for the silent failure mode that monitoring alone cannot prevent. Together, they ensure data consistency even during traffic spikes.
