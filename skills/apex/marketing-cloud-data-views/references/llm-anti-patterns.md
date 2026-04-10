# LLM Anti-Patterns — Marketing Cloud Data Views

Common mistakes AI coding assistants make when generating or advising on Marketing Cloud Data Views.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending REST API Calls to Query System Data Views

**What the LLM generates:** Code that calls the Marketing Cloud REST API Tracking Events endpoint (e.g., `GET /data/v1/events/tracking`) or the SOAP API `RetrieveRequest` with ObjectType `SentEvent` or `ClickEvent`, claiming these return the same data as `_Sent` or `_Click` data views.

**Why it happens:** LLMs associate "query subscriber engagement data" with API patterns they have seen for other platforms. Marketing Cloud does have REST tracking event endpoints, and training data likely conflates those endpoints with system data view access. The model does not distinguish between the REST Tracking Events API (different data store, different schema, limited aggregation) and the SQL system data view access model.

**Correct pattern:**

```sql
-- System data views are ONLY accessible via SQL Query Activity in Automation Studio.
-- There is no REST or SOAP API path.

SELECT
    s.SubscriberKey,
    s.EmailAddress,
    s.EventDate AS SentDate
INTO Target_DE_Name
FROM _Sent s
WHERE s.EventDate >= DATEADD(DAY, -30, GETDATE())
```

Stage this via a scheduled Automation Studio Query Activity. Expose the output DE to external systems via the Data Extension REST API (`/data/v1/customobjectdata/key/<externalKey>/rowset`).

**Detection hint:** Any code that references `/data/v1/events/` or SOAP ObjectType containing `Event` in a data view context is likely this anti-pattern. Flag any suggestion that system data views are "queryable via API."

---

## Anti-Pattern 2: Writing SQL Without SELECT INTO Syntax

**What the LLM generates:** A standard SQL SELECT statement without a SELECT INTO clause, often accompanied by code to consume the result set:

```sql
-- WRONG: No SELECT INTO — this will fail in Automation Studio
SELECT SubscriberKey, EmailAddress, EventDate
FROM _Sent
WHERE EventDate >= DATEADD(DAY, -30, GETDATE())
```

Or an INSERT INTO pattern copied from standard SQL:

```sql
-- WRONG: INSERT INTO ... SELECT is not valid in Marketing Cloud SQL
INSERT INTO Target_DE_Name (SubscriberKey, EmailAddress)
SELECT SubscriberKey, EmailAddress
FROM _Sent
```

**Why it happens:** Standard SQL and most database training data use `SELECT` for queries and `INSERT INTO ... SELECT` for inserting query results. Marketing Cloud's T-SQL dialect uses a non-standard `SELECT ... INTO` pattern that puts the target table in the middle of the statement. This is counterintuitive and rarely appears in general SQL training data.

**Correct pattern:**

```sql
SELECT
    s.SubscriberKey,
    s.EmailAddress,
    s.EventDate AS SentDate
INTO Target_DE_Name
FROM _Sent s
WHERE s.EventDate >= DATEADD(DAY, -30, GETDATE())
```

**Detection hint:** Any generated SQL that starts with `SELECT` from a system data view but does not contain `INTO <DE_name>` between the SELECT list and the FROM clause is this anti-pattern. Also flag any `INSERT INTO` usage.

---

## Anti-Pattern 3: Joining Data Views on EmailAddress Instead of JobID + SubscriberKey

**What the LLM generates:** A join between two system data views using EmailAddress as the key:

```sql
-- WRONG: Join on EmailAddress causes fan-out
FROM _Sent s
INNER JOIN _Click c ON s.EmailAddress = c.EmailAddress
```

Or joining on SubscriberKey alone without JobID:

```sql
-- WRONG: Missing JobID causes Cartesian fan-out across all jobs
FROM _Sent s
INNER JOIN _Click c ON s.SubscriberKey = c.SubscriberKey
```

**Why it happens:** EmailAddress is the most human-recognizable subscriber identifier. SubscriberKey alone seems like the natural primary key for a subscriber join. LLMs correctly identify that these are subscriber-level fields but miss the event-level join requirement: in system data views, each row is a per-job, per-subscriber event. Without JobID in the join, one subscriber's click events for all jobs in the retention window match against all of that subscriber's send events, producing a Cartesian product.

**Correct pattern:**

```sql
SELECT
    s.SubscriberKey,
    s.EmailAddress,
    s.EventDate AS SentDate,
    c.EventDate AS ClickDate
INTO Sent_With_Clicks
FROM _Sent s
INNER JOIN _Click c
    ON s.JobID = c.JobID
   AND s.SubscriberKey = c.SubscriberKey
WHERE s.EventDate >= DATEADD(DAY, -30, GETDATE())
```

