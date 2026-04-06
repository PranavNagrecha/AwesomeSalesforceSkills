# LLM Anti-Patterns — Recursive Trigger Prevention

Common mistakes AI coding assistants make when generating or advising on preventing recursive Apex triggers.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using a single static Boolean guard that blocks ALL re-entry

**What the LLM generates:**

```apex
public class TriggerGuard {
    public static Boolean hasRun = false;
}

trigger AccountTrigger on Account (after update) {
    if (TriggerGuard.hasRun) return;
    TriggerGuard.hasRun = true;
    // process records
}
```

**Why it happens:** LLMs default to the simplest recursion guard — a static Boolean. But this blocks ALL re-entry for the entire transaction, not just re-entry for the same records. If an after-update trigger updates other Account records that legitimately need processing, those records are silently skipped.

**Correct pattern:**

```apex
public class TriggerGuard {
    private static Set<Id> processedIds = new Set<Id>();

    public static Boolean isAlreadyProcessed(Id recordId) {
        return processedIds.contains(recordId);
    }

    public static void markProcessed(Set<Id> recordIds) {
        processedIds.addAll(recordIds);
    }
}

trigger AccountTrigger on Account (after update) {
    List<Account> toProcess = new List<Account>();
    for (Account a : Trigger.new) {
        if (!TriggerGuard.isAlreadyProcessed(a.Id)) {
            toProcess.add(a);
        }
    }
    if (toProcess.isEmpty()) return;
    TriggerGuard.markProcessed(new Map<Id, Account>(toProcess).keySet());
    // process toProcess
}
```

**Detection hint:** `static Boolean.*hasRun|isRunning|alreadyRun` used as the sole recursion guard in a trigger.

---

## Anti-Pattern 2: Not resetting the guard between test methods

**What the LLM generates:**

```apex
public class TriggerGuard {
    public static Boolean hasRun = false;
}

// Test 1 sets hasRun = true
// Test 2 sees hasRun = true and the trigger is silently skipped
```

**Why it happens:** LLMs declare static guards but forget that static variables persist across test methods in the same test class execution (unless each test explicitly resets them). Test 2 may see leftover state from Test 1, causing tests to pass or fail depending on execution order.

**Correct pattern:**

```apex
public class TriggerGuard {
    @TestVisible
    private static Set<Id> processedIds = new Set<Id>();

    @TestVisible
    static void reset() {
        processedIds.clear();
    }
}

// In each test method:
@IsTest
static void testTrigger() {
    TriggerGuard.reset(); // Ensure clean state
    // ... test logic
}
```

**Detection hint:** Static recursion guard variables without a `@TestVisible` reset method, and test classes that do not reset the guard.

---

## Anti-Pattern 3: Guarding by operation type but not by record identity

**What the LLM generates:**

```apex
public class TriggerGuard {
    public static Boolean afterUpdateRun = false;
    public static Boolean afterInsertRun = false;
}
```

**Why it happens:** LLMs create per-event-type Boolean flags. This is slightly better than a single Boolean, but still blocks all records of that event type. If Account A's update triggers Account B's update, Account B is skipped because `afterUpdateRun` is already true.

**Correct pattern:**

```apex
public class TriggerGuard {
    private static Map<String, Set<Id>> processedByContext = new Map<String, Set<Id>>();

    public static Boolean hasBeenProcessed(String context, Id recordId) {
        if (!processedByContext.containsKey(context)) return false;
        return processedByContext.get(context).contains(recordId);
    }

    public static void markProcessed(String context, Set<Id> recordIds) {
        if (!processedByContext.containsKey(context)) {
            processedByContext.put(context, new Set<Id>());
        }
        processedByContext.get(context).addAll(recordIds);
    }
}

// Usage:
if (!TriggerGuard.hasBeenProcessed('AccountAfterUpdate', a.Id)) {
    // process
}
```

**Detection hint:** Multiple `static Boolean` flags named by trigger event (e.g., `afterUpdateRun`, `beforeInsertRun`) without record-level tracking.

---

