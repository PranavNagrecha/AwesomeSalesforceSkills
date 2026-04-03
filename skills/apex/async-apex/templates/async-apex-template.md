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

## Mechanism Choice

| Option | Choose? | Why / Why Not |
|---|---|---|
| Queueable | | |
| Batch Apex | | |
| `@future` | | |
| Schedulable | | |

## Guardrails

- [ ] Do not enqueue jobs inside loops.
- [ ] Queueable callout work implements `Database.AllowsCallouts`.
- [ ] Batch `execute()` is idempotent and handles partial failure intentionally.
- [ ] Scheduler dispatches a worker rather than performing business logic inline.
- [ ] Tests use `Test.startTest()` and `Test.stopTest()` for async assertions.

## Final Recommendation

**Chosen async mechanism:**  
`Queueable / Batch / @future / Schedulable`

**Operational notes:**  
Document retries, monitoring owner, and failure destination.
