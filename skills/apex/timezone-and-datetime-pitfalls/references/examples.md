# Examples — Timezone and Datetime Pitfalls

## Example 1: Off-by-One Day in Apex Trigger Using Date.today()

**Context:** A trigger on Opportunity sets a `Due_Date__c` (Date field) to "today plus 30 days" as a default when the record is created. Users in the APAC region (UTC+10 to UTC+12) consistently see `Due_Date__c` set to 31 days in the future, not 30.

**Problem:** The trigger uses `Date.today()` to get the current date and adds 30. `Date.today()` returns the UTC server date. For an APAC user creating a record at 2:00 AM local time (still 4:00 PM UTC the previous day), the server date is one day behind their local date, so `Date.today().addDays(30)` computes from yesterday, yielding 31 days in the future relative to the user's calendar.

```apex
// WRONG — uses server UTC date, not the user's local date
trigger OpportunityDefaults on Opportunity (before insert) {
    for (Opportunity opp : Trigger.new) {
        if (opp.Due_Date__c == null) {
            opp.Due_Date__c = Date.today().addDays(30); // Returns UTC date, not user's date
        }
    }
}
```

**Solution:**

```apex
// CORRECT — shifts Datetime.now() by the running user's UTC offset before extracting date
trigger OpportunityDefaults on Opportunity (before insert) {
    TimeZone tz = UserInfo.getTimeZone();
    Datetime nowUtc = Datetime.now();
    // getOffset returns milliseconds; divide by 1000 for seconds
    Datetime localNow = nowUtc.addSeconds(tz.getOffset(nowUtc) / 1000);
    Date userToday = localNow.date();

    for (Opportunity opp : Trigger.new) {
        if (opp.Due_Date__c == null) {
            opp.Due_Date__c = userToday.addDays(30);
        }
    }
}
```

**Why it works:** `UserInfo.getTimeZone().getOffset(instant)` returns the offset in milliseconds between UTC and the user's local time **at that specific instant**, accounting for DST. Adding that offset to `Datetime.now()` produces a Datetime whose `.date()` component matches the user's local calendar date.

---

## Example 2: SOQL Date Literal Returning Different Records Depending on Running User

**Context:** A Lightning component runs a SOQL query to fetch Cases created `TODAY` for a dashboard. The component is used globally. Support managers in US-Eastern and users in Europe see different record counts for the same dashboard at 8:00 AM Eastern time.

**Problem:** `TODAY` in SOQL is evaluated relative to the **running user's timezone**. At 8:00 AM Eastern (UTC-4), the UTC time is 12:00 PM — both timezones agree it is the same calendar day, so counts match. But at 11:00 PM Eastern (3:00 AM UTC next day), a European user (UTC+1, 4:00 AM) is on the next calendar day. Their `TODAY` window starts at a different UTC boundary. The inconsistency compounds for users in UTC+8 or higher, where a full overlap gap exists.

```apex
// PROBLEMATIC — result set varies by running user's timezone
List<Case> todayCases = [
    SELECT Id, Subject, CreatedDate
    FROM Case
    WHERE CreatedDate = TODAY
    ORDER BY CreatedDate DESC
];
```

**Solution:** Use explicit UTC datetime boundaries derived from the org's or target timezone's midnight times. This makes the filter deterministic for all users.

```apex
// CORRECT — explicit UTC window for "today" in a target timezone (e.g., org timezone)
TimeZone orgTz = TimeZone.getTimeZone(UserInfo.getTimeZone().getId());
Datetime nowUtc = Datetime.now();
// Calculate start of day in the target timezone
Integer offsetMs = orgTz.getOffset(nowUtc);
Datetime localMidnight = Datetime.now().addSeconds(offsetMs / 1000);
// Rebuild as start-of-day UTC
Datetime localStartOfDay = Datetime.newInstanceGmt(
    localMidnight.yearGmt(),
    localMidnight.monthGmt(),
    localMidnight.dayGmt(),
    0, 0, 0
).addSeconds(-offsetMs / 1000);
Datetime localEndOfDay = localStartOfDay.addDays(1);

List<Case> todayCases = [
    SELECT Id, Subject, CreatedDate
    FROM Case
    WHERE CreatedDate >= :localStartOfDay AND CreatedDate < :localEndOfDay
    ORDER BY CreatedDate DESC
];
```

