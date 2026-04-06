# LLM Anti-Patterns — Trigger Framework

Common mistakes AI coding assistants make when generating or advising on Apex trigger architecture and handler patterns.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Putting logic directly in the trigger body instead of a handler class

**What the LLM generates:**

```apex
trigger AccountTrigger on Account (before insert, after update) {
    if (Trigger.isBefore && Trigger.isInsert) {
        for (Account a : Trigger.new) {
            if (String.isBlank(a.Description)) {
                a.Description = 'Created via trigger';
            }
        }
    }
    if (Trigger.isAfter && Trigger.isUpdate) {
        List<Task> tasks = new List<Task>();
        for (Account a : Trigger.new) {
            if (a.Status__c != Trigger.oldMap.get(a.Id).Status__c) {
                tasks.add(new Task(WhatId = a.Id, Subject = 'Follow up'));
            }
        }
        insert tasks;
    }
}
```

**Why it happens:** LLMs generate self-contained trigger code because it compiles and runs. But logic in the trigger body is untestable in isolation (you must perform DML to invoke it), cannot be reused from other entry points, and becomes unmanageable as the object grows.

**Correct pattern:**

```apex
// Trigger: thin dispatcher
trigger AccountTrigger on Account (before insert, after update) {
    AccountTriggerHandler handler = new AccountTriggerHandler();
    if (Trigger.isBefore && Trigger.isInsert) handler.beforeInsert(Trigger.new);
    if (Trigger.isAfter && Trigger.isUpdate) handler.afterUpdate(Trigger.new, Trigger.oldMap);
}

// Handler: testable logic
public class AccountTriggerHandler {
    public void beforeInsert(List<Account> newAccounts) {
        AccountDomain.setDefaultDescription(newAccounts);
    }
    public void afterUpdate(List<Account> newAccounts, Map<Id, Account> oldMap) {
        AccountService.createFollowUpTasks(newAccounts, oldMap);
    }
}
```

**Detection hint:** `.trigger` files with more than 10 lines of logic, SOQL queries, or DML statements.

---

## Anti-Pattern 2: Creating multiple triggers on the same object

**What the LLM generates:**

```apex
// File: AccountValidationTrigger.trigger
trigger AccountValidationTrigger on Account (before insert, before update) { ... }

// File: AccountIntegrationTrigger.trigger
trigger AccountIntegrationTrigger on Account (after insert, after update) { ... }
```

**Why it happens:** LLMs create separate triggers for separate concerns, mimicking how separate classes handle separate concerns. But Salesforce does not guarantee trigger execution order when multiple triggers exist on the same object. This creates non-deterministic behavior that is impossible to debug.

**Correct pattern:**

```apex
// ONE trigger per object
trigger AccountTrigger on Account (before insert, before update, after insert, after update) {
    AccountTriggerHandler handler = new AccountTriggerHandler();
    if (Trigger.isBefore) {
        if (Trigger.isInsert) handler.beforeInsert(Trigger.new);
        if (Trigger.isUpdate) handler.beforeUpdate(Trigger.new, Trigger.oldMap);
    }
    if (Trigger.isAfter) {
        if (Trigger.isInsert) handler.afterInsert(Trigger.new);
        if (Trigger.isUpdate) handler.afterUpdate(Trigger.new, Trigger.oldMap);
    }
}
```

**Detection hint:** Multiple `.trigger` files for the same SObject — `grep -l "trigger.*on Account"` returning more than one file.

---

## Anti-Pattern 3: No bypass mechanism for data loads or emergency fixes

**What the LLM generates:**

```apex
public class AccountTriggerHandler {
    public void afterUpdate(List<Account> newAccounts, Map<Id, Account> oldMap) {
        // Always runs — no way to disable without deploying code
        processStatusChanges(newAccounts, oldMap);
    }
}
```

**Why it happens:** LLMs generate handlers with no disable mechanism. In production, data loads, one-time fixes, or emergency situations may require bypassing trigger logic. Without a Custom Setting, Custom Metadata, or Custom Permission check, the only option is deploying a code change.

**Correct pattern:**

```apex
public class AccountTriggerHandler {
    public void afterUpdate(List<Account> newAccounts, Map<Id, Account> oldMap) {
        // Check bypass setting before running
        TriggerSetting__c settings = TriggerSetting__c.getInstance(UserInfo.getUserId());
        if (settings != null && settings.Bypass_Account_Trigger__c) {
            return;
        }
        processStatusChanges(newAccounts, oldMap);
    }
}
```

**Detection hint:** Trigger handler classes with no reference to Custom Settings, Custom Metadata, or Custom Permissions for bypass control.

---

