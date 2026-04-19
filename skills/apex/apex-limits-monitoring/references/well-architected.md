# Well-Architected Notes — Apex Limits Monitoring

## Relevant Pillars

- **Reliability** — Governor limits are the primary reliability constraint in Apex. A transaction that exceeds any limit fails entirely and rolls back all work. Defensive coding with guard clauses and re-queue patterns ensures that partial progress is preserved and work can be resumed rather than lost. The `System.LimitException` is uncatchable, making prevention the only reliability strategy.
- **Performance Efficiency** — Monitoring actual limit consumption (via `Limits.getX()` methods) and logging headroom percentages provides the observability needed to tune batch scope sizes, identify hot code paths, and right-size asynchronous work. Without this visibility, performance problems surface only as production failures.

## Architectural Tradeoffs

**Guard clause granularity vs code verbosity:** Adding a guard clause before every SOQL and DML call produces highly defensive code at the cost of verbosity. The tradeoff is acceptable in service-layer classes used from triggers (high-risk context) but may be over-engineered for isolated, single-purpose utility classes with predictable limit consumption. The recommended approach is to guard any code path that is called from a variable-volume context (trigger handler, batch execute, Queueable execute) and skip guards for isolated test-only or single-invocation utility methods.

**Re-queue strategy vs batch splitting:** When a Queueable job approaches its CPU limit mid-execution, it can either (a) re-queue itself with the remaining work (cursor-based re-queue) or (b) be redesigned as Batch Apex with a smaller scope. Re-queue is operationally simpler but consumes Queueable chain depth (max 5 levels in sync context, unlimited in async). Batch Apex provides built-in chunking and retry but requires job design changes. Use the `standards/decision-trees/async-selection.md` tree to select the right mechanism.

**Batch scope size vs job count tradeoff:** A smaller scope size increases the number of batch executions (each execution counts against asynchronous Apex job limits and adds overhead). A larger scope risks hitting limits within a single execution. The correct scope is the largest value where per-execution limit consumption stays below 80% of the ceiling for the binding constraint (usually SOQL or CPU). Document the calculation in the class header so it can be re-validated when the execute logic changes.

## Anti-Patterns

1. **Trying to catch `System.LimitException`** — Adding `try/catch (System.LimitException e)` around expensive operations creates a false sense of safety. The exception is uncatchable; the catch block never executes on a real breach. The correct pattern is prevention via guard clauses, not exception handling.

2. **Hardcoding limit ceilings** — Writing `if (Limits.getQueries() > 90)` (hardcoded constant) instead of `if ((Limits.getLimitQueries() - Limits.getQueries()) < 10)` makes the code fragile. The correct ceiling changes between sync and async contexts, and it may change between Salesforce releases. Always derive the ceiling from `Limits.getLimitX()` at runtime.

3. **Checking limits only at method entry** — A guard clause at the top of a method that calls multiple SOQL queries inside a loop only validates headroom for the first query. Limit consumption compounds inside the method. Guard clauses must be placed immediately before each expensive operation, or checked incrementally inside the loop.

## Official Sources Used

- Apex Reference Guide — Limits Class: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_limits.htm
- Apex Developer Guide — Execution Governors and Limits: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Apex Developer Guide — Running Apex within Governor Execution Limits: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_limits_tips.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
