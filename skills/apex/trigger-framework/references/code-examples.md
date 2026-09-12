# Code Examples: A Deployable WorkOrder Trigger Package

A complete, deploy-ready package for one object that no other example in this
skill uses. `references/examples.md` shows the *shapes* (dispatch, guard, delta,
bulk lookup); this file shows one finished unit of work — every file, its
`-meta.xml`, the manifest, the deploy order, and the command that verifies it.

The object is **WorkOrder**. It was chosen because the Object Reference describes
`WorkOrder.EndDate` as "The date when the work order is completed. This field is
blank unless you set up an Apex trigger or quick action to populate it" — the
behaviour below is the documented use for the field, not an invented scenario.
`ParentWorkOrderId` is a self-lookup to WorkOrder, which makes the roll-up in
`afterUpdate` genuine same-object DML — the case that needs a recursion guard.

What the package does:

| Context | Behaviour | Why that context |
|---|---|---|
| `beforeUpdate` | When `Status` becomes `Completed` and `EndDate` is null, stamp `EndDate` with `System.now()` | Field update on the triggering record — before-save, no DML |
| `afterUpdate` | When a child work order completes, check its siblings; if all are complete, complete the parent | DML on another record — after-save only |

The `afterUpdate` path updates **WorkOrder from a WorkOrder trigger**, so it
re-enters its own trigger. The guard is `TriggerHandler.skipOnce(...)` from the
canonical base class, issued immediately before the parent DML.

---

## 1. `WorkOrderTriggerHandler.cls`

Target path: `force-app/main/default/classes/WorkOrderTriggerHandler.cls`

Extends [`templates/apex/TriggerHandler.cls`](../../../../templates/apex/TriggerHandler.cls).
The base class hooks take **no arguments** — `run()` has already established the
trigger context, so each override reads `Trigger.new` / `Trigger.oldMap` itself
and casts. Each override is declared `protected override`, matching the base
class's `protected virtual`: a bare `override` stops compiling at `apiVersion`
65.0 and above (see `references/gotchas.md`, Gotcha 6).

```apex
/**
 * WorkOrderTriggerHandler — all trigger logic for WorkOrder.
 *
 * Sharing is written out on purpose. The .trigger file always runs in system
 * mode and cannot carry a sharing keyword, so this class is the only place the
 * decision is expressible; and what an *absent* keyword means is gated on this
 * class's own apiVersion.
 */
public with sharing class WorkOrderTriggerHandler extends TriggerHandler {

    @TestVisible private static final String HANDLER_NAME = 'WorkOrderTriggerHandler';
    @TestVisible private static final String STATUS_COMPLETED = 'Completed';

    /** Parents this handler has already completed in this transaction. */
    @TestVisible private static Set<Id> completedParentIds = new Set<Id>();

    @TestVisible
    private static void resetForTest() {
        completedParentIds.clear();
    }

    // ─── Before save: field defaulting on the triggering record ───────────────

    protected override void beforeUpdate() {
        List<WorkOrder> newOrders = (List<WorkOrder>) Trigger.new;
        Map<Id, WorkOrder> oldMap = (Map<Id, WorkOrder>) Trigger.oldMap;

        for (WorkOrder order : newOrders) {
            WorkOrder prior = oldMap.get(order.Id);
            Boolean justCompleted = order.Status == STATUS_COMPLETED
                && prior.Status != STATUS_COMPLETED;
            if (justCompleted && order.EndDate == null) {
                order.EndDate = System.now();
            }
        }
    }

    // ─── After save: DML on other records of the same object ─────────────────

    protected override void afterUpdate() {
        List<WorkOrder> newOrders = (List<WorkOrder>) Trigger.new;
        Map<Id, WorkOrder> oldMap = (Map<Id, WorkOrder>) Trigger.oldMap;

        // 1. Which parents might now be fully complete? One pass, no queries.
        Set<Id> candidateParentIds = new Set<Id>();
        for (WorkOrder order : newOrders) {
            WorkOrder prior = oldMap.get(order.Id);
            if (order.ParentWorkOrderId == null) {
                continue;
            }
            if (order.Status == STATUS_COMPLETED && prior.Status != STATUS_COMPLETED) {
                candidateParentIds.add(order.ParentWorkOrderId);
            }
        }
        // Parents this handler already completed earlier in the transaction need
        // no second pass. Only IDs it actually updated are in this set, so a
        // parent that stayed open is still re-evaluated when its last child lands.
        candidateParentIds.removeAll(completedParentIds);
        if (candidateParentIds.isEmpty()) {
            return;
        }

        // 2. One query for every child of every candidate parent.
        Map<Id, Boolean> allChildrenDoneByParent = new Map<Id, Boolean>();
        for (Id parentId : candidateParentIds) {
            allChildrenDoneByParent.put(parentId, true);
        }
        for (WorkOrder child : [
            SELECT Id, Status, ParentWorkOrderId
            FROM WorkOrder
            WHERE ParentWorkOrderId IN :candidateParentIds
        ]) {
            if (child.Status != STATUS_COMPLETED) {
                allChildrenDoneByParent.put(child.ParentWorkOrderId, false);
            }
        }

        // 3. One query for the parents that are still open, then one update.
        List<WorkOrder> parentsToComplete = new List<WorkOrder>();
        for (WorkOrder parent : [
            SELECT Id, Status
            FROM WorkOrder
            WHERE Id IN :candidateParentIds AND Status != :STATUS_COMPLETED
        ]) {
            if (allChildrenDoneByParent.get(parent.Id) == true) {
                parent.Status = STATUS_COMPLETED;
                parentsToComplete.add(parent);
            }
        }
        if (parentsToComplete.isEmpty()) {
            return;
        }

        // 4. Recursion guard. This DML re-enters WorkOrderTrigger; skipOnce makes
        //    the next entry for this handler return before dispatch, and the base
        //    class's depth counter is the backstop if a future edit removes it.
        TriggerHandler.skipOnce(HANDLER_NAME);
        update parentsToComplete;

        for (WorkOrder parent : parentsToComplete) {
            completedParentIds.add(parent.Id);
        }
    }
}
```

