/**
 * [ObjectName]Trigger
 *
 * Purpose:    Single trigger for [ObjectName]. All logic in [ObjectName]TriggerHandler.
 * Owner:      TODO: Team/individual
 *
 * Activation: Controlled via Trigger_Setting__mdt — set Is_Active__c = false to disable
 *             without deployment (e.g. during data migrations).
 */
trigger [ObjectName]Trigger on [ObjectName] (
    before insert, before update, before delete,
    after insert, after update, after delete, after undelete
) {
    // ─── Activation Bypass ────────────────────────────────────────────────────
    // Allows disabling this trigger via Custom Metadata without a deployment.
    // Usage: In Setup → Custom Metadata → Trigger_Setting__mdt, set Is_Active__c = false.
    Trigger_Setting__mdt[] settings = [
        SELECT Is_Active__c
        FROM Trigger_Setting__mdt
        WHERE Object_API_Name__c = '[ObjectAPIName]'
        LIMIT 1
    ];
    if (!settings.isEmpty() && !settings[0].Is_Active__c) {
        return;
    }

    // ─── Handler Dispatch ─────────────────────────────────────────────────────
    // Zero logic in trigger body. Handler class handles all routing and execution.
    [ObjectName]TriggerHandler handler = new [ObjectName]TriggerHandler();

    if (Trigger.isBefore) {
        if (Trigger.isInsert) handler.onBeforeInsert(Trigger.new);
        if (Trigger.isUpdate) handler.onBeforeUpdate(Trigger.new, Trigger.oldMap);
        if (Trigger.isDelete) handler.onBeforeDelete(Trigger.old);
    }

    if (Trigger.isAfter) {
        if (Trigger.isInsert)   handler.onAfterInsert(Trigger.new);
        if (Trigger.isUpdate)   handler.onAfterUpdate(Trigger.new, Trigger.oldMap);
        if (Trigger.isDelete)   handler.onAfterDelete(Trigger.oldMap);
        if (Trigger.isUndelete) handler.onAfterUndelete(Trigger.new);
    }
}
