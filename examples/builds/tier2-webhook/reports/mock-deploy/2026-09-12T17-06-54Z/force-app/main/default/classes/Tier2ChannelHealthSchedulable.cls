/**
 * Tier2ChannelHealthSchedulable
 *
 * Clock-only entry point for the hourly Tier 2 notification-channel health check
 * (build tier2-webhook, step M1-S04, decision D11). It holds the CRON literal and
 * the job name, and it hands every query, every decision and every send to
 * Tier2ChannelHealthQueueable.
 *
 * Why so thin: the step input fixes the shape as "execute() only enqueues a
 * Queueable and does nothing else", and the Apex Developer Guide gives the reason
 * - "Although scheduled Apex is an asynchronous feature, synchronous limits apply
 * to scheduled Apex jobs" (apexdev L19536), so this body gets 100 SOQL / 6 MB heap
 * / 10,000 ms CPU rather than the async budget. The guide's own recommendation is
 * that "all processing must take place in a separate class" (apexdev L16972).
 *
 * `public` (not `global`) is deliberate: the guide requires the execute method be
 * "global or public" (apexdev L16620) and its own sample is a `public with sharing`
 * class. `global` is only needed to cross a managed-package namespace.
 *
 * Deliberately NOT here, and why - read deploy-order.md sections 0 and 4 before adding any:
 *  - No logging call of any kind. The 2026-09-12 amendment set include_logger false:
 *    ApplicationLogger is not referenced by this step, and with no logging requirement
 *    left there is nothing to weigh against "does nothing else". execute() enqueues,
 *    full stop. Dispatch is observable on CronTrigger and AsyncApexJob - the
 *    verification SOQL is in deploy-order.md section 6.
 *  - No in-flight guard on a prior run. skills/apex/apex-scheduled-jobs' Review
 *    Checklist asks for one; the step input's "does nothing else" forbids the SOQL
 *    it needs. The worker is four queries and one email, so a run that outlives its
 *    hour is not a shape this feature produces.
 *  - No System.schedule call. The active job is data, not metadata: nothing in
 *    package.xml recreates a CronTrigger, so scheduling is a post-deploy step
 *    (deploy-order.md section 6), and a prior job of this name must be aborted
 *    first or System.schedule throws
 *    'System.AsyncException: The Apex job named "jobName" is already scheduled
 *    for execution' (apexdev L16812).
 */
public with sharing class Tier2ChannelHealthSchedulable implements Schedulable {

    /**
     * Display name stored on CronJobDetail.Name. Unique per org: a duplicate name
     * throws System.AsyncException at schedule time (apexdev L16810-L16813).
     */
    public static final String JOB_NAME = 'Tier 2 Channel Health Check';

    /**
     * Hourly, on the hour. Six fields in the documented order
     * Seconds Minutes Hours Day_of_month Month Day_of_week (apexdev L16815-L16817),
     * with Day_of_week set to the no-specific-value marker because Day_of_month is
     * a wildcard - that marker is legal only in those two fields (apexdev L16879-L16881).
     * Hourly is the maximum legal frequency: "Apex doesn't allow for a job to be
     * scheduled more than once an hour" (apexdev L16923).
     *
     * The expression is read in the TIME ZONE OF THE USER WHO RUNS System.schedule
     * (apexdev L16820) and frozen onto CronTrigger.TimeZoneSidKey. On the hour, that
     * makes no difference to when this job fires; it is recorded because the same is
     * not true of any later change to this literal.
     */
    public static final String CRON_EXPRESSION = '0 0 * * * ?';

    /** Enqueue the worker. Nothing else. */
    public void execute(SchedulableContext sc) {
        System.enqueueJob(new Tier2ChannelHealthQueueable());
    }
}