Target path: `force-app/main/default/classes/WorkOrderTriggerHandler.cls-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

`ApexCodeUnitStatus` on an `ApexClass` accepts only `Active` and `Deleted` — the
Metadata API Developer Guide notes that the enum "includes an `Inactive` option,
but it's only supported for `ApexTrigger`; it isn't supported for `ApexClass`".
Writing `Inactive` into a class meta file is a deploy error, not a way to park a
class.

---

## 2. `WorkOrderTrigger.trigger`

Target path: `force-app/main/default/triggers/WorkOrderTrigger.trigger`

One trigger on the object. The body has no logic at all: no loop, no query, no
DML, no `if` on trigger context. Everything the dispatcher needs already lives in
`TriggerHandler.run()`, including the `TriggerControl` activation check.

```apex
/**
 * WorkOrderTrigger — the only trigger on WorkOrder.
 *
 * Activation is controlled by TriggerControl via Trigger_Setting__mdt, keyed on
 * (Object API Name, Handler Class). Set Is_Active__c = false on the
 * WorkOrder/WorkOrderTriggerHandler record to disable this without a deployment.
 */
trigger WorkOrderTrigger on WorkOrder (
    before insert, before update, before delete,
    after insert, after update, after delete, after undelete
) {
    new WorkOrderTriggerHandler().run();
}
```

Target path: `force-app/main/default/triggers/WorkOrderTrigger.trigger-meta.xml`

An `ApexTrigger` meta file takes `apiVersion` and `status`, and `status` here
*does* accept `Inactive` — "Active — the trigger is active", "Inactive — the
trigger is inactive, but not deleted", "Deleted — the trigger is marked for
deletion". Prefer `TriggerControl` for day-to-day bypass: flipping `status` to
`Inactive` is a deployment, which is exactly what the activation layer exists to
avoid.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexTrigger xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexTrigger>
```

---

## 3. `WorkOrderTriggerHandlerTest.cls`

Target path: `force-app/main/default/classes/WorkOrderTriggerHandlerTest.cls`

200 records, one DML statement, assertions on the business outcome. The 200-child
case is the one that proves the roll-up query does not scale with row count.

Two harness details matter and are easy to get wrong:

- `TriggerControl.overrideForTest('WorkOrder', 'WorkOrderTriggerHandler', true)`
  seeds the activation cache so the test does not depend on which
  `Trigger_Setting__mdt` rows happen to exist in the target org.
