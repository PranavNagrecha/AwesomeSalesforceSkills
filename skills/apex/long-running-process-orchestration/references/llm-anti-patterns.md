# LLM Anti-Patterns — Long-Running Process Orchestration

Common mistakes AI coding assistants make when generating or advising on long-running Apex orchestration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using Static Variables To Share State Across Chained Queueables

**What the LLM generates:** A Queueable class with a `public static Map<String, Object> processState` variable that is populated in step 1 and expected to be present in step 2:

```apex
// WRONG
public class StepOneQueueable implements Queueable {
    public static Map<String, Object> state = new Map<String, Object>();

    public void execute(QueueableContext ctx) {
        state.put('orderId', '001...');
        state.put('step', 2);
        System.enqueueJob(new StepTwoQueueable()); // state expected to be shared
    }
}
```

**Why it happens:** LLMs are trained heavily on synchronous Java and Apex patterns where static variables persist for the duration of the application lifecycle. The async transaction boundary concept — that each Queueable runs in a completely fresh execution context — is underrepresented in training data compared to synchronous code examples.

**Correct pattern:**

```apex
// CORRECT — state travels through constructor
public class StepOneQueueable implements Queueable {
    public void execute(QueueableContext ctx) {
        ProcessState state = new ProcessState();
        state.orderId = '001...';
        state.currentStep = 2;
        System.enqueueJob(new StepTwoQueueable(state));
    }
}
```

**Detection hint:** Search generated code for `static` field declarations on Queueable classes used in chains. Any static field used for inter-step communication is incorrect.

---

## Anti-Pattern 2: Setting `MaximumQueueableStackDepth` Only On The First Enqueue

**What the LLM generates:** The LLM sets `AsyncOptions` once when launching the chain and omits it on all subsequent `enqueueJob` calls inside the chain, because it assumes the option propagates:

```apex
// WRONG — only set on first call
AsyncOptions opts = new AsyncOptions();
opts.MaximumQueueableStackDepth = 5;
System.enqueueJob(new StepOneQueueable(state), opts); // Step 1 has the guard

// Inside StepOneQueueable.execute():
System.enqueueJob(new StepTwoQueueable(state)); // No opts — guard is gone
```

**Why it happens:** The behavior is counterintuitive. Developers and LLMs expect that a limit set on a chain's root would be enforced for all descendants. The Apex platform does not implement it this way — each `enqueueJob` call is independent.

**Correct pattern:**

```apex
// CORRECT — opts on every enqueueJob in the chain
AsyncOptions opts = new AsyncOptions();
opts.MaximumQueueableStackDepth = 5;
System.enqueueJob(new StepTwoQueueable(state), opts);
```

**Detection hint:** Count occurrences of `System.enqueueJob(` in the generated code. Compare to occurrences of `AsyncOptions`. If the counts differ (and the difference is not the initial launch call), the guard is missing on some chain links.

---

## Anti-Pattern 3: Attaching The Finalizer After Code That Can Throw

**What the LLM generates:** A Queueable that performs SOQL or DML before calling `System.attachFinalizer()`:

```apex
// WRONG
public void execute(QueueableContext ctx) {
    List<Account> accounts = [SELECT Id FROM Account WHERE ...]; // could throw
    doSomethingRisky(accounts);
    System.attachFinalizer(new MyFinalizer(state)); // too late — exception above bypasses this
}
```

**Why it happens:** LLMs generate code top-to-bottom following logical flow. Since the Finalizer is conceptually about "what to do at the end," the LLM naturally places it near the end of `execute()`. The critical requirement — that `attachFinalizer` must precede any code that could throw — is a non-obvious platform constraint.

**Correct pattern:**

```apex
// CORRECT — Finalizer attached before any risky code
public void execute(QueueableContext ctx) {
    System.attachFinalizer(new MyFinalizer(state)); // first line
    List<Account> accounts = [SELECT Id FROM Account WHERE ...];
    doSomethingRisky(accounts);
}
```

**Detection hint:** In the generated Queueable `execute()` method, verify that `System.attachFinalizer(` appears before the first SOQL query, DML operation, or callout. Any other ordering is incorrect.

---

## Anti-Pattern 4: Enqueuing Multiple Child Jobs From A Single `execute()` Call

**What the LLM generates:** Fan-out logic inside a Queueable that loops and calls `System.enqueueJob()` for each child:

```apex
// WRONG
public void execute(QueueableContext ctx) {
    List<Id> groupIds = getGroupsToProcess();
    for (Id groupId : groupIds) {
        System.enqueueJob(new ProcessGroupQueueable(groupId)); // fails on second iteration
    }
}
```

**Why it happens:** In most programming environments, spawning parallel workers in a loop is idiomatic. The single-child rule of Queueable Apex is a Salesforce-specific constraint that is not widely known and is often omitted from LLM training examples.

**Correct pattern:**

```apex
// CORRECT — use Platform Events for fan-out
List<ProcessGroup__e> events = new List<ProcessGroup__e>();
for (Id groupId : groupIds) {
    events.add(new ProcessGroup__e(GroupId__c = groupId));
}
List<Database.SaveResult> results = EventBus.publish(events);
// Subscriber trigger handles each event and enqueues one Queueable per event
```

