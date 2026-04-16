# Eval: apex/trigger-framework

- **Skill under test:** `skills/apex/trigger-framework/SKILL.md`
- **Priority:** P0
- **Cases:** 3
- **Last verified:** 2026-04-16
- **Related templates:** `templates/apex/TriggerHandler.cls`, `templates/apex/TriggerControl.cls`, `templates/apex/cmdt/Trigger_Setting__mdt.object-meta.xml`
- **Related decision trees:** `standards/decision-trees/automation-selection.md`

## Pass criteria

All 3 cases are P0. The AI must produce a bulkified, recursion-safe trigger
dispatch that uses a handler class, references the canonical `TriggerHandler`
template, and supports runtime activation bypass via `Trigger_Setting__mdt`.
Any answer that places logic directly inside `trigger` body, uses
`Trigger.new[0]`, or ignores recursion guards fails.

## Case 1 — Green-field trigger on a custom object

**Priority:** P0

**User prompt:**

> "I need to add a trigger on my custom `Invoice__c` object. On insert I must
> roll up the total amount to the parent `Account` and prevent creation if
> `Status__c = 'Closed'`. We don't have a trigger framework yet."

**Context provided:** None.

**Expected output MUST include:**

- Exactly one `trigger InvoiceTrigger on Invoice__c` declaration.
- A `InvoiceTriggerHandler` class extending the canonical `TriggerHandler`
  base class (reference to `templates/apex/TriggerHandler.cls`).
- Logic split into two methods: `beforeInsert()` (validation) and
  `afterInsert()` (roll-up) — NOT both in one method.
- Bulk-safe parent lookup (single SOQL collecting all parent Ids, no SOQL
  in a loop).
- A recommendation to add a `Trigger_Setting__mdt` record so the trigger
  can be deactivated in production.
- Mention of a test class that inserts 200 invoices inside
  `Test.startTest()/stopTest()`.

**Expected output MUST NOT include:**

- Logic placed in the trigger body itself (e.g. `if (Trigger.isBefore) { ... }`).
- `Trigger.new[0]` or any other single-record dereference outside a loop.
- `insert parents;` inside a `for (...) {` loop.
- `System.debug` as the error-handling strategy.
- A second ad-hoc framework when the canonical one is available.

**Rubric (0–5):**

- **Correctness:** Does the trigger actually enforce both rules on bulk insert?
- **Completeness:** Are handler class, trigger, test class, and metadata record all present?
- **Bulk safety:** Zero SOQL/DML in loops; aggregate updates on parents.
- **Security:** Uses `WITH USER_MODE` or `Security.stripInaccessible`.
- **Citation of official docs:** Links to the trigger best-practices page on developer.salesforce.com.

**Reference answer (gold):**

```apex
// InvoiceTrigger.trigger
trigger InvoiceTrigger on Invoice__c (before insert, after insert) {
    new InvoiceTriggerHandler().run();
}
```

```apex
// InvoiceTriggerHandler.cls
public with sharing class InvoiceTriggerHandler extends TriggerHandler {

    protected override void beforeInsert() {
        for (Invoice__c inv : (List<Invoice__c>) Trigger.new) {
            if (inv.Status__c == 'Closed') {
                inv.addError('Cannot create invoice in Closed status.');
            }
        }
    }

    protected override void afterInsert() {
        Set<Id> accountIds = new Set<Id>();
        for (Invoice__c inv : (List<Invoice__c>) Trigger.new) {
            if (inv.Account__c != null) { accountIds.add(inv.Account__c); }
        }
        if (accountIds.isEmpty()) { return; }

        Map<Id, Decimal> totals = new Map<Id, Decimal>();
        for (AggregateResult ar : [
            SELECT Account__c acct, SUM(Amount__c) total
            FROM Invoice__c
            WHERE Account__c IN :accountIds
            WITH USER_MODE
            GROUP BY Account__c
        ]) {
            totals.put((Id) ar.get('acct'), (Decimal) ar.get('total'));
        }

        List<Account> toUpdate = new List<Account>();
        for (Id acctId : totals.keySet()) {
            toUpdate.add(new Account(Id = acctId, Invoice_Total__c = totals.get(acctId)));
        }
        if (!toUpdate.isEmpty()) {
            update toUpdate;
        }
    }
}
```

Plus a `Trigger_Setting__mdt` record with `Object_API_Name__c = Invoice__c`,
`Handler_Class__c = InvoiceTriggerHandler`, `Is_Active__c = true`, and a
200-record bulk test using `TestDataFactory`.

## Case 2 — Diagnosing recursion on an existing trigger

**Priority:** P0

**User prompt:**

> "My `Account` trigger is firing twice on update and I'm getting
> `Too many SOQL queries: 101`. We already have an `AccountTriggerHandler`
> that extends a `TriggerHandler` base class."

