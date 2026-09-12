/**
 * Tier2EscalationService — the escalating transaction's half of the feature.
 *
 * Two things happen here and both belong in the transaction that saved the Case
 * (decision D10):
 *
 *  1. Tier2_Escalation__e is published for the ops dashboard. The event is declared
 *     PublishAfterCommit (M1-S01), so a rolled-back escalation reaches neither the
 *     dashboard nor the on-call tool (Q10).
 *  2. Exactly ONE Tier2WebhookQueueable is enqueued for the whole transaction,
 *     carrying every escalated Case Id (Q13). Never one job per Case: the ceiling is
 *     50 enqueues per synchronous transaction, and a per-Case enqueue passes a
 *     single-record test and fails the first bulk save.
 *
 * The publish is NOT moved inside the Queueable. A publish-after-commit publish is a
 * DML statement, and a callout is not allowed once a transaction has pending
 * uncommitted work — so publishing inside execute() before the callout would break
 * the callout (decision D10, second half).
 *
 * EventBus.publish never throws for a rejected event: the SaveResult is the only
 * failure signal (Q11). A failed publish writes an Integration_Failure__c row with
 * Severity__c Error, which is distinct from a failed webhook row and distinguishable
 * by its blank Endpoint__c.
 *
 * There is no BaseService base class in this build (remedy B, 2026-09-12) — see
 * deploy-order.md section 4.
 */
public with sharing class Tier2EscalationService {

    @TestVisible
    private static final String STATUS_NEW = 'New';

    @TestVisible
    private static final String SEVERITY_ERROR = 'Error';

    /**
     * Publish the escalation events and enqueue the webhook job.
     *
     * @param escalatedCases Cases whose owner just became the Tier 2 queue. Trigger
     *        context records carry every field, so nothing is re-queried here.
     */
    public static void escalate(List<Case> escalatedCases) {
        if (escalatedCases == null || escalatedCases.isEmpty()) {
            return;
        }

        // One timestamp for the whole transaction. It is the escalation time the
        // dashboard dedupes on (Q12) and the second half of every Idempotency-Key
        // (Q8, decision D6), so it is captured once and carried, never recomputed.
        Datetime escalatedAt = System.now();

        String baseUrl = URL.getSalesforceBaseUrl().toExternalForm();

        List<Tier2_Escalation__e> events = new List<Tier2_Escalation__e>();
        Map<Id, Datetime> escalatedAtByCaseId = new Map<Id, Datetime>();
        for (Case c : escalatedCases) {
            events.add(new Tier2_Escalation__e(
                Case_Number__c = c.CaseNumber,
                Subject__c = c.Subject,
                // UNVERIFIED mapping — see deploy-order.md section 5 item 1. No answer
                // maps the event's Severity__c to a Case field; Priority is the only
                // severity-shaped field this build has seen on Case.
                Severity__c = c.Priority,
                Case_Link__c = baseUrl + '/' + c.Id,
                Escalated_At__c = escalatedAt
            ));
            escalatedAtByCaseId.put(c.Id, escalatedAt);
        }

        // The result is assigned and inspected, never discarded: publish() returns
        // normally for a rejected event, so this list is the only place a rejection
        // is visible.
        List<Database.SaveResult> publishResults = EventBus.publish(events);

        List<Integration_Failure__c> publishFailures = new List<Integration_Failure__c>();
        for (Integer i = 0; i < publishResults.size(); i++) {
            Database.SaveResult sr = publishResults[i];
            if (sr.isSuccess()) {
                continue;
            }
            Case c = escalatedCases[i];
            publishFailures.add(new Integration_Failure__c(
                Case__c = c.Id,
                Case_Number__c = c.CaseNumber,
                Status__c = STATUS_NEW,
                Severity__c = SEVERITY_ERROR,
                Attempt_Count__c = 1,
                Last_Attempted_At__c = escalatedAt,
                // Endpoint__c is deliberately left blank: no callout was attempted.
                // A blank Endpoint__c with an error message is how an admin tells a
                // publish failure from a webhook failure.
                Error_Message__c = 'Tier2_Escalation__e publish rejected: '
                    + errorText(sr.getErrors())
            ));
        }

        // Enqueue before the failure-row DML so the job is queued even if the row
        // insert partially fails; the webhook is the primary channel and a lost event
        // is the tolerable half (Q11).
        System.enqueueJob(new Tier2WebhookQueueable(escalatedAtByCaseId));

        if (!publishFailures.isEmpty()) {
            insert publishFailures;
        }
    }

    /**
     * Flatten a SaveResult's errors into one readable line.
     *
     * getMessage() only. Database.Error also exposes a status code, but this build has
     * no source it can copy that accessor's exact name from, and a plausible-looking
     * name that does not compile is worse than a message that carries the detail
     * anyway (AGENT_CONTRACT.md rule 12).
     */
    @TestVisible
    private static String errorText(List<Database.Error> errors) {
        if (errors == null || errors.isEmpty()) {
            return 'no error detail returned';
        }
        List<String> parts = new List<String>();
        for (Database.Error e : errors) {
            parts.add(e.getMessage());
        }
        return String.join(parts, ' | ');
    }
}
