# Gotchas — Currency Management Patterns

Multi-currency platform behaviors that cause real production bugs.

---

## Gotcha 1: Enabling multi-currency is irreversible

**What happens.** Setup -> Company Information -> Enable Multiple
Currencies. Once saved, the `CurrencyIsoCode` field appears on every
currency-aware object and cannot be removed. Salesforce does not
provide a "disable multi-currency" path.

**When it occurs.** A mid-implementation switch to multi-currency,
later regretted because of complexity or reporting overhead.

**How to avoid.** Treat enable-multi-currency as a permanent
architectural decision. Pilot in a sandbox first with a real volume
of records and reports to validate the impact.

---

## Gotcha 2: `convertCurrency()`'s rate depends on ACM and the field

**What happens.** Whether `SELECT convertCurrency(Amount) FROM
Opportunity` uses a dated or a static rate depends on two things.
Without ACM it uses the current `CurrencyType.ConversionRate` (the
most recent conversion date entered). With ACM it uses the dated rate
tied to the field's date — `CloseDate` on opportunities — for the
ACM-eligible standard fields (opportunities, opportunity line items,
opportunity history), so it matches the standard report. For fields
that are *not* ACM-eligible (custom currency fields, formula fields,
roll-up summaries), it always uses the static rate even under ACM.

**When it occurs.** The two failure modes are opposite: assuming
`convertCurrency()` never honors dated rates — and hand-rolling a
`DatedConversionRate` lookup for Opportunity `Amount` that isn't
needed — or assuming it honors dated rates for a custom currency
field, which it doesn't.

**How to avoid.** For ACM-eligible standard fields, trust
`convertCurrency()` to match reports. For an as-of-date value on a
non-eligible field, or when ACM is off, query `DatedConversionRate`
explicitly.

---

## Gotcha 3: ACM does not apply to formula fields, custom currency fields, or roll-up summaries

**What happens.** ACM is enabled. A custom currency field on
Opportunity is expected to use the dated rate when displayed in a
report. It does not.

**When it occurs.** Any custom currency field, formula field
returning a currency, or roll-up summary on a currency. ACM's dated-
rate scope is restricted to a defined list of standard fields
(notably Opportunity Amount, OpportunityLineItem TotalPrice, and
related history / forecast tables).

**How to avoid.** Read the official ACM coverage list. Anything
outside it uses the static rate. If dated rates are required for a
custom field, the calculation must happen in Apex.

---

## Gotcha 4: Roll-up summary across mixed-currency children uses static rates

**What happens.** Account roll-up `SUM(Opportunity.Amount)` produces
a number in the parent's currency, internally converting each child
using `CurrencyType.ConversionRate` regardless of ACM. The same
report on the same data produces a different number.

**When it occurs.** Mixed-currency children rolled up to a parent.

**How to avoid.** Either constrain children to share the parent's
currency, or replace the roll-up summary with an Apex calculation
that uses dated rates explicitly.

---

## Gotcha 5: `CurrencyIsoCode` on a child is independent of the parent

**What happens.** Inserting an Opportunity under an Account does not
inherit the Account's currency. The Opportunity gets the running
user's default currency unless explicitly set.

**When it occurs.** Apex / Flow / API inserts that omit
`CurrencyIsoCode`. Standard UI defaults to the user's currency.

**How to avoid.** Set `CurrencyIsoCode` explicitly when inserting
related records via API. Validation rules can enforce parent-child
currency consistency where required.

---

## Gotcha 6: Deactivated currencies remain on existing records

**What happens.** An admin deactivates a currency. Records with that
`CurrencyIsoCode` remain valid; reports filter on the deactivated
currency still return them; their `CurrencyType` record is
`IsActive = false` but exists.

**When it occurs.** Cleanup or rationalization of unused currencies.

**How to avoid.** Audit existing records before deactivating a
currency. Convert or delete affected records first, or accept that
the currency continues to appear in historical reporting.

---

## Gotcha 7: SOQL filters on currency fields use the record's native value

