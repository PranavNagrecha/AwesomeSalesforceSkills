# Well-Architected Notes — Integration Pattern Selection

## Relevant Pillars

- **Reliability** — Pattern selection directly determines integration failure modes; choosing synchronous for high-latency or high-volume scenarios creates systemic reliability risks.
- **Security** — Pattern selection affects data exposure surface; synchronous callouts require Named Credentials and mTLS considerations; event-driven patterns introduce event replay security considerations.
- **Operational Excellence** — Documented pattern decision records provide the rationale that future maintainers need when changing the integration; undocumented pattern choices create maintenance debt.
- **Performance** — Volume threshold analysis (REST vs Bulk API 2.0) is a performance decision that must be made at pattern selection time.
- **Scalability** — Event-driven patterns (Platform Events, CDC) scale better than synchronous point-to-point for growing volumes; pattern selection is a scalability investment.

## Architectural Tradeoffs

**Synchronous vs Asynchronous:** Synchronous provides immediate confirmation and simpler error handling but creates latency coupling between systems. Asynchronous decouples systems and handles variable latency better but requires more complex error recovery design.

**Point-to-Point vs Event-Driven vs Hub-and-Spoke:** Point-to-point is simplest but creates a web of dependencies. Event-driven decouples producers and consumers. Hub-and-spoke provides centralized visibility but Salesforce cannot be the hub for cross-system transactions.

**Native Salesforce vs Middleware:** Not every integration requires middleware. For simple bidirectional REST API integrations, native Salesforce mechanisms (callouts, REST API, Platform Events) are sufficient. Middleware is required for orchestration, protocol conversion, and cross-system transactions.

## Anti-Patterns

1. **Hub-and-spoke orchestration in Apex** — Apex cannot coordinate cross-system transactions with rollback. Multi-system orchestration with transactional integrity requires middleware.

2. **Synchronous REST for high-volume or high-latency scenarios** — Synchronous callouts have a 120-second timeout and per-transaction call limits. High-volume batch sync must use Bulk API 2.0.

3. **Skipping pattern framework and defaulting to familiarity** — Choosing REST because "we always use REST" or Platform Events because "we want real-time" without applying the two-axis framework leads to mismatched patterns that require costly redesigns.

## Official Sources Used

- `standards/decision-trees/integration-pattern-selection.md` — the canonical routing tree this skill applies: § *Strategic defaults*, Direction 1 Q1–Q4 (Salesforce → external), Direction 2 Q5–Q9 (external → Salesforce), Direction 3 Q10–Q14 (events and replication), § *Pattern summary*, § *Named Credentials — always, not sometimes*, § *Anti-patterns* and § *Security overlays*. Every citation in a decision record resolves to a question in this file.
- Bulk API 2.0 Developer Guide — *Understanding Bulk API 2.0 Ingest*, *Create a Job*, and the three result resources (batching at 10,000 records, the 150,000,000-record daily maximum, 5-minute batch window with up to 20 automatic retries, `externalIdFieldName` required for upsert, `successfulResults` / `failedResults` / `unprocessedrecords`; supports worked decision 1 and gotcha 6): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_asynch.pdf
- Salesforce Developer Limits and Allocations Quick Reference — *Concurrent API Request Limits*, *Total API Request Allocations*, *Limits Specific to Ingest Jobs*, Apex Governor Limits and Static Apex Limits (25 concurrent long-running inbound requests in production, the per-edition 24-hour API formula, 7-day ingest results lifespan, 100 callouts and 120 s cumulative timeout per transaction, 10 s default callout timeout, 6 MB / 12 MB callout size, 150 `EventBus.publish` calls, 2,000 platform-event trigger batch size; supports gotchas 4, 6 and 9 and worked decision 2): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf
- Apex Developer Guide — *Trigger Considerations* and *Working with Data in Apex* (callouts must be made asynchronously from a trigger; `You have uncommitted work pending. Please commit or rollback before calling out.` and `All active Savepoints must be released before making callouts.`; supports gotcha 5): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Metadata API Developer Guide — `NamedCredential`, `ExternalCredential`, `ConnectedApp`, `PlatformEventChannel`, `RemoteSiteSetting`, `CustomObject.publishBehavior` and `ManagedEventSubscription` (the `namedCredentialType` and `authenticationProtocol` enums, file suffixes and API availability, the Spring '26 connected-app creation restriction, the `PublishImmediately` default, and the 72-hour replay window; supports worked decisions 2 and 3, gotchas 7, 9 and 10, and the inventory retrieve): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- REST API Developer Guide — *Status Codes and Error Responses*, *Limits*, *sObject Collections* (HTTP 300 when an external Id matches more than one record, HTTP 403 with `REQUEST_LIMIT_EXCEEDED`, `GET /limits/` returning `DailyApiRequests`, and 200 records per sObject Collections request counting as a single API call; supports gotchas 4 and 8): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_rest.pdf
- Object Reference for the Salesforce Platform — `EventBusSubscriber` (`Status`, `Retries`, `LastProcessed`, `LastPublished`) and `PlatformEventUsageMetric` (`UsageType`, `Client`, `Value`) — supports the verification queries in `references/decision-record-examples.md` and gotcha 7: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Integration Patterns and Practices — Pattern Selection Guide (the six canonical patterns and the integration-type × timing axes in Core Concepts) — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Salesforce Architects Integration Patterns Fundamentals (the distributed-transaction constraint behind gotcha 1) — https://architect.salesforce.com/content/1508/integration-patterns-fundamentals
- Salesforce Well-Architected Overview (the pillar framing above) — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

## Cross-Skill References

- `integration/event-driven-architecture-patterns` — implementation for event-driven pattern
- `architect/api-led-connectivity-architecture` — governance architecture for multi-system integration
- `integration/error-handling-in-integrations` — error recovery for selected pattern
- `integration/bulk-api-2-patterns` — the job lifecycle once the record says `bulk_api_2`
- `integration/named-credentials-setup` — the `auth` block on every record
- `integration/idempotent-integration-patterns` — subscriber-side dedup for the Q12 at-least-once branch
- `admin/api-contract-documentation` — the contract document for the endpoint the chosen pattern exposes
- `admin/process-automation-selection` — the sibling decision skill, when the question is which automation surface owns a rule rather than which integration mechanism moves the data
