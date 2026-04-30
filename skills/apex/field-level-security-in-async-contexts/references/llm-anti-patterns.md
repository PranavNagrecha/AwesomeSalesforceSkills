# LLM Anti-Patterns — FLS in Async Contexts

Common mistakes AI coding assistants make when generating async Apex that needs to respect FLS.

## Anti-Pattern 1: Claiming `WITH USER_MODE` enforces "the user's" FLS in any async context

**What the LLM generates:**

> "The Queueable runs in user mode because of `WITH USER_MODE`, so the original user's FLS is enforced."

**Why it happens:** Conflates the SOQL clause's name with its actual semantics. `WITH USER_MODE` evaluates against `UserInfo.getUserId()` at execution time — it does not "remember" any other user.

**Correct pattern:**

```apex
// Capture originating user explicitly
private final Id originatingUserId;
public MyQueueable(...) {
    this.originatingUserId = UserInfo.getUserId();
}

public void execute(QueueableContext qc) {
    // Assert running user matches; only THEN is WITH USER_MODE meaningful
    if (UserInfo.getUserId() != originatingUserId) throw new SecurityException(...);
    [SELECT ... FROM ... WITH USER_MODE];
}
```

**Detection hint:** Any async Apex (`implements Queueable | Schedulable | Database.Batchable`) that uses `WITH USER_MODE` without first asserting `UserInfo.getUserId() == capturedOriginatingId`.

---

## Anti-Pattern 2: Using `WITH USER_MODE` inside a Platform Event subscriber

**What the LLM generates:**

```apex
trigger AccountSyncSubscriber on Account_Sync__e (after insert) {
    List<Account> rows = [SELECT Id, SSN__c FROM Account WHERE Id IN :ids WITH USER_MODE];
}
```

**Why it happens:** Treats every Apex trigger as user-context. PE-subscribed triggers are not.

**Correct pattern:** Filter on the publisher side before publishing the event. The subscriber runs as Automated Process and any "user mode" claim is meaningless.

```apex
// In publisher (user context)
List<Account> visible = (List<Account>) Security.stripInaccessible(
    AccessType.READABLE, [SELECT Id, SSN__c FROM Account WHERE Id IN :ids]
).getRecords();
EventBus.publish(new Account_Sync__e(Payload__c = JSON.serialize(visible)));
```

**Detection hint:** Any trigger on a `__e` object that uses `WITH USER_MODE`, `WITH SECURITY_ENFORCED`, or `Security.stripInaccessible`. These calls are no-ops in that context.

---

## Anti-Pattern 3: Using `System.runAs` outside test context

**What the LLM generates:**

```apex
public void execute(SchedulableContext sc) {
    System.runAs(targetUser) {
        // do work
    }
}
```

**Why it happens:** `System.runAs` looks like the obvious primitive for "run as another user." The Apex docs say it switches user context. The LLM doesn't notice the docs scope it to tests only.

**Correct pattern:** `System.runAs` only works in test context. In production, use the cross-user FLS helper (manual `FieldPermissions` lookup) or filter at the publishing transaction boundary.

**Detection hint:** Any `System.runAs` call outside a class annotated `@isTest` or method annotated `testMethod`/`@isTest`.

---

## Anti-Pattern 4: Passing `List<sObject>` into `@future`

**What the LLM generates:**

```apex
@future(callout=true)
public static void syncAccounts(List<Account> accounts) { ... }
```

**Why it happens:** It looks like a normal Apex method signature. The compiler error is unfamiliar.

**Correct pattern:** `@future` only accepts primitive types and collections of primitives. Pass IDs and re-query inside, with `WITH USER_MODE`.

```apex
@future(callout=true)
public static void syncAccounts(Set<Id> accountIds) {
    List<Account> accounts = [SELECT Id, Name FROM Account WHERE Id IN :accountIds WITH USER_MODE];
    // ...
}
```

**Detection hint:** Any `@future`-annotated method with a non-primitive parameter type.

---

## Anti-Pattern 5: "Database.Stateful preserves the security context"

**What the LLM generates:**

> "The batch class implements `Database.Stateful`, so the user context is preserved across `execute()` calls."

**Why it happens:** Misreads "stateful" as "context-preserving" generally. `Database.Stateful` only preserves member-field values across `execute()` calls.

**Correct pattern:** Document explicitly that every `execute(...)` runs as the user who called `Database.executeBatch(...)`, regardless of `Database.Stateful`. If the contract is "honor user X," apply target-user FLS manually in each `execute()`.

**Detection hint:** Any explanation of `Database.Stateful` that mentions security, user context, or "the same user." Stateful only preserves member fields.