## Anti-Pattern 4: Not filtering records by which fields actually changed in after-update

**What the LLM generates:**

```apex
public void afterUpdate(List<Account> newAccounts, Map<Id, Account> oldMap) {
    for (Account a : newAccounts) {
        // Runs for EVERY updated record, even if the relevant field didn't change
        System.enqueueJob(new SyncJob(a.Id));
    }
}
```

**Why it happens:** LLMs process all records in `Trigger.new` without checking which fields changed. This fires expensive operations (callouts, child record updates) for irrelevant field changes like `LastModifiedDate`, causing unnecessary processing and potential recursion.

**Correct pattern:**

```apex
public void afterUpdate(List<Account> newAccounts, Map<Id, Account> oldMap) {
    List<Id> statusChangedIds = new List<Id>();
    for (Account a : newAccounts) {
        Account old = oldMap.get(a.Id);
        if (a.Status__c != old.Status__c) {
            statusChangedIds.add(a.Id);
        }
    }
    if (!statusChangedIds.isEmpty()) {
        System.enqueueJob(new SyncJob(statusChangedIds));
    }
}
```

**Detection hint:** After-update handler methods that iterate `Trigger.new` without comparing field values to `oldMap`.

---

## Anti-Pattern 5: Hardcoding the trigger context check pattern instead of using a framework dispatch

**What the LLM generates:**

```apex
trigger AccountTrigger on Account (before insert, before update, after insert, after update, before delete, after delete, after undelete) {
    if (Trigger.isBefore && Trigger.isInsert) {
        AccountTriggerHandler.beforeInsert(Trigger.new);
    } else if (Trigger.isBefore && Trigger.isUpdate) {
        AccountTriggerHandler.beforeUpdate(Trigger.new, Trigger.oldMap);
    } else if (Trigger.isAfter && Trigger.isInsert) {
        AccountTriggerHandler.afterInsert(Trigger.new);
    } else if (Trigger.isAfter && Trigger.isUpdate) {
        AccountTriggerHandler.afterUpdate(Trigger.new, Trigger.oldMap);
    }
    // Repeated for every object trigger in the org
}
```

**Why it happens:** LLMs duplicate the context-checking boilerplate in every trigger. For an org with 30 objects, that is 30 nearly identical trigger files. A framework base class with virtual methods eliminates this duplication.

**Correct pattern:**

```apex
// Base handler with virtual methods
public virtual class TriggerHandler {
    public void run() {
        if (Trigger.isBefore && Trigger.isInsert) beforeInsert(Trigger.new);
        if (Trigger.isBefore && Trigger.isUpdate) beforeUpdate(Trigger.new, Trigger.oldMap);
        if (Trigger.isAfter && Trigger.isInsert) afterInsert(Trigger.new);
        if (Trigger.isAfter && Trigger.isUpdate) afterUpdate(Trigger.new, Trigger.oldMap);
    }
    protected virtual void beforeInsert(List<SObject> newList) {}
    protected virtual void beforeUpdate(List<SObject> newList, Map<Id, SObject> oldMap) {}
    protected virtual void afterInsert(List<SObject> newList) {}
    protected virtual void afterUpdate(List<SObject> newList, Map<Id, SObject> oldMap) {}
}

// Per-object handler overrides only what it needs
public class AccountTriggerHandler extends TriggerHandler {
    protected override void afterUpdate(List<SObject> newList, Map<Id, SObject> oldMap) {
        // Account-specific logic
    }
}

// Trigger: one line
trigger AccountTrigger on Account (before insert, before update, after insert, after update) {
    new AccountTriggerHandler().run();
}
```

**Detection hint:** Multiple trigger files with identical `if (Trigger.isBefore && Trigger.isInsert)` dispatch patterns.

---

## Anti-Pattern 6: Introducing a second trigger framework when one already exists in the org

**What the LLM generates:**

```apex
// Generates Kevin O'Hara's framework when the org already uses a custom TriggerHandler base class
// Now the org has two competing dispatch mechanisms
```

**Why it happens:** LLMs generate whatever framework they pattern-match on from training data without checking whether the org already has one. Having two frameworks creates confusion about which to use, potential ordering conflicts, and maintenance overhead.

**Correct pattern:**

```
Before generating a trigger framework:
1. Check if a TriggerHandler or TriggerDispatcher base class already exists
2. Check if the org uses FFLIB, Kevin O'Hara, or a custom framework
3. If a framework exists, extend it — do not introduce a second one
4. If no framework exists, pick one and apply it consistently to all objects
```

**Detection hint:** Codebase containing multiple different trigger base classes or dispatch patterns (e.g., both `TriggerHandler` and `fflib_SObjectDomain`).