**Detection hint:** Search for loops containing `System.enqueueJob(` in the generated code. Any loop with multiple `enqueueJob` calls violates the single-child rule and will throw `System.LimitException` at runtime.

---

## Anti-Pattern 5: Publishing A Step-Advance Platform Event Inside A DML Transaction That May Roll Back

**What the LLM generates:** A Queueable that publishes a next-step Platform Event inside a try/catch block before catching or after throwing an exception from DML:

```apex
// WRONG
public void execute(QueueableContext ctx) {
    try {
        insert newRecords; // may partially succeed, then other DML throws
        EventBus.publish(new StepAdvance__e(Step__c = 'NextStep')); // published
        insert riskyRecords; // throws — rolls back insert above, but event is delivered
    } catch (DmlException e) {
        // newRecords DML is rolled back, but the event was already delivered
    }
}
```

**Why it happens:** LLMs apply general "publish then process" patterns from event-driven architectures without knowing the Salesforce-specific behavior: Platform Events are durable even when their publishing transaction rolls back. This is the opposite of how most databases handle message publishing within transactions.

**Correct pattern:**

```apex
// CORRECT — publish only after all DML in the step succeeds
public void execute(QueueableContext ctx) {
    System.attachFinalizer(new StepFinalizer(state));
    insert newRecords;
    insert riskyRecords; // if this throws, Finalizer handles recovery — no event was published
    // Only if we reach here did all DML succeed
    Database.SaveResult result = EventBus.publish(new StepAdvance__e(Step__c = 'NextStep'));
    if (!result.isSuccess()) {
        throw new EventBusException('Step advance event failed: ' + result.getErrors()[0].getMessage());
    }
}
```

**Detection hint:** Look for `EventBus.publish(` calls that appear before all DML in the `execute()` method, or inside try blocks where later DML can cause rollback. The publish call should be the final operation in `execute()` after all DML has been confirmed successful.

---

## Anti-Pattern 6: Using `@future` Methods As Steps In An Orchestration Chain

**What the LLM generates:** A sequence of `@future` methods calling each other to simulate a chain:

```apex
// WRONG
@future(callout=true)
public static void stepOne(Id recordId) {
    doCallout(recordId);
    stepTwo(recordId); // cannot call @future from @future
}

@future
public static void stepTwo(Id recordId) { ... }
```

**Why it happens:** `@future` is simpler syntactically and LLMs encounter it frequently in training data. The mutual-exclusion rule — `@future` cannot call `@future` — and the absence of Finalizers, chaining, state passing, and depth control are non-obvious constraints.

**Correct pattern:**

```apex
// CORRECT — use Queueable for chainable multi-step orchestration
public class StepOneQueueable implements Queueable, Database.AllowsCallouts {
    public void execute(QueueableContext ctx) {
        System.attachFinalizer(new StepFinalizer(state));
        doCallout(state.recordId);
        System.enqueueJob(new StepTwoQueueable(state));
    }
}
```

**Detection hint:** Presence of `@future` annotations alongside an orchestration design with multiple dependent steps. Any `@future` method that calls or references another `@future` method is an immediate red flag.

---

## Anti-Pattern 7: Stating the Per-Transaction Callout Budget as 10 Seconds

**What the LLM generates:**

Prose in an architecture or design doc:

> "Salesforce imposes hard transaction limits: 60,000 ms CPU, 100 SOQL, 150 DML, 12 MB heap, and a 10-second total callout timeout. Because our sync step makes four callouts averaging four seconds, we must split it across four Queueables."

…and the sibling arithmetic error, "each callout can run up to 10 seconds, for a combined 120-second total".

**Why it happens:** 10 seconds is the documented **default** timeout of a single `HttpRequest`, which is the value developers hit first and therefore the value that circulates as "the callout limit". Slotted into a per-transaction limits table alongside CPU, SOQL, DML, and heap — which genuinely *are* per-transaction — it looks native. The second variant is worse because it back-rationalises: the author remembers the correct 120-second total, remembers 10 seconds and 100 callouts, and invents a product relationship to connect them. 100 × 10 = 1,000, not 120, so the sentence refutes itself, and it still ships.

**Correct pattern:** The per-transaction limit is **120 seconds cumulative across all callouts** — "The maximum cumulative timeout for callouts by a single Apex transaction is 120 seconds" — alongside a separate limit of 100 callouts. Per callout, 10 seconds is only the default; `setTimeout()` accepts 1 to 120,000 ms, identically in synchronous and asynchronous Apex. The two limits are independent: one 120-second callout exhausts the transaction budget while using 1 of 100 callouts; 100 callouts averaging 1.2 s exhaust it the other way. Orchestration splits are justified by the 120-second budget, the 100-callout count, CPU, or heap — never by a 10-second figure.

**Detection hint:** in any limits table or bulleted limits list, flag `10[- ]?second` appearing next to `total`, `cumulative`, or `transaction`; the correct value in that position is always 120 seconds. Separately, flag any sentence containing both a per-callout duration and the word `combined` or `total` where the stated product is not the product of its operands — a self-refuting arithmetic claim is a reliable fabrication marker. Correct text pairs `120 seconds` with `cumulative`/`transaction` and `10 seconds` with `default`.