**Why it works:** By computing explicit UTC start and end bounds for the target "day" and binding them as parameters, the SOQL filter is identical for every running user. The timezone calculation happens once in Apex where it is visible and testable, not hidden inside the SOQL engine's implicit date literal resolution.

---

## Example 3: Datetime Received from External API Stored with Wrong Offset

**Context:** An integration receives event timestamps from an external system in ISO 8601 format with a timezone offset (`2025-09-10T14:30:00-07:00`). The code uses `Datetime.valueOf()` to parse the string and stores it. Records consistently appear one hour off in the UI.

**Problem:** `Datetime.valueOf(String)` accepts the format `YYYY-MM-DD HH:MM:SS` (space-separated, no timezone offset) and **silently ignores** any timezone offset in the input, treating the numeric portion as local server time. Passing `'2025-09-10T14:30:00-07:00'` to `Datetime.valueOf()` does not parse the offset — it either throws or truncates depending on the input format. Using `Datetime.newInstance()` with parsed components also uses server local time, not UTC.

```apex
// WRONG — Datetime.valueOf does not parse timezone offsets from ISO 8601
String incoming = '2025-09-10T14:30:00-07:00';
Datetime parsed = Datetime.valueOf(incoming); // Does not handle the offset
myRecord.EventTime__c = parsed; // Stored with wrong UTC value
```

**Solution:** Use JSON deserialization, which correctly parses ISO 8601 strings with timezone offsets:

```apex
// CORRECT — JSON.deserialize handles ISO 8601 with timezone offset
String incoming = '2025-09-10T14:30:00-07:00';
Datetime parsed = (Datetime) JSON.deserialize('"' + incoming + '"', Datetime.class);
// parsed is now 2025-09-10T21:30:00Z in UTC — correct
myRecord.EventTime__c = parsed;
```

Alternatively, if you already know the UTC components (the external system provides a UTC timestamp), use `Datetime.newInstanceGmt(year, month, day, hour, minute, second)` explicitly.

**Why it works:** Salesforce's JSON deserializer handles ISO 8601 datetime strings including timezone offsets and converts them to UTC for internal Datetime storage, matching the behavior of every Datetime field in the platform.

---

## Anti-Pattern: Hardcoding a Fixed Timezone Offset for Scheduled Jobs

**What practitioners do:** When scheduling a batch job to run at "9 AM Pacific", developers compute the UTC equivalent by subtracting 8 hours (PST offset) and schedule it at `17:00:00`. They set this once and never revisit it.

**What goes wrong:** Pacific Daylight Time (PDT) is UTC-7, not UTC-8. When DST begins in March, the job fires at 10 AM Pacific instead of 9 AM. The same issue occurs in reverse when DST ends in November. The job will be off by one hour for approximately half the year.

```apex
// WRONG — hardcoded offset, breaks at DST boundaries
// Targets 09:00 PST (UTC-8), but wrong during PDT (UTC-7)
String cronExpr = '0 0 17 * * ?'; // 17:00 UTC, assumes PST
System.schedule('Daily Batch', cronExpr, new MyDailyBatch());
```

**Correct approach:** Calculate the UTC equivalent dynamically using the actual offset at the next scheduled run date, and re-schedule after each execution if wall-clock consistency across DST is required. For a simpler approach, schedule in UTC and accept that the wall-clock time shifts with DST, documenting this explicitly.

```apex
// BETTER — dynamically calculate UTC equivalent for next run
TimeZone pacificTz = TimeZone.getTimeZone('America/Los_Angeles');
// Target: tomorrow at 09:00 Pacific
Date tomorrow = Date.today().addDays(1);
Datetime targetLocal = Datetime.newInstance(tomorrow, Time.newInstance(9, 0, 0, 0));
// getOffset at the target datetime, not today (DST may differ)
Integer offsetMs = pacificTz.getOffset(targetLocal);
Datetime targetUtc = targetLocal.addSeconds(-offsetMs / 1000);

String cronExpr = targetUtc.format('\'0 \'m\' \'H\' * * ?\'');
System.schedule('Daily Batch', cronExpr, new MyDailyBatch());
```
