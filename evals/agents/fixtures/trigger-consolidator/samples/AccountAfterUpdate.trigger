/**
 * AccountAfterUpdate — synthetic sample for trigger-consolidator eval.
 * Has a handler class but the handler does NOT extend the canonical
 * TriggerHandler framework. Belongs in the "ad-hoc handler" bucket the
 * consolidator must classify.
 */
trigger AccountAfterUpdate on Account (after update) {
    AccountAfterUpdateService.syncToWarehouse(Trigger.newMap, Trigger.oldMap);
}
