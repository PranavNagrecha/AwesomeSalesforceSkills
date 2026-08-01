# Gotchas — Pub/Sub API Patterns

## Gotcha 1: tenantid Must Be 18-Character Org ID

**What happens:** All Pub/Sub API gRPC calls return authentication or authorization errors despite valid access tokens, because the `tenantid` header contains the 15-character Org ID instead of the required 18-character version.

**When it occurs:** When developers copy the Org ID from Salesforce Setup UI (which displays 15 characters in some locations) without converting to 18-character format.

**How to avoid:** Always retrieve the Org ID via SOQL: `SELECT Id FROM Organization`. The `Id` field always returns the 18-character format. Verify the length before configuring `tenantid`.

---

## Gotcha 2: 100-Event FetchRequest Cap Is Per-Request, Not a Rate Limit

**What happens:** An architect designs capacity planning based on "100 event limit" per FetchRequest, believing the API can only deliver 100 events total per second or per connection. They over-provision infrastructure based on a misunderstood constraint.

**When it occurs:** When the per-request batch size limit is communicated as a throughput rate limit.

**How to avoid:** The 100-event cap in `num_requested` is the maximum number of events the server delivers per FetchRequest. After consuming those 100, the client sends another FetchRequest for the next batch. There is no rate limit on how many FetchRequests can be issued per second — throughput is controlled by the client's processing speed and the event volume on the topic.

---

## Gotcha 3: 2-Hour Session Does Not Drop Active Subscribe Streams

**What happens:** A developer implements token refresh logic that also closes and reopens the gRPC Subscribe stream on every 2-hour token renewal, causing brief event-delivery gaps every 2 hours.

**When it occurs:** When developers model the 2-hour OAuth session timeout as also timing out the Subscribe stream connection.

**How to avoid:** The 2-hour OAuth session timeout does NOT drop active Subscribe streams — the stream remains open. Only implement token refresh; do not close and reopen the Subscribe stream unless the connection actually errors. However, implement pre-emptive token refresh before the 2-hour window to avoid PublishStream idle connection closure.

---

## Gotcha 4: An Out-of-Window Replay ID Errors — It Does Not Silently Reposition

**What happens:** A consumer offline for four days reconnects with a stored replay ID. It does **not** quietly restart from the oldest retained event. The Subscribe call fails with `sfdc.platform.eventbus.grpc.subscription.fetch.replayid.corrupted` — documented as "Replay ID invalid or outside retention window." A consumer written on the assumption of silent repositioning has no handler for this path and stays down.

Three further facts about the window that change recovery design:

- Retention is 72 hours and the boundary is fuzzy in the *permissive* direction only: "The purging process sometimes starts later, and as a result, platform events and change data capture events that are older than 72 hours can still be available. Salesforce doesn't guarantee the storage of events beyond the retention period of 72 hours." So a 74-hour-old replay ID may work in a test and fail in production. Never build a recovery path on events older than 72 hours.
- Org migration wipes the stream: "the stream of retained events can be reset if the Salesforce org is moved to a new instance. As a result, you can no longer access the retained events." A stored replay ID can therefore become invalid with zero downtime on the subscriber side.
- Replay IDs are opaque. "Replay ID values aren't guaranteed to be contiguous for consecutive events", so a gap between two IDs is not evidence of a lost event and arithmetic on them is meaningless.

**The ReplayPreset trade-off — do not reflex to EARLIEST.** The documented recovery is "retry the `Subscribe` call with the `LATEST ReplayPreset` enum value to receive new events only, or use the `EARLIEST` option to receive all events that are stored." EARLIEST replays up to 72 hours of traffic through the org's 24-hour delivery allocation (25,000/day on Enterprise, 50,000 Performance/Unlimited, 10,000 Developer). On a busy channel that converts a recoverable gap into `...subscription.limit.exceeded` and a full-day outage for **every** subscriber in the org, because the allocation is org-wide. Prefer LATEST plus an out-of-band reconciliation (Bulk API re-query of the affected records) unless you have measured the replay volume against remaining allocation.

**How to avoid:** Handle `replayid.corrupted` explicitly. Alert on subscriber downtime at 24 hours, well inside the window. If downtime beyond 72 hours is plausible, archive events on arrival so replay comes from your store rather than the event bus.

---

## Gotcha 5: Managed Subscription Limit Is 200 Per Org

**What happens:** A new ManagedEventSubscription metadata record fails to deploy because the org has reached its 200 managed subscription limit.

**When it occurs:** In large organizations with many independent event consumers, each using a Managed Subscription.

**How to avoid:** Audit and clean up unused ManagedEventSubscription records regularly. Design consumer topology to share subscriptions where consumers have the same event processing requirements. Consider standard Subscribe with external replay ID storage for consumers where 200 limit is a constraint.
