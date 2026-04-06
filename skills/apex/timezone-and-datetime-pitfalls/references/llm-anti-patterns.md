# LLM Anti-Patterns — Timezone and Datetime Pitfalls

Common mistakes AI coding assistants make when generating or advising on Date and Datetime handling in Salesforce Apex and SOQL. These patterns help the consuming agent self-check its own output.

---

## Anti-Pattern 1: Using Date.today() for User-Facing Date Defaults

**What the LLM generates:**

```apex
trigger CaseDefaults on Case (before insert) {
    for (Case c : Trigger.new) {
        c.Response_Due__c = Date.today().addDays(2); // "today plus 2 business days"
    }
}
```

**Why it happens:** `Date.today()` is the most obvious way to get the current date and appears throughout Salesforce documentation examples. LLMs generalize from these examples without distinguishing between system-level date semantics (where server UTC is correct) and user-facing date semantics (where the user's local calendar day is what matters).

**Correct pattern:**

```apex
trigger CaseDefaults on Case (before insert) {
    TimeZone tz = UserInfo.getTimeZone();
    Datetime nowUtc = Datetime.now();
    Datetime localNow = nowUtc.addSeconds(tz.getOffset(nowUtc) / 1000);
    Date userToday = localNow.date();

    for (Case c : Trigger.new) {
        c.Response_Due__c = userToday.addDays(2);
    }
}
```

**Detection hint:** Any `Date.today()` call inside a trigger, flow action, or Apex class that feeds a user-visible Date field. Flag for review — the correct fix depends on whether server-UTC or user-local semantics are intended.

---

## Anti-Pattern 2: Using Datetime.newInstance() for UTC Component Construction

**What the LLM generates:**

```apex
// Constructing a UTC midnight boundary for a date range query
Datetime startOfDay = Datetime.newInstance(2025, 6, 15, 0, 0, 0);
Datetime endOfDay   = Datetime.newInstance(2025, 6, 16, 0, 0, 0);
List<Case> cases = [SELECT Id FROM Case WHERE CreatedDate >= :startOfDay AND CreatedDate < :endOfDay];
```

**Why it happens:** `Datetime.newInstance(year, month, day, hour, minute, second)` looks like a UTC constructor. The LLM has seen it used in many code examples and does not distinguish it from `newInstanceGmt`. The GMT variant exists precisely because the non-GMT variant uses server local time, which LLMs rarely flag.

**Correct pattern:**

```apex
// Explicitly UTC — contract is clear, behavior is unambiguous
Datetime startOfDay = Datetime.newInstanceGmt(2025, 6, 15, 0, 0, 0);
Datetime endOfDay   = Datetime.newInstanceGmt(2025, 6, 16, 0, 0, 0);
List<Case> cases = [SELECT Id FROM Case WHERE CreatedDate >= :startOfDay AND CreatedDate < :endOfDay];
```

**Detection hint:** `Datetime.newInstance(` with four or more integer arguments (year, month, day, hour...) in integration or analytics code where UTC semantics are expected. Prefer `newInstanceGmt` for any code dealing with known UTC components.

---

## Anti-Pattern 3: Parsing ISO 8601 with Timezone Offset Using Datetime.valueOf()

**What the LLM generates:**

```apex
// Incoming webhook payload: "eventTime": "2025-09-10T14:30:00-07:00"
String rawTimestamp = payload.get('eventTime');
Datetime eventTime = Datetime.valueOf(rawTimestamp); // Loses the -07:00 offset
record.EventTime__c = eventTime;
```

**Why it happens:** `Datetime.valueOf(String)` is documented for parsing datetime strings, and LLMs associate ISO 8601 parsing with it. However, `Datetime.valueOf()` expects the format `YYYY-MM-DD HH:MM:SS` (space separator, no timezone offset). It does not parse timezone offsets — it either throws or silently truncates the offset, storing the numeric portion as if it were server local time.

**Correct pattern:**

```apex
// JSON.deserialize correctly handles ISO 8601 with timezone offsets
String rawTimestamp = payload.get('eventTime'); // "2025-09-10T14:30:00-07:00"
Datetime eventTime = (Datetime) JSON.deserialize('"' + rawTimestamp + '"', Datetime.class);
// Stored as 2025-09-10T21:30:00Z — correct UTC equivalent
record.EventTime__c = eventTime;
```

**Detection hint:** `Datetime.valueOf(` receiving a string that contains `T` (ISO 8601 separator) or `+` or `-` offset notation. Flag this pattern for replacement with JSON deserialization or explicit UTC component construction.

---

## Anti-Pattern 4: Hardcoding a Numeric Timezone Offset Instead of Using TimeZone.getOffset()

**What the LLM generates:**

```apex
// "Convert UTC to Pacific time for display"
Datetime utcNow = Datetime.now();
Datetime pacificTime = utcNow.addHours(-8); // Hardcoded PST offset — wrong during PDT
String display = pacificTime.format('MM/dd/yyyy hh:mm a');
```

**Why it happens:** The LLM knows that Pacific Standard Time is UTC-8 and applies it as a static arithmetic offset. It does not model DST transitions or the fact that the correct offset depends on the specific date/time being converted, not a global constant.

**Correct pattern:**

```apex
// Use Datetime.format() with an explicit timezone ID — handles DST automatically
Datetime utcNow = Datetime.now();
String display = utcNow.format('MM/dd/yyyy hh:mm a', 'America/Los_Angeles');
// Correct for both PST (UTC-8) and PDT (UTC-7) based on the actual date
```

**Detection hint:** `addHours(-8)`, `addHours(-5)`, `addHours(+9)`, or any `.addHours(` call with a literal integer in code that is described as "timezone conversion". Also flag `addSeconds(` with a literal integer that looks like a timezone offset (e.g., -28800, 32400).

---

## Anti-Pattern 5: Applying Running User Timezone to All Records in a Batch

**What the LLM generates:**

```apex
// Scheduled batch to set "local date processed" on records
global class DateProcessingBatch implements Database.Batchable<SObject> {
    // Compute user timezone once outside the loop — but uses running user, not record owner
    private static TimeZone tz = UserInfo.getTimeZone();

    global void execute(Database.BatchableContext bc, List<MyObject__c> records) {
        Datetime nowUtc = Datetime.now();
        Datetime localNow = nowUtc.addSeconds(tz.getOffset(nowUtc) / 1000);
        Date localDate = localNow.date();
        for (MyObject__c rec : records) {
            rec.ProcessedDate__c = localDate; // Same date for all records, using scheduler's TZ
        }
        update records;
    }
}
```

**Why it happens:** `UserInfo.getTimeZone()` is the standard way to get "the current timezone" in Apex. LLMs apply it uniformly without recognizing that in a scheduled or system context, it returns the **scheduler user's timezone**, which may differ from every record owner's timezone in the batch.

**Correct pattern:**

```apex
global void execute(Database.BatchableContext bc, List<MyObject__c> records) {
    // Collect unique owner IDs in this batch
    Set<Id> ownerIds = new Set<Id>();
    for (MyObject__c rec : records) { ownerIds.add(rec.OwnerId); }

    // Query each owner's timezone
    Map<Id, String> tzById = new Map<Id, String>();
    for (User u : [SELECT Id, TimeZoneSidKey FROM User WHERE Id IN :ownerIds]) {
        tzById.put(u.Id, u.TimeZoneSidKey);
    }

    Datetime nowUtc = Datetime.now();
    for (MyObject__c rec : records) {
        String tzKey = tzById.get(rec.OwnerId);
        if (tzKey != null) {
            TimeZone ownerTz = TimeZone.getTimeZone(tzKey);
            Datetime localNow = nowUtc.addSeconds(ownerTz.getOffset(nowUtc) / 1000);
            rec.ProcessedDate__c = localNow.date();
        }
    }
    update records;
}
```

**Detection hint:** `UserInfo.getTimeZone()` inside a class implementing `Database.Batchable`, `Database.Schedulable`, or any context where the running user is a system or integration user rather than the record owner.

---

## Anti-Pattern 6: Using DAY_ONLY() in SOQL for User-Timezone Date Grouping

**What the LLM generates:**

```apex
// Count records created "today" grouped by day
AggregateResult[] results = [
    SELECT DAY_ONLY(CreatedDate) dayBucket, COUNT(Id) cnt
    FROM Case
    GROUP BY DAY_ONLY(CreatedDate)
    ORDER BY DAY_ONLY(CreatedDate)
];
```

**Why it happens:** `DAY_ONLY()` is a documented SOQL date function and appears in many official examples for grouping by calendar date. LLMs use it as the natural answer to "group by date" without noting that it extracts the UTC date, not the user's local date.

**Correct pattern:** If UTC bucketing is intentional (e.g., a system-level audit), document it explicitly. If local-timezone bucketing is needed, compute UTC boundaries for each local day and use range filters instead of `DAY_ONLY()`, or perform the bucketing in Apex after querying the raw Datetime values.

```apex
// If user-timezone bucketing is required, query raw CreatedDate and bucket in Apex
TimeZone tz = UserInfo.getTimeZone();
List<Case> cases = [SELECT Id, CreatedDate FROM Case WHERE CreatedDate = LAST_N_DAYS:7];
Map<Date, Integer> countByLocalDate = new Map<Date, Integer>();
for (Case c : cases) {
    Datetime localDt = c.CreatedDate.addSeconds(tz.getOffset(c.CreatedDate) / 1000);
    Date localDate = localDt.date();
    Integer current = countByLocalDate.get(localDate) ?? 0;
    countByLocalDate.put(localDate, current + 1);
}
```

**Detection hint:** `DAY_ONLY(` in SOQL queries that are described as user-facing analytics or reporting. Flag for review of whether UTC or local-timezone bucketing is intended.
