# Org Limits Monitoring Template

Use this template to document the org-level limit monitoring strategy for a Salesforce org. Fill in all sections before deploying the monitoring solution.

---

## 1. Org Context

| Field | Value |
|---|---|
| Org Edition | _Enterprise / Unlimited / Performance / Developer_ |
| Org ID | _00Dxxxxxxxxxx_ |
| Primary Use Case | _Integration-heavy / High-growth data / Event-driven / Mixed_ |
| Monitoring Objective | _Greenfield setup / Incident response / Enhancement of existing monitoring_ |
| Review Date | _YYYY-MM-DD_ |
| Designed By | _Name / Role_ |

---

## 2. Limits to Monitor

For each limit to monitor, complete one row. Add rows as needed. Use limit names as they appear in `OrgLimits.getAll()` or the REST Limits resource.

| Limit Name | Current Allocation | Current Consumption | Pct Used | Warning Threshold (%) | Critical Threshold (%) | Available Via OrgLimits? | Notes |
|---|---|---|---|---|---|---|---|
| DailyApiRequests | _e.g., 1,000,000_ | _e.g., 450,000_ | _45%_ | _70_ | _85_ | Yes | _Primary integration concern_ |
| DataStorageMB | _e.g., 20,480_ | _e.g., 14,200_ | _69%_ | _75_ | _85_ | Yes | _Growing 500MB/quarter_ |
| FileStorageMB | | | | _75_ | _85_ | Yes | |
| HourlyPublishedPlatformEvents | | | | _60_ | _80_ | Yes | _Silent drop risk above limit_ |
| DailyAsyncApexExecutions | | | | _70_ | _85_ | Yes | |
| DailyBulkApiRequests | | | | _70_ | _85_ | Yes | |
| _Add more as needed_ | | | | | | | |

---

## 3. Monitoring Architecture

### Monitoring Surface Selection

| Surface | Used? | Purpose |
|---|---|---|
| Apex OrgLimits.getAll() | _Yes / No_ | _Primary polling from Scheduled Apex_ |
| REST GET /limits | _Yes / No_ | _External monitoring tool / limits not in OrgLimits_ |
| Setup > Company Information | _Yes / No_ | _Manual fallback only_ |

### Polling Frequency

| Limit Category | Frequency | Justification |
|---|---|---|
| API consumption limits | _Every 1 hour_ | _High-velocity integrations require early warning_ |
| Storage limits | _Every 4 hours / Daily_ | _Storage changes slowly; daily is usually sufficient_ |
| Platform event limits | _Every 15 minutes_ | _Hourly reset means mid-hour spikes need fast detection_ |
| Async processing limits | _Every 1 hour_ | _Batch chains can consume rapidly during business hours_ |

---

## 4. Alert Routing

| Alert Severity | Channel | Recipients | Expected Response Time |
|---|---|---|---|
| Warning (threshold 1) | _Email / Custom Notification_ | _Platform team DL_ | _Same business day_ |
| Critical (threshold 2) | _PagerDuty / Slack / Email_ | _On-call engineer + Platform lead_ | _Within 1 hour_ |
| Informational (daily digest) | _Email_ | _Architecture team_ | _No immediate action_ |

---

## 5. Custom Metadata Configuration

Define the `Limit_Monitor_Config__mdt` records to deploy:

| DeveloperName | Limit_Name__c | Warning_Threshold__c | Critical_Threshold__c | Enabled__c | Notification_Channel__c |
|---|---|---|---|---|---|
| _DailyApiRequests_ | DailyApiRequests | _70_ | _85_ | _true_ | _Email_ |
| _DataStorageMB_ | DataStorageMB | _75_ | _85_ | _true_ | _Email_ |
| _HourlyPlatformEvents_ | HourlyPublishedPlatformEvents | _60_ | _80_ | _true_ | _PlatformEvent_ |
| _Add more_ | | | | | |

---

## 6. Visibility and Dashboards

| Component | Type | Data Source | Refresh Frequency |
|---|---|---|---|
| _Org Limits Overview_ | _Lightning Dashboard / LWC_ | _Org_Limit_Snapshot__c records_ | _Every 30 minutes_ |
| _API Consumption Trend_ | _CRM Analytics Dashboard_ | _Org_Limit_Snapshot__c (90-day)_ | _Daily_ |
| _Storage Growth Projection_ | _CRM Analytics Lens_ | _Org_Limit_Snapshot__c_ | _Weekly_ |

---

## 7. Reconciliation and Silent Failure Coverage

For limits with silent failure modes (e.g., Platform Event hourly limits):

| Limit | Silent Failure Risk | Reconciliation Mechanism | Frequency |
|---|---|---|---|
| HourlyPublishedPlatformEvents | Events dropped without exception | _Subscriber-side count reconciliation_ | _Nightly_ |
| _Add others as needed_ | | | |

---

## 8. Operational Runbook

| Alert | Immediate Action | Escalation Path | Recovery Procedure |
|---|---|---|---|
| DailyApiRequests > Warning | _Identify top API consumers via Login History + API Usage_ | _Integration team lead_ | _Throttle non-critical integrations_ |
| DailyApiRequests > Critical | _Page on-call; disable lowest-priority integrations_ | _VP Engineering_ | _Request emergency API add-on from Salesforce AE_ |
| DataStorageMB > Warning | _Run storage audit; identify archival candidates_ | _Data governance team_ | _Archive old records to Big Objects or external storage_ |
| DataStorageMB > Critical | _Freeze non-critical data creation jobs_ | _Platform lead + Data governance_ | _Emergency archival + storage add-on request_ |
| HourlyPublishedPlatformEvents > Warning | _Check event publisher volume; defer non-critical events_ | _Integration team_ | _Spread event publishing across hours_ |

---

## 9. Review Schedule

| Review Activity | Frequency | Owner |
|---|---|---|
| Threshold accuracy review | _Quarterly_ | _Platform Architect_ |
| New limit coverage assessment | _Each Salesforce release_ | _Platform Team_ |
| Alert fatigue assessment | _Monthly_ | _On-call rotation lead_ |
| Storage trend projection update | _Quarterly_ | _Data Governance_ |

---

## Sign-Off

| Role | Name | Date | Approved? |
|---|---|---|---|
| Platform Architect | | | |
| Integration Lead | | | |
| Data Governance Lead | | | |
