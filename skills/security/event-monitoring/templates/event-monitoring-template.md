# Event Monitoring — Work Template

Use this template when working on an Event Monitoring task. Fill in each section before starting implementation.

---

## Scope

**Skill:** `event-monitoring`

**Request summary:** (describe what the user needs — e.g., "download Login logs for last 30 days", "set up real-time session hijacking detection", "investigate suspicious report exports")

---

## Context Gathered

Answer these before proceeding:

- **License tier:** Shield / Event Monitoring add-on / Free (5 types only)
- **Mode required:** Batch (EventLogFile) / Real-Time (RTEM streaming) / Both
- **Event types needed:** (e.g., Login, Report, ApiAnomaly, SessionHijacking, ContentTransfer)
- **Retention window required:** (e.g., 7 days, 30 days, same-day)
- **Integration target:** SIEM / Spreadsheet / Custom app / Transaction Security enforcement
- **Permissions confirmed:** View Event Log Files / View Real-Time Event Monitoring Data

---

## Event Log File Query (Batch Mode)

Customize for the target event type and date range:

```soql
SELECT Id, EventType, LogDate, LogFileLength, Interval, Sequence
FROM EventLogFile
WHERE EventType = '<<EVENT_TYPE>>'   -- e.g., Login, Report, API, ContentTransfer
  AND LogDate = LAST_N_DAYS:<<DAYS>> -- e.g., 30
  AND Interval = 'Daily'             -- change to 'Hourly' if Shield + hourly needed
ORDER BY LogDate DESC
```

Download command for each log (replace `{Id}` and `{SESSION_ID}`):

```bash
curl -H "Authorization: Bearer {SESSION_ID}" \
  "https://<<MY_DOMAIN>>.my.salesforce.com/services/data/v63.0/sobjects/EventLogFile/{Id}/LogFile" \
  --output "<<EVENT_TYPE>>_<<YYYY-MM-DD>>.csv.gz"
```

Decompress:
```bash
gunzip <<EVENT_TYPE>>_<<YYYY-MM-DD>>.csv.gz
```

---

## Real-Time Event Monitoring Setup (RTEM Mode)

### PlatformEventChannel (Metadata API XML)

```xml
<!-- File: <<ChannelName>>__chn.platformEventChannel -->
<?xml version="1.0" encoding="UTF-8"?>
<PlatformEventChannel xmlns="http://soap.sforce.com/2006/04/metadata">
  <channelType>event</channelType>
  <eventType>monitoring</eventType>
  <label><<Channel Label>></label>
</PlatformEventChannel>
```

### PlatformEventChannelMember (one per event type)

```xml
<!-- File: <<ChannelName>>_chn_<<EventType>>.platformEventChannelMember -->
<?xml version="1.0" encoding="UTF-8"?>
<PlatformEventChannelMember xmlns="http://soap.sforce.com/2006/04/metadata">
  <eventChannel><<ChannelName>>__chn</eventChannel>
  <selectedEntity><<EventType>></selectedEntity>  <!-- e.g., LoginEvent, ApiAnomalyEvent -->
</PlatformEventChannelMember>
```

---

## Threat Detection / Storage Object Query

For querying persisted RTEM events (replace event store name as needed):

```soql
-- Session Hijacking
SELECT Id, EventDate, UserId, Score, Summary, SourceIp
FROM SessionHijackingEventStore
WHERE EventDate = LAST_N_DAYS:<<DAYS>>
ORDER BY Score DESC

-- API Anomaly
SELECT Id, EventDate, UserId, Score, EvaluationTime, Operation
FROM ApiAnomalyEventStore
WHERE EventDate = LAST_N_DAYS:<<DAYS>>
ORDER BY Score DESC

-- Report Anomaly
SELECT Id, EventDate, UserId, Score, ReportId, Summary
FROM ReportAnomalyEventStore
WHERE EventDate = LAST_N_DAYS:<<DAYS>>
ORDER BY Score DESC

-- Credential Stuffing
SELECT Id, EventDate, UserId, Score, Summary
FROM CredentialStuffingEventStore
WHERE EventDate = LAST_N_DAYS:<<DAYS>>
ORDER BY Score DESC
```

---

## Transaction Security Policy Design

| Field | Value |
|---|---|
| Event Type | <<EventType — must support policy enforcement>> |
| Condition | <<describe the trigger condition, e.g., SourceIp not in approved ranges>> |
| Action | Block / Notify / MFA step-up / Custom Apex |
| Notification recipients | <<email addresses or in-app targets>> |
| Custom Apex class (if any) | <<class name if custom action needed>> |

---

## Approach

Which pattern from SKILL.md applies?

- [ ] Bulk Log Download for SIEM Integration
- [ ] Real-Time Threat Alerting with RTEM + Transaction Security
- [ ] SOQL-Based Login Forensics
- [ ] Other: (describe)

---

## Checklist

- [ ] Confirmed org has Shield or Event Monitoring add-on (not free 5-type tier)
- [ ] User has correct permission: "View Event Log Files" or "View Real-Time Event Monitoring Data"
- [ ] Log downloads use separate REST GET on `/sobjects/EventLogFile/{Id}/LogFile`, not inline SOQL
- [ ] SOQL queries filter on `LogDate`, not `CreatedDate`
- [ ] For RTEM: PlatformEventChannel has `eventType=monitoring`
- [ ] Transaction Security Policy event types confirmed to support enforcement
- [ ] Retention window matches license tier
- [ ] Hourly vs. daily Interval requirement confirmed against license

---

## Notes

(Record any deviations from the standard pattern and the reason. E.g., "Used hourly Interval — confirmed org has Shield license. Reduced date range to 7 days due to log file size concerns.")
