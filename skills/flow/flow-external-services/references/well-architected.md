# Well-Architected Notes — Flow External Services

## Relevant Pillars

- **Security** — Every callout must use a Named Credential backed by an External Credential. Hard-coded URLs, API keys in flow variables, or credentials in Custom Settings violate the Trusted pillar. External Credential principals with Permission Set gating ensure only authorized users and processes can initiate callouts.
- **Reliability** — Fault connectors are mandatory on every callout action. Network failures, timeouts, and server errors must be explicitly handled. HTTP Callout actions require an additional Decision element checking the status code because they do not fault on 4xx/5xx. Without explicit error routing, callout flows fail silently or expose raw platform errors to users.
- **Operational Excellence** — Fault paths should log `$Flow.FaultMessage` to a custom log object or send an admin notification rather than swallowing errors. External Service spec versions should be tracked so API contract changes are visible. Deployment runbooks must document that Named Credential secrets require manual re-entry in each environment — they are not carried by metadata deployment.
- **Performance** — Synchronous callouts from Flow are subject to the same governor limits as Apex: 100 callouts per transaction, 120-second timeout per callout. High-volume or batch contexts must use Queueable or Batch Apex instead of Flow callouts. Record-triggered flows require async dispatch (Platform Events, scheduled paths) to avoid the uncommitted-work restriction.
- **Adaptability** — External Services spec-versioning allows API contract evolution without immediately breaking existing flows. Designing Named Credentials as a configuration layer (separate from the flow logic) means endpoint changes require only credential updates rather than flow redeployment.

---

## Architectural Tradeoffs

**External Services vs HTTP Callout Action:** External Services offers typed, spec-validated actions with compile-time field checking in Flow Builder. The tradeoff is spec maintenance overhead — every API update requires re-importing the spec and potentially updating action references in all dependent flows. HTTP Callout action is simpler to configure with no spec required, but produces untyped string responses that require manual parsing, and has no build-time validation of input/output fields.

**Flow callouts vs Apex callouts:** Flow External Services is appropriate when there is no custom business logic around the HTTP request itself (no retry logic, no complex conditional routing of the raw response, no callout-inside-a-loop pattern). Apex is appropriate when the callout is part of a larger transaction that requires precise control, when bulk context demands list-safe batch processing, or when the response requires algorithmic parsing. The two approaches are not mutually exclusive — a common pattern uses a lightweight `@InvocableMethod` for JSON parsing while keeping the callout and flow orchestration in Flow Builder.

**Sync vs async for record-triggered contexts:** Salesforce prohibits synchronous callouts in record-triggered transactions. This is a platform enforcement, not a guideline. Any integration requirement that originates from a record save must use async dispatch. Platform Events are the cleanest dispatch mechanism because they are transactional (published only on commit) and decouple the record-triggered logic from the integration logic.

---

## Anti-Patterns

1. **Callout in a record-triggered flow without async dispatch** — Results in a runtime `CalloutException` and transaction rollback. Pattern: always use Platform Events or scheduled paths to push callout work outside the save transaction.

2. **Fault connector wired but no status code check on HTTP Callout actions** — Creates a false sense of error coverage. The fault connector handles network errors; a 500 from the server goes undetected. Pattern: always add a Decision element checking `Response_Status_Code >= 400` after every HTTP Callout action.

3. **Credentials stored outside Named Credentials** — Storing API keys in Flow variables, Custom Settings, Custom Metadata, or Custom Labels makes them readable via SOQL or the Metadata API. Named Credential vault storage is the only safe mechanism.

---

## Official Sources Used

- Salesforce Well-Architected Overview — architecture quality framing (Trusted, Reliable, Easy, Adaptable pillars)
  URL: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Integration Patterns — synchronous vs asynchronous integration decision guidance, callout patterns
  URL: https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Flow Reference (Help) — Flow element behavior, fault connector semantics, callout restrictions
  URL: https://help.salesforce.com/s/articleView?id=sf.flow_ref.htm&type=5
- Flow Builder (Help) — External Services registration, HTTP Callout action, Named Credential selection
  URL: https://help.salesforce.com/s/articleView?id=sf.flow.htm&type=5
- Named Credentials Help — External Credential principal types, permission set assignment, deployment behavior
  URL: https://help.salesforce.com/s/articleView?id=sf.named_credentials_about.htm&type=5
- External Services Developer Guide — OpenAPI spec registration, supported schema features, generated action types
  URL: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/external_services.htm
