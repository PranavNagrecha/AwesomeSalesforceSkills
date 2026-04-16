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

## Gotcha 4: Events Retained for Only 3 Days

**What happens:** A consumer that goes offline for 4 days reconnects using a stored replay ID. The events from 4 days ago are no longer available — the replay request silently starts from the earliest available event (3 days back) rather than the requested position.

**When it occurs:** When consumer downtime exceeds the 3-day event bus retention window.

**How to avoid:** Monitor consumer health and alert on downtime exceeding 24 hours. Design consumers with 3-day SLA tolerance. If consumer downtime may exceed 3 days, implement a parallel archive (e.g., log all events to S3 as they arrive) to enable historical replay from the archive rather than the event bus.

---

## Gotcha 5: Managed Subscription Limit Is 200 Per Org

**What happens:** A new ManagedEventSubscription metadata record fails to deploy because the org has reached its 200 managed subscription limit.

**When it occurs:** In large organizations with many independent event consumers, each using a Managed Subscription.

**How to avoid:** Audit and clean up unused ManagedEventSubscription records regularly. Design consumer topology to share subscriptions where consumers have the same event processing requirements. Consider standard Subscribe with external replay ID storage for consumers where 200 limit is a constraint.
