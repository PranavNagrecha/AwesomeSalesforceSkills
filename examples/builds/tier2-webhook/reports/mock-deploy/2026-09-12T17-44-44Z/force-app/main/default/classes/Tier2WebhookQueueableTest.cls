/**
 * Tier2WebhookQueueableTest — what the job records, per response class.
 *
 * Every assertion here is on a decision the job persisted: the stamp, the failure row,
 * the Status__c value, the recorded HTTP status. None is on how many chain links the
 * test runtime happened to drive, because only one job may be added to the queue from
 * a test context and a retry is a different async transaction.
 *
 * Test.startTest() precedes Test.setMock() in every method — the @TestSetup DML leaves
 * work pending and startTest opens the governor context the enqueue belongs in. The
 * enqueue itself is always between startTest and stopTest, so the job actually runs.
 *
 * Responses are routed with the mock's default response rather than by endpoint,
 * because whether the HttpRequest handed to respond() still carries the literal
 * callout: string is UNVERIFIED (step input `unverified`) and no test here depends on
 * the answer.
 *
 * Every assertion runs inside System.runAs(agent()). Tier2WebhookQueueable enforces
 * the running user's FLS with WITH USER_MODE, and Case.Tier2_Notified_At__c plus the
 * Tier2_Webhook_Admin permission set that grants it ship in this same deployment; a
 * job enqueued and awaited as the deploying user fails at validation with "No such
 * column 'Tier2_Notified_At__c' on entity 'Case'" — see
 * skills/apex/test-class-standards/references/gotchas.md Gotcha 13 and
 * references/examples.md Example 5, the shape this fix follows. The async context
 * user is the user whose transaction enqueued the job (assumption A2), so the
 * enqueue itself must happen inside the runAs block, not only the assertions after it.
 */
@IsTest
private class Tier2WebhookQueueableTest {

