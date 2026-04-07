# LLM Anti-Patterns — CPQ Apex Plugins

Common mistakes AI coding assistants make when generating or advising on CPQ Apex Plugins.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Generating an Apex Trigger on SBQQ__QuoteLine__c Instead of a Plugin Hook

**What the LLM generates:**

```apex
trigger QuoteLinePricingTrigger on SBQQ__QuoteLine__c (after update) {
    for (SBQQ__QuoteLine__c line : Trigger.new) {
        if (line.SBQQ__ProductFamily__c == 'Hardware') {
            line.SBQQ__CustomerPrice__c = line.SBQQ__NetPrice__c * 1.05;
        }
    }
}
```

**Why it happens:** LLMs are trained on abundant trigger-pattern examples and default to triggers for any "run logic when a record changes" requirement. CPQ-specific plugin documentation is underrepresented in training data compared to standard Apex trigger tutorials.

**Correct pattern:**

```javascript
// JS QCP onAfterCalculate hook — runs inside the CPQ calculation engine
export function onAfterCalculate(quoteModel, quoteLineModels, conn) {
    quoteLineModels.forEach(function(line) {
        if (line.record['SBQQ__ProductFamily__c'] === 'Hardware') {
            line.record['SBQQ__CustomerPrice__c'] =
                (line.record['SBQQ__NetPrice__c'] || 0) * 1.05;
        }
    });
    return Promise.resolve();
}
```

**Detection hint:** Any Apex trigger whose object is `SBQQ__QuoteLine__c` or `SBQQ__Quote__c` and that modifies fields that CPQ's engine owns (price fields, totals, discounts) is almost certainly wrong. Flag any file matching `trigger\s+\w+\s+on\s+SBQQ__Quote(Line)?__c`.

---

## Anti-Pattern 2: Mixing an Active JS QCP and an Apex QuoteCalculatorPlugin

**What the LLM generates:**

```apex
// Registers both in CPQ Settings
// SBQQ__QuoteCalculatorPlugin__c = 'MyApexPlugin'

// AND creates SBQQ__CustomScript__c with SBQQ__Active__c = true
// containing JS QCP hooks
```

The LLM may suggest implementing both as a "belt and suspenders" approach, or may be unaware that the two plugin types are mutually exclusive.

**Why it happens:** Documentation for both plugin types is presented in the same CPQ developer guide. LLMs often treat two described options as combinable without reading the constraint that only one calculator type can be active.

**Correct pattern:**

Choose one. For new implementations, use JS QCP (the modern approach). For orgs with an existing Apex `QuoteCalculatorPlugin`, either extend the Apex class or migrate fully to JS QCP. Query `SELECT SBQQ__Active__c FROM SBQQ__CustomScript__c WHERE SBQQ__Active__c = true` to confirm no active JS QCP before registering an Apex calculator plugin, and vice versa.

**Detection hint:** A response that references both `SBQQ__CustomScript__c` with `SBQQ__Active__c = true` AND `SBQQ__QuoteCalculatorPlugin__c` registration in CPQ Settings at the same time is wrong.

---

## Anti-Pattern 3: Using `public` Instead of `global` on the Plugin Class

**What the LLM generates:**

```apex
public class MyOrderPlugin implements SBQQ.OrderPlugin {
    public void onBeforeInsert(List<Order> orders,
                               SBQQ.DefaultOrderProduct d,
                               Database.UnitOfWork uow) { ... }
    public void onAfterInsert(List<Order> orders,
                              SBQQ.DefaultOrderProduct d,
                              Database.UnitOfWork uow) { ... }
}
```

**Why it happens:** `public` is the conventional access modifier for Apex classes. LLMs default to `public` because it is the most common modifier in training data. The constraint that managed-package interfaces require `global` implementing classes is a Salesforce-specific namespace rule not commonly found in generic Apex tutorials.

**Correct pattern:**

```apex
global class MyOrderPlugin implements SBQQ.OrderPlugin {
    global void onBeforeInsert(List<Order> orders,
                               SBQQ.DefaultOrderProduct d,
                               Database.UnitOfWork uow) { ... }
    global void onAfterInsert(List<Order> orders,
                              SBQQ.DefaultOrderProduct d,
                              Database.UnitOfWork uow) { ... }
}
```

**Detection hint:** Any class that `implements SBQQ.<anything>` but is declared `public class` instead of `global class` is wrong. Check method-level modifiers too — every overridden interface method must also be `global`.

---

## Anti-Pattern 4: JS QCP Hook Functions That Return Void or Lack a Return Statement

**What the LLM generates:**

```javascript
export function onBeforeCalculate(quoteModel, quoteLineModels, conn) {
    quoteLineModels.forEach(function(line) {
        // ... logic ...
    });
    // No return statement — returns undefined
}
```

Or with an early return:

