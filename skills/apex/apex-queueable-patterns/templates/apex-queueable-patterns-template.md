# Apex Queueable Patterns — Work Template

Use this template when designing, implementing, or reviewing Queueable Apex jobs.

---

## Scope

**Skill:** `apex-queueable-patterns`

**Request summary:** (fill in what the user asked for — new implementation, review, or troubleshoot)

**Mode:** [ ] Mode 1 — Implement   [ ] Mode 2 — Review/Audit   [ ] Mode 3 — Troubleshoot

---

## Context Gathered

Answer these before proceeding:

| Question | Answer |
|---|---|
| Where is the enqueue called from — trigger, controller, batch `finish()`, finalizer? (50 per sync transaction, 1 per async) | |
| Does the job make outbound HTTP or web service callouts, and does it also write records? (callouts must precede all DML) | |
| Does the job need to chain to a next step? If so, how many steps maximum? | |
| Does failure require cleanup, notification, or compensating action? | |
| How is state passed between chain links? | |
| What is the expected record or payload volume per job execution? | |
| Can the same logical work be enqueued from two different transactions? (`AsyncOptions.DuplicateSignature`) | |
| Who runs it, and are they in system mode? (View Setup and Configuration is required outside system mode) | |
| How will operations monitor job success and failure? | |

---

## Pattern Selection

Check the pattern that applies:

- [ ] **Single deferred job** — plain Queueable, no chaining, Finalizer optional
- [ ] **Bounded multi-step chain** — Queueable + `AsyncOptions.MaximumQueueableStackDepth` + stack depth guard
- [ ] **Callout job** — `implements Queueable, Database.AllowsCallouts`
- [ ] **Callout with retry** — Queueable + `AllowsCallouts` + Finalizer-based retry with counter
- [ ] **Error recovery / compensating action** — Queueable + `System.attachFinalizer()`

**Reason for selection:** ___________________________________________

---

## Implementation Checklist

Work through these in order:

- [ ] Class declaration includes `implements Queueable` (and `Database.AllowsCallouts` if callouts are made).
- [ ] `System.attachFinalizer(new MyFinalizer(...))` is the first call inside `execute()` if failure handling matters.
- [ ] `execute()` body enqueues **at most one** child Queueable.
- [ ] If chaining: `AsyncOptions.MaximumQueueableStackDepth` is set on every `System.enqueueJob()` call.
- [ ] If chaining: `System.AsyncInfo.getCurrentQueueableStackDepth()` is checked before re-enqueueing.
- [ ] State is passed through constructor parameters — no static variables used to bridge transactions.
- [ ] Finalizer implements `System.Finalizer` and checks `ctx.getResult()` before deciding action.
- [ ] Finalizer uses `ctx.getAsyncApexJobId()` and `ctx.getRequestId()` — `FinalizerContext` has no `getJobId()`.
- [ ] No `transient` member on the Queueable or the Finalizer (serialized as `null`).
- [ ] Sharing is declared explicitly on the Queueable class.
- [ ] The enqueue call site is a single helper, not a per-record loop.
- [ ] Finalizer enqueues retry or compensating Queueable (not performing heavy inline work).
- [ ] Tests use `Test.startTest()` / `Test.stopTest()` boundaries for async execution.
- [ ] No test class that enqueues carries `@IsTest(IsParallel=true)`.
- [ ] Checker run clean: `python3 skills/apex/apex-queueable-patterns/scripts/check_apex_queueable_patterns.py --manifest-dir <src> --strict`.
- [ ] `AsyncApexJob` query or monitoring plan is in place for operations.

---

## Finalizer Design

Complete this section if a Finalizer is included:

**Finalizer class name:** ___________________________________________

**On `ParentJobResult.SUCCESS`:** ___________________________________________

**On `ParentJobResult.UNHANDLED_EXCEPTION`:**

- Max retries before giving up: ___________
- Retry action: [ ] Re-enqueue same job   [ ] Enqueue compensating job   [ ] Neither
- Failure record or notification: ___________________________________________

---

## Chain Design

Complete this section if the job chains to a next step:

**Maximum stack depth (`MaximumQueueableStackDepth`):** ___________

**Termination condition (what stops the chain):** ___________________________________________

**Action when depth cap is reached before termination:** ___________________________________________

**State fields passed to next job constructor:**

| Field | Type | Purpose |
|---|---|---|
| | | |
| | | |

---

## Review Findings (Mode 2)

If reviewing an existing Queueable, record findings here:

| Finding | Severity | File | Recommendation |
|---|---|---|---|
| | | | |
| | | | |

Run the checker for automated findings:
```bash
python3 skills/apex/apex-queueable-patterns/scripts/check_apex_queueable_patterns.py \
  --manifest-dir force-app/main/default/classes
```

---

## Troubleshooting Notes (Mode 3)

If diagnosing a failing or stuck job:

**Symptom:** ___________________________________________

**`AsyncApexJob` query used:**
```soql
SELECT Id, ApexClass.Name, JobType, Status, NumberOfErrors, ExtendedStatus,
       CreatedDate, CompletedDate
FROM AsyncApexJob
WHERE Id = '<job-id>'
```

Do not filter on `Status = 'Holding'` or read `JobItemsProcessed` / `TotalJobItems`:
`Holding` is a batch/flex-queue status and the batch counters are always zero for
Queueable jobs. See `references/gotchas.md`.

**`ExtendedStatus` error message:** ___________________________________________

**Probable cause (select one):**
- [ ] Missing `Database.AllowsCallouts`
- [ ] Multiple children enqueued in one `execute()` (LimitException)
- [ ] Unbounded chain hit platform queue limits
- [ ] Finalizer failure (separate transaction rolled back)
- [ ] State deserialization error (complex type in constructor)
- [ ] `transient` member arrived `null`
- [ ] Callout attempted after DML in the same `execute()`
- [ ] Duplicate signature suppressed the enqueue (`DuplicateMessageException` treated as an error)
- [ ] Running user lacks View Setup and Configuration (enqueue outside system mode)
- [ ] Sharing mode changed by an `apiVersion` bump to 67.0 or later
- [ ] Governor limit exceeded inside `execute()`
- [ ] Other: ___________________________________________

**Resolution steps:** ___________________________________________

---

## Notes

Record any deviations from the standard patterns and the reason why:

___________________________________________
