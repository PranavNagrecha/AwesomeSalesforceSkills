---
name: timezone-and-datetime-pitfalls
description: "Use when writing or reviewing Apex, SOQL, or Flow logic that involves Date or Datetime fields: scheduling jobs, comparing dates across timezones, displaying Datetime values to users, filtering records by date literals, or persisting Datetime from external systems. NOT for calendar UI component layout, time-zone configuration in org settings, or Salesforce Connect external object date mapping."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "records appear on the wrong day in reports when users are in different timezones"
  - "Date.today() in Apex returns yesterday's or tomorrow's date for some users"
  - "my SOQL date literal filter is returning wrong records depending on who runs it"
  - "Datetime.format() shows a different time than what was stored"
  - "scheduled Apex fires at the wrong wall-clock time after daylight saving changes"
  - "a Flow DateTime comparison gives incorrect results compared to what the user entered"
  - "a Datetime stored via API shows the wrong date in the UI"
tags:
  - datetime
  - timezone
  - date-handling
  - soql-date-literals
  - apex-scheduling
  - utc
  - dst
inputs:
  - "Whether the problem involves a Date field, a Datetime field, or both"
  - "The timezone(s) of the org, the running user, and any external system involved"
  - "The operation causing the issue: storage, retrieval, display, SOQL filter, or Apex arithmetic"
  - "Whether Daylight Saving Time transitions are in scope"
outputs:
  - "Corrected Apex code handling UTC/local timezone conversion explicitly"
  - "SOQL query using the right date literal or explicit offset for the target timezone"
  - "Pattern guidance for safe Datetime storage, display, and arithmetic"
  - "Explanation of which layer (DB, Apex runtime, UI, SOQL engine) applies timezone conversion and which does not"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Timezone and Datetime Pitfalls

This skill activates when a practitioner encounters bugs or uncertainty around how Salesforce stores, filters, and displays Date and Datetime values across timezones. It covers the full stack from database storage (always UTC) through Apex runtime behavior, SOQL date literals, and UI rendering — and explains why the same value can appear as a different date depending on who is looking at it and from where.

---

## Before Starting

Gather this context before working on anything in this domain:

- Identify whether the field in question is a **Date** type or a **Datetime** type — they have fundamentally different timezone semantics and the fix for one does not apply to the other.
- Determine the **org's default timezone** (Setup > Company Information), the **running user's timezone** (User record), and the **timezone of any external system** sending or receiving the value.
- Identify **where the bug surfaces**: in a report, in Apex logic, in a SOQL filter, in a Flow, or in a UI component. Each layer applies timezone rules differently.
- Check whether **Daylight Saving Time (DST)** is in scope: scheduled Apex fire times and fixed-offset calculations both shift at DST boundaries.

---

## Core Concepts

### Datetime Fields Are Stored as UTC, Displayed in User Timezone

Every Datetime field in the Salesforce database is stored as a UTC value. When Salesforce displays a Datetime in the UI (record detail, list view, report), it converts UTC to the **viewing user's timezone** automatically. This means the same stored value can show as Monday for a user in New York and as Tuesday for a user in Tokyo.

Apex `Datetime` values in memory are also UTC-referenced internally, but `Datetime.format()` with no arguments renders using the **running user's locale and timezone**. If you format a Datetime in an Apex context running as a system user (anonymous Apex, scheduled jobs), the output reflects that system user's timezone setting, which may differ from the user whose data you are processing.

```apex
// Datetime stored in DB: 2025-06-15T02:00:00Z
// Running user timezone: America/New_York (UTC-4 in summer)
Datetime dt = [SELECT CreatedDate FROM Account LIMIT 1].CreatedDate;
System.debug(dt.format()); // Prints "6/14/2025, 10:00 PM" — the previous calendar day
```

### Date Fields Have No Timezone — And That Is the Pitfall

Date fields store a calendar date without any time component. Salesforce persists them as midnight UTC of that date (`2025-06-15T00:00:00Z`). There is **no timezone conversion** applied on read or write — the date is always the literal day string stored.

