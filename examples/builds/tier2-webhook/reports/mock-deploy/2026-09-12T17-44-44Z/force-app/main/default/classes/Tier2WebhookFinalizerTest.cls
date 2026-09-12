/**
 * Tier2WebhookFinalizerTest — unit tests of Tier2WebhookFinalizer.execute(FinalizerContext)
 * in isolation from Tier2WebhookQueueable, closing the gap
 * deploy-order.md § 5 item 3 named "deliberately uncovered" and mock-deploy run 9's
 * S2-F-14 (Tier2WebhookFinalizer 63 of 76 lines uncovered).
 *
 * WHY THIS CLASS EXISTS RATHER THAN DRIVING THE REAL QUEUEABLE TO FAILURE:
 * deploy-order.md § 5 item 3 already records, from this same build, that "an unhandled
 * exception in a job run by Test.stopTest() fails the test method" — the transient-retry
 * branch requires Tier2WebhookQueueable.execute() to throw for real, and letting that
 * happen inside Test.startTest()/Test.stopTest() was the reason the branch stayed
 * uncovered in the first place. skills/apex/apex-transaction-finalizers/references/
 * code-examples.md documents the identical finding for its own worked Finalizer test
 * ("Letting the Queueable actually throw inside startTest/stopTest fails the test method
 * itself") and its answer is to extract a @TestVisible decision seam (`handle(...)`) that
 * a test calls directly. Tier2WebhookFinalizer.cls ships with no such seam and this repair
 * is scoped to leave shipped classes unchanged (no seam can be added here), so this class
 * takes the other documented option: implement System.FinalizerContext directly and call
 * Tier2WebhookFinalizer.execute(ctx) as a plain synchronous method call — no
 * System.enqueueJob of the parent job, no Test.startTest()/Test.stopTest(), so the real
 * platform machinery that fails a test on an uncaught async exception is never invoked.
 *
 * UNVERIFIED (2026-09-12): no skill in this repo's corpus confirms or denies that a
 * customer-authored class may implement System.FinalizerContext — it is not the technique
 * skills/apex/apex-transaction-finalizers uses in its own worked example. FinalizerContext
 * is documented as a plain four-method interface (getAsyncApexJobId, getRequestId,
 * getResult, getException — no getJobId; skills/apex/apex-queueable-patterns/SKILL.md
 * lines 124-133) with no stated restriction on implementation, by the same shape as
 * QueueableContext and BatchableContext, which customer code does not implement but is
 * not documented as forbidden to. Confirm this compiles and behaves as expected against a
 * scratch org before trusting the coverage number this class contributes in production —
 * see deploy-order.md § 0d for the full reasoning and the fallback if it does not compile.
 *
 * None of the enqueueJob calls inside execute() are wrapped in Test.startTest()/
 * Test.stopTest() here, deliberately: forcing the re-enqueued Tier2WebhookQueueable
 * (attempt + 1) to actually run via Test.stopTest() would attempt a real HTTP callout with
 * no Test.setMock() registered in these methods, and per the same § 5 item 3 finding that
 * failure would fail the test. Limits.getQueueableJobs() after a bare (unwrapped)
 * System.enqueueJob() call still reports the call was made — that counter is a per-
 * transaction call count, not something Test.startTest()/Test.stopTest() gates — so the
 * "at most one async job" assertion below (skills/apex/apex-transaction-finalizers/
 * SKILL.md "One async job per Finalizer") is still meaningful without ever letting that
 * job run.
 *
 * Every assertion runs inside System.runAs(agent()): Tier2WebhookFinalizer.recordAttempt
 * queries Case WITH USER_MODE and writes Integration_Failure__c with plain insert/update,
 * which is user-mode DML by default at API 67.0+ — the same reason
 * Tier2WebhookQueueableTest wraps every method the same way (Gotcha 13, Gotcha 14).
 */
@IsTest
private class Tier2WebhookFinalizerTest {

    private static final String QUEUE_DEVELOPER_NAME = 'Tier_2_Engineering';

    /** Permission set this deployment ships (M1-S02) — grants the FLS this class's
     *  WITH USER_MODE query and user-mode writes need. */
    private static final String PERM_SET = 'Tier2_Webhook_Admin';
    private static final String PROFILE = 'Standard User';

