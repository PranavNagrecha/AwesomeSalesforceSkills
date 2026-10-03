# LLM Anti-Patterns: Multi-Currency and Advanced Currency Management

Common mistakes AI coding assistants make when advising on Salesforce multi-currency and ACM. These help the consuming agent self-check its own output.

## Anti-Pattern 1: Not warning that enabling multi-currency is permanent

**What the LLM generates:** "Enable multi-currency in Setup to support international transactions," with no warning.

**Why it happens:** Most feature settings can be turned off again, and the setup steps look routine.

**Correct pattern:**

```text
Enabling multiple currencies is permanent: CurrencySettings.enableMultiCurrency
cannot be set back to false (Metadata API Developer Guide, CurrencySettings).

Before enabling:
1. Rehearse in a full-copy sandbox.
2. Inventory reports, dashboards, roll-ups, Apex, and integrations that read money.
3. Confirm integrations can send and receive CurrencyIsoCode.
4. Record sponsor sign-off.
```

**Detection hint:** An enablement recommendation without the words "permanent," "irreversible," or "cannot be undone," or without a sandbox rehearsal.

---

## Anti-Pattern 2: Using convertCurrency() in WHERE or ORDER BY

**What the LLM generates:** `SELECT Name, convertCurrency(Amount) FROM Opportunity WHERE convertCurrency(Amount) > 1000000 ORDER BY convertCurrency(Amount)`

**Why it happens:** The model treats `convertCurrency()` like any scalar function. Version 1.0.0 of this skill made the same mistake and listed WHERE and HAVING as valid.

**Correct pattern:**

```text
Allowed: SELECT Id, convertCurrency(Amount) FROM Opportunity
Not allowed: convertCurrency() in WHERE (returns an error), in ORDER BY,
or around an aggregate such as SUM().

Filter across currencies with an ISO-prefixed literal:
  SELECT Id, Name FROM Opportunity WHERE Amount > USD5000
Aggregates with GROUP BY or HAVING return the org's default currency.
```

Source: SOQL and SOSL Reference (262), "convertCurrency()."

**Detection hint:** `convertCurrency(` after WHERE, ORDER BY, or HAVING, or wrapping SUM, MAX, MIN, or AVG.

---

## Anti-Pattern 3: Inventing ACM coverage for other objects

**What the LLM generates:** "With ACM, other objects use the dated rate based on the date field you configure in the dated exchange rate settings."

**Why it happens:** The model generalizes from opportunities and invents a configuration screen.

**Correct pattern:**

```text
Dated rates apply to opportunities, opportunity line items, and opportunity
history (SOQL and SOSL Reference, convertCurrency()). Other currency fields use
the static CurrencyType rate. DatedConversionRate has only IsoCode,
ConversionRate, StartDate, and NextStartDate; nothing ties it to another
object or date field.

For historical rates on other objects, store the rate or the converted
amount on the record when the transaction happens.
UNVERIFIED (2026-10-03): help-only statements about ACM and Account roll-up
summary fields; test roll-ups in a sandbox before enabling ACM.
```

**Detection hint:** Any claim that ACM can be pointed at a custom object or a chosen date field.

---

## Anti-Pattern 4: Hard-coding currency ISO codes in Apex

**What the LLM generates:** `record.CurrencyIsoCode = 'USD';` with no check that the currency is active.

**Why it happens:** Literal codes are what training examples show.

**Correct pattern:**

```text
Query active currencies (dynamic SOQL if the code must also run in
single-currency orgs) and validate before assignment:

  String soql = 'SELECT IsoCode FROM CurrencyType WHERE IsActive = true';
  Set<String> active = new Set<String>();
  for (SObject ct : Database.query(soql)) {
      active.add((String) ct.get('IsoCode'));
  }
  if (active.contains(incomingCode)) {
      record.put('CurrencyIsoCode', incomingCode);
  }

Keep any default currency for an integration in custom metadata, not a literal.
```

**Detection hint:** `'USD'`, `'EUR'`, `'GBP'`, or similar literals assigned to `CurrencyIsoCode`.

---

## Anti-Pattern 5: Claiming every currency value converts everywhere

**What the LLM generates:** "All currency fields automatically convert to the user's currency in a multi-currency org."

**Why it happens:** The model flattens UI, report, and API behavior into one rule.

**Correct pattern:**

```text
- API responses and Apex return the stored amount in the record's
  CurrencyIsoCode. SOQL converts only when you call convertCurrency().
- Aggregates with GROUP BY or HAVING return the org default currency.
- Record pages show a parenthetical converted amount to users whose personal
  currency differs only when CurrencySettings.isParenCurrencyConvDisabled is false.
- UNVERIFIED (2026-10-03): report and list view conversion details, which are
  documented only on help.salesforce.com.
```

**Detection hint:** "Automatically converts" with no context named.

---

## Anti-Pattern 6: Writing exchange rates with Apex DML

**What the LLM generates:** A scheduled Apex class that does `insert new DatedConversionRate(...)` or `update currencyTypes;`.

**Why it happens:** The model assumes every sObject supports DML.

**Correct pattern:** `CurrencyType` and `DatedConversionRate` are on the Apex Developer Guide's list of sObjects that don't support DML. Load rates from an integration through the API, and send every field when updating `CurrencyType`.

**Detection hint:** `insert`, `update`, `upsert`, or `delete` on either object in Apex.

---

## Anti-Pattern 7: Static SOQL on currency fields in shared code

**What the LLM generates:** `[SELECT Id, Amount, CurrencyIsoCode FROM Opportunity]` in a class meant for a package or for many orgs.

**Why it happens:** The model writes code in a multi-currency mental model.

**Correct pattern:** `CurrencyIsoCode` exists only in multi-currency orgs. Guard with `UserInfo.isMultiCurrencyOrganization()`, build the field list dynamically, and fall back to `UserInfo.getDefaultCurrency()`.

**Detection hint:** Static SOQL naming `CurrencyIsoCode` or `CurrencyType` in code that must run in any org.
