# LLM Anti-Patterns — Debug and Logging

Common mistakes AI coding assistants make when generating or advising on Apex debugging and logging strategies.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Scattering System.debug everywhere instead of using a logging framework

**What the LLM generates:**

```apex
public class AccountService {
    public static void processAccounts(List<Account> accounts) {
        System.debug('Starting processAccounts with ' + accounts.size() + ' records');
        for (Account a : accounts) {
            System.debug('Processing account: ' + a.Id + ' - ' + a.Name);
            // business logic
            System.debug('Finished processing: ' + a.Id);
        }
        System.debug('processAccounts complete');
    }
}
```

**Why it happens:** LLMs add `System.debug` statements as the default logging mechanism because it is the simplest. But debug logs are transient (auto-purged after 24 hours), not queryable, and the per-record debugging adds CPU overhead at scale. In production, debug logs are often disabled or truncated.

**Correct pattern:**

```apex
public class AccountService {
    public static void processAccounts(List<Account> accounts) {
        Logger.info('AccountService.processAccounts', 'Processing ' + accounts.size() + ' accounts');
        try {
            // business logic
        } catch (Exception e) {
            Logger.error('AccountService.processAccounts', e);
            throw e;
        }
    }
}

// Logger writes to a custom object or platform event for durable observability
```

**Detection hint:** More than 3 `System\.debug` calls in a single method, especially inside loops.

---

## Anti-Pattern 2: Using System.debug without specifying a LoggingLevel

**What the LLM generates:**

```apex
System.debug('Account processed: ' + account.Id);
```

**Why it happens:** LLMs omit the `LoggingLevel` parameter, which defaults to `DEBUG`. This means all log statements appear at the same level, making it impossible to filter noise from signal when reading debug logs.

**Correct pattern:**

```apex
System.debug(LoggingLevel.FINE, 'Account processed: ' + account.Id);
System.debug(LoggingLevel.ERROR, 'Failed to process account: ' + account.Id + ' — ' + e.getMessage());
System.debug(LoggingLevel.WARN, 'Approaching governor limit: ' + Limits.getQueries() + '/100 SOQL');
```

**Detection hint:** `System\.debug\(` without `LoggingLevel\.` as the first argument.

---

## Anti-Pattern 3: Serializing entire SObjects in debug statements

**What the LLM generates:**

```apex
for (Account a : accounts) {
    System.debug('Account data: ' + JSON.serializePretty(a));
}
```

**Why it happens:** LLMs produce maximally verbose logging. `JSON.serializePretty` on every record in a loop consumes significant CPU and heap. If the SObject has many fields or large text fields, a single serialization can add kilobytes to heap per record.

**Correct pattern:**

```apex
System.debug(LoggingLevel.FINE, 'Processing ' + accounts.size() + ' accounts');
// Only serialize specific fields when debugging a specific issue
if (accounts.size() <= 5) {
    for (Account a : accounts) {
        System.debug(LoggingLevel.FINEST, 'Account: Id=' + a.Id + ', Status=' + a.Status__c);
    }
}
```

**Detection hint:** `JSON\.serialize` or `JSON\.serializePretty` inside a `for` loop combined with `System\.debug`.

---

## Anti-Pattern 4: Not monitoring AsyncApexJob for batch and queueable failures

**What the LLM generates:**

```apex
// Batch finish method with no monitoring
public void finish(Database.BatchableContext bc) {
    System.debug('Batch complete');
}
```

**Why it happens:** LLMs treat `finish()` as a formality. But `finish()` is the only place to check whether the batch had errors, how many records failed, and whether follow-up action is needed. Without querying `AsyncApexJob`, failures go unnoticed.

**Correct pattern:**

```apex
public void finish(Database.BatchableContext bc) {
    AsyncApexJob job = [
        SELECT Id, Status, NumberOfErrors, JobItemsProcessed, TotalJobItems, ExtendedStatus
        FROM AsyncApexJob WHERE Id = :bc.getJobId()
    ];
    if (job.NumberOfErrors > 0) {
        LogService.logBatchFailure('MyBatch', job);
        // Send alert or create a task for ops
        Messaging.SingleEmailMessage mail = new Messaging.SingleEmailMessage();
        mail.setSubject('Batch Failed: ' + job.NumberOfErrors + ' errors');
        mail.setPlainTextBody('Status: ' + job.ExtendedStatus);
        mail.setToAddresses(new List<String>{'ops@company.com'});
        Messaging.sendEmail(new List<Messaging.SingleEmailMessage>{mail});
    }
}
```

**Detection hint:** Batch `finish()` method that contains only `System.debug` or is empty, with no `AsyncApexJob` query.

---

## Anti-Pattern 5: Logging sensitive data (PII, credentials) in debug statements

**What the LLM generates:**

```apex
System.debug('User SSN: ' + contact.SSN__c);
System.debug('API Key: ' + apiSettings.API_Key__c);
System.debug('Auth token: ' + response.getHeader('Authorization'));
```

**Why it happens:** LLMs add debugging for all variables without considering data sensitivity. Debug logs can be viewed by any user with "Manage Users" or "View All Data" permissions, and they persist in the system for up to 24 hours. Logging PII or secrets creates a compliance and security risk.

**Correct pattern:**

```apex
// Never log credentials or PII
System.debug(LoggingLevel.FINE, 'Callout completed with status: ' + response.getStatusCode());
// Mask sensitive fields
System.debug(LoggingLevel.FINE, 'Processing contact: ' + contact.Id + ', SSN: ***masked***');
```

**Detection hint:** `System\.debug.*SSN|Password|Secret|API_Key|Token|Authorization` — sensitive field names in debug statements.

---

## Anti-Pattern 6: Creating a custom logging object without considering governor limits

**What the LLM generates:**

```apex
// Logging every operation as a separate DML
public static void log(String message) {
    insert new App_Log__c(Message__c = message, Timestamp__c = Datetime.now());
}

// Called from a loop:
for (Account a : accounts) {
    Logger.log('Processed: ' + a.Id);
}
```

**Why it happens:** LLMs generate per-event log inserts. Calling `insert` per log entry inside a loop quickly hits the 150 DML statement limit. Logging should be buffered and flushed in a single DML or published as platform events.

**Correct pattern:**

```apex
public class Logger {
    private static List<App_Log__c> buffer = new List<App_Log__c>();

    public static void log(String level, String message) {
        buffer.add(new App_Log__c(
            Level__c = level, Message__c = message, Timestamp__c = Datetime.now()
        ));
    }

    public static void flush() {
        if (!buffer.isEmpty()) {
            Database.insert(buffer, false); // Single DML, partial success
            buffer.clear();
        }
    }
}

// Usage:
for (Account a : accounts) {
    Logger.log('INFO', 'Processed: ' + a.Id);
}
Logger.flush(); // One DML for all log entries
```

**Detection hint:** `insert new.*Log__c` inside a `for` or `while` loop.
