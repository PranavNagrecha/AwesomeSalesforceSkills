# Examples — Custom Logging and Monitoring

## Example 1: Platform Event-Based Rollback-Safe Error Logging

**Context:** An Apex trigger processes order records and makes external callouts. When the callout fails, the transaction should rollback to leave the order in its original state — but the team needs the error logged for investigation.

**Problem:** Direct DML to `Log__c` in a catch block is included in the transaction rollback. The error log disappears along with the failed order update.

**Solution:**

Define a Platform Event `Log_Event__e` with fields: `Level__c`, `Source__c`, `Message__c`.

In the trigger catch block:
```apex
try {
    // callout and DML
} catch (Exception ex) {
    // DML log to Log__c WOULD be rolled back — use PE instead
    EventBus.publish(new Log_Event__e(
        Level__c = 'ERROR',
        Source__c = 'OrderTrigger.processCallout',
        Message__c = ex.getMessage() + ' Stack: ' + ex.getStackTraceString()
    ));
    // Now rollback the transaction
    Database.rollback(sp);
}
```

A trigger on `Log_Event__e` inserts a `Log__c` record in a new transaction that is independent of the original rollback.

**Why it works:** Platform Events are published outside the transaction boundary — they survive when the parent transaction rolls back. The subscriber trigger runs in a new transaction, so the `Log__c` insert is permanent.

---

## Example 2: Level-Gated Logger with Custom Metadata Configuration

**Context:** A large org has high-volume batch processing. DEBUG logging was turned on during development and is now consuming gigabytes of storage in the `Log__c` object. The team needs to disable DEBUG without a deployment.

**Problem:** The minimum log level is hardcoded in the Apex logger class.

**Solution:**
1. Create Custom Metadata type `Logger_Config__mdt` with field `Minimum_Level__c` (Picklist: DEBUG, INFO, WARN, ERROR).
2. Update LoggerService to read this at instantiation:

```apex
public class LoggerService {
    private static LoggingLevel minimumLevel;

    static {
        Logger_Config__mdt config = Logger_Config__mdt.getInstance('Default');
        String levelName = config != null ? config.Minimum_Level__c : 'WARN';
        minimumLevel = LoggingLevel.valueOf(levelName);
    }

    public static void log(LoggingLevel level, String source, String message) {
        if (level.ordinal() < minimumLevel.ordinal()) return; // level gate
        // buffer and insert...
    }
}
```

3. In Setup > Custom Metadata Types > Logger_Config, change `Minimum_Level__c` from `DEBUG` to `WARN`. Change takes effect on the next transaction without a deployment.

**Why it works:** Custom Metadata values are read at runtime, not compile time. Changing the record value immediately affects all subsequent transactions.

---

## Anti-Pattern: Logging Inside a Loop Without Buffering

**What practitioners do:** Call a `log()` method inside a `for` loop over a list of records, where each call immediately inserts a `Log__c` record.

**What goes wrong:** Each insert is a separate DML statement. A batch of 200 records produces 200 DML statements — exceeding the 150 DML statement governor limit.

**Correct approach:** Buffer log records in a `List<Log__c>` during the loop. Call `flush()` once at the end to perform a single bulk insert with `Database.insert(buffer, false)`. This uses 1 DML statement regardless of how many records are logged.
