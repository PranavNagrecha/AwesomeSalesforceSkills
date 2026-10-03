---
name: multi-currency-and-advanced-currency-management
description: "Use when designing or reviewing Salesforce multi-currency behavior, especially irreversible activation, `CurrencyIsoCode`, `convertCurrency()`, dated exchange rates, and Advanced Currency Management tradeoffs. Triggers: 'multi currency', 'advanced currency management', 'CurrencyIsoCode', 'dated exchange rate', 'convertCurrency', 'enable multiple currencies', 'load daily exchange rates'. NOT for what convertCurrency() allows in WHERE/ORDER BY or querying CurrencyType and DatedConversionRate — use data/currency-management-patterns. NOT for wrong converted amounts in Sales Cloud reports and roll-ups — use architect/multi-currency-sales-architecture."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
tags:
  - multi-currency
  - advanced-currency-management
  - currencyisocode
  - convertcurrency
  - dated-exchange-rates
triggers:
  - "should we enable multi currency in Salesforce"
  - "advanced currency management and dated exchange rates"
  - "CurrencyIsoCode handling in Apex"
  - "convertCurrency in SOQL"
  - "roll up summary and ACM currency issues"
  - "advanced currency management vs standard multi-currency for Sales Cloud"
  - "standard multi-currency versus advanced currency management comparison"
  - "enable multiple currencies in our org and what breaks afterwards"
  - "load daily exchange rates into Salesforce from our finance system"
inputs:
  - "whether multi-currency or ACM is already enabled"
  - "objects and reports involved"
  - "query, rollup, or Apex behavior that must respect currency context"
outputs:
  - "currency architecture recommendation"
  - "review findings for conversion and reporting risks"
  - "query and Apex guidance for currency-aware behavior"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# Multi Currency And Advanced Currency Management

Use this skill when currency is no longer just a formatting concern. Multi-currency and Advanced Currency Management (ACM) change how data is stored, queried, reported, and explained to the business. The design rule: keep every amount next to its currency, and convert only where the consumer asked for a converted value.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is multi-currency already enabled? `CurrencySettings.enableMultiCurrency` cannot be set back to `false` once it is `true`.
- Is ACM (effective dated currency) enabled or planned? It requires multi-currency first.
- Which consumers read money: Opportunity reports, forecasts, roll-ups, Apex, integrations, CRM Analytics?
- Does each consumer need the stored transaction currency, the viewer's currency, or a dated historical conversion?
- Does any Apex or managed package code have to run in both single-currency and multi-currency orgs?

---

## Questions to Ask Before Configuring

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Have the sponsors signed off that turning on multiple currencies is permanent?" | The Metadata API says `enableMultiCurrency` "can't be set to false" after it is set to true | A recorded decision and a full sandbox rehearsal before production | No surprise one-way change to every record's data model |
| "Which amounts need historical rates, and on which objects?" | The SOQL guide says ACM dated rates apply to opportunities, opportunity line items, and opportunity history; other currency fields use the static rate | A list of reports that will change meaning under ACM, and those that will not | Finance knows which numbers are dated and which are not |
| "Who loads exchange rates, how often, and through which API?" | `CurrencyType` and `DatedConversionRate` do not support Apex DML; rates come in through the API or Setup | A named owner and an API-only job for rate loads | Rates that stay current without a manual Setup task |
| "Do integrations send the ISO code with every amount?" | `CurrencyIsoCode` exists only in multi-currency orgs and the stored amount is in that currency | A payload contract of amount plus ISO code | Downstream systems stop guessing the currency |
| "Do any queries total money with GROUP BY?" | Aggregates with GROUP BY or HAVING return the org's default currency, and `convertCurrency()` cannot wrap them | Reports or code that label totals as corporate currency | Totals that match what users expect to see |
| "Does code need to run in single-currency orgs too?" | Static SOQL naming `CurrencyIsoCode` or `CurrencyType` assumes multi-currency | A `UserInfo.isMultiCurrencyOrganization()` guard and dynamic SOQL | Packages and shared code that install in any org |

What a proper configuration adds over just ticking the box: the irreversible switch is rehearsed, every amount travels with its ISO code, the team knows exactly which reports use dated rates, and rate loads are an owned, automated job.

---

## Core Concepts

### Enabling multi-currency is one-way

`CurrencySettings` (Metadata API, `Currency.settings`) holds `enableMultiCurrency`, `enableCurrencyEffectiveDates`, `enableCurrencySymbolWithMultiCurrency`, and `isParenCurrencyConvDisabled`. After `enableMultiCurrency` is true it cannot be set to false. `enableCurrencyEffectiveDates` (ACM) requires `enableMultiCurrency`.

### Where currency lives

| Object or field | What it holds | Writable how |
|---|---|---|
| `CurrencyIsoCode` on records | The record's currency; available only in multi-currency orgs | Normal DML |
| `CurrencyType` | One row per currency: `IsoCode`, `ConversionRate` against the corporate currency, `DecimalPlaces`, `IsActive`, `IsCorporate` | API `create()` and `update()`; no Apex DML; cannot be deleted |
| `DatedConversionRate` | Rate per currency per date range: `IsoCode`, `ConversionRate`, `StartDate`, read-only `NextStartDate` | API `update()` and `delete()` listed in the Object Reference; no Apex DML; exists only with ACM |

