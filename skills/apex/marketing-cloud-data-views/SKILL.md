---
name: marketing-cloud-data-views
description: "Use this skill when identifying, querying, or troubleshooting the built-in system data views in Salesforce Marketing Cloud (e.g., _Sent, _Open, _Click, _Bounce, _Subscribers, _Job). Trigger keywords: SFMC system data views, underscore data views, _Subscribers status, _Job metadata, data retention marketing cloud, data view schema, MC engagement reporting SQL. NOT for custom Data Extensions, NOT for Data Cloud (CDP) data streams, NOT for SOQL against Salesforce CRM sObjects, NOT for Query Activity SQL syntax in general (use marketing-cloud-sql-queries instead)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
  - Operational Excellence
triggers:
  - "How do I find out which subscribers bounced in the last 30 days using Marketing Cloud system data?"
  - "What fields are available in the _Sent data view and how long does it retain data?"
  - "My Marketing Cloud query joining _Open to _Click is returning duplicate rows — what join key should I use?"
  - "How do I get subscriber status (active, unsubscribed, held) from Marketing Cloud without exporting a list?"
  - "What system data views exist in Marketing Cloud and what is each one used for?"
  - "I need email send metadata like subject line and from name for each job — where is that stored in Marketing Cloud?"
  - "Can I query Marketing Cloud data views through the REST API or do I need Automation Studio?"
tags:
  - marketing-cloud
  - system-data-views
  - automation-studio
  - sql-query-activity
  - engagement-data
  - subscriber-management
  - data-retention
inputs:
  - Business question or reporting goal (e.g., bounce rate, click-through rate, suppression list build)
  - "Target date range (note: engagement views retain only ~6 months of rolling data)"
  - Available join keys (SubscriberKey, JobID, EmailAddress)
  - Target Data Extension name and schema for SELECT INTO output
  - Whether the downstream use case is segmentation, suppression, reporting, or subscriber status sync
outputs:
  - Identification of the correct system data view(s) and their schemas
  - SQL SELECT INTO statement referencing the appropriate data views
  - Guidance on join keys, date scoping, and retention window constraints
  - Decision table for which data view to use per business question
  - Review checklist for query correctness and data completeness
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# Marketing Cloud Data Views

This skill activates when a practitioner needs to understand, locate, or query the built-in system data views in Salesforce Marketing Cloud — read-only system tables prefixed with an underscore (e.g., `_Sent`, `_Open`, `_Click`) that are queryable only through SQL Query Activities in Automation Studio. It covers schema reference, data retention windows, join key patterns, and the access model for each view. It does not replace the `marketing-cloud-sql-queries` skill, which covers T-SQL syntax and Query Activity mechanics in full.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the query target is a system data view (underscore-prefixed), not a custom Data Extension. System data views cannot be created, modified, or accessed via REST/SOAP API — they are only available inside SQL Query Activities in Automation Studio.
- Identify the retention window for the views involved. All engagement data views (_Sent, _Open, _Click, _Bounce, _Job, _Complaint) retain approximately 6 months of rolling data. The `_Subscribers` view reflects current subscriber state and has no expiry. Querying engagement views for data older than 6 months returns incomplete results with no error or warning.
- Establish the composite join key. When joining between any two system data views, or joining a system data view to a custom DE, use `JobID + SubscriberKey` as the composite key. Joining on `EmailAddress` alone causes fan-out because one email address can map to multiple SubscriberKey values across lists and business units.

---

## Core Concepts

### System Data Views Are Read-Only System Tables

System data views are pre-built, platform-managed tables that record every trackable subscriber event across the Marketing Cloud account. They are identified by an underscore prefix (e.g., `_Sent`, `_Open`). They cannot be modified, schema-extended, truncated, or called through external APIs. They are not visible in Contact Builder or the Data Extension Navigator. The only mechanism to access their data is a SQL Query Activity running inside Automation Studio.

This is a hard platform constraint, not a configuration choice. There is no REST API endpoint, no SOAP call, and no Marketing Cloud Connect passthrough that exposes system data view data. Any architecture that relies on polling these views via API is fundamentally broken.

### Data Retention and Rolling Windows

All engagement-related system data views retain approximately 6 months of rolling data. Salesforce does not publish an exact row-expiry policy — the ~6-month figure is the documented and observed behavior. Once data ages out, it is permanently gone and cannot be recovered.

- `_Sent`, `_Open`, `_Click`, `_Bounce`, `_Job`, `_Complaint`: ~6 months rolling
- `_Subscribers`: current subscriber state; no expiry; reflects latest status for every subscriber in the business unit
- `_SMSLog`, `_UndeliveredSMS`: rolling retention similar to email engagement views

Practical implication: any long-term engagement history (loyalty tiers, annual re-engagement windows) must be persisted to a custom Data Extension incrementally, since querying a system data view for a 12-month window will silently return only the most recent 6 months.

