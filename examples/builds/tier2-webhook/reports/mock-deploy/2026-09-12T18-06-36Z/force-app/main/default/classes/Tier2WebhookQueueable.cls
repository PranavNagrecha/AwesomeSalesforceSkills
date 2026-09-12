/**
 * Tier2WebhookQueueable — POSTs each escalated Case to the on-call tool.
 *
 * One job per transaction, carrying every escalated Case Id (Q13), never one per Case.
 *
 * Runtime order inside execute() is fixed and is decision D10's second half: every
 * callout happens first, then the DML that stamps Case.Tier2_Notified_At__c and writes
 * Integration_Failure__c. A callout is not allowed once the transaction has pending
 * uncommitted work; Database.AllowsCallouts grants permission, not ordering.
 *
 * METHOD ORDER IN THIS FILE IS DELIBERATE. The callout path is declared before any
 * method that performs DML, mirroring that runtime order —
 * skills/apex/callouts-and-http-integrations/scripts/check_callouts_and_http_integrations.py
 * reads a class body as one span and flags any DML token that precedes the first
 * callout offset, so the layout and the rule it encodes are the same fact.
 *
 * Retry is the Finalizer's, not this class's (step input `retry_contract`). On a
 * transient failure this job throws BEFORE writing anything, so nothing is half
 * persisted and Tier2WebhookFinalizer owns the whole decision. That means a
 * mixed-outcome batch is re-POSTed whole on the next attempt; the Idempotency-Key is
 * what makes that safe, and it is stable across attempts because the escalation
 * timestamp is captured once at enqueue time and carried (Q8, decision D6,
 * assumption A10).
 *
 * No HttpClient wrapper and no ApplicationLogger in this build (remedy B,
 * 2026-09-12) — see deploy-order.md section 4. The visible log is
 * Integration_Failure__c; everything else is System.debug.
 */
