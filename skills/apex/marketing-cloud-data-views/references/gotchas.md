# Gotchas — Marketing Cloud Data Views

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Engagement Views Return Zero Rows for Data Older Than ~6 Months — No Error, No Warning

**What happens:** A SQL Query Activity that queries `_Sent`, `_Open`, `_Click`, `_Bounce`, or `_Job` with a WHERE clause covering a period older than approximately 6 months completes successfully, returns exit code 0 in Automation Studio, and writes zero (or fewer than expected) rows to the target DE — with no error message, no warning, and no indication that data was unavailable.

**When it occurs:** Any time the query's date range extends beyond the rolling ~6-month retention window. Common triggers: annual re-engagement campaigns ("query last 12 months of opens"), year-over-year reporting queries, or historical data migrations where the practitioner assumes the data exists in system views.

**How to avoid:** Always scope engagement data queries to 6 months or less. If longer historical windows are needed, implement an incremental staging job that runs on a weekly or monthly schedule and appends results to a permanent custom Data Extension. Document the retention boundary in the target DE's description field so downstream consumers know the effective date range.

---

## Gotcha 2: Omitting JobID from Cross-View Joins Creates Silent Cartesian Products

**What happens:** When joining two system data views — for example, `_Sent` and `_Click` — on `SubscriberKey` alone (without `JobID`), the query produces a Cartesian fan-out: every click event for a subscriber is matched against every send event for that subscriber, regardless of which job they belong to. The query succeeds and writes rows to the target DE, but the row count is massively inflated and the data is logically incorrect.

**When it occurs:** Any join between `_Sent` and `_Click`, `_Sent` and `_Open`, or `_Click` and `_Open` where `JobID` is not included in the ON clause. Also occurs when joining system data views to a custom staging DE that stores events without preserving `JobID`.

**How to avoid:** Always use `JobID + SubscriberKey` as the composite join key for all cross-view event joins:
```sql
FROM _Sent s
INNER JOIN _Click c
    ON s.JobID = c.JobID
   AND s.SubscriberKey = c.SubscriberKey
```
The only exception is `_Subscribers`, which is a current-state view (not event-based) and joins correctly to event views on `SubscriberKey` alone when correlating subscriber status with any event history.

---

## Gotcha 3: _Subscribers Shows Current State Only — Past Status Values Are Not Retained

**What happens:** The `_Subscribers` view reflects the subscriber's current status (`Active`, `Bounced`, `Unsubscribed`, `Held`). If a subscriber was unsubscribed and later re-opted in, the view shows only `Active`. There is no built-in history table or changelog for status transitions.

**When it occurs:** Compliance audits requiring proof that a subscriber was unsubscribed at a specific past date; re-permission workflows that need to know when a subscriber's status last changed; customer service requests to confirm opt-out timing.

**How to avoid:** Implement an incremental status snapshot automation: query `_Subscribers` daily or weekly and append rows (with a run timestamp) to a persistent custom DE. This gives a temporal record of status changes. Do not rely on `DateUnsubscribed` or `DateHeld` fields in `_Subscribers` as comprehensive audit trails — those fields reflect the most recent state-change date, not a complete history.

---

## Gotcha 4: System Data Views Are Not Visible in Contact Builder or the DE Navigator

**What happens:** Practitioners who look for `_Sent` or `_Open` in the Data Extension Navigator (under Email Studio or Contact Builder) do not find them. There is no folder, no search result, and no schema preview available in the UI. Attempts to reference them in SSJS `DataExtension.Retrieve()` calls or in Journey Builder splits also fail.

**When it occurs:** Any time a practitioner tries to explore, document, or use system data views outside of a SQL Query Activity. This is especially common for developers familiar with standard databases who expect to browse a schema catalog.

**How to avoid:** Accept the constraint: system data views are queryable only via SQL Query Activity. Use Salesforce's published documentation for schema reference (field names, data types, key columns). Build schema reference notes or a team wiki entry using the published field lists so they are accessible without needing to browse the MC UI. Query Studio (Salesforce Labs AppExchange app) provides the only interactive way to see query results from system data views.

---

## Gotcha 5: JobID Type Mismatch Between System Views and Custom DEs Causes Silent Empty Joins

**What happens:** `_Job` and other system data views store `JobID` as an integer (Number type). When a custom staging DE stores `JobID` as a Text field (a common default in DE creation), an INNER JOIN between the staging DE and `_Job` on `JobID` returns zero rows. The join succeeds syntactically but the implicit type comparison returns no matches.

**When it occurs:** Any time a custom DE is used as an intermediate store for job-level data and the DE was created with `JobID` as a Text or EmailAddress field type rather than Number. Especially common when DEs are created from an import or copy-paste of query results, which defaults all columns to Text.

**How to avoid:** When creating a custom DE that will join to system data views, define `JobID` as a Number field type (no decimal places). Verify the target DE field type before writing the join query. If a staging DE already exists with the wrong type, either rebuild it or cast with `CONVERT(INT, staging.JobID)` in the JOIN condition.

---

## Gotcha 6: _Click Stores One Row Per Link Per Event — Not One Row Per Subscriber

**What happens:** `_Click` stores one row per tracked link click, per subscriber, per job. A subscriber who clicks three links in one email generates three rows in `_Click` for that job. Queries that do not use `SELECT DISTINCT` or `GROUP BY` on `SubscriberKey` produce inflated counts and duplicate rows in the output DE.

**When it occurs:** Any query against `_Click` that is meant to produce a one-row-per-subscriber result (e.g., a clickthrough segment) without deduplication logic. Also causes double-counting in aggregate reports that sum rows without understanding the one-row-per-click-event data model.

**How to avoid:** Always apply `SELECT DISTINCT c.SubscriberKey, c.EmailAddress` or use `GROUP BY c.SubscriberKey, c.EmailAddress` with an aggregate like `COUNT(*) AS ClickCount` or `MAX(c.EventDate) AS LastClickDate` when building subscriber-level segments or reports from `_Click`.
