# Examples — Currency Management Patterns

## Example 1 — `convertCurrency()` does not consult dated rates

**Context.** Org has Advanced Currency Management enabled. Finance
runs a SOQL-driven backfill in Apex:

```apex
List<Opportunity> opps = [
    SELECT Id, convertCurrency(Amount), CloseDate
    FROM Opportunity
    WHERE CloseDate >= LAST_FISCAL_YEAR
];
```

**The bug.** `convertCurrency()` uses the static
`CurrencyType.ConversionRate`, even when ACM is enabled. Opportunities
closed 18 months ago are converted at today's rate, not the rate
that was effective on `CloseDate`. The Lightning UI and standard
Opportunity reports display the dated rate, producing a discrepancy
between Apex output and the report.

**Right answer.** Either accept the static-rate semantics for SOQL
(document it), or compute the dated conversion explicitly by
querying `DatedConversionRate`:

```apex
DatedConversionRate r = [
    SELECT ConversionRate FROM DatedConversionRate
    WHERE IsoCode = :opp.CurrencyIsoCode
      AND StartDate <= :opp.CloseDate
      AND (NextStartDate > :opp.CloseDate OR NextStartDate = NULL)
    LIMIT 1
];
```

Then apply `r.ConversionRate` manually to `opp.Amount`.

---

## Example 2 — Formula field summing fields in different currencies

**Context.** Custom formula on Opportunity:
`Amount + Custom_Add_On__c`. Both are currency fields. Opportunity is
in EUR.

**The bug.** Currency formulas do not auto-convert. The result is the
sum of the numeric values, regardless of whether the inputs share
the same `CurrencyIsoCode`. Within a single record this is fine
because all currency fields on that record share the parent's
`CurrencyIsoCode`. The bug appears when the formula references a
field on a related object that has a different `CurrencyIsoCode`.

**Right answer.** Cross-record currency arithmetic in formula fields
is fragile. For the case of `Account.Total__c` rolling up child
Opportunities in mixed currencies, formula will not deliver — drop
to Apex with explicit conversion or constrain children to the
parent's currency.

---

## Example 3 — Roll-up summary in a mixed-currency context

**Context.** `Account.Open_Pipeline__c` is a roll-up summary `SUM` of
`Opportunity.Amount` filtered to open stages. Account is in USD.
Half the child Opportunities are EUR.

**Behavior.** Roll-up summary on a currency field across child
records in different currencies returns the parent's currency, but
internally the platform converts each child using the static
`CurrencyType.ConversionRate`. With ACM enabled, the report next to
the same data may show a different total because the report uses
dated rates.

**Right answer.** If exact-rate consistency matters, the roll-up
summary is not the right tool. Use Apex-driven calculations that
explicitly query `DatedConversionRate` for each child's `CloseDate`,
or constrain the relationship so children always share the parent's
currency.

---

## Example 4 — `CurrencyIsoCode` picklist and active currencies

**Context.** Setup -> Company Information shows USD, EUR, GBP, CAD as
active. JPY was activated, used briefly, then deactivated. Records
created during the JPY-active window still have `CurrencyIsoCode =
'JPY'`.

**Behavior.**

- Deactivating a currency does not delete the `CurrencyType` record;
  it sets `IsActive = false`.
- Existing records keep their `CurrencyIsoCode = 'JPY'` and remain
  valid.
- New records cannot be created with deactivated currencies via
  standard UI; Apex insert with `CurrencyIsoCode = 'JPY'` may succeed
  depending on validation.

**Implication.** Audit existing data before deactivating a currency.
Reports that filter by currency will still show the JPY records.

---

## Example 5 — Exchange-rate update process

**Context.** ACM is enabled. Finance needs to load monthly exchange
rates effective the first of each month.

**Approach.**

```apex
public class ExchangeRateLoader {
    public static void loadMonthlyRates(
        String isoCode, Date startDate, Decimal rate
    ) {
        DatedConversionRate r = new DatedConversionRate(
            IsoCode = isoCode,
            StartDate = startDate,
            ConversionRate = rate
        );
        insert r;
        // Salesforce auto-fills NextStartDate based on the next row.
    }
}
```

Notes:

- `DatedConversionRate` rows are read-only via standard UI; metadata
  API and Apex can write them.
- `NextStartDate` is computed by the platform — do not set it.
- After insert, existing records' converted values in reports update
  to reflect the new dated rate.

---

## Example 6 — When to use `convertCurrency()` vs not

| Scenario | `convertCurrency()` | Reason |
|---|---|---|
| Total revenue in corporate currency for a dashboard | Yes | Dashboard expects single-currency totals |
| Editing an Opportunity record (display Amount in the rep's currency) | No | Need the record's native value |
| Comparing budget across regions | Yes | Apples-to-apples requires single currency |
| Financial-period audit query | No (use `DatedConversionRate` explicitly) | `convertCurrency()` uses static rate; audit needs dated rate |
| Cross-currency aggregations in a controller | Yes (and document the static-rate semantics) | Better than re-implementing rate lookup |