**Context provided:**

- Handler code showing it calls `update contactsToUpdate;` in `afterUpdate()`
  where those Contact records have their own trigger that updates their
  parent Account.

**Expected output MUST include:**

- Explanation that recursion is user-triggered (Account→Contact→Account
  cycle), not framework-internal.
- Recommendation to use `TriggerHandler.skipOnce('AccountTriggerHandler')`
  immediately before the Contact update, OR to flag the records that
  cause re-entry with a per-transaction `Set<Id>`.
- Root-cause framing: the real fix is a selector method that only reads
  the changed fields once, not additional recursion guards.
- Reminder to add an integration test that updates 200 accounts
  simultaneously to reproduce the failure.

**Expected output MUST NOT include:**

- A blanket `if (Trigger.isExecuting) return;` or similar kill-switch.
- Adding a static `Boolean alreadyRan` WITHOUT explaining its test implications.
- Suggesting to "turn off the Contact trigger" without using `Trigger_Setting__mdt`.

**Rubric (0–5):**

- **Correctness:** Does the diagnosis identify the cross-object cycle?
- **Completeness:** Covers both immediate fix (skipOnce) and root-cause.
- **Bulk safety:** Refactor still handles 200 updates.
- **Security:** Mentions that `WITH USER_MODE` enforcement survives the refactor.
- **Citation of official docs:** Links to Apex governor limits docs.

**Reference answer (gold):**

"The 101-query error is cross-object recursion: `AccountTriggerHandler.afterUpdate()` calls `update contactsToUpdate`, which fires `ContactTrigger`, whose handler updates the Account again — re-entering your trigger with a fresh 100-query budget gone.

Short-term fix: call `TriggerHandler.skipOnce('AccountTriggerHandler')` right before the Contact update:

```apex
TriggerHandler.skipOnce('AccountTriggerHandler');
update contactsToUpdate;
```

Long-term fix: your `afterUpdate` reads the old Account values in a selector anyway — move that selector call outside the cycle and accept that the Contact trigger may re-enter once. Keep the `TriggerHandler.MAX_DEPTH` guard as a safety net.

Add a test that updates 200 Accounts in a single transaction and asserts `Limits.getQueries() < 50` and `Limits.getDmlStatements() < 50`."

## Case 3 — Disabling a misbehaving trigger without a deployment

**Priority:** P0

**User prompt:**

> "Data load in production is running slow because the `CaseTrigger` is
> doing assignment logic on every row. We need to turn it off for a 4-hour
> load window without deploying metadata. What are the options?"

**Expected output MUST include:**

- Use `Trigger_Setting__mdt` → `Is_Active__c = false` for
  `Object_API_Name__c = Case` + `Handler_Class__c = CaseTriggerHandler`.
- Alternative for break-glass: grant the loading user the
  `TriggerControl_BypassAll` Custom Permission.
- Reminder that Custom Metadata deploys propagate in seconds and are
  subject to the existing release process — i.e. no package build needed
  but still tracked.
- Post-load checklist: re-enable the setting, verify counts, run the
  handler's post-load reconcile job.

**Expected output MUST NOT include:**

- Hard-coded `if (System.IsBatch)` bypass in Apex.
- Editing the trigger directly to add a short-circuit.
- Advice to "just disable the trigger in Setup" (Salesforce removed that
  UI for Apex triggers long ago).

**Rubric (0–5):**

- **Correctness:** Identifies the canonical metadata-driven approach.
- **Completeness:** Covers both metadata flip AND custom-permission break-glass.
- **Bulk safety:** N/A for this case — score 5 by default.
- **Security:** Notes that the Custom Permission should only be on a dedicated Integration profile.
- **Citation of official docs:** Links to Custom Metadata deployment docs.

**Reference answer (gold):**

"You have two levers, both declarative:

1. **Per-handler disable** (preferred for planned loads): update the
   `Trigger_Setting__mdt` record keyed by `Case::CaseTriggerHandler` so
   `Is_Active__c = false`, deploy the metadata change (seconds), run the
   load, re-enable after. `TriggerControl.isActive()` caches per
   transaction so the impact is immediate for new transactions.

2. **Org-wide break-glass**: grant the running user the
   `TriggerControl_BypassAll` Custom Permission. `TriggerControl.hasBypassAllPermission()`
   short-circuits ALL handlers using this framework. Only assign this
   to a dedicated Integration user's profile or permission set — never
   to interactive users.

Avoid hard-coding `System.IsBatch` or similar context checks in the
trigger itself — that's untestable and hides intent.

Post-load: flip `Is_Active__c` back on and run `CaseAssignmentBatch`
over the loaded rows to backfill the assignments the trigger would have done."
