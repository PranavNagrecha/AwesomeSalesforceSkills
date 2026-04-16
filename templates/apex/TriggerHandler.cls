/**
 * TriggerHandler — canonical base class for all Apex trigger dispatch.
 *
 * Design goals:
 *  - Single entry point (`run()`) for every object trigger.
 *  - Explicit dispatch to virtual methods per trigger context.
 *  - Recursion guard using `skipOnce()` + per-class depth counter.
 *  - Declarative activation via `TriggerControl` (Custom Metadata + Custom Permissions).
 *
 * Do not add object-specific logic here. Subclass it:
 *
 *     public class AccountTriggerHandler extends TriggerHandler {
 *         protected override void beforeInsert() { ... }
 *         protected override void afterUpdate()  { ... }
 *     }
 *
 * And invoke from the trigger body:
 *
 *     trigger AccountTrigger on Account (before insert, before update, after insert, after update) {
 *         new AccountTriggerHandler().run();
 *     }
 */
public virtual class TriggerHandler {

    @TestVisible private static Map<String, Integer> depthByHandler = new Map<String, Integer>();
    @TestVisible private static Set<String> skipOnceHandlers = new Set<String>();

    private static final Integer MAX_DEPTH = 10;

    public void run() {
        if (!Trigger.isExecuting && !Test.isRunningTest()) {
            return;
        }

        String handlerName = String.valueOf(this).split(':')[0];
        String sObjectName = inferSObjectName();

        if (!TriggerControl.isActive(sObjectName, handlerName)) {
            return;
        }

        if (skipOnceHandlers.remove(handlerName)) {
            return;
        }

        Integer depth = depthByHandler.get(handlerName);
        if (depth == null) { depth = 0; }
        if (depth >= MAX_DEPTH) {
            throw new TriggerHandlerException(
                'Recursion depth exceeded for ' + handlerName + ' on ' + sObjectName
            );
        }
        depthByHandler.put(handlerName, depth + 1);

        try {
            dispatch();
        } finally {
            depthByHandler.put(handlerName, depthByHandler.get(handlerName) - 1);
        }
    }

    public static void skipOnce(String handlerName) {
        skipOnceHandlers.add(handlerName);
    }

    protected virtual void dispatch() {
        if (Trigger.isBefore) {
            if (Trigger.isInsert) { beforeInsert(); }
            else if (Trigger.isUpdate) { beforeUpdate(); }
            else if (Trigger.isDelete) { beforeDelete(); }
        } else if (Trigger.isAfter) {
            if (Trigger.isInsert) { afterInsert(); }
            else if (Trigger.isUpdate) { afterUpdate(); }
            else if (Trigger.isDelete) { afterDelete(); }
            else if (Trigger.isUndelete) { afterUndelete(); }
        }
    }

    protected virtual void beforeInsert() {}
    protected virtual void beforeUpdate() {}
    protected virtual void beforeDelete() {}
    protected virtual void afterInsert()  {}
    protected virtual void afterUpdate()  {}
    protected virtual void afterDelete()  {}
    protected virtual void afterUndelete(){}

    private String inferSObjectName() {
        List<SObject> records = Trigger.new != null ? Trigger.new : Trigger.old;
        if (records == null || records.isEmpty()) {
            return 'Unknown';
        }
        return String.valueOf(records[0].getSObjectType());
    }

    public class TriggerHandlerException extends Exception {}
}
