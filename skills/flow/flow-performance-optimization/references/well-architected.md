# Well-Architected Notes — Flow Performance Optimization

## Relevant Pillars

- **Performance** — The whole skill is about performance. Each pattern addresses one of the six highest-impact levers.
- **Reliability** — A performant flow survives load spikes. Un-tuned flows pass in test but break on the first busy production day.

## Architectural Tradeoffs

### Before-Save vs After-Save

| Before-Save | After-Save |
|---|---|
| No DML cost | Adds a DML per record update |
| Same transaction | Same transaction |
| Same-record field work only | All element types |
| 10-50× cheaper for field derivation | Needed for cross-object work |

Rule: Before-Save for field derivation on the same record; After-Save for cross-object work.

### Inline vs Scheduled Path

| Inline | Scheduled Path +0 |
|---|---|
| User feels save time | Negligible user impact |
| Shared limits with save | Fresh limits |
| Atomic with save | Runs after commit; no rollback |
| Sync latency | 1-5 min latency |

Rule: inline for atomic / user-expected; async for fire-and-forget enrichment.

### Optimize vs split

Sometimes a flow is inherently too much work for one transaction. Splitting into a record-triggered Flow (critical path) + a Scheduled Path (non-critical enrichment) beats trying to tune everything inline.

## Anti-Patterns

1. **Tuning without measuring** — Can't verify the fix. Fix: benchmark.
2. **Optimizing the wrong thing** — Micro-optimizations while SOQL-in-loop dominates. Fix: profile first.
3. **Async as panacea** — Moving to Scheduled Path without fixing bulk-unsafe code. Fix: fix the code; async is transaction isolation, not bulk safety.
4. **Loading all fields unconditionally** — Heap bloat. Fix: explicit field lists.
5. **Premature micro-optimization** — Readability cost exceeds perf gain. Fix: stop at SLA + 30% headroom.

## Official Sources Used

- Salesforce Developer — Flow Performance Optimization: https://developer.salesforce.com/blogs/2022/07/flow-performance-optimization
- Salesforce Help — Flow Limits and Considerations: https://help.salesforce.com/s/articleView?id=sf.flow_considerations_limit.htm
- Salesforce Help — Before-Save vs After-Save Flows: https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger.htm
- Salesforce Architects — Performance Engineering: https://architect.salesforce.com/