### Composite Join Key: JobID + SubscriberKey

When joining between system data views — for example, joining `_Sent` to `_Click` to find subscribers who clicked after a send — always use the composite key `JobID + SubscriberKey`. `JobID` identifies a specific email send job; `SubscriberKey` identifies the subscriber within that job. Relying on `EmailAddress` alone produces a Cartesian fan-out because:

1. One email address can appear under multiple `SubscriberKey` values across lists and imports.
2. System data views record events per `SubscriberKey`, not per `EmailAddress`.

Using only `JobID` as a join key also causes fan-out because a single job sends to many subscribers. Both fields are required.

### SELECT INTO Is the Only Output Mechanism

All SQL queries against system data views must use the `SELECT INTO` syntax to write results into a pre-existing target Data Extension. There are no direct result sets, no response objects, no cursors. The target DE must exist before the query runs. Column names in the SELECT list must match DE field names exactly (case-insensitive matching). Any column omitted from the SELECT list receives a NULL or DE-defined default value.

This architecture means that real-time queries against data views are not possible. Data views must be pre-queried on a schedule via Automation Studio, with results staged in a custom DE that downstream automation or API calls can then read.

---

## Common Patterns

### Pattern 1: Build a Bounce Suppression List from _Bounce

**When to use:** After a campaign, identify hard-bounce subscribers and stage them for suppression before the next send.

**How it works:** Query `_Bounce` with a date filter and BounceType filter, then write to a suppression DE. Use `SubscriberKey` as the Primary Key of the target DE and set Query Activity action to Update so repeated runs append without duplicating.

```sql
SELECT DISTINCT
    b.SubscriberKey,
    b.EmailAddress,
    b.BounceType,
    MAX(b.EventDate) AS LastBounceDate
INTO Suppression_Bounced_Subscribers
FROM _Bounce b
WHERE b.EventDate >= DATEADD(DAY, -90, GETDATE())
  AND b.BounceType = 'HardBounce'
GROUP BY b.SubscriberKey, b.EmailAddress, b.BounceType
```

**Why not the alternative:** Pulling bounce data via the REST API's Bounce event tracking endpoint returns event-level records with no SQL filtering capability and subject to separate API rate limits. System data views give efficient set-based access.

### Pattern 2: Enrich Send History with Job Metadata from _Job

**When to use:** Building an engagement history DE that includes the email subject line and from-name alongside subscriber-level events, typically for reporting or customer service lookups.

**How it works:** Join `_Sent` to `_Job` on `JobID`. The `_Job` view stores the send job attributes (subject, from name, send date, email name). Always scope the date range to avoid full-table scans on both views.

```sql
SELECT
    s.SubscriberKey,
    s.EmailAddress,
    s.EventDate AS SentDate,
    j.EmailName,
    j.Subject,
    j.FromName
INTO Send_History_Enriched
FROM _Sent s
INNER JOIN _Job j ON s.JobID = j.JobID
WHERE s.EventDate >= DATEADD(DAY, -30, GETDATE())
```

**Why not the alternative:** `_Sent` alone does not contain email subject or from-name. Storing this in a single DE requires a join to `_Job` at query time, rather than repeated REST API calls to retrieve job metadata per send.

### Pattern 3: Subscriber Status Audit from _Subscribers

**When to use:** Identifying which subscribers are currently active, unsubscribed, held, or bounced across the business unit, for compliance audits or list health reporting.

**How it works:** Query `_Subscribers` with a Status filter. This view reflects current state and is not bound by a rolling retention window, making it suitable for full-account subscriber scans.

```sql
SELECT
    sub.SubscriberKey,
    sub.EmailAddress,
    sub.Status,
    sub.DateUnsubscribed,
    sub.DateHeld
INTO Subscriber_Status_Audit
FROM _Subscribers sub
WHERE sub.Status IN ('Unsubscribed', 'Bounced', 'Held')
```

**Why not the alternative:** Exporting the All Subscribers list via the SOAP API is rate-limited, paginated, and not filterable by status on the server side. A single Query Activity run against `_Subscribers` is far more efficient for large account populations.

---

## Decision Guidance

