/**
 * Tier2ChannelHealthQueueable
 *
 * The worker behind Tier2ChannelHealthSchedulable. Counts what happened on the
 * Tier 2 notification channel in the last hour and the last day, decides whether
 * the channel has gone dark, and emails the Support Engineering roster when it has.
 *
 * The two thresholds are Q24's, verbatim from the step input:
 *   1. more than three Integration_Failure__c rows created in the last hour; OR
 *   2. no Case stamped with Tier2_Notified_At__c in the last 24 hours, while at
 *      least one escalation occurred in that window.
 *
 * How "an escalation occurred" is read, and why it is not a guess: a Tier 2
 * escalation either succeeds - stamping Case.Tier2_Notified_At__c - or fails,
 * creating an Integration_Failure__c row (M1-S01's object model, Q16-Q18). Those are
 * the only two records the build produces per escalation, so "escalations occurred
 * but none succeeded" is exactly successesLastDay == 0 AND failuresLastDay > 0.
 * Without that second count the rule cannot distinguish a dead channel from a quiet
 * night, which is the one distinction Q24 asked for.
 *
 * Logging (2026-09-12 amendment, step input `logging_decision_2026_09_12`):
 * include_logger is FALSE and ApplicationLogger is not referenced. The visible log
 * for this feature is Integration_Failure__c; everything else is System.debug.
 * LoggingLevel.ERROR carries the two failure paths and a failed send;
 * LoggingLevel.INFO and WARN carry the run outcome, because a debug line that is
 * only read when something is wrong should not label a healthy run an error.
 *
 * Security: this class is pinned to apiVersion 67.0 in its -meta.xml, where SOQL
 * runs in USER MODE by default with no keyword at all, so all four queries below
 * enforce the running user's object permissions, field permissions and sharing.
 * The running user is the user who called System.schedule - not the escalating
 * user and not Automated Process (assumption A13, decision D14) - and the
 * Tier2_Webhook_Admin permission set from M1-S02 carries what they need for the
 * failure counts: Integration_Failure__c read with viewAllRecords, and read on
 * Case.Tier2_Notified_At__c. Case RECORD access and PermissionSetAssignment read
 * access are NOT granted by that permission set (assumption A14); see
 * deploy-order.md section 4.
 *
 * Not a Database.AllowsCallouts job: it makes no callout. The webhook delivery
 * path that does is M1-S03's.
 */
