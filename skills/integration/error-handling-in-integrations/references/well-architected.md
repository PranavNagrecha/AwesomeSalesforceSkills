# Well-Architected Notes — Error Handling In Integrations

## Relevant Pillars

- **Reliability** — Integration error handling is the foundation of reliable integration architecture; silent failures cause invisible data drift that surfaces only in customer complaints.
- **Operational Excellence** — DLQ visibility, Replay ID tracking, and cross-channel notifications are operational tools that enable recovery from failures without data loss.
- **Security** — Error payloads may contain sensitive data; DLQ records must apply field-level security; error notification channels (Slack, email) should not expose full payload content.
- **Performance** — Circuit breakers prevent API limit exhaustion during external system downtime; without them a single failing external endpoint can exhaust Salesforce API limits for all integrations.
- **Scalability** — DLQ retry jobs must be designed for high volumes; a single large failure event should not cause DLQ retry jobs to exceed governor limits.

## Architectural Tradeoffs

**RetryableException vs DLQ:** RetryableException provides automatic platform retries but suspends the trigger after 9 failures. DLQ writes failures to a persistent store for manual or automated retry with full control. Permanent errors must use DLQ; transient errors should use RetryableException.

**Centralized vs per-integration DLQ:** A single DLQ object (Integration_DLQ__c) for all integration types is simpler to monitor but produces a mixed queue. Per-integration DLQ objects provide cleaner separation but require more monitoring dashboards. Teams with many integrations should centralize.

**Circuit breaker threshold:** A low threshold (3 failures) opens the circuit quickly and protects Salesforce API limits but may cause false positives on intermittent external errors. A high threshold (10 failures) tolerates more errors but may allow API limit exhaustion before opening.

## Anti-Patterns

1. **RetryableException on permanent errors** — Causes trigger suspension after 9 wasted retries, blocking all event processing on that channel.

2. **Silent failure discard** — Catching exceptions and logging to debug without DLQ persistence causes permanent data loss with no recovery path.

3. **No ops notification** — Failures accumulate in DLQ but no one is notified; the integration runs silently broken for days or weeks.

## Official Sources Used

- Platform Events Developer Guide — Retry Event Triggers with EventBus.RetryableException — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_retry_trigger.htm
- Salesforce Integration Patterns and Practices — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

## Cross-Skill References

- `integration/retry-and-backoff-patterns` — HTTP retry backoff
- `integration/api-error-handling-design` — HTTP error response contracts
- `admin/integration-pattern-selection` — upstream pattern selection
