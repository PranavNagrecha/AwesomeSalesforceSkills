# Metadata and REST Examples: Multi Currency And Advanced Currency Management

## Example A: Deploy currency settings from source control

**Context:** The org has passed its sandbox rehearsal and sign-off. The team wants the switch and display options in source control instead of a Setup click.

**File:** `force-app/main/default/settings/Currency.settings-meta.xml` (Metadata API: `CurrencySettings`, stored in `Currency.settings` in the `settings` directory)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CurrencySettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableCurrencyEffectiveDates>false</enableCurrencyEffectiveDates>
    <enableCurrencySymbolWithMultiCurrency>true</enableCurrencySymbolWithMultiCurrency>
    <enableMultiCurrency>true</enableMultiCurrency>
    <isParenCurrencyConvDisabled>false</isParenCurrencyConvDisabled>
</CurrencySettings>
```

package.xml member form (all org settings use the `Settings` type name):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Currency</members>
        <name>Settings</name>
    </types>
    <version>67.0</version>
</Package>
```

**Why it works:** Element names and the `Settings`/`Currency` member come from the Metadata API Developer Guide (262), "CurrencySettings." `enableMultiCurrency` cannot be set back to false once deployed as true, so this file is the last step of the rehearsal, not the first. Turn `enableCurrencyEffectiveDates` on in a later release once the ACM report review is done; it requires `enableMultiCurrency`. `isMultiCurrencyActivationAllowed` is deprecated in API 49.0 and later and is left out.

---

## Example B: Update a static exchange rate from a finance system

**Context:** A nightly job updates the EUR static rate. Apex cannot do this because `CurrencyType` does not support DML.

```http
PATCH /services/data/v67.0/sobjects/CurrencyType/01Lxx0000004AbCEAU
Content-Type: application/json
Authorization: Bearer [REDACTED]

{
  "IsoCode": "EUR",
  "ConversionRate": 0.912345,
  "DecimalPlaces": 2,
  "IsActive": true
}
```

**Why it works:** The Object Reference (262) lists `update()` for `CurrencyType` and warns that a missing `IsActive` defaults to false. Sending every editable field keeps the currency active. `IsCorporate` is left out because the corporate currency is not being changed here. UNVERIFIED (2026-10-03): whether an omitted `IsCorporate` on a non-corporate row is left unchanged; send it explicitly if your job may touch the corporate row. For ACM rates, the job updates `DatedConversionRate`; the Object Reference lists `update()` and `delete()` for it but does not list `create()`, so confirm in a sandbox how your org adds new date ranges (Setup or API). UNVERIFIED (2026-10-03).
