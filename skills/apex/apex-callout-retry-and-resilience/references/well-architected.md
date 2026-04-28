# Well-Architected — Apex Callout Retry and Resilience

## Pillars Addressed

### Reliability

Resilient callouts directly serve the Reliability pillar by:

- **Tolerating transient failures** without surfacing errors to end users or losing data
- **Limiting blast radius** via per-endpoint circuit breakers — one degraded partner doesn't take down all integrations
- **Guaranteeing eventual delivery** via the dead-letter pattern + reprocessing path
- **Bounding worst-case latency** via timeouts and attempt caps

The single biggest reliability win: a `Failed_Callout__c` row exists for every exhausted retry. Without it, failures vanish into logs and the business loses revenue silently.

### Operational Excellence

The pattern serves Operational Excellence by making integration health observable and tuneable:

- Custom Metadata-driven config (`Callout_Resilience_Config__mdt`) lets ops adjust thresholds without deploys
- Dead-letter volume per endpoint is a leading indicator of partner degradation
- Circuit-breaker state changes are loggable events, feeding dashboards
- Idempotency keys make incident replay safe

## Anti-Patterns That Violate These Pillars

| Anti-pattern | Pillar violated | Why |
|---|---|---|
| Unbounded `while (!success) { retry; }` | Reliability + perf | Burns 100-callout limit; can hang the transaction |
| Retrying 4xx | Reliability | Wastes budget; hides real bugs |
| One global circuit breaker | Reliability | Bad endpoint A blackholes endpoint B |
| Hard-coded thresholds in Apex | Operational Excellence | Ops can't tune without a deploy |
| No dead letter | Reliability | Failures vanish silently |
| Sync `Thread.sleep`-style loop | Reliability + perf | Apex has no sleep; busy-wait blows CPU limit |

## Decision Tree Linkage

When choosing between retry-in-place vs queueable chain vs Platform Event:

- See `standards/decision-trees/async-selection.md` — Queueable for chained retry with state; Platform Event for fan-out or cross-org delivery
- See `standards/decision-trees/integration-pattern-selection.md` — if the failure rate is structural (not transient), the right answer may be Salesforce Connect or middleware, not retries

## Official Sources Used

- **Apex Developer Guide — HttpRequest** — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_HttpRequest.htm — authoritative on `setTimeout`, allowed methods, header semantics, and the 120-second cumulative callout cap.
- **Apex Developer Guide — Limits Class** — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_limits.htm — authoritative on `getCallouts()` / `getLimitCallouts()` (100 per transaction) and the per-transaction governor scope.
- **Apex Developer Guide — Testing HTTP Callouts** — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_test.htm — authoritative on `Test.setMock` and `HttpCalloutMock`.
- **Salesforce Architects — Build Reliable Integrations** — https://architect.salesforce.com/well-architected/trusted/reliable — authoritative on the Reliability pillar, idempotency, retries, circuit breakers, and dead-letter patterns in Salesforce-context integrations.
- **Apex Developer Guide — Platform Cache** — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/cache_namespace_overview.htm — authoritative on `Cache.Org` partitions, TTLs, and key semantics used by the circuit-breaker store.