    @TestSetup
    static void seed() {
        User thisUser = new User(Id = UserInfo.getUserId());
        User agent;
        System.runAs(thisUser) {
            Group queue = new Group(
                Name = 'Tier 2 Engineering',
                DeveloperName = QUEUE_DEVELOPER_NAME,
                Type = 'Queue'
            );
            insert queue;
            insert new QueueSObject(QueueId = queue.Id, SObjectType = 'Case');

            // Setup-object DML (Group, QueueSObject, User, PermissionSetAssignment) is
            // fenced together here, ahead of the Case insert below
            // (skills/apex/mixed-dml-and-setup-objects). TestUserFactory.createUser
            // inserts the User and the matching PermissionSetAssignment rows; see
            // templates/apex/tests/TestUserFactory.cls.
            agent = TestUserFactory.createUser(PROFILE, new List<String>{ PERM_SET });
        }

        // Business data is seeded as the permissioned user, so a create-FLS gap in
        // Tier2_Webhook_Admin fails here — loudly, in setup (Gotcha 14).
        System.runAs(agent) {
            insert TestDataFactory.createCases(1, null, null);
        }
    }

    /** Re-queried per method: @TestSetup state reaches a test method only through the database. */
    private static User agent() {
        return [SELECT Id FROM User WHERE Alias LIKE 'tu%' ORDER BY CreatedDate DESC LIMIT 1];
    }

    private static Id oneCaseId() {
        return [SELECT Id FROM Case LIMIT 1].Id;
    }

    private static List<Integration_Failure__c> failureRows() {
        return [
            SELECT Id, Case__c, Case_Number__c, Status__c, Severity__c, Attempt_Count__c,
                   Endpoint__c, HTTP_Status__c, Error_Message__c, Request_Payload__c,
                   Response_Body__c, Resend__c
            FROM Integration_Failure__c
        ];
    }

    /**
     * Hand-built System.FinalizerContext. The platform never constructs one for a test;
     * it is stood up here purely so Tier2WebhookFinalizer.execute(ctx) can be called as a
     * plain synchronous method, per the class header's UNVERIFIED note.
     */
    private class StubFinalizerContext implements System.FinalizerContext {
        private final Id asyncJobId;
        private final String requestId;
        private final System.ParentJobResult result;
        private final Exception cause;

        StubFinalizerContext(
            Id asyncJobId,
            String requestId,
            System.ParentJobResult result,
            Exception cause
        ) {
            this.asyncJobId = asyncJobId;
            this.requestId = requestId;
            this.result = result;
            this.cause = cause;
        }

        public Id getAsyncApexJobId() { return asyncJobId; }
        public String getRequestId() { return requestId; }
        public System.ParentJobResult getResult() { return result; }
        public Exception getException() { return cause; }
    }

    @IsTest
    static void nullContextIsANoOp() {
        System.runAs(agent()) {
            Map<Id, Datetime> batch = new Map<Id, Datetime>{
                oneCaseId() => Datetime.newInstance(2026, 9, 12, 9, 0, 0)
            };
            Tier2WebhookFinalizer finalizer =
                new Tier2WebhookFinalizer(batch, new Map<Id, Id>(), 1, false);

            finalizer.execute(null);

            Assert.areEqual(
                0,
                failureRows().size(),
                'A null FinalizerContext must be a no-op — the platform never passes one, '
                    + 'but the guard is defensive, first-statement code and is asserted here '
                    + 'rather than left as an unnamed uncovered line'
            );
        }
    }

    @IsTest
    static void successResultTakesNoActionAndDoesNotConsumeTheEnqueueSlot() {
        System.runAs(agent()) {
            Map<Id, Datetime> batch = new Map<Id, Datetime>{
                oneCaseId() => Datetime.newInstance(2026, 9, 12, 9, 0, 0)
            };
            Tier2WebhookFinalizer finalizer =
                new Tier2WebhookFinalizer(batch, new Map<Id, Id>(), 1, false);
            Integer queuedBefore = Limits.getQueueableJobs();

            finalizer.execute(new StubFinalizerContext(
                null, 'REQ-TEST-SUCCESS', System.ParentJobResult.SUCCESS, null
            ));

            Assert.areEqual(
                0,
                failureRows().size(),
                'SUCCESS means the parent already recorded every outcome it decided; the '
                    + 'Finalizer must write no Integration_Failure__c row on top of that'
            );
            Assert.areEqual(
                queuedBefore,
                Limits.getQueueableJobs(),
                'SUCCESS must not consume the one async job a Finalizer may enqueue '
                    + '(skills/apex/apex-transaction-finalizers, "One async job per Finalizer")'
            );
        }
    }

