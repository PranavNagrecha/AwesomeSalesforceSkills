/**
 * Tier2EscalationServiceTest — detection, suppression and the one-job-per-transaction
 * contract, driven through a real Case save rather than by calling the service.
 *
 * Test.startTest() precedes Test.setMock() in every method here. The @TestSetup DML
 * leaves work pending in the transaction, and startTest opens the new governor
 * context the mock and the enqueue belong in
 * (skills/apex/test-class-standards/references/code-examples.md).
 *
 * The queue is created by DeveloperName, never seeded as an Id literal. Group is a
 * setup object, so it is inserted inside System.runAs to keep it out of the same DML
 * batch as Case.
 *
 * Every assertion in this class runs inside System.runAs(agent()) — this class's own
 * production code (Tier2WebhookQueueable, CaseTriggerHandler) enforces the running
 * user's FLS with WITH USER_MODE, and Case.Tier2_Notified_At__c plus the
 * Tier2_Webhook_Admin permission set that grants it ship in this same deployment.
 * A test that never leaves the deploying user's context fails at validation with
 * "No such column 'Tier2_Notified_At__c' on entity 'Case'" — see
 * skills/apex/test-class-standards/references/gotchas.md Gotcha 13 and
 * references/examples.md Example 5, the shape this fix follows.
 */
@IsTest
private class Tier2EscalationServiceTest {

    private static final Integer BULK_SIZE = 200;
    private static final String QUEUE_DEVELOPER_NAME = 'Tier_2_Engineering';
    private static final String OK_BODY = '{"accepted":true,"incidentId":"INC-1001"}';

