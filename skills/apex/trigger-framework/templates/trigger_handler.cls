/**
 * [ObjectName]TriggerHandler
 *
 * Purpose:    Handles all trigger logic for [ObjectName] (see [ObjectName]Trigger).
 * Owner:      TODO: Team/individual
 * Dependencies: [ObjectName]Service, TestDataFactory (tests)
 *
 * WAF Pillars: Scalability (bulkified), Reliability (recursion guard), Security (with sharing)
 */
public with sharing class [ObjectName]TriggerHandler {

    // ─── Recursion Guard ───────────────────────────────────────────────────────
    // Set-based guard tracks processed record IDs this transaction.
    // More precise than a boolean flag — allows new records in the same
    // transaction to be processed while blocking already-handled records.
    private static Set<Id> processedIds = new Set<Id>();

    // @TestVisible allows test classes to reset static state between test methods
    @TestVisible
    private static void resetForTest() {
        processedIds.clear();
    }

    // ─── Before Save Contexts ─────────────────────────────────────────────────
    // Use for: field updates on the triggering record, validation
    // Do NOT use for: DML on other objects, callouts

    public void onBeforeInsert(List<[ObjectName]> newRecords) {
        // TODO: Add before-insert logic
        // Example: [ObjectName]Service.setDefaults(newRecords);
    }

    public void onBeforeUpdate(List<[ObjectName]> newRecords, Map<Id, [ObjectName]> oldMap) {
        // Delta check — only process records where relevant fields changed
        List<[ObjectName]> changed = new List<[ObjectName]>();
        for ([ObjectName] record : newRecords) {
            // TODO: Replace with your field name
            if (record.Status__c != oldMap.get(record.Id).Status__c) {
                changed.add(record);
            }
        }
        if (changed.isEmpty()) return;

        // TODO: [ObjectName]Service.handleStatusChange(changed, oldMap);
    }

    public void onBeforeDelete(List<[ObjectName]> oldRecords) {
        // TODO: Add before-delete logic, or leave empty
    }

    // ─── After Save Contexts ──────────────────────────────────────────────────
    // Use for: DML on related objects, callouts (via @future/Queueable), async

    public void onAfterInsert(List<[ObjectName]> newRecords) {
        // Recursion guard
        List<[ObjectName]> toProcess = filterUnprocessed(newRecords);
        if (toProcess.isEmpty()) return;

        // TODO: [ObjectName]Service.createRelatedRecords(toProcess);
    }

    public void onAfterUpdate(List<[ObjectName]> newRecords, Map<Id, [ObjectName]> oldMap) {
        // Recursion guard
        List<[ObjectName]> toProcess = filterUnprocessed(newRecords);
        if (toProcess.isEmpty()) return;

        // TODO: [ObjectName]Service.handlePostUpdateSideEffects(toProcess, oldMap);
    }

    public void onAfterDelete(Map<Id, [ObjectName]> oldMap) {
        // TODO: Add after-delete logic, or leave empty
    }

    public void onAfterUndelete(List<[ObjectName]> newRecords) {
        // TODO: Add after-undelete logic, or leave empty
    }

    // ─── Private Helpers ──────────────────────────────────────────────────────

    private List<[ObjectName]> filterUnprocessed(List<[ObjectName]> records) {
        List<[ObjectName]> result = new List<[ObjectName]>();
        for ([ObjectName] rec : records) {
            if (!processedIds.contains(rec.Id)) {
                processedIds.add(rec.Id);
                result.add(rec);
            }
        }
        return result;
    }
}
