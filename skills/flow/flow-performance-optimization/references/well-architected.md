# Well-Architected Notes — Flow Performance Optimization

## Relevant Pillars

- **Performance** — The whole skill is about performance. Each pattern addresses one of the six highest-impact levers.
- **Reliability** — A performant flow survives load spikes. Un-tuned flows pass in test but break on the first busy production day.

## Architectural Tradeoffs

### Before-Save vs After-Save

| Before-Save | After-Save |
|---|---|
| No Update Records element needed (api_meta 264 L75266-75268) | Updating the record is a DML that runs the save procedure again (apexdev 264 L15671) |
| Same transaction (before commit, apexdev 264 L15643, L15681) | Same transaction (apexdev 264 L15673, L15681) |
| Same-record field work only (api_meta 264 L75266-75268) | All element types |
| UNVERIFIED (2026-10-20): "10-50× cheaper for field derivation" | Needed for cross-object work |

Rule: Before-Save for field derivation on the same record; After-Save for cross-object work.

### Inline vs asynchronous path

| Inline | Asynchronous path (`AsyncAfterCommit`) |
|---|---|
| User feels save time | Negligible user impact |
| Shared limits with save | UNVERIFIED (2026-10-20): "Fresh limits" — the corpus does not say which limits the path runs under |
| Atomic with save | Runs after commit; no rollback (apexdev 264 L15682, L15692) |
| Sync latency | UNVERIFIED (2026-10-20): "1-5 min latency" is not in the corpus |

Rule: inline for atomic / user-expected; async for fire-and-forget enrichment.

### Optimize vs split

Sometimes a flow is inherently too much work for one transaction. Splitting into a record-triggered Flow (critical path) + an asynchronous path (non-critical enrichment) beats trying to tune everything inline.

## Anti-Patterns

1. **Tuning without measuring** — Can't verify the fix. Fix: benchmark.
2. **Optimizing the wrong thing** — Micro-optimizations while SOQL-in-loop dominates. Fix: profile first.
3. **Async as panacea** — Moving to an asynchronous path without fixing bulk-unsafe code. Fix: fix the code; async is transaction isolation, not bulk safety.
4. **Loading all fields unconditionally** — Heap bloat. Fix: explicit field lists.
5. **Premature micro-optimization** — Readability cost exceeds perf gain. Fix: stop at SLA + 30% headroom.

## Official Sources Used

- Salesforce Developer — Flow Performance Optimization (a blog post; not a corpus guide, UNVERIFIED (2026-10-20) for every figure in this package): https://developer.salesforce.com/blogs/2022/07/flow-performance-optimization
- Salesforce Help — Flow Limits and Considerations: https://help.salesforce.com/s/articleView?id=sf.flow_considerations_limit.htm
- Salesforce Help — Before-Save vs After-Save Flows: https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger.htm
- Apex Developer Guide 264 — Per-Transaction Apex Limits (100 SOQL L19747, 150 DML L19757, heap 10/25 MB L19780) and order of execution (before-save L15643, after-save L15673, post-commit asynchronous paths L15692)
- Metadata API Developer Guide 264 — FlowStart triggerType (L75261-75269), FlowScheduledPath pathType (L74148-74151), FlowRecordLookup queriedFields (L73623-73625)
- Salesforce Architects — Performance Engineering: https://architect.salesforce.com/
