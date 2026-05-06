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

## Gotcha 2: `convertCurrency()` ignores `DatedConversionRate`

**What happens.** SOQL `SELECT convertCurrency(Amount) FROM
Opportunity` returns values converted at the static
`CurrencyType.ConversionRate`, even when ACM is enabled. The same
field viewed in a standard report uses the dated rate. Apex output
and report output diverge.

**When it occurs.** Any Apex / SOQL that expects "the same value the
report shows" while ACM is enabled.

**How to avoid.** Explicitly query `DatedConversionRate` when you
need the historical-as-of rate. Document for callers that
`convertCurrency()` is the static-rate path.

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

**How to avoid.** Either compare in a uniform currency (use
`convertCurrency()` in the SELECT and filter on the converted alias
where supported) or document the filter as "native-currency >= X".

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