    @IsTest
    static void transientFailureBelowAttemptCeilingIsRecordedRetryingAndReEnqueuedOnce() {
        System.runAs(agent()) {
            Id caseId = oneCaseId();
            Datetime escalatedAt = Datetime.newInstance(2026, 9, 12, 9, 0, 0);
            Map<Id, Datetime> batch = new Map<Id, Datetime>{ caseId => escalatedAt };
            Integer attempt = 1;
            Assert.isTrue(
                attempt < Tier2WebhookFinalizer.MAX_ATTEMPTS,
                'This test exercises the retry branch, which requires attempt below the ceiling'
            );

            Tier2WebhookFinalizer finalizer =
                new Tier2WebhookFinalizer(batch, new Map<Id, Id>(), attempt, false);
            Exception cause = new Tier2WebhookQueueable.Tier2WebhookException(
                'Transient failure on attempt ' + attempt + ' of '
                    + Tier2WebhookFinalizer.MAX_ATTEMPTS + ' for 1 Case(s); '
                    + 'Tier2WebhookFinalizer will retry.'
            );
            Integer queuedBefore = Limits.getQueueableJobs();

            // Deliberately not wrapped in Test.startTest()/Test.stopTest() — see the class
            // header. This call is a plain synchronous method call; the System.enqueueJob
            // inside it registers a job that is never forced to run in this test.
            finalizer.execute(new StubFinalizerContext(
                null, 'REQ-TEST-RETRY', System.ParentJobResult.UNHANDLED_EXCEPTION, cause
            ));

            List<Integration_Failure__c> rows = failureRows();
            Assert.areEqual(
                1,
                rows.size(),
                'The first failed attempt has no existing row, so recordAttempt must insert '
                    + 'exactly one'
            );
            Integration_Failure__c row = rows[0];
            Assert.areEqual(caseId, row.Case__c, 'The row points at the Case it belongs to');
            Assert.areEqual(
                Tier2WebhookFinalizer.STATUS_RETRYING,
                row.Status__c,
                'Below the attempt ceiling the row is Retrying, not Abandoned or New — this '
                    + 'is the value only the Finalizer\'s own retry path writes'
            );
            Assert.areEqual('Error', row.Severity__c, 'A failed webhook is Severity Error');
            Assert.areEqual(
                attempt,
                row.Attempt_Count__c.intValue(),
                'Attempt_Count__c records which attempt just failed'
            );
            Assert.isTrue(
                row.Error_Message__c.contains('Tier2WebhookQueueable.Tier2WebhookException'),
                'The message names the exception type the parent job threw, got: '
                    + row.Error_Message__c
            );
            Assert.isTrue(
                row.Error_Message__c.contains('attempt 1 of 3'),
                'The message carries the attempt budget, got: ' + row.Error_Message__c
            );
            Assert.areEqual(
                Tier2WebhookQueueable.pendingEnvelope(caseId, escalatedAt),
                row.Request_Payload__c,
                'recordAttempt records the pending envelope (no body — the parent rolled '
                    + 'back before building one) so a resend can still replay the '
                    + 'Idempotency-Key'
            );
            Assert.isNull(
                row.HTTP_Status__c,
                'recordAttempt never learns an HTTP status — only Tier2WebhookQueueable.'
                    + 'persistOutcomes does, on the Queueable\'s own success/permanent-'
                    + 'failure path'
            );
            Assert.isNull(
                row.Endpoint__c,
                'recordAttempt never sets Endpoint__c — only persistOutcomes does'
            );

            Case c = [SELECT Id, Tier2_Notified_At__c FROM Case WHERE Id = :caseId];
            Assert.isNull(
                c.Tier2_Notified_At__c,
                'The Finalizer never stamps the Case; only a successful webhook POST does'
            );
            Assert.areEqual(
                queuedBefore + 1,
                Limits.getQueueableJobs(),
                'Below the ceiling the Finalizer must enqueue exactly one retry — the single '
                    + 'async job a Finalizer may use'
            );
        }
    }

