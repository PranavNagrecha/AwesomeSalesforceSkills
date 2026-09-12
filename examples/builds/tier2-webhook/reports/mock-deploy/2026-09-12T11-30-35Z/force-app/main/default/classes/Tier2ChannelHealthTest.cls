/**
 * Tier2ChannelHealthTest
 *
 * Covers the hourly Tier 2 channel-health check: the Schedulable's CronTrigger and
 * its dispatch, both Q24 thresholds in both directions, the quiet-night case the
 * second threshold must NOT fire on, and the two guards that stop the job mailing
 * into the void.
 *
 * Two deliberate shapes, both from skills/apex/apex-scheduled-jobs:
 *  - System.schedule sits inside Test.startTest() / Test.stopTest(). "All asynchronous
 *    calls made after the startTest method are collected by the system. When stopTest
 *    is executed, all asynchronous processes are run synchronously" (apexdev
 *    L16712-L16716). Outside the bracket the job would run only at the end of the
 *    method, too late for any assertion in it.
 *  - The CRON literal is far-future so NextFireTime is deterministic and the job never
 *    fires for real, and every job name is unique because System.schedule rejects a
 *    duplicate name in the same org.
 *
 * The threshold assertions call Tier2ChannelHealthQueueable.evaluate() directly rather
 * than through the queue. That is the point of the split: a Queueable's work runs in a
 * separate transaction after stopTest, where static state and Limits counters from this
 * transaction are not observable, so an assertion made here about work done there would
 * pass vacuously.
 *
 * No PermissionSetAssignment is inserted anywhere below. It is a setup object, and setup
 * DML mixed with the Case and Integration_Failure__c DML in one transaction throws
 * MIXED_DML_OPERATION (skills/apex/apex-system-runas references/gotchas.md). The roster
 * is therefore passed into sendAlert as a parameter, and resolveRecipients is asserted
 * against whatever assignments the org actually holds.
 */
@IsTest
private class Tier2ChannelHealthTest {

    /** Far-future, 7 fields, Day_of_week is the no-specific-value marker. */
    private static final String TEST_CRON = '0 0 0 3 9 ? 2042';

    private static String uniqueJobName(String suffix) {
        return 'Test Tier 2 Channel Health ' + suffix + ' ' +
            String.valueOf(Crypto.getRandomInteger()).right(8);
    }

    /**
     * Baseline: the healthy state. Two delivery failures in the last hour - under the
     * more-than-three threshold - and one Case notified 30 minutes ago, so the channel
     * has demonstrably worked inside the 24 hour window.
     */
    @TestSetup
    static void seed() {
        insert TestDataFactory.createCases(
            1,
            null,
            new Map<String, Object>{ 'Tier2_Notified_At__c' => Datetime.now().addMinutes(-30) }
        );
        insert buildFailures(2);
    }

    /**
     * Integration_Failure__c has no TestDataFactory method: it is this build's own object
     * (M1-S01), not one of the factory's standard five. Status__c is restricted and
     * required, and 'New' is one of the five values M1-S01 declared.
     */
    private static List<Integration_Failure__c> buildFailures(Integer count) {
        List<Integration_Failure__c> failures = new List<Integration_Failure__c>();
        for (Integer i = 0; i < count; i++) {
            failures.add(new Integration_Failure__c(
                Status__c = 'New',
                // Scheme omitted deliberately: a '//' inside an Apex string literal is
                // legal, but a static checker that blanks line comments before string
                // literals mis-lexes the rest of the file from here. Endpoint__c is Text.
                Endpoint__c = 'oncall.example.test/hooks/tier2',
                Error_Message__c = 'Seeded by Tier2ChannelHealthTest row ' + i
            ));
        }
        return failures;
    }

