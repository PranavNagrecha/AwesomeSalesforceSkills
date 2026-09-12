/**
 * Tier2WebhookFinalizer — the only place a webhook retry is decided.
 *
 * Runs in its own Apex and database transaction after Tier2WebhookQueueable
 * completes, however it completed: caught exception, uncaught exception, or platform
 * termination. That is why the retry lives here and not in a catch block — a catch
 * only sees caught exceptions, and a limit exception or a platform termination
 * bypasses it entirely, leaving no cleanup and no failure record.
 *
 * FinalizerContext has exactly four methods and getJobId() is not one of them:
 * getAsyncApexJobId(), getRequestId(), getResult() and getException()
 * (step input `finalizer_contract`, Q15).
 *
 * Sharing is declared on purpose: a Finalizer runs as the async context user, and at
 * apiVersion 67.0 its DML enforces that user's permissions by default. The rows it
 * writes need Tier2_Webhook_Admin, per decision D14.
 */
public with sharing class Tier2WebhookFinalizer implements System.Finalizer {

    @TestVisible
    private static final Integer MAX_ATTEMPTS = 3;

    /**
     * Back-off between attempts, in minutes. AsyncOptions caps this at 10, and a
     * Finalizer may re-enqueue a failed job five consecutive times, so three attempts
     * sits inside both ceilings (step input `retry_contract`).
     *
     * The delay is IGNORED during Apex testing, so no test in this step asserts on
     * the interval — asserting on observed timing would prove nothing. See
     * deploy-order.md section 5 item 3.
     */
    @TestVisible
    private static final Integer BACKOFF_MINUTES = 5;

    /** Restricted picklist values from M1-S01 (Q17). Nothing else is ever written. */
    @TestVisible
    private static final String STATUS_RETRYING = 'Retrying';
    @TestVisible
    private static final String STATUS_ABANDONED = 'Abandoned';
    @TestVisible
    private static final String SEVERITY_ERROR = 'Error';

    private final Map<Id, Datetime> escalatedAtByCaseId;
    private final Map<Id, Id> failureRowIdByCaseId;
    private final Integer attempt;
    private final Boolean isResend;

    public Tier2WebhookFinalizer(
        Map<Id, Datetime> escalatedAtByCaseId,
        Map<Id, Id> failureRowIdByCaseId,
        Integer attempt,
        Boolean isResend
    ) {
        this.escalatedAtByCaseId = escalatedAtByCaseId == null
            ? new Map<Id, Datetime>()
            : escalatedAtByCaseId;
        this.failureRowIdByCaseId = failureRowIdByCaseId == null
            ? new Map<Id, Id>()
            : failureRowIdByCaseId;
        this.attempt = attempt == null ? 1 : attempt;
        this.isResend = isResend == true;
    }

    public void execute(FinalizerContext ctx) {
        if (ctx == null) {
            return;
        }

        if (ctx.getResult() == ParentJobResult.SUCCESS) {
            // The parent already recorded every outcome it decided. Completion is
            // noted where a support engineer correlating with Event Monitoring can
            // find it, and nowhere else: a success is not an Integration_Failure__c.
            System.debug(
                LoggingLevel.INFO,
                'Tier2WebhookFinalizer: attempt ' + attempt + ' completed for '
                    + escalatedAtByCaseId.size() + ' Case(s). AsyncApexJob '
                    + ctx.getAsyncApexJobId() + ', request ' + ctx.getRequestId() + '.'
            );
            return;
        }

        // The parent threw. Nothing it attempted was persisted, so the whole batch is
        // in the same state and this Finalizer records it as one.
        Boolean willRetry = attempt < MAX_ATTEMPTS;
        String failureText = ctx.getException() == null
            ? 'The webhook job ended with an unhandled exception and no exception detail.'
            : ctx.getException().getTypeName() + ': ' + ctx.getException().getMessage();

        Map<Id, Id> rowIdByCaseId = recordAttempt(ctx, willRetry, failureText);

        if (!willRetry) {
            System.debug(
                LoggingLevel.ERROR,
                'Tier2WebhookFinalizer: attempt budget of ' + MAX_ATTEMPTS
                    + ' is spent for ' + escalatedAtByCaseId.size()
                    + ' Case(s); rows left Abandoned for an admin to resend.'
            );
            return;
        }

        // Re-enqueue the whole batch. Every Case keeps its original escalation
        // timestamp, so each Idempotency-Key is byte-identical to the one the failed
        // attempt sent and the on-call tool can discard the repeat.
        AsyncOptions opts = new AsyncOptions();
        opts.MinimumQueueableDelayInMinutes = BACKOFF_MINUTES;
        System.enqueueJob(
            new Tier2WebhookQueueable(
                escalatedAtByCaseId,
                rowIdByCaseId,
                attempt + 1,
                isResend
            ),
            opts
        );
    }

    /**
     * Write or update one Integration_Failure__c row per Case in the batch, and
     * return the row Id for each so the next attempt can resolve them rather than
     * inserting duplicates.
     *
     * One row per Case is accurate rather than over-reporting: the parent threw
     * before persisting anything, so every Case in the batch really is in the same
     * unconfirmed state and really will be re-sent together.
     */
    private Map<Id, Id> recordAttempt(FinalizerContext ctx, Boolean willRetry, String failureText) {
        Datetime now = System.now();
        String status = willRetry ? STATUS_RETRYING : STATUS_ABANDONED;
        String message = failureText
            + ' (attempt ' + attempt + ' of ' + MAX_ATTEMPTS
            + ', AsyncApexJob ' + ctx.getAsyncApexJobId()
            + ', request ' + ctx.getRequestId() + ')';

        Map<Id, Id> rowIdByCaseId = new Map<Id, Id>();
        List<Integration_Failure__c> toInsert = new List<Integration_Failure__c>();
        List<Id> insertedForCaseIds = new List<Id>();
        List<Integration_Failure__c> toUpdate = new List<Integration_Failure__c>();

        Map<Id, Case> caseById = new Map<Id, Case>([
            SELECT Id, CaseNumber
            FROM Case
            WHERE Id IN :escalatedAtByCaseId.keySet()
            WITH USER_MODE
        ]);

        for (Id caseId : escalatedAtByCaseId.keySet()) {
            Id existingRowId = failureRowIdByCaseId.get(caseId);
            if (existingRowId == null) {
                Case c = caseById.get(caseId);
                toInsert.add(new Integration_Failure__c(
                    Case__c = caseId,
                    Case_Number__c = c == null ? null : c.CaseNumber,
                    Status__c = status,
                    Severity__c = SEVERITY_ERROR,
                    Attempt_Count__c = attempt,
                    Last_Attempted_At__c = now,
                    Error_Message__c = message,
                    Request_Payload__c = Tier2WebhookQueueable.pendingEnvelope(
                        caseId, escalatedAtByCaseId.get(caseId)
                    )
                ));
                insertedForCaseIds.add(caseId);
            } else {
                toUpdate.add(new Integration_Failure__c(
                    Id = existingRowId,
                    Status__c = status,
                    Severity__c = SEVERITY_ERROR,
                    Resend__c = false,
                    Attempt_Count__c = attempt,
                    Last_Attempted_At__c = now,
                    Error_Message__c = message
                ));
                rowIdByCaseId.put(caseId, existingRowId);
            }
        }

        if (!toInsert.isEmpty()) {
            insert toInsert;
            for (Integer i = 0; i < toInsert.size(); i++) {
                rowIdByCaseId.put(insertedForCaseIds[i], toInsert[i].Id);
            }
        }
        if (!toUpdate.isEmpty()) {
            update toUpdate;
        }
        return rowIdByCaseId;
    }
}
