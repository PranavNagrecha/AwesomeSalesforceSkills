/**
 * CaseTriggerHandler — all Case trigger logic for the Tier 2 escalation feature.
 *
 * Sharing is written out on purpose. The .trigger file always runs in system mode
 * and cannot carry a sharing keyword, so this class is the only place the decision
 * is expressible. At apiVersion 67.0 an absent keyword would still mean user mode
 * for SOQL and DML; `with sharing` states the intent rather than relying on it.
 *
 * Detection (step input `detection`, assumption A12): an after-update save in which
 * OwnerId changed and the new owner is the Tier_2_Engineering queue.
 *
 * The queue is resolved by DeveloperName and cached for the transaction — there is no
 * Id literal anywhere in this build. The shape is
 * skills/apex/apex-hardcoded-id-elimination/references/examples.md Example 3
 * ("Group/Queue assignment for Case routing"), minus its CustomMetadata mapping,
 * which this feature does not need: there is exactly one queue to resolve.
 *
 * This build ships no TriggerControl kill switch (remedy B, 2026-09-12). See
 * deploy-order.md section 4.
 */
public with sharing class CaseTriggerHandler {

    /** The escalation queue, by DeveloperName. Never an Id literal (assumption A8). */
    @TestVisible
    private static final String TIER2_QUEUE_DEVELOPER_NAME = 'Tier_2_Engineering';

    /** Duplicate-suppression window, in minutes (Q14, decision D13). */
    @TestVisible
    private static final Integer SUPPRESSION_WINDOW_MINUTES = 10;

    /** Queue Ids by DeveloperName, resolved at most once per transaction. */
    private static Map<String, Id> queueIdByDevName;

    /**
     * Cases this handler has already escalated in this transaction.
     *
     * The per-transaction recursion guard. It is a Set<Id> rather than a static
     * Boolean because a Boolean would block every record of a bulk save after the
     * first re-entry, where only the already-escalated ones should be skipped
     * (skills/apex/recursive-trigger-prevention/references/examples.md).
     *
     * The webhook stamps Case.Tier2_Notified_At__c on success, which updates Case and
     * re-enters this trigger. That re-entry does not change OwnerId, so the detection
     * below would already reject it; the guard is the belt to that pair of braces.
     */
    @TestVisible
    private static Set<Id> escalatedCaseIds = new Set<Id>();

    @TestVisible
    private static void resetForTest() {
        escalatedCaseIds.clear();
        queueIdByDevName = null;
    }

    /**
     * Resolve a queue Id from its DeveloperName, one SOQL per transaction.
     *
     * Returns null when the org has no queue by that name — the caller decides what
     * that means rather than this method inventing a fallback.
     */
    @TestVisible
    private static Id queueId(String devName) {
        if (queueIdByDevName == null) {
            queueIdByDevName = new Map<String, Id>();
            for (Group g : [
                SELECT Id, DeveloperName
                FROM Group
                WHERE Type = 'Queue'
                WITH USER_MODE
            ]) {
                queueIdByDevName.put(g.DeveloperName, g.Id);
            }
        }
        return queueIdByDevName.get(devName);
    }

    /**
     * True when this Case was notified inside the suppression window.
     *
     * Cross-transaction suppression, per decision D13. AsyncOptions.DuplicateSignature
     * is the rejected alternative and is not used: a suppressed enqueue throws
     * DuplicateMessageException rather than no-op'ing, and the field stamp doubles as
     * the audit trail an admin reads on the Case.
     */
    @TestVisible
    private static Boolean isWithinSuppressionWindow(Case c) {
        if (c.Tier2_Notified_At__c == null) {
            return false;
        }
        return c.Tier2_Notified_At__c > System.now().addMinutes(-SUPPRESSION_WINDOW_MINUTES);
    }

    /**
     * after update: escalate every Case whose owner just became the Tier 2 queue.
     *
     * Bulk-safe throughout — one pass to find owner changes, at most one SOQL to
     * resolve the queue, one hand-off to the service for the whole transaction.
     */
    public static void afterUpdate(List<Case> newCases, Map<Id, Case> oldMap) {
        if (newCases == null || newCases.isEmpty() || oldMap == null) {
            return;
        }

        // Pass 1: owner changed at all? Cheap, and it keeps the Group query off every
        // Case save that has nothing to do with escalation.
        List<Case> ownerChanged = new List<Case>();
        for (Case c : newCases) {
            Case prior = oldMap.get(c.Id);
            if (prior != null && c.OwnerId != prior.OwnerId) {
                ownerChanged.add(c);
            }
        }
        if (ownerChanged.isEmpty()) {
            return;
        }

        Id tier2QueueId = queueId(TIER2_QUEUE_DEVELOPER_NAME);
        if (tier2QueueId == null) {
            // Assumption A8 says the queue exists. If it does not, escalation is
            // silently impossible, so say so where an admin debugging a missing page
            // will find it. Integration_Failure__c is the visible log for delivery
            // attempts; this is a configuration fault before any attempt exists.
            System.debug(
                LoggingLevel.ERROR,
                'CaseTriggerHandler: no queue with DeveloperName '
                    + TIER2_QUEUE_DEVELOPER_NAME
                    + ' is visible to this user; no Tier 2 escalation was raised for '
                    + ownerChanged.size() + ' owner change(s).'
            );
            return;
        }

        // Pass 2: of those, which are escalations this transaction has not handled and
        // the suppression window does not cover?
        List<Case> escalated = new List<Case>();
        for (Case c : ownerChanged) {
            if (c.OwnerId != tier2QueueId) {
                continue;
            }
            if (escalatedCaseIds.contains(c.Id)) {
                continue;
            }
            if (isWithinSuppressionWindow(c)) {
                continue;
            }
            escalated.add(c);
        }
        if (escalated.isEmpty()) {
            return;
        }

        for (Case c : escalated) {
            escalatedCaseIds.add(c.Id);
        }
        Tier2EscalationService.escalate(escalated);
    }
}
