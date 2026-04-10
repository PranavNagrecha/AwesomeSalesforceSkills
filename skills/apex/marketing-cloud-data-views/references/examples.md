# Examples — Marketing Cloud Data Views

## Example 1: Identifying Active Clickers in the Last 90 Days for a Re-engagement Campaign

**Context:** A marketing team wants to build a segment of subscribers who clicked at least one email in the past 90 days for a loyalty campaign. They need SubscriberKey, EmailAddress, and the date of the most recent click.

**Problem:** The team initially tries to export click data from the Marketing Cloud Reports tab, but the export is limited to specific jobs, not date ranges, and does not produce a DE they can use as a sendable audience. A developer suggests a REST API call to the Tracking Events endpoint, but it returns paginated event-level records with no aggregation, making deduplication and DE population manual and slow.

**Solution:**

```sql
SELECT
    c.SubscriberKey,
    c.EmailAddress,
    MAX(c.EventDate) AS LastClickDate
INTO Clickers_Last_90_Days
FROM _Click c
WHERE c.EventDate >= DATEADD(DAY, -90, GETDATE())
GROUP BY c.SubscriberKey, c.EmailAddress
```

Configure the Query Activity action as **Overwrite** so each run produces a fresh, deduplicated segment. The target DE (`Clickers_Last_90_Days`) must exist in advance with fields: SubscriberKey (Text 254, Primary Key), EmailAddress (Email Address 254), LastClickDate (Date).

**Why it works:** `_Click` is a system data view that records every tracked click event. Using `MAX(EventDate)` with `GROUP BY` deduplicates subscribers who clicked multiple times, producing one row per subscriber with the most recent click date. The 90-day WHERE clause keeps the query well within the 6-month retention window and avoids a full-table scan that would risk a 30-minute timeout.

---

## Example 2: Enriching Send History with Job Metadata for a Customer Service Lookup Tool

**Context:** A customer service team needs a DE they can query (via Data Extension Report or SSJS) to look up what emails a given subscriber received, including subject line and send date. The system data views alone do not surface subject line — that lives in `_Job`, not `_Sent`.

**Problem:** An initial implementation queries `_Sent` only and stores event timestamps, but the CS team also needs the email subject to answer subscriber complaints. Fetching the `_Job` metadata separately per subscriber via REST API is slow and adds complexity. A developer attempts to join `_Sent` to `_Job` on EmailAddress only — this fails because `_Job` does not store EmailAddress as a column; it stores job-level metadata keyed on `JobID`.

**Solution:**

```sql
SELECT
    s.SubscriberKey,
    s.EmailAddress,
    s.EventDate           AS SentDate,
    j.JobID,
    j.EmailName,
    j.Subject,
    j.FromName,
    j.FromEmail
INTO CS_Send_History_Enriched
FROM _Sent s
INNER JOIN _Job j ON s.JobID = j.JobID
WHERE s.EventDate >= DATEADD(DAY, -60, GETDATE())
```

Set Query Activity action to **Overwrite** and schedule daily. The target DE (`CS_Send_History_Enriched`) needs fields: SubscriberKey, EmailAddress, SentDate, JobID (Number), EmailName, Subject, FromName, FromEmail.

**Why it works:** `_Job` stores one row per send job, containing the job-level metadata (subject, from details, send date, email name). Joining `_Sent` to `_Job` on `JobID` produces subscriber-level rows enriched with job metadata. The join on `JobID` alone is correct here because the intent is to enrich each `_Sent` row with its corresponding job's subject — there is no fan-out risk because `_Job` has exactly one row per `JobID`.

---

## Example 3: Building a Subscriber Health Report Using _Subscribers and _Bounce

**Context:** A deliverability team needs a monthly health report showing current opt-in status alongside historical bounce activity for each subscriber. They want to identify subscribers who are still "Active" in `_Subscribers` but have hard-bounced in the last 90 days — a sign of stale or invalid addresses.

**Problem:** The team queries `_Subscribers` and `_Bounce` in separate Query Activities and tries to join them in a spreadsheet export. The manual join introduces latency and human error. A developer attempts to join the two views using EmailAddress as the key, which produces fan-out rows for subscribers who appear under multiple SubscriberKey values.

**Solution:**

```sql
SELECT
    sub.SubscriberKey,
    sub.EmailAddress,
    sub.Status            AS CurrentStatus,
    sub.DateUnsubscribed,
    b.BounceType,
    MAX(b.EventDate)      AS LastBounceDate
INTO Subscriber_Health_Report
FROM _Subscribers sub
INNER JOIN _Bounce b
    ON sub.SubscriberKey = b.SubscriberKey
WHERE sub.Status = 'Active'
  AND b.BounceType = 'HardBounce'
  AND b.EventDate >= DATEADD(DAY, -90, GETDATE())
GROUP BY
    sub.SubscriberKey,
    sub.EmailAddress,
    sub.Status,
    sub.DateUnsubscribed,
    b.BounceType
```

**Why it works:** Joining `_Subscribers` to `_Bounce` on `SubscriberKey` (without `JobID`) is correct in this case because the intent is subscriber-level status correlation, not event-to-event correlation. `JobID` is required in join patterns that need to correlate two event types for the same send (e.g., who opened AND clicked the same job). For subscriber-to-event joins where any job is acceptable, `SubscriberKey` alone is the correct key.

---

## Anti-Pattern: Querying Data Views Through the REST API

**What practitioners do:** Attempt to retrieve `_Sent` or `_Open` data by calling the Marketing Cloud REST Tracking Events endpoint or the SOAP RetrieveRequest with ObjectType "SentEvent", expecting to receive the same data as the system data views.

**What goes wrong:** The REST/SOAP Tracking Events APIs return event data from a different internal store than the SQL data views. The REST API does not expose the full system data view schema (e.g., `_Job` fields are not included), returns paginated records that require custom aggregation, and is subject to API call limits. More importantly, the system data views (`_Sent`, `_Click`, etc.) are not accessible through any REST or SOAP API endpoint — attempting to do so either fails with an error or returns a completely different data set with different retention semantics.

**Correct approach:** Stage data view data into a custom Data Extension using a SQL Query Activity on a scheduled Automation. Expose that custom DE to downstream systems via the Data Extension REST API (`/data/v1/customobjectdata/key/<externalKey>/rowset`) or via SSJS within Marketing Cloud.
