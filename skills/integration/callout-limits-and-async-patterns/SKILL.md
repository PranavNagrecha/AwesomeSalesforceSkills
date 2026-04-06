---
name: callout-limits-and-async-patterns
description: "Use when designing or troubleshooting Apex callouts that approach governor limits: choosing between synchronous callouts, @future, Queueable, Continuation, or async chaining strategies. NOT for HTTP request construction or Named Credential setup (use named-credentials-setup)."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
triggers:
  - "how many callouts can I make in a single Apex transaction"
  - "System.CalloutException after uncommitted DML in Apex"
  - "how to make more than 100 callouts from a trigger"
  - "Continuation class vs Queueable for long-running HTTP requests in Salesforce"
  - "how to chain callouts asynchronously without hitting governor limits"
tags:
  - callouts
  - governor-limits
  - async-apex
  - continuation
  - queueable
inputs:
  - "Callout volume required per transaction (number of records, number of endpoints)"
  - "Synchronous vs asynchronous context (trigger, batch, LWC controller, REST endpoint)"
  - "Whether DML operations occur before or after the callout"
outputs:
  - "Callout pattern recommendation (sync, @future, Queueable, Continuation)"
  - "Governor limit analysis for the proposed callout design"
  - "Code pattern for the recommended async callout approach"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Callout Limits And Async Patterns

This skill activates when a practitioner needs to design or debug Apex callouts that are approaching governor limits or require an asynchronous execution model. It covers the decision between synchronous, `@future`, Queueable, Continuation, and chained async callout patterns, including the DML-before-callout restriction.

---

## Before Starting

Gather this context before working on anything in this domain:

- Identify the execution context: synchronous trigger, batch Apex, LWC/Aura controller, REST endpoint, or scheduled Apex — this determines which async callout options are available.
- Count the expected number of callouts per transaction and whether they are to a single endpoint or multiple distinct endpoints.
- Confirm whether DML occurs before the callout in the transaction — if yes, the callout will throw `System.CalloutException` and must be moved to an async context.

---

## Core Concepts

### Synchronous Callout Governor Limits

Per Apex transaction limits for callouts (from Apex Governor Limits documentation):
- **100 callouts** per transaction (synchronous or asynchronous)
- **120 seconds** maximum timeout per individual callout (configurable via `HttpRequest.setTimeout()`)
- **10 MB** maximum response body size per callout

These limits apply equally to synchronous and asynchronous transactions. An async context (Queueable, Batch, @future) does NOT increase the 100-callout limit — it only changes the execution context.

### DML-Before-Callout Rule

If DML operations (insert, update, delete, upsert) are executed before a callout in the same transaction, the callout throws `System.CalloutException: You have uncommitted work pending`. This is a hard platform restriction.

**The fix:** Move the callout to an async context by enqueuing a Queueable (with `callout=true`) after the DML completes. The Queueable runs in a new transaction where no uncommitted DML exists.

```apex
// Trigger: DML first, then enqueue callout
trigger AccountTrigger on Account (after insert) {
    List<Id> newAccountIds = new List<Id>();
    for (Account a : Trigger.new) newAccountIds.add(a.Id);
    System.enqueueJob(new AccountCalloutQueueable(newAccountIds));
}
```

### @future vs Queueable for Callouts

`@future(callout=true)` is the simplest async callout mechanism but has significant restrictions:
- Cannot pass sObject parameters (only primitives and collections of primitives)
- Cannot chain — no way to enqueue another @future from within a @future
- Cannot be called from Batch Apex

`Queueable with callout=true` is the preferred approach for all new code:
- Accepts any type as a parameter (sObjects, custom objects, Maps)
- Can chain: call `System.enqueueJob()` from within `execute()` to create a callout chain
- Works from Batch Apex `execute()` method (one enqueue per execute call)

### Continuation Class for Long-Running LWC/Aura Callouts

The `Continuation` class enables asynchronous callouts from LWC, Aura, and Visualforce controllers when the callout may take longer than the synchronous response window. Key behavior:
- Maximum timeout per Continuation: 120 seconds
- Maximum 3 callout requests per Continuation instance
- Maximum 3 Continuations chained (3 × 3 requests = 9 total, with new Apex transaction limits resetting on each callback)
- NOT available from triggers, batch Apex, or Queueable — LWC/Aura/VF controllers only

Each callback in a Continuation chain runs in a fresh Apex transaction with its own governor limits.

---

## Common Patterns

### Queueable Callout After DML

**When to use:** A trigger or synchronous Apex class needs to make a callout after performing DML.

**How it works:**
```apex
public class AccountCalloutQueueable implements Queueable, Database.AllowsCallouts {
    private List<Id> accountIds;

    public AccountCalloutQueueable(List<Id> accountIds) {
        this.accountIds = accountIds;
    }

    public void execute(QueueableContext ctx) {
        List<Account> accounts = [SELECT Id, Name FROM Account WHERE Id IN :accountIds];
        for (Account a : accounts) {
            HttpRequest req = new HttpRequest();
            req.setEndpoint('callout:MyNamedCredential/api/sync');
            req.setMethod('POST');
            req.setBody(JSON.serialize(a));
            req.setTimeout(30000);
            new Http().send(req);
        }
    }
}
```

