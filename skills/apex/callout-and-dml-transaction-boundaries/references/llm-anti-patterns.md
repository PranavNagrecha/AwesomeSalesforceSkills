# LLM Anti-Patterns — Callout and DML Transaction Boundaries

Common mistakes AI coding assistants make when generating or advising on callout and DML transaction boundaries.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Placing DML Before Callout in the Same Synchronous Method

**What the LLM generates:**

```apex
public void syncAccount(Account acc) {
    insert acc;  // DML first
    HttpRequest req = new HttpRequest();
    req.setEndpoint('callout:My_Service/api/accounts');
    req.setMethod('POST');
    req.setBody(JSON.serialize(acc));
    new Http().send(req);  // BOOM — uncommitted work pending
}
```

**Why it happens:** LLMs follow a natural "save then notify" narrative flow. In most programming languages, this ordering is fine. Salesforce's transaction model is unusual in prohibiting callouts after DML.

**Correct pattern:**

```apex
public void syncAccount(Account acc) {
    // Callout FIRST — no DML yet
    HttpRequest req = new HttpRequest();
    req.setEndpoint('callout:My_Service/api/accounts');
    req.setMethod('POST');
    req.setBody(JSON.serialize(new Map<String, String>{'name' => acc.Name}));
    HttpResponse res = new Http().send(req);
    // Parse response, THEN DML
    acc.External_Id__c = parseId(res);
    insert acc;
}
```

**Detection hint:** Look for `insert|update|upsert|delete|Database\.(insert|update|upsert|delete)` appearing before `new Http\(\)\.send\(` in the same method without an async boundary.

---

## Anti-Pattern 2: Making a Callout Directly in a Trigger Handler

**What the LLM generates:**

```apex
public class AccountTriggerHandler {
    public static void afterInsert(List<Account> newAccounts) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:ERP/api/sync');
        req.setMethod('POST');
        req.setBody(JSON.serialize(newAccounts));
        new Http().send(req);  // Fails — trigger DML is uncommitted
    }
}
```

**Why it happens:** LLMs do not always account for the fact that the triggering DML (the insert that fired the trigger) is itself uncommitted work. There is no explicit DML statement in the handler, so the LLM assumes it is safe.

**Correct pattern:**

```apex
public class AccountTriggerHandler {
    public static void afterInsert(List<Account> newAccounts) {
        List<Id> ids = new List<Id>();
        for (Account a : newAccounts) { ids.add(a.Id); }
        System.enqueueJob(new AccountErpSyncQueueable(ids));
    }
}
```

**Detection hint:** Any `Http().send()` or `HttpRequest` inside a method named `afterInsert`, `afterUpdate`, `beforeInsert`, `beforeUpdate`, or inside a trigger body.

---

## Anti-Pattern 3: Queueable That Makes Callouts Without Database.AllowsCallouts

**What the LLM generates:**

```apex
public class SyncQueueable implements Queueable {
    // Missing: Database.AllowsCallouts
    public void execute(QueueableContext ctx) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:Service/api');
        new Http().send(req);  // Runtime error — callouts not allowed
    }
}
```

**Why it happens:** LLMs remember that Queueable is the correct async boundary but forget the `Database.AllowsCallouts` interface declaration. Without it, the platform blocks the callout entirely.

**Correct pattern:**

```apex
public class SyncQueueable implements Queueable, Database.AllowsCallouts {
    public void execute(QueueableContext ctx) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:Service/api');
        new Http().send(req);
    }
}
```

**Detection hint:** Class implements `Queueable` but not `Database.AllowsCallouts`, and the `execute` method contains `Http` or `HttpRequest`.

---

## Anti-Pattern 4: Using Database.rollback() to Clear Uncommitted Work Before Callout

**What the LLM generates:**

```apex
Savepoint sp = Database.setSavepoint();
insert someRecord;
Database.rollback(sp);
// LLM assumes the rollback clears uncommitted work
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:Service/api');
new Http().send(req);  // Still fails — rollback does not reset the flag
```

**Why it happens:** In relational databases, a rollback undoes the transaction state. LLMs apply this mental model to Salesforce, but Salesforce tracks that DML was attempted regardless of rollback.

**Correct pattern:**

```apex
// Do not rely on rollback. Move the callout to a Queueable
// or reorder so the callout happens before any DML.
```

**Detection hint:** `Database.rollback` appearing in the same method before a `Http().send()` call.

---

## Anti-Pattern 5: Passing sObjects to @future Methods for Post-DML Callouts

**What the LLM generates:**

```apex
@future(callout=true)
public static void syncToExternal(Account acc) {
    // Compile error — @future cannot accept sObject parameters
    HttpRequest req = new HttpRequest();
    req.setEndpoint('callout:Service/api');
    req.setBody(JSON.serialize(acc));
    new Http().send(req);
}
```

**Why it happens:** LLMs generate @future as a quick async fix but forget the sObject parameter restriction. Even when corrected to use IDs, @future still cannot chain or be monitored easily, making Queueable the better choice.

**Correct pattern:**

```apex
// Use Queueable instead
public class SyncQueueable implements Queueable, Database.AllowsCallouts {
    private List<Id> recordIds;
    public SyncQueueable(List<Id> recordIds) { this.recordIds = recordIds; }
    public void execute(QueueableContext ctx) {
        List<Account> accs = [SELECT Id, Name FROM Account WHERE Id IN :recordIds];
        // Make callout with queried data
    }
}
```

**Detection hint:** `@future` method signature containing an sObject type parameter, or `@future(callout=true)` used where Queueable would be more appropriate.

---

## Anti-Pattern 6: Assuming EventBus.publish() Is Not DML

**What the LLM generates:**

```apex
EventBus.publish(new My_Event__e(Data__c = 'payload'));
// LLM assumes this is not DML
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:Service/api');
new Http().send(req);  // Fails — EventBus.publish is DML
```

**Why it happens:** Platform events feel like messaging, not database operations. LLMs do not classify `EventBus.publish()` as DML, but Salesforce treats it as such for transaction boundary purposes.

**Correct pattern:**

```apex
// Callout first, then publish
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:Service/api');
HttpResponse res = new Http().send(req);
EventBus.publish(new My_Event__e(Data__c = res.getBody()));
```

**Detection hint:** `EventBus.publish` appearing before `Http().send()` in the same transaction.
