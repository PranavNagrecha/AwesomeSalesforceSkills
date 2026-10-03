# Gotchas: Multi Currency And Advanced Currency Management

Non-obvious Salesforce platform behaviors that cause real production problems in this domain. Each one names the official source it rests on.

## Gotcha 1: Turning on multiple currencies is permanent

**What happens:** Teams enable multi-currency to "try it" and find there is no off switch.

**When it occurs:** When the setting is flipped in production, or deployed as `enableMultiCurrency` true in `Currency.settings`, before the consumers are reviewed.

**How to avoid:** Rehearse in a full sandbox, inventory reports, roll-ups, integrations, and Apex, and record sign-off before production.

**Source:** Metadata API Developer Guide (262), "CurrencySettings," `enableMultiCurrency`: "After set to true, this field can't be set to false."

---

## Gotcha 2: A partial CurrencyType update deactivates the currency

**What happens:** A rate-load job sends only `ConversionRate`. The currency becomes inactive and disappears from picklists.

**When it occurs:** On API updates to `CurrencyType` that omit `IsActive`.

**How to avoid:** Send every field on each update: `IsoCode`, `ConversionRate`, `DecimalPlaces`, `IsActive`, and `IsCorporate` as currently set.

**Source:** Object Reference (262), "CurrencyType," Usage: "if a value for IsActive is not provided, the default (false) is used, which could result in a currently active CurrencyType becoming inactive."

---

## Gotcha 3: Apex cannot write exchange rates

**What happens:** A trigger or scheduled class that inserts or updates `CurrencyType` or `DatedConversionRate` fails.

**When it occurs:** When a team tries to keep rate loads inside Salesforce code.

**How to avoid:** Load rates from an integration through the API, or in Setup. Apex can query both objects but not modify them.

**Source:** Apex Developer Guide (262), "sObjects That Don't Support DML Operations" (lists `CurrencyType` and `DatedConversionRate`).

---

## Gotcha 4: convertCurrency() is rejected in WHERE and ORDER BY

**What happens:** A query such as `WHERE convertCurrency(Amount) > 1000000` returns an error.

**When it occurs:** When the converted value is used to filter or sort.

**How to avoid:** Filter with an ISO-prefixed literal, for example `WHERE Amount > USD5000`, which compares against the equivalent amount in each record's currency. Drop `convertCurrency()` from ORDER BY; ordering already uses converted values.

**Source:** SOQL and SOSL Reference (262), "convertCurrency()," Considerations and Workarounds.

---

## Gotcha 5: A WHERE amount without an ISO prefix compares raw numbers

**What happens:** `WHERE Amount > 5000` returns JPY 5,001 and EUR 5,001 alongside USD 5,001.

**When it occurs:** When a filter written for a single-currency org runs in a multi-currency org.

**How to avoid:** Prefix the literal with an active ISO code. Do not mix ISO and non-ISO values in one IN list.

**Source:** SOQL and SOSL Reference (262), "convertCurrency()," Considerations and Workarounds.

---

## Gotcha 6: Aggregates come back in the corporate currency

**What happens:** `SUM(Amount)` with GROUP BY returns a total in the org's default currency, even for a user whose personal currency differs. `convertCurrency(SUM(Amount))` is not allowed.

**When it occurs:** In Apex rollups, dashboards fed by Apex, and integration summaries.

**How to avoid:** Label aggregated money as corporate currency, or convert per record before totaling. An ISO-prefixed literal is not allowed in HAVING with an aggregate either.

**Source:** SOQL and SOSL Reference (262), "convertCurrency()," Considerations and Workarounds.

---

## Gotcha 7: Dated rates apply only to the opportunity family

**What happens:** After ACM is enabled, opportunity reports use period rates but a custom `Invoice__c` amount still converts at today's static rate. Finance sees two conversions of "the same" money.

**When it occurs:** When ACM is expected to make every currency field historical.

**How to avoid:** Document which amounts are dated. For other objects, store the rate or converted amount on the record at transaction time.

**Source:** SOQL and SOSL Reference (262), "convertCurrency()": dated rates are used for opportunities, opportunity line items, and opportunity history; otherwise the most recent rate is used. Object Reference (262), "DatedConversionRate": the object has no field linking a rate to another object or date field.

---

## Gotcha 8: CurrencyIsoCode and CurrencyType do not exist in single-currency orgs

**What happens:** Shared code or a package that names `CurrencyIsoCode` or `CurrencyType` in static SOQL fails in orgs without multi-currency.

**When it occurs:** When code written in a multi-currency sandbox is installed in a single-currency org.

**How to avoid:** Check `UserInfo.isMultiCurrencyOrganization()` and build the query dynamically. Fall back to `UserInfo.getDefaultCurrency()`, which returns the org currency in a single-currency org.

**Source:** Object Reference (262): `CurrencyIsoCode` "Available only for orgs with the multicurrency feature enabled"; `CurrencyType` "is not available in single-currency organizations." Apex Reference Guide (262), `UserInfo.getDefaultCurrency()` and `isMultiCurrencyOrganization()`.

---

## Gotcha 9: Changing the corporate currency rebases every rate

**What happens:** Setting a different currency as corporate makes the system reconfigure all conversion rates against it.

**When it occurs:** During a reorganization or when a test org is set up with the wrong corporate currency.

**How to avoid:** Decide the corporate currency before loading rates. After a change, reload or verify every `ConversionRate`.

**Source:** Object Reference (262), "CurrencyType," `IsCorporate`.