- `resetForTest()` clears the completed-parent ledger. It is called *inside* a
  test method, between two phases — never between test methods. Each test method
  is its own transaction and statics are reinitialised at the start of every one,
  so a between-methods reset is dead code (see `references/gotchas.md`, Gotcha 1).

```apex
@IsTest
private class WorkOrderTriggerHandlerTest {

    private static final Integer BULK_SIZE = 200;

    private static List<WorkOrder> buildChildren(Integer count, Id parentId) {
        List<WorkOrder> children = new List<WorkOrder>();
        for (Integer i = 0; i < count; i++) {
            children.add(new WorkOrder(
                Subject = 'Child ' + i,
                Status = 'New',
                ParentWorkOrderId = parentId
            ));
        }
        return children;
    }

    @IsTest
    static void beforeUpdate_stampsEndDate_onBulkCompletion() {
        TriggerControl.overrideForTest('WorkOrder', 'WorkOrderTriggerHandler', true);
        List<WorkOrder> orders = buildChildren(BULK_SIZE, null);
        insert orders;

        for (WorkOrder order : orders) {
            order.Status = 'Completed';
        }

        Test.startTest();
        update orders;
        Test.stopTest();

        List<WorkOrder> reloaded = [
            SELECT Id, EndDate FROM WorkOrder WHERE Id IN :orders
        ];
        Assert.areEqual(BULK_SIZE, reloaded.size(), 'All 200 work orders should still exist');
        for (WorkOrder order : reloaded) {
            Assert.isNotNull(order.EndDate, 'EndDate must be stamped when Status becomes Completed');
        }
    }

    @IsTest
    static void afterUpdate_rollsUpParent_onlyWhenEveryChildIsComplete() {
        TriggerControl.overrideForTest('WorkOrder', 'WorkOrderTriggerHandler', true);
        WorkOrder parent = new WorkOrder(Subject = 'Parent', Status = 'New');
        insert parent;
        List<WorkOrder> children = buildChildren(BULK_SIZE, parent.Id);
        insert children;

        // Phase 1 — complete all but one child. The parent must stay open.
        List<WorkOrder> allButOne = new List<WorkOrder>();
        for (Integer i = 1; i < children.size(); i++) {
            children[i].Status = 'Completed';
            allButOne.add(children[i]);
        }

        Test.startTest();
        update allButOne;
        Assert.areEqual(
            'New',
            [SELECT Status FROM WorkOrder WHERE Id = :parent.Id].Status,
            'Parent must not complete while one child is open'
        );

        // Phase 2 — same transaction. Phase 1 left the parent open, so the ledger
        // is empty and the reset is a no-op here; it is called to prove the guard
        // does not depend on a fresh transaction to release.
        WorkOrderTriggerHandlerTest.resetHandlerState();
        children[0].Status = 'Completed';
        update children[0];
        Test.stopTest();

        Assert.areEqual(
            'Completed',
            [SELECT Status FROM WorkOrder WHERE Id = :parent.Id].Status,
            'Parent must complete once every child is complete'
        );
    }

    @IsTest
    static void run_isSuppressed_whenTriggerControlSaysInactive() {
        TriggerControl.overrideForTest('WorkOrder', 'WorkOrderTriggerHandler', false);
        List<WorkOrder> orders = buildChildren(BULK_SIZE, null);
        insert orders;
        for (WorkOrder order : orders) {
            order.Status = 'Completed';
        }

        Test.startTest();
        update orders;
        Test.stopTest();

        Integer stamped = [
            SELECT COUNT() FROM WorkOrder WHERE Id IN :orders AND EndDate != NULL
        ];
        Assert.areEqual(0, stamped, 'A deactivated handler must not stamp EndDate');
    }

    private static void resetHandlerState() {
        WorkOrderTriggerHandler.resetForTest();
    }
}
```

Target path: `force-app/main/default/classes/WorkOrderTriggerHandlerTest.cls-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

---

## 4. `package.xml`

Target path: `manifest/package.xml`

Every class in the manifest below is shipped by this package. That is the point
of listing `TriggerHandler` and `TriggerControl` here and not only in prose.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Trigger_Setting__mdt</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>TriggerControl</members>
        <members>TriggerHandler</members>
        <members>WorkOrderTriggerHandler</members>
        <members>WorkOrderTriggerHandlerTest</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>WorkOrderTrigger</members>
        <name>ApexTrigger</name>
    </types>
    <version>67.0</version>
</Package>
```

---

