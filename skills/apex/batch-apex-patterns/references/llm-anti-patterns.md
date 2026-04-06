# LLM Anti-Patterns — Batch Apex Patterns

Common mistakes AI coding assistants make when generating or advising on Batch Apex.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Accumulating state in instance variables without implementing Database.Stateful

**What the LLM generates:**

```apex
public class ErrorCollectorBatch implements Database.Batchable<SObject> {
    public List<String> errors = new List<String>(); // Reset every execute()

    public void execute(Database.BatchableContext bc, List<Account> scope) {
        for (Account a : scope) {
            if (a.Name == null) errors.add('Missing name: ' + a.Id);
        }
    }

    public void finish(Database.BatchableContext bc) {
        System.debug('Total errors: ' + errors.size()); // Always 0 or last scope only
    }
}
```

**Why it happens:** LLMs declare instance variables and assume they persist across `execute()` calls. Without `Database.Stateful`, the batch instance is re-serialized between each scope and instance variables reset to their initial values.

**Correct pattern:**

```apex
public class ErrorCollectorBatch implements Database.Batchable<SObject>, Database.Stateful {
    public List<String> errors = new List<String>(); // Persists across executes

    public void execute(Database.BatchableContext bc, List<Account> scope) {
        for (Account a : scope) {
            if (a.Name == null) errors.add('Missing name: ' + a.Id);
        }
    }

    public void finish(Database.BatchableContext bc) {
        if (!errors.isEmpty()) {
            // Send summary email or log errors
        }
    }
}
```

**Detection hint:** Batch class that accumulates data into instance variables across `execute()` calls but does not implement `Database.Stateful`.

---

## Anti-Pattern 2: Using a scope size of 1 to "be safe" with callouts

**What the LLM generates:**

```apex
Database.executeBatch(new IntegrationBatch(), 1); // One record at a time
```

**Why it happens:** LLMs set scope to 1 when the batch makes callouts, thinking it avoids governor limit issues. A scope of 1 means one `execute()` call per record. With 10,000 records, that is 10,000 transactions — dramatically slower, higher platform overhead, and more likely to hit the 24-hour batch timeout.

**Correct pattern:**

```apex
// Use a reasonable scope — each execute() can make up to 100 callouts
Database.executeBatch(new IntegrationBatch(), 10); // 10 records per callout batch

// Inside execute(), make one callout per record or batch them:
public void execute(Database.BatchableContext bc, List<Account> scope) {
    for (Account a : scope) {
        // One callout per record is fine within a scope of 10-20
        callExternalApi(a);
    }
}
```

**Detection hint:** `executeBatch\(.*,\s*1\)` — a scope of 1 should be a red flag unless there is a documented reason.

---

## Anti-Pattern 3: Returning a List from start() when Database.getQueryLocator would work

**What the LLM generates:**

```apex
public List<Account> start(Database.BatchableContext bc) {
    return [SELECT Id, Name FROM Account WHERE Status__c = 'Active'];
    // Limited to 50,000 records — same as synchronous SOQL
}
```

**Why it happens:** LLMs return a `List<SObject>` from `start()` because it looks simpler. But `List` return is subject to the 50K SOQL row limit. `Database.getQueryLocator` supports up to 50 million rows. Using `List` silently truncates large datasets.

**Correct pattern:**

```apex
public Database.QueryLocator start(Database.BatchableContext bc) {
    return Database.getQueryLocator(
        'SELECT Id, Name FROM Account WHERE Status__c = \'Active\''
    );
    // Supports up to 50 million rows
}
```

**Detection hint:** Batch `start()` method that returns `List<SObject>` or `Iterable<SObject>` when the data source is a simple SOQL query (no external API, no computed data).

---

## Anti-Pattern 4: Not using Database.insert/update with allOrNone=false for partial success

**What the LLM generates:**

```apex
public void execute(Database.BatchableContext bc, List<Account> scope) {
    for (Account a : scope) {
        a.Status__c = 'Processed';
    }
    update scope; // One bad record fails the entire scope
}
```

**Why it happens:** LLMs use standard DML (`update`) which is all-or-nothing. If one record in a scope of 200 has a validation rule failure, all 200 records roll back. In batch processing, partial success is usually preferred.

**Correct pattern:**

```apex
public void execute(Database.BatchableContext bc, List<Account> scope) {
    for (Account a : scope) {
        a.Status__c = 'Processed';
    }
    List<Database.SaveResult> results = Database.update(scope, false);
    for (Integer i = 0; i < results.size(); i++) {
        if (!results[i].isSuccess()) {
            for (Database.Error err : results[i].getErrors()) {
                errorLog.add(scope[i].Id + ': ' + err.getMessage());
            }
        }
    }
}
```

**Detection hint:** `update ` or `insert ` (standard DML) in batch `execute()` methods — should be `Database.update(scope, false)` for partial success handling.

---

## Anti-Pattern 5: Chaining batch jobs without checking flex queue capacity

**What the LLM generates:**

```apex
public void finish(Database.BatchableContext bc) {
    Database.executeBatch(new FollowUpBatch());
}
```

**Why it happens:** LLMs chain batches in `finish()` assuming a slot is always available. If the flex queue is full (100 jobs), `executeBatch` throws `AsyncException` and the chain breaks with no recovery.

**Correct pattern:**

```apex
public void finish(Database.BatchableContext bc) {
    try {
        Database.executeBatch(new FollowUpBatch(), 200);
    } catch (AsyncException e) {
        // Flex queue full — schedule a retry
        System.schedule('RetryFollowUp_' + Datetime.now().getTime(),
            '0 5 * * * ? *', new BatchRetryScheduler(FollowUpBatch.class));
    }
}
```

**Detection hint:** `Database\.executeBatch` in a `finish` method without a try/catch or flex queue capacity check.

---

## Anti-Pattern 6: Querying child records inside execute() instead of including them in start()

**What the LLM generates:**

```apex
public Database.QueryLocator start(Database.BatchableContext bc) {
    return Database.getQueryLocator('SELECT Id FROM Account');
}

public void execute(Database.BatchableContext bc, List<Account> scope) {
    for (Account a : scope) {
        List<Contact> contacts = [SELECT Id FROM Contact WHERE AccountId = :a.Id]; // SOQL in loop
    }
}
```

**Why it happens:** LLMs separate the parent query from child access. This creates N SOQL queries per scope — one per record — hitting the 100 SOQL query limit on large scopes.

**Correct pattern:**

```apex
public Database.QueryLocator start(Database.BatchableContext bc) {
    return Database.getQueryLocator(
        'SELECT Id, (SELECT Id, Email FROM Contacts) FROM Account'
    );
}

public void execute(Database.BatchableContext bc, List<Account> scope) {
    for (Account a : scope) {
        List<Contact> contacts = a.Contacts; // Already loaded — no additional SOQL
    }
}
```

**Detection hint:** SOQL query inside a `for` loop within a batch `execute()` method — `\[SELECT.*WHERE.*:.*\]` inside `for`.
