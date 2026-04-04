# Well-Architected Notes — Auto-Launched Flow Patterns

## Relevant Pillars

- **Reliability** — Auto-launched Flows are a primary reliability concern because invocation failures (unhandled faults, governor limit breaches, variable mapping errors) can silently corrupt data or roll back entire transactions. The skill's fault-path requirements, exception handling patterns, and governor limit budgeting directly address reliability.

- **Operational Excellence** — Auto-launched Flows invoked from Apex or external systems are harder to observe than record-triggered Flows because they have no built-in UI, no Process Builder equivalent audit trail, and failures surface only if fault paths are instrumented. The skill's guidance on logging `{!$Flow.FaultMessage}`, creating error log records, and naming conventions for variable traceability addresses operational observability.

- **Security** — REST API invocations require OAuth access tokens with the `api` scope and "Run Flows" user permission. The running user's object-level permissions govern what DML the Flow can perform. Overly broad integration user permissions are a common security gap. Platform Event-triggered Flows run as the Automated Process user, not the event publisher — this affects what records the Flow can access.

- **Performance** — Shared governor limits between the calling Apex transaction and the Flow are the primary performance concern. A Flow that issues SOQL queries inside a trigger's bulk context can multiply query counts by the batch size. Collection-variable patterns and asynchronous Platform Event invocations are the performance mitigations.

- **Scalability** — Collection input variables (single `start()` call for a batch) and async Platform Event invocations are the two patterns that allow auto-launched Flows to scale to bulk data loads and high-throughput integrations. Single-record-per-invocation patterns do not scale.

---

## Architectural Tradeoffs

**Synchronous Apex invocation vs. async Platform Event:**
- Synchronous via `Flow.Interview` gives the caller immediate output (case ID, discount value, routing result) but shares governor limits and causes the caller to fail if the Flow faults.
- Async via Platform Event decouples the publisher from the Flow, resets governor limits, and isolates failures — but the publisher cannot receive output values from the Flow. Choose based on whether the caller needs a synchronous return value.

**Flow-managed logic vs. Apex-managed logic:**
- Auto-launched Flows allow business analysts to modify routing, pricing, and validation rules without a code deployment. The tradeoff is reduced testability (Flow tests via `Test.startTest/stopTest` cover fewer edge cases than Apex unit tests) and reduced type safety (variable mapping errors surface at runtime, not compile time).
- Prefer auto-launched Flows for logic that changes frequently and is owned by non-developers. Prefer Apex for logic that must be tested exhaustively or that requires complex data structures.

**REST Flows resource vs. custom Apex REST endpoint:**
- The standard `/actions/custom/flow/<ApiName>` endpoint requires no custom Apex. It handles auth, serialization, and error wrapping automatically. The tradeoff is less control over the response shape and no ability to add custom HTTP headers.
- Use the standard REST Flows resource for straightforward invocations. Use a custom Apex REST endpoint only when the integration requires non-standard response formatting, streaming, or conditional authentication logic.

---

## Anti-Patterns

1. **Calling `Flow.Interview.start()` inside a for-loop** — This multiplies the Flow's internal SOQL and DML by the record count. In a bulk trigger context this reliably causes `System.LimitException`. The correct pattern is to pass a collection variable and call `start()` once. See `references/examples.md` for the correct implementation.

2. **No Fault connectors on DML elements** — A Flow with unhandled faults propagates as `System.FlowException` through the Apex caller and rolls back the entire transaction. Users receive a cryptic error and no audit trail. Every DML and external-call element must have a Fault path that logs `{!$Flow.FaultMessage}` and terminates gracefully.

3. **Storing Flow API names as inline string literals scattered across Apex classes** — When a Flow is renamed, all inline literals go stale with no compile-time error. Centralise Flow API name constants in a dedicated `FlowConstants` class and reference that class from all callers. This makes renames a single-file change detectable in code review.

4. **Using Platform Event-triggered Flows for logic that requires synchronous return values** — Platform Event delivery is asynchronous and the publisher cannot read Flow output variables. Using events for logic that the publisher needs to act on immediately forces awkward polling or callback patterns. Use `Flow.Interview` for synchronous needs and Platform Events only for fire-and-forget async processing.

---

## Official Sources Used

- Apex Developer Guide — `Flow.Interview` Class: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_class_Flow_Interview.htm
- REST API Developer Guide — Flows Resource: https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_process_flow.htm
- Flow Reference — Start Element (trigger types including Platform Event): https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_start.htm
- Flow Reference (general): https://help.salesforce.com/s/articleView?id=sf.flow_ref.htm&type=5
- Flow Builder overview: https://help.salesforce.com/s/articleView?id=sf.flow.htm&type=5
- Salesforce Well-Architected Framework — Reliability pillar: https://architect.salesforce.com/well-architected/reliable
- Salesforce Well-Architected Framework — Operational Excellence pillar: https://architect.salesforce.com/well-architected/operational-excellence
