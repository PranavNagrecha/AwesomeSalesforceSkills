# LLM Anti-Patterns — SOQL Date Functions

Common mistakes AI coding assistants make when generating or advising on SOQL date functions.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Comparing a date function to a date literal

**What the LLM generates:**

```sql
WHERE CALENDAR_YEAR(CloseDate) = 2026-01-01
WHERE CALENDAR_MONTH(CreatedDate) = THIS_MONTH
```

**Why it happens:** the model sees "date field" and pattern-matches a date on the right-hand
side, blending SOQL date literals with date functions. It misses that the function returns a
number.

**Correct pattern:**

```sql
WHERE CALENDAR_YEAR(CloseDate) = 2026
WHERE CALENDAR_MONTH(CreatedDate) = 7
```

**Detection hint:** a date function on the left of a comparison whose right-hand side matches
`\d{4}-\d{2}-\d{2}` or a relative literal keyword (`THIS_MONTH`, `LAST_N_DAYS:...`).

---

## Anti-Pattern 2: Confusing date functions with SOQL date literals

**What the LLM generates:** invents `THIS_YEAR()` / `LAST_MONTH()` as functions, or claims
`CALENDAR_YEAR` is a relative window.

```sql
WHERE CloseDate = THIS_YEAR()          -- literals are not called like functions
WHERE CALENDAR_YEAR(CloseDate) = LAST_YEAR
```

**Why it happens:** both live in the "SOQL date" space, so the model fuses two distinct
features — functions that *extract a period number* vs. literals that *name a rolling window*.

**Correct pattern:** literals are bare keywords on the raw field; functions wrap a field and
return a number:

```sql
WHERE CloseDate = THIS_YEAR                       -- relative literal, no parentheses
WHERE CALENDAR_YEAR(CloseDate) = 2025             -- function returns a number
```

**Detection hint:** parentheses after `THIS_YEAR`/`LAST_MONTH`/`TODAY`, or a `CALENDAR_*` /
`FISCAL_*` function compared to a literal keyword.

---

## Anti-Pattern 3: Date function in SELECT without matching GROUP BY

**What the LLM generates:**

```sql
SELECT CALENDAR_YEAR(CloseDate), SUM(Amount) FROM Opportunity
```

**Why it happens:** the model treats a date function like an ordinary selected field and
forgets the aggregation contract.

**Correct pattern:**

```sql
SELECT CALENDAR_YEAR(CloseDate), SUM(Amount)
FROM Opportunity
GROUP BY CALENDAR_YEAR(CloseDate)
```

**Detection hint:** a `CALENDAR_*`/`FISCAL_*`/`DAY_*`/`WEEK_*`/`HOUR_IN_DAY` call in the
`SELECT` list with no identical expression in a `GROUP BY` clause.

---

## Anti-Pattern 4: Applying DAY_ONLY() / HOUR_IN_DAY() to a Date field

**What the LLM generates:**

```sql
SELECT DAY_ONLY(CloseDate) FROM Opportunity     -- CloseDate is a Date, not DateTime
```

**Why it happens:** the model knows these are "date" functions and doesn't track that they
are DateTime-only.

**Correct pattern:** use them on `DateTime` fields; for a `Date` field use the calendar/day
functions:

```sql
SELECT DAY_ONLY(CreatedDate) FROM Opportunity    -- CreatedDate is a DateTime
SELECT DAY_IN_MONTH(CloseDate) FROM Opportunity  -- Date field
```

**Detection hint:** `DAY_ONLY(` or `HOUR_IN_DAY(` wrapping a known `Date` field such as
`CloseDate`, `Birthdate`, or a custom `__c` date field.

---

## Anti-Pattern 5: Using FISCAL_* without flagging the custom-fiscal-year restriction

**What the LLM generates:** confident `FISCAL_QUARTER()` / `FISCAL_YEAR()` guidance with no
caveat, presented as universally available.

**Why it happens:** the restriction is an org-configuration detail the model rarely surfaces.

**Correct pattern:** state that `FISCAL_MONTH/QUARTER/YEAR` are **not supported when the org
has custom fiscal years enabled**, and offer a calendar-function or fiscal-formula fallback.

**Detection hint:** any `FISCAL_*` recommendation that omits the custom-fiscal-year caveat.

---

## Anti-Pattern 6: Hallucinated function names

**What the LLM generates:** `CALENDAR_DAY()`, `DAY_OF_WEEK()`, `WEEK_OF_YEAR()`,
`FISCAL_WEEK()`, `MONTH()`, `YEAR()` — names borrowed from SQL/Java date APIs.

**Why it happens:** SQL dialects and Java `Calendar`/`java.time` bleed into the model's
output; it produces plausible-looking names that don't exist in SOQL.

**Correct pattern:** use only the 13 documented functions: `CALENDAR_MONTH`,
`CALENDAR_QUARTER`, `CALENDAR_YEAR`, `DAY_IN_MONTH`, `DAY_IN_WEEK`, `DAY_IN_YEAR`,
`DAY_ONLY`, `FISCAL_MONTH`, `FISCAL_QUARTER`, `FISCAL_YEAR`, `HOUR_IN_DAY`, `WEEK_IN_MONTH`,
`WEEK_IN_YEAR`.

**Detection hint:** any date-ish `*(field)` call whose name is not in the 13-function list —
especially `MONTH()`, `YEAR()`, `DAY_OF_*`, `*_OF_*`, or `FISCAL_WEEK`.
