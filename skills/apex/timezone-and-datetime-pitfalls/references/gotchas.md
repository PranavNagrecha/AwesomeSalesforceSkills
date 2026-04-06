# Gotchas — Timezone and Datetime Pitfalls

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: Date Fields Display the Stored Calendar String — No Timezone Conversion Ever

**What happens:** Date fields do not undergo any timezone conversion at any layer — not in the database, not in Apex, not in the UI. The date stored is the date displayed, period. This sounds safe until you realize that Date fields are often populated from Datetime values using `.date()`, which extracts the **UTC date**, not the local user's date.

A Datetime field value of `2025-11-01T22:00:00Z` belongs to November 1st in UTC. But a user in UTC+4 (local time: November 2nd at 02:00 AM) would expect a Date derived from that Datetime to be November 2nd. `.date()` returns November 1st — the UTC date — regardless of the user's locale.

**When it occurs:** Any code path that populates a Date field from a Datetime: `SObject.DateField__c = someDateTime.date()`. This commonly appears in triggers, flow actions, and integration ingest layers that store "the date this event happened" as a Date field. The bug affects all users east of UTC who work with records in the late evening UTC hours.

**How to avoid:** When the semantics of the Date field are "the local calendar date for this user or event", always shift the Datetime by the relevant timezone offset before calling `.date()`:

```apex
TimeZone tz = UserInfo.getTimeZone(); // or the timezone of the relevant location
Datetime adjusted = someDatetime.addSeconds(tz.getOffset(someDatetime) / 1000);
Date localDate = adjusted.date();
```

---

## Gotcha 2: Datetime.newInstance() Uses Server Local Time, Not UTC

**What happens:** `Datetime.newInstance(year, month, day, hour, minute, second)` creates a Datetime interpreted in the **Salesforce server's local timezone**, which is documented as behaving like UTC in practice. However, the contract is not "always UTC" — the explicit UTC-safe method is `Datetime.newInstanceGmt(year, month, day, hour, minute, second)`. Code that uses `newInstance()` with UTC-component integers is relying on an undocumented coincidence.

More concretely: `Datetime.newInstance(2025, 3, 14, 2, 30, 0)` during a DST transition (when 2:30 AM does not exist in some US timezones) can produce ambiguous or unexpected results. `Datetime.newInstanceGmt(2025, 3, 14, 2, 30, 0)` is unambiguous — it always means 2025-03-14T02:30:00Z.

**When it occurs:** Integration code that parses date components from an external payload and constructs a Datetime from parts. Report generation code that builds date range boundaries from component integers. Any code constructing a Datetime from known UTC values.

**How to avoid:** Always use `Datetime.newInstanceGmt(year, month, day, hour, minute, second)` when you know your inputs are UTC components. Use `Datetime.newInstance(date, time)` only when you intentionally want local-time semantics (rare). Treat `newInstance(year, month, day, ...)` as a code smell in any integration or UTC-aware context.

---

## Gotcha 3: SOQL Aggregate Functions and GROUP BY with Datetime Produce UTC-Bucketed Results

**What happens:** When you use SOQL to group records by a Datetime field — for example, counting Cases by `DAY_ONLY(CreatedDate)` — the bucketing is done in **UTC**. A Case created at `2025-06-15T23:30:00Z` by a user in UTC+10 (local date: June 16) will be bucketed into June 15 in the aggregate result. Reports built from this query will show the wrong day count for users in non-UTC timezones.

The `DAY_ONLY()` SOQL function extracts the date portion of a Datetime in UTC, not in the running user's timezone. This is different from how the UI renders the same Datetime field in a list view (which converts to user timezone).

**When it occurs:** Custom SOQL-backed analytics, LWC dashboards using wire adapters with SOQL aggregates, and any Apex code that groups or counts records by calendar date derived from a Datetime field.

**How to avoid:** For timezone-correct date bucketing, compute the UTC boundaries of the target "day" in the desired timezone explicitly (as shown in Example 2 in examples.md) and use range filters rather than `DAY_ONLY()`. If you must use `DAY_ONLY()`, document that results are UTC-bucketed and adjust expectations — or compensate by querying an adjacent date range.

