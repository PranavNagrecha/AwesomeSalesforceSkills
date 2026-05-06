# LLM Anti-Patterns — Currency Management Patterns

Mistakes AI assistants commonly make when generating multi-currency
Apex / SOQL / formula / report logic.

---

## Anti-Pattern 1: Using `convertCurrency()` and assuming ACM dated rates apply

**What the LLM generates.**

```apex
SELECT convertCurrency(Amount) FROM Opportunity WHERE CloseDate >= LAST_FISCAL_YEAR
```

> This converts each opportunity's amount to corporate currency using
> the dated exchange rate effective on the close date.

**Why it happens.** Documentation pages mention `convertCurrency()`
and dated rates in the same general topic; the LLM conflates them.

**Correct pattern.** `convertCurrency()` consults the static
`CurrencyType.ConversionRate`, never `DatedConversionRate`. For
dated-rate conversion, query `DatedConversionRate` explicitly.

**Detection hint.** Any code or comment that pairs
`convertCurrency()` with the assertion that it uses dated /
historical / period rates.

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
