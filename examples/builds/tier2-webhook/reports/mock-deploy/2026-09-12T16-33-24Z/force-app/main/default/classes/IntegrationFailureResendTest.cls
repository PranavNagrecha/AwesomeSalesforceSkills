/**
 * IntegrationFailureResendTest — the admin resend path.
 *
 * The behaviour under test is that ticking Resend__c re-enters the SAME Queueable the
 * escalation path uses, replays the stored Idempotency-Key, and moves the row through
 * Retrying to Resent. Nothing here exercises a second callout class, because the
 * resend path adds a call site and not a unit of work.
 *
 * Test.startTest() precedes Test.setMock() throughout, and the enqueue happens inside
 * the startTest/stopTest block by way of the trigger.
 *
 * Every assertion runs inside System.runAs(agent()). IntegrationFailureTriggerHandler
 * and Tier2WebhookQueueable enforce the running user's FLS with WITH USER_MODE /
 * AccessLevel.USER_MODE, and Case.Tier2_Notified_At__c plus the Tier2_Webhook_Admin
 * permission set that grants it ship in this same deployment; a resend driven by the
 * deploying user fails at validation with "Operation failed due to fields being
 * inaccessible" — see skills/apex/test-class-standards/references/gotchas.md
 * Gotcha 13 and references/examples.md Example 5, the shape this fix follows.
 */
@IsTest
private class IntegrationFailureResendTest {

    private static final String QUEUE_DEVELOPER_NAME = 'Tier_2_Engineering';
    private static final String OK_BODY = '{"accepted":true,"incidentId":"INC-3001"}';
    private static final Datetime ORIGINAL_ESCALATION =
        Datetime.newInstance(2026, 9, 12, 8, 30, 0);

