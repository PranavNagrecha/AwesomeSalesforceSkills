# Well-Architected Notes — Timezone and Datetime Pitfalls

## Relevant Pillars

- **Reliability** — Timezone bugs are silent and intermittent. They surface only for users in specific timezones at specific times of day, making them difficult to reproduce and easy to miss in testing. Incorrect date comparisons can silently skip records, process them twice, or assign wrong deadlines — all reliability failures. Using explicit UTC-safe methods and testing with non-UTC users is required for reliable date-handling code.

- **Operational Excellence** — Timezone-related defects are disproportionately hard to diagnose in production because the incorrect behavior depends on the running user's profile and the wall-clock time. Code that is explicit about timezone semantics — using `newInstanceGmt`, named timezone strings in `format()`, and owner-timezone-aware batch logic — is far easier to reason about during an incident. Operational excellence requires that timezone behavior be visible in the code, not implicit in platform defaults.

- **Security** — Timezone bugs are not a direct security concern, but incorrect date filtering in SOQL can cause records to appear in the wrong user's view window, potentially exposing data for the wrong reporting period. Date-boundary errors in access-control logic (e.g., "this record is only visible today") can produce incorrect access windows. These are low-severity but real confidentiality risks in compliance-sensitive orgs.

- **Performance** — SOQL date literals are well-indexed. Replacing them with explicit datetime range bind variables (to achieve timezone-correctness) does not harm query performance if the Datetime field is indexed. However, computing timezone-adjusted values in Apex for every record in a large batch can add overhead — centralize offset calculations outside the record loop.

## Architectural Tradeoffs

**Date literals vs explicit UTC ranges in SOQL:** Date literals (`TODAY`, `LAST_WEEK`) are readable and concise, but their result sets depend on the running user's timezone. Explicit UTC datetime ranges are deterministic across all users but require more code. The right choice depends on whether the query is user-context-sensitive (date literals acceptable) or system-context (UTC ranges required).

**`Date.today()` vs user-timezone-aware today:** `Date.today()` is simpler and correct for most system-level operations where the server UTC date is the authoritative date. For user-facing record defaults or SLA calculations, the user's local calendar date is what matters. Choosing the wrong "today" semantics silently introduces off-by-one-day errors for a subset of users.

**Storing local dates vs UTC Datetime:** Some teams store a "local date" as a separate Date field alongside a Datetime field to avoid extraction pitfalls. This trades storage for clarity and eliminates the timezone-extraction problem at read time. The cost is keeping the Date field in sync whenever the Datetime changes — a consistency problem for updates.

## Anti-Patterns

1. **Timezone-implicit Date extraction** — Calling `.date()` on a Datetime and storing the result in a Date field without acknowledging that the extracted date is UTC-based. This creates a systematic off-by-one-day error for users east of UTC. Every `.date()` call in production code should have a comment explaining whether UTC-date semantics are intentional or whether a timezone-adjusted extraction is needed.

2. **Fixed-offset timezone arithmetic** — Hardcoding a numeric offset (e.g., `-8` for Pacific) instead of using `TimeZone.getOffset(targetDatetime)`. Fixed offsets break twice a year at DST transitions. The platform provides the `TimeZone` class precisely so that DST-aware offset lookup is a single method call — there is no justification for hardcoding timezone offsets in Apex.

3. **Assuming the running user's timezone is the record owner's timezone** — In batch jobs, scheduled Apex, and system integrations, `UserInfo.getTimeZone()` returns the executing user's timezone, not the timezone of the records being processed or their owners. Applying the system user's timezone to calculate dates for records owned by users in other timezones produces wrong results at scale in global orgs.

## Official Sources Used

- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Apex Reference Guide — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm
- SOQL and SOSL Reference — Date Formats and Date Literals — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_dateformats.htm
- Salesforce Help — Date and Time Field Types — https://help.salesforce.com/s/articleView?id=sf.custom_field_types.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
