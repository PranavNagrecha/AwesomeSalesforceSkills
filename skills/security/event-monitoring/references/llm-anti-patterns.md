# LLM Anti-Patterns — Event Monitoring

Common mistakes AI coding assistants make when generating or advising on Salesforce Shield Event Monitoring.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Trying to Read LogFile Content Inline via SOQL

**What the LLM generates:** "Query `SELECT LogFile FROM EventLogFile WHERE EventType = 'Login'` to get the CSV data."

**Why it happens:** LLMs treat LogFile as a regular text field. In reality, querying LogFile returns a relative URL path, not the CSV content.

**Correct pattern:**

```
The LogFile field returns a relative URL path, not CSV bytes. To retrieve the
actual log content:

1. Query EventLogFile to get the record Id:
   SELECT Id, EventType, LogDate FROM EventLogFile WHERE EventType = 'Login'

2. Issue a separate authenticated REST GET:
   GET /services/data/v63.0/sobjects/EventLogFile/{Id}/LogFile
   Authorization: Bearer {sessionId}

3. The response is gzip-compressed CSV. Decompress before parsing.
```

**Detection hint:** If the SOQL query selects the LogFile field expecting CSV data in the result, the approach is wrong.

---

## Anti-Pattern 2: Assuming All Event Types Are Available Without Shield

**What the LLM generates:** "Query EventLogFile for ReportEvent to see who exported data" without confirming the org has Shield or the Event Monitoring add-on.

**Why it happens:** Training data discusses event types generically. LLMs do not consistently distinguish between the free 5-type tier and the paid 70+ type tier.

**Correct pattern:**

```
Without Shield or the Event Monitoring add-on, only 5 event types are available
with 1-day retention:
- Login, Logout, URI, API Total Usage, Apex Unexpected Exception

All other event types (Report, ContentTransfer, BulkApi, ApexExecution, etc.)
require Shield or the Event Monitoring add-on with 30-day retention.

Always confirm licensing before designing queries against event types beyond
the free tier.
```

**Detection hint:** If the advice queries event types beyond Login, Logout, URI, API Total Usage, and Apex Unexpected Exception without confirming Shield licensing, the query will return no results in unlicensed orgs.

---

## Anti-Pattern 3: Using EventLogFile for Same-Day Incident Response

**What the LLM generates:** "Query EventLogFile to investigate the login anomaly that happened this morning."

**Why it happens:** LLMs treat EventLogFile as a real-time query source. Training data does not consistently emphasize the 24-hour delay.

**Correct pattern:**

```
EventLogFile records have a 24-hour delay. Logs for today's date are NOT
available until tomorrow (UTC). For same-day forensics during an active
incident, use:

- LoginEventStream or other RTEM storage objects (available immediately)
- Setup > Login History UI (real-time, limited to recent records)
- Hourly log files (Shield only, still delayed by up to 1 hour)

EventLogFile is for historical analysis, not real-time incident response.
```

**Detection hint:** If the advice uses EventLogFile for investigating an event that happened today, the 24-hour delay makes this impossible.

---

## Anti-Pattern 4: Filtering EventLogFile on CreatedDate Instead of LogDate

**What the LLM generates:** `WHERE CreatedDate >= LAST_N_DAYS:7` when querying EventLogFile.

**Why it happens:** CreatedDate is the default time filter in most SOQL patterns. LLMs apply the general pattern without knowing that EventLogFile uses LogDate as the meaningful date field.

**Correct pattern:**

```
EventLogFile uses LogDate — the calendar date the log covers — not CreatedDate.
CreatedDate reflects when Salesforce generated the log record, which may differ
from the event coverage date.

Correct filter:
  SELECT Id, EventType, LogDate FROM EventLogFile
  WHERE EventType = 'Login' AND LogDate = LAST_N_DAYS:7

Using CreatedDate can return unexpected results or miss logs for the intended
date range.
```

**Detection hint:** If the SOQL query filters EventLogFile on CreatedDate rather than LogDate, the date range may not match the intended event coverage window.

---

## Anti-Pattern 5: Creating a Policy on an Unsupported RTEM Event Type

**What the LLM generates:** "Create a Transaction Security Policy on MobileEmailEvent to detect mobile data exfiltration."

**Why it happens:** LLMs see event type names in documentation and assume all RTEM events support policy enforcement. Several event types explicitly do not.

**Correct pattern:**

```
Not all RTEM event types support Transaction Security Policy enforcement.
Unsupported types include MobileEmailEvent, MobileScreenshotEvent,
IdentityVerificationEvent, and IdentityProviderEvent. A policy on an
unsupported type will NEVER fire — no error, no warning.

Always verify "Can Be Used in a Transaction Security Policy?" in the Salesforce
Object Reference before designing enforcement logic on an RTEM event type.
```

**Detection hint:** If the advice designs a Transaction Security Policy on an unsupported event type, the policy will silently produce no enforcement.

---

## Anti-Pattern 6: Treating Threat Detection Event Timestamps as Exact

**What the LLM generates:** "The SessionHijackingEvent fired at 14:32 UTC, so that is when the session was hijacked."

**Why it happens:** LLMs treat event timestamps as precise records of when the action occurred. Threat Detection ML models have a processing lag.

**Correct pattern:**

```
Threat Detection events (ApiAnomalyEvent, ReportAnomalyEvent,
SessionHijackingEvent, CredentialStuffingEvent, etc.) have a processing lag.
The EventDate field reflects when the ML model completed its evaluation — NOT
the exact moment the suspicious action occurred.

When investigating anomaly events, use the EventDate as an approximate reference
and cross-reference with LoginHistory, EventLogFile, or RTEM storage objects
for the precise activity timestamp.
```

**Detection hint:** If the advice treats a Threat Detection event timestamp as the exact time of the suspicious activity, the timeline reconstruction may be inaccurate.