The critical consequence: **`Date.today()` in Apex returns the server-side date**, which is determined by the Salesforce server's clock in UTC. For a user in UTC+10 at 11:00 PM, the server is still on the previous calendar day. `Date.today()` will return yesterday's date relative to the user. This is one of the most common sources of off-by-one-day bugs in scheduled jobs and trigger logic.

```apex
// Server UTC time: 2025-06-14T23:30:00Z
// User local time (UTC+10): 2025-06-15T09:30:00 (next day)
Date serverToday = Date.today(); // Returns 2025-06-14 — wrong from the user's perspective
```

To get a Datetime representing the user's local "now", use `Datetime.now()` (which is UTC-equivalent) and then apply `addSeconds(UserInfo.getTimeZone().getOffset(Datetime.now()) / 1000)` to shift to local time before extracting a Date.

### SOQL Date Literals Use the Running User's Timezone

SOQL date literals (`TODAY`, `LAST_WEEK`, `LAST_N_DAYS:30`, `THIS_MONTH`) are evaluated relative to the **running user's timezone**. The Salesforce SOQL engine converts the date literal boundaries to UTC ranges before executing the query.

This means the same SOQL statement can return different record sets depending on who runs it. A record created at `2025-06-15T01:00:00Z` will match `TODAY` for a user in UTC+3 (their local date is June 15) but will match `YESTERDAY` for a user in UTC-5 (their local date is still June 14).

In Apex, the running user for a SOQL query is determined by whether the code runs in user mode or system mode — but the timezone used for date literals is still the **running user's timezone profile**, not the server timezone.

### Datetime.format() and Timezone-Aware Formatting

`Datetime.format()` with no arguments uses the running user's locale and timezone. To produce a timezone-explicit string, use `Datetime.format(String dateFormat, String timezone)`. To convert a Datetime to a different timezone for display or arithmetic, use `TimeZone.getTimeZone(String id)` combined with `Datetime.format()`.

```apex
Datetime utcNow = Datetime.now();
// Format in a specific timezone regardless of running user:
String pacificTime = utcNow.format('yyyy-MM-dd HH:mm:ss', 'America/Los_Angeles');
String tokyoTime   = utcNow.format('yyyy-MM-dd HH:mm:ss', 'Asia/Tokyo');
```

The timezone ID strings follow the Java `TimeZone` naming convention (e.g., `'America/Chicago'`, `'Europe/London'`, `'UTC'`). Passing `'UTC'` forces the output to show the raw stored UTC value.

---

## Common Patterns

### Safe "Today" for the Running User

**When to use:** Any Apex logic that needs the current calendar date from the user's perspective (not the server's), such as populating a Date field, comparing against a deadline, or filtering with a dynamic SOQL date value.

**How it works:**

```apex
// Get the running user's timezone
TimeZone tz = UserInfo.getTimeZone();
// Shift Datetime.now() by the user's UTC offset to get their local date
Datetime localNow = Datetime.now().addSeconds(tz.getOffset(Datetime.now()) / 1000);
Date userToday = localNow.date();
```

Note: `TimeZone.getOffset()` returns milliseconds, so divide by 1000 for seconds. This approach handles DST correctly because `getOffset()` is evaluated at the given instant, not a fixed offset.

**Why not `Date.today()`:** `Date.today()` uses the server's UTC date, which can differ from the user's local calendar date by one day near midnight.

### Storing Datetime from External Systems

**When to use:** Inbound API calls, integration middleware, or external event systems that send timestamps in a local timezone (e.g., `2025-06-15T14:30:00-07:00`).

**How it works:**

Always convert incoming timestamps to UTC before storing in a Datetime field. Use `Datetime.valueOf(String iso8601)` which parses ISO 8601 with timezone offsets correctly. Never strip the offset and store the local time as if it were UTC — this introduces a systematic offset error equal to the source timezone.

