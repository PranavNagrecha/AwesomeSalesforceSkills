# Gotchas: Apex Trigger Framework

---

## Gotcha 1: A Static Recursion Guard Suppresses the Second Half of a Single Test Method

**What happens:** The handler holds `private static Set<Id> processedIds = new Set<Id>()`. A test method inserts a record (the guard records its Id), then — in the same method — updates that record and asserts the after-update side effect happened. It didn't: the guard already holds the Id, so the second pass is filtered out. The assertion fails, and the failure looks like broken business logic rather than test-harness state.

**Correction (2026-09-12).** An earlier version of this gotcha claimed the leak crosses *test methods* — that test 1 poisons test 2. The Apex Developer Guide contradicts that: "Every test method, including the test setup method, runs as a separate transaction. The static context of the test class is reinitialized before each transaction begins. Therefore, static variable initializers and static blocks are executed fresh at the start of every test method." Combined with "A static variable is static only within the scope of the Apex transaction … reset across transaction boundaries", statics do **not** survive from one test method into the next. The remedy below is unchanged, but the reason is: the guard bites *inside* one method, not *between* two.

**When it occurs:** Any test method that exercises the same handler twice — insert-then-update, update-then-update, or an assertion after a `Database.update(..., false)` retry — while a static Set or Boolean guard is live. It also occurs in production for the same reason: partial-success DML retries stay in one transaction (Gotcha 7).

**How to avoid it:**
- Expose a `@TestVisible static void resetForTest()` method on the handler that clears static state
- Call it between the two phases of a multi-DML test method — not (only) at the top
- Prefer one behaviour per test method, so the guard has nothing to suppress
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

## Gotcha 2: `Trigger.new` Is Read-Only in After-Save Contexts

**What happens:** A developer writes an after-insert handler and tries to update a field on the new record: `Trigger.new[0].Status__c = 'Active'`. Salesforce throws: `SObject row was retrieved via SOQL without querying the requested field`. Wait — wrong error for this. The actual error is: `System.FinalException: Record is read-only`. The developer is confused because it works in before-insert.

**When it bites you:** After-insert or after-update contexts when you try to update the triggering record's fields directly.

**How to avoid it:**
- Field updates on the triggering record → before-save context, use direct assignment on `Trigger.new`
- If you must update the triggering record in after-save → query it, modify the queried list, DML the list (this causes re-trigger — ensure recursion guard handles it)
- Better: refactor to before-save for field updates; after-save for DML on other objects

---

## Gotcha 3: `Trigger.old` / `oldMap` Is Null on Insert

**What happens:** A handler accesses `oldMap.get(account.Id)` in the `onBeforeInsert` method. `oldMap` is null for insert contexts. The code throws a `NullPointerException`. The developer never notices in unit tests because they never pass `oldMap` to `onBeforeInsert` in tests — they only test `onBeforeUpdate` with an oldMap.

**When it bites you:** Any handler method that takes `oldMap` as a parameter but might be called in an insert context, or any handler that shares logic between insert and update.

**How to avoid it:**
- `onBeforeInsert` should never receive or use `oldMap`
- If sharing logic between insert and update in a helper method, pass `oldMap` as nullable and guard: `if (oldMap != null && oldMap.containsKey(record.Id))`
- Delta checks (`acc.Status__c != oldMap.get(acc.Id).Status__c`) belong only in update methods

---

## Gotcha 4: Handler `without sharing` Silently Exposes All Records

**What happens:** A developer writes `public without sharing class AccountTriggerHandler` because they saw a `with sharing` error in testing. The `without sharing` fixes the test. In production, the handler now runs in system context for every user — including community/portal users and restricted internal users. These users' trigger actions now query and modify records they're not supposed to see.

**When it bites you:** Always, silently. `without sharing` in a trigger handler is a data exposure risk that doesn't throw errors — it just ignores the sharing model.

**What Summer '26 did and did not change:** an *explicit* `without sharing` opts the class out of the sharing model at every `apiVersion`, so this gotcha is not retired — though at 67.0+ what a bare operation inside such a class actually reaches also depends on its access mode, which now defaults to user mode (see "How to avoid it" below). What inverted at **67.0** is the meaning of *no* keyword — a bare `public class AccountTriggerHandler` runs `with sharing` there, while at **66.0 and below** it runs without sharing. The gate is the `apiVersion` in the handler's `.cls-meta.xml`, not the org's release, and the inheritance rule means one 67.0+ class anywhere in the chain pulls the rest to `with sharing`. Separately, the `.trigger` file always runs in system mode at every version and cannot carry a sharing keyword at all — the handler is the only place this decision exists. Canonical table: [`agents/_shared/AGENT_CONTRACT.md`](../../../../agents/_shared/AGENT_CONTRACT.md) § *Apex security idiom by API version*.

