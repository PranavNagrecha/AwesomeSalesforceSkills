# LLM Anti-Patterns — Marketing Cloud SQL Queries

Common mistakes AI coding assistants make when generating or advising on Marketing Cloud SQL Query Activities.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using NOW(), SYSDATE(), or DATE_SUB() Instead of T-SQL Date Functions

**What the LLM generates:**

```sql
SELECT SubscriberKey, EmailAddress
INTO Recent_Openers
FROM _Open
WHERE EventDate >= DATE_SUB(NOW(), INTERVAL 30 DAY)
```

**Why it happens:** LLMs are trained on large volumes of MySQL and PostgreSQL SQL, where `NOW()` and `DATE_SUB()` are standard. The Marketing Cloud SQL dialect is T-SQL-like but narrower, and this distinction is underrepresented in training data.

**Correct pattern:**

```sql
SELECT SubscriberKey, EmailAddress
INTO Recent_Openers
FROM _Open
WHERE EventDate >= DATEADD(DAY, -30, GETDATE())
```

**Detection hint:** Scan the generated SQL for `NOW()`, `SYSDATE()`, `DATE_SUB(`, `DATE_FORMAT(`, `CURDATE()`, or `INTERVAL` keyword. Any of these indicates a non-T-SQL date expression that will fail at runtime.

---

## Anti-Pattern 2: Using INSERT INTO ... SELECT Instead of SELECT INTO

**What the LLM generates:**

```sql
INSERT INTO Target_DE (SubscriberKey, EmailAddress)
SELECT SubscriberKey, EmailAddress
FROM _Open
WHERE EventDate >= DATEADD(DAY, -30, GETDATE())
```

**Why it happens:** `INSERT INTO ... SELECT` is the standard SQL pattern for inserting query results into a table. LLMs generalize from standard SQL training data and do not know that Marketing Cloud Query Activities require the `SELECT ... INTO target_DE` form exclusively.

**Correct pattern:**

```sql
SELECT
    SubscriberKey,
    EmailAddress
INTO Target_DE
FROM _Open
WHERE EventDate >= DATEADD(DAY, -30, GETDATE())
```

**Detection hint:** Look for `INSERT INTO` anywhere in the generated SQL. Marketing Cloud Query Activities do not support this syntax — any occurrence is wrong.

---

## Anti-Pattern 3: Using Window Functions (ROW_NUMBER OVER, RANK OVER)

**What the LLM generates:**

```sql
SELECT SubscriberKey, EmailAddress, EventDate,
       ROW_NUMBER() OVER (PARTITION BY SubscriberKey ORDER BY EventDate DESC) AS rn
INTO Deduped_Openers
FROM _Open
WHERE EventDate >= DATEADD(DAY, -30, GETDATE())
```

Then further instructs the user to filter `WHERE rn = 1` — which requires a subquery or CTE, also unsupported.

**Why it happens:** Window functions are the idiomatic solution for top-N-per-group deduplication in modern SQL. LLMs default to this well-established pattern without knowing it is not available in the Marketing Cloud SQL dialect.

**Correct pattern:**

```sql
SELECT
    SubscriberKey,
    EmailAddress,
    MAX(EventDate) AS LastOpenDate
INTO Deduped_Openers
FROM _Open
WHERE EventDate >= DATEADD(DAY, -30, GETDATE())
GROUP BY SubscriberKey, EmailAddress
```

**Detection hint:** Search for `OVER (`, `PARTITION BY`, `ROW_NUMBER`, `RANK(`, `DENSE_RANK`, or `LEAD(` / `LAG(`. All window functions are unsupported and will cause a runtime error.

---

## Anti-Pattern 4: Omitting the Date Range Filter on System Data Views

**What the LLM generates:**

```sql
SELECT DISTINCT
    SubscriberKey,
    EmailAddress
INTO All_Openers
FROM _Open
```

Or generates a very broad range like `DATEADD(YEAR, -2, GETDATE())`.

**Why it happens:** LLMs model "get all records" or "get recent records" as logically complete queries. They do not know that system data views in Marketing Cloud retain only approximately 6 months of data, or that an unbounded query causes a full-table scan that reliably times out on high-volume accounts.

**Correct pattern:**

```sql
SELECT DISTINCT
    SubscriberKey,
    EmailAddress
INTO All_Openers
FROM _Open
WHERE EventDate >= DATEADD(DAY, -90, GETDATE())
```

**Detection hint:** If the query references `_Open`, `_Click`, `_Sent`, `_Bounce`, or `_Job` without a `WHERE EventDate >=` clause, flag it as missing the required date scope. Date ranges exceeding 180 days should also be flagged.

---

## Anti-Pattern 5: Joining System Data Views on EmailAddress Instead of JobID + SubscriberKey

**What the LLM generates:**

```sql
SELECT
    cs.CampaignName,
    o.SubscriberKey,
    o.EventDate
INTO Campaign_Opens
FROM _Open o
INNER JOIN Campaign_Sends cs ON cs.EmailAddress = o.EmailAddress
WHERE o.EventDate >= DATEADD(DAY, -30, GETDATE())
```

**Why it happens:** Email address is the human-readable identifier and appears prominently in both system data views and custom DEs. LLMs use it as the natural join key without knowing that a single email address can map to multiple SubscriberKey values across subscriber lists in Marketing Cloud, causing join fan-out.

**Correct pattern:**

```sql
SELECT
    cs.CampaignName,
    o.SubscriberKey,
    o.EventDate
INTO Campaign_Opens
FROM _Open o
INNER JOIN Campaign_Sends cs
    ON cs.JobID = o.JobID
   AND cs.SubscriberKey = o.SubscriberKey
WHERE o.EventDate >= DATEADD(DAY, -30, GETDATE())
```

**Detection hint:** Any join between a system data view (`_Open`, `_Click`, `_Sent`, `_Bounce`) and a custom DE that uses only `EmailAddress` as the join condition should be flagged. The composite key `JobID + SubscriberKey` is always required.

---

## Anti-Pattern 6: Recommending Temp Tables, CTEs, or Stored Procedures

**What the LLM generates:**

```sql
WITH RecentOpens AS (
    SELECT SubscriberKey, MAX(EventDate) AS LastOpen
    FROM _Open
    WHERE EventDate >= DATEADD(DAY, -30, GETDATE())
    GROUP BY SubscriberKey
)
SELECT ro.SubscriberKey, s.EmailAddress
INTO Target_DE
FROM RecentOpens ro
JOIN _Subscribers s ON s.SubscriberKey = ro.SubscriberKey
```

Or recommends `CREATE TABLE #temp ...` for intermediate results.

**Why it happens:** CTEs (`WITH` clauses), temp tables (`#tmp`), and multi-statement stored procedures are standard T-SQL features. LLMs generate them as natural solutions to complex query problems without knowing that Marketing Cloud Query Activities support only a single `SELECT INTO` statement with no auxiliary DDL or multi-statement batches.

**Correct pattern:** Decompose the logic into multiple Query Activities. Write the intermediate result to a real staging DE, then reference that DE in a subsequent Query Activity.

**Detection hint:** Look for `WITH ` followed by a CTE name and `AS (`, `CREATE TABLE #`, `CREATE PROCEDURE`, or `EXEC `. All of these are unsupported and will fail at parse time.
