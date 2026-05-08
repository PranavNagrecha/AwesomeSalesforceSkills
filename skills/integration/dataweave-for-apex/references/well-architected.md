# Well-Architected Notes — DataWeave for Apex

## Relevant Pillars

- **Performance** — DataWeave runs inside the Apex governor envelope; heap and CPU planning is part of the design, not an afterthought. The choice to use DataWeave vs hand-rolled Apex is largely a performance/maintainability tradeoff.
- **Reliability** — A registered, declarative `.dwl` script is more robust to schema drift than a hand-rolled DOM/Map walker. The Apex code stays small and the change-surface for new fields is one line.

## Architectural Tradeoffs

- **DataWeave-for-Apex vs MuleSoft Anypoint** — When a MuleSoft license already exists, complex transformations belong off-platform: better tooling, no Apex governor limits, and centralized integration governance. DataWeave-for-Apex earns its place when you need a transformation *inside* a Salesforce transaction (trigger, Queueable, REST class) and pulling MuleSoft into the call path adds unacceptable latency or operational cost.
- **DataWeave-for-Apex vs hand-rolled Apex** — Use DataWeave when field count >15 or the source has nested arrays, attribute-vs-element XML quirks, or "one or many" repeats. Use hand-rolled Apex for trivial reshapes where the script registration and call overhead exceed the maintainability gain.
- **In-line vs registered scripts** — Apex only supports registered (static-resource) scripts. The tradeoff is "more files for the smallest transform" vs "single source of truth for the spec." On any transformation that will be called from more than one place, the registered script wins by default.

## Anti-Patterns

1. **Treating DataWeave as a license-free MuleSoft replacement** — The transformation language is the same; the runtime, deployment model, and operational guarantees are not. Don't migrate orchestration / connector / SLA-bound integrations from MuleSoft into Apex DataWeave wholesale.
2. **Ignoring static-resource cache control** — A `Private` cache control on the `.dwl` resource forces re-parse per call. Performance dies under load and the root cause is invisible without profiling.
3. **Catching `Dataweave.ExecuteException` and discarding the message** — The platform's diagnostic detail is in the message; collapsing to a generic exception with no log line is the difference between a 5-minute fix and a 5-day incident.

## Official Sources Used

- Apex Reference Guide — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm — `Dataweave.Script`, `Dataweave.Result`, `Dataweave.ExecuteException`, `Dataweave.ScriptException`.
- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm — DataWeave-for-Apex section, governor-limit interactions.
- Integration Patterns — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html — when to transform on-platform vs off-platform.
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html — Performance and Reliability framing.