    @IsTest
    static void abandonedAfterFinalAttemptIsRecordedAbandonedWithNoReEnqueue() {
        System.runAs(agent()) {
            Id caseId = oneCaseId();
            Datetime escalatedAt = Datetime.newInstance(2026, 9, 12, 9, 0, 0);
            Map<Id, Datetime> batch = new Map<Id, Datetime>{ caseId => escalatedAt };
            Integer attempt = Tier2WebhookFinalizer.MAX_ATTEMPTS;

            Tier2WebhookFinalizer finalizer =
                new Tier2WebhookFinalizer(batch, new Map<Id, Id>(), attempt, false);
            Exception cause = new Tier2WebhookQueueable.Tier2WebhookException(
                'Transient failure on attempt ' + attempt + ' of '
                    + Tier2WebhookFinalizer.MAX_ATTEMPTS + ' for 1 Case(s).'
            );
            Integer queuedBefore = Limits.getQueueableJobs();

            finalizer.execute(new StubFinalizerContext(
                null, 'REQ-TEST-ABANDON', System.ParentJobResult.UNHANDLED_EXCEPTION, cause
            ));

            List<Integration_Failure__c> rows = failureRows();
            Assert.areEqual(1, rows.size(), 'The exhausted attempt writes exactly one row');
            Assert.areEqual(
                Tier2WebhookFinalizer.STATUS_ABANDONED,
                rows[0].Status__c,
                'At the attempt ceiling the row is Abandoned, telling an admin it is theirs '
                    + 'to resend'
            );
            Assert.areEqual(
                attempt,
                rows[0].Attempt_Count__c.intValue(),
                'Attempt_Count__c records which attempt gave up'
            );
            Assert.areEqual(
                queuedBefore,
                Limits.getQueueableJobs(),
                'At the ceiling the Finalizer must not enqueue a retry — this is the branch '
                    + 'that stops the chain rather than extending it'
            );
        }
    }

    @IsTest
    static void secondConsecutiveFailureUpdatesTheExistingRowRatherThanInsertingASecond() {
        System.runAs(agent()) {
            Id caseId = oneCaseId();
            Datetime escalatedAt = Datetime.newInstance(2026, 9, 12, 9, 0, 0);
            Case c = [SELECT Id, CaseNumber FROM Case WHERE Id = :caseId];

            // Simulates the row attempt 1's Finalizer run already left behind, so this run
            // exercises recordAttempt's "existing row" branch instead of its "new row" one.
            Integration_Failure__c existing = new Integration_Failure__c(
                Case__c = caseId,
                Case_Number__c = c.CaseNumber,
                Status__c = Tier2WebhookFinalizer.STATUS_RETRYING,
                Severity__c = 'Error',
                Attempt_Count__c = 1,
                Last_Attempted_At__c = System.now().addMinutes(-5),
                Error_Message__c = 'seed: attempt 1 of 3',
                Request_Payload__c = Tier2WebhookQueueable.pendingEnvelope(caseId, escalatedAt)
            );
            insert existing;

            Integer attempt = 2;
            Map<Id, Datetime> batch = new Map<Id, Datetime>{ caseId => escalatedAt };
            Map<Id, Id> failureRowIdByCaseId = new Map<Id, Id>{ caseId => existing.Id };
            Tier2WebhookFinalizer finalizer =
                new Tier2WebhookFinalizer(batch, failureRowIdByCaseId, attempt, false);
            Exception cause = new Tier2WebhookQueueable.Tier2WebhookException(
                'Transient failure on attempt ' + attempt + ' of '
                    + Tier2WebhookFinalizer.MAX_ATTEMPTS + ' for 1 Case(s).'
            );

            finalizer.execute(new StubFinalizerContext(
                null, 'REQ-TEST-UPDATE', System.ParentJobResult.UNHANDLED_EXCEPTION, cause
            ));

            List<Integration_Failure__c> rows = failureRows();
            Assert.areEqual(
                1,
                rows.size(),
                'A second consecutive failure for the same Case must update the row the '
                    + 'first attempt left, never insert a second one'
            );
            Assert.areEqual(existing.Id, rows[0].Id, 'The same row Id survives the update');
            Assert.areEqual(
                Tier2WebhookFinalizer.STATUS_RETRYING,
                rows[0].Status__c,
                'Still below the ceiling at attempt 2, so still Retrying'
            );
            Assert.areEqual(
                attempt,
                rows[0].Attempt_Count__c.intValue(),
                'Attempt_Count__c advances to the attempt that just failed'
            );
            Assert.isFalse(
                rows[0].Resend__c,
                'recordAttempt\'s update path explicitly clears Resend__c so a completed '
                    + 'resend request does not loop'
            );
            Assert.areEqual(
                Tier2WebhookQueueable.pendingEnvelope(caseId, escalatedAt),
                rows[0].Request_Payload__c,
                'recordAttempt\'s update branch does not touch Request_Payload__c, so the '
                    + 'value from the seeded first-attempt row survives unchanged'
            );
        }
    }
}
