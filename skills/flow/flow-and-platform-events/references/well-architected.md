# Well-Architected Notes — Flow and Platform Events

## Relevant Pillars

- **Scalability** — the event bus lets a user-facing transaction finish without
  waiting for downstream work. The constraint that actually binds an internal
  Flow-to-Flow design is the publishing allocation (250,000 per hour on
  Enterprise, Performance, and Unlimited), not the delivery allocation, which
  excludes flows entirely.
- **Reliability** — subscribers are independent failure domains. That is the
  benefit and the hazard: one subscriber failing does not take the others down,
  and equally does not tell anyone it failed.
- **Operational Excellence** — a subscriber runs as Automated Process with no
  user present, so observability has to be built rather than assumed. A
  correlation key on the event is what makes "published but never processed"
  distinguishable from "never published".

## Architectural Tradeoffs

- **Publish After Commit vs Publish Immediately:** After Commit prevents phantom
  events on rollback but spends the shared 150-DML budget; Immediately has its
  own 150-call allocation and delivers even when the transaction rolls back.
  This is a property of the event definition, so a flow author reasoning about
  governor cost has to read a setting that lives somewhere else.
- **Batch size vs drain rate:** a platform-event-triggered flow processes up to
  200 messages per transaction. Lowering the maximum buys governor headroom and
  costs throughput; it moves the cliff rather than removing it. Bulkifying the
  subscriber removes it.
- **Event granularity:** one event per business fact keeps subscribers cheap and
  schemas independent; one fat envelope with a type discriminator wakes every
  subscriber for every message and couples all their schema changes together.
  The per-org definition allocation (50 on Enterprise) is rarely the real
  constraint people fear.
- **Flow subscriber vs Apex subscriber:** a Flow subscriber is admin-owned and
  caps at a 200-message batch; an Apex subscriber defaults to 2,000 and gets
  `EventBus.RetryableException` with a documented ten-execution ceiling. Choosing
  Apex buys retry semantics and costs admin ownership — and a single poison
  message can put the Apex trigger into an error state where it stops consuming
  entirely.
- **Event as durability vs record as durability:** the bus retains high-volume
  messages for 72 hours and Flow cannot replay them. Anything needing recovery
  beyond that window needs a Salesforce record marked processed, which is a
  different design.

## Hygiene

- Every publish sits after the loop, not inside it.
- Every publish element and every subscriber DML has a fault connector.
- Subscriber log rows carry the event's correlation key, not just the interview
  GUID.
- Subscriber flows are bulkified against a 200-message batch, not a single event.
- Error emails for subscriber flows go to a monitored alias.
- No `$Permission` or `$User` gating inside a subscriber.
- Publishing volume is sized against the peak hour, not the daily total.

## Related

- `templates/flow/PlatformEvent_Publisher_Flow.md` — the canonical publisher
  skeleton, including `eventId__c` and the fault path.
- `flow/flow-platform-events-integration` — publish-after-commit semantics,
  subscriber idempotency, and fan-out failure design.
- `flow/flow-bulkification` — the collection patterns a 200-message batch needs.
- `flow/flow-interview-debugging` — instrumenting the invisible subscriber.
- `integration/platform-events-integration` — cross-system pub/sub, Pub/Sub API,
  replay.
- `standards/decision-trees/async-selection.md` — Platform Events vs Queueable vs
  Batch vs Scheduled Flow.
- `standards/decision-trees/integration-pattern-selection.md` — when the event
  bus is the right integration surface at all.

## Official Sources Used

- Platform Event Allocations — publishing 250,000/hour (Enterprise, Performance, Unlimited) and 50,000/hour (Developer); delivery 50,000 / 25,000 / 10,000 per 24 hours and explicitly not applicable to Apex triggers, flows, or Process Builder; 1 MB max message; 72-hour retention; 4,000 total / 2,000 active flow subscriptions per event; 100 / 50 / 5 event definitions — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_event_limits.htm
- Publish Platform Event Messages Using Apex — Publish After Commit counts as a DML statement; Publish Immediately draws on a separate 150-call allocation (`Limits.getPublishImmediateDML()`); publish behaviour is set on the platform event definition — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_publish_apex.htm
- Configure the User and Batch Size for Your Platform Event Trigger with PlatformEventSubscriberConfig — default Apex trigger batch of 2,000 event messages, against 200 for object triggers — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_trigger_config.htm
- Retry Event Triggers with EventBus.RetryableException — up to ten executions (initial run plus nine retries), then the trigger moves to an error state and stops processing new events; `EventBus.TriggerContext.currentContext().retries` — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_subscribe_apex_refire.htm
- Resume a Platform Event Trigger After an Uncaught Exception — `setResumeCheckpoint(replayId)`; events resent in ReplayId order — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_subscribe_batch_resume.htm
- Message Durability (Streaming API) — high-volume events retained 72 hours, standard-volume 24 hours; new definitions are high-volume by default and standard-volume events can no longer be defined — https://developer.salesforce.com/docs/atlas.en-us.api_streaming.meta/api_streaming/using_streaming_api_durability.htm
- Standard-Volume Platform Events Are Being Retired — https://help.salesforce.com/s/articleView?id=release-notes.rn_messaging_standard_volume_retirement.htm&type=5
- Platform Events Maximum Batch Size Is 200 (flow subscribers) — https://help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow_mgmt_platform_events_max_batch_size.htm&release=234&type=5
- Run Event-Triggered Flows as Workflow User (Spring '24) — https://help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow_builder_run_event_triggered_flows_as_workflow_user.htm&release=248&type=5
- Per-Transaction Apex Governor Limits — the 100/200 SOQL and 150 DML ceilings a batched subscriber shares — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Salesforce Well-Architected — Resilient — https://architect.salesforce.com/docs/architect/well-architected/resilient/resilient