---

## Gotcha 4: UserInfo.getTimeZone() in Scheduled Apex Returns the Scheduled User's Timezone

**What happens:** In a scheduled Apex job, `UserInfo.getTimeZone()` returns the timezone of the **user who scheduled the job** (or the system/integration user for system-scheduled jobs), not the timezone of any end user whose records are being processed. If a US-based admin schedules a nightly batch that processes records for APAC users, `UserInfo.getTimeZone()` will return a US timezone, producing wrong local-date calculations for APAC records.

**When it occurs:** Any scheduled Apex that uses `UserInfo.getTimeZone()` to calculate "today" or date boundaries and then applies those boundaries to records owned by users in different timezones. Common in nightly sync jobs, SLA calculation batches, and reminder-email schedulers.

**How to avoid:** When processing records for users across timezones, use the **record owner's timezone** rather than the running user's timezone. Query the owner's `TimeZoneSidKey` field from the User object and use `TimeZone.getTimeZone(owner.TimeZoneSidKey)` for per-record timezone calculations:

```apex
// Get timezone for the record owner, not the running user
User owner = [SELECT TimeZoneSidKey FROM User WHERE Id = :record.OwnerId LIMIT 1];
TimeZone ownerTz = TimeZone.getTimeZone(owner.TimeZoneSidKey);
```

---

## Gotcha 5: Flow DateTime Comparisons Are Always UTC; User-Entered Dates Are Calendar Days

**What happens:** In Salesforce Flow, a DateTime variable holds a UTC value. If a screen flow presents a date picker and the user selects June 15, Flow stores this as a Date type (no time component). Comparing a Date value directly to a DateTime variable in a Flow decision element can produce counter-intuitive results because Flow internally converts the Date to `midnight UTC of that day` for the comparison.

For a user in UTC-5 whose local midnight is 05:00 UTC, a DateTime of `2025-06-15T03:00:00Z` (which is June 14 local time at 10 PM) will compare as **equal to or before** June 15 when compared to a Date value of `2025-06-15`, even though the user's local time is the previous evening.

**When it occurs:** Screen flows with date pickers feeding decision elements that branch on DateTime comparisons. Autolaunched flows triggered by process builder that compare a DateTime field to a user-entered Date variable.

**How to avoid:** In Flow, convert both sides of any date comparison to the same type before comparing. If comparing a user-entered Date to a DateTime field, convert the DateTime to a Date using a formula resource: `DATEVALUE({!MyDateTimeField})`. Be aware that `DATEVALUE()` in Flow extracts the UTC date — the same gotcha as `.date()` in Apex. For timezone-correct Flow comparisons, pass the record into an Apex action that performs the comparison with explicit timezone handling.

---

## Gotcha 6: Visualforce renderAs="pdf" Renders Datetime in Server Timezone, Not User Timezone

**What happens:** Standard Visualforce pages render Datetime fields in the viewing user's timezone via normal UI rendering. However, when a Visualforce page is rendered as a PDF (using `renderAs="pdf"`), the rendering engine does not apply user timezone conversion. Datetime values are rendered as-is from the database, which is UTC.

A user in UTC-5 generating a PDF at 3:00 PM local time will see Datetime fields showing 8:00 PM (the UTC equivalent) in the PDF, while the on-screen version correctly shows 3:00 PM.

**When it occurs:** Any Visualforce PDF generation that outputs Datetime fields using merge fields like `{!record.CreatedDate}` without explicit formatting. Common in invoice generation, contract PDFs, and compliance reports.

**How to avoid:** In Visualforce PDF templates, use explicit `SUBSTITUTE` or `TEXT` formula functions with a timezone-adjusted value, or compute the display value in the Apex controller using `Datetime.format('pattern', 'Timezone/ID')` and expose it as a formatted string property rather than relying on the merge field's default rendering.