    @IsTest
    static void scheduleCreatesAWaitingCronTriggerAndDispatchesTheQueueable() {
        String jobName = uniqueJobName('dispatch');

        Test.startTest();
        String jobId = System.schedule(
            jobName, TEST_CRON, new Tier2ChannelHealthSchedulable()
        );

        CronTrigger scheduled = [
            SELECT Id, CronExpression, State, TimesTriggered, NextFireTime,
                   CronJobDetail.Name, CronJobDetail.JobType
            FROM CronTrigger
            WHERE Id = :jobId
        ];
        Assert.areEqual(
            TEST_CRON, scheduled.CronExpression, 'CronExpression should round-trip unchanged'
        );
        Assert.areEqual('WAITING', scheduled.State, 'A freshly scheduled job waits to execute');
        Assert.areEqual(0, scheduled.TimesTriggered, 'The job must not have run before stopTest');
        Assert.areEqual(
            '2042-09-03 00:00:00',
            String.valueOf(scheduled.NextFireTime),
            'NextFireTime must match the far-future CRON expression'
        );
        Assert.areEqual(
            jobName, scheduled.CronJobDetail.Name, 'CronJobDetail carries the display name'
        );
        Assert.areEqual('7', scheduled.CronJobDetail.JobType, 'JobType 7 is scheduled Apex');

        // stopTest runs the collected scheduled job synchronously; its execute() enqueues.
        Test.stopTest();

        List<AsyncApexJob> dispatched = [
            SELECT Id, JobType, Status
            FROM AsyncApexJob
            WHERE JobType = 'Queueable' AND ApexClass.Name = 'Tier2ChannelHealthQueueable'
        ];
        Assert.areEqual(
            1,
            dispatched.size(),
            'The Schedulable execute() should enqueue exactly one Tier2ChannelHealthQueueable'
        );
    }

    @IsTest
    static void productionCronIsHourlyOnTheHour() {
        List<String> fields = Tier2ChannelHealthSchedulable.CRON_EXPRESSION.split(' ');
        Assert.areEqual(
            6,
            fields.size(),
            'The documented syntax is Seconds Minutes Hours Day_of_month Month Day_of_week ' +
            'with an optional year; this literal uses the six required fields'
        );
        Assert.areEqual('0', fields[0], 'Seconds must be 0 so the job fires on the hour');
        Assert.areEqual('0', fields[1], 'Minutes must be 0 so the job fires on the hour');
        Assert.areEqual('*', fields[2], 'Hours must be a wildcard for an hourly cadence');
        Assert.areEqual(
            '?',
            fields[5],
            'Day_of_week carries the no-specific-value marker because Day_of_month is a wildcard'
        );
    }

    @IsTest
    static void belowBothThresholdsRaisesNoAlert() {
        Test.startTest();
        Tier2ChannelHealthQueueable.HealthCheckResult result =
            Tier2ChannelHealthQueueable.evaluate();
        Test.stopTest();

        Assert.areEqual(2, result.failuresLastHour, 'The seed created two failures this hour');
        Assert.areEqual(1, result.successesLastDay, 'The seed notified one Case within the window');
        Assert.isFalse(result.failureBurst, 'Two failures is not more than three');
        Assert.isFalse(result.channelSilent, 'A success inside the window means the channel works');
        Assert.isFalse(result.alertRequired, 'Neither rule fired, so no alert is due');
    }

    @IsTest
    static void moreThanThreeFailuresInAnHourRaisesTheBurstAlert() {
        insert buildFailures(2); // seed had two; four is the first count above the threshold

        Test.startTest();
        Tier2ChannelHealthQueueable.HealthCheckResult result =
            Tier2ChannelHealthQueueable.evaluate();
        Test.stopTest();

        Assert.areEqual(4, result.failuresLastHour, 'Four failures landed inside the hour');
        Assert.isTrue(result.failureBurst, 'Four is more than the threshold of three');
        Assert.isFalse(
            result.channelSilent,
            'A Case was notified inside the window, so the silent rule must stay quiet'
        );
        Assert.isTrue(result.alertRequired, 'The burst rule alone is enough to alert');
    }