## 5. Deploy order — and which template classes must ship

`WorkOrderTriggerHandler` references `TriggerHandler`. `TriggerHandler.run()`
references `TriggerControl`. `TriggerControl` queries `Trigger_Setting__mdt`.
Every one of those must either be in this package as a **verbatim copy** of the
canonical template, or already declared by an earlier step of the build plan —
the template-class provenance rule in `agents/apex-builder/AGENT.md` Step 6. A
package that ships a subclass without its base class fails the deploy with
`Invalid type: TriggerHandler`, and there is no runtime warning first.

Same-day rule, stated plainly: **a class that references a canonical
`templates/apex/**` class ships that class verbatim in the same deployment, or an
earlier step of the same plan has already declared it. There is no third option.**
Copy the template byte-for-byte; do not edit it downstream. If the base class
genuinely needs a change, change it in `templates/apex/` and re-copy.

| # | Component | Source | Verbatim? |
|---|---|---|---|
| 1 | `Trigger_Setting__mdt` (object + `Is_Active__c`, `Object_API_Name__c`, `Handler_Class__c`) | `templates/apex/cmdt/Trigger_Setting__mdt/` | Yes |
| 2 | `TriggerControl.cls` + `.cls-meta.xml` | [`templates/apex/TriggerControl.cls`](../../../../templates/apex/TriggerControl.cls) | Yes — `diff` must be empty |
| 3 | `TriggerHandler.cls` + `.cls-meta.xml` | [`templates/apex/TriggerHandler.cls`](../../../../templates/apex/TriggerHandler.cls) | Yes — `diff` must be empty |
| 4 | `WorkOrderTriggerHandler.cls` + `.cls-meta.xml` | this file, § 1 | No — object-specific |
| 5 | `WorkOrderTrigger.trigger` + `.trigger-meta.xml` | this file, § 2 | No — object-specific |
| 6 | `WorkOrderTriggerHandlerTest.cls` + `.cls-meta.xml` | this file, § 3 | No — object-specific |

Steps 1–3 can go in one deployment; 4–6 depend on them and must follow. The
`TriggerControl_BypassAll` Custom Permission is **not** shipped by the templates —
`TriggerControl` fails closed when it is absent, so the package deploys and runs
without it, and the break-glass bypass simply isn't available until someone
creates it.

Not shipped here, and deliberately: `TestDataFactory` has no `createWorkOrders`
method, so this test builds its records inline rather than referencing a template
class the package would then be obliged to ship.

---

## 6. Verification

Run the skill's checker against the deploy tree before the deploy, not after:

```bash
python3 skills/apex/trigger-framework/scripts/check_trigger_framework.py \
    --manifest-dir force-app/main/default
```

Expected on this package: `Summary: 0 error(s), 0 warning(s)` and exit `0`. The
checker reads `.trigger` and `.cls` files only — it never contacts an org.

Tighten the gate in CI, where an advisory finding should also fail the build:

```bash
python3 skills/apex/trigger-framework/scripts/check_trigger_framework.py \
    --manifest-dir force-app/main/default --strict
```

Exit codes: `0` clean (or warnings without `--strict`), `1` at least one ERROR
(or any WARN under `--strict`, or a missing `--manifest-dir`). An empty directory
is a WARN and exit `0` — a tree with no triggers in it is not a failure.

What the checker will catch in this package if you break it:

| Break | Rule | Severity |
|---|---|---|
| Move the roll-up loop into `WorkOrderTrigger.trigger` | `TF-BODY-01` — logic in the trigger body beyond handler dispatch | ERROR |
| Add `WorkOrderSyncTrigger.trigger` on WorkOrder | `TF-ONE-01` — more than one trigger on an SObject | ERROR |
| Delete the `TriggerHandler.skipOnce(...)` line | `TF-RECUR-01` — after-update handler updates its own object with no recursion guard | ERROR |
| Deploy the subclass without `TriggerHandler.cls` | `TF-PROV-01` — referenced template class not in the tree | ERROR |
| Drop the `with sharing` keyword | `TF-SHARE-01` — handler has no explicit sharing declaration | WARN |

Then run the tests. `RunSpecifiedTests` keeps the feedback loop short while the
handler is still moving:

```bash
sf project deploy start --manifest manifest/package.xml \
    --test-level RunSpecifiedTests --tests WorkOrderTriggerHandlerTest --dry-run
```