When updating a `CurrencyType` record, send every field. The Object Reference warns that a missing `IsActive` defaults to false and can deactivate an active currency.

### `convertCurrency()` rules

- It converts a currency field to the running user's currency in the SELECT clause.
- It cannot be used in WHERE. Compare against an ISO-prefixed literal instead: `WHERE Amount > USD5000`. Without the prefix, the raw number is compared across currencies.
- It cannot be used with ORDER BY. Ordering already uses the converted value.
- It cannot convert aggregate results. With GROUP BY or HAVING, aggregates return the org's default currency.
- With ACM, conversion on opportunities, opportunity line items, and opportunity history uses the rate for the field's date (for example `CloseDate`). Otherwise the most recent rate is used.

### ACM scope

ACM adds a time dimension only where the SOQL guide says dated rates apply. Everything else keeps converting at the static `CurrencyType` rate. UNVERIFIED (2026-10-03): the help-only statements about ACM and roll-up summary fields on Account; help.salesforce.com does not return article text to a fetch, so test roll-ups in a sandbox before enabling ACM.

---

## Common Patterns

### Currency-aware query

Query `CurrencyIsoCode` with every amount you expose. Use `convertCurrency()` only when the requirement is the viewer's currency. Example with a test class in `references/examples.md`.

### Code that runs in any org

Guard with `UserInfo.isMultiCurrencyOrganization()` and build the field list dynamically. `UserInfo.getDefaultCurrency()` returns the user's currency in a multi-currency org and the org currency in a single-currency org.

### Rate loads from finance

An API-only integration user updates `CurrencyType` (static rates) or `DatedConversionRate` (ACM rates) on a schedule. Apex cannot do this with DML.

### Integration DTO with currency context

Send amount and ISO code together. Never send a bare decimal.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Org needs multiple transactional currencies | Multi-currency, after a rehearsal | One-way switch |
| Historical opportunity reporting needs period rates | ACM | Dated rates apply to opportunity, line item, and history amounts |
| Historical rates needed on a custom object | Store the rate or converted amount on the record | Dated rates do not apply outside the opportunity family |
| Apex exposes money values externally | Include `CurrencyIsoCode` with the amount | Prevents silent interpretation errors |
| Filter by amount across currencies | ISO-prefixed literal in WHERE | `convertCurrency()` is not allowed in WHERE |
| Total money in SOQL | Label the result as corporate currency | Aggregates return the org default currency |
| Change exchange rates from Apex | Do not; use the API from an integration | No DML on `CurrencyType` or `DatedConversionRate` |

---

## Recommended Workflow

1. **Inventory currency consumers.** List reports, forecasts, roll-ups, Apex, integrations, and analytics that read money.
2. **Decide the switch.** If multi-currency is not enabled, run it in a full sandbox, review the inventory, and record sign-off that it is permanent.
3. **Scope ACM.** Mark which consumers use opportunity-family amounts (dated) and which use static rates.
4. **Fix the code.** Add `CurrencyIsoCode` next to amounts, remove `convertCurrency()` from WHERE and ORDER BY, guard shared code with `isMultiCurrencyOrganization()`, and run `python3 scripts/check_multi_currency_and_advanced_currency_management.py --manifest-dir force-app`.
5. **Automate rate loads.** Build the API job that updates `CurrencyType` or `DatedConversionRate`, sending all fields on `CurrencyType` updates.
6. **Deploy settings and verify.** Deploy `Currency.settings` from `references/metadata-examples.md` and check converted amounts in a report and in SOQL for a known record.

---

## Review Checklist

- [ ] Sign-off on the one-way switch is recorded
- [ ] Apex and integrations carry `CurrencyIsoCode` with every amount
- [ ] No `convertCurrency()` in WHERE or ORDER BY
- [ ] Aggregated money is labeled as corporate currency
- [ ] Shared code is guarded with `UserInfo.isMultiCurrencyOrganization()`
- [ ] No Apex DML on `CurrencyType` or `DatedConversionRate`
- [ ] `CurrencyType` updates send every field, including `IsActive`
- [ ] Reports that change meaning under ACM are documented

---

## Salesforce-Specific Gotchas

See `references/gotchas.md`. The two that cause the most rework: a `CurrencyType` update that omits `IsActive` deactivates the currency, and aggregates return the corporate currency no matter who runs the query.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Currency design review | Findings on activation, conversion, reporting, and Apex handling |
| Query guidance | Stored-currency versus converted-currency retrieval per consumer |
| ACM decision | Which amounts get dated rates and which do not |
| `Currency.settings` and rate-load job | Deployable settings and the API job for rates |

---

## Related Skills

- `data/currency-management-patterns`: what `convertCurrency()` allows in WHERE and ORDER BY, and querying `CurrencyType` and `DatedConversionRate`
- `architect/multi-currency-sales-architecture`: wrong converted amounts in Sales Cloud reports and roll-ups
- `data/roll-up-summary-alternatives`: when parent totals and roll-ups become the main implementation issue
- `apex/custom-metadata-in-apex`: when exchange-rate or currency-routing config belongs in metadata-driven logic
- `integration/oauth-flows-and-connected-apps`: when the blocker is external finance-system authentication
