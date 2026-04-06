# LLM Anti-Patterns — Callout Limits And Async Patterns

Common mistakes AI coding assistants make when generating or advising on Callout Limits And Async Patterns.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Making a Callout Directly After DML in a Trigger

**What the LLM generates:** A trigger that performs a DML insert (e.g., logging record) and then immediately makes an HttpRequest callout within the same execute block.

**Why it happens:** LLMs generate linear trigger code following the order of operations without knowing the Salesforce-specific constraint that uncommitted DML blocks callouts. In most languages, DML and HTTP calls can coexist in any order.

**Correct pattern:**
```apex
// WRONG: DML before callout in same transaction
trigger AccountTrigger on Account (after insert) {
    insert new Log__c(Event__c = 'Account created');
    HttpRequest req = new HttpRequest();
    // ^ System.CalloutException: You have uncommitted work pending
}

// CORRECT: Enqueue callout after DML
trigger AccountTrigger on Account (after insert) {
    insert new Log__c(Event__c = 'Account created');
    System.enqueueJob(new AccountCalloutQueueable(Trigger.newMap.keySet()));
}
```

**Detection hint:** Any trigger that contains both a DML operation (insert/update/delete/upsert) and an `HttpRequest` or `Http` instantiation in the same execute block.

---

## Anti-Pattern 2: Using @future with sObject Parameters

**What the LLM generates:** A `@future(callout=true)` method with an Account, Contact, or other sObject as a parameter.

**Why it happens:** LLMs know @future is used for async callouts and generate method signatures with the most convenient parameter types without knowing the Apex compiler restriction that @future cannot accept sObjects.

**Correct pattern:**
```apex
// WRONG: @future cannot accept sObject parameters
@future(callout=true)
public static void syncAccount(Account a) { // Compiler error
    // ...
}

// CORRECT: Use Queueable instead
public class AccountSyncQueueable implements Queueable, Database.AllowsCallouts {
    private Account account;
    public AccountSyncQueueable(Account a) { this.account = a; }
    public void execute(QueueableContext ctx) { /* callout logic */ }
}
```

**Detection hint:** Any `@future(callout=true)` method signature with an sObject (Account, Contact, Lead, or any `__c`) as a parameter type.

---

## Anti-Pattern 3: Using Continuation in a Trigger or Queueable

**What the LLM generates:** Code instantiating `System.Continuation` or `new Continuation(timeout)` inside a trigger handler or a Queueable `execute()` method.

**Why it happens:** LLMs know Continuation handles long-running async callouts and apply it broadly, without knowing the restriction that it is only available in LWC/Aura/Visualforce controller contexts.

**Correct pattern:**
```apex
// Continuation is ONLY valid in @AuraEnabled controller methods
// or Visualforce controller methods
@AuraEnabled
public static Object startLongCallout() {
    Continuation c = new Continuation(60);
    c.continuationMethod = 'handleCallbackResult';
    // add requests...
    return c;
}
```

**Detection hint:** `new Continuation(` appearing inside a trigger class, a class implementing `Queueable`, or a class implementing `Database.Batchable`.

---

## Anti-Pattern 4: Assuming Async Context Increases the 100-Callout Limit

**What the LLM generates:** Advice stating "use Queueable instead of synchronous Apex to get more callouts" without clarifying that the 100-callout limit applies equally to async contexts.

**Why it happens:** LLMs know that async contexts have different governor limits (heap, CPU) and incorrectly generalize this to callout limits. The callout limit does NOT increase in async contexts.

**Correct pattern:**
```
Each Apex transaction (synchronous OR async) is limited to 100 callouts.
To process more than 100 callout-requiring records:
1. Use Batch Apex — each execute() chunk is a separate transaction with 100 callouts
2. Chain Queueables — each link in the chain is a separate transaction with 100 callouts
```

**Detection hint:** Any statement claiming async context "gives more callouts" or "removes the callout limit."

---

## Anti-Pattern 5: Thread.sleep() Suggestion for Callout Throttling

**What the LLM generates:** Apex code using `Thread.sleep(1000)` or similar Java-style sleep to introduce a delay between callouts for rate limiting purposes.

**Why it happens:** Java/C# bleed — in those languages, `Thread.sleep()` is a standard pattern for implementing delays. Apex does not have a `Thread.sleep()` method. The LLM generates it by analogy.

**Correct pattern:**
```apex
// Thread.sleep() does not exist in Apex — compiler error
// For rate limiting between callouts, use Queueable chaining with scheduled delays
// or implement rate-limit tracking via Custom Metadata and retry on HTTP 429:

HttpResponse res = http.send(req);
if (res.getStatusCode() == 429) {
    // Re-enqueue with a delay by scheduling a future Queueable
    System.enqueueJob(new RetryQueueable(requestData, retryCount + 1));
    return;
}
```

**Detection hint:** Any mention of `Thread.sleep`, `wait()`, or `sleep(` in an Apex context.