    @IsTest
    static void noSuccessInTwentyFourHoursWhileEscalationsOccurredRaisesTheSilentAlert() {
        // Push the only success outside the window; the two seeded failures stay inside it.
        Case notified = [SELECT Id, Tier2_Notified_At__c FROM Case LIMIT 1];
        notified.Tier2_Notified_At__c = Datetime.now().addHours(-25);
        update notified;

        Test.startTest();
        Tier2ChannelHealthQueueable.HealthCheckResult result =
            Tier2ChannelHealthQueueable.evaluate();
        Test.stopTest();

        Assert.areEqual(0, result.successesLastDay, 'The only success is now outside the window');
        Assert.areEqual(2, result.failuresLastDay, 'Two escalations still failed inside the window');
        Assert.isFalse(result.failureBurst, 'Two failures is still not more than three');
        Assert.isTrue(
            result.channelSilent,
            'Escalations happened and none succeeded, which is the dead-channel signal'
        );
        Assert.isTrue(result.alertRequired, 'The silent rule alone is enough to alert');
    }

    @IsTest
    static void aQuietWindowWithNoEscalationsRaisesNoAlert() {
        // The distinction Q24 asked for: nothing happened, versus everything failed.
        delete [SELECT Id FROM Integration_Failure__c];
        Case notified = [SELECT Id, Tier2_Notified_At__c FROM Case LIMIT 1];
        notified.Tier2_Notified_At__c = Datetime.now().addHours(-25);
        update notified;

        Test.startTest();
        Tier2ChannelHealthQueueable.HealthCheckResult result =
            Tier2ChannelHealthQueueable.evaluate();
        Test.stopTest();

        Assert.areEqual(0, result.failuresLastDay, 'No escalation failed inside the window');
        Assert.areEqual(0, result.successesLastDay, 'No escalation succeeded inside the window');
        Assert.isFalse(
            result.channelSilent,
            'No successes AND no failures is a quiet night, not a dead channel'
        );
        Assert.isFalse(result.alertRequired, 'A quiet night must not page Support Engineering');
    }

    @IsTest
    static void noActiveRecipientRecordsAWarningFailureRowAndSendsNothing() {
        Integer failuresBefore = [SELECT COUNT() FROM Integration_Failure__c];

        Test.startTest();
        Integer emailsBefore = Limits.getEmailInvocations();
        Tier2ChannelHealthQueueable.sendAlert(
            Tier2ChannelHealthQueueable.evaluate(), new List<String>()
        );
        Integer emailsAfter = Limits.getEmailInvocations();
        Test.stopTest();

        Assert.areEqual(
            emailsBefore,
            emailsAfter,
            'With no active assignee the job must record the gap and send nothing, not mail ' +
            'nowhere. Messaging.sendEmail is short-circuited in a test but still consumes ' +
            'this counter.'
        );

        List<Integration_Failure__c> gapRows = [
            SELECT Id, Severity__c, Status__c, Error_Message__c, Last_Attempted_At__c
            FROM Integration_Failure__c
            WHERE Severity__c = 'Warning'
        ];
        Assert.areEqual(1, gapRows.size(), 'The recipient gap must leave exactly one visible row');
        Assert.areEqual('New', gapRows[0].Status__c, 'The gap row starts in the New state');
        Assert.isTrue(
            gapRows[0].Error_Message__c.contains('Tier2_Webhook_Admin'),
            'The gap row must name the permission set with no active assignee, got: ' +
            gapRows[0].Error_Message__c
        );
        Assert.areEqual(
            failuresBefore + 1,
            [SELECT COUNT() FROM Integration_Failure__c],
            'Exactly one row is written for the gap'
        );
    }

    @IsTest
    static void alertPathDependsOnTheOrgWideAddressPrerequisite() {
        // The org-wide address is a deploy prerequisite this build cannot create
        // (assumption A4) and OrgWideEmailAddress cannot be inserted by a test. Both
        // outcomes are asserted so the test is portable: in an org without the address
        // the guard must suppress the send; in an org that has it the send must happen.
        List<String> roster = new List<String>{ 'support-engineering@example.test' };

        List<OrgWideEmailAddress> senders = [
            SELECT Id FROM OrgWideEmailAddress WHERE Address = 'support-noreply@acme.example' LIMIT 1
        ];

        Test.startTest();
        Integer emailsBefore = Limits.getEmailInvocations();
        Tier2ChannelHealthQueueable.sendAlert(Tier2ChannelHealthQueueable.evaluate(), roster);
        Integer emailsAfter = Limits.getEmailInvocations();
        Test.stopTest();

        if (senders.isEmpty()) {
            Assert.areEqual(
                emailsBefore,
                emailsAfter,
                'Without the org-wide address the job must suppress the send and log the ' +
                'unmet prerequisite rather than falling back to the running user as From'
            );
        } else {
            Assert.areEqual(
                emailsBefore + 1,
                emailsAfter,
                'With the org-wide address present the alert must be sent exactly once'
            );
        }

        Assert.areEqual(
            0,
            [SELECT COUNT() FROM Integration_Failure__c WHERE Severity__c = 'Warning'],
            'A populated roster must not take the recipient-gap path'
        );
    }