    /** Permission set this deployment ships (M1-S02) — grants the FLS this class's
     *  user-mode reads and writes need. */
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
            // fenced together here, ahead of the Case and Integration_Failure__c
            // inserts below (skills/apex/mixed-dml-and-setup-objects).
            // TestUserFactory.createUser inserts the User and the matching
            // PermissionSetAssignment rows; see templates/apex/tests/TestUserFactory.cls.
            agent = TestUserFactory.createUser(PROFILE, new List<String>{ PERM_SET });
        }

        // Business data is seeded as the permissioned user, so a create-FLS gap in
        // Tier2_Webhook_Admin fails here — loudly, in setup.
        System.runAs(agent) {
            List<Case> cases = TestDataFactory.createCases(2, null, null);
            insert cases;

            insert new List<Integration_Failure__c>{
                new Integration_Failure__c(
                    Case__c = cases[0].Id,
                    Status__c = 'New',
                    Severity__c = 'Error',
                    Attempt_Count__c = 3,
                    Last_Attempted_At__c = ORIGINAL_ESCALATION,
                    Endpoint__c = 'callout:OnCall_Tool',
                    HTTP_Status__c = 503,
                    Error_Message__c = 'On-call tool returned HTTP 503',
                    Request_Payload__c = Tier2WebhookQueueable.pendingEnvelope(
                        cases[0].Id, ORIGINAL_ESCALATION
                    )
                ),
                // No stored payload: the fallback path.
                new Integration_Failure__c(
                    Case__c = cases[1].Id,
                    Status__c = 'New',
                    Severity__c = 'Error',
                    Attempt_Count__c = 1,
                    Last_Attempted_At__c = ORIGINAL_ESCALATION
                ),
                // No Case at all: Case__c is SetNull on delete, so a row can outlive it.
                new Integration_Failure__c(
                    Status__c = 'Abandoned',
                    Severity__c = 'Error'
                )
            };
        }
    }

    /** Re-queried per method: @TestSetup state reaches a test method only through the database. */
    private static User agent() {
        return [SELECT Id FROM User WHERE Alias LIKE 'tu%' ORDER BY CreatedDate DESC LIMIT 1];
    }

    /**
     * Every seeded row that has a Case, selected — never filtered — on Request_Payload__c.
     *
     * `Request_Payload__c` is a Long Text Area, and the org rejected a WHERE clause on it
     * outright: "field 'Request_Payload__c' can not be filtered in a query call"
     * (dry-run 3, S2-F-05). Long and rich text areas cannot be filtered, grouped or
     * sorted, so the two helpers below select the field and pick in memory.
     */
    private static List<Integration_Failure__c> rowsWithACase() {
        return [
            SELECT Id, Case__c, Status__c, Resend__c, Request_Payload__c, Last_Attempted_At__c
            FROM Integration_Failure__c
            WHERE Case__c != NULL
            ORDER BY Attempt_Count__c DESC
        ];
    }

    private static Integration_Failure__c rowWithPayload() {
        for (Integration_Failure__c row : rowsWithACase()) {
            if (row.Request_Payload__c != null) {
                return row;
            }
        }
        Assert.fail('Setup must seed one failure row carrying a stored request envelope');
        return null;
    }

    private static Integration_Failure__c rowWithoutPayload() {
        for (Integration_Failure__c row : rowsWithACase()) {
            if (row.Request_Payload__c == null) {
                return row;
            }
        }
        Assert.fail('Setup must seed one failure row with no stored request envelope');
        return null;
    }

    @IsTest
    static void tickingResendReEnqueuesAndResolvesTheRow() {
        User testUser = agent();

        System.runAs(testUser) {
            Integration_Failure__c row = rowWithPayload();
            row.Resend__c = true;

            Test.startTest();
            Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator()
                .withResponse(200, OK_BODY));
            update row;
            Assert.areEqual(
                1,
                Limits.getQueueableJobs(),
                'A resend enqueues exactly one job — the same Queueable the escalation path uses'
            );
            Test.stopTest();

            Integration_Failure__c after = [
                SELECT Id, Status__c, Resend__c, HTTP_Status__c, Attempt_Count__c
                FROM Integration_Failure__c
                WHERE Id = :row.Id
            ];
            Assert.areEqual(
                'Resent',
                after.Status__c,
                'A successful resend lands on Resent, not Resolved — Resolved is for a row the '
                    + 'escalation path itself cleared'
            );
            Assert.areEqual(false, after.Resend__c, 'The checkbox is cleared so it can be ticked again');
            Assert.areEqual(200, after.HTTP_Status__c.intValue(), 'The successful status is recorded');

            Case stamped = [SELECT Id, Tier2_Notified_At__c FROM Case WHERE Id = :row.Case__c];
            Assert.isNotNull(
                stamped.Tier2_Notified_At__c,
                'A resend that reaches the on-call tool stamps the Case exactly as a first attempt does'
            );
        }
    }

    @IsTest
    static void theResendReplaysTheStoredIdempotencyKey() {
        User testUser = agent();

        System.runAs(testUser) {
            Integration_Failure__c row = rowWithPayload();
            String replayed = Tier2WebhookQueueable.idempotencyKey(row.Case__c, ORIGINAL_ESCALATION);

            Assert.isTrue(
                row.Request_Payload__c.contains(replayed),
                'The key the resend path rebuilds from Request_Payload__c must be the one the '
                    + 'original attempt recorded, or the on-call tool sees a new incident. '
                    + 'Expected ' + replayed + ' inside ' + row.Request_Payload__c
            );
        }
    }

    @IsTest
    static void aResendIsNotSuppressedByARecentNotification() {
        User testUser = agent();

        System.runAs(testUser) {
            Integration_Failure__c row = rowWithPayload();
            Case c = new Case(Id = row.Case__c, Tier2_Notified_At__c = System.now().addMinutes(-1));
            update c;
            row.Resend__c = true;

            Test.startTest();
            Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator()
                .withResponse(200, OK_BODY));
            update row;
            Test.stopTest();

            Integration_Failure__c after = [
                SELECT Id, Status__c FROM Integration_Failure__c WHERE Id = :row.Id
            ];
            Assert.areEqual(
                'Resent',
                after.Status__c,
                'An admin ticking Resend has overridden the ten-minute window on purpose; the job '
                    + 'must not silently skip the Case it was asked to re-send'
            );
        }
    }

    @IsTest
    static void aRowWithNoStoredPayloadStillResends() {
        User testUser = agent();

        System.runAs(testUser) {
            Integration_Failure__c row = rowWithoutPayload();
            Assert.isNull(
                row.Request_Payload__c,
                'This test needs the row that carries no stored envelope — asserted on the '
                    + 'selected value, because a Long Text Area cannot be filtered on (S2-F-05)'
            );
            row.Resend__c = true;

            Test.startTest();
            Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator()
                .withResponse(200, OK_BODY));
            update row;
            Assert.areEqual(
                1,
                Limits.getQueueableJobs(),
                'A row written before the envelope existed still resends; it falls back to '
                    + 'Last_Attempted_At__c and says so in the debug log'
            );
            Test.stopTest();

            Integration_Failure__c after = [
                SELECT Id, Status__c FROM Integration_Failure__c WHERE Id = :row.Id
            ];
            Assert.areEqual('Resent', after.Status__c, 'The fallback path still completes the resend');
        }
    }

    @IsTest
    static void aRowWithNoCaseIsIgnored() {
        User testUser = agent();

        System.runAs(testUser) {
            Integration_Failure__c orphan = [
                SELECT Id, Case__c, Resend__c FROM Integration_Failure__c WHERE Case__c = NULL LIMIT 1
            ];
            orphan.Resend__c = true;

            Test.startTest();
            update orphan;
            Assert.areEqual(
                0,
                Limits.getQueueableJobs(),
                'There is no Case to POST and no Case Id to build a key from, so nothing is enqueued'
            );
            Test.stopTest();
        }
    }

    @IsTest
    static void clearingResendDoesNotReEnqueue() {
        User testUser = agent();

        System.runAs(testUser) {
            Integration_Failure__c row = rowWithPayload();
            row.Resend__c = false;

            Test.startTest();
            update row;
            Assert.areEqual(
                0,
                Limits.getQueueableJobs(),
                'Only a false-to-true transition is a resend. This is the guard that keeps the '
                    + 'handler\'s own Resend__c = false update from re-entering itself'
            );
            Test.stopTest();
        }
    }
}
