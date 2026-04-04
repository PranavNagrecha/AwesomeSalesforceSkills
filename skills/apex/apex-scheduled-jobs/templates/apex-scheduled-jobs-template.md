# Apex Scheduled Jobs — Work Template

Use this template when designing, reviewing, or troubleshooting Apex scheduled jobs.

---

## Scope

**Skill:** `apex-scheduled-jobs`

**Request summary:** (fill in what the user asked for)

**Mode:** (circle one) Implement / Review-Audit / Troubleshoot

---

## Context Gathered

Answer these before proceeding:

- **Schedulable class name:** `___________________________________`
- **Purpose / business operation:** ___________________________________
- **Desired schedule frequency:** (e.g., daily, weekly, first of month)
- **Desired time of day:** ___________ (prefer off-peak, typically 1:00 AM – 5:00 AM)
- **Approximate record volume processed per run:** ___________________________________
- **Does the job need outbound callouts?** Yes / No
- **Current org scheduled job count:** ___ / 100

---

## Cron Expression Builder

| Field | Value | Notes |
|---|---|---|
| Seconds | `0` | Must be 0 — sub-minute scheduling not supported |
| Minutes | ___ | 0–59 |
| Hours | ___ | 0–23 |
| Day_of_month | ___ or `?` | Use `?` if Day_of_week is specified |
| Month | `*` or specific | `*` = every month; `1-12` or `JAN-DEC` |
| Day_of_week | ___ or `?` | Use `?` if Day_of_month is specified; `MON-FRI`, `SUN`, etc. |
| Year (optional) | _(omit)_ | Omit for recurring schedules |

**Resulting cron expression:** `'_______________________'`

**Plain-English verification:** This job runs ___________________________________

---

## Implementation Checklist

### Schedulable Class

- [ ] Class declared `global` (not `public`)
- [ ] Implements `Schedulable`
- [ ] Method signature: `global void execute(SchedulableContext SC)`
- [ ] `execute()` contains only dispatch calls — no heavy SOQL or DML inline
- [ ] Callouts delegated to Queueable with `Database.AllowsCallouts` (if applicable)

### Scheduling Call

- [ ] Job name is unique in the org (verify with CronTrigger query below)
- [ ] Cron expression validated against the seven-field format
- [ ] Abort-before-schedule pattern used in deployment script (idempotent)
- [ ] Post-deployment script documented and checked into source control

### Testing

- [ ] Test class uses `Test.startTest()` / `Test.stopTest()` boundary
- [ ] `CronTrigger` state verified as `'WAITING'` after `Test.stopTest()`
- [ ] `CronExpression` field verified against expected value

### Operational

- [ ] Org job count verified below 100 before scheduling
- [ ] Off-peak timing confirmed
- [ ] Sandbox post-refresh scheduling script exists (if job is needed in sandboxes)

---

## Code Scaffold

### Schedulable Class

```apex
global class [ClassName] implements Schedulable {

    global void execute(SchedulableContext SC) {
        // DISPATCH ONLY — do not put heavy logic here
        // Option A: Batch Apex
        // Database.executeBatch(new [BatchClass](), [batchSize]);

        // Option B: Queueable
        // System.enqueueJob(new [QueueableClass]());
    }
}
```

### Post-Deployment Script (Anonymous Apex)

```apex
// [ProjectName] — Schedule [ClassName]
// Run this after each deployment that introduces or modifies this job.

final String JOB_NAME = '[Human-readable job name]';
final String CRON    = '[0 0 2 * * ?]'; // Update with correct expression

List<CronTrigger> existing = [
    SELECT Id FROM CronTrigger
    WHERE CronJobDetail.Name = :JOB_NAME
    AND State = 'WAITING'
    LIMIT 1
];
if (!existing.isEmpty()) {
    System.abortJob(existing[0].Id);
}
String jobId = System.schedule(JOB_NAME, CRON, new [ClassName]());
System.debug('Scheduled job ID: ' + jobId);
```

### Monitoring Query

```soql
SELECT Id, CronJobDetail.Name, CronExpression, State, NextFireTime, PreviousFireTime
FROM CronTrigger
WHERE State IN ('WAITING', 'PAUSED', 'BLOCKED', 'ERROR')
ORDER BY NextFireTime ASC
```

### Test Class

```apex
@IsTest
private class [ClassName]Test {

    @IsTest
    static void testScheduling() {
        Test.startTest();
        String jobId = System.schedule(
            'Test [ClassName]',
            '0 0 2 * * ?',
            new [ClassName]()
        );
        Test.stopTest();

        CronTrigger ct = [
            SELECT State, CronExpression
            FROM CronTrigger
            WHERE Id = :jobId
        ];
        System.assertEquals('WAITING', ct.State, 'Job should be in WAITING state');
        System.assertEquals('0 0 2 * * ?', ct.CronExpression, 'Cron expression should match');
    }
}
```

---

## Troubleshooting Reference

| Symptom | First Query | Likely Cause |
|---|---|---|
| Job not running | `SELECT State FROM CronTrigger WHERE CronJobDetail.Name = 'My Job'` | State may be ERROR, DELETED, or BLOCKED |
| AsyncException on schedule | `SELECT COUNT() FROM CronTrigger WHERE State IN ('WAITING','PAUSED','BLOCKED')` | Org at or near 100-job limit |
| CalloutException at runtime | Review `execute()` for direct HTTP calls | Callouts not supported in Scheduled Apex context |
| Job missing after deployment | Check if post-deploy script was run | Scheduled jobs are not Metadata API-deployable |
| Job missing after sandbox refresh | Check sandbox initialization runbook | Scheduled jobs are not copied on sandbox refresh |
| Duplicate name exception | Query CronTrigger by name before scheduling | Job with that name already exists in WAITING state |

---

## Notes

(Record any deviations from the standard pattern and the reason for each)

-
