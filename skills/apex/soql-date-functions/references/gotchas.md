# Gotchas — SOQL Date Functions

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: A date-function result cannot be compared to a date literal

**What happens:** `WHERE CALENDAR_YEAR(CloseDate) = 2026-01-01` (or `= THIS_YEAR`) fails to
compile with a malformed-query error.

**When it occurs:** whenever the right-hand side of the comparison is a date literal — an ISO
date (`2026-01-01`) or a relative literal (`TODAY`, `THIS_MONTH`, `LAST_N_DAYS:30`). A date
function returns a number, and you can't compare that result to a date literal.

**How to avoid:** compare to an **integer** (`CALENDAR_YEAR(CloseDate) = 2026`). If you meant
a rolling window, drop the function and put the literal on the raw field
(`WHERE CloseDate = THIS_YEAR`).

---

## Gotcha 2: FISCAL_* functions break under custom fiscal years

**What happens:** `FISCAL_MONTH()`, `FISCAL_QUARTER()`, or `FISCAL_YEAR()` throws in one org
while the identical query works in another.

**When it occurs:** the failing org has **custom (generic) fiscal years enabled**. These
functions are not supported in that configuration — it is an org setting, not a query bug.

**How to avoid:** confirm the org uses standard fiscal years before relying on `FISCAL_*`.
Where custom fiscal years are in play, group by calendar functions (`CALENDAR_QUARTER()`) or
by a fiscal-period formula/roll-up field defined for that calendar.

---

## Gotcha 3: DAY_ONLY() and HOUR_IN_DAY() reject Date fields

**What happens:** `DAY_ONLY(SomeDate__c)` or `HOUR_IN_DAY(CloseDate)` errors even though the
field holds a date.

**When it occurs:** the argument is a `Date` field (or a formula returning `Date`). Both
functions accept **only a `DateTime` field** — they exist to extract the date part or hour
from a `DateTime`.

**How to avoid:** apply them to genuine `DateTime` fields (`CreatedDate`, `LastModifiedDate`,
a custom `DateTime` field). For period extraction from a `Date` field, use
`CALENDAR_MONTH()` / `DAY_IN_MONTH()` and friends, which accept both types.

---

## Gotcha 4: Date functions bucket on UTC, not the user's day

**What happens:** a record the user created at 11:30pm local time shows up in the next day's,
month's, or quarter's bucket.

**When it occurs:** the field is a `DateTime`. SOQL returns `DateTime` values as UTC, and the
date function extracts the period from that raw UTC instant — so local evening records cross
the UTC date boundary.

**How to avoid:** wrap the field in `convertTimezone()` before the date function
(`CALENDAR_MONTH(convertTimezone(CreatedDate))`) when buckets must follow the running user's
local day. Pure `Date` fields have no time component and are unaffected.

---

## Gotcha 5: A date function in SELECT must be repeated in GROUP BY

**What happens:** `SELECT CALENDAR_YEAR(CloseDate), SUM(Amount) FROM Opportunity` (no
`GROUP BY`) fails, or a mismatch between the `SELECT` and `GROUP BY` expressions is rejected.

**When it occurs:** any time a date function appears in the `SELECT` list. You can't use a
date function in a `SELECT` clause unless you also include it in the `GROUP BY` clause, and
the two expressions must match.

**How to avoid:** repeat the function verbatim in `GROUP BY`
(`GROUP BY CALENDAR_YEAR(CloseDate)`). If you only want to *filter*, move the function to
`WHERE` — there it needs no `GROUP BY` at all.