    /** Permission set this deployment ships (M1-S02) — grants the FLS this class's
     *  WITH USER_MODE queries and writes need. */
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
            // fenced together here, ahead of the Case insert below, so this transaction
            // never mixes setup-object DML with non-setup DML
            // (skills/apex/mixed-dml-and-setup-objects). TestUserFactory.createUser
            // inserts the User and the matching PermissionSetAssignment rows; see
            // templates/apex/tests/TestUserFactory.cls.
            agent = TestUserFactory.createUser(PROFILE, new List<String>{ PERM_SET });
        }

        // Business data is seeded as the permissioned user, so a create-FLS gap in
        // Tier2_Webhook_Admin fails here — loudly, in setup — rather than surfacing
        // later as an unexplained empty query result.
        System.runAs(agent) {
            insert TestDataFactory.createCases(BULK_SIZE, null, null);
        }
    }

    /** Re-queried per method: @TestSetup state reaches a test method only through the database. */
    private static User agent() {
        return [SELECT Id FROM User WHERE Alias LIKE 'tu%' ORDER BY CreatedDate DESC LIMIT 1];
    }

    private static List<Case> cases(Integer howMany) {
        return [
            SELECT Id, OwnerId, Subject, Tier2_Notified_At__c
            FROM Case
            ORDER BY CaseNumber
            LIMIT :howMany
        ];
    }

    /** Resolved by DeveloperName so no test in this file ever holds a queue Id literal. */
    private static Id tier2QueueId() {
        return [
            SELECT Id
            FROM Group
            WHERE Type = 'Queue' AND DeveloperName = :QUEUE_DEVELOPER_NAME
            LIMIT 1
        ].Id;
    }

    @IsTest
    static void ownerChangeToTier2QueueEscalatesAndStamps() {
        User testUser = agent();

        // The real permissioned block: inside it the user's object- and field-level
        // permissions are enforced regardless of this class's sharing mode (apexdev
        // L41331-L41333), which is the only reason CaseTriggerHandler's and
        // Tier2WebhookQueueable's WITH USER_MODE paths can see the new fields at all.
        System.runAs(testUser) {
            List<Case> toEscalate = cases(2);
            Id queueId = tier2QueueId();
            for (Case c : toEscalate) {
                c.OwnerId = queueId;
            }

            Test.startTest();
            Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator()
                .withResponse(200, OK_BODY));
            update toEscalate;
            Assert.areEqual(
                1,
                Limits.getQueueableJobs(),
                'Two escalated Cases in one save must produce exactly one Queueable, not one per Case'
            );
            Test.stopTest();

            Set<Id> escalatedIds = new Map<Id, Case>(toEscalate).keySet();
            List<Case> stamped = [
                SELECT Id, Tier2_Notified_At__c
                FROM Case
                WHERE Id IN :escalatedIds AND Tier2_Notified_At__c != NULL
            ];
            Assert.areEqual(2, stamped.size(), 'A 2xx webhook response must stamp Tier2_Notified_At__c');
            Assert.areEqual(
                0,
                [SELECT COUNT() FROM Integration_Failure__c],
                'A successful escalation writes no failure row'
            );
        }
    }

    @IsTest
    static void bulkOwnerChangeStillEnqueuesExactlyOneJob() {
        User testUser = agent();

        System.runAs(testUser) {
            List<Case> toEscalate = cases(BULK_SIZE);
            Assert.areEqual(BULK_SIZE, toEscalate.size(), 'Setup must seed a full bulk batch');
            Id queueId = tier2QueueId();
            for (Case c : toEscalate) {
                c.OwnerId = queueId;
            }

            Test.startTest();
            Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator()
                .withResponse(200, OK_BODY));
            update toEscalate;
            Assert.areEqual(
                1,
                Limits.getQueueableJobs(),
                BULK_SIZE + ' escalated Cases in one save must still produce exactly one Queueable'
            );
            Test.stopTest();

            // The job covers MAX_CASES_PER_JOB Cases and chains the tail. Only one job is
            // allowed from a test context, so the chained tail does not run here — this
            // asserts the bound, which is the part a bulk save can get wrong.
            Integer stamped = [SELECT COUNT() FROM Case WHERE Tier2_Notified_At__c != NULL];
            Assert.areEqual(
                Tier2WebhookQueueable.MAX_CASES_PER_JOB,
                stamped,
                'One job must call out for at most MAX_CASES_PER_JOB Cases, keeping the '
                    + 'transaction inside the 100-callout ceiling'
            );
        }
    }

    @IsTest
    static void ownerChangeToAUserIsNotAnEscalation() {
        User testUser = agent();

        System.runAs(testUser) {
            List<Case> toReassign = cases(2);
            for (Case c : toReassign) {
                c.OwnerId = UserInfo.getUserId();
            }

            Test.startTest();
            update toReassign;
            Assert.areEqual(
                0,
                Limits.getQueueableJobs(),
                'Reassigning a Case to a user is not an escalation to the Tier 2 queue'
            );
            Test.stopTest();
        }
    }

    @IsTest
    static void aSaveThatDoesNotChangeOwnerIsIgnored() {
        User testUser = agent();

        System.runAs(testUser) {
            List<Case> toTouch = cases(2);
            for (Case c : toTouch) {
                c.Subject = 'Edited subject, same owner';
            }

            Test.startTest();
            update toTouch;
            Assert.areEqual(
                0,
                Limits.getQueueableJobs(),
                'A save that leaves OwnerId alone must not query for queues or enqueue anything'
            );
            Test.stopTest();
        }
    }

    @IsTest
    static void aRecentlyNotifiedCaseIsSuppressed() {
        User testUser = agent();

        System.runAs(testUser) {
            List<Case> toEscalate = cases(1);
            Id queueId = tier2QueueId();
            toEscalate[0].Tier2_Notified_At__c = System.now().addMinutes(-2);
            toEscalate[0].OwnerId = queueId;

            Test.startTest();
            update toEscalate;
            Assert.areEqual(
                0,
                Limits.getQueueableJobs(),
                'A Case notified two minutes ago is inside the ten-minute window and must be skipped'
            );
            Test.stopTest();
        }
    }

    @IsTest
    static void aNotificationOlderThanTheWindowIsNotSuppressed() {
        User testUser = agent();

        System.runAs(testUser) {
            List<Case> toEscalate = cases(1);
            Id queueId = tier2QueueId();
            toEscalate[0].Tier2_Notified_At__c = System.now().addMinutes(-30);
            toEscalate[0].OwnerId = queueId;

            Test.startTest();
            Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator()
                .withResponse(200, OK_BODY));
            update toEscalate;
            Assert.areEqual(
                1,
                Limits.getQueueableJobs(),
                'A notification thirty minutes old is outside the window and must escalate again'
            );
            Test.stopTest();
        }
    }

    // ── Direct calls to Tier2EscalationService.escalate(), not through a Case save ──
    //
    // reports/mock-deploy/2026-09-12T17-17-07Z/result.json's per-class table names 19 of
    // 41 lines uncovered in Tier2EscalationService (S2-F-16, mock-deploy run 11:
    // "Test coverage of selected Apex Class is 53.659%"). Both of the two branches below
    // are unreachable through CaseTriggerHandler, the path every method above uses:
    // the empty/null-list guard is never hit because the handler only calls escalate()
    // with at least one Case in the batch it already filtered, and CaseNumber is a
    // system-assigned field no Case save can ever leave null, so the two methods below
    // call the service directly instead — the class's own escalate(List<Case>) is
    // public static for exactly this reason.

    @IsTest
    static void escalateWithNoCasesReturnsImmediately() {
        System.runAs(agent()) {
            Integer jobsBefore = Limits.getQueueableJobs();
            Integer failuresBefore = [SELECT COUNT() FROM Integration_Failure__c];

            Tier2EscalationService.escalate(null);
            Tier2EscalationService.escalate(new List<Case>());

            Assert.areEqual(
                jobsBefore,
                Limits.getQueueableJobs(),
                'A null or empty list must return before any EventBus.publish or enqueue'
            );
            Assert.areEqual(
                failuresBefore,
                [SELECT COUNT() FROM Integration_Failure__c],
                'and before any DML'
            );
        }
    }

    @IsTest
    static void escalateWithAMissingCaseNumberWritesAPublishFailureRowAndStillEnqueuesTheJob() {
        System.runAs(agent()) {
            Id caseId = [SELECT Id FROM Case ORDER BY CaseNumber LIMIT 1].Id;

            // Tier2_Escalation__e.Case_Number__c is required=true (M1-S01). escalate()
            // maps it straight from Case.CaseNumber with no null guard
            // (Tier2EscalationService.cls line 61), so an in-memory Case with no
            // CaseNumber makes EventBus.publish() reject that event deterministically —
            // a required-field rejection, not an FLS one, so unlike mock-deploy run 8's
            // S2-F-13 (missing Tier2_Escalation__e Create) this needs no second
            // permission set to reach. escalate() reads only the fields set here; it
            // never re-queries the Case, so the real row's own CaseNumber is irrelevant.
            Case c = new Case(Id = caseId, Subject = 'Missing case number', Priority = 'High');

            Test.startTest();
            Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator()
                .withResponse(200, OK_BODY));
            Tier2EscalationService.escalate(new List<Case>{ c });
            Assert.areEqual(
                1,
                Limits.getQueueableJobs(),
                'The webhook job is enqueued before the failure-row DML regardless of '
                    + 'whether the publish succeeded (Q11) — a lost event is the '
                    + 'tolerable half, not the webhook'
            );
            Test.stopTest();

            List<Integration_Failure__c> rows = [
                SELECT Case__c, Status__c, Severity__c, Attempt_Count__c, Endpoint__c,
                       Error_Message__c
                FROM Integration_Failure__c
            ];
            Assert.areEqual(1, rows.size(), 'A rejected publish writes exactly one failure row');
            Integration_Failure__c row = rows[0];
            Assert.areEqual(caseId, row.Case__c, 'The row points at the Case it belongs to');
            Assert.areEqual(
                Tier2EscalationService.STATUS_NEW,
                row.Status__c,
                'A publish-rejection row is New, the same status a fresh webhook failure gets'
            );
            Assert.areEqual(
                Tier2EscalationService.SEVERITY_ERROR,
                row.Severity__c,
                'A publish rejection is Severity Error'
            );
            Assert.areEqual(
                1,
                row.Attempt_Count__c.intValue(),
                'The first (and only) publish attempt'
            );
            Assert.isNull(
                row.Endpoint__c,
                'Endpoint__c stays blank — no callout was attempted — which is how an '
                    + 'admin tells a publish failure from a webhook failure'
            );
            Assert.isTrue(
                row.Error_Message__c.startsWith('Tier2_Escalation__e publish rejected: '),
                'errorText() must be reached and its output folded into the message, got: '
                    + row.Error_Message__c
            );
        }
    }
}
