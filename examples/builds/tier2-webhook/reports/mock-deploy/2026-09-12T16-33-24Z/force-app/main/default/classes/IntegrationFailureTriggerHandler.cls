/**
 * IntegrationFailureTriggerHandler — the admin resend path.
 *
 * An admin ticks Resend__c on a failure row; this handler re-enters the SAME
 * Tier2WebhookQueueable the escalation path uses, marks the row Retrying and clears
 * the checkbox. It emits no callout, publishes no event and defines no class the
 * escalation path does not already need — which is the whole reason the resend lives
 * in this step rather than one of its own.
 *
 * Sharing is declared here because the .trigger file cannot carry the keyword.
 *
 * Suppression does not apply to a resend: an admin asking for a replay has overridden
 * the ten-minute window on purpose, so the job is constructed with isResend true.
 */
public with sharing class IntegrationFailureTriggerHandler {

    /** Restricted picklist value from M1-S01 (Q17). */
    @TestVisible
    private static final String STATUS_RETRYING = 'Retrying';

    /**
     * Rows this handler has already re-enqueued in this transaction.
     *
     * Load-bearing, not decorative: the last thing this handler does is update the
     * rows it just processed, which re-enters this same trigger. The re-entry sets
     * Resend__c false, so the "just became true" test below already rejects it — this
     * set is the guard that does not depend on that ordering staying true.
     */
    @TestVisible
    private static Set<Id> resentRowIds = new Set<Id>();

    @TestVisible
    private static void resetForTest() {
        resentRowIds.clear();
    }

    public static void afterUpdate(
        List<Integration_Failure__c> newRows,
        Map<Id, Integration_Failure__c> oldMap
    ) {
        if (newRows == null || newRows.isEmpty() || oldMap == null) {
            return;
        }

        List<Integration_Failure__c> toResend = new List<Integration_Failure__c>();
        for (Integration_Failure__c row : newRows) {
            Integration_Failure__c prior = oldMap.get(row.Id);
            if (prior == null) {
                continue;
            }
            if (row.Resend__c != true || prior.Resend__c == true) {
                continue;
            }
            if (resentRowIds.contains(row.Id)) {
                continue;
            }
            if (row.Case__c == null) {
                // Case__c is SetNull on delete, so a row can outlive its Case. There
                // is nothing to re-send and no Case Id to build a key from.
                System.debug(
                    LoggingLevel.WARN,
                    'IntegrationFailureTriggerHandler: row ' + row.Id
                        + ' has no Case; resend ignored.'
                );
                continue;
            }
            toResend.add(row);
        }
        if (toResend.isEmpty()) {
            return;
        }

        Map<Id, Datetime> escalatedAtByCaseId = new Map<Id, Datetime>();
        Map<Id, Id> failureRowIdByCaseId = new Map<Id, Id>();
        List<Integration_Failure__c> toUpdate = new List<Integration_Failure__c>();

        for (Integration_Failure__c row : toResend) {
            resentRowIds.add(row.Id);
            escalatedAtByCaseId.put(row.Case__c, originalEscalationTime(row));
            failureRowIdByCaseId.put(row.Case__c, row.Id);
            toUpdate.add(new Integration_Failure__c(
                Id = row.Id,
                Status__c = STATUS_RETRYING,
                Resend__c = false
            ));
        }

        // One job for every row resent in this save, never one per row (Q13).
        System.enqueueJob(
            new Tier2WebhookQueueable(escalatedAtByCaseId, failureRowIdByCaseId, 1, true)
        );

        update toUpdate;
    }

    /**
     * The escalation timestamp this row's original attempt used.
     *
     * Read back from Request_Payload__c so the replayed Idempotency-Key is identical
     * to the one that failed (Q8, decision D6, assumption A10). escalatedAtMillis is
     * read rather than the ISO string beside it because milliseconds parse back into
     * a Datetime without a format assumption.
     *
     * A row written by Tier2WebhookFinalizer carries the envelope but no body; a row
     * from an older build, or one an admin created by hand, may carry neither. In
     * that case the key cannot be replayed exactly and the fallback says so in the
     * debug log rather than pretending otherwise.
     */
    @TestVisible
    private static Datetime originalEscalationTime(Integration_Failure__c row) {
        if (String.isNotBlank(row.Request_Payload__c)) {
            try {
                Object parsed = JSON.deserializeUntyped(row.Request_Payload__c);
                if (parsed instanceof Map<String, Object>) {
                    Object millis = ((Map<String, Object>) parsed).get('escalatedAtMillis');
                    if (millis != null) {
                        return Datetime.newInstance(Long.valueOf(String.valueOf(millis)));
                    }
                }
            } catch (Exception e) {
                System.debug(
                    LoggingLevel.WARN,
                    'IntegrationFailureTriggerHandler: Request_Payload__c on row ' + row.Id
                        + ' could not be parsed for escalatedAtMillis (' + e.getMessage()
                        + '); falling back to Last_Attempted_At__c.'
                );
            }
        }
        if (row.Last_Attempted_At__c != null) {
            System.debug(
                LoggingLevel.WARN,
                'IntegrationFailureTriggerHandler: row ' + row.Id + ' carries no stored '
                    + 'escalation time; the resend uses Last_Attempted_At__c, so its '
                    + 'Idempotency-Key will differ from the original attempt.'
            );
            return row.Last_Attempted_At__c;
        }
        System.debug(
            LoggingLevel.WARN,
            'IntegrationFailureTriggerHandler: row ' + row.Id + ' carries neither a stored '
                + 'escalation time nor Last_Attempted_At__c; the resend uses the current '
                + 'time and its Idempotency-Key will differ from the original attempt.'
        );
        return System.now();
    }
}
