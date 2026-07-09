# Examples — SOQL Aggregate Field-Type Support

All queries below are illustrative and authored from the official SOQL and SOSL Reference
(Aggregate Functions and "Support for Field Types in Aggregate Functions"). Field and object
API names are placeholders — substitute your own. The compatibility matrix these examples rely
on lives in `SKILL.md`.

## Example 1: "Average close date" — the classic non-numeric aggregate error

**Context:** a report request asks for the "average close date" of won Opportunities, and the
first instinct (from SQL habit) is to average the date field.

**Problem:** `CloseDate` is a `date` field. Date and dateTime types support the counts, `MIN()`,
and `MAX()` — but **not** `AVG()` or `SUM()`. The query below does not return null; it fails to
execute, taking the whole request down with it.

**Solution:**

```sql
-- WRONG: AVG()/SUM() are not defined for date fields — this errors
SELECT AVG(CloseDate) FROM Opportunity WHERE IsWon = true

-- RIGHT: express the intent with MIN()/MAX(), which dates DO support
SELECT MIN(CloseDate) earliest, MAX(CloseDate) latest
FROM Opportunity
WHERE IsWon = true
```

**Why it works:** the matrix row for date/dateTime is `MIN/MAX/COUNT/COUNT_DISTINCT = Yes`,
`AVG/SUM = No`. "Earliest" and "latest" map onto `MIN()`/`MAX()`; there is no meaningful average
of a set of dates in SOQL, so the platform doesn't offer one.

---

## Example 2: Summing a currency field in a multi-currency org

**Context:** an org has multi-currency enabled. A dashboard needs pipeline totals, and someone
writes a single `SUM(Amount)`.

**Problem:** aggregate results on currency fields **default to the system (corporate) currency**.
An ungrouped `SUM(Amount)` silently converts every record to corporate currency and adds them —
producing a number that no single stakeholder's currency view will match, with nothing in the
result to indicate which currency it is.

**Solution:**

```sql
-- Ambiguous in a multi-currency org: one corporate-currency figure, untraceable
SELECT SUM(Amount) FROM Opportunity

-- Auditable: each subtotal is in exactly one currency
SELECT CurrencyIsoCode, SUM(Amount) total
FROM Opportunity
GROUP BY CurrencyIsoCode
ORDER BY CurrencyIsoCode
```

**Why it works:** grouping by `CurrencyIsoCode` keeps each `SUM()` within a single currency, so the
"defaults to system currency" behavior no longer blends unlike values. `currency` is a fully
numeric type, so `SUM()`/`AVG()` are valid — the multi-currency nuance is about *interpretation*,
not support.

---

## Example 3: Counting semantics and a picklist MIN/MAX inside a selector

**Context:** you want, per Account, the number of Contacts, the number with an Email on file, the
number of distinct Lead Sources, and the "lowest" Stage — and you keep the SOQL in a selector.

**Problem:** `COUNT(Id)` and `COUNT(Email)` are easy to conflate, and `MIN()` on a picklist looks
like it should sort alphabetically. Both assumptions produce wrong numbers, not errors.

**Solution:** keep the query in a selector method (extends
[`templates/apex/BaseSelector.cls`](../../../templates/apex/BaseSelector.cls)) so it runs in the
caller's mode and is reusable:

```sql
SELECT AccountId,
       COUNT(Id) totalContacts,          -- counts every row (nulls included)
       COUNT(Email) withEmail,           -- ignores rows where Email is null
       COUNT_DISTINCT(LeadSource) sources -- distinct, non-null LeadSource values
FROM Contact
GROUP BY AccountId
```

```apex
// ContactsSelector.cls — extends BaseSelector (templates/apex/BaseSelector.cls)
public with sharing class ContactsSelector extends BaseSelector {
    public List<AggregateResult> countsByAccount() {
        return [
            SELECT AccountId,
                   COUNT(Id) totalContacts,
                   COUNT(Email) withEmail,
                   COUNT_DISTINCT(LeadSource) sources
            FROM Contact
            GROUP BY AccountId
        ];
    }
}
```

For a picklist, remember the ordering rule:

```sql
-- MIN(StageName) returns the FIRST stage in the picklist's Setup sort order,
-- NOT the alphabetically-first label.
SELECT AccountId, MIN(StageName) firstStage
FROM Opportunity
GROUP BY AccountId
```

**Why it works:** `COUNT(Id)` counts all rows (it and `COUNT()` are the only functions that don't
ignore nulls), while `COUNT(Email)` and `COUNT_DISTINCT(LeadSource)` skip nulls — so the three
numbers legitimately differ. `MIN()`/`MAX()` on a picklist follow the picklist's defined value
order, so `MIN(StageName)` is the top-of-list stage, not "A…".

---

## Anti-Pattern: assuming a formula or picklist field is numeric enough to average

**What practitioners do:** call `AVG()` or `SUM()` on a picklist (e.g. `AVG(Rating__c)`), or on a
formula field that *displays* a number, without checking the underlying type or the formula's
return type.

**What goes wrong:** a text or picklist field — even one whose values look numeric — has no
`AVG()`/`SUM()` support, so the query errors. A formula field only supports what its **return
type** supports, so a Text-returning formula behaves like text, not like a number.

**Correct approach:** confirm the field is int, double, currency, or percent before using
`AVG()`/`SUM()`. For a formula field, look up its return type and apply that type's matrix row. If
you need to average a categorical field, convert it to a genuine numeric field (or a
number-returning formula) upstream first.
