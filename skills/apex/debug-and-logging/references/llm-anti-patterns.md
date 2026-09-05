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

**Why it happens:** LLMs add `System.debug` statements as the default logging mechanism because it is the simplest. But debug logs are transient — "System debug logs are retained for 24 hours. Monitoring debug logs are retained for seven days" (Apex Developer Guide L38118) — not queryable, and the per-record debugging adds CPU overhead at scale. A log over 20 MB is silently trimmed, and the lines removed "can be removed from any location, not just the start of the debug log" (L38115–38117), so the statement you needed may be the one that went.

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
System.debug(LoggingLevel.WARN, 'Approaching governor limit: ' + Limits.getQueries() + '/' + Limits.getLimitQueries());
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

**Why it happens:** LLMs add debugging for all variables without considering data sensitivity. The platform scrubs exactly one thing for you — "Session IDs are replaced with `SESSION_ID_REMOVED` in Apex debug logs" (Apex Developer Guide L38133) — and nothing else. At `FINEST` the log "includes details of all Apex variable assignments" (L38171–38175), so a password held in a local string is in the file. Retention is 24 hours for system logs and seven days for monitoring logs (L38118). UNVERIFIED (2026-09-05): which permissions grant a user access to another user's debug log is documented on help.salesforce.com, which is not in the grounding corpus — do not repeat a specific permission name without checking.

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

**Why it happens:** LLMs generate per-event log inserts. Calling `insert` per log entry inside a loop quickly hits the DML statement ceiling — the limit block written into every debug log reads "Number of DML statements: 0 out of 150" (Apex Developer Guide L38279). Logging should be buffered and flushed in a single DML or published as platform events. Note the meters differ: publish-after-commit events count against that same DML limit, publish-immediately events against "a separate event publishing limit of 150 `EventBus.publish()` calls" (Apex Reference Guide L214524–214528).

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

---

## Anti-Pattern 7: Building a log platform event and leaving `publishBehavior` at the default

**What the LLM generates:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <deploymentStatus>Deployed</deploymentStatus>
    <label>Log Event</label>
    <pluralLabel>Log Events</pluralLabel>
    <eventType>HighVolume</eventType>
</CustomObject>
```

**Why it happens:** The model knows platform events are the durable-logging answer but treats the
publish behaviour as boilerplate. Two failure modes follow. If a human later sets it to
`PublishAfterCommit` — which is what the Setup UI's wording nudges toward — the log for the failing
transaction is discarded with the rollback: "If the transaction fails, the event message isn't
published" (api_meta L42222–42224). And an unstated behaviour is invisible in code review.

**Correct pattern:** state it, and route only ERROR/FATAL down it so the 150-call publish-immediate
limit is not spent on breadcrumbs.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <deploymentStatus>Deployed</deploymentStatus>
    <label>Log Event</label>
    <pluralLabel>Log Events</pluralLabel>
    <eventType>HighVolume</eventType>
    <publishBehavior>PublishImmediately</publishBehavior>
</CustomObject>
```

**Detection hint:** a `.object-meta.xml` whose `fullName`/directory ends in `__e` and whose name
matches `Log|Error|Audit|Trace`, with no `<publishBehavior>` element.

---

## Anti-Pattern 8: A test that publishes a log event and asserts on the subscriber without `Test.getEventBus().deliver()`

**What the LLM generates:**

```apex
@IsTest
static void logsError() {
    Test.startTest();
    LogService.error('X', new MyException('boom'));
    LogService.flush();
    Test.stopTest();

    System.assertEquals(1, [SELECT COUNT() FROM Application_Log__c]);
}
```

**Why it happens:** The model assumes `Test.stopTest()` flushes every async path the way it does for
`@future` and Queueable. Platform event delivery to an Apex subscriber is not one of them — the guide
tells you to call `deliver()` explicitly and to "Enclose `Test.getEventBus().deliver()` within the
`Test.startTest()` and `Test.stopTest()` statement block" (Apex Reference Guide L157701). The
assertion then fails against an empty table and the next move is usually to weaken the assertion,
which is how a logging path ships untested.

**Correct pattern:**

```apex
@IsTest
static void logsError() {
    Test.startTest();
    LogService.error('X', new MyException('boom'));
    LogService.flush();
    Test.getEventBus().deliver();
    Test.stopTest();

    List<Application_Log__c> rows = [SELECT Severity__c, Request_Id__c FROM Application_Log__c];
    System.assertEquals(1, rows.size(), 'Subscriber should have written one row');
    System.assertEquals('ERROR', rows[0].Severity__c, 'Severity should round-trip');
}
```

If a downstream process publishes further events, call `deliver()` again — "If further platform
events are published by downstream processes, add `Test.getEventBus().deliver();` to deliver the event
messages for each process" (Apex Developer Guide L17938–17940).

**Detection hint:** a test method containing `EventBus.publish` or a `Log`/`Event` service call, plus
a SOQL assertion, with no `Test.getEventBus().deliver()` between them.