**Why not @future:** `@future` cannot accept sObject parameters and cannot chain. Queueable is the modern replacement with no restrictions on parameter types.

### Continuation for LWC Long-Running Callout

**When to use:** An LWC component needs to call an external API that may take 10–30 seconds to respond, and a synchronous Apex call would time out the LWC request.

**How it works:**
```apex
// Apex controller
public class ContinuationController {
    @AuraEnabled
    public static Object invokeLongCall(String endpoint) {
        Continuation c = new Continuation(40); // 40 second timeout
        c.continuationMethod = 'handleResponse';
        HttpRequest req = new HttpRequest();
        req.setEndpoint(endpoint);
        req.setMethod('GET');
        c.addHttpRequest(req);
        return c;
    }

    @AuraEnabled
    public static String handleResponse(List<String> labels, Object state) {
        HttpResponse res = Continuation.getResponse(labels[0]);
        return res.getBody();
    }
}
```

**Why not Queueable:** Queueable cannot return a result to an LWC component — it runs fully async with no callback to the UI. Continuation keeps the user session alive and returns the result to the LWC once the callout completes.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Callout needed after DML in same transaction | Queueable with `Database.AllowsCallouts` | Moves callout to new transaction where no uncommitted DML exists |
| Simple fire-and-forget callout, no chaining needed | `@future(callout=true)` | Simpler to implement; acceptable for basic integrations |
| Chained callouts (callout → process result → callout again) | Queueable chain via `System.enqueueJob()` in `execute()` | @future cannot chain; Queueable supports sequential chaining |
| LWC/Aura component needs callout result in UI | Continuation class | Returns result to UI session; supports up to 120s wait |
| Trigger needs to call out to 150+ endpoints (> 100 limit) | Batch Apex + Queueable per batch chunk | Split records into batch chunks; each chunk's Queueable gets 100 fresh callout slots |
| Callout from Batch Apex `execute()` | Queueable with callouts, enqueued once per `execute()` call | Direct callouts in Batch execute are allowed if `Database.AllowsCallouts` is implemented |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Identify the execution context: synchronous trigger, Batch Apex, LWC controller, scheduled Apex, or REST endpoint.
2. Check whether DML occurs before the callout in the same transaction — if yes, the callout must move to a Queueable.
3. Count the required callouts per transaction — if over 100, split into Batch Apex chunks or multiple Queueable chains.
4. Select the appropriate callout pattern from the decision table above.
5. Implement the selected pattern using Named Credentials for endpoint configuration (never hardcode endpoint URLs in Apex).
6. Test governor limit behavior with `Limits.getCallouts()` assertions in test classes, using `HttpCalloutMock` to simulate responses.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] No callout occurs after uncommitted DML in the same transaction
- [ ] `@future(callout=true)` only used for simple fire-and-forget with no sObject parameters
- [ ] Queueable used instead of @future for any chaining, sObject parameters, or Batch context
- [ ] Continuation used only for LWC/Aura/Visualforce — not for triggers or Queueables
- [ ] Total callout count per transaction is under 100 (verified by design — not relying on runtime limit checks)
- [ ] Named Credentials used for all callout endpoints — no hardcoded URLs in Apex

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Async context does NOT reset the 100-callout limit per Queueable** — Each Queueable execution gets 100 callouts, not per-chain. A chain of 5 Queueables gets 5 × 100 = 500 total callouts but 100 per Queueable execution. Attempting to make 150 callouts in a single Queueable `execute()` still fails.
2. **Continuation is not available outside LWC/Aura/Visualforce** — Calling the Continuation class from a trigger, Batch Apex, or Queueable throws a runtime exception. It is exclusively for controller classes backing UI components.
3. **DML-before-callout error is transaction-scoped, not method-scoped** — The restriction applies across the entire Apex transaction, including any helper methods called earlier in the trigger or class chain. Even if the DML was done by a completely different class called earlier in the transaction, the callout will still fail.
4. **Chained Queueables have a maximum depth of 5 per transaction** — You can call `System.enqueueJob()` from within a Queueable's `execute()` method, but the total chain depth per originating transaction is limited to avoid infinite chains. In sandboxes, only one Queueable level is executed synchronously (others are queued) — this affects testing.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Callout pattern recommendation | Selected pattern (sync, @future, Queueable, Continuation) with rationale |
| Governor limit analysis | Calculated callout count per transaction vs limit |
| Queueable callout implementation | Apex class implementing Queueable + Database.AllowsCallouts |
| Continuation implementation | Apex controller method and callback for LWC async callout |

---

## Related Skills

- named-credentials-setup — configuring Named Credentials for the callout endpoint
- retry-and-backoff-patterns — handling callout failures with retry logic
- apex-queueable-patterns — general Queueable design patterns beyond callouts
