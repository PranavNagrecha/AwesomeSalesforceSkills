# Gotchas: Apex Trigger Framework

---

## Static Recursion Guard Variables Persist Across Test Methods

**What happens:** The `AccountTriggerHandler` has `private static Set<Id> processedIds = new Set<Id>()`. Test method 1 inserts an Account — `processedIds` gets that Account's ID added. Test method 2 runs: it inserts the SAME test Account (using TestDataFactory). The Account ID is already in `processedIds`. The after-insert logic is skipped. The test asserts that something was created — but it wasn't, because the recursion guard prevented processing. Test fails intermittently depending on execution order.

**When it bites you:** Any trigger handler with a static recursion guard, once test coverage reaches 2+ test methods that test the same trigger.

**How to avoid it:**
- Expose a `@TestVisible static void resetForTest()` method on the handler that clears static state
- Call it at the start of each test method
- Or: use `@TestSetup` to reset state before each test
```apex
@TestVisible
private static void resetForTest() {
    processedIds.clear();
}

// In test class:
@isTest
static void testAfterInsert_secondMethod() {
    AccountTriggerHandler.resetForTest();  // ← clear before this test
    // ... rest of test
}
```

---

## `Trigger.new` Is Read-Only in After-Save Contexts

**What happens:** A developer writes an after-insert handler and tries to update a field on the new record: `Trigger.new[0].Status__c = 'Active'`. Salesforce throws: `SObject row was retrieved via SOQL without querying the requested field`. Wait — wrong error for this. The actual error is: `System.FinalException: Record is read-only`. The developer is confused because it works in before-insert.

**When it bites you:** After-insert or after-update contexts when you try to update the triggering record's fields directly.

**How to avoid it:**
- Field updates on the triggering record → before-save context, use direct assignment on `Trigger.new`
- If you must update the triggering record in after-save → query it, modify the queried list, DML the list (this causes re-trigger — ensure recursion guard handles it)
- Better: refactor to before-save for field updates; after-save for DML on other objects

---

## `Trigger.old` / `oldMap` Is Null on Insert

**What happens:** A handler accesses `oldMap.get(account.Id)` in the `onBeforeInsert` method. `oldMap` is null for insert contexts. The code throws a `NullPointerException`. The developer never notices in unit tests because they never pass `oldMap` to `onBeforeInsert` in tests — they only test `onBeforeUpdate` with an oldMap.

**When it bites you:** Any handler method that takes `oldMap` as a parameter but might be called in an insert context, or any handler that shares logic between insert and update.

**How to avoid it:**
- `onBeforeInsert` should never receive or use `oldMap`
- If sharing logic between insert and update in a helper method, pass `oldMap` as nullable and guard: `if (oldMap != null && oldMap.containsKey(record.Id))`
- Delta checks (`acc.Status__c != oldMap.get(acc.Id).Status__c`) belong only in update methods

---

## Handler `without sharing` Silently Exposes All Records

**What happens:** A developer writes `public without sharing class AccountTriggerHandler` because they saw a `with sharing` error in testing. The `without sharing` fixes the test. In production, the handler now runs in system context for every user — including community/portal users and restricted internal users. These users' trigger actions now query and modify records they're not supposed to see.

**When it bites you:** Always, silently. `without sharing` in a trigger handler is a data exposure risk that doesn't throw errors — it just ignores the sharing model.

**How to avoid it:**
- Default to `with sharing` on all handler classes
- If a specific sub-operation needs elevated context (e.g. querying config records the user can't see): extract it to a private inner class `private without sharing class SystemContextHelper {...}` — scope the elevation to the minimum necessary code
- Document why `without sharing` is used with a comment: `// without sharing: required to query TriggerSettings__c which is admin-only`