public with sharing class Tier2ChannelHealthQueueable implements Queueable {

    /** Debug-log prefix, matching the class name so log lines group by class. */
    private static final String SOURCE = 'Tier2ChannelHealthQueueable';

    /** Q24: alert when failures in the last hour are MORE THAN three. */
    @TestVisible
    private static final Integer FAILURES_PER_HOUR_THRESHOLD = 3;

    /** Q24: the no-success window, in hours. */
    @TestVisible
    private static final Integer SUCCESS_WINDOW_HOURS = 24;

    /**
     * The verified org-wide address the alert is sent FROM (Q24, assumption A4).
     * It has no metadata type and no step in this build can create or verify it;
     * deploy-order.md section 3 records it as a deploy prerequisite. If the row is
     * absent at run time this job logs and sends nothing rather than falling back
     * to the running user as the From address.
     */
    @TestVisible
    private static final String SENDER_ADDRESS = 'support-noreply@acme.example';

    /**
     * The permission set whose active assignees ARE the Support Engineering alert
     * roster (requester answer 2026-09-12, step input `alert_recipients`). M1-S02
     * ships it, and decision D14 assigns it to everyone who can escalate a Case plus
     * the user who schedules this job.
     *
     * A hardcoded PermissionSet.Name in Apex is the shape
     * skills/apex/apex-user-and-permission-checks flags as its Anti-Pattern 3 - but
     * that anti-pattern is about GATING behaviour on an assignment, where a Custom
     * Permission is the proper abstraction. This is roster resolution: "who holds
     * this" is a question FeatureManagement.checkPermission cannot answer, only
     * "can the running user". The name is a constant so a rename is one edit.
     */
    @TestVisible
    private static final String ROSTER_PERMISSION_SET = 'Tier2_Webhook_Admin';

    /** What one run of the health check observed and concluded. */
    public class HealthCheckResult {
        public Integer failuresLastHour = 0;
        public Integer failuresLastDay = 0;
        public Integer successesLastDay = 0;
        /** Q24 rule 1: more than three failures landed in the hour. */
        public Boolean failureBurst = false;
        /** Q24 rule 2: escalations happened in the window and none succeeded. */
        public Boolean channelSilent = false;
        /** Either rule fired. */
        public Boolean alertRequired = false;
    }

    public void execute(QueueableContext context) {
        HealthCheckResult result = evaluate();

        if (!result.alertRequired) {
            System.debug(LoggingLevel.INFO, SOURCE + ': channel healthy. ' + describe(result));
            return;
        }

        System.debug(LoggingLevel.WARN, SOURCE + ': channel health alert raised. ' + describe(result));
        sendAlert(result, resolveRecipients());
    }

    /**
     * Three aggregate queries and the two threshold decisions. Separated from
     * execute() so the decision can be asserted synchronously in a test, without
     * crossing the Test.stopTest asynchronous boundary that resets static state.
     *
     * Aggregate COUNT() is the bulk-safe shape by construction: it returns one
     * value whatever the row count, so this job's SOQL and heap cost is flat at
     * any volume (three queries, three Integers).
     */
    @TestVisible
    private static HealthCheckResult evaluate() {
        Datetime evaluatedAt = Datetime.now();
        Datetime hourWindowStart = evaluatedAt.addHours(-1);
        Datetime dayWindowStart = evaluatedAt.addHours(-SUCCESS_WINDOW_HOURS);

        HealthCheckResult result = new HealthCheckResult();

        // reason: apiVersion 67.0 runs database operations in user mode by default, so
        // no WITH USER_MODE keyword is required for FLS/CRUD/sharing enforcement here
        // (step input "running_user"; agents/_shared/AGENT_CONTRACT.md, Apex security
        // idiom by API version, 67.0+ row). Whether the clause is even legal on an
        // aggregate COUNT() query is stated in no cited skill and is recorded
        // UNVERIFIED in deploy-order.md section 4 rather than guessed either way.
        // WITH SECURITY_ENFORCED does not compile at this version.
        result.failuresLastHour = [
            SELECT COUNT()
            FROM Integration_Failure__c
            WHERE CreatedDate >= :hourWindowStart
        ];

        result.failuresLastDay = [
            SELECT COUNT()
            FROM Integration_Failure__c
            WHERE CreatedDate >= :dayWindowStart
        ];

        result.successesLastDay = [
            SELECT COUNT()
            FROM Case
            WHERE Tier2_Notified_At__c >= :dayWindowStart
        ];

        result.failureBurst = result.failuresLastHour > FAILURES_PER_HOUR_THRESHOLD;
        result.channelSilent = (result.successesLastDay == 0 && result.failuresLastDay > 0);
        result.alertRequired = result.failureBurst || result.channelSilent;

        return result;
    }

    /**
     * The alert roster: the email of every ACTIVE user holding Tier2_Webhook_Admin.
     *
     * Inactive users are excluded in the WHERE clause rather than filtered afterwards,
     * so an all-inactive roster returns empty and takes the recipient-gap path below
     * rather than sending to nobody. Addresses are de-duplicated: one user can hold the
     * same permission set through more than one assignment row.
     *
     * This is a query, not DML: PermissionSetAssignment is a setup object, and only
     * setup-object DML mixed with record DML in one transaction throws
     * MIXED_DML_OPERATION (skills/apex/apex-system-runas references/gotchas.md lists
     * PermissionSetAssignment among the setup objects). Reading it beside the
     * Integration_Failure__c insert below is safe.
     */
    @TestVisible
    private static List<String> resolveRecipients() {
        Set<String> addresses = new Set<String>();
        for (PermissionSetAssignment assignment : [
                SELECT Assignee.Email
                FROM PermissionSetAssignment
                WHERE PermissionSet.Name = :ROSTER_PERMISSION_SET
                  AND Assignee.IsActive = true
        ]) {
            if (String.isNotBlank(assignment.Assignee.Email)) {
                addresses.add(assignment.Assignee.Email);
            }
        }
        return new List<String>(addresses);
    }

    /**
     * Send one alert to the roster from the org-wide address.
     *
     * The roster is passed in rather than resolved here so both the populated and the
     * empty case are testable without inserting a PermissionSetAssignment, which is
     * setup DML and would have to be isolated with System.runAs.
     *
     * allOrNone is false, so nothing is thrown and every outcome arrives in the
     * result list: per skills/apex/apex-outbound-email-patterns, sendEmail(msgs, false)
     * "does not throw at all - inspect each Messaging.SendEmailResult". A try/catch
     * around that call would be dead code.
     */
    @TestVisible
    private static void sendAlert(HealthCheckResult result, List<String> recipients) {
        if (recipients == null || recipients.isEmpty()) {
            recordRecipientGap(result);
            return;
        }

        List<OrgWideEmailAddress> senders = [
            SELECT Id, Address
            FROM OrgWideEmailAddress
            WHERE Address = :SENDER_ADDRESS
            LIMIT 1
        ];

        if (senders.isEmpty()) {
            System.debug(LoggingLevel.ERROR, SOURCE +
                ': channel health alert NOT sent - the org-wide address ' + SENDER_ADDRESS +
                ' is not present in this org. It is a deploy prerequisite (assumption A4) ' +
                'and must be created and verified in Setup before this job can alert. ' +
                describe(result));
            return;
        }

        Messaging.SingleEmailMessage message = new Messaging.SingleEmailMessage();
        message.setOrgWideEmailAddressId(senders[0].Id);
        message.setToAddresses(recipients);
        message.setSubject(buildSubject(result));
        message.setPlainTextBody(buildBody(result));
        // No whatId and no targetObjectId on this message, so an activity record
        // would have nothing to relate to and the save would silently no-op.
        message.setSaveAsActivity(false);

        List<Messaging.SendEmailResult> sendResults =
            Messaging.sendEmail(new List<Messaging.SingleEmailMessage>{ message }, false);

        for (Messaging.SendEmailResult sendResult : sendResults) {
            if (sendResult.isSuccess()) {
                System.debug(LoggingLevel.INFO, SOURCE + ': channel health alert sent to ' +
                    recipients.size() + ' recipient(s). ' + describe(result));
                continue;
            }
            for (Messaging.SendEmailError sendError : sendResult.getErrors()) {
                System.debug(LoggingLevel.ERROR, SOURCE + ': channel health alert send failed [' +
                    String.valueOf(sendError.getStatusCode()) + '] ' + sendError.getMessage());
            }
        }
    }

    /**
     * Nobody holds the roster permission set, so there is no one to alert. Per the
     * 2026-09-12 requester answer, that gap is made visible on the feature's own log
     * object rather than left in a debug log nobody reads.
     *
     * The row is Severity Warning, which is what distinguishes it from a real delivery
     * failure to a human reading the list view. It does NOT distinguish it to this
     * job's own thresholds, which count rows without a Severity filter - see
     * deploy-order.md section 4 item 5.
     */
    @TestVisible
    private static void recordRecipientGap(HealthCheckResult result) {
        String message = SOURCE + ': channel health alert NOT sent - no active user holds the ' +
            ROSTER_PERMISSION_SET + ' permission set, so the alert has no recipient. ' +
            describe(result);
        System.debug(LoggingLevel.ERROR, message);

        Integration_Failure__c gapRecord = new Integration_Failure__c(
            Status__c = 'New',
            Severity__c = 'Warning',
            Last_Attempted_At__c = Datetime.now(),
            Error_Message__c = message
        );

        try {
            insert gapRecord;
        } catch (DmlException e) {
            // Last resort. The debug line above already carries the gap; re-throwing
            // here would only surface the same fact as a failed AsyncApexJob, and
            // would lose the original message behind a DML error.
            System.debug(LoggingLevel.ERROR, SOURCE +
                ': could not record the recipient gap on Integration_Failure__c - ' +
                e.getMessage());
        }
    }

    /** Subject line. Names which of the two rules fired, because the operator response differs. */
    @TestVisible
    private static String buildSubject(HealthCheckResult result) {
        if (result.failureBurst && result.channelSilent) {
            return 'Tier 2 channel alert: failure burst AND no successful notification in ' +
                SUCCESS_WINDOW_HOURS + 'h';
        }
        if (result.failureBurst) {
            return 'Tier 2 channel alert: ' + result.failuresLastHour +
                ' delivery failures in the last hour';
        }
        return 'Tier 2 channel alert: no successful notification in ' + SUCCESS_WINDOW_HOURS +
            'h while escalations occurred';
    }

    /** Plain-text body. No merge syntax: a literal template token would be sent verbatim. */
    @TestVisible
    private static String buildBody(HealthCheckResult result) {
        List<String> lines = new List<String>();
        lines.add('The hourly Tier 2 notification-channel health check raised an alert.');
        lines.add('');
        lines.add('Observed at: ' + Datetime.now().format());
        lines.add('Delivery failures created in the last hour: ' + result.failuresLastHour +
            ' (threshold: more than ' + FAILURES_PER_HOUR_THRESHOLD + ')');
        lines.add('Delivery failures created in the last ' + SUCCESS_WINDOW_HOURS + ' hours: ' +
            result.failuresLastDay);
        lines.add('Cases successfully notified in the last ' + SUCCESS_WINDOW_HOURS + ' hours: ' +
            result.successesLastDay);
        lines.add('');
        lines.add('Rule fired - failure burst in the hour: ' + result.failureBurst);
        lines.add('Rule fired - no success while escalations occurred: ' + result.channelSilent);
        lines.add('');
        lines.add('Open the Integration Failure list view to triage. A failed delivery is ' +
            'resent by ticking Resend on the failure record.');
        return String.join(lines, '\n');
    }

    /** One-line summary reused by every log line this class writes. */
    private static String describe(HealthCheckResult result) {
        return 'failuresLastHour=' + result.failuresLastHour +
            ', failuresLastDay=' + result.failuresLastDay +
            ', successesLastDay=' + result.successesLastDay +
            ', failureBurst=' + result.failureBurst +
            ', channelSilent=' + result.channelSilent;
    }
}