**What happens.** `WHERE Amount > 100000` filters on the raw native
value, not the corporate-currency-converted value. An EUR
Opportunity with `Amount = 90000` (EUR) does not match, even though
its USD-equivalent is over 100K.

**When it occurs.** Filters expressed in "amount above X" without
specifying which currency X is in.

**How to avoid.** `convertCurrency()` can't appear in a `WHERE`
clause. To filter by a value in a stated currency, use an
ISO-code-qualified literal — `WHERE Amount > USD5000` — or document
the filter as "native-currency >= X". If you need "converted value
above X", select `convertCurrency(Amount)` and filter in Apex.

---

## Gotcha 8: `DatedConversionRate.NextStartDate` is computed; do not set it

**What happens.** Code inserts a `DatedConversionRate` with a
`NextStartDate` value. The platform either rejects the insert or
overrides the value. Subsequent rates are misaligned.

**When it occurs.** Engineers porting a finance system's "valid
from / valid to" model directly to Salesforce.

**How to avoid.** Insert only `IsoCode`, `StartDate`,
`ConversionRate`. The platform computes `NextStartDate` based on the
adjacent row. Insert in any order — the recomputation runs on commit.

---

## Gotcha 9: User's display currency vs corporate currency

**What happens.** The Lightning UI shows amounts converted to the
running user's `DefaultCurrencyIsoCode`. Reports and dashboards show
amounts in the corporate currency. Different parts of the same UI
display different numbers for the same record.

**When it occurs.** Any user whose default currency is not the
corporate currency.

**How to avoid.** Document explicitly which currency each surface
displays. For executive dashboards, set the dashboard to display in
corporate currency to remove ambiguity.

---

## Gotcha 10: `convertCurrency()` is rejected in `WHERE` and `ORDER BY`

**What happens.** `convertCurrency()` is only valid in the `SELECT`
clause. Putting it in a `WHERE` clause returns an error. It also can't
be combined with `ORDER BY` — sorting on a currency field already runs
against the converted value, the same as reports.

**When it occurs.** Code that tries to filter or sort on a converted
amount, e.g. `WHERE convertCurrency(Amount) > 5000` or
`ORDER BY convertCurrency(Amount)`.

**How to avoid.** Filter with an ISO-code-qualified literal
(`WHERE Amount > USD5000`). To sort by converted value, `ORDER BY`
the field directly — the platform already sorts on the converted
value. Fall back to sorting in Apex only if you need a different order.

---

## Gotcha 11: Aggregates under `GROUP BY` / `HAVING` return the corporate currency

**What happens.** When a query includes a `GROUP BY` or `HAVING`
clause, currency data returned by an aggregate function such as
`SUM()` or `MAX()` comes back in the org's default (corporate)
currency — not the running user's currency. You can't wrap the
aggregate in `convertCurrency()`, and you can't compare an aggregated
currency value against an ISO-code literal.

**When it occurs.** Grouped dashboards and summary controllers that
present per-group currency totals to users whose currency isn't the
corporate currency.

**How to avoid.** Label aggregate results as corporate-currency
figures. For per-user-currency totals, select `convertCurrency(Amount)`
per row and aggregate in Apex.

---

## Gotcha 12: Data Cloud (DLO/DMO) currency queries follow different rules

**What happens.** SOQL against Data Cloud data lake / data model
objects diverges from standard sObjects: the ISO code lives in
`cdp_sys_record_currency__c` (not `CurrencyIsoCode`);
`toLabel(CurrencyIsoCode)` requires an alias in the `SELECT` clause
(but not in `WHERE` / `ORDER BY`); an all-null currency result means
the record's ISO code is unsupported or invalid; and
`convertCurrency()` on a Data Cloud currency field does not round to
the org's configured decimal places.

**When it occurs.** Reusing standard-sObject currency query patterns
against DLOs/DMOs, then hitting query errors, null values, or
unrounded amounts.

**How to avoid.** Use `cdp_sys_record_currency__c` for the ISO code,
alias `toLabel(CurrencyIsoCode)` in `SELECT`, verify unsupported ISO
codes against Manage Multiple Currencies when values come back null,
and round Data Cloud converted amounts in the consuming layer.
