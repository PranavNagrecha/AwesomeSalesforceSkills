# Examples - Multi Currency And Advanced Currency Management

## Example 1: Query Amount With Currency Context

**Context:** Apex must return Opportunity amounts to an external service.

**Problem:** A payload with only the amount value loses its meaning in a multi-currency org.

**Solution:**

```apex
List<Opportunity> records = [
    SELECT Id, Amount, CurrencyIsoCode
    FROM Opportunity
    WHERE Id IN :opportunityIds
];
```

**Why it works:** The consumer receives both the number and the transaction currency.

---

## Example 2: User-Currency Projection In SOQL

**Context:** A user-facing report helper needs values in the running user's currency context.

**Problem:** Stored amounts alone do not satisfy the presentation requirement.

**Solution:**

```apex
List<Opportunity> records = [
    SELECT Id, convertCurrency(Amount)
    FROM Opportunity
    WHERE CloseDate = THIS_QUARTER
];
```

**Why it works:** The query explicitly asks for converted values instead of assuming all consumers want stored currency.

---

## Anti-Pattern: Hardcoded USD Math

**What practitioners do:** They divide or multiply amounts using a hardcoded currency assumption in Apex.

**What goes wrong:** The logic breaks as soon as records or users span multiple currencies or dated rates.

**Correct approach:** Keep currency context explicit and let supported currency mechanisms drive conversion behavior.
