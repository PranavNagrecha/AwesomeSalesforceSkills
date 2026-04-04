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
| Does the job make outbound HTTP or web service callouts? | |
| Does the job need to chain to a next step? If so, how many steps maximum? | |
| Does failure require cleanup, notification, or compensating action? | |
| How is state passed between chain links? | |
| What is the expected record or payload volume per job execution? | |
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
- [ ] Finalizer enqueues retry or compensating Queueable (not performing heavy inline work).
- [ ] Tests use `Test.startTest()` / `Test.stopTest()` boundaries for async execution.
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
SELECT Id, Status, NumberOfErrors, ExtendedStatus, JobType
FROM AsyncApexJob
WHERE Id = '<job-id>'
```

**`ExtendedStatus` error message:** ___________________________________________

**Probable cause (select one):**
- [ ] Missing `Database.AllowsCallouts`
- [ ] Multiple children enqueued in one `execute()` (LimitException)
- [ ] Unbounded chain hit platform queue limits
- [ ] Finalizer failure (separate transaction rolled back)
- [ ] State deserialization error (complex type in constructor)
- [ ] Governor limit exceeded inside `execute()`
- [ ] Other: ___________________________________________

**Resolution steps:** ___________________________________________

---

## Notes

Record any deviations from the standard patterns and the reason why:

___________________________________________