```apex
// Incoming from external system: "2025-06-15T14:30:00-07:00"
// Datetime.valueOf parses the offset and stores the equivalent UTC value
Datetime utcValue = (Datetime) JSON.deserialize('"2025-06-15T14:30:00-07:00"', Datetime.class);
// Stored as 2025-06-15T21:30:00Z in the database
myRecord.EventTime__c = utcValue;
```

Alternatively, use `Datetime.newInstanceGmt(year, month, day, hour, minute, second)` when you already know the UTC components.

**Why not `Datetime.newInstance(year, month, day, hour, minute, second)`:** The no-suffix variant uses the **local (server) timezone**, not UTC, producing incorrect UTC storage if the server timezone is not UTC.

### Avoiding Date Field Midnight UTC Crossing

**When to use:** Reports, dashboards, or Apex that groups or compares Date field values for users in timezones far from UTC (UTC+10 to UTC+12, or UTC-8 to UTC-10).

**How it works:**

Recognize that Date fields display the stored date string directly with no conversion. If your process populates a Date field from a Datetime (`myDate = myDatetime.date()`), the resulting date is the **UTC date** of that Datetime, not the local date. For users in UTC+10, a Datetime of `2025-06-15T23:00:00Z` converts to `2025-06-16` local time but `.date()` returns `2025-06-15`.

To store the user's local calendar date:

```apex
TimeZone tz = UserInfo.getTimeZone();
Datetime localDt = myDatetime.addSeconds(tz.getOffset(myDatetime) / 1000);
Date localDate = localDt.date();
```

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need today's date in Apex for the running user | `UserInfo.getTimeZone()` + `Datetime.now().addSeconds(offset/1000).date()` | `Date.today()` returns server UTC date, not user's local date |
| SOQL filter by date must be timezone-independent | Use explicit ISO 8601 bind variable or date range in WHERE clause | Date literals depend on running user's timezone; explicit ranges are deterministic |
| Displaying Datetime in a specific timezone | `dt.format('pattern', 'Timezone/ID')` | No-arg `format()` uses running user's locale, which varies by context |
| Storing a Datetime received from an external API | Parse ISO 8601 with offset via `JSON.deserialize` or `Datetime.newInstanceGmt` | `Datetime.newInstance` uses server local timezone, not UTC |
| Extracting a Date from a Datetime for a user | Shift Datetime by user's `getOffset()` before calling `.date()` | `.date()` extracts UTC date, not local date |
| Scheduled Apex needs to fire at a specific local wall-clock time | Convert target local time to UTC using `TimeZone.getOffset()` at the target date | DST shifts change the UTC equivalent; recalculate at the target date, not today |
| Flow DateTime comparison against a user-entered Date | Convert the Date to a Datetime using `$Flow.CurrentDateTime` and explicit time components before comparing | Flow DateTime is UTC-based; user-entered Date is a calendar day without time, causing comparison skew |

---

## Recommended Workflow

1. **Identify the field type and the failure layer.** Determine whether the bug involves a Date field, a Datetime field, or the boundary between them. Identify where the wrong value appears: in Apex logic, SOQL results, the UI, or a Flow comparison.
2. **Map all timezone contexts in play.** List: the Salesforce server timezone (UTC), the running user's profile timezone, the external system's timezone (if any), and the timezone implicit in any date literals or hardcoded dates.
3. **Trace the value lifecycle.** Follow the value from origin (creation, inbound API, user input) through storage (always UTC for Datetime), through any Apex arithmetic, through SOQL filtering, and through display. At each step identify whether a timezone conversion is happening explicitly, implicitly, or not at all.
4. **Apply the appropriate fix pattern.** Use the Decision Guidance table to select the right approach. For `Date.today()` bugs use the user-local today pattern. For SOQL date literal bugs use explicit bind variables. For display bugs use `Datetime.format()` with an explicit timezone string.
5. **Test with a user in a UTC+ timezone and a UTC- timezone.** Most timezone bugs only manifest for users far from UTC. Add test cases that simulate a `System.runAs()` for a user with a non-UTC timezone.
6. **Verify DST boundary behavior.** If the logic runs on or near a DST transition date (e.g., second Sunday in March or first Sunday in November for US timezones), test with a Datetime value that crosses the boundary to confirm offset recalculation works correctly.