| Business Question | Data View to Use | Key Join / Filter |
|---|---|---|
| Which subscribers received a specific send? | `_Sent` | Filter by `JobID`; join to `_Job` for email name |
| Which subscribers opened any email in the past 60 days? | `_Open` | `EventDate >= DATEADD(DAY, -60, GETDATE())` |
| Which subscribers clicked a link? | `_Click` | `EventDate` scoped; join to `_Sent` on `JobID + SubscriberKey` |
| Which subscribers hard-bounced? | `_Bounce` | Filter `BounceType = 'HardBounce'`; use `DISTINCT SubscriberKey` |
| What is the current opt-in/opt-out status of subscribers? | `_Subscribers` | Filter by `Status`; no date constraint needed |
| What was the subject line and from-name for a send? | `_Job` | Join to `_Sent` on `JobID` |
| Did a subscriber mark an email as spam? | `_Complaint` | Filter by `EventDate`; join to `_Sent` on `JobID + SubscriberKey` |
| Need engagement data older than 6 months | Custom DE (pre-persisted) | Cannot retrieve from system views — must have been staged previously |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Identify the business question and map it to the correct data view.** Use the decision table above to determine which system data view(s) hold the required data. Confirm whether the question involves current state (`_Subscribers`) or time-bound events (all others).
2. **Check the date range against the retention window.** If the required lookback exceeds ~6 months for any engagement view, clarify with the requester whether a pre-persisted custom DE exists. Do not promise data that has aged out of the system view.
3. **Determine the target Data Extension schema.** Confirm the target DE exists and its field names match the columns to be selected. Establish whether the Query Activity action should be Overwrite (full refresh) or Update (append/upsert based on Primary Key).
4. **Construct the SELECT INTO query.** Reference the correct data view(s). Apply a date WHERE clause on `EventDate` scoped to the minimum necessary window. Use `JobID + SubscriberKey` as the composite join key for any cross-view join. Use T-SQL functions (`GETDATE()`, `DATEADD()`, `CONVERT()`).
5. **Validate join keys and filter logic.** Review every JOIN condition. Ensure no join uses `EmailAddress` as the sole key. Confirm DISTINCT or GROUP BY is used where the query could return duplicate `SubscriberKey` rows.
6. **Test in Query Studio before embedding in Automation.** Run the query interactively in Query Studio (Salesforce Labs AppExchange) to verify row count and output shape. Confirm the query completes well under the 30-minute timeout.
7. **Embed in Automation Studio and monitor.** Set Query Activity action explicitly. Schedule the automation. After the first run, confirm target DE row count and review Automation Studio activity history for errors or timeout warnings.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] The correct system data view is identified for the business question (see decision table)
- [ ] Date range is scoped to 6 months or less for engagement views (_Sent, _Open, _Click, _Bounce, _Job, _Complaint)
- [ ] SELECT INTO targets a pre-existing Data Extension with matching field names
- [ ] Query Activity action (Overwrite vs Update) is set explicitly and appropriate for the use case
- [ ] All cross-view joins use `JobID + SubscriberKey` as composite key — not EmailAddress alone
- [ ] DISTINCT or GROUP BY is applied where duplicate SubscriberKey rows are possible
- [ ] T-SQL date functions used (`GETDATE()`, `DATEADD()`) — no MySQL or ANSI equivalents
- [ ] Query tested in Query Studio and completes within the 30-minute limit

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **No API Access — SQL Only** — System data views cannot be queried through the Marketing Cloud REST or SOAP APIs. There is no endpoint that exposes `_Sent`, `_Open`, or any other data view. The only access path is a SQL Query Activity inside Automation Studio. Any architecture that routes API calls to these views will fail silently or return generic errors.
2. **6-Month Rolling Window Returns No Error on Out-of-Range Queries** — If a query requests data older than ~6 months, the platform returns zero rows for the aged-out period with no warning or error message. The query runs successfully with an incomplete result set. Practitioners routinely misdiagnose this as a filter problem.
3. **_Subscribers Reflects Current State Only — No History** — The `_Subscribers` view shows the subscriber's current status. It does not retain previous status values. If a subscriber was unsubscribed and then re-opted in, only the current "Active" status is visible. Point-in-time status history must be captured incrementally to a custom DE.
4. **JobID Is Required in Cross-View Joins — Not Optional** — Omitting `JobID` from a join between `_Sent` and `_Click` produces a Cartesian product across all jobs in the query window, multiplying row counts by the number of jobs. This is a silent data correctness bug — the query succeeds but returns many times more rows than expected.
5. **_Job View Stores JobID as Integer — Type Mismatch Causes Silent Empty Join** — If the custom DE used to stage JobIDs stores them as Text rather than Number, an INNER JOIN to `_Job` on `JobID` can return zero rows due to implicit type mismatch in T-SQL. Always confirm the data type of `JobID` in any DE that joins to system views.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Data view selection decision | Identifies the correct system data view(s) for the business question and explains why |
| SQL SELECT INTO statement | Complete T-SQL query ready for Automation Studio Query Activity |
| Query Activity configuration note | Target DE name, Primary Key field, and action setting (Overwrite vs Update) |
| Data retention warning (if applicable) | Flags if the requested date range exceeds the ~6-month retention window |

---

## Related Skills

- data/marketing-cloud-sql-queries — Use for T-SQL syntax, T-SQL dialect rules, date functions, and Query Activity performance optimization; this skill complements data-views by covering the query language layer
- data/data-extension-design — Use when designing the target or intermediate Data Extension schema that stores query output from system data views
- admin/marketing-cloud-engagement-setup — Use when the underlying Automation Studio or business unit configuration needs to be validated before query work begins
