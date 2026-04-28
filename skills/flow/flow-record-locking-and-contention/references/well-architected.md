# Well-Architected Notes — Flow Record Locking And Contention

## Relevant Pillars

- **Reliability** — Lock contention is a primary cause of silent data loss in Salesforce orgs. A flow that surfaces UNABLE_TO_LOCK_ROW once a day is corrupting state in a way that's hard to detect (the user thinks the change happened; the database disagrees). Eliminating lock contention through decouple patterns is foundational reliability work — it transforms a flaky, load-dependent flow into one that completes deterministically regardless of concurrent traffic. Adding fault paths and central error logging makes the remaining contention observable, which is the precondition for ongoing reliability improvement.
- **Performance** — Lock contention is the dominant cause of latency for high-traffic flows. A synchronous Update Account from an Opportunity flow holds the Account lock for the duration of the entire transaction, serializing every concurrent Opportunity update on the same Account. Under sustained load, throughput on the Account drops to roughly 1/N of its parallel potential, where N is the contention factor. Decoupling via Platform Event releases the lock immediately, restoring parallel throughput on the user-facing transaction.
- **Operational Excellence** — Contention is observable through `EventLogFile`, fault emails, Background Operations status, and central log queries. A mature ops practice monitors these signals weekly, treats new UNABLE_TO_LOCK_ROW occurrences as a regression, and feeds the data back into flow design reviews. Without monitoring, contention accumulates as invisible technical debt that surfaces only during peak events (quarter-end, marketing campaigns, M&A data loads) when it's hardest to debug.

(Security is not the primary pillar here — contention is a reliability/performance issue, and the decouple patterns themselves do not change the security posture. However, Scheduled Path and Platform Event subscriber flows run as Automated Process user, which has implications for sharing — see gotcha 10.)

## Architectural Tradeoffs

The decouple patterns each trade off latency, complexity, and observability differently:

| Pattern | User-perceived latency | Complexity | Observability | When it's the right call |
|---|---|---|---|---|
| Collect-then-update (single bulk DML) | Same as before (in-line) | Low — restructure existing flow | Same as before | Always — it's a no-cost win for any loop+DML pattern |
| Platform Event decouple | Near-zero (publisher commits immediately) | Medium — event definition + subscriber flow | Medium — events appear in Event Monitoring | High concurrent traffic on the parent; user can't wait |
| Queueable Apex handoff | Near-zero (action enqueues and returns) | Medium-High — requires Apex skill | High — Queueable jobs visible in Apex Jobs | Heavy parent recalc, callouts, or work that needs Apex governor headroom |
| Scheduled Path | Up to N minutes lag | Low — built into Flow Builder | Low — scheduled paths visible only in setup | Parent update can tolerate latency; off-hours batching desired |
| `FOR UPDATE` invocable | Higher (lock held longer) | High — requires Apex | Low | Genuine read-modify-write race; never as a generic contention fix |

The right tradeoff depends on:

1. **User expectation of immediate consistency.** If the rep edits an Opportunity and immediately refreshes the Account page expecting to see the new Total_Pipeline, Platform Event decouple's eventual consistency may surprise them. In practice, Platform Event subscriber latency is sub-second under normal load, and the user rarely refreshes within that window. But if strict immediate consistency is required, decoupling is the wrong answer — instead, reduce the work in the synchronous transaction so the parent lock is held briefly.

2. **Failure visibility.** Decoupled patterns separate the failure surface from the user's transaction. This is usually good (the user isn't impacted by transient contention) but bad if the user needs to know about failures (e.g., a sales rep wants to know their pipeline rolled up correctly). Platform Event subscriber failures need an alerting path back to a human, typically via `Integration_Log__c` + a daily ops review.

3. **Apex skill in the org.** Queueable handoff requires Apex. Orgs without Apex capacity should default to Platform Event or Scheduled Path. The skill cost of introducing Apex for one decouple pattern is rarely justified — but if Apex is already in use elsewhere, Queueable is the most flexible decouple target.

4. **Skew.** Account skew amplifies contention non-linearly. Decouple patterns help but cannot fully solve a 100k-Opportunity-per-Account problem. Skew resolution should precede contention work — don't put a Platform Event in front of a skew problem and expect it to scale.

## Anti-Patterns

1. **Adding application-level retry on top of platform retry** — Salesforce already retries DML 10 times with exponential backoff. Layering a Flow-level retry loop with Wait elements multiplies the contention window without resolving the underlying problem. The fix is architectural decoupling, not more retries.

2. **Using `FOR UPDATE` as a generic contention fix** — `FOR UPDATE` is correct only for read-modify-write race conditions (counter increments, sequence number generation). Used for generic contention, it makes the problem worse by extending the lock-hold duration. Practitioners reach for it because it sounds like a "stronger lock" — it's actually a longer lock.

3. **Synchronous parent update from a high-traffic child flow** — The default flow design pattern (Get → Update parent in the same transaction as the child Update) is a contention bomb on hot parents. Recognize this shape and decouple by default if the parent is high-traffic (>1 transaction/sec sustained).

4. **Master-Detail with frequent reparenting** — Reparenting a Master-Detail child locks both old and new masters. If your data model requires frequent reparenting, switch to Lookup. Master-Detail is for cascading deletes and roll-up summaries; if neither benefit applies, Lookup is cheaper for the lock budget.

5. **Loop + DML inside the loop** — The single most common contention shape. 200 iterations × 1 DML each = 200 lock acquisitions on the same parent. Always collect and Update once after the loop, even if the body is "trivial" — Flow's Loop+DML is the worst-case shape under contention.

6. **Ignoring queue Group locks during mass routing** — Bulk inserting Cases into one inbound queue locks the queue's Group row for the duration of the bulk DML. If a sales-ops user is simultaneously updating queue membership, both transactions contend. Queue contention is invisible because the locked row is the Group, not the records.

## Official Sources Used

- Salesforce Help — Record Locking Overview: https://help.salesforce.com/s/articleView?id=platform.record_locking_overview.htm
- Salesforce Help — What Records Are Locked by an Update: https://help.salesforce.com/s/articleView?id=platform.record_locking_locks.htm
- Apex Developer Guide — Locking Statements: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_locking_statements.htm
- Apex Developer Guide — Locking Records: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_locking_records.htm
- Salesforce Help — Flow Considerations and Limits: https://help.salesforce.com/s/articleView?id=sf.flow_considerations.htm
- Salesforce Knowledge — Resolving UNABLE_TO_LOCK_ROW Errors: https://help.salesforce.com/s/articleView?id=000385621&type=1
- Salesforce Architects — Asynchronous Processing Decision Guide: https://architect.salesforce.com/decision-guides/async/
- Salesforce Architects — Well-Architected (Reliability + Performance pillars): https://architect.salesforce.com/well-architected/overview