## Anti-Pattern 4: Placing the guard inside the trigger body instead of the handler

**What the LLM generates:**

```apex
trigger AccountTrigger on Account (after update) {
    if (TriggerGuard.hasRun) return; // Guard in trigger file
    TriggerGuard.hasRun = true;
    AccountTriggerHandler handler = new AccountTriggerHandler();
    handler.afterUpdate(Trigger.new, Trigger.oldMap);
}
```

**Why it happens:** LLMs place the guard in the trigger body for simplicity. But if multiple entry points (trigger, service class, test) call the handler, only the trigger path is guarded. The guard should live in the handler or a shared utility, not the trigger body.

**Correct pattern:**

```apex
// Trigger: thin dispatcher only
trigger AccountTrigger on Account (after update) {
    new AccountTriggerHandler().afterUpdate(Trigger.new, Trigger.oldMap);
}

// Handler: owns the guard logic
public class AccountTriggerHandler {
    public void afterUpdate(List<Account> newList, Map<Id, Account> oldMap) {
        List<Account> unprocessed = new List<Account>();
        for (Account a : newList) {
            if (!RecursionGuard.isProcessed('AccountAfterUpdate', a.Id)) {
                unprocessed.add(a);
            }
        }
        if (unprocessed.isEmpty()) return;
        RecursionGuard.markProcessed('AccountAfterUpdate', new Map<Id, Account>(unprocessed).keySet());
        // process unprocessed
    }
}
```

**Detection hint:** Recursion guard logic (`if.*hasRun.*return`) inside a `.trigger` file rather than in a handler class.

---

## Anti-Pattern 5: Using try/finally to reset the guard, hiding exceptions

**What the LLM generates:**

```apex
public void afterUpdate(List<Account> accounts) {
    if (isRunning) return;
    isRunning = true;
    try {
        processAccounts(accounts);
    } finally {
        isRunning = false; // Reset even on exception
    }
}
```

**Why it happens:** LLMs use `try/finally` to ensure the guard resets even if processing throws an exception. But in a trigger context, an unhandled exception already rolls back the entire transaction, which means the guard reset is irrelevant — there will be no subsequent execution in the same transaction. The `finally` block adds complexity without value.

**Correct pattern:**

```apex
public void afterUpdate(List<Account> accounts) {
    Set<Id> newIds = new Set<Id>();
    for (Account a : accounts) {
        if (!processedIds.contains(a.Id)) {
            newIds.add(a.Id);
        }
    }
    if (newIds.isEmpty()) return;
    processedIds.addAll(newIds);
    // Let exceptions propagate naturally — transaction rolls back on failure
    processAccounts(accounts);
}
```

**Detection hint:** `try.*finally` block that only resets a recursion guard Boolean — unnecessary complexity.

---

## Anti-Pattern 6: Ignoring that Workflow Field Updates and Flows cause legitimate re-entry

**What the LLM generates:**

```apex
// "Prevent recursion" by blocking all after-update re-entry
// But a Workflow Field Update fires after update again legitimately
```

**Why it happens:** LLMs treat all re-entry as harmful recursion. In Salesforce, after-save Workflow Field Updates and after-save Record-Triggered Flows cause the trigger to fire again with the updated values. If the guard blocks this second pass, the trigger misses processing the workflow/flow-updated values.

**Correct pattern:**

```apex
// Allow re-entry for records that have changed since last processing
public void afterUpdate(List<Account> newList, Map<Id, Account> oldMap) {
    List<Account> toProcess = new List<Account>();
    for (Account a : newList) {
        // Only skip if we already processed this record AND the relevant field hasn't changed
        if (processedIds.contains(a.Id) && a.Status__c == lastProcessedStatus.get(a.Id)) {
            continue;
        }
        toProcess.add(a);
    }
    // Track what we processed
    for (Account a : toProcess) {
        processedIds.add(a.Id);
        lastProcessedStatus.put(a.Id, a.Status__c);
    }
}
```

**Detection hint:** Recursion guard that makes no distinction between self-DML recursion and legitimate platform-caused re-entry (workflow field updates, flow).
