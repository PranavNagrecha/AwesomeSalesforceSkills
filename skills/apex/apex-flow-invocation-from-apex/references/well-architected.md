# Well-Architected Notes — Apex Flow Invocation From Apex

## Relevant Pillars

### Reliability

Flow invocations from Apex fail at runtime for many reasons (wrong Flow type, missing variable, type mismatch, governor exhaustion). None of these are caught at compile time. Reliable code wraps the invocation in structured error handling and plans for Flow shape changes driven by admins.

Tag findings as Reliability when:
- `start()` is called without try/catch
- Flow API name is hardcoded with no CI check that it exists
- output variable casts have no null check
- no fallback exists when the Flow is unavailable

### Performance

Every Flow interview consumes CPU, SOQL, and DML from the caller's transaction budget. Per-record invocation in a trigger is a reliable way to exhaust the 10-second sync CPU limit on bulk DML.

Tag findings as Performance when:
- `createInterview` is inside a `for`/`while` loop
- a Flow runs inside a trigger without being designed for bulk
- invocation happens in a hot path where inline Apex would be cheaper

### Operational Excellence

The "Apex calls Flow" pattern exists to decouple admin-owned business rules from developer-owned integration code. It succeeds only when admins know they own the Flow; it fails when Apex "borrows" the Flow as a convenient utility the admin didn't know anyone depended on. Documentation and ownership clarity are required.

Tag findings as OpEx when:
- no documentation indicates which Apex classes invoke this Flow
- the Flow's description doesn't note "invoked from Apex"
- no integration test exists for the Apex→Flow contract

## Architectural Tradeoffs

- **Apex-owned logic vs Flow-owned logic:** Flow ownership is the right call when admins need runtime editability without a deploy. Apex is right for complex or performance-sensitive logic.
- **Direct `Flow.Interview` vs Invocable Action:** Direct invocation is simpler; Invocable Action framework adds discovery, parameter metadata, and a cleaner error surface for dynamic selection.
- **Synchronous vs Queueable Flow invocation:** Sync is fine for small Flows. Long-running or record-heavy Flows should be invoked from a Queueable to isolate failures and amortize governor limits.

## Anti-Patterns

1. **Per-record Flow invocation** — multiplies cost and couples failure modes. Always design the Flow to accept collections.
2. **Unhandled `start()`** — runtime failure aborts the caller's DML. Always wrap.
3. **Hardcoded Flow names scattered across Apex** — refactoring or renaming silently breaks callers. Centralize Flow names.

## Official Sources Used

- Apex Reference — Flow Namespace: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_namespace_Flow.htm
- Apex Reference — Flow.Interview: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Flow_Interview.htm
- Flow Builder Guide — Invoke Flows From Apex: https://help.salesforce.com/s/articleView?id=sf.flow_ref_apex.htm
- Flow Types: https://help.salesforce.com/s/articleView?id=sf.flow_concepts_type.htm
- Salesforce Well-Architected — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
