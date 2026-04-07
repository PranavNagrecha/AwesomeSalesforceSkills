# Marketing Cloud SQL Queries — Work Template

Use this template when writing or debugging a SQL Query Activity in Salesforce Marketing Cloud Automation Studio.

## Scope

**Skill:** `marketing-cloud-sql-queries`

**Request summary:** (describe what the user needs — e.g., "segment openers from last 90 days into RE_Engage_DE")

---

## Context Gathered

Answer these before writing any SQL:

- **Target DE name:** (e.g., `Engaged_Subscribers_90D`)
- **Target DE Primary Key field:** (e.g., `SubscriberKey`)
- **Query Activity action:** [ ] Overwrite  [ ] Update  ← _must be explicitly set_
- **Source tables/views:** (list each — e.g., `_Open`, `Campaign_Sends_DE`)
- **Date range required:** (max 6 months for system data views — specify days, e.g., 90)
- **Join keys available:** (e.g., `SubscriberKey`, `JobID`, `EmailAddress` — note which to use)
- **Deduplication needed?** [ ] Yes — use `GROUP BY` + `MAX()`  [ ] No
- **Row count expectation:** (approximate, used to sanity-check output)

---

## Checklist: Before Writing SQL

- [ ] Confirmed target DE exists with correct field names and Primary Key
- [ ] Confirmed Query Activity action (Overwrite vs Update) is appropriate for this use case
- [ ] Date range is 6 months or less for any system data view source
- [ ] Identified indexed columns to use in WHERE and JOIN clauses

---

## SQL Query Draft

```sql
SELECT
    -- List columns explicitly — no SELECT *
    <source_alias>.<Field1>,
    <source_alias>.<Field2>,
    -- For deduplication: MAX(<source_alias>.EventDate) AS LastEventDate
INTO <Target_DE_Name>
FROM <SourceTable_or_SystemDataView> <source_alias>
-- JOIN example (use composite key for system data views):
-- INNER JOIN <CustomDE> de
--     ON de.JobID = <source_alias>.JobID
--    AND de.SubscriberKey = <source_alias>.SubscriberKey
WHERE <source_alias>.EventDate >= DATEADD(DAY, -<N>, GETDATE())
  -- AND additional indexed-column filters
-- GROUP BY <source_alias>.<Field1>, <source_alias>.<Field2>
-- HAVING COUNT(*) > 1  -- if aggregation filter needed
```

**Substitution guide:**

| Placeholder | Replace with |
|---|---|
| `<Target_DE_Name>` | Exact name of the existing target Data Extension |
| `<SourceTable_or_SystemDataView>` | e.g., `_Open`, `_Click`, `_Sent`, or a custom DE name |
| `<source_alias>` | Short alias, e.g., `o` for `_Open` |
| `<Field1>`, `<Field2>` | Column names that match the target DE field names exactly |
| `<N>` | Number of days to look back (max 180 for system data views) |

---

## Checklist: After Writing SQL

- [ ] `SELECT INTO` syntax used — no `INSERT INTO ... SELECT`
- [ ] No `NOW()`, `SYSDATE()`, `DATE_SUB()`, or `INTERVAL` — only `GETDATE()`, `DATEADD()`, `DATEDIFF()`
- [ ] No window functions (`ROW_NUMBER OVER`, `RANK OVER`, `LEAD`, `LAG`)
- [ ] No CTEs (`WITH ... AS (`) and no temp tables (`#table`)
- [ ] NULL checks use `IS NULL` / `IS NOT NULL` — not `= NULL`
- [ ] System data view joins use `JobID + SubscriberKey` composite key — not `EmailAddress` alone
- [ ] Date range is bounded to 6 months or less for system data view sources
- [ ] Column names in SELECT list match target DE field names exactly

---

## Query Studio Validation Steps

Before embedding in Automation Studio:

1. Open Query Studio (SF Labs AppExchange app) in the correct Marketing Cloud business unit.
2. Paste the SQL — remove the `INTO <Target_DE_Name>` line for preview mode.
3. Confirm the result columns match the target DE field names.
4. Verify row count is within expected range.
5. Note approximate run time in Query Studio (full Automation run will be slower at volume).
6. If run time approaches 5+ minutes in Query Studio, narrow the date range further before production use.

---

## Automation Studio Configuration

| Setting | Value |
|---|---|
| Query Activity name | (descriptive, e.g., `SQL_Openers_90D_to_Engaged_DE`) |
| Target Data Extension | `<Target_DE_Name>` |
| Action | Overwrite / Update (circle one) |
| Schedule | (cron or trigger) |
| Error notification | (email or Automation Studio alert) |

---

## Notes

(Record any deviations from the standard pattern, business logic edge cases, or known data quality issues with source DEs.)
