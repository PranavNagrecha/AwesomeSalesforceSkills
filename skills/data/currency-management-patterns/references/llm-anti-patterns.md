# LLM Anti-Patterns — Currency Management Patterns

Mistakes AI assistants commonly make when generating multi-currency
Apex / SOQL / formula / report logic.

---

## Anti-Pattern 1: Over-generalizing which rate `convertCurrency()` uses

**What the LLM generates.**

```apex
SELECT convertCurrency(Custom_Amount__c) FROM Opportunity
```

> This converts the custom amount to corporate currency using the
> dated exchange rate effective on the close date.

**Why it happens.** The LLM learns "ACM = dated rates" and "convert =
corporate currency" as blanket rules and applies them to every field.

**Correct pattern.** Two corrections. (1) `convertCurrency()` converts
to the *running user's* currency, not the corporate currency. (2) It
honors dated rates only under ACM and only for ACM-eligible standard
fields (opportunities, opportunity line items, opportunity history); a
custom currency field, formula field, or roll-up summary always
converts at the static `CurrencyType.ConversionRate`. For an
as-of-date value on a non-eligible field, query `DatedConversionRate`
explicitly.

**Detection hint.** Any claim that `convertCurrency()` returns the
corporate currency, or that it applies dated rates to a custom /
formula / roll-up currency field.

---

## Anti-Pattern 2: Filter on currency field without specifying currency

**What the LLM generates.**

```apex
SELECT Id FROM Opportunity WHERE Amount > 100000
```

> Returns all opportunities worth more than $100K.

**Why it happens.** Dollar bias — the LLM interprets a numeric
threshold as USD without surfacing that the filter compares native
values.

**Correct pattern.** State the currency explicitly. Either filter on
`CurrencyIsoCode = 'USD' AND Amount > 100000`, or convert before
filtering.

**Detection hint.** Any unqualified "Amount > N" SOQL filter in a
multi-currency org context, especially when the comment talks
about "$" or implies a particular currency.

---

## Anti-Pattern 3: Inserting `DatedConversionRate` with `NextStartDate`

**What the LLM generates.**

```apex
DatedConversionRate r = new DatedConversionRate(
    IsoCode = 'EUR',
    StartDate = Date.newInstance(2026, 1, 1),
    NextStartDate = Date.newInstance(2026, 2, 1),
    ConversionRate = 1.07
);
insert r;
```

**Why it happens.** Mirrors a typical "valid from / valid to" data
model in financial systems.

**Correct pattern.** Omit `NextStartDate`. The platform computes it
based on the next contiguous row.

**Detection hint.** Any DML against `DatedConversionRate` that sets
`NextStartDate`.

---

## Anti-Pattern 4: Formula `Amount + Related_Cost__c` as cross-currency total

**What the LLM generates.**

```
Total__c = Amount + Account.Negotiated_Discount__c
```

**Why it happens.** Looks like a clean cross-record total. The LLM
does not surface that currency arithmetic across different
`CurrencyIsoCode` values is not auto-converted in formulas.

**Correct pattern.** Cross-record currency arithmetic in formula
fields is fragile. Use Apex with explicit conversion, or constrain
both records to the same currency.

**Detection hint.** Any formula adding / subtracting currency fields
that come from different parent records (cross-object reference in
the formula).

---

## Anti-Pattern 5: Suggesting "disable multi-currency" when simplification is desired

**What the LLM generates.**

> If multi-currency is no longer needed, disable it from Setup ->
> Company Information.

**Why it happens.** The LLM mirrors the toggle's name without
surfacing irreversibility.

**Correct pattern.** Multi-currency cannot be disabled. The only
options are to coexist (and constrain new records to a single
currency) or to migrate to a fresh org.

**Detection hint.** Any guidance about disabling or removing
multi-currency.

---

## Anti-Pattern 6: Roll-up summary expected to use dated rates with ACM

**What the LLM generates.**

> With ACM enabled, the roll-up summary on Account.Total_Pipeline
> aggregates child opportunity amounts using each opportunity's
> dated exchange rate.

**Why it happens.** ACM marketing emphasizes dated rates without
listing exclusions.

**Correct pattern.** Roll-up summaries are not in ACM scope. They
use the static `CurrencyType.ConversionRate`. For dated-rate
roll-ups, drop to Apex.

**Detection hint.** Any claim that ACM affects roll-up summary or
formula or custom-currency-field calculations.

---

## Anti-Pattern 7: Assuming child records inherit parent's `CurrencyIsoCode`

**What the LLM generates.**

```apex
Opportunity o = new Opportunity(AccountId = acc.Id, ... );
insert o;
// o.CurrencyIsoCode == acc.CurrencyIsoCode
```

**Why it happens.** Cascading defaults are intuitive.

**Correct pattern.** `CurrencyIsoCode` defaults to the running
user's currency, not the parent record's. Set it explicitly when
parent-child consistency matters.

**Detection hint.** Any Apex insert of a currency-aware child
without explicit `CurrencyIsoCode`, accompanied by an assumption
that it will match the parent.

---

## Anti-Pattern 8: `convertCurrency()` in a `WHERE` or `ORDER BY` clause

**What the LLM generates.**

```apex
SELECT Id FROM Opportunity
WHERE convertCurrency(Amount) > 5000
ORDER BY convertCurrency(Amount) DESC
```

**Why it happens.** By analogy with ordinary functions, the LLM
assumes a `SELECT`-clause function is valid anywhere in the query.

**Correct pattern.** `convertCurrency()` is only valid in `SELECT`. In
`WHERE`, use an ISO-code-qualified literal (`WHERE Amount > USD5000`).
For sorting, `ORDER BY Amount` already sorts on the converted value —
`convertCurrency()` can't be combined with `ORDER BY`.

**Detection hint.** `convertCurrency(` appearing anywhere other than
the `SELECT` clause.

---

## Anti-Pattern 9: Assuming grouped aggregates return the user's currency

**What the LLM generates.**

```apex
SELECT OwnerId, SUM(Amount) total FROM Opportunity GROUP BY OwnerId
```

> total is each owner's pipeline in the running user's currency.

**Why it happens.** The LLM assumes currency results follow the same
user-currency convention as ungrouped queries.

**Correct pattern.** With `GROUP BY` or `HAVING`, aggregate currency
results (`SUM()`, `MAX()`, …) come back in the org's default
(corporate) currency. You can't wrap the aggregate in
`convertCurrency()` or compare it to an ISO-code literal. Label the
result as corporate currency, or aggregate converted per-row values in
Apex.

**Detection hint.** A grouped currency aggregate described as being in
the user's or a per-record currency.

---

## Anti-Pattern 10: Querying Data Cloud currency like a standard sObject

**What the LLM generates.**

```apex
SELECT CurrencyIsoCode, toLabel(CurrencyIsoCode), Currency__c FROM <DMO>
```

**Why it happens.** The LLM applies standard-sObject currency patterns
to Data Cloud data lake / data model objects.

**Correct pattern.** For DLOs/DMOs: read the ISO code from
`cdp_sys_record_currency__c` (not `CurrencyIsoCode`); alias
`toLabel(CurrencyIsoCode)` in `SELECT`
(`toLabel(CurrencyIsoCode) CurrencyCodeAlias`); treat an all-null
currency result as an unsupported/invalid ISO code; and round
`convertCurrency()` output yourself, because it isn't rounded to the
org's configured decimal places for Data Cloud fields.

**Detection hint.** Standard `CurrencyIsoCode` usage, or an unaliased
`toLabel(CurrencyIsoCode)`, against a Data Cloud DLO/DMO.
