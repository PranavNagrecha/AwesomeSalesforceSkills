---
name: scheduled-path-patterns
description: "Scheduled Paths in record-triggered Flow: delayed execution, time-offset from field, batch size tuning, monitoring Paused Flow Interviews, async limits. NOT for Scheduled Flow (use scheduled-flow-patterns). NOT for time-based workflow rules (use migrate-workflow-pb)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
tags:
  - scheduled-paths
  - flow
  - record-triggered
  - async
  - paused-interviews
triggers:
  - "record triggered flow scheduled path 1 hour after create"
  - "scheduled path batch size and governor limit behavior"
  - "paused flow interview monitoring and failures"
  - "scheduled path runs too late or never runs"
  - "flow time offset from custom date field"
  - "scheduled path vs scheduled flow difference"
inputs:
  - Record-triggered Flow in scope
  - Offset requirement (after/before record create/update event)
  - Expected volume of records per path per hour
  - Time-sensitivity of execution
outputs:
  - Scheduled Path design (offset, batch size, filter)
  - Monitoring plan for Paused Flow Interviews
  - Fallback strategy for failed paths
  - Bulk test plan
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
---

# Scheduled Path Patterns

Activate when designing a record-triggered Flow with delayed execution — "after 1 hour," "1 day before Close Date," "every Monday at 9 AM after creation." Scheduled Paths replace many time-based workflow rule use cases but have their own batching, monitoring, and failure semantics.

## Before Starting

- **Understand the offset anchor.** Scheduled Paths offset from either the record-triggered event time OR a field value on the record.
- **Plan for volume.** Scheduled Paths queue paused Flow Interviews; bulk inserts create bulk paused interviews with batch-size tuning.
- **Know the monitoring surface.** Setup → Paused Flow Interviews shows queued interviews; failures surface in the Flow debug log and Apex exception email.

## Core Concepts

### Offset types

- **From the trigger event**: "1 hour after record is created"
- **From a field value**: "3 days before CloseDate" — uses a datetime/date field on the record

### Batch size

Salesforce processes paused interviews in batches (default 200, tunable in Process Automation settings). Batching controls governor limits for the collection of resumed flows.

### Paused Flow Interview

When a Flow hits a Scheduled Path wait, it suspends as a Paused Flow Interview. The interview resumes at the scheduled time. Monitor at Setup → Paused Flow Interviews.

### Execution context

Scheduled path execution runs in system context by default (like other record-triggered Flow), with its own governor limit scope. Updates to records made in the scheduled branch are separate transactions from the trigger.

## Common Patterns

### Pattern: Follow-up reminder 24 hours after creation

Record-Triggered Flow on Case Create → Scheduled Path 1 day after creation → Check IsClosed → If open, send notification to owner.

### Pattern: Pre-renewal email 30 days before renewal date

Trigger on Contract update → Scheduled Path 30 days before `RenewalDate__c` → Send email alert.

### Pattern: Re-check condition at path execution

Always re-query record state in the scheduled branch. The record may have changed between queue-time and execution-time.

## Decision Guidance

| Need | Mechanism |
|---|---|
| Run N hours/days after record event | Scheduled Path |
| Run at an absolute time (9 AM Monday) | Scheduled Flow or cron |
| Run when a field value changes | Record-triggered Flow (no scheduled path) |
| Delayed re-check of async state | Scheduled Path + re-query |
| High-volume time-based fan-out | Apex Schedulable + Queueable |

## Recommended Workflow

1. Identify the offset anchor: event time vs field value.
2. Define the exact offset (units: minutes, hours, days).
3. Add explicit filter criteria to the path entry — avoid queuing millions of no-op interviews.
4. In the scheduled branch, re-query or re-check the record's current state.
5. Tune Process Automation batch size for your volume.
6. Monitor Paused Flow Interviews in Setup; handle failures via admin email.
7. Test with a bulk insert to confirm batch behavior.

## Review Checklist

- [ ] Offset type explicit (event vs field)
- [ ] Entry criteria scoped tightly (no "always queue")
- [ ] Scheduled branch re-checks current record state
- [ ] Batch size reviewed for volume profile
- [ ] Paused Flow Interview monitoring documented
- [ ] Admin notification on scheduled-path errors enabled
- [ ] Bulk insert test confirms expected behavior

## Salesforce-Specific Gotchas

1. **Deleting the triggering record deletes its paused interview.** The scheduled branch never runs for deleted records.
2. **Changing the source field after the path is scheduled does NOT reschedule.** The scheduled time is computed once at entry.
3. **Flow version updates do not migrate paused interviews.** Queued interviews execute under the version that queued them; test version swaps carefully.

## Output Artifacts

| Artifact | Description |
|---|---|
| Scheduled Path design | Offset anchor, filter, re-check logic |
| Monitoring runbook | Where to check Paused Flow Interviews + error emails |
| Volume test plan | Bulk insert → expected queued count |

## Related Skills

- `flow/scheduled-flow-patterns` — absolute-time scheduled flows
- `admin/migrate-workflow-pb` — replacing time-based workflow rules
- `apex/apex-queueable-patterns` — programmatic async alternatives
