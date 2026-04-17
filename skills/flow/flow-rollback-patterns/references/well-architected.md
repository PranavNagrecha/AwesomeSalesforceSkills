# Well-Architected Notes — Flow Rollback Patterns

## Relevant Pillars

- **Reliability** — Rollback is the only Flow primitive that gives atomic all-or-nothing semantics. Without it, partial commits accumulate as data inconsistency that requires manual cleanup.
- **Security** — Incomplete record graphs may expose sensitive data in unexpected contexts (an orphan Opportunity without Account linkage). Rollback restores the invariant that protects security posture.

## Architectural Tradeoffs

### Rollback vs compensation

| Rollback | Compensation |
|---|---|
| Scope: current transaction only | Scope: across systems or across transactions |
| Instant | Requires explicit reversal logic |
| Free (built-in element) | Must design + test |
| Doesn't affect external systems | Works anywhere |

Rule: use Rollback when all affected state is in the current Salesforce transaction. Use compensation when external systems or previously-committed transactions are involved.

### Atomic flow vs split-transaction flow

Atomic: keep everything in one transaction; use Rollback on failure. Simpler recovery, but the whole operation is synchronous.

Split: push non-critical work to Scheduled Path (new transaction). Faster UX, but loses atomic semantics — the Scheduled Path's work may fail independently.

## Anti-Patterns

1. **Explicit Delete instead of Rollback** — uses more DML, can itself fault mid-cleanup. Fix: use Rollback Records.

2. **Log after Rollback** — the log is rolled back too. Fix: log first, rollback second.

3. **Rollback on every fault** — over-applied, erases logging and notification work. Fix: rollback only for business-invariant violations; use Silent End for non-critical failures.

4. **Assume Rollback undoes callouts / emails / events** — it doesn't. Fix: sequence those operations AFTER rollback-eligible DML, or design compensation for them.

## Official Sources Used

- Salesforce Help — Flow Rollback Records Element: https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_rollback.htm
- Salesforce Help — Flow Fault Connector Paths: https://help.salesforce.com/s/articleView?id=sf.flow_ref_faults.htm
- Salesforce Developer — Transaction Control: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_transaction_control.htm
- Salesforce Architects — Well-Architected Framework: https://architect.salesforce.com/