public with sharing class Tier2WebhookQueueable implements Queueable, Database.AllowsCallouts {

    /**
     * Named Credential API name. Identical in every org; only its Url parameter
     * differs (assumption A7). The credential's Url already carries the full path
     * (M1-S02), so NO path segment is appended here — step input `callout_endpoint`.
     */
    @TestVisible
    private static final String NAMED_CREDENTIAL = 'OnCall_Tool';

    /**
     * Explicit timeout. The platform default is 10 s and every callout draws on the
     * same 120 s per-transaction budget; 50 Cases at 20 s worst case would exceed it,
     * which is what MAX_CASES_PER_JOB below bounds.
     */
    @TestVisible
    private static final Integer CALLOUT_TIMEOUT_MS = 20000;

    /** Total attempts including the first (step input `retry_contract`, Q7). */
    @TestVisible
    private static final Integer MAX_ATTEMPTS = 3;

    /**
     * Cases per job. One callout per Case (assumption A6) against a ceiling of 100
     * callouts per transaction; 50 is the worst single burst the requester described
     * (Q22) and leaves the second half of the budget as headroom. A larger set is
     * chained rather than truncated.
     */
    @TestVisible
    private static final Integer MAX_CASES_PER_JOB = 50;

    /** Chain cap. No production edition enforces one, so AsyncOptions must. */
    @TestVisible
    private static final Integer MAX_CHAIN_DEPTH = 10;

    /** Transient: retry. Connection failures arrive as status 0 (Q7). */
    @TestVisible
    private static final Set<Integer> TRANSIENT_STATUSES = new Set<Integer>{ 429, 502, 503, 504 };

    /** Permanent: no retry. Retrying a 400 or a 422 just re-sends a bad request (Q7). */
    @TestVisible
    private static final Set<Integer> PERMANENT_STATUSES = new Set<Integer>{ 400, 401, 403, 404, 422 };

    /** Restricted picklist values from M1-S01. Nothing else is ever written (Q17). */
    @TestVisible
    private static final String STATUS_NEW = 'New';
    @TestVisible
    private static final String STATUS_RESENT = 'Resent';
    @TestVisible
    private static final String STATUS_RESOLVED = 'Resolved';
    @TestVisible
    private static final String STATUS_ABANDONED = 'Abandoned';
    @TestVisible
    private static final String SEVERITY_ERROR = 'Error';

    /** Duplicate-suppression window, in minutes (Q14, decision D13). */
    @TestVisible
    private static final Integer SUPPRESSION_WINDOW_MINUTES = 10;

    public class Tier2WebhookException extends Exception {}

    /** What one POST did. Not persisted directly; phase 3 turns these into records. */
    private class Attempt {
        public Id caseId;
        public Integer statusCode;
        public String responseBody;
        public String errorMessage;
        public String requestPayload;
        public Boolean succeeded = false;
        public Boolean transientFailure = false;
    }

    // ── State carried across the async boundary ──────────────────────────────────

    /**
     * Escalation timestamp per Case. A Map rather than a List plus one Datetime
     * because the resend path replays each row's own original timestamp, so the
     * Idempotency-Key it rebuilds is byte-identical to the one that failed.
     */
    private final Map<Id, Datetime> escalatedAtByCaseId;

    /** Existing failure rows to update, when this job is a retry or an admin resend. */
    private final Map<Id, Id> failureRowIdByCaseId;

    /** 1 for the first attempt (step input `retry_contract`). */
    private final Integer attempt;

    /** An admin asked for this explicitly, so the suppression window does not apply. */
    private final Boolean isResend;

    /** The escalation path: first attempt, no prior rows, suppression applies. */
    public Tier2WebhookQueueable(Map<Id, Datetime> escalatedAtByCaseId) {
        this(escalatedAtByCaseId, new Map<Id, Id>(), 1, false);
    }

    /** The retry and resend paths. */
    public Tier2WebhookQueueable(
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

    // ── Classification and payload — no DML, no callout ──────────────────────────

    @TestVisible
    private static Boolean isTransientStatus(Integer statusCode) {
        // Status 0 is this class's marker for "never reached a response" — a
        // connection failure or a timeout, which step input `retry_contract` groups
        // with the transient codes.
        return statusCode == 0 || TRANSIENT_STATUSES.contains(statusCode);
    }

    @TestVisible
    private static Boolean isPermanentStatus(Integer statusCode) {
        return PERMANENT_STATUSES.contains(statusCode);
    }

    @TestVisible
    private static Boolean isWithinSuppressionWindow(Case c) {
        if (c.Tier2_Notified_At__c == null) {
            return false;
        }
        return c.Tier2_Notified_At__c > System.now().addMinutes(-SUPPRESSION_WINDOW_MINUTES);
    }

    /** Case Id plus the escalation timestamp (Q8, decision D6). Stable across attempts. */
    @TestVisible
    private static String idempotencyKey(Id caseId, Datetime escalatedAt) {
        return String.valueOf(caseId) + ':' + String.valueOf(escalatedAt.getTime());
    }

    /**
     * The JSON recorded on Request_Payload__c: the body sent plus the
     * Idempotency-Key used, so a resend replays the identical request. escalatedAt is
     * carried twice — ISO for a human reading the record, epoch milliseconds because
     * that is what the resend path parses back into a Datetime without a format guess.
     */
    @TestVisible
    private static String requestEnvelope(String key, Datetime escalatedAt, String body) {
        Map<String, Object> envelope = new Map<String, Object>{
            'endpoint' => 'callout:' + NAMED_CREDENTIAL,
            'idempotencyKey' => key,
            'escalatedAt' => escalatedAt.formatGmt('yyyy-MM-dd\'T\'HH:mm:ss\'Z\''),
            'escalatedAtMillis' => escalatedAt.getTime(),
            'body' => body
        };
        return JSON.serialize(envelope);
    }

    /**
     * The envelope for an attempt that never reached the persistence phase.
     *
     * Tier2WebhookFinalizer calls this: the parent job threw before writing anything,
     * so the Finalizer has the Case Id and the escalation timestamp but not the body
     * that was built and rolled back. Recording the key and the timestamp is what lets
     * a later admin resend replay the identical Idempotency-Key; body is null because
     * the Finalizer genuinely does not have it, not because it was empty.
     */
    public static String pendingEnvelope(Id caseId, Datetime escalatedAt) {
        return requestEnvelope(idempotencyKey(caseId, escalatedAt), escalatedAt, null);
    }

    @TestVisible
    private static String requestBody(Case c, Datetime escalatedAt) {
        return JSON.serialize(new Map<String, Object>{
            'caseId' => String.valueOf(c.Id),
            'caseNumber' => c.CaseNumber,
            'subject' => c.Subject,
            'priority' => c.Priority,
            'status' => c.Status,
            'escalatedAt' => escalatedAt.formatGmt('yyyy-MM-dd\'T\'HH:mm:ss\'Z\''),
            // getOrgDomainUrl(), not getSalesforceBaseUrl(): removed after version 58.0
            // and these classes are pinned to 67.0 (S2-F-04, deploy-order.md § 0).
            'caseUrl' => URL.getOrgDomainUrl().toExternalForm() + '/' + c.Id
        });
    }

    // ── The callout path. Declared before every DML method on purpose. ───────────

    /**
     * POST one Case. Sets no Authorization and no X-API-Key header and reads no
     * credential value: the External Credential's AuthHeader parameter is what the
     * platform injects at callout time (M1-S02, Q5). The endpoint is
     * callout:OnCall_Tool with no path appended — the Named Credential's Url is
     * already the full endpoint.
     */
    @TestVisible
    private static Attempt attemptOne(Case c, Datetime escalatedAt) {
        Attempt out = new Attempt();
        out.caseId = c.Id;

        String key = idempotencyKey(c.Id, escalatedAt);
        String body = requestBody(c, escalatedAt);
        out.requestPayload = requestEnvelope(key, escalatedAt, body);

        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:' + NAMED_CREDENTIAL);
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/json');
        req.setHeader('Accept', 'application/json');
        req.setHeader('Idempotency-Key', key);
        req.setTimeout(CALLOUT_TIMEOUT_MS);
        req.setBody(body);

        try {
            Http http = new Http();
            HttpResponse res = http.send(req);
            out.statusCode = res.getStatusCode();
            out.responseBody = truncate(res.getBody(), 32768);
            out.succeeded = out.statusCode >= 200 && out.statusCode < 300;
            if (!out.succeeded) {
                out.transientFailure = isTransientStatus(out.statusCode);
                out.errorMessage = 'On-call tool returned HTTP ' + out.statusCode
                    + ' ' + res.getStatus()
                    + (out.statusCode == 401 || out.statusCode == 403
                        ? '. Confirm the running user holds Tier2_Webhook_Admin and that the'
                            + ' API key is set on the OnCallToolNamedPrincipal principal.'
                        : '');
            }
        } catch (CalloutException e) {
            // Recorded, never swallowed: statusCode 0 is this class's marker for an
            // attempt that never reached a response, which classifies as transient.
            System.debug(LoggingLevel.ERROR, 'Tier2WebhookQueueable callout failed for '
                + c.Id + ': ' + e.getMessage());
            out.statusCode = 0;
            out.transientFailure = true;
            out.errorMessage = 'CalloutException: ' + e.getMessage();
        } catch (Exception e) {
            System.debug(LoggingLevel.ERROR, 'Tier2WebhookQueueable unexpected failure for '
                + c.Id + ': ' + e.getMessage());
            out.statusCode = 0;
            out.transientFailure = true;
            out.errorMessage = e.getTypeName() + ': ' + e.getMessage();
        }
        return out;
    }

    @TestVisible
    private static String truncate(String value, Integer maxLength) {
        if (value == null) {
            return null;
        }
        return value.length() <= maxLength ? value : value.left(maxLength);
    }

    // ── The job itself ───────────────────────────────────────────────────────────

    public void execute(QueueableContext ctx) {
        // First statement, before anything that can throw, so failure handling is
        // guaranteed even when the platform terminates this transaction.
        System.attachFinalizer(
            new Tier2WebhookFinalizer(escalatedAtByCaseId, failureRowIdByCaseId, attempt, isResend)
        );

        List<Id> ordered = new List<Id>(escalatedAtByCaseId.keySet());
        ordered.sort();

        Map<Id, Datetime> slice = new Map<Id, Datetime>();
        Map<Id, Datetime> remaining = new Map<Id, Datetime>();
        for (Integer i = 0; i < ordered.size(); i++) {
            Id caseId = ordered[i];
            if (i < MAX_CASES_PER_JOB) {
                slice.put(caseId, escalatedAtByCaseId.get(caseId));
            } else {
                remaining.put(caseId, escalatedAtByCaseId.get(caseId));
            }
        }

        Map<Id, Case> caseById = new Map<Id, Case>([
            SELECT Id, CaseNumber, Subject, Priority, Status, Tier2_Notified_At__c
            FROM Case
            WHERE Id IN :slice.keySet()
            WITH USER_MODE
        ]);

        // ── Phase 1: every callout, and no DML of any kind ───────────────────────
        List<Attempt> attempts = new List<Attempt>();
        Boolean anyTransient = false;
        for (Id caseId : slice.keySet()) {
            Case c = caseById.get(caseId);
            if (c == null) {
                // Deleted, or invisible to this user, between enqueue and run.
                System.debug(LoggingLevel.WARN, 'Tier2WebhookQueueable: Case ' + caseId
                    + ' is no longer readable; skipped.');
                continue;
            }
            if (!isResend && isWithinSuppressionWindow(c)) {
                continue;
            }
            Attempt a = attemptOne(c, slice.get(caseId));
            attempts.add(a);
            if (a.transientFailure) {
                anyTransient = true;
            }
        }

        // ── Phase 2: the retry decision, still before any DML ────────────────────
        // Throwing here hands the whole batch to the Finalizer, which runs in its own
        // transaction and is the only place a retry is decided. Nothing above this
        // line has written a record, so there is no half-persisted attempt to undo.
        if (anyTransient && attempt < MAX_ATTEMPTS) {
            throw new Tier2WebhookException(
                'Transient failure on attempt ' + attempt + ' of ' + MAX_ATTEMPTS
                    + ' for ' + attempts.size() + ' Case(s); Tier2WebhookFinalizer will retry.'
            );
        }

        // ── Phase 3: DML ─────────────────────────────────────────────────────────
        persistOutcomes(attempts, caseById);

        // ── Phase 4: the tail, if this transaction's escalation exceeded one job ──
        chainRemainder(remaining);
    }

    /**
     * Stamp the successes and record the failures.
     *
     * Reached only when nothing is going to be retried: either every attempt
     * succeeded or failed permanently, or the attempt budget is spent.
     */
    private void persistOutcomes(List<Attempt> attempts, Map<Id, Case> caseById) {
        if (attempts.isEmpty()) {
            return;
        }

        Datetime now = System.now();
        List<Case> toStamp = new List<Case>();
        List<Integration_Failure__c> toInsert = new List<Integration_Failure__c>();
        List<Integration_Failure__c> toUpdate = new List<Integration_Failure__c>();

        for (Attempt a : attempts) {
            Id existingRowId = failureRowIdByCaseId.get(a.caseId);

            if (a.succeeded) {
                toStamp.add(new Case(Id = a.caseId, Tier2_Notified_At__c = now));
                if (existingRowId != null) {
                    toUpdate.add(new Integration_Failure__c(
                        Id = existingRowId,
                        Status__c = isResend ? STATUS_RESENT : STATUS_RESOLVED,
                        Resend__c = false,
                        Attempt_Count__c = attempt,
                        Last_Attempted_At__c = now,
                        HTTP_Status__c = a.statusCode,
                        Response_Body__c = a.responseBody
                    ));
                }
                continue;
            }

            // Failed, and nothing above will retry it: a permanent status, or a
            // transient one with the attempt budget spent.
            String finalStatus = a.transientFailure ? STATUS_ABANDONED : STATUS_NEW;
            if (existingRowId == null) {
                Case c = caseById.get(a.caseId);
                toInsert.add(new Integration_Failure__c(
                    Case__c = a.caseId,
                    Case_Number__c = c == null ? null : c.CaseNumber,
                    Status__c = finalStatus,
                    Severity__c = SEVERITY_ERROR,
                    Attempt_Count__c = attempt,
                    Last_Attempted_At__c = now,
                    Endpoint__c = 'callout:' + NAMED_CREDENTIAL,
                    HTTP_Status__c = a.statusCode == 0 ? null : a.statusCode,
                    Error_Message__c = a.errorMessage,
                    Request_Payload__c = a.requestPayload,
                    Response_Body__c = a.responseBody
                ));
            } else {
                toUpdate.add(new Integration_Failure__c(
                    Id = existingRowId,
                    Status__c = finalStatus,
                    Severity__c = SEVERITY_ERROR,
                    Resend__c = false,
                    Attempt_Count__c = attempt,
                    Last_Attempted_At__c = now,
                    Endpoint__c = 'callout:' + NAMED_CREDENTIAL,
                    HTTP_Status__c = a.statusCode == 0 ? null : a.statusCode,
                    Error_Message__c = a.errorMessage,
                    Request_Payload__c = a.requestPayload,
                    Response_Body__c = a.responseBody
                ));
            }
        }

        if (!toStamp.isEmpty()) {
            update toStamp;
        }
        if (!toInsert.isEmpty()) {
            insert toInsert;
        }
        if (!toUpdate.isEmpty()) {
            update toUpdate;
        }
    }

    /**
     * Chain the Cases this job did not have callout budget for.
     *
     * Guarded by Test.isRunningTest(): only one job may be added to the queue from a
     * test context, so a chain enqueued during Test.stopTest() raises a LimitException
     * rather than running. The tail is therefore not exercised by this step's tests —
     * recorded in deploy-order.md section 5 item 3.
     */
    private void chainRemainder(Map<Id, Datetime> remaining) {
        if (remaining.isEmpty() || Test.isRunningTest()) {
            return;
        }
        AsyncOptions opts = new AsyncOptions();
        opts.MaximumQueueableStackDepth = MAX_CHAIN_DEPTH;
        System.enqueueJob(
            new Tier2WebhookQueueable(remaining, failureRowIdByCaseId, attempt, isResend),
            opts
        );
    }
}