**How to avoid it:**
- Default to `with sharing` on all handler classes
- If a specific sub-operation needs elevated context (e.g. querying config records the user can't see): extract it to a private inner class `private without sharing class SystemContextHelper {...}` — scope the elevation to the minimum necessary code. At `apiVersion` **67.0+** the keyword alone no longer buys the elevation: database operations default to user mode, so the helper must declare `without sharing` *and* state the mode on the operation itself (`WITH SYSTEM_MODE` on the query, `as system` on the DML, or `AccessLevel.SYSTEM_MODE` on the `Database` call) with a `// reason:` comment. Below 67.0 the keyword is sufficient
- Document why `without sharing` is used with a comment: `// without sharing: required to query TriggerSettings__c which is admin-only`

---

## Gotcha 5: Duplicate Unique-Field Values in One Bulk Batch Produce Misleading Error Messages

**What happens:** A trigger enforces or relies on a unique field (a `Unique` custom field, or an External ID). A Bulk API / Data Loader batch arrives with two records carrying the *same* unique value. Because a trigger is present, Salesforce doesn't simply fail the batch — it runs an internal rollback/retry cycle. Per the Apex Developer Guide: the retry logic in bulk operations causes a rollback/retry cycle, and that cycle assigns new keys to the new records. The second duplicate fails reporting the ID of the first record; but once the system rolls back and re-inserts the first record by itself, that record receives a *new* ID — so the ID named in the error message is no longer valid.

**When it bites you:** Any before-insert / before-upsert logic that validates against a unique field, or any code that parses the record ID out of a `DUPLICATE_VALUE` / unique-constraint error to report which row collided. The reported ID points at a record that no longer exists under that ID after the retry, so your "row X duplicates row Y" message is wrong.

**How to avoid it:**
- Detect in-batch duplicates *yourself* inside the handler before the platform's retry kicks in — build a `Map<Object, SObject>` keyed by the unique value while looping `Trigger.new`, and `addError()` the second occurrence with a message that does not depend on a persisted record ID.
- Never key user-facing "duplicate of record ..." messages on the ID Salesforce returns in the constraint error during a bulk batch; identify the collision by the unique value itself.
- Reproduce this with a bulk test that inserts 200 records containing an intentional in-batch duplicate — a single-record test will never surface the rollback/retry behavior.

---

## Gotcha 6: A Bare `override` on a Handler Hook Stops Compiling at `apiVersion` 65.0

**What happens:** A subclass hook is written without an access modifier — `override void beforeInsert() { ... }` instead of `protected override void beforeInsert() { ... }`. Below API 65.0 the compiler accepted it. From 65.0 the class fails to compile.

**When it bites you:** Whenever a handler is created or bumped to `apiVersion` 65.0 or higher — which includes every class scaffolded against the current default of 67.0. The failure is a build error at deploy, not a runtime surprise, so it shows up as a broken deployment rather than bad data. It is easy to miss when reading old blog-post framework code, where the bare form is common.

The Apex Developer Guide's versioned behavior changes state it directly: "In API version 65.0 and later, an abstract or override method requires a protected, public, or global access modifier," and "if one of these access modifiers isn't explicitly included in the method declaration, then method access defaults to private." A private method cannot override a `protected virtual` one, so the compiler rejects the class.

**How to avoid it:**
- Declare every hook override with the same visibility the base class used. [`templates/apex/TriggerHandler.cls`](../../../../templates/apex/TriggerHandler.cls) declares its seven hooks `protected virtual`, so subclasses write `protected override void beforeInsert()`.
- The rule is not specific to trigger handlers — it applies to every `abstract` and `override` method, including `BaseDomain`, `BaseService`, and `BaseSelector` subclasses, and to third-party frameworks such as fflib.
- The gate is the `apiVersion` in the class's own `.cls-meta.xml`, not the org's release. A handler pinned at 64.0 keeps compiling with the bare form; raise the version and the same source stops building.

---

## Gotcha 7: A Static Guard Resets Between Batch Apex Chunks, but Not Across a Partial-Success Retry

**What happens:** A handler uses a static `Set<Id>` to make a side effect fire once per record — an outbound notification, an audit row, a counter increment. The guard's lifetime is exactly one transaction: "A static variable is static only within the scope of the Apex transaction. It's not static across the server or the entire organization. The value of a static variable persists within the context of a single transaction and is reset across transaction boundaries." Batch Apex hands the work over in chunks, and "Each execution of a batch Apex job is considered a discrete transaction. For example, a batch Apex job that contains 1,000 records and is executed without the optional scope parameter from `Database.executeBatch` is considered five transactions of 200 records each." So a 1,000-record job gives the guard five independent lifetimes. "Once per record for this job" is not what the code expresses; "once per record per chunk" is.

The mirror case surprises people the other way. A partial-success DML does **not** clear the guard: "If a DML call is made with partial success allowed, triggers are fired during the first attempt and are fired again during subsequent attempts. Because these trigger invocations are part of the same transaction, static class variables that are accessed by the trigger aren't reset." Neither does a rollback: "Static variables aren't reverted during a rollback. If you try to run the trigger again, the static variables retain the values from the first run." Records the first attempt marked processed are silently skipped on the retry that actually saves them.

**When it occurs:** Any once-per-record effect guarded only by a static, driven by `Database.executeBatch` (chunk boundaries erase the guard) or by `Database.insert(records, false)` / `Database.update(records, false)` (the retry inherits it). It also occurs when the same record legitimately appears in two chunks of one job.

**How to avoid it:**
- Treat the static guard as what it is — re-entry control *within one transaction*. `TriggerHandler.depthByHandler` in [`templates/apex/TriggerHandler.cls`](../../../../templates/apex/TriggerHandler.cls) is a depth counter for exactly that, not a de-duplicator.
- Idempotency across a job needs a persisted marker: a checkbox or timestamp field on the record, or an External Id on the child record you create, checked with a single query per chunk.
- Test the batch path with a job whose record count exceeds one chunk (over 200), and assert the side effect fired the right number of times — a 200-record test never crosses a chunk boundary and will pass regardless.
- For the retry direction, test with `Database.update(records, false)` and a deliberately failing row, then assert the surviving rows still got their side effect.

---

## Gotcha 8: A Workflow Field Update Re-Fires Before- *and* After-Update Triggers One More Time

**What happens:** The handler's after-update path runs, does its work, and the transaction looks finished. Then a workflow rule field update on the same record fires and the order of execution loops back: at step 11, "Executes workflow rules. If there are workflow field updates: a. Updates the record again. b. Runs system validations again … c. Executes before update triggers and after update triggers, regardless of the record operation (insert or update), one more time (and only one more time)." An after-*insert* path is not re-run, but an after-update handler on that object sees a second invocation with no user-visible edit behind it.

The delta check that usually saves you can mislead here. "If a workflow rule field update is triggered by a record update, `Trigger.old` doesn't hold the newly updated field by the workflow after the update. Instead, `Trigger.old` holds the object before the initial record update was made." A field that went 1 → 10 (user) → 11 (workflow) presents on the second pass as old = 1, new = 11 — so a naive `old != new` test still reports "changed" and the side effect fires twice.

**Candidate question worth verifying against your own org:** does a **before-save record-triggered flow** cause the same re-entry? The order of execution puts before-save flows at step 3, ahead of "Executes all before triggers" at step 4 — one pass, no loop-back, so the answer from the documented sequence is no. An **after-save** flow is different: it runs at step 14, and "When a process or flow executes a DML operation, the affected record goes through the save procedure" — a same-record update from an after-save flow re-enters the whole save procedure, triggers included. `UNVERIFIED (2026-09-12):` the Apex Developer Guide's numbered sequence supports both readings above, but it does not state the before-save-flow case as a negative in so many words. Confirm in a scratch org before relying on it.

**When it occurs:** Any object that still carries workflow rules with field updates alongside an Apex after-update handler — commonly a legacy object mid-migration to Flow. Symptoms: doubled audit rows, doubled outbound notifications, a counter that increments by two.

**How to avoid it:**
- Gate the after-update side effect on a static re-entry guard per record (`processedIds` / `TriggerHandler.skipOnce`), which is correct here because the re-fire is inside the same transaction.
- Don't trust an `old != new` delta alone on an object with workflow field updates — the `Trigger.old` snapshot on the second pass is the *pre-edit* value, not the value from the first pass.
- Inventory the object's workflow field updates before you write the handler, and prefer migrating them to the same record-triggered flow or to the handler itself, so there is one writer.

---

## Checker Ignores Comments And String Literals

**What happens:** The skill checker flags a keyword that appears only in a comment or a string literal (for example a note that `WITH SECURITY_ENFORCED` is not used, or an assertion message that mentions `EventBus.publish`).

**When it occurs:** Before the checker blanked `//` line comments, `/* … */` block comments, and `'…'` string literals to spaces (same length, newlines preserved) for code-pattern rules.

**How to avoid:** Trust the checker on executable code only. Mentions inside comments and string literals are ignored for pattern matches; rules that intentionally read comments (for example a `// reason:` search) still read the original text.
