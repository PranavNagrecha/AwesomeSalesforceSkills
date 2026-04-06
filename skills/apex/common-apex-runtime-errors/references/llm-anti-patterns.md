# LLM Anti-Patterns — Common Apex Runtime Errors

Common mistakes AI coding assistants make when generating or advising on Common Apex Runtime Errors.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Generating catch (LimitException e) as a valid recovery block

**What the LLM generates:** A try/catch that wraps SOQL or DML and includes a `catch (System.LimitException e)` or `catch (LimitException e)` block with a log statement or graceful fallback, presented as working error handling.

**Why it happens:** LLMs are trained on Java, C#, and Python patterns where resource exhaustion (OutOfMemoryError, StackOverflowError) can sometimes be caught. The Apex exception hierarchy looks similar, so the model applies the same pattern. Additionally, the Apex documentation noting that LimitException "cannot be caught" is a nuanced negative rule that gets underweighted during generation.

**Correct pattern:**

```apex
// WRONG — catch block is dead code, will never execute
try {
    List<Account> all = [SELECT Id FROM Account];
} catch (LimitException e) {
    System.debug('Caught: ' + e.getMessage()); // NEVER RUNS
}

// CORRECT — prevent, don't catch
if (Limits.getQueries() < Limits.getLimitQueries()) {
    List<Account> all = [SELECT Id FROM Account];
}
```

**Detection hint:** Search generated code for `catch.*LimitException` — any occurrence is a bug.

---

## Anti-Pattern 2: Using scalar SOQL assignment without a null guard

**What the LLM generates:** A helper method or trigger handler that assigns a SOQL result directly to a scalar SObject and immediately accesses a field on the result, without checking for null or using a List.

**Why it happens:** Single-record lookups by ID are a common pattern in tutorial code where the record is guaranteed to exist. LLMs replicate this pattern without adding the defensive check that real production code requires where record existence is not guaranteed.

**Correct pattern:**

```apex
// WRONG — NullPointerException when no record matches
Account acc = [SELECT Name FROM Account WHERE Id = :recordId];
return acc.Name;

// CORRECT — List with isEmpty() guard
List<Account> accs = [SELECT Name FROM Account WHERE Id = :recordId LIMIT 1];
if (accs.isEmpty()) { return null; }
return accs[0].Name;
```

**Detection hint:** Look for `SObjectType varName = [SELECT` patterns immediately followed by `varName.FieldName` without an intervening null check or try/catch for QueryException.

---

## Anti-Pattern 3: Logging only e.getMessage() for DmlException and discarding per-row detail

**What the LLM generates:** A catch block for `DmlException` that logs `e.getMessage()` and returns, treating DML failure as a single-message error rather than a per-row collection of errors.

**Why it happens:** `getMessage()` is the standard `Exception` method across all languages. LLMs default to it without knowing that `DmlException` carries richer structured data unique to Salesforce's bulk DML model.

**Correct pattern:**

```apex
// WRONG — loses per-row context
} catch (DmlException e) {
    System.debug('DML failed: ' + e.getMessage());
}

// CORRECT — extract per-row errors
} catch (DmlException e) {
    for (Integer i = 0; i < e.getNumDml(); i++) {
        System.debug('Row ' + e.getDmlIndex(i)
            + ': ' + e.getDmlMessage(i)
            + ' | Fields: ' + e.getDmlFields(i));
    }
}
```

**Detection hint:** Any `catch (DmlException` block that contains only `e.getMessage()` and no `getNumDml()` or `getDmlMessage(i)` call is logging incomplete information.

---

## Anti-Pattern 4: Placing SOQL inside a for loop over Trigger.new

**What the LLM generates:** A trigger handler that queries related records inside a `for (SObject o : Trigger.new)` loop, issuing one SOQL query per record. The code works correctly in unit tests (small data volumes) and breaks silently in production under bulk load.

**Why it happens:** LLMs learn from code samples where the loop body is logically self-contained. The bulkification constraint (SOQL must be outside loops) is a Salesforce-specific platform rule that is frequently violated in tutorial-grade examples in the training corpus.

**Correct pattern:**

```apex
// WRONG — one SOQL per Opportunity, breaks at > 100 records
for (Opportunity opp : Trigger.new) {
    List<Quote> quotes = [SELECT Id FROM Quote WHERE OpportunityId = :opp.Id];
}

// CORRECT — one SOQL for the whole batch
Set<Id> oppIds = new Set<Id>(new Map<Id, Opportunity>(Trigger.new).keySet());
Map<Id, List<Quote>> byOpp = new Map<Id, List<Quote>>();
for (Quote q : [SELECT Id, OpportunityId FROM Quote WHERE OpportunityId IN :oppIds]) {
    if (!byOpp.containsKey(q.OpportunityId)) byOpp.put(q.OpportunityId, new List<Quote>());
    byOpp.get(q.OpportunityId).add(q);
}
```

**Detection hint:** Any SOQL statement (`[SELECT`) that appears inside a for loop body (indented within `for (` or `for(`) is a potential LimitException site.

---

## Anti-Pattern 5: Treating QueryException as always meaning "no rows" and swallowing it

**What the LLM generates:** A catch block for `QueryException` that silently returns null or a default value, assuming the only cause is zero rows. This hides the two-or-more-rows case, which indicates a data integrity problem.

**Why it happens:** The LLM associates `QueryException` with "record not found" patterns common in web frameworks (404 Not Found). The multi-row case — which indicates an ambiguous or overconstrained query — requires a different response (surface the ambiguity, not silently pick a record).

**Correct pattern:**

```apex
// WRONG — silently swallows a multi-row query that indicates a data problem
try {
    Contact c = [SELECT Id FROM Contact WHERE Email = :email];
    return c;
} catch (QueryException e) {
    return null; // Hides the "more than 1 row" case
}

// CORRECT — use List and distinguish the cases
List<Contact> results = [SELECT Id FROM Contact WHERE Email = :email LIMIT 2];
if (results.isEmpty()) { return null; }
if (results.size() > 1) {
    // Log ambiguity — do not silently pick the first record
    System.debug(LoggingLevel.WARN, 'Ambiguous contact lookup for email: ' + email);
    return null;
}
return results[0];
```

**Detection hint:** Any `catch (QueryException` block with a single `return null;` or `return defaultValue;` without branching on the exception message is masking a potentially different failure mode.

---

## Anti-Pattern 6: Accessing Trigger.new inside a delete trigger handler without checking Trigger.isDelete

**What the LLM generates:** A trigger handler method that accesses `Trigger.new` or `Trigger.new[0]` without checking whether the current trigger operation is a delete event, where `Trigger.new` is null.

**Why it happens:** Trigger handler templates frequently show `Trigger.new` as the primary collection without noting that it is null on delete events. LLMs replicate this pattern when generating delete trigger logic.

**Correct pattern:**

```apex
// WRONG — Trigger.new is null on delete events; throws NullPointerException
if (Trigger.isDelete) {
    String name = Trigger.new[0].Name; // NPE
}

// CORRECT — use Trigger.old on delete events
if (Trigger.isDelete) {
    for (Account acc : Trigger.old) {
        System.debug('Deleting account: ' + acc.Name);
    }
}
```

**Detection hint:** Any `Trigger.new` access inside a block guarded by `Trigger.isDelete` or within a trigger that includes `before delete` or `after delete` in its definition is a bug.