```javascript
export function onAfterCalculate(quoteModel, quoteLineModels, conn) {
    if (!quoteLineModels || quoteLineModels.length === 0) {
        return; // returns undefined on this branch
    }
    // ... logic ...
    return Promise.resolve();
}
```

**Why it happens:** LLMs model JavaScript functions after common patterns where void returns are acceptable. The CPQ-specific requirement that every hook must return a `Promise` in every branch is a framework constraint not found in general JavaScript documentation.

**Correct pattern:**

```javascript
export function onAfterCalculate(quoteModel, quoteLineModels, conn) {
    if (!quoteLineModels || quoteLineModels.length === 0) {
        return Promise.resolve(); // Always return a Promise
    }
    quoteLineModels.forEach(function(line) {
        // ... logic ...
    });
    return Promise.resolve();
}
```

**Detection hint:** Scan any JS QCP for hook functions that contain `return;` (bare return) or that have code paths ending without an explicit `return Promise`. Flag functions where the last statement is not `return Promise.resolve()` or `return new Promise(...)`.

---

## Anti-Pattern 5: Performing Per-Line SOQL Inside Plugin Loop Iterations

**What the LLM generates:**

```apex
global class MyCalcPlugin implements SBQQ.QuoteCalculatorPlugin {
    global void calculate(List<SBQQ__QuoteLine__c> lines,
                          SBQQ.CalculateCallback callback) {
        for (SBQQ__QuoteLine__c line : lines) {
            // SOQL inside the loop — hits governor limits on large quotes
            Product2 prod = [SELECT Custom_Multiplier__c FROM Product2
                              WHERE Id = :line.SBQQ__Product__c LIMIT 1];
            line.SBQQ__CustomerPrice__c *= prod.Custom_Multiplier__c;
        }
        callback.run(lines);
    }
}
```

**Why it happens:** LLMs produce code that works correctly for small datasets, which is how it is usually tested. The N+1 query pattern is common in training data and the SOQL-in-loop anti-pattern is well-documented for triggers but not always applied to plugin contexts by LLMs.

**Correct pattern:**

```apex
global class MyCalcPlugin implements SBQQ.QuoteCalculatorPlugin {
    global void calculate(List<SBQQ__QuoteLine__c> lines,
                          SBQQ.CalculateCallback callback) {
        // Collect all product IDs first
        Set<Id> productIds = new Set<Id>();
        for (SBQQ__QuoteLine__c line : lines) {
            productIds.add(line.SBQQ__Product__c);
        }

        // Single bulk query
        Map<Id, Product2> productMap = new Map<Id, Product2>(
            [SELECT Id, Custom_Multiplier__c FROM Product2
             WHERE Id IN :productIds]
        );

        // O(1) map lookups inside the loop — no SOQL
        for (SBQQ__QuoteLine__c line : lines) {
            Product2 prod = productMap.get(line.SBQQ__Product__c);
            if (prod != null && prod.Custom_Multiplier__c != null) {
                line.SBQQ__CustomerPrice__c =
                    (line.SBQQ__CustomerPrice__c ?? 0) * prod.Custom_Multiplier__c;
            }
        }
        callback.run(lines);
    }
}
```

**Detection hint:** Any Apex plugin method containing a `SELECT` statement inside a `for` loop or a `.forEach` iteration block is performing SOQL in a loop. Flag patterns matching `for\s*\(.*\)\s*\{[^}]*\[SELECT` in plugin class files.

---

## Anti-Pattern 6: Registering a New Plugin Without Checking the Existing Registration

**What the LLM generates:**

A complete implementation and deployment guide for a new `OrderPlugin` class that instructs the developer to enter the new class name in CPQ Settings — with no mention of checking whether a plugin is already registered.

**Why it happens:** LLMs generate complete implementations in isolation without considering the stateful org context. The single-slot constraint (only one plugin per type) and the risk of overwriting an existing registration are not surfaced unless the LLM has been explicitly prompted with that context.

**Correct pattern:**

Before registering, query the current CPQ Settings:

```apex
// Run as anonymous Apex or in a SOQL query tool
SBQQ__CustomActionSettings__c settings = SBQQ__CustomActionSettings__c.getOrgDefaults();
System.debug('Current Order Plugin: ' + settings.SBQQ__OrderPlugin__c);
System.debug('Current Contracting Plugin: ' + settings.SBQQ__ContractingPlugin__c);
System.debug('Current Calculator Plugin: ' + settings.SBQQ__QuoteCalculatorPlugin__c);
```

If a class is already registered, incorporate the new logic into the existing class (or create a dispatcher) rather than replacing it.

**Detection hint:** A response that includes CPQ Settings registration instructions but does not include a step to check the existing plugin registration value before overwriting it is incomplete. Flag responses that say "enter X in the plugin field" without a preceding "check if a plugin is already registered."
