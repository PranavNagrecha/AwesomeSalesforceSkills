# Gotchas — Marketing Cloud SQL Queries

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Overwrite Action Silently Empties the Target DE on Zero-Row Results

**What happens:** The Query Activity action defaults to **Overwrite**, which truncates the entire target Data Extension before inserting the query result. If the query returns zero rows (e.g., due to a typo in a date filter, or a source DE that is temporarily empty), the target DE is completely wiped with no error raised. Automation Studio marks the activity as successful.

**When it occurs:** Any Query Activity where the action was not explicitly set to **Update**, especially when the WHERE clause date range is narrow or references a volatile condition. Particularly dangerous on master profile DEs or suppression lists — a zero-row wipe silently removes all suppression records.

**How to avoid:** Always explicitly set the Query Activity action to **Update** for any DE that must retain rows across query runs. Reserve **Overwrite** only for staging DEs that are fully rebuilt each cycle. Before setting Overwrite on a critical DE, add a row-count guard: test the query in Query Studio first and confirm it returns rows before enabling the automation.

---

## Gotcha 2: System Data View Retention Is ~6 Months but the Query Returns No Error for Out-of-Range Dates

**What happens:** Queries against system data views (_Sent, _Open, _Click, _Bounce, _Job) silently return zero rows for dates older than approximately 6 months. The query completes successfully, reports no error, and writes zero rows to the target DE (which, combined with Overwrite action, also wipes the target).

**When it occurs:** Whenever a date filter references a range exceeding the retention window — for example `WHERE EventDate >= DATEADD(MONTH, -12, GETDATE())`. The system does not warn that data beyond 6 months is unavailable; it simply returns no rows for that period.

**How to avoid:** Always scope system data view queries to a maximum of 6 months. For historical analysis beyond 6 months, data must have been pre-extracted into a custom DE during the retention window. Document the retention limit in any automation that reads from system data views so future editors do not silently break the query by extending the date range.

---

## Gotcha 3: Non-Indexed Column WHERE Clauses Trigger Full-Table Scans and Timeouts

**What happens:** Filtering on a non-indexed column in a system data view or large DE causes a full-table scan. On accounts with millions of send events, full-table scans reliably exceed the 30-minute query timeout. The query is killed with no partial results written to the target DE.

**When it occurs:** Common examples include filtering `_Sent` on `EmailName` instead of `EventDate`, or filtering a subscriber DE on a custom attribute field that is not the Primary Key. The timeout error in Automation Studio is generic and does not identify which column caused the scan.

**How to avoid:** Always include a WHERE clause on an indexed column — primarily `EventDate` for system data views and the Primary Key field for custom DEs. Consult the Salesforce Marketing Cloud SQL Reference to confirm which columns are indexed for each system data view. If a business requirement forces filtering on a non-indexed column, pre-filter using an indexed column to narrow the row set, then apply the non-indexed filter on the reduced result.

---

## Gotcha 4: The 30-Minute Timeout Has No Partial Commit — Target DE State Depends on Action Setting

**What happens:** When a query exceeds 30 minutes and is killed, the behavior of the target DE depends on whether the action was Overwrite or Update. With Overwrite, the target DE was truncated at the start of the run and nothing was inserted — the DE is now empty. With Update, the DE retains its prior state. This distinction is not documented in the error message.

**When it occurs:** Any long-running query that hits the timeout limit, especially on large system data views or unindexed column filters.

**How to avoid:** Monitor query run time in Automation Studio activity history. If a query regularly approaches 20 minutes, shorten the date range, add more restrictive indexed filters, or split into multiple Query Activities that write to intermediate DEs before a final union step. Set the action to **Update** rather than Overwrite on critical target DEs as a safety measure even if full-refresh semantics are intended.

---

## Gotcha 5: Query Studio Results Use a Different Execution Path Than Automation Studio

**What happens:** A query that runs successfully in Query Studio (SF Labs AppExchange) can still fail or behave differently in Automation Studio. Query Studio enforces a lower row limit on results (typically 100 rows in preview mode) and may not surface timeout errors that occur at full scale. Additionally, Query Studio does not exercise the actual SELECT INTO mechanism — it only previews the SELECT portion of the query.

**When it occurs:** When testing queries on small samples in Query Studio and then embedding them in Automation Studio without load testing, practitioners are surprised when the full-volume run times out or the target DE shape does not match expectations.

**How to avoid:** Use Query Studio for syntax validation and logic checks. Always test Automation Studio Query Activities against a real run on a representative data sample — either by temporarily reducing the date range to a short window, or by running in a sandbox MC business unit with production data replicated. Treat Query Studio as a syntax checker, not a performance validator.
