# Gotchas — Error Handling in Integrations

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Trigger Suspension Blocks ALL Events — Not Just the Failing Ones

**What happens:** When a Platform Event trigger is suspended after 9 RetryableException failures, it stops processing all new events on that Platform Event channel — not just the events with the same failure pattern. A single bad payload causing 9 failures suspends an entire integration channel. Events published during the suspension period accumulate in the 72-hour buffer and must be replayed manually after re-enabling.

**When it occurs:** When RetryableException is thrown for permanent errors (bad data, invalid configuration) or when a transient external error persists beyond 9 retry attempts.

**How to avoid:** Only throw RetryableException for genuinely transient errors. For permanent errors, write to DLQ and return normally without throwing. Monitor for trigger suspension with automated alerts — Setup > Event Bus Monitoring or via the Platform Events developer console.

---

## Gotcha 2: Replay ID Is Not Stable After Salesforce Maintenance

**What happens:** Platform Event Replay IDs can be corrupted or reset after a Salesforce maintenance event or major release update. If a subscriber is re-enabled after maintenance using a Replay ID stored before the maintenance, the replay may start from an unexpected position or fail entirely.

**When it occurs:** After any Salesforce maintenance window, emergency patch, or major release update.

**How to avoid:** Store both the Replay ID and the event message ID (the unique stable identifier) on each successful event processing. Use Replay ID only for resuming the stream; use event message ID for deduplication on the subscriber side. After maintenance, verify the stored Replay ID is still valid before re-enabling.

---

## Gotcha 3: EventBus.RetryableException Affects the Entire Trigger Batch

**What happens:** If a Platform Event trigger processes events in bulk (Trigger.new has multiple events) and one event causes a RetryableException, ALL events in that batch are retried — not just the failing event. This means a single bad event in a batch can cause all events in the batch to be retried 9 times and eventually suspend the trigger for all of them.

**When it occurs:** When Platform Event triggers process multiple events per invocation (standard when events are published rapidly) and RetryableException is thrown without distinguishing which specific event failed.

**How to avoid:** Process events in the trigger one at a time using individual try/catch blocks. When one event fails permanently, write it to DLQ and continue processing the remaining events in the batch normally. Do not allow one bad event to block the entire batch.
