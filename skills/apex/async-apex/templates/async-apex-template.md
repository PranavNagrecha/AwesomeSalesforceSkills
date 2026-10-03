# Async Apex Decision Worksheet

## Workload Profile

| Question | Answer |
|---|---|
| Trigger point | Trigger / UI / Flow / Schedule / Integration |
| Estimated records or payloads | |
| Callout required? | Yes / No |
| Must run on a schedule? | Yes / No |
| Need monitoring by job ID? | Yes / No |
| Partial success acceptable? | Yes / No |
| Called from an async context (Batch, Queueable, future)? | Yes / No (1 enqueue, 0 future calls from Batch or future) |
| Concurrent batch jobs expected at peak | (5 active, 100 in flex queue) |
| Share of daily async executions this job uses | |

## Mechanism Choice

| Option | Choose? | Why / Why Not |
|---|---|---|
| Queueable | | |
| Batch Apex | | |
| `@future` | | |
| Schedulable | | |
| Apex Cursors + chained Queueable | | |

## Guardrails

- [ ] Do not enqueue jobs inside loops.
- [ ] Queueable callout work implements `Database.AllowsCallouts`.
- [ ] Batch `execute()` is idempotent and handles partial failure intentionally.
- [ ] Scheduler dispatches a worker rather than performing business logic inline.
- [ ] Tests use `Test.startTest()` and `Test.stopTest()` for async assertions.
- [ ] No future calls from Batch or future contexts.
- [ ] Scheduled class has no synchronous callouts; pending jobs deleted before redeploy.
- [ ] `python3 scripts/check_async_apex.py --manifest-dir force-app/main/default` reviewed.

## Final Recommendation

**Chosen async mechanism:**  
`Queueable / Batch / @future / Schedulable`

**Operational notes:**  
Document retries, monitoring owner, and failure destination.
