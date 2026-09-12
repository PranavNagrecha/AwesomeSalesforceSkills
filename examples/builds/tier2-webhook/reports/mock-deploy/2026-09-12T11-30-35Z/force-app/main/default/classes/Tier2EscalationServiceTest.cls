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
 */
@IsTest
private class Tier2EscalationServiceTest {

    private static final Integer BULK_SIZE = 200;
    private static final String QUEUE_DEVELOPER_NAME = 'Tier_2_Engineering';
    private static final String OK_BODY = '{"accepted":true,"incidentId":"INC-1001"}';

    @TestSetup
    static void seed() {
        User thisUser = new User(Id = UserInfo.getUserId());
        System.runAs(thisUser) {
            Group queue = new Group(
                Name = 'Tier 2 Engineering',
                DeveloperName = QUEUE_DEVELOPER_NAME,
                Type = 'Queue'
            );
            insert queue;
            insert new QueueSObject(QueueId = queue.Id, SObjectType = 'Case');
        }
        insert TestDataFactory.createCases(BULK_SIZE, null, null);
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

    private static List<Case> cases(Integer howMany) {
        return [
            SELECT Id, OwnerId, Subject, Tier2_Notified_At__c
            FROM Case
            ORDER BY CaseNumber
            LIMIT :howMany
        ];
    }

    @IsTest
    static void ownerChangeToTier2QueueEscalatesAndStamps() {
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

    @IsTest
    static void bulkOwnerChangeStillEnqueuesExactlyOneJob() {
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

    @IsTest
    static void ownerChangeToAUserIsNotAnEscalation() {
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

    @IsTest
    static void aSaveThatDoesNotChangeOwnerIsIgnored() {
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

    @IsTest
    static void aRecentlyNotifiedCaseIsSuppressed() {
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

    @IsTest
    static void aNotificationOlderThanTheWindowIsNotSuppressed() {
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
