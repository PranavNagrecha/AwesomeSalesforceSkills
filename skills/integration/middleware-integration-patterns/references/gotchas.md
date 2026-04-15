# Gotchas — Middleware Integration Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Platform Events Replay Window Is Not a Middleware Substitute

**What happens:** Teams use Salesforce Platform Events as their integration backbone and assume that external middleware subscribers that go offline and reconnect will automatically catch up on missed events. This works — but only if the reconnection happens within the 72-hour replay window. After 72 hours, Salesforce permanently discards the events. The external subscriber has no way to detect that it missed events; it simply receives no events for the gap period and continues as if nothing occurred.

**When it occurs:** Any integration where the middleware platform (MuleSoft, Boomi) experiences a prolonged outage or scheduled downtime longer than 72 hours. Also triggered by subscriber replay ID mismanagement: if the middleware loses its persisted replay ID (e.g., a cold restart without durable state), it defaults to receiving only new events, silently skipping everything in the gap.

**How to avoid:** Do not treat Platform Events as a durable message store. For integrations that require guaranteed delivery regardless of subscriber outage duration, use a middleware durable queue (MuleSoft JMS, Boomi Atom Queue) as the authoritative store. The middleware subscribes to the Platform Event and immediately writes to its own queue; downstream processing reads from the queue, not from the Salesforce event bus directly. Also ensure the middleware persists the Pub/Sub API replay ID in durable storage that survives restarts.

---

## Gotcha 2: Workato Real-Time Trigger Is a 5-Minute Poll, Not a Push Subscription

**What happens:** Workato markets its Salesforce connector as supporting "real-time triggers." In practice, the Salesforce record-change trigger in Workato polls the Salesforce API at a configurable interval with a minimum of approximately 5 minutes (the exact minimum depends on the Workato plan tier). Recipes configured for "real-time" Salesforce triggers still have an inherent latency of up to 5 minutes for any record change.

**When it occurs:** Any Workato integration that requires sub-5-minute latency for Salesforce record changes. Common examples: fraud detection integrations that must react within seconds, customer-facing order status syncs, SLA-gated case escalations. Teams discover the latency constraint only when business stakeholders report that the integration is "too slow."

**How to avoid:** For sub-5-minute latency requirements, do not use Workato's standard Salesforce trigger. Either (a) configure Workato to receive an inbound webhook from Salesforce (Flow + HTTP callout to a Workato recipe URL) to achieve near-real-time delivery, or (b) choose a different iPaaS that supports native Pub/Sub API subscription (MuleSoft, Boomi). Document the latency constraint explicitly during vendor selection, before recipes are built.

---

## Gotcha 3: Salesforce Governor Limits Fail Hard — There Is No Queue or Backpressure

**What happens:** When Apex code in an integration scenario hits a governor limit (100 callouts per transaction, 10-second synchronous timeout, 6 MB heap), Salesforce does not queue the work or apply backpressure — it throws a `System.LimitException` that rolls back the entire transaction. Any DML already committed in the same transaction is also rolled back. The integration fails completely and silently unless there is explicit exception handling and alerting.

**When it occurs:** Incremental growth of integration complexity is the most common trigger. A trigger that starts with one callout accumulates two more over time as new integrations are added to the same object. The limit is not hit until peak volume (end-of-quarter, migration weekend). In batch context, `Database.executeBatch` and `@future` methods also have callout limits per batch chunk.

**How to avoid:** Model integration architecture so that Apex triggers produce Platform Events and exit immediately; middleware consumes the events asynchronously. This keeps Apex transactions free of callouts entirely, eliminating governor limit risk on the Salesforce side. Never add a second outbound callout to an existing Apex trigger without auditing the total callout count and timeout budget.

---

## Gotcha 4: Transactional Guarantees Require Two-Phase Coordination — Middleware Alone Is Not Enough

**What happens:** Teams implement a middleware integration to handle a cross-system transaction (e.g., create Order in Salesforce + decrement inventory in ERP + send warehouse notification) and assume that because middleware is orchestrating the steps, the transaction is atomic. In reality, most iPaaS platforms (including MuleSoft and Boomi) do not provide distributed two-phase commit across heterogeneous systems. If the ERP update succeeds but the Salesforce write fails, the middleware has no automatic rollback mechanism for the ERP step.

**When it occurs:** Any integration that writes to two or more systems in a single business transaction and assumes all-or-nothing semantics. Common in order management, financial reconciliation, and inventory sync.

**How to avoid:** Design compensating transactions explicitly. When the middleware detects a failure in any step, trigger a compensating action to undo the previously succeeded steps (e.g., ERP order cancellation if Salesforce write fails). Document which steps are compensable and which are not. For integrations that truly require strict atomicity, evaluate whether a saga orchestration pattern or a two-phase commit-capable transactional middleware (rare and expensive) is justified. Per Salesforce Architects guidance, most integrations should be designed for eventual consistency rather than distributed atomicity.

---

## Gotcha 5: Informatica IICS Real-Time Event Support Is Weaker Than Batch ETL

**What happens:** Teams select Informatica IICS for a Salesforce integration based on its strong batch ETL and data quality reputation, then discover that its real-time event processing capabilities (subscribing to Salesforce Platform Events or Pub/Sub API) are significantly less mature than its batch pipeline capabilities. Latency for event-triggered flows in IICS is higher, event replay management is more complex, and the connector documentation for Salesforce streaming APIs is less comprehensive than MuleSoft or Boomi.

**When it occurs:** When the integration architecture requires both real-time event subscription (e.g., Salesforce CDC or Platform Events) and heavy batch data transformation / MDM normalization in the same platform. IICS excels at the latter but is a suboptimal choice for the former.

**How to avoid:** During vendor selection, test real-time event scenarios explicitly against each vendor's Salesforce connector, not only batch throughput. If the integration requires both real-time events and complex data quality / MDM, evaluate a hybrid architecture: MuleSoft or Boomi handles real-time event pipelines, Informatica handles scheduled batch MDM normalization, and the two platforms are connected via a shared message bus or database landing zone.
