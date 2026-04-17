# Well-Architected Notes — Flow Governor Limits Deep Dive

## Relevant Pillars

- **Performance** — Limit budgeting is performance engineering. A flow with 70% headroom survives load spikes; a flow at 95% fails on the first busy day.
- **Reliability** — Shared-transaction math predicts cascading failures before they happen. Adding "one more flow" without budget analysis is how orgs become fragile.

## Architectural Tradeoffs

### Inline vs async execution

| Inline (sync transaction) | Async (Scheduled Path, Platform Event) |
|---|---|
| Fresh limits? No — shared with caller | Fresh limits? Yes |
| Latency | Immediate | 1-5 min |
| Rollback on failure | Yes (with original save) | No (original already committed) |
| User-perceived save time | Flow time adds to save | Negligible |

Rule: async for work that doesn't need to be atomic with the save.

### Budget thresholds

- 70% of limit = healthy
- 70-90% = monitor, consider tuning
- 90%+ = unstable, must tune

Design target: stay under 70% at peak bulk size.

## Anti-Patterns

1. **SOQL/DML in a Loop** — The classic limit breach. Fix: hoist out, bulk-operate on collections.
2. **Nominal-limit reasoning** — Ignoring shared transaction. Fix: forecast total across all automations on the object.
3. **Unbounded collections** — Heap breach. Fix: chunk + process.
4. **No test-level limit assertion** — Regressions ship silently. Fix: assert `Limits.getQueries()` in tests.
5. **Async-as-panacea** — Routing to Scheduled Path without fixing bulk-unsafe code. Fix: fix the code first; async is for transaction isolation, not bulk safety.

## Official Sources Used

- Salesforce Developer — Execution Governors and Limits: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Salesforce Help — Flow Limits and Considerations: https://help.salesforce.com/s/articleView?id=sf.flow_considerations_limit.htm
- Salesforce Architects — Performance Engineering: https://architect.salesforce.com/
- Salesforce Developer — Trigger Order of Execution: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_order_of_execution.htm
