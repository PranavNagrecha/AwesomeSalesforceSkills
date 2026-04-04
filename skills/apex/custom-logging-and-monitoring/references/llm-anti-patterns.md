# LLM Anti-Patterns — Custom Logging and Monitoring

Common mistakes AI coding assistants make when generating or advising on custom Apex logging frameworks.

## Anti-Pattern 1: Per-Record DML Insert Inside a Loop

**What the LLM generates:** A logger that calls `insert new Log__c(...)` inside every loop iteration.

**Why it happens:** LLMs model logging as a simple write operation without considering governor limits in bulk contexts.

**Correct pattern:**
```apex
// WRONG: DML per log call
public static void log(String msg) {
    insert new Log__c(Message__c = msg); // 1 DML per call = governor limit in loops
}

// CORRECT: buffer and flush once
private List<Log__c> buffer = new List<Log__c>();

public void log(String msg) {
    buffer.add(new Log__c(Message__c = msg));
}

public void flush() {
    if (!buffer.isEmpty()) {
        Database.insert(buffer, false);
        buffer.clear();
    }
}
```

**Detection hint:** Any logging class that calls `insert` or `Database.insert()` inside the `log()` method directly, rather than adding to a buffer.

---

## Anti-Pattern 2: Not Handling Log Insert Failure (Missing allOrNone=false)

**What the LLM generates:** `Database.insert(logs)` or `insert logs` — both of which throw an exception if any log record fails validation.

**Why it happens:** LLMs default to simple DML. They do not consider that a failing log insert should never interrupt business logic.

**Correct pattern:**
```apex
// WRONG: throws on log insert failure, interrupts business logic
Database.insert(buffer);

// CORRECT: partial success — log failures do not interrupt execution
Database.insert(buffer, false);
```

**Detection hint:** Any `Database.insert(buffer)` or `insert buffer` in a logging flush method without `false` as the second argument.

---

## Anti-Pattern 3: Using Direct DML for Error Logs Without Considering Rollback

**What the LLM generates:** A catch block that inserts a `Log__c` record via direct DML, assuming the error will always be captured.

**Why it happens:** LLMs model DML as always committed. They do not know that DML in a rolled-back transaction is undone.

**Correct pattern:**
```apex
// WRONG: log may be rolled back with the transaction
} catch (Exception ex) {
    insert new Log__c(Level__c = 'ERROR', Message__c = ex.getMessage());
    Database.rollback(sp);
}

// CORRECT: Platform Event survives rollback
} catch (Exception ex) {
    EventBus.publish(new Log_Event__e(Level__c = 'ERROR', Message__c = ex.getMessage()));
    Database.rollback(sp);
}
```

**Detection hint:** Any catch block that does DML to a Log object AND then performs a rollback (or where the surrounding transaction is known to roll back on exception).

---

## Anti-Pattern 4: Singleton That Does Not Support Test Reset

**What the LLM generates:** A Logger singleton with a private static variable and no test reset capability.

**Why it happens:** LLMs generate the simplest singleton pattern without considering test isolation.

**Correct pattern:**
```apex
public class LoggerService {
    @TestVisible private static LoggerService instance;

    public static LoggerService getInstance() {
        if (instance == null) instance = new LoggerService();
        return instance;
    }

    // Required for test isolation
    @TestVisible
    public static void reset() {
        instance = null;
    }
}
```

**Detection hint:** Any singleton class used in test contexts that does not have a `reset()` or `clearInstance()` method.

---

## Anti-Pattern 5: Storing Log Level Minimum in Apex Code

**What the LLM generates:** `private static final LoggingLevel MIN_LEVEL = LoggingLevel.DEBUG;` hardcoded in the class.

**Why it happens:** Hardcoding is the simplest approach. LLMs do not consider the operational need to change log verbosity without a deployment.

**Correct pattern:** Store the minimum log level in Custom Metadata (`Logger_Config__mdt`). Read it at logger instantiation. This allows changing verbosity in production without a deployment or code change.

**Detection hint:** Any log level constant defined with `static final` in the Apex logger class rather than read from Custom Metadata or Custom Settings.
