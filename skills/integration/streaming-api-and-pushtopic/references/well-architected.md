# Well-Architected Notes — Streaming API and PushTopic

## Relevant Pillars

- **Reliability** — The primary pillar for this skill. Streaming API's 24-hour event retention, CometD session expiry, and connection drop behavior all create failure modes that must be designed around. Replay ID persistence is the core reliability mechanism. Systems that use Streaming API must plan for reconnection, event replay, and gap detection. For availability requirements exceeding the 24-hour retention window, Platform Events is the architecturally correct choice.

- **Operational Excellence** — Channel naming conventions, monitoring for concurrent client limits, and structured reconnection logic are operational concerns. Durable replay ID storage (e.g., a database rather than an in-memory variable) enables operators to recover from outages without manual intervention. CometD connection health should be surfaced as a metric; silent `401` failures are a common source of invisible production degradation.

- **Security** — The CometD session is tied to an OAuth access token. Short-lived tokens (2-hour default) mean the client must implement token refresh or continuous re-authentication. Long-lived session tokens reduce re-auth overhead but increase the blast radius of credential theft. The Connected App session policy must be set to match the operational model of the subscriber (daemon vs. interactive). Avoid storing OAuth credentials in plaintext; use a secrets manager or the OS keychain.

- **Performance** — `NotifyForFields = All` fires a streaming event on every field change to a matching record, including non-functional system fields (LastModifiedDate, SystemModstamp). `Referenced` limits events to fields that appear in the SELECT or WHERE, which reduces noise and payload size. Avoid overly broad PushTopic queries (no WHERE filter) on high-volume objects like Task or Event.

- **Scalability** — The 100 simultaneous clients per channel and 1,000 org-wide limits constrain horizontal scaling of streaming subscribers. Fan-out architectures (one Salesforce subscriber relays events to internal consumers via a message bus like Kafka or SQS) scale better than many direct CometD connections. For very high event volumes, the Pub/Sub API (gRPC) offers higher throughput than Streaming API.

## Architectural Tradeoffs

**PushTopic vs. Platform Events:** PushTopic requires no Apex code and directly tracks sObject record changes. Platform Events require explicit `EventBus.publish()` calls in Apex but offer 72-hour retention, defined schema, and higher throughput. For new architectures, Platform Events are generally preferred; PushTopic is appropriate for lightweight, existing-object-change notification scenarios where adding Apex is undesirable.

**Replay ID persistence strategy — before vs. after processing:** Saving the replay ID before processing the event guarantees at-most-once data loss but risks duplicate processing if the process crashes after saving but before processing. Saving after processing guarantees at-most-once duplicate processing but risks missed events. Choose based on downstream idempotency capabilities. Most data warehouse sinks support upsert by record ID, making "save before, upsert downstream" the correct default.

**Generic Streaming vs. Platform Events for custom payloads:** Generic Streaming requires no schema definition and is simpler to set up. Platform Events have a defined schema, are visible in Salesforce event logs, support high-volume allocations, and integrate with Flow and Process Builder. For anything beyond a simple UI trigger, Platform Events are the more maintainable and observable choice.

## Anti-Patterns

1. **Polling the `/connect` endpoint on a timer instead of immediately re-issuing after each response** — This creates gaps in the long-poll loop that the server interprets as disconnection, causing `clientId` invalidation and missed events. The long-poll is not a batch job; it is a continuous connection that must be maintained without gaps. See `references/examples.md` for the correct reconnect pattern.

2. **Using `NotifyForFields = All` on high-write objects without a narrow WHERE clause** — On objects like Task, ActivityHistory, or high-frequency custom objects, this generates a streaming event on every single DML operation regardless of business relevance. This burns streaming API allocations and overwhelms subscribers with noise, potentially causing them to fall behind and lose events to the 24-hour expiry. Always use `NotifyForFields = Referenced` and add a discriminating WHERE clause to the PushTopic SOQL.

3. **Opening one CometD connection per subscriber thread instead of multiplexing subscriptions on a shared connection** — Each CometD connection counts as one concurrent client against the 100-per-channel and 1,000-org-wide limits. Services that spawn a new connection per event type, per user, or per thread will hit the limit rapidly. The correct architecture is one CometD connection per application instance with multiple subscriptions registered on it.

## Official Sources Used

- Streaming API Developer Guide (Introduction) — https://developer.salesforce.com/docs/atlas.en-us.api_streaming.meta/api_streaming/intro_stream.htm
- Streaming API Developer Guide (Defining PushTopics) — https://developer.salesforce.com/docs/atlas.en-us.api_streaming.meta/api_streaming/pushtopic_define.htm
- Streaming API Developer Guide (PushTopic SOQL Restrictions) — https://developer.salesforce.com/docs/atlas.en-us.api_streaming.meta/api_streaming/pushtopic_soql.htm
- Streaming API Developer Guide (Replay Events) — https://developer.salesforce.com/docs/atlas.en-us.api_streaming.meta/api_streaming/using_streaming_api_durability.htm
- Streaming API Developer Guide (Generic Streaming) — https://developer.salesforce.com/docs/atlas.en-us.api_streaming.meta/api_streaming/create_streaming_channel.htm
- Streaming API Developer Guide (Streaming API Limits) — https://developer.salesforce.com/docs/atlas.en-us.api_streaming.meta/api_streaming/streaming_api_limits.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Integration Patterns and Practices — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
