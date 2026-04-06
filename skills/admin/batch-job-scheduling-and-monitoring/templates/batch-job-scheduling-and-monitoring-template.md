# Batch Job Scheduling And Monitoring — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `batch-job-scheduling-and-monitoring`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- **Job type:** [ ] Batch Apex  [ ] Scheduled Apex  [ ] Queueable  [ ] Flow scheduled  [ ] @future
- **Issue type:** [ ] Job stuck in Queued  [ ] Job failed silently  [ ] Job never fired  [ ] Performance
- **Time range of interest:** _______________

## Diagnostic SOQL

```soql
-- Job status check (last 24 hours)
SELECT ApexClass.Name, Status, JobType, NumberOfErrors, TotalJobItems,
       CreatedDate, CompletedDate, ExtendedStatus
FROM AsyncApexJob
WHERE JobType IN ('BatchApex', 'ScheduledApex', 'Queueable')
  AND CreatedDate = LAST_N_HOURS:24
ORDER BY CreatedDate DESC
LIMIT 50

-- Count concurrent Batch Apex jobs
SELECT Id, ApexClass.Name, Status, CreatedDate
FROM AsyncApexJob
WHERE JobType = 'BatchApex'
  AND Status = 'Processing'
```

## Findings

- **Status:** _______________
- **NumberOfErrors:** _______________
- **ExtendedStatus:** _______________
- **Concurrent Batch jobs in Processing:** ___ / 5 (limit)

## Checklist

- [ ] Correct monitoring view used (Apex Jobs vs Scheduled Jobs for Flows)
- [ ] ExtendedStatus checked for failed jobs
- [ ] Concurrent job count checked against 5-job limit
- [ ] Batch finish() method has NumberOfErrors notification
- [ ] Scheduled Apex schedule definition confirmed in Scheduled Jobs UI

## Notes

(Record any deviations from the standard pattern and why.)