---

## Review Checklist

- [ ] No `Date.today()` calls in code that needs the running user's local calendar date
- [ ] All `Datetime.newInstance()` calls have been reviewed; UTC variants (`newInstanceGmt`) used for external data
- [ ] SOQL date literals (`TODAY`, `THIS_WEEK`, etc.) are intentional; dynamic SOQL using explicit ranges used where timezone-independence is required
- [ ] `Datetime.format()` calls include an explicit timezone string where output timezone matters
- [ ] `Datetime.date()` calls that feed Date fields have been verified to extract the correct local date, not the UTC date
- [ ] Scheduled Apex fire times are calculated in UTC using the target date's offset, not a fixed offset
- [ ] Test classes include at least one `System.runAs()` with a non-UTC timezone user for any date/time-sensitive logic

---

## Salesforce-Specific Gotchas

1. **`Date.today()` uses the server clock, not the user clock** — Apex runs on Salesforce servers set to UTC. `Date.today()` returns the UTC calendar date at the moment of execution. A user in UTC+12 at 1:00 AM is already on the next calendar day, but `Date.today()` returns yesterday's date. This silently breaks due-date logic, deadline comparisons, and any Date field auto-population that should reflect the user's local date.

2. **`Datetime.newInstance()` silently uses the server local timezone** — The four-to-seven-argument `Datetime.newInstance(year, month, day[, hour, minute, second])` creates a Datetime in the **Salesforce server local timezone** (which is UTC in practice, but this is an implementation detail, not a contract). The explicitly UTC-safe method is `Datetime.newInstanceGmt(year, month, day, hour, minute, second)`. For code that must be portable and explicit, always use the GMT variant.

3. **SOQL date literals shift the result set based on running user** — Running the same SOQL in anonymous Apex as a System Administrator and in a trigger running as a field rep in Tokyo produces different record sets if the query uses date literals like `TODAY` or `LAST_N_DAYS:7`. The Salesforce SOQL engine converts literals to UTC ranges using the running user's timezone profile. This means report results can change depending on who refreshes the report.

4. **Datetime.date() extracts the UTC date, not the local date** — Calling `.date()` on a Datetime strips the time component and returns the **UTC date**. If the Datetime is `2025-06-15T23:00:00Z` and the running user is in UTC+10 (local time: June 16, 09:00), `.date()` returns `2025-06-15`, not `2025-06-16`. Any code that populates a Date field from a Datetime using `.date()` will show the wrong calendar day for users east of UTC when the Datetime is in the evening UTC hours.

5. **Scheduled Apex and DST: fixed offsets break twice a year** — If a scheduled job is configured to fire at a target wall-clock time (e.g., "9 AM Eastern") by computing a UTC equivalent using a fixed offset (`-5` for EST), that offset becomes wrong when DST is in effect (`-4` for EDT). The job will fire at 10 AM Eastern during summer. Always compute the UTC equivalent dynamically using `TimeZone.getOffset(targetDatetime)` at the target date, not a static offset.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Corrected Apex date/datetime handling code | Rewritten logic using `UserInfo.getTimeZone()`, `newInstanceGmt`, and explicit `format()` calls |
| SOQL query with explicit date ranges | Parameterized SOQL using bind variables for timezone-safe filtering |
| Datetime conversion utility snippet | Reusable static methods for UTC-to-local conversion, local Date extraction, and timezone-aware formatting |

---

## Related Skills

- apex/apex-scheduling — scheduling Apex jobs at correct wall-clock times accounting for DST
- data/data-reconciliation-patterns — when datetime mismatches cause record duplication or missed matches during data loads
