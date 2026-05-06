---
name: currency-management-patterns
description: "Working with multi-currency Salesforce orgs at the data layer — `CurrencyIsoCode` field semantics on every object, the `CurrencyType` and `DatedConversionRate` standard objects, the `convertCurrency()` SOQL function, Advanced Currency Management vs basic multi-currency, formula fields with currency conversion, roll-up summaries across currencies, and the irreversibility of enabling multi-currency on an org. NOT for currency UI formatting in LWC (that's Lightning's `lightning-formatted-number`), NOT for tax / financial-doc rounding rules (those are app-layer concerns)."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "multi-currency org currencyisocode field salesforce"
  - "datedconversionrate currencytype standard object"
  - "soql convertcurrency function corporate currency"
  - "advanced currency management acm dated exchange rates"
  - "formula field currency conversion gotcha"
  - "roll-up summary across currencies opportunities"
  - "enable multi currency irreversible salesforce"
tags:
  - multi-currency
  - currency-iso-code
  - dated-conversion-rate
  - acm
  - convert-currency
inputs:
  - "Whether multi-currency is already enabled on the org (irreversible decision)"
  - "Whether Advanced Currency Management (dated exchange rates) is enabled"
  - "Source-of-truth for exchange rates (manual maintenance vs integration)"
outputs:
  - "Pattern for SOQL queries that need currency conversion (`convertCurrency()` usage)"
  - "Formula-field design that survives multi-currency without producing nonsense values"
  - "Roll-up / report design that respects corporate vs record currency"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-05
---

# Currency Management Patterns

Multi-currency in Salesforce is one of the most subtle data-layer
features in the platform. Once enabled it cannot be disabled. Every
record on every currency-aware object carries a `CurrencyIsoCode`
field. Reports, formulas, roll-ups, and SOQL all change semantics.

This skill covers the data-layer behavior that surprises practitioners:
how `CurrencyIsoCode` interacts with formula fields, when the
`DatedConversionRate` table is consulted versus the static
`CurrencyType.ConversionRate`, what `convertCurrency()` in SOQL
actually does, and the patterns for getting roll-up summaries to
behave when child records carry different currencies than the parent.

## The two tiers: basic multi-currency vs Advanced Currency Management

**Basic multi-currency.** Enabled in Setup -> Company Information ->
Currency. Every currency-aware standard object gains a
`CurrencyIsoCode` picklist; the org gains the `CurrencyType` table
with one static conversion rate per active currency. Conversions
always use the current `ConversionRate`, even on a record dated three
years ago.

**Advanced Currency Management (ACM).** Enabled separately. Adds the
`DatedConversionRate` standard object — exchange rates with a
`StartDate`. ACM applies dated rates to a defined subset of fields,
notably Opportunity Amount, OpportunityLineItem TotalPrice, and a
small number of related history / forecast tables. ACM does **not**
apply dated rates to formula fields, custom currency fields, or
roll-up summaries — those continue to use the static
`CurrencyType.ConversionRate`. This split is the single biggest
source of multi-currency bugs.

## Corporate currency vs record currency

The org has one Corporate Currency (set in `CurrencyType` where
`IsCorporate = true`). Reports and the Lightning UI typically display
amounts converted to corporate currency. SOQL by default returns the
record's native currency value — without `convertCurrency()`, you get
the raw number stamped against `CurrencyIsoCode`.

```apex
// Returns Opportunity.Amount in the record's native currency
SELECT Amount, CurrencyIsoCode FROM Opportunity

// Returns Opportunity.Amount converted to running user's currency
SELECT convertCurrency(Amount), CurrencyIsoCode FROM Opportunity
```

`convertCurrency()` uses the static `CurrencyType.ConversionRate` — it
does **not** consult `DatedConversionRate`, even when ACM is enabled.
Reports built against the same field can produce different numbers
than the SOQL-converted value because reports do consult dated rates
for the eligible standard fields.

## Recommended Workflow

1. **Confirm multi-currency status.** Setup -> Company Information shows whether multi-currency is enabled. If it is enabled, `CurrencyIsoCode` is on every currency-aware object. If considering enabling: it is irreversible. Plan accordingly.
2. **Confirm ACM status.** Advanced Currency Management is a separate switch and only adds dated rates for a specific subset of fields. Enumerate which fields are in scope from the official ACM coverage list before designing.
3. **Audit formula fields that mix currencies.** A formula like `Amount + Discount__c` where the two fields are in different currencies produces a meaningless number. The platform does not auto-convert. Either constrain both fields to the same currency, use a single-currency parent record, or compute the conversion explicitly.
4. **Design SOQL queries with `convertCurrency()` deliberately.** When the calling code needs corporate-currency totals, use `convertCurrency()`. When it needs the record's native currency for display alongside its currency code, do not use it.
5. **Validate roll-up summaries cross-currency.** A roll-up sum on Account.Total_Open_Amount across child Opportunities in different currencies will sum the raw numeric values — meaningless if children are in mixed currencies. Either constrain children to the parent's currency or compute the sum in Apex with explicit conversion.
6. **Set up the exchange-rate update process.** `CurrencyType` and `DatedConversionRate` need refreshing. Manual via Setup is the default; for production, integrate against an exchange-rate provider via scheduled Apex.
7. **Document the rate-source for auditors.** Financial reporting auditors will ask which exchange rate was applied to which record on which date. ACM records this implicitly via `DatedConversionRate`; basic multi-currency does not, so document the rate source and update cadence.

## What This Skill Does Not Cover

| Topic | See instead |
|---|---|
| LWC currency display formatting | `lwc/lwc-base-components-formatted` |
| Tax / financial-doc rounding rules | App-layer (CPQ, Revenue Cloud, custom Apex) |
| Initial enable / disable of multi-currency | `admin/multi-currency-enablement` |
| Forecasting and currency | `admin/forecasting-configuration` |
