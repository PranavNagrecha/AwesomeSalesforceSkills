# Well-Architected Notes — Flow Rollback Patterns

## Relevant Pillars

- **Reliability** — Rollback is the only Flow primitive that gives atomic all-or-nothing semantics (UNVERIFIED (2026-10-20): "only" is not a corpus claim; Rollback Records is screen-flow only, api_meta 264 L73987). Without it, partial commits accumulate as data inconsistency that requires manual cleanup.
- **Security** — Incomplete record graphs may expose sensitive data in unexpected contexts (an orphan Opportunity without Account linkage). Rollback restores the invariant that protects security posture.

## Architectural Tradeoffs

### Rollback vs compensation

| Rollback | Compensation |
|---|---|
| Scope: current transaction only | Scope: across systems or across transactions |
| Instant | Requires explicit reversal logic |
| Free (built-in element, screen flows only, api_meta 264 L73987) | Must design + test |
| Doesn't affect external systems | Works anywhere |

Rule: use Rollback when all affected state is in the current Salesforce transaction. Use compensation when external systems or previously-committed transactions are involved.

### Atomic flow vs split-transaction flow

Atomic: keep everything in one transaction; use Rollback on failure. Simpler recovery, but the whole operation is synchronous.

Split: push non-critical work to an asynchronous path (post-commit logic, apexdev 264 L15692; a new transaction). Faster UX, but loses atomic semantics — the asynchronous path's work may fail independently.

## Anti-Patterns

1. **Explicit Delete instead of Rollback** — uses more DML, can itself fault mid-cleanup. Fix: use Rollback Records.

2. **Relying on a Create Records log around a Rollback** — a log created before the rollback is cancelled with it (api_meta 264 L73986). Fix: write the evidence to a Publish Immediately platform event (platform_events 264 L276-277). The earlier text said "log first, rollback second".

3. **Rollback on every fault** — over-applied, erases logging and notification work. Fix: rollback only for business-invariant violations; use Silent End for non-critical failures.

4. **Assume Rollback undoes callouts / emails / events** — it doesn't. Fix: sequence those operations AFTER rollback-eligible DML, or design compensation for them.

## Official Sources Used

- Metadata API Developer Guide 264 — FlowRecordRollback L73985-73992 (screen flows only), FlowCustomError L72592-72594, publishBehavior L44509-44520, flowTransactionModel L71022-71030
- Platform Events Developer Guide 264 — Publish Immediately cannot be rolled back L274-277, L660-661
- Apex Developer Guide 264 — order of execution, post-commit logic L15681-15692; callouts and pending operations L36340-36342
- Salesforce Help — Flow Rollback Records Element: https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_rollback.htm
- Salesforce Help — Flow Fault Connector Paths: https://help.salesforce.com/s/articleView?id=sf.flow_ref_faults.htm
- Salesforce Developer — Transaction Control: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_transaction_control.htm
- Salesforce Architects — Well-Architected Framework: https://architect.salesforce.com/
