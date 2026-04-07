# Examples — Marketing Cloud SQL Queries

## Example 1: Clicker Segment for Last 30 Days Using _Click System Data View

**Context:** A marketing ops team needs to build a segment of subscribers who clicked any link in the last 30 days, to be used as an audience for a re-engagement journey. The target DE already exists with fields `SubscriberKey`, `EmailAddress`, and `LastClickDate`.

**Problem:** The team's initial query uses `SELECT *` and no date filter, causing it to scan the full 6-month _Click data view. On a 5-million-subscriber account this reliably hits the 30-minute timeout and writes nothing to the target DE.

**Solution:**

```sql
SELECT DISTINCT
    c.SubscriberKey,
    c.EmailAddress,
    MAX(c.EventDate) AS LastClickDate
INTO Clickers_Last_30_Days
FROM _Click c
WHERE c.EventDate >= DATEADD(DAY, -30, GETDATE())
GROUP BY c.SubscriberKey, c.EmailAddress
```

**Why it works:** The `WHERE c.EventDate >= DATEADD(DAY, -30, GETDATE())` clause leverages the indexed `EventDate` column on the _Click system data view, preventing a full-table scan. `DISTINCT` is replaced by an explicit `GROUP BY` with `MAX()` to capture the most recent click date per subscriber. `GETDATE()` is the correct T-SQL function for the current timestamp — `NOW()` and `SYSDATE()` are not available in the Marketing Cloud SQL dialect.

---

## Example 2: Enriching a Subscriber Profile DE with Bounce History

**Context:** A deliverability team wants to mark subscribers who have hard-bounced in the last 90 days in a master profile DE called `Master_Subscriber_Profile`. The DE has a Primary Key on `SubscriberKey` and an existing field `HardBounceFlag` that should be set to `Y` for affected subscribers.

**Problem:** The team tries an `INSERT INTO ... SELECT` statement (standard SQL syntax). The Query Activity fails immediately because Marketing Cloud only supports `SELECT INTO` as the output mechanism.

**Solution:**

```sql
SELECT
    b.SubscriberKey,
    b.EmailAddress,
    'Y'                        AS HardBounceFlag,
    MAX(b.EventDate)           AS LastBounceDate
INTO Master_Subscriber_Profile
FROM _Bounce b
WHERE b.BounceCategory = 'Hard bounce'
  AND b.EventDate >= DATEADD(DAY, -90, GETDATE())
GROUP BY b.SubscriberKey, b.EmailAddress
```

Query Activity action must be set to **Update** (not Overwrite) so existing rows in `Master_Subscriber_Profile` are updated in place rather than the entire DE being truncated.

**Why it works:** The `SELECT INTO` syntax is the only supported output mechanism in Marketing Cloud Query Activities. Setting the action to **Update** with a Primary Key on `SubscriberKey` causes the platform to upsert — updating matching rows and inserting new ones — without removing subscribers not present in this query's result set. The `BounceCategory` filter and `EventDate` range keep the query within the _Bounce view's retention window and prevent full-table scans.

---

## Example 3: Joining a System Data View to a Custom DE

**Context:** A team tracks campaign membership in a custom DE called `Campaign_Sends` with fields `SubscriberKey`, `JobID`, and `CampaignName`. They want to produce a report DE showing each subscriber's last open date per campaign.

**Problem:** The team joins `_Open` to `Campaign_Sends` on `EmailAddress` alone. Because one email address can belong to multiple subscribers across lists, the join produces fan-out: a single open event matches multiple Campaign_Sends rows, inflating row counts in the output DE.

**Solution:**

```sql
SELECT
    cs.CampaignName,
    o.SubscriberKey,
    o.EmailAddress,
    MAX(o.EventDate) AS LastOpenDate
INTO Campaign_Open_Summary
FROM _Open o
INNER JOIN Campaign_Sends cs
    ON cs.JobID = o.JobID
   AND cs.SubscriberKey = o.SubscriberKey
WHERE o.EventDate >= DATEADD(DAY, -90, GETDATE())
GROUP BY cs.CampaignName, o.SubscriberKey, o.EmailAddress
```

**Why it works:** The composite join key `JobID + SubscriberKey` is the correct way to join system data views to custom DEs. `JobID` uniquely identifies a send job and `SubscriberKey` uniquely identifies a subscriber within that job. This eliminates the fan-out caused by email address ambiguity. The 90-day `EventDate` filter scopes the scan to an indexed column on `_Open`.

---

## Anti-Pattern: Using Window Functions for Deduplication

**What practitioners do:** Attempt to use `ROW_NUMBER() OVER (PARTITION BY SubscriberKey ORDER BY EventDate DESC)` to pick the most recent row per subscriber — a common pattern in standard SQL environments.

**What goes wrong:** Marketing Cloud's SQL dialect does not support window functions. The query fails at runtime with a syntax error in Automation Studio. The error message is generic and does not name the unsupported feature specifically.

**Correct approach:** Replace window functions with `GROUP BY` and aggregate functions:

```sql
-- Wrong (not supported):
SELECT SubscriberKey, EmailAddress, EventDate,
       ROW_NUMBER() OVER (PARTITION BY SubscriberKey ORDER BY EventDate DESC) AS rn
FROM _Open

-- Correct:
SELECT
    SubscriberKey,
    EmailAddress,
    MAX(EventDate) AS LastOpenDate
FROM _Open
WHERE EventDate >= DATEADD(DAY, -90, GETDATE())
GROUP BY SubscriberKey, EmailAddress
```
