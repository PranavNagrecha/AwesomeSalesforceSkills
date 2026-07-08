# Examples — Currency Management Patterns

## Example 1 — `convertCurrency()` and dated rates under ACM

**Context.** Org has Advanced Currency Management enabled. Finance
runs a SOQL-driven backfill in Apex:

```apex
List<Opportunity> opps = [
    SELECT Id, convertCurrency(Amount), CloseDate
    FROM Opportunity
    WHERE CloseDate >= LAST_FISCAL_YEAR
];
```

**What actually happens.** Under ACM, `convertCurrency(Amount)` on an
Opportunity uses the dated exchange rate that corresponds to
`CloseDate`, not today's rate. `Amount` is an ACM-eligible field, so
the SOQL-converted value matches what the standard Opportunity report
shows. The common mistake is assuming `convertCurrency()` always uses
the current rate and then hand-rolling a `DatedConversionRate` lookup
to "fix" a discrepancy that doesn't exist for this field. (The
converted value is in the running user's currency, not necessarily
corporate.)

**When you DO need the manual lookup.** ACM's dated rates cover only a
defined set of standard fields (opportunities, opportunity line items,
opportunity history). For a value that isn't ACM-eligible — a custom
currency field, a formula input, or any field when ACM is off — an
as-of-date conversion requires an explicit `DatedConversionRate`
query:

```apex
DatedConversionRate r = [
    SELECT ConversionRate FROM DatedConversionRate
    WHERE IsoCode = :opp.CurrencyIsoCode
      AND StartDate <= :opp.CloseDate
      AND (NextStartDate > :opp.CloseDate OR NextStartDate = NULL)
    LIMIT 1
];
```

Then apply `r.ConversionRate` manually to the non-eligible field.

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
| Financial-period audit on Opportunity `Amount` (ACM on) | Yes | Under ACM, `convertCurrency()` on `Amount` uses the `CloseDate` dated rate and matches reports |
| Financial-period audit on a custom currency field | No (use `DatedConversionRate` explicitly) | Custom fields aren't ACM-eligible; `convertCurrency()` uses the static rate |
| Cross-currency aggregations in a controller | Yes for per-row conversion; note grouped aggregates return the org default currency | Wrapping an aggregate in `convertCurrency()` isn't allowed |
| Filtering by a currency threshold | No (`convertCurrency()` is banned in `WHERE`) | Use an ISO-code literal such as `Amount > USD5000` |

---

## Example 7 — Filtering by a currency threshold (`convertCurrency()` is banned in `WHERE`)

**Context.** A controller needs opportunities worth more than 5,000
US dollars, across mixed-currency records.

**The bug.**

```apex
// Throws an error — convertCurrency() is not allowed in WHERE
SELECT Id FROM Opportunity WHERE convertCurrency(Amount) > 5000
```

**Right answer.** `convertCurrency()` is only valid in `SELECT`. To
filter by a value in a stated currency, use an ISO-code-qualified
literal — the ISO code immediately followed by the number, no space:

```apex
SELECT Id, convertCurrency(Amount) FROM Opportunity WHERE Amount > USD5000
```

The literal denominates the threshold in US dollars and the platform
handles the cross-currency comparison. `convertCurrency()` still
belongs in the `SELECT` list if you also want the converted amount
back. If you genuinely need "converted value above X", fetch the
converted alias and filter in Apex.

---

## Example 8 — Grouped aggregates return the corporate currency, not the user's

**Context.** A dashboard controller sums opportunity Amount by owner:

```apex
SELECT OwnerId, SUM(Amount) total
FROM Opportunity
GROUP BY OwnerId
```

**Behavior.** With a `GROUP BY` (or `HAVING`) clause, the currency
value returned by `SUM()` (or `MAX()`, etc.) is in the org's default
(corporate) currency — not the running user's currency, and not
something you can redirect with `convertCurrency()`. You also can't
wrap the aggregate in `convertCurrency()`, and you can't compare an
aggregated currency value against an ISO-code literal.

**Right answer.** Treat grouped aggregate currency results as
corporate-currency figures and label them as such in the UI. If
per-user-currency totals are required, select `convertCurrency(Amount)`
per row and aggregate in Apex.

---

## Example 9 — Locale-formatted converted currency with `FORMAT()`

**Context.** A Lightning controller returns a converted amount already
formatted for the user's locale, avoiding client-side formatting.

```apex
SELECT Amount, FORMAT(convertCurrency(Amount)) convertedCurrency
FROM Opportunity WHERE Id = :oppId
```

**Behavior.** `FORMAT()` wraps `convertCurrency()` to render the
converted value as a locale-appropriate currency string (grouping
separators, symbol, decimal places per the user's locale). The aliased
field (`convertedCurrency`) comes back as a formatted string, so
downstream code must treat it as text, not a number.

---

## Example 10 — Querying currency on a Data Cloud DLO/DMO

**Context.** A SOQL query runs against a Data Cloud data model object
(DMO) that carries a currency field.

**The trap.** Data Cloud objects don't behave like standard sObjects
for currency:

```apex
// Fails — toLabel(CurrencyIsoCode) needs an alias in SELECT
SELECT toLabel(CurrencyIsoCode), Currency__c FROM <DMO>
```

**Right answer.**

```apex
SELECT toLabel(CurrencyIsoCode) CurrencyCodeAlias, Currency__c FROM <DMO>
```

- The alias on `toLabel(CurrencyIsoCode)` is mandatory in `SELECT`
  (not in `WHERE` / `ORDER BY`).
- To read the raw ISO code of a Data Cloud record, use the
  `cdp_sys_record_currency__c` system field rather than
  `CurrencyIsoCode`.
- If every currency field comes back null, the record's ISO code is
  unsupported or invalid — check the org's Manage Multiple Currencies
  setup.
- `convertCurrency()` on a Data Cloud currency field does not round to
  the org's configured decimal places, so round in the consuming layer
  if presentation precision matters.
