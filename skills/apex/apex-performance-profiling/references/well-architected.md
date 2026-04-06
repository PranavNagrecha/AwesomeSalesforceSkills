# Well-Architected Notes -- Apex Performance Profiling

## Relevant Pillars

- **Performance** -- This skill is fundamentally about finding performance bottlenecks. Profiling enables evidence-based optimization rather than guessing. The flame graph and Query Plan tools directly support the Well-Architected performance principle of measuring before optimizing.
- **Operational Excellence** -- Establishing profiling discipline and permanent instrumentation supports ongoing operational health. Teams that profile proactively catch regressions before users report them. Limits checkpoint instrumentation left in code serves as built-in observability.
- **Scalability** -- Profiling reveals whether a transaction's cost grows linearly or quadratically with data volume. Identifying O(n^2) patterns early prevents scalability failures as orgs grow.
- **Reliability** -- CPU time limit failures and SOQL query timeouts are reliability problems. Profiling reduces mean time to root cause, improving incident response and reducing production downtime.

## Architectural Tradeoffs

### Flame Graph Depth vs. Log Truncation

Capturing a flame graph at maximum fidelity (FINEST level for all categories) produces the most detailed call tree but risks log truncation at the 20 MB limit. The tradeoff is between diagnostic completeness and log integrity. The recommended approach is to use FINEST only for Apex Code and Database, reducing other categories to ERROR.

### Permanent Instrumentation vs. Clean Code

Leaving `Limits.getCpuTime()` checkpoints in production code provides ongoing performance visibility but adds lines that are not business logic. The tradeoff favors instrumentation for business-critical transaction paths (order processing, payment flows, integration endpoints) and removing it for low-risk utility code.

### Production Profiling vs. Sandbox Fidelity

Profiling in production captures real data volumes and real managed package behavior but adds overhead and risk. Profiling in sandbox is safe but may miss production-only bottlenecks (data skew, custom indexes, sharing rules). Use production Limits checkpoints with WARN-level logging for critical paths and save FINEST-level profiling for sandbox or full-copy sandbox.

## Anti-Patterns

1. **Optimizing without profiling** -- Making code changes based on intuition about where the bottleneck is. This wastes effort on fast code and misses the actual hotspot. Always profile first, then optimize the identified bottleneck, then re-measure.
2. **Profiling once and assuming stability** -- Treating a single profiling session as permanent truth. Performance characteristics change as data volume grows, new automation is added, and managed packages are updated. Establish periodic profiling checkpoints or permanent instrumentation.
3. **Using wall-clock time as the primary metric** -- Measuring elapsed time instead of CPU time, SOQL count, and DML count separately. Wall-clock time conflates Apex compute, database, callout wait, and platform overhead into a single number that cannot guide targeted optimization.

## Official Sources Used

- Apex Developer Guide -- Execution Governors and Limits: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Apex Developer Guide -- Apex Debugging: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_debugging.htm
- Apex Reference Guide -- Limits Class: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_limits.htm
- Salesforce Well-Architected -- Performance: https://architect.salesforce.com/well-architected/performant
- SOQL and SOSL Reference -- Query Plan Tool: https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_query_plan.htm
