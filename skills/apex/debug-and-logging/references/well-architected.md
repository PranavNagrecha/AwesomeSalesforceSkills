# Well-Architected Notes — Debug And Logging

## Relevant Pillars

### Operational Excellence

This skill is primarily about making Apex supportable. Teams cannot operate what they cannot observe.

Tag findings as Operational Excellence when:
- failures leave no durable record
- debug output is noisy or unstructured
- async processes cannot be traced from business action to job failure

### Reliability

Observability supports reliable systems because silent failures and opaque async behavior delay remediation.

Tag findings as Reliability when:
- exceptions are swallowed with only debug output
- support cannot distinguish transient versus systemic failures
- batch or queueable processing lacks failure visibility

## Architectural Tradeoffs

- **Rich logs vs minimal logs:** more detail helps diagnosis until it overwhelms support or leaks data.
- **Debug logs vs structured logs:** debug logs are fast to add; structured logs are what production support needs.
- **Central logger vs ad hoc logging:** centralization adds discipline and correlation, but only if teams use it consistently.

## Anti-Patterns

1. **Production observability built on `System.debug`** — transient and weak.
2. **Secret-bearing logs** — useful in the moment, harmful in operation.
3. **No async correlation** — async failures become disconnected from business impact.

## Official Sources Used

- Apex Developer Guide — debug logs and runtime debugging guidance
- Apex Reference Guide — `System.debug` and logging-level behavior
- Salesforce Well-Architected Overview — operational excellence and reliability framing
