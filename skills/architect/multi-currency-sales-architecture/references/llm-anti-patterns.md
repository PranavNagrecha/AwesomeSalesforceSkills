# LLM Anti-Patterns — Multi-Currency Sales Architecture

Common mistakes AI coding assistants make when generating or advising on multi-currency architecture in Salesforce Sales Cloud.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Suggesting ACM Can Be Disabled

**What the LLM generates:** "If advanced currency management doesn't work for your use case, you can always disable it later and revert to standard multi-currency."

**Why it happens:** LLMs generalize from other Salesforce features that can be toggled on and off (e.g., Person Accounts prior to recent changes, various settings). ACM's irreversibility is a specific platform constraint that is underrepresented in training data.

**Correct pattern:**

```
Advanced currency management CANNOT be disabled once enabled.
Treat ACM enablement as a permanent, irreversible architecture decision.
Test in a full-copy sandbox and get stakeholder sign-off before enabling in production.
```

**Detection hint:** Look for words like "disable ACM", "turn off advanced currency", "revert to standard multi-currency", or "roll back ACM".

---

## Anti-Pattern 2: Assuming Custom Objects Use Dated Exchange Rates

**What the LLM generates:** "With ACM enabled, all currency fields across standard and custom objects will automatically use the dated exchange rate based on the record's date field."

**Why it happens:** LLMs assume ACM is a global toggle that applies uniformly. In reality, only specific standard objects (Opportunity, OpportunityLineItem, and a few others) support dated rates. Custom objects always use the static CurrencyType rate.

**Correct pattern:**

```
With ACM enabled, only supported standard objects use dated exchange rates.
Custom objects always use the static CurrencyType rate.
To get dated-rate conversion on custom objects, query DatedConversionRate
in Apex and compute the conversion manually.
```

**Detection hint:** Look for claims that "all objects" or "custom objects" use dated rates, or that ACM applies "org-wide" to currency conversion.

---

## Anti-Pattern 3: Treating ConvertedAmount and Amount as Interchangeable

**What the LLM generates:** "You can use either Amount or ConvertedAmount in your SOQL query — they represent the same value."

**Why it happens:** LLMs conflate the two fields because they both appear on the same object and both hold monetary values. The critical distinction — that Amount is in the record's currency while ConvertedAmount is in the querying user's or corporate currency — is nuanced.

**Correct pattern:**

```
Amount stores the value in the record's CurrencyIsoCode.
ConvertedAmount stores the value converted to the running user's personal currency.
In API/Apex contexts without a running user, ConvertedAmount uses the corporate currency.
With ACM, ConvertedAmount on supported objects uses dated rates.
Always use Amount for the canonical value; use ConvertedAmount only for display/reporting.
```

**Detection hint:** Look for SOQL queries or logic that treats `Amount` and `ConvertedAmount` as equivalent, or that uses `ConvertedAmount` for currency-aware arithmetic without understanding which rate produced it.

---

## Anti-Pattern 4: Recommending Roll-Up Summaries for Financial Totals Under ACM

**What the LLM generates:** "Create a roll-up summary field on Account to sum the Amount from child Opportunities. This will automatically convert to the Account's currency."

**Why it happens:** Roll-up summary fields are the standard declarative answer for parent-child aggregation, and LLMs default to the simplest declarative approach. The nuance that roll-ups always use the static rate (not dated rates) even under ACM is rarely surfaced in training data.

**Correct pattern:**

```
Roll-up summary fields always use the static CurrencyType rate for conversion,
even when ACM is enabled. For accurate financial totals under ACM:
- Use Apex triggers or Flow to aggregate ConvertedAmount from child records
- Or query child records' ConvertedAmount (which uses dated rates) and sum in code
- Store the result in a custom currency field on the parent
```

**Detection hint:** Look for recommendations to use "roll-up summary" or "ROLLUP" for aggregating currency fields when ACM is mentioned or implied in the conversation context.

---

## Anti-Pattern 5: Ignoring Report Currency Display Rules

**What the LLM generates:** "The report will show all converted amounts in the corporate currency by default."

**Why it happens:** LLMs assume a single consistent currency display behavior. In reality, Salesforce reports show converted amounts in the running user's personal currency, not the corporate currency, unless explicitly overridden.

**Correct pattern:**

```
Reports display converted amounts in the RUNNING USER's personal currency by default.
To display in corporate currency, use Report Builder > Show > Currencies
and select the corporate currency explicitly.
For dashboards, set the running user to a service account
whose personal currency matches the desired display currency.
Two users running the same report will see different converted values
unless the report's currency display is explicitly overridden.
```

**Detection hint:** Look for claims that reports "default to corporate currency" or that "all users see the same converted amounts" without mentioning explicit currency override settings.

---

## Anti-Pattern 6: Hardcoding Exchange Rates in Apex

**What the LLM generates:** Code that includes a hardcoded exchange rate map or constant values like `Decimal eurToUsd = 1.08;` for currency conversion.

**Why it happens:** LLMs trained on general-purpose code default to simple constant-based conversion. They do not know to query `CurrencyType` or `DatedConversionRate` for Salesforce-managed rates.

**Correct pattern:**

```apex
// Query the platform-managed rate instead of hardcoding
DatedConversionRate rate = [
    SELECT ConversionRate FROM DatedConversionRate
    WHERE IsoCode = :currencyCode
      AND StartDate <= :targetDate
    ORDER BY StartDate DESC
    LIMIT 1
];
Decimal convertedValue = originalAmount * rate.ConversionRate;
```

**Detection hint:** Look for hardcoded numeric exchange rates, static maps of currency-to-rate values, or any conversion logic that does not query `CurrencyType` or `DatedConversionRate`.