**Detection hint:** Any JOIN between two system event data views (\_Sent, \_Open, \_Click, \_Bounce) that does not include `JobID` in the ON clause is this anti-pattern. Flag joins that use only `EmailAddress` or only `SubscriberKey`.

---

## Anti-Pattern 4: Claiming Data Views Retain More Than 6 Months of Engagement Data

**What the LLM generates:** SQL queries with 12-month, 24-month, or open-ended date ranges against engagement data views:

```sql
-- WRONG: Data older than ~6 months does not exist in system data views
WHERE EventDate >= DATEADD(YEAR, -1, GETDATE())
```

Or a recommendation to "query _Sent for all sends since the account was created."

**Why it happens:** LLMs do not reliably internalize platform-specific data retention limits. General SQL training associates tables as storing all historical data unless explicitly deleted. The ~6-month rolling window is a Marketing Cloud-specific constraint that is not inferrable from SQL syntax or general database knowledge.

**Correct pattern:**

```sql
-- CORRECT: Scope to within the ~6-month retention window
WHERE EventDate >= DATEADD(DAY, -180, GETDATE())
```

For longer historical windows, explain that data must be continuously staged to a custom DE:

```
Long-term engagement history requires an incremental staging automation that runs on a
weekly or monthly cadence and appends results to a permanent custom Data Extension.
System data views cannot retain data beyond approximately 6 months.
```

**Detection hint:** Any WHERE clause on a system data view's EventDate that uses DATEADD with more than 180 days, or any query without a date WHERE clause entirely, is this anti-pattern.

---

## Anti-Pattern 5: Suggesting _Subscribers Can Provide Subscriber Status History

**What the LLM generates:** A recommendation to query `_Subscribers` to find when a subscriber was unsubscribed, or to build a historical opt-in/opt-out audit trail from `_Subscribers` alone:

```sql
-- MISLEADING: _Subscribers shows current state only
-- DateUnsubscribed reflects the most recent unsubscribe date, not a history
SELECT SubscriberKey, Status, DateUnsubscribed
FROM _Subscribers
```

Often accompanied by the claim that joining `_Subscribers` to itself or using a date filter will reveal historical states.

**Why it happens:** `_Subscribers` contains a `DateUnsubscribed` field, which appears to offer temporal context. LLMs extrapolate from this that the view can answer "was this subscriber unsubscribed on date X?" But `DateUnsubscribed` stores only the most recent unsubscribe event. If the subscriber has since re-opted in, `DateUnsubscribed` may still hold a historical date while `Status` shows `Active`.

**Correct pattern:**

```
_Subscribers reflects current subscriber state only. It does not retain status history.
To answer "was this subscriber unsubscribed on date X?", you need a custom Data Extension
that records daily or weekly subscriber status snapshots via a scheduled Query Activity:

SELECT
    sub.SubscriberKey,
    sub.EmailAddress,
    sub.Status,
    GETDATE() AS SnapshotDate
INTO Subscriber_Status_History
FROM _Subscribers sub
```

Set Query Activity action to Update with SubscriberKey + SnapshotDate as the composite Primary Key.

**Detection hint:** Any recommendation that `_Subscribers` can answer point-in-time historical status questions, or any suggestion to filter `_Subscribers` by `DateUnsubscribed` to reconstruct status at a past date, is this anti-pattern.

---

## Anti-Pattern 6: Using MySQL or PostgreSQL Date Functions in Data View Queries

**What the LLM generates:** SQL queries against system data views using non-T-SQL date functions:

```sql
-- WRONG: NOW(), DATE_SUB(), SYSDATE() are not valid in Marketing Cloud T-SQL
WHERE EventDate >= DATE_SUB(NOW(), INTERVAL 30 DAY)
-- Or:
WHERE EventDate >= SYSDATE() - 30
-- Or:
WHERE EventDate >= CURRENT_DATE - INTERVAL '30 days'
```

**Why it happens:** Most SQL training data comes from MySQL, PostgreSQL, or ANSI SQL contexts where `NOW()`, `DATE_SUB()`, `SYSDATE()`, or `CURRENT_DATE` are idiomatic. Marketing Cloud uses a T-SQL dialect with SQL Server-style functions. The model does not reliably apply the platform constraint unless specifically prompted about the Marketing Cloud T-SQL dialect.

**Correct pattern:**

```sql
-- CORRECT: T-SQL date functions only
WHERE EventDate >= DATEADD(DAY, -30, GETDATE())
```

Key T-SQL functions valid in Marketing Cloud: `GETDATE()`, `DATEADD()`, `DATEDIFF()`, `CONVERT()`, `CAST()`, `YEAR()`, `MONTH()`, `DAY()`.

**Detection hint:** Any query against a system data view containing `NOW()`, `DATE_SUB()`, `SYSDATE()`, `CURRENT_DATE`, `DATE_TRUNC()`, or PostgreSQL/MySQL interval syntax is this anti-pattern.
