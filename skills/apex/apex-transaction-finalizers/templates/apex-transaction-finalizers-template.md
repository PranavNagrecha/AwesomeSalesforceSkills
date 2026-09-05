# Apex Transaction Finalizers — Work Template

Fill this in while you work. It is the hand-off artifact a reviewer reads before the diff.

## Scope

**Skill:** `apex-transaction-finalizers`

**Request summary:** _(what the user asked for, in one sentence)_

**Parent Queueable class:** `______________________`
**Finalizer class:** `______________________` (or `same class, both interfaces`)
**Test class:** `______________________`

## Answers to the Questions to Ask

| Question | Answer |
|---|---|
| What must still happen when the job fails — retry, durable record, released lock? | |
| Is the failure transient (callout, row lock) or deterministic (payload, validation)? | |
| `MAX_ATTEMPTS` value, and where the counter is carried | |
| Context the Finalizer needs (record IDs, payload snapshot, correlation key) | |
| Does the Finalizer call out, and to what endpoint / Named Credential? | |
| Who reads the failure signal, through which object or event, with what permissions? | |
| Is the abort / unexpected-termination path covered, or knowingly uncovered? | |

## Design Decisions

| Decision | Choice | Why |
|---|---|---|
| One class (both interfaces) vs. two | | |
| The single enqueue slot is spent on | | |
| Failure record target (`Async_Job_Error__c` / `Application_Log__c` / Platform Event) | | |
| Retry-eligible exception types | | |
| Abort-path mechanism (or "none, accepted") | | |

## Constraints Confirmed

Grounded in the Apex Developer Guide v67.0 (see `references/gotchas.md` for the line references).

- [ ] `MAX_ATTEMPTS` is strictly below the platform's five consecutive re-enqueues
- [ ] Exactly one async job (`enqueueJob` / `executeBatch` / `@future`) is reachable in the Finalizer
- [ ] No field on the Finalizer is declared `transient`
- [ ] `attachFinalizer` is the first statement of the Queueable's `execute(QueueableContext)`, called once
- [ ] Finalizer work is sized for synchronous SOQL/DML/CPU ceilings, not async ones
- [ ] `ctx.getAsyncApexJobId()` (not `getJobId()`) is used for the `AsyncApexJob` correlation

## Verification Run

```text
Checker:  python3 scripts/check_apex_transaction_finalizers.py --manifest-dir ______
Result:   ______________________________________________

Deploy:   sf project deploy start -x manifest/package.xml -o ______ -w 30
Result:   ______________________________________________

Tests:    sf apex run test -o ______ -n ______ -r human -w 20 -c
Pass/fail: ______   Coverage: ______%

AsyncApexJob check (post-run):  ______ rows Failed / ______ dead-letter rows
```

## Deviations

_(Anything done differently from `references/code-examples.md`, and why. If a claim in this package could not be grounded, record the UNVERIFIED marker you added and where.)_
