# LLM Anti-Patterns — Multi-Currency and Advanced Currency Management

Common mistakes AI coding assistants make when generating or advising on Salesforce multi-currency and ACM.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Not Warning That Multi-Currency Enablement Is Irreversible

**What the LLM generates:** "Enable multi-currency in Setup to support international transactions" without prominently warning that enabling multi-currency is a permanent, irreversible change that cannot be undone.

**Why it happens:** Most Salesforce feature enablement is reversible or configurable. Multi-currency is one of the few irreversible changes, but LLMs treat it as a routine toggle because the setup steps are simple.

**Correct pattern:**

```text
CRITICAL: Enabling multi-currency is IRREVERSIBLE.

Before enabling:
1. Test in a full-copy sandbox first
2. Verify that ALL existing reports, dashboards, and roll-up summaries
   work correctly with the CurrencyIsoCode field added to all records
3. Confirm that all integrations can handle the CurrencyIsoCode field
4. Understand that every record will get a CurrencyIsoCode field
5. Roll-Up Summary fields will use the parent record's currency
6. Formula fields referencing currency fields may need updates

Once enabled, you cannot revert to a single-currency org.
```

**Detection hint:** Flag multi-currency enablement recommendations that do not include the word "irreversible" or "cannot be undone." Check for missing sandbox testing recommendation.

---

## Anti-Pattern 2: Confusing convertCurrency() Behavior in SOQL

**What the LLM generates:** `SELECT Name, convertCurrency(Amount) FROM Opportunity WHERE convertCurrency(Amount) > 1000000` — using `convertCurrency()` in both SELECT and WHERE clauses, or misunderstanding which currency the conversion targets.

**Why it happens:** `convertCurrency()` has specific rules: it converts to the running user's currency, can be used in SELECT or WHERE/HAVING (but with restrictions), and cannot be used in ORDER BY. LLMs generate it like a standard function without these constraints.

**Correct pattern:**

```text
convertCurrency() rules in SOQL:

- Converts currency fields to the running user's personal currency
- Can be used in: SELECT, WHERE, HAVING
- Cannot be used in: ORDER BY
- Cannot use with GROUP BY if using aggregate functions
- In WHERE clause, the comparison value is in the user's currency

Valid:
  SELECT Name, convertCurrency(Amount) FROM Opportunity
  WHERE convertCurrency(Amount) > 1000000

Invalid:
  SELECT Name FROM Opportunity ORDER BY convertCurrency(Amount)

In Apex, the running user is the context user (or system for async).
In reports, conversion uses the viewer's currency.

For API integrations, converted values use the integration user's currency,
which may not be the intended target currency.
```

**Detection hint:** Flag `convertCurrency()` in ORDER BY clauses. Check whether the code accounts for which user's currency the conversion targets.

---

## Anti-Pattern 3: Ignoring ACM Impact on Roll-Up Summary Fields

**What the LLM generates:** "Enable Advanced Currency Management for dated exchange rates" without mentioning that ACM changes how roll-up summary fields calculate currency conversions, potentially breaking existing reports and dashboard metrics.

**Why it happens:** ACM's impact on roll-up summaries is a subtle but significant behavior change. Training data covers the dated exchange rate concept but not the downstream effects on roll-up calculations.

**Correct pattern:**

```text
Advanced Currency Management (ACM) impact on roll-up summaries:

Without ACM:
- Roll-up summary converts child record amounts using the STATIC
  exchange rate (current rate at time of calculation)

With ACM enabled:
- Roll-up summary for Opportunity Amount uses the CloseDate to
  determine the dated exchange rate
- Other objects: dated rate based on the date field configured
  in the dated exchange rate settings
- If no dated rate exists for the record's date, the static rate is used

Potential breaking changes:
1. Historical roll-up values will recalculate with dated rates
2. Report totals may change retroactively
3. Forecast amounts may shift
4. Validate all currency-based reports in sandbox before enabling ACM
```

**Detection hint:** Flag ACM enablement recommendations that do not mention roll-up summary recalculation or report impact. Look for missing sandbox validation steps.

---

## Anti-Pattern 4: Hard-Coding Currency ISO Codes in Apex

**What the LLM generates:** Apex code with hard-coded currency strings like `record.CurrencyIsoCode = 'USD'` without validating that the currency is active in the org or using a configurable approach.

**Why it happens:** LLMs generate literal string values for currency codes because that is what appears in training examples. The fact that orgs must explicitly activate each currency and that inactive currencies cause DML failures is not widely covered.

**Correct pattern:**

```text
Currency handling in Apex:

// Query active currencies instead of hard-coding:
List<CurrencyType> activeCurrencies = [
    SELECT IsoCode, ConversionRate, DecimalPlaces
    FROM CurrencyType
    WHERE IsActive = true
];
Set<String> validCodes = new Set<String>();
for (CurrencyType ct : activeCurrencies) {
    validCodes.add(ct.IsoCode);
}

// Validate before assignment:
if (validCodes.contains(incomingCurrencyCode)) {
    record.CurrencyIsoCode = incomingCurrencyCode;
} else {
    // Handle: default to org currency or raise error
}

// For integrations, store default currency in Custom Metadata:
Currency_Config__mdt config = Currency_Config__mdt.getInstance('Default');
```

**Detection hint:** Flag hard-coded currency ISO codes (`'USD'`, `'EUR'`, `'GBP'`) in Apex code. Look for CurrencyIsoCode assignments without validation against CurrencyType.

---

## Anti-Pattern 5: Assuming All Currency Fields Automatically Convert

**What the LLM generates:** "All currency fields in Salesforce automatically convert to the user's currency in multi-currency orgs" without noting that custom currency fields display in the record's CurrencyIsoCode by default, and that conversion happens only in reports, list views (with conversion column), and `convertCurrency()` in SOQL.

**Why it happens:** The multi-currency documentation emphasizes automatic conversion, but the nuance of where conversion happens (reports, specific UI contexts) vs where it does not (record detail page by default, API responses) is underrepresented.

**Correct pattern:**

```text
Where currency conversion happens automatically:
- Reports: converted to the running user's currency
- List views: with "Converted" column enabled
- SOQL: using convertCurrency() function
- Forecasts: converted to the forecast currency

Where currency is displayed in the RECORD's currency (no auto-conversion):
- Record detail page (standard and Lightning)
- API responses (REST, SOAP): return the record's CurrencyIsoCode amount
- Apex: record.Amount returns the value in record.CurrencyIsoCode
- Data exports: values in the record's currency

For API integrations that need converted values:
- Use convertCurrency() in SOQL queries
- Or convert programmatically using CurrencyType.ConversionRate
```

**Detection hint:** Flag claims that "all currency fields auto-convert everywhere" without distinguishing between reporting, UI, and API contexts.
