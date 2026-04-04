# Gotchas — Event Monitoring

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: LogFile Field Returns a URL Path, Not the CSV Content

**What happens:** When you query `EventLogFile` and include the `LogFile` field in your SELECT, the field value in the SOQL response is a relative URL string (e.g., `/services/data/v63.0/sobjects/EventLogFile/0AT.../LogFile`), not the actual CSV content. Attempting to parse this as CSV produces garbage or empty results.

**When it occurs:** Any time a practitioner includes `LogFile` in a SOQL SELECT clause and tries to use the value directly as log data. This is a common first-attempt mistake.

**How to avoid:** Treat the SOQL query as a log discovery step only. Use the `Id` field from the SOQL result to construct a separate authenticated REST GET request:
```
GET /services/data/v63.0/sobjects/EventLogFile/{Id}/LogFile
Authorization: Bearer {sessionId}
```
The REST response returns the actual gzip-compressed CSV bytes.

---

## Gotcha 2: EventLogFile Has a 24-Hour Delay — Today's Events Are Not Available

**What happens:** A practitioner investigating a live incident queries `EventLogFile` for today's `LogDate` and gets zero results. They assume monitoring is broken or the license is not active. In reality, EventLogFile records for a given date are generated after UTC midnight and are typically available the following day.

**When it occurs:** Any same-day forensics scenario: login investigation while an attack is ongoing, trying to see if a specific action just happened, or building a "near-real-time" dashboard with EventLogFile as the data source.

**How to avoid:** For same-day data, query the RTEM storage objects directly:
- Logins: `LoginEventStream`
- Logouts: `LogoutEventStream`
- Admin impersonation: `LoginAsEventStream`
- API calls: `ApiEventStream`

These sObjects store RTEM event data and are queryable via SOQL immediately after the event fires. EventLogFile remains the right tool for historical analysis and SIEM ingestion.

---

## Gotcha 3: Free Tier Covers Only 5 Event Types

**What happens:** An org without Shield or the Event Monitoring add-on receives EventLogFile records for only five event types: Login, Logout, URI, API Total Usage, and Apex Unexpected Exception. Attempts to query `EventLogFile WHERE EventType = 'Report'` return no results — not an error, just empty. Practitioners interpret the empty result as "no reports were run" rather than "this event type is not licensed."

**When it occurs:** Any org that has not purchased Salesforce Shield or the Event Monitoring add-on. This is especially common in Enterprise Edition orgs where Event Monitoring was never added.

**How to avoid:** Before building any event monitoring solution, verify the available event types by running:
```soql
SELECT EventType, COUNT(Id) count
FROM EventLogFile
WHERE LogDate = YESTERDAY
GROUP BY EventType
ORDER BY count DESC
```
If only Login, Logout, URI, API Total Usage, and ApexUnexpectedException appear, the full Event Monitoring add-on or Shield is not active. Contact your account team to add the subscription.

---

## Gotcha 4: Not All RTEM Events Support Transaction Security Policies

**What happens:** A practitioner designs a Transaction Security Policy against a RTEM event type (e.g., `MobileEmailEvent` or `IdentityVerificationEvent`) expecting enforcement. The policy either fails to save or silently never fires, because the event type does not support policy enforcement.

**When it occurs:** When selecting event types for Transaction Security Policies without consulting the "Can Be Used in a Transaction Security Policy?" column in the Salesforce Object Reference for RTEM objects.

**How to avoid:** Before designing a policy, confirm the event type supports enforcement. Confirmed policy-compatible types include: `ApiAnomalyEvent`, `ApiEventStream`, `BulkApiResultEvent`, `CredentialStuffingEvent`, `FileEvent`, `LoginEvent`, `ReportAnomalyEvent`, `ReportEventStream`, `SessionHijackingEvent`. Events like `MobileEmailEvent`, `MobileScreenshotEvent`, `IdentityProviderEvent`, and `IdentityVerificationEvent` do not support Transaction Security policies.

---

## Gotcha 5: Threat Detection Event Timestamps Lag Behind the Actual Activity

**What happens:** An `ApiAnomalyEvent` or `SessionHijackingEvent` fires with an `EventDate` that is several minutes or more after the actual suspicious API call or session token reuse occurred. Practitioners correlating threat detection events with other logs (e.g., Login history, ContentTransfer) against timestamps find the timestamps do not align.

**When it occurs:** Whenever ML-powered threat detection events (`ApiAnomalyEvent`, `ReportAnomalyEvent`, `SessionHijackingEvent`, `CredentialStuffingEvent`, `GuestUserAnomalyEvent`, `LoginAnomalyEvent`) are used in time-correlation workflows.

**How to avoid:** Use the `EventIdentifier` field (shared between the platform event and its storage object) to correlate the anomaly event back to the originating raw event — not timestamp proximity. The official documentation explicitly states: "This results in an expected time difference between the Event Detection Date and the Event Creation Date." Design forensic workflows around `EventIdentifier` correlation, not timestamp matching.

---

## Gotcha 6: Hourly Log Files Require Shield (Not Just the Add-On)

**What happens:** An org with only the Event Monitoring add-on (not full Salesforce Shield) queries for `Interval = 'Hourly'` EventLogFile records and receives no results. The practitioner assumes hourly logs are unavailable due to a bug or misconfiguration.

**When it occurs:** Orgs that have the Event Monitoring add-on license but not the full Salesforce Shield subscription. The add-on provides 30-day retention and all 70+ event types for daily logs, but not hourly granularity.

**How to avoid:** Hourly EventLogFile records require a Salesforce Shield subscription specifically. Verify the actual license tier with the org's Account Executive before designing solutions that depend on sub-daily granularity. For add-on customers, the best available granularity is daily `LogDate` with the 24-hour delay.
