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

## Anti-Pattern 2: Believing the guard leaks between test methods

**What the LLM generates:**

```apex
@IsTest
static void testTrigger() {
    TriggerGuard.reset(); // "statics persist across test methods"
    insert new Account(Name = 'A');
    Assert.isTrue(TriggerGuard.hasRun);
}
```

**Why it happens:** It is the most repeated claim in trigger-framework blog posts, and it is wrong. The
Apex Developer Guide is explicit: "Every test method, including the test setup method, runs as a separate
transaction. The static context of the test class is reinitialized before each transaction begins.
Therefore, static variable initializers and static blocks are executed fresh at the start of every test
method" (`apexdev` L41032–41035). The `reset()` call at the top of a test method is a no-op.

**What the belief costs:** an assistant that thinks cross-method leakage is *the* guard risk writes one
DML per test method and never writes the test that actually fails — two DML statements inside **one**
method, which is the same transaction and therefore the same static state. That is precisely the shape a
recursive save presents to the handler.

**Correct pattern:**

```apex
@IsTest
static void secondDmlInSameTransactionSeesTheGuard() {
    List<Account> accounts = [SELECT Id, Health_Score__c FROM Account LIMIT 5];
    for (Account a : accounts) { a.Health_Score__c = 71; }
    update accounts;                          // pass 1 — guard is populated here
    Integer afterFirst = AccountTriggerHandler.processedAccountIds.size();

    update accounts;                          // pass 2 — same transaction, same statics
    Assert.areEqual(afterFirst, AccountTriggerHandler.processedAccountIds.size(),
        'an unchanged re-save must not be counted as new work');

    for (Account a : accounts) { a.Health_Score__c = 72; }
    update accounts;                          // pass 3 — real change must be served
    Assert.areEqual(5, [SELECT COUNT() FROM Contact WHERE Account_Health_Score__c = 72]);
}
```

Keep a `@TestVisible reset()` on the guard anyway — not for cross-method hygiene, but so a single test
method can deliberately start a second scenario from clean state. The full version is
`identicalSecondPassSuppressedNewValueAllowed` in `references/code-examples.md`.

**Detection hint:** a test class whose every method performs exactly one DML statement, or a comment
asserting that statics survive between test methods.

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

## Anti-Pattern 5: Resetting the guard in a `finally` block, for the wrong reason

**What the LLM generates:**

```apex
public void afterUpdate(List<Account> accounts) {
    if (isRunning) return;
    isRunning = true;
    try {
        processAccounts(accounts);
    } finally {
        isRunning = false; // "reset even on exception"
    }
}
```

**Why it happens:** `try/finally` around mutable state is a reflex from other languages. Assistants then
justify it — or reject it — with the claim that an unhandled exception rolls the whole transaction back,
so the reset can never matter.

**Why that justification is wrong:** the transaction does not always end. With partial success allowed,
"triggers are fired during the first attempt and are fired again during subsequent attempts. Because
these trigger invocations are part of the same transaction, static class variables that are accessed by
the trigger aren't reset" (`apexdev` L15499–15501) — up to three attempts (`apexdev` L9070–9076). And
after a savepoint rollback, "static variables aren't reverted during a rollback. If you try to run the
trigger again, the static variables retain the values from the first run" (`apexdev` L8692–8693). So
there really are later passes in the same transaction that read this flag.

**Why the `finally` still doesn't fix it:** it resets a Boolean, and the problem is that the state is a
Boolean. On the retry the flag reads `false` and the *whole* subset is reprocessed, including rows that
already got their side effects on attempt one — the opposite failure. Duplicate work instead of missing
work.

**Correct pattern:**

```apex
public void afterUpdate(List<Account> accounts) {
    String context = RecursionGuard.contextKey('AccountTriggerHandler');
    List<Account> toProcess = new List<Account>();
    for (Account a : accounts) {
        String fingerprint = fingerprintOf(a);
        if (RecursionGuard.isProcessed(context, a.Id, fingerprint)) {
            continue;
        }
        RecursionGuard.markProcessed(context, a.Id, fingerprint);
        toProcess.add(a);
    }
    if (toProcess.isEmpty()) {
        return;
    }
    // No try/finally: per-record state needs no unwinding, and the retry subset
    // is decided by record identity rather than by one transaction-wide flag.
    processAccounts(toProcess);
}
```

**Detection hint:** a `finally` block whose only statement assigns `false` to a recursion flag.

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


---

## Anti-Pattern 7: Deriving re-entry state from governor-limit counters

**What the LLM generates:**

```apex
// "If no DML has run yet, this must be the first pass."
if (Limits.getDmlStatements() == 0) {
    processAccounts(Trigger.new);
}
```

**Why it happens:** limit counters look like a free, dependency-less signal for "how deep am I?", and in
a synchronous Apex DML the correlation roughly holds, so it passes every test.

**Why it breaks:** under Bulk API the two clocks run at different rates. "If a Bulk API request causes a
trigger to fire multiple times for chunks of 200 records, governor limits are reset between these
trigger invocations for the same HTTP request. Static variables aren't reset within the multiple trigger
invocations for the same Bulk API request" (`apexdev` L3789–3792). Every chunk therefore reads
`getDmlStatements() == 0` and declares itself the first pass, while the actual guard state has carried
over. The same divergence appears in partial-success retries, where "governor limits are reset to their
original state before the first attempt" (`apexdev` L9077–9078).

**Correct pattern:** state that answers "have I done this?" must be stored, not inferred — a keyed entry
in `RecursionGuard`. Limit counters answer "how much budget is left", which is a different question and
belongs to `apex/governor-limits`.

**Detection hint:** `Limits.get*()` appearing in a conditional that gates business logic rather than in
a log line or a batching decision.

---

## Anti-Pattern 8: Treating `TriggerHandler.skipOnce()` as a bulk-safe mute

**What the LLM generates:**

```apex
TriggerHandler.skipOnce('ContactTriggerHandler');
update contactsToSync;   // 500 rows
```

**Why it happens:** the method name reads like "suppress the next handler run", and for the single-record
demo in every code sample it behaves that way.

**Why it breaks:** `templates/apex/TriggerHandler.cls` implements the skip as
`skipOnceHandlers.remove(handlerName)` — a `Set.remove()` that returns `true` once and leaves the set
empty. A DML over 200 rows invokes the trigger once per batch (`apexdev` L15029–15033), so rows 201–500
run with no suppression at all. Worse, the failure is silent and volume-dependent: it passes in a
sandbox with 20 test rows and misfires on the first real load.

**Correct pattern:**

```apex
// Mark the child records in the record-keyed guard BEFORE the DML, so every batch
// of the resulting trigger invocation finds them already accounted for.
String childContext = 'ContactTriggerHandler.AFTER_UPDATE';
for (Contact c : contactsToSync) {
    RecursionGuard.markProcessed(childContext, c.Id, fingerprintOf(c));
}
update contactsToSync;
```

Use `skipOnce` only where the row count is provably at most 200. For a data load, switch the handler off
through `TriggerControl` instead — see `apex/apex-trigger-bypass-and-killswitch-patterns`.

**Detection hint:** `skipOnce(` immediately preceding a DML on a list whose size is not bounded in the
same method.
