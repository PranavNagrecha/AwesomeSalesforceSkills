# Well-Architected Notes — OmniStudio Remote Actions

## Relevant Pillars

- **Reliability** — Remote Actions are the bridge between the client-side OmniScript and server-side logic. Misconfigured invoke modes, unhandled error responses, or missing timeout handling cause silent failures that the user cannot recover from. Reliability demands that every action has explicit error handling and that invoke mode matches the data dependency graph.

- **Security** — Remote Actions control what data leaves the client and reaches the server. Unscoped Send JSON Paths leak PII to backends that should not receive it. Apex classes without `with sharing` bypass record-level security. Named Credentials must be used for all external callouts to prevent credential exposure in source control or logs.

- **Performance** — Each Remote Action is a server round-trip. Unnecessary actions, overly broad Send JSON Paths (large payloads), and synchronous callouts to slow external systems degrade the user experience. Action consolidation, scoped payloads, and Continuation patterns are the primary performance levers.

## Architectural Tradeoffs

### IP Action vs Apex Remote Action

Integration Procedure Actions are declarative, auditable, and support built-in error handling per step. They are the default choice for orchestration. However, they add serialization overhead and are harder to unit test than Apex. For single, complex operations where Apex unit testing and governor control matter more than declarative auditability, Apex Remote Actions are preferred.

### Promise vs Fire and Forget

Promise mode guarantees data availability but blocks the UI. Fire and Forget mode improves perceived performance but risks data loss. The tradeoff is strict: if any downstream step reads the action's output, Promise is mandatory. Fire and Forget is safe only for true side effects (logging, analytics, audit writes) where data loss is acceptable.

### Scoped vs Full JSON Payload

Sending the full OmniScript JSON is simpler to configure but violates least-privilege, increases payload size, and couples the backend to the OmniScript's internal structure. Scoped Send JSON Paths require more upfront design but produce more secure, performant, and maintainable integrations.

## Anti-Patterns

1. **God Action** — A single Remote Action that handles all server-side logic for the entire OmniScript. This creates a monolithic backend, makes error handling coarse-grained, and prevents step-level retry. Break logic into discrete actions aligned to specific steps and concerns.

2. **Hardcoded Endpoints in Apex** — Apex Remote Action classes that contain URLs, API keys, or environment-specific configuration directly in code. This breaks across environments and leaks credentials into version control. Use Named Credentials and Custom Metadata Types for all environment-specific configuration.

3. **Fire and Forget for Critical Data** — Using Fire and Forget invoke mode for actions whose output is displayed to the user or validated in subsequent steps. The perceived performance gain is not worth the intermittent, hard-to-reproduce data loss. Use Promise mode for any data dependency.

## Official Sources Used

- OmniStudio Developer Guide — OmniScript action elements, VlocityOpenInterface2 contract, invoke mode behavior
  https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer_guide.meta/omnistudio_developer_guide/omnistudio_intro.htm
- Salesforce Help: OmniScript Remote Actions — Action type configuration, Send/Response JSON Path
  https://help.salesforce.com/s/articleView?id=sf.os_omniscript_remote_action.htm&type=5
- Salesforce Help: Integration Procedures — IP Action element behavior and error handling
  https://help.salesforce.com/s/articleView?id=sf.os_integration_procedures.htm&type=5
- Salesforce Well-Architected Overview — architecture quality framing for Reliability, Security, Performance pillars
  https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Integration Patterns — synchronous vs asynchronous pattern selection for Remote Action backends
  https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
