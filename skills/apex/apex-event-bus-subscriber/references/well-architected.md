# Well-Architected Notes — Apex Event Bus Subscriber

## Relevant Pillars

- **Reliability** — The retry-strategy choice (checkpoint vs
  RetryableException vs drop) is a first-class reliability decision.
  Each one has a different cost-of-failure profile: checkpoint is
  resilient to per-event failures but only retries the unprocessed
  slice; RetryableException retries the whole batch but requires
  idempotency; drop preserves throughput at the cost of losing the
  event. The 9-retry hard cap means "rely on retry" without a
  dead-letter is not a real reliability strategy.
- **Operational Excellence** — `PlatformEventSubscriberConfig` in
  source control (rather than tribal knowledge of "we tuned the batch
  size in production") is the difference between a maintainable
  subscriber and one whose behavior is folklore.

## Architectural Tradeoffs

- **Checkpoint vs RetryableException.** Checkpoint preserves
  per-event work on retry (skips already-processed events) but
  doesn't cover all-or-nothing semantics. RetryableException retries
  the whole batch atomically (good for ledger-style use cases) but
  requires every event in the batch to be idempotent. Pick based on
  whether the unit of work is the event or the batch.
- **2,000-event batch vs tuned smaller batch.** Larger batches
  amortize overhead but blow CPU/SOQL/DML governors faster. Smaller
  batches are safer per-batch but spend more wall-clock on platform
  overhead. Default 2,000 is fine for trivial work; CPU-heavy work
  needs measurement and tuning.
- **Default running user vs explicit integration user.** Default is
  whatever published the event — often a low-permission context
  unsuited for the trigger's downstream operations. Explicit
  integration user is more code (a `PlatformEventSubscriberConfig`)
  but produces predictable permissions.
- **In-org Apex subscriber vs external Pub/Sub API subscriber.**
  Apex trigger is in-org, runs against governor limits, retries are
  platform-managed up to 9 times. Pub/Sub API client is external,
  has no governor pressure, but you operate the client (deployment,
  monitoring, retry, replay). For high-volume / heavy-work flows,
  external Pub/Sub may beat Apex.

## Anti-Patterns

1. **Default trigger with no `setResumeCheckpoint`.** Any uncaught
   exception re-processes already-handled events on retry. Always
   checkpoint after each success unless deliberately Pattern B
   (all-or-nothing).
2. **Mixing checkpoint with `RetryableException`.** Contradictory.
   Pick one strategy.
3. **Catching `Exception` instead of typed exceptions.** Loses the
   transient-vs-permanent distinction; permanent failures burn the
   9-retry budget.
4. **Relying on retry without a dead-letter for must-not-lose flows.**
   After 10 attempts the events are gone. Plan accordingly.
5. **Calling fictional `EventBus.subscribe(...)` API.** Doesn't exist
   in Apex.
6. **Tests without `Test.EventBus.deliver()`.** Trigger never fires;
   tests are fake-passing.

## Official Sources Used

- Subscribe to Platform Events with Apex Triggers — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_subscribe_apex.htm
- Retry Event Triggers with EventBus.RetryableException — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_subscribe_apex_refire.htm
- EventBus.TriggerContext class reference — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_eventbus_TriggerContext.htm
- PlatformEventSubscriberConfig metadata — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_platformeventsubscriberconfig.htm
- Pub/Sub API overview (external clients) — https://developer.salesforce.com/docs/platform/pub-sub-api/overview
- Sibling skill — `skills/integration/event-relay-configuration/SKILL.md` (the same channel relayed to AWS EventBridge runs in parallel to this in-org subscriber)