    @IsTest
    static void rosterResolutionReturnsTheDistinctActiveAssigneeEmails() {
        // Asserted against whatever assignments the org holds, because the roster is
        // org state rather than test data: inserting a PermissionSetAssignment here
        // would be setup DML beside this class's record DML.
        Set<String> expected = new Set<String>();
        for (PermissionSetAssignment assignment : [
                SELECT Assignee.Email
                FROM PermissionSetAssignment
                WHERE PermissionSet.Name = 'Tier2_Webhook_Admin'
                  AND Assignee.IsActive = true
        ]) {
            if (String.isNotBlank(assignment.Assignee.Email)) {
                expected.add(assignment.Assignee.Email);
            }
        }

        Test.startTest();
        List<String> resolved = Tier2ChannelHealthQueueable.resolveRecipients();
        Test.stopTest();

        Assert.areEqual(
            expected.size(),
            resolved.size(),
            'resolveRecipients must return one entry per distinct active assignee, and must ' +
            'de-duplicate a user who holds the permission set through more than one row'
        );
        Assert.isTrue(
            expected.containsAll(resolved),
            'Every resolved address must belong to an active assignee of the permission set'
        );
        for (String address : resolved) {
            Assert.isTrue(
                String.isNotBlank(address),
                'A blank Email on an assignee must be dropped, not sent to'
            );
        }
    }

    @IsTest
    static void subjectAndBodyNameTheRuleThatFired() {
        Tier2ChannelHealthQueueable.HealthCheckResult burst =
            new Tier2ChannelHealthQueueable.HealthCheckResult();
        burst.failuresLastHour = 9;
        burst.failureBurst = true;
        burst.alertRequired = true;

        String burstSubject = Tier2ChannelHealthQueueable.buildSubject(burst);
        Assert.isTrue(
            burstSubject.contains('9 delivery failures'),
            'The burst subject should carry the observed count, got: ' + burstSubject
        );

        Tier2ChannelHealthQueueable.HealthCheckResult silent =
            new Tier2ChannelHealthQueueable.HealthCheckResult();
        silent.failuresLastDay = 4;
        silent.channelSilent = true;
        silent.alertRequired = true;

        String silentSubject = Tier2ChannelHealthQueueable.buildSubject(silent);
        Assert.isTrue(
            silentSubject.contains('no successful notification'),
            'The silent subject should name the dead-channel rule, got: ' + silentSubject
        );

        String body = Tier2ChannelHealthQueueable.buildBody(silent);
        Assert.isTrue(
            body.contains('escalations occurred: true'),
            'The body should state which rule fired, got: ' + body
        );
        Assert.isFalse(
            body.contains('{!'),
            'A literal merge token would be sent verbatim; the body must be pre-rendered'
        );
    }

    @IsTest
    static void queryBudgetStaysFlatAtBulkVolume() {
        Test.startTest();
        insert buildFailures(200);

        Integer queriesBefore = Limits.getQueries();
        Tier2ChannelHealthQueueable.HealthCheckResult result =
            Tier2ChannelHealthQueueable.evaluate();
        Integer queriesAfter = Limits.getQueries();
        Test.stopTest();

        Assert.areEqual(
            202, result.failuresLastHour, 'Two seeded plus 200 bulk failures land inside the hour'
        );
        Assert.isTrue(result.failureBurst, 'A 202-failure hour is well past the threshold');
        Assert.areEqual(
            3,
            queriesAfter - queriesBefore,
            'evaluate() must cost three aggregate queries whatever the row count - COUNT() ' +
            'returns one value, so the cost does not scale with volume'
        );
    }
}
