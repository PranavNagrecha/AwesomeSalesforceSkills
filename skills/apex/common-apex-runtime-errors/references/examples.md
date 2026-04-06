# Examples — Common Apex Runtime Errors

## Example 1: NullPointerException from scalar SOQL on zero rows

**Context:** A service method loads an Account by ID to read the BillingCountry field. The ID was passed from a Flow with a misconfigured variable that occasionally resolves to a non-existent record.

**Problem:** The scalar SOQL assignment silently returns `null` when no row matches, and the field access on the next line throws `NullPointerException` with a misleading stack trace pointing to the field access, not the query.

```apex
// UNSAFE — throws NullPointerException when no Account matches
public String getCountry(Id accountId) {
    Account acc = [SELECT BillingCountry FROM Account WHERE Id = :accountId];
    return acc.BillingCountry; // NPE thrown here if acc is null
}
```

**Solution:**

```apex
// SAFE — uses List + isEmpty() guard
public String getCountry(Id accountId) {
    List<Account> accounts = [
        SELECT BillingCountry FROM Account WHERE Id = :accountId LIMIT 1
    ];
    if (accounts.isEmpty()) {
        throw new AuraHandledException('Account not found: ' + accountId);
    }
    return accounts[0].BillingCountry;
}
```

**Why it works:** A `List<SObject>` SOQL query never returns `null` — it returns an empty list on zero rows. The explicit `isEmpty()` check surfaces the real problem (missing record) with a meaningful error rather than deferring to a `NullPointerException` on field access.

---

## Example 2: QueryException — List has more than 1 row

**Context:** A trigger handler queries a Contact by email to link it to an incoming Lead. The email is not unique in the org, so two Contacts match.

**Problem:** The scalar SObject assignment throws `QueryException: List has more than 1 row for assignment to SObject`.

```apex
// UNSAFE — throws QueryException when email matches multiple Contacts
Contact c = [SELECT Id FROM Contact WHERE Email = :lead.Email];
```

**Solution:**

```apex
// SAFE — handles 0, 1, or many rows explicitly
List<Contact> matches = [
    SELECT Id FROM Contact WHERE Email = :lead.Email LIMIT 2
];
if (matches.isEmpty()) {
    // No match — skip linking
    return;
}
if (matches.size() > 1) {
    // Ambiguous — log and skip; do not silently pick one
    System.debug(LoggingLevel.WARN,
        'Multiple Contacts match email ' + lead.Email + ' — skipping auto-link');
    return;
}
lead.Contact__c = matches[0].Id;
```

**Why it works:** `LIMIT 2` caps the query cost. The explicit size checks handle all three cases (0, 1, many) with deliberate behavior rather than letting the platform throw.

---

## Example 3: DmlException with per-row error logging

**Context:** A batch job inserts a list of Case records. Some records fail validation rules. The job must log failures and continue processing the rest.

**Problem:** Using `insert cases;` (allOrNone=true by default) rolls back all records in the batch when even one fails validation, making partial success impossible.

**Solution:**

```apex
List<Database.SaveResult> results = Database.insert(cases, false); // allOrNone=false
for (Integer i = 0; i < results.size(); i++) {
    if (!results[i].isSuccess()) {
        for (Database.Error err : results[i].getErrors()) {
            System.debug(LoggingLevel.ERROR,
                'Case insert failed — row ' + i
                + ' | Message: ' + err.getMessage()
                + ' | Fields: ' + err.getFields()
                + ' | Subject: ' + cases[i].Subject);
        }
    }
}
```

**Why it works:** `Database.insert` with `allOrNone=false` commits successful rows and returns a `SaveResult` per record. Iterating the results with the same index as the source list (`cases[i]`) lets you attach the source record's identifying fields to the error log, making triage far faster.

---

## Example 4: LimitException prevention with Limits API guard

**Context:** A trigger on Opportunity updates related Quote records in a loop — a classic SOQL-inside-loop pattern that works in developer orgs (small data volumes) but fails in production under bulk load.

**Problem:** The SOQL executes once per Opportunity record. With 150 Opportunities in a batch, the trigger issues 150 SOQL queries and hits the 101-query governor limit (`LimitException: Too many SOQL queries: 101`). This exception cannot be caught.

```apex
// UNSAFE — SOQL inside trigger loop
for (Opportunity opp : Trigger.new) {
    List<Quote> quotes = [SELECT Id FROM Quote WHERE OpportunityId = :opp.Id];
    // ... update quotes
}
```

**Solution:**

```apex
// SAFE — collect IDs, query once, process in-memory
Set<Id> oppIds = new Set<Id>();
for (Opportunity opp : Trigger.new) {
    oppIds.add(opp.Id);
}
Map<Id, List<Quote>> quotesByOpp = new Map<Id, List<Quote>>();
for (Quote q : [SELECT Id, OpportunityId FROM Quote WHERE OpportunityId IN :oppIds]) {
    if (!quotesByOpp.containsKey(q.OpportunityId)) {
        quotesByOpp.put(q.OpportunityId, new List<Quote>());
    }
    quotesByOpp.get(q.OpportunityId).add(q);
}
for (Opportunity opp : Trigger.new) {
    List<Quote> quotes = quotesByOpp.containsKey(opp.Id)
        ? quotesByOpp.get(opp.Id) : new List<Quote>();
    // ... process quotes
}
```

**Why it works:** One SOQL query replaces N queries. The `IN :oppIds` bind variable is evaluated once. This pattern works for any batch size.

---

## Example 5: ListException — index out of bounds on filtered result

**Context:** A controller method retrieves the most recent log entry for a record. The SOQL uses ORDER BY and LIMIT 1 but the developer accesses `[0]` without checking if the list is empty.

**Problem:** When no log entries exist yet, `[0]` throws `ListException: List index out of bounds: 0`.

```apex
// UNSAFE
List<Log__c> logs = [SELECT Id, Message__c FROM Log__c
    WHERE Parent__c = :recordId ORDER BY CreatedDate DESC LIMIT 1];
String lastMessage = logs[0].Message__c; // ListException if logs is empty
```

**Solution:**

```apex
// SAFE
List<Log__c> logs = [SELECT Id, Message__c FROM Log__c
    WHERE Parent__c = :recordId ORDER BY CreatedDate DESC LIMIT 1];
String lastMessage = logs.isEmpty() ? null : logs[0].Message__c;
```

**Why it works:** The ternary short-circuits before the index access when the list is empty, returning a safe null that callers can handle explicitly.

---

## Anti-Pattern: Catching LimitException

**What practitioners do:** Wrap SOQL or DML in a try/catch block with `catch (LimitException e)` expecting to handle limit breaches gracefully.

**What goes wrong:** `System.LimitException` cannot be caught. The catch block is dead code. The transaction is terminated by the platform before any catch handler executes. The error surfaces to the caller as an unhandled exception regardless.

**Correct approach:** Use the `Limits.*` API to check proximity to limits before executing operations. Move bulk work to Queueable or Batch Apex. See the `governor-limits` skill for systematic prevention patterns.

```apex
// DEAD CODE — LimitException will never be caught
try {
    List<Account> all = [SELECT Id FROM Account]; // Could exceed limits
} catch (LimitException e) {
    System.debug('Caught limit: ' + e.getMessage()); // NEVER RUNS
}

// CORRECT — prevent, don't catch
if (Limits.getQueries() < Limits.getLimitQueries()) {
    List<Account> all = [SELECT Id FROM Account];
}
```
