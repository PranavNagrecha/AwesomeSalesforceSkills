# LLM Anti-Patterns — SOQL Aggregate Field-Type Support

Common mistakes AI coding assistants make when generating or advising on SOQL aggregate functions
across field types. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: AVG()/SUM() on a date or dateTime field

**What the LLM generates:** `SELECT AVG(CloseDate) FROM Opportunity` or `SUM(CreatedDate)`, treating
a date like a numeric column.

**Why it happens:** ANSI SQL and Java training data freely average and subtract dates, so the model
transfers that habit to SOQL — where date/dateTime support only the counts, `MIN()`, and `MAX()`.

**Correct pattern:**

```sql
SELECT MIN(CloseDate) earliest, MAX(CloseDate) latest FROM Opportunity
```

**Detection hint:** flag any `AVG(` or `SUM(` whose argument is a date/dateTime field (names ending
`Date`, `Datetime`, `__c` date fields). SOQL never averages or sums dates.

---

## Anti-Pattern 2: Assuming MIN()/MAX() on a picklist sorts alphabetically

**What the LLM generates:** commentary like "`MIN(StageName)` returns the alphabetically-first
stage," or logic that depends on A–Z ordering of a picklist.

**Why it happens:** in SQL, `MIN()` on a string is lexicographic, so the model assumes the same for
Salesforce picklists — but SOQL uses the picklist's **defined value sort order** instead.

**Correct pattern:**

```
MIN(StageName) => the FIRST value in the picklist's Setup ordering,
                  which may differ from the alphabetically-first label.
```

**Detection hint:** any explanation of picklist `MIN()`/`MAX()` that mentions "alphabetical,"
"A to Z," or lexicographic order is wrong for picklists.

---

## Anti-Pattern 3: Treating COUNT(field) like SQL COUNT(*)

**What the LLM generates:** `COUNT(Email)` (or any `COUNT(fieldName)`) presented as the total number
of rows, interchangeable with `COUNT(Id)`.

**Why it happens:** SQL's `COUNT(column)` vs `COUNT(*)` distinction is subtle, and models often
collapse them; in SOQL, all aggregate functions ignore nulls **except** `COUNT()` and `COUNT(Id)`.

**Correct pattern:**

```
COUNT(Id)     => every matching row (nulls included)  -- use for total record count
COUNT(Email)  => only rows where Email is non-null     -- use for "populated" count
```

**Detection hint:** a `COUNT(<non-Id field>)` described as "the number of records" without noting it
skips nulls is a defect.

---

## Anti-Pattern 4: Claiming any field can be aggregated

**What the LLM generates:** guidance that "you can COUNT any field," or an aggregate over a boolean,
time, multipicklist, address, location, base64, or encryptedstring field.

**Why it happens:** the model generalizes "aggregate functions work on fields" without surfacing the
documented exclusion set — several types support **no** aggregate function, not even `COUNT()`.

**Correct pattern:** state the exclusion explicitly and refactor. base64, boolean, time,
multipicklist, address, location, and encryptedstring support none of the six functions; derive a
supported field (e.g. a 1/0 number for a boolean) and aggregate that.

**Detection hint:** any aggregate call whose field type is in the no-support set, or advice omitting
that set entirely.

---

## Anti-Pattern 5: Ignoring multi-currency currency defaulting

**What the LLM generates:** `SELECT SUM(Amount) FROM Opportunity` in a multi-currency org, presented
as "the total pipeline," with no mention of currency conversion.

**Why it happens:** the model treats currency as an ordinary number and doesn't model the org-level
multi-currency behavior — aggregate results on currency fields default to the system (corporate)
currency.

**Correct pattern:**

```sql
SELECT CurrencyIsoCode, SUM(Amount) total FROM Opportunity GROUP BY CurrencyIsoCode
```

**Detection hint:** an ungrouped `SUM()`/`AVG()` on a currency field with no `GROUP BY
CurrencyIsoCode` and no note about corporate-currency defaulting, in a multi-currency context.

---

## Anti-Pattern 6: Averaging a formula field by its display, not its return type

**What the LLM generates:** `AVG(SomeFormula__c)` because the formula "shows a number," or a blanket
claim that formula fields are always aggregatable.

**Why it happens:** the model reasons from the rendered value rather than the field's declared return
type; support "depends on the type of the calculated field," which the model doesn't check.

**Correct pattern:** determine the formula's return type first — a Number/Currency/Percent formula
supports `AVG()`/`SUM()`; a Text, Date, or Checkbox formula follows that type's row (no AVG/SUM for
Text or Date, none at all for Checkbox).

**Detection hint:** an aggregate on a formula field with no verification of its return type, or an
`AVG()`/`SUM()` on a Text- or Date-returning formula.

---

## Anti-Pattern 7: Hallucinating a maturity label or LIMIT-with-aggregate

**What the LLM generates:** "this GA feature since Spring 'XX," or `SELECT COUNT(Id) FROM Account
LIMIT 100`.

**Why it happens:** models pattern-fill GA/Beta labels and add `LIMIT` reflexively. Aggregate
field-type support is longstanding core SOQL reference behavior with **no** GA/Beta/Pilot label
(only `MAX()` carries a version note: available in API 18.0 and later), and `LIMIT` is disallowed on
an aggregate query that has no `GROUP BY`.

**Correct pattern:** do not attach a maturity label the docs don't state; drop `LIMIT` from
ungrouped aggregates and constrain rows with `WHERE` instead.

**Detection hint:** a "Generally Available / Beta" claim for this behavior, or a `LIMIT` on an
aggregate query with no `GROUP BY`.
