# Timezone and Datetime Pitfalls — Work Template

Use this template when diagnosing or fixing timezone/datetime bugs, or when designing new Apex/SOQL code that handles Date or Datetime values.

## Scope

**Skill:** `timezone-and-datetime-pitfalls`

**Request summary:** (fill in what the user asked for — e.g., "Records show the wrong date for APAC users", "Scheduled job fires at wrong time after DST change")

---

## Context Gathered

Answer these before writing any code:

- **Field type in question:** Date / Datetime / both
- **Operation causing the issue:** Storage | Retrieval | Display | SOQL filter | Apex arithmetic | Flow comparison
- **Timezones in play:**
  - Salesforce server: UTC (always)
  - Running user timezone: _________
  - Record owner timezone(s): _________
  - External system timezone (if applicable): _________
- **DST in scope?** Yes / No / Unknown
- **Execution context:** Interactive user | Scheduled Apex | Batch | Integration API | Flow

---

## Timezone Behavior Summary for This Task

Fill in which layers apply timezone conversion and which do not:

| Layer | Conversion Applied? | Notes |
|---|---|---|
| Database storage | No — always UTC for Datetime | Date fields store the calendar string as-is |
| Apex `Date.today()` | Server UTC date only | Does NOT use running user's timezone |
| Apex `Datetime.now()` | Returns UTC instant | No local conversion |
| Apex `Datetime.format()` no-arg | Yes — running user locale/TZ | Use `format(pattern, tzId)` for explicit TZ |
| Apex `Datetime.date()` | Extracts UTC date | NOT the local date |
| SOQL date literals (`TODAY`) | Yes — running user's TZ | Evaluates to UTC range using user's TZ |
| SOQL `DAY_ONLY()` | No — UTC date | Not user's local date |
| UI (standard page, list view) | Yes — viewing user's TZ | Datetime rendered in user's locale |
| Visualforce renderAs="pdf" | No — UTC as-is | Does not apply user TZ conversion |
| Flow DateTime fields | UTC-based | Compare to Date requires explicit conversion |

---

## Approach

Which pattern from SKILL.md applies?

- [ ] Safe "Today" for the running user — needed when `Date.today()` returns wrong date for non-UTC users
- [ ] Storing Datetime from external systems — needed when inbound timestamps have timezone offsets
- [ ] Avoiding Date field midnight UTC crossing — needed when `.date()` extracts wrong local date
- [ ] Explicit SOQL date range — needed when date literal filter must be timezone-independent
- [ ] Owner-timezone-aware batch — needed when batch processes records for multi-timezone user base
- [ ] DST-aware scheduling — needed when scheduled job must fire at consistent wall-clock time

---

## Checklist

- [ ] No `Date.today()` calls in user-facing date default logic (replaced with user-timezone-aware today)
- [ ] All `Datetime.newInstance(year, month, day, hour, minute, second)` replaced with `newInstanceGmt` where UTC input is intended
- [ ] ISO 8601 strings with timezone offsets parsed via `JSON.deserialize`, not `Datetime.valueOf()`
- [ ] `Datetime.format()` calls that matter to users include an explicit timezone ID string
- [ ] `Datetime.date()` calls producing user-visible Date values apply `getOffset()` shift before extraction
- [ ] SOQL date literals documented as intentionally user-timezone-relative, or replaced with explicit UTC range bind variables
- [ ] Batch/scheduled code uses record owner's `TimeZoneSidKey`, not `UserInfo.getTimeZone()`
- [ ] DST-sensitive scheduling uses `TimeZone.getOffset(targetDatetime)` at the target date, not a fixed offset
- [ ] Test cases include a `System.runAs()` user with a non-UTC timezone (e.g., `'America/New_York'` or `'Asia/Tokyo'`)

---

## Code Snippets Used

Record timezone patterns actually applied in this task:

```apex
// User-local today (copy and adapt as needed)
TimeZone tz = UserInfo.getTimeZone();
Datetime nowUtc = Datetime.now();
Datetime localNow = nowUtc.addSeconds(tz.getOffset(nowUtc) / 1000);
Date userToday = localNow.date();
```

```apex
// Timezone-aware Datetime formatting
String displayValue = myDatetime.format('MM/dd/yyyy hh:mm a', 'America/Los_Angeles');
```

```apex
// Parsing ISO 8601 with offset from external system
Datetime parsed = (Datetime) JSON.deserialize('"' + isoString + '"', Datetime.class);
```

---

## Notes

Record any deviations from the standard patterns here, and why:

- (e.g., "Used `Date.today()` intentionally — this is a system-level audit log date where server UTC is the authoritative date, not the user's local date. Documented in code comment.")
