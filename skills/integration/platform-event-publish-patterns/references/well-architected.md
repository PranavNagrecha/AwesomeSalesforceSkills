# Well-Architected Notes — Platform Event Publish Patterns

## Relevant Pillars

Platform Event publishing sits between Salesforce's transactional
boundary and the world outside. The architectural weight is mostly
in Reliability (does the event reach subscribers?) and
Operational Excellence (can ops debug failures?). Performance and
scalability matter at high volume; security applies in narrower
ways.

- **Reliability** — Platform Events are at-most-once by default —
  `EventBus.publish` returns a `SaveResult` per event, and a
  `SaveResult` failure is permanent unless the caller retries.
  Designing for reliability here means deciding up-front whether
  the event's semantics tolerate loss (telemetry: usually yes;
  business event: usually no) and pairing the publisher with
  an outbox pattern when loss is unacceptable.
- **Operational Excellence** — Publish failures are silent unless
  you log them. The default code path is:
  `EventBus.publish(events);` without inspecting the result.
  Production-grade publishers always log failure
  (`SaveResult.getErrors()[0].getMessage()`), track the event-
  allocation budget weekly, and surface a "publish failure rate"
  metric to dashboards.
- **Scalability** — High-volume publishes burn event allocation —
  the org's monthly budget is finite and license-dependent. A
  single mis-built publisher (one that fires on every save instead
  of just transitions) can exhaust the allocation in days. Capacity
  planning is a real architectural concern.
- **Security** — Platform Events bypass record-level FLS — anyone
  with subscribe permission on the event sees the payload regardless
  of their CRUD on the underlying records. PII-sensitive payloads
  must be designed around this (see Tradeoff 2 below).

## Architectural Tradeoffs

The defining tradeoff is **PublishBehavior** —
`PublishAfterCommit` vs `PublishImmediately`:

| Dimension | `PublishAfterCommit` (default) | `PublishImmediately` |
|---|---|---|
| Fires on rollback | No | Yes |
| Subscriber sees committed state | Yes | Sometimes — race window |
| Best for | Business events (order submitted, case escalated) | Telemetry, audit, fire-and-forget |
| Cost on failure | Both DML AND event rollback | Event consumed even if DML failed |
| Test ergonomics | Requires `Test.getEventBus().deliver()` | Same |

The naive default is "use PublishAfterCommit for safety," and it's
the right choice ~90% of the time. The exceptions: audit-trail
events (must fire so the audit log shows the *attempt* even if the
DML rolled back), system-health telemetry (must reach the
monitoring system even on transaction failure).

A second tradeoff is **payload size vs subscriber lookup cost**:

| Approach | Pros | Cons |
|---|---|---|
| Minimal payload (just IDs) | Small, fast, low storage | Every subscriber must do its own lookup; race window with `PublishImmediately` |
| Full payload (all fields subscribers need) | Subscribers self-contained; no race | Larger event size; storage cost; payload may include sensitive data |
| Hybrid (key fields + ID) | Common subscribers self-contained; rare subscribers can lookup | Versioning complexity |

For a high-fanout event (many subscribers), full payload often
wins — saves N lookup queries across N subscribers. For a single-
subscriber event, minimal payload is fine. For sensitive data
(PII, financial), the calculus is different: don't put it in the
payload at all (Platform Events bypass record-level FLS); put
just the record ID and require the subscriber to re-fetch with
its own context permissions.

A third tradeoff: **direct publish vs outbox pattern**. Direct
publish is fast and simple but at-most-once. Outbox is slower
(events buffered for seconds-to-minutes by the drain job) and
more code but gives at-least-once delivery with bounded retries.
The right call depends on the business impact of a lost event:
- **Lost telemetry / non-critical signal**: direct publish, log
  failures, move on.
- **Lost business event** (welcome email, invoice generation,
  status sync): outbox pattern. The extra latency is the price of
  durability.
- **Lost regulatory / audit event**: outbox with extended retry
  AND a dead-letter alert that pages oncall.

A fourth tradeoff: **Platform Event vs Change Data Capture (CDC)**.
Both deliver "something changed" notifications to subscribers; the
mechanism is different. PE is publisher-emitted with custom payload
shape; CDC is platform-emitted from SObject changes with a fixed
shape. Use PE when:
- The event maps to a business action, not a row change (e.g.,
  "OrderSubmitted" is a state transition that's hard to derive from
  row diffs alone)
- Subscribers need a custom payload shape
- Bidirectional integration is involved (PE can be published from
  external systems too; CDC can't)

Use CDC when:
- Subscribers care about all changes to an SObject, not a
  specific business event
- Implementing a real-time data sync to an external data lake
- The team doesn't want to maintain custom event metadata

## Anti-Patterns

1. **`EventBus.publish` inside a loop.** Burns DML budget per
   call, not per event. Always batch into a list.
2. **Publishing from `@future`** to "ensure delivery." Wrong tool
   — see `examples.md` anti-pattern.
3. **Ignoring `Database.SaveResult` failures.** A failed publish
   is silent unless you check. Always inspect and log/retry.
4. **Cluttering events with sensitive PII.** Events bypass
   record-level FLS. Put IDs only; let subscribers fetch with
   context permissions.
5. **No event versioning.** Subscribers can't tell whether the
   payload schema changed. Always include a `Schema_Version__c`
   field and bump it on breaking changes — subscribers can
   then version-handle.
6. **No allocation monitoring.** Monthly allocation can be
   exhausted mid-cycle; recovery requires a Salesforce support
   ticket. Track usage weekly via Setup → Platform Events →
   Event Delivery Usage.

## Official Sources Used

- Apex Developer Guide — Publishing Platform Events:
  https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_publish.htm
- Apex Developer Guide — `EventBus.publish`:
  https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_EventBus.htm
- Platform Events Developer Guide — `PublishBehavior` metadata:
  https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_define.htm
- Apex Developer Guide — `Test.getEventBus()`:
  https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_Test.htm
- Salesforce Integration Patterns — Publish/Subscribe:
  https://architect.salesforce.com/fundamentals/integration-patterns-and-practices/integration-patterns
- Salesforce Well-Architected — Adaptable (Event-Driven):
  https://architect.salesforce.com/well-architected/adaptable/event-driven
