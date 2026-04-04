# Examples — Event Monitoring

## Example 1: Downloading Login Logs for a Compliance Audit

**Context:** A security team needs to produce a report of all login activity over the past 30 days for an external compliance audit. They need source IPs, browser types, and login status codes.

**Problem:** Practitioners often try to query the Login History standard UI page or the `LoginHistory` sObject directly for this data. While `LoginHistory` covers recent data, it does not provide the full breadth of detail (e.g., platform type, client version, session type) available in the Event Log File, and it is not suitable for bulk export to a CSV.

**Solution:**

Step 1 — Query for available Login log files:
```soql
SELECT Id, EventType, LogDate, LogFileLength, Interval
FROM EventLogFile
WHERE EventType = 'Login'
  AND LogDate = LAST_N_DAYS:30
ORDER BY LogDate DESC
```

Step 2 — Download each log file (repeat per Id from step 1):
```bash
curl -H "Authorization: Bearer $SESSION_ID" \
  "https://MyDomain.my.salesforce.com/services/data/v63.0/sobjects/EventLogFile/{Id}/LogFile" \
  --output login_log_YYYY-MM-DD.csv.gz
```

Step 3 — Decompress and inspect:
```bash
gunzip login_log_YYYY-MM-DD.csv.gz
# Open CSV; relevant columns: USER_ID, SOURCE_IP, LOGIN_STATUS,
# BROWSER_TYPE, PLATFORM_TYPE, CLIENT_VERSION, SESSION_TYPE
```

Step 4 — Filter failures for investigation:
```python
import csv
with open('login_log_YYYY-MM-DD.csv') as f:
    reader = csv.DictReader(f)
    failures = [row for row in reader if row['LOGIN_STATUS'] != 'LOGIN_NO_ERROR']
```

**Why it works:** `EventLogFile` provides the canonical structured audit record for login events. The 30-day retention window (Shield/add-on) covers the full compliance window. The CSV format is standard and importable into any SIEM or spreadsheet tool.

---

## Example 2: Configuring Real-Time Session Hijacking Detection

**Context:** A financial services org has a Salesforce Shield subscription and needs to detect and automatically notify the security team when a session token is being reused from a different IP address or browser fingerprint — a signal of session hijacking.

**Problem:** Without RTEM, the organization can only discover session hijacking the following day via EventLogFile logs. By then the attacker has already had hours of undetected access.

**Solution:**

Step 1 — Create the RTEM channel (Metadata API XML):
```xml
<!-- File: Security_Monitoring_Channel__chn.platformEventChannel -->
<?xml version="1.0" encoding="UTF-8"?>
<PlatformEventChannel xmlns="http://soap.sforce.com/2006/04/metadata">
  <channelType>event</channelType>
  <eventType>monitoring</eventType>
  <label>Security Monitoring Channel</label>
</PlatformEventChannel>
```

Step 2 — Add SessionHijackingEvent as a channel member:
```xml
<!-- File: Security_Monitoring_Channel_chn_SessionHijackingEvent.platformEventChannelMember -->
<?xml version="1.0" encoding="UTF-8"?>
<PlatformEventChannelMember xmlns="http://soap.sforce.com/2006/04/metadata">
  <eventChannel>Security_Monitoring_Channel__chn</eventChannel>
  <selectedEntity>SessionHijackingEvent</selectedEntity>
</PlatformEventChannelMember>
```

Step 3 — Create a Transaction Security Policy in Setup:
- Navigate to Setup > Security > Transaction Security Policies
- New policy: Event Type = `SessionHijackingEvent`
- Action: Send notification + Block operation
- Condition: `Score >= 0.5` (confidence threshold from ML model)

Step 4 — Query stored session hijacking events for investigation:
```soql
SELECT Id, EventDate, UserId, Score, Summary, SourceIp
FROM SessionHijackingEventStore
WHERE EventDate = LAST_N_DAYS:7
ORDER BY Score DESC
```

**Why it works:** The `SessionHijackingEvent` ML model detects token reuse from a different context and fires the RTEM event within seconds. The Transaction Security Policy provides immediate enforcement. The `SessionHijackingEventStore` object persists events for post-hoc forensics and correlation.

---

## Example 3: Identifying Anomalous Report Exports

**Context:** A data governance team suspects that a set of user accounts are exporting sensitive Salesforce reports in bulk — a potential data exfiltration pattern.

**Problem:** Standard report run history visible in the UI is limited and does not show export volume by user. The security team needs to quantify report export events per user over the past 14 days.

**Solution:**

Step 1 — Query Report event log files:
```soql
SELECT Id, LogDate, LogFileLength
FROM EventLogFile
WHERE EventType = 'Report'
  AND LogDate = LAST_N_DAYS:14
ORDER BY LogDate DESC
```

Step 2 — Download and aggregate (Python pseudocode):
```python
import csv, collections, gzip, io

user_export_count = collections.Counter()

for log_id in log_ids:
    content = download_log_file(log_id)  # REST GET, returns bytes
    with gzip.open(io.BytesIO(content)) as gz:
        reader = csv.DictReader(io.TextIOWrapper(gz))
        for row in reader:
            if row.get('EXPORT_FILE_FORMAT'):  # non-empty = export occurred
                user_export_count[row['USER_ID']] += 1

# Top exporters
for user_id, count in user_export_count.most_common(20):
    print(f"{user_id}: {count} exports")
```

Step 3 — For near-real-time coverage, query `ReportAnomalyEventStore`:
```soql
SELECT Id, EventDate, UserId, Score, ReportId, Summary
FROM ReportAnomalyEventStore
WHERE EventDate = LAST_N_DAYS:14
ORDER BY Score DESC
```

**Why it works:** The `Report` EventLogFile contains an `EXPORT_FILE_FORMAT` column populated only when the report was exported (not just viewed). The ML-powered `ReportAnomalyEvent` provides a risk score for unusual export patterns without requiring manual threshold calibration.

---

## Anti-Pattern: Polling EventLogFile for Real-Time Incident Response

**What practitioners do:** When an incident is reported, practitioners write scripts that poll `EventLogFile` on a 5–15 minute cycle to "stay current" on suspicious activity.

**What goes wrong:** EventLogFile records for a given `LogDate` do not appear until the day after, regardless of polling frequency. A script polling for today's Login logs will return no results until the following UTC day. The practitioner believes their monitoring is current when it is actually 24+ hours stale for any ongoing attack.

**Correct approach:** Use Real-Time Event Monitoring storage objects (`LoginEventStream`, `ApiEventStream`, etc.) for same-day data. Use Transaction Security Policies for real-time enforcement. Reserve EventLogFile for historical analysis and compliance exports.