    private static final String QUEUE_DEVELOPER_NAME = 'Tier_2_Engineering';
    private static final String OK_BODY = '{"accepted":true,"incidentId":"INC-2001"}';
    private static final String REJECT_BODY = '{"error":"unprocessable payload"}';

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
        // Tier2_Webhook_Admin fails here — loudly, in setup.
        System.runAs(agent) {
            insert TestDataFactory.createCases(3, null, null);
        }
    }

    /** Re-queried per method: @TestSetup state reaches a test method only through the database. */
    private static User agent() {
        return [SELECT Id FROM User WHERE Alias LIKE 'tu%' ORDER BY CreatedDate DESC LIMIT 1];
    }

    private static Map<Id, Datetime> oneCase() {
        Case c = [SELECT Id FROM Case ORDER BY CaseNumber LIMIT 1];
        return new Map<Id, Datetime>{ c.Id => Datetime.newInstance(2026, 9, 12, 9, 0, 0) };
    }

    private static List<Integration_Failure__c> failureRows() {
        return [
            SELECT Id, Case__c, Case_Number__c, Status__c, Severity__c, Attempt_Count__c,
                   Endpoint__c, HTTP_Status__c, Error_Message__c, Request_Payload__c,
                   Response_Body__c
            FROM Integration_Failure__c
        ];
    }

    @IsTest
    static void successStampsTheCaseAndWritesNoFailureRow() {
        User testUser = agent();

        System.runAs(testUser) {
            Map<Id, Datetime> batch = oneCase();

            Test.startTest();
            Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator()
                .withResponse(200, OK_BODY));
            System.enqueueJob(new Tier2WebhookQueueable(batch));
            Test.stopTest();

            Id caseId = new List<Id>(batch.keySet())[0];
            Case stamped = [SELECT Id, Tier2_Notified_At__c FROM Case WHERE Id = :caseId];
            Assert.isNotNull(
                stamped.Tier2_Notified_At__c,
                'A 2xx response must stamp Tier2_Notified_At__c — it is both the suppression '
                    + 'window and the audit trail an admin reads on the Case'
            );
            Assert.areEqual(0, failureRows().size(), 'A success writes no Integration_Failure__c');
        }
    }

    @IsTest
    static void permanentFailureRecordsTheAttemptAndDoesNotStamp() {
        User testUser = agent();

        System.runAs(testUser) {
            Map<Id, Datetime> batch = oneCase();

            Test.startTest();
            Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator()
                .withResponse(422, REJECT_BODY));
            System.enqueueJob(new Tier2WebhookQueueable(batch));
            Test.stopTest();

            Id caseId = new List<Id>(batch.keySet())[0];
            Case notStamped = [SELECT Id, Tier2_Notified_At__c FROM Case WHERE Id = :caseId];
            Assert.isNull(
                notStamped.Tier2_Notified_At__c,
                'A 422 is not a delivery; Tier2_Notified_At__c must stay null'
            );

            List<Integration_Failure__c> rows = failureRows();
            Assert.areEqual(1, rows.size(), 'A permanent failure writes exactly one failure row');
            Integration_Failure__c row = rows[0];
            Assert.areEqual('New', row.Status__c, 'A permanent failure is New — it is not being retried');
            Assert.areEqual('Error', row.Severity__c, 'A failed webhook is Severity Error');
            Assert.areEqual(
                422,
                row.HTTP_Status__c.intValue(),
                'The HTTP status the tool returned is recorded'
            );
            Assert.areEqual(caseId, row.Case__c, 'The row points at the Case it belongs to');
            Assert.areEqual(
                'callout:OnCall_Tool',
                row.Endpoint__c,
                'Endpoint__c records the Named Credential reference actually used, with no path '
                    + 'appended and no hostname'
            );
            Assert.isTrue(
                row.Request_Payload__c.contains('idempotencyKey'),
                'Request_Payload__c must carry the Idempotency-Key so a resend replays it, got: '
                    + row.Request_Payload__c
            );
            Assert.isTrue(
                row.Request_Payload__c.contains('escalatedAtMillis'),
                'Request_Payload__c must carry the escalation time the resend path parses back'
            );
        }
    }

    @IsTest
    static void authFailurePointsTheReaderAtThePrincipalGrant() {
        User testUser = agent();

        System.runAs(testUser) {
            Map<Id, Datetime> batch = oneCase();

            Test.startTest();
            Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator()
                .withResponse(401, ''));
            System.enqueueJob(new Tier2WebhookQueueable(batch));
            Test.stopTest();

            List<Integration_Failure__c> rows = failureRows();
            Assert.areEqual(1, rows.size(), 'A 401 writes one failure row');
            Assert.areEqual(
                401,
                rows[0].HTTP_Status__c.intValue(),
                'The 401 is recorded as the HTTP status'
            );
            Assert.isTrue(
                rows[0].Error_Message__c.contains('Tier2_Webhook_Admin'),
                'A 401 is almost always the missing principal grant (decision D14), so the message '
                    + 'must name the permission set rather than leaving the reader to guess. Got: '
                    + rows[0].Error_Message__c
            );
        }
    }

    @IsTest
    static void transientFailureOnTheLastAttemptIsAbandonedRatherThanRetried() {
        User testUser = agent();

        System.runAs(testUser) {
            Map<Id, Datetime> batch = oneCase();

            Test.startTest();
            Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator()
                .withResponse(503, ''));
            // attempt = MAX_ATTEMPTS: the budget is spent, so this job records the outcome
            // instead of throwing for the Finalizer to retry.
            System.enqueueJob(new Tier2WebhookQueueable(
                batch, new Map<Id, Id>(), Tier2WebhookQueueable.MAX_ATTEMPTS, false
            ));
            Test.stopTest();

            List<Integration_Failure__c> rows = failureRows();
            Assert.areEqual(1, rows.size(), 'The exhausted attempt writes one failure row');
            Assert.areEqual(
                'Abandoned',
                rows[0].Status__c,
                'A transient failure with no attempts left is Abandoned, which is what tells an '
                    + 'admin the row is theirs to resend'
            );
            Assert.areEqual(
                Tier2WebhookQueueable.MAX_ATTEMPTS,
                rows[0].Attempt_Count__c.intValue(),
                'Attempt_Count__c records which attempt gave up'
            );
        }
    }

    @IsTest
    static void aCaseNotifiedInsideTheWindowIsSkippedByTheJobToo() {
        User testUser = agent();

        System.runAs(testUser) {
            Case c = [SELECT Id FROM Case ORDER BY CaseNumber LIMIT 1];
            c.Tier2_Notified_At__c = System.now().addMinutes(-1);
            update c;
            Map<Id, Datetime> batch = new Map<Id, Datetime>{ c.Id => System.now() };

            Test.startTest();
            Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator()
                .withResponse(200, OK_BODY));
            System.enqueueJob(new Tier2WebhookQueueable(batch));
            Test.stopTest();

            Assert.areEqual(
                0,
                failureRows().size(),
                'A suppressed Case is not called out for, so there is nothing to record. The job '
                    + 're-checks the window because the handler cannot see an escalation still in '
                    + 'flight in another transaction'
            );
        }
    }

    @IsTest
    static void statusCodesAreClassifiedTheWayTheRetryContractSays() {
        User testUser = agent();

        System.runAs(testUser) {
            for (Integer code : new List<Integer>{ 429, 502, 503, 504 }) {
                Assert.isTrue(
                    Tier2WebhookQueueable.isTransientStatus(code),
                    code + ' is transient per step input retry_contract and must be retried'
                );
            }
            Assert.isTrue(
                Tier2WebhookQueueable.isTransientStatus(0),
                'Status 0 is this class\'s marker for a connection failure or timeout, which the '
                    + 'retry contract groups with the transient codes'
            );
            for (Integer code : new List<Integer>{ 400, 401, 403, 404, 422 }) {
                Assert.isTrue(
                    Tier2WebhookQueueable.isPermanentStatus(code),
                    code + ' is permanent per step input retry_contract and must not be retried'
                );
                Assert.isTrue(
                    !Tier2WebhookQueueable.isTransientStatus(code),
                    code + ' must not also classify as transient'
                );
            }
        }
    }

    @IsTest
    static void theIdempotencyKeyIsStableForTheSameCaseAndEscalationTime() {
        User testUser = agent();

        System.runAs(testUser) {
            Id caseId = [SELECT Id FROM Case ORDER BY CaseNumber LIMIT 1].Id;
            Datetime escalatedAt = Datetime.newInstance(2026, 9, 12, 9, 0, 0);

            String first = Tier2WebhookQueueable.idempotencyKey(caseId, escalatedAt);
            String second = Tier2WebhookQueueable.idempotencyKey(caseId, escalatedAt);
            String later = Tier2WebhookQueueable.idempotencyKey(caseId, escalatedAt.addMinutes(1));

            Assert.areEqual(
                first,
                second,
                'The same Case and escalation time must rebuild the identical key — that is what '
                    + 'lets a retry and a resend be discarded by the on-call tool'
            );
            Assert.areNotEqual(
                first,
                later,
                'A different escalation time is a different escalation and must not share a key'
            );
        }
    }
}
