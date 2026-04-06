# Examples — Callout Limits And Async Patterns

## Example 1: Resolving CalloutException After DML in a Trigger

**Context:** An Account trigger needed to send account data to an external ERP system via REST callout when an Account was inserted. The trigger used `Database.insert()` to create a related log record before the callout.

**Problem:** The trigger threw `System.CalloutException: You have uncommitted work pending` because the DML operation (log record insert) occurred before the callout in the same transaction.

**Solution:**
```apex
// Trigger: perform DML, then enqueue callout separately
trigger AccountTrigger on Account (after insert) {
    List<Id> accountIds = new List<Id>();
    for (Account a : Trigger.new) accountIds.add(a.Id);
    System.enqueueJob(new AccountSyncQueueable(accountIds));
}

// Queueable: runs in a new transaction — no uncommitted DML
public class AccountSyncQueueable implements Queueable, Database.AllowsCallouts {
    private List<Id> ids;
    public AccountSyncQueueable(List<Id> ids) { this.ids = ids; }

    public void execute(QueueableContext ctx) {
        List<Account> accounts = [SELECT Id, Name, BillingCountry FROM Account WHERE Id IN :ids];
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:ERPNamedCredential/api/accounts');
        req.setMethod('POST');
        req.setBody(JSON.serialize(accounts));
        req.setTimeout(30000);
        Http http = new Http();
        HttpResponse res = http.send(req);
        // handle response
    }
}
```

**Why it works:** The trigger enqueues the Queueable after the DML completes and the transaction commits. The Queueable executes in a fresh Apex transaction with no uncommitted DML, so the callout succeeds. The `Database.AllowsCallouts` interface declaration is required to allow callouts from a Queueable context.

---

## Example 2: Chained Queueable Callouts for Sequential API Calls

**Context:** An integration needed to call three sequential external APIs where each call's result was required as input to the next: step 1 = authenticate and get token, step 2 = create order using token, step 3 = confirm order using order ID.

**Problem:** Three sequential callouts with data dependencies between them could not be done in a single trigger context (DML before callout restriction) and could not be done in a single @future (no chaining, no sObject parameters).

**Solution:**
```apex
// Step 1: Get auth token
public class Step1AuthQueueable implements Queueable, Database.AllowsCallouts {
    public void execute(QueueableContext ctx) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:ExternalAPI/auth');
        req.setMethod('POST');
        HttpResponse res = new Http().send(req);
        String token = (String) ((Map<String,Object>) JSON.deserializeUntyped(res.getBody())).get('token');
        // Chain to step 2, passing token as parameter
        System.enqueueJob(new Step2CreateOrderQueueable(token));
    }
}

// Step 2: Create order using token
public class Step2CreateOrderQueueable implements Queueable, Database.AllowsCallouts {
    private String token;
    public Step2CreateOrderQueueable(String token) { this.token = token; }
    public void execute(QueueableContext ctx) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:ExternalAPI/orders');
        req.setMethod('POST');
        req.setHeader('Authorization', 'Bearer ' + token);
        HttpResponse res = new Http().send(req);
        String orderId = (String) ((Map<String,Object>) JSON.deserializeUntyped(res.getBody())).get('orderId');
        System.enqueueJob(new Step3ConfirmOrderQueueable(token, orderId));
    }
}
```

**Why it works:** Each Queueable executes in a separate Apex transaction with its own 100-callout limit. Chaining via `System.enqueueJob()` within `execute()` passes data between steps without shared state. @future could not accomplish this — it cannot accept sObject parameters and cannot chain.

---

## Anti-Pattern: Using @future for Callouts Requiring sObject Parameters

**What practitioners do:** Use `@future(callout=true)` for callouts that need to pass Account, Contact, or other sObject data to the external system.

**What goes wrong:** `@future` methods cannot accept sObject parameters — they accept only primitives and collections of primitives. Practitioners work around this by querying the sObject inside the @future using an ID parameter, but this adds an extra SOQL query and fails if the record was modified between the enqueue and execution.

**Correct approach:** Use `Queueable implements Database.AllowsCallouts` instead. Queueable accepts any parameter type including sObjects, Lists, and Maps. Pass the full sObject data (or the IDs + required fields) to the Queueable constructor and query only what's needed in `execute()`.
