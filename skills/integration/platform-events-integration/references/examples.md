# Examples — Platform Events Integration

## Example 1: External ERP Publishing Order Events into Salesforce via REST

**Context:** An external Java-based ERP system needs to notify Salesforce whenever an order ships. A Platform Event named `OrderShipped__e` has been defined in Salesforce with fields `OrderId__c` (Text), `ShippedDate__c` (DateTime), and `CorrelationId__c` (Text, for idempotency).

**Problem:** Without a structured publish pattern, teams often call a Salesforce custom REST endpoint or trigger a workflow via polling. This couples the ERP to Salesforce record structure and loses the decoupled event model entirely.

**Solution:**

```bash
# Step 1: Get an access token using JWT Bearer flow
curl -X POST https://login.salesforce.com/services/oauth2/token \
  -d "grant_type=urn:ietf:params:oauth2:grant-type:jwt-bearer" \
  -d "assertion=<signed_jwt>"

# Step 2: Publish the Platform Event
curl -X POST https://yourorg.salesforce.com/services/data/v61.0/sobjects/OrderShipped__e/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "OrderId__c": "801xx000000ABCDEF",
    "ShippedDate__c": "2025-10-15T14:30:00Z",
    "CorrelationId__c": "erp-order-ship-20251015-801xx000000ABCDEF"
  }'

# Response includes the replayId of the published event:
# { "id": "e00xx000000GHIJK", "success": true, "errors": [] }
```

**Why it works:** The Connected App JWT flow provides machine-to-machine auth with no user interaction. The `CorrelationId__c` field on the event payload allows Apex or Flow subscribers to perform idempotent processing — the same event published twice can be detected and skipped. The REST endpoint is available on any API version that supports the event definition.

---

## Example 2: Node.js Middleware Using Pub/Sub API with Durable Replay

**Context:** A Node.js integration platform subscribes to `InventoryUpdated__e` events from Salesforce to update a downstream warehouse management system. The platform restarts nightly for deployments and must not miss events published during the maintenance window.

**Problem:** If the subscriber always connects with replay ID `-1` (latest), events published during the maintenance window are silently dropped. The warehouse system ends up with stale inventory counts until the next full sync.

**Solution:**

```javascript
// Pseudo-code using the Salesforce Pub/Sub API Node.js client
// https://github.com/forcedotcom/pub-sub-api-node-client

const { PubSubApiClient } = require('salesforce-pubsub-api-client');
const db = require('./replay-store'); // durable key-value store, e.g. Redis or Postgres

async function subscribe() {
  const client = new PubSubApiClient();
  await client.connect();

  // Retrieve last stored replay ID from durable store
  let lastReplayId = await db.get('InventoryUpdated__e:lastReplayId');

  // Use stored ID on restart; fall back to -2 (earliest) on first run
  const replayPreset = lastReplayId ?? -2;

  const eventEmitter = await client.subscribe(
    '/event/InventoryUpdated__e',
    handleEvent,
    replayPreset
  );

  async function handleEvent(event) {
    // Process the event payload
    await warehouseSystem.update(event.payload);

    // Persist replay ID AFTER successful processing
    await db.set('InventoryUpdated__e:lastReplayId', event.replayId);
  }
}

subscribe();
```

**Why it works:** Persisting the `replayId` only after successful downstream processing ensures that a crash mid-batch causes the subscriber to replay from the last confirmed position rather than advancing past unprocessed events. Starting with `-2` on first run replays all events still inside the retention window (72 hours for high-volume events), preventing loss on initial deployment. Note the values: `-1` is the default and means new events only; `-2` means replay everything retained.

---

## Example 3: Durable Ledger for a Replay Window Longer Than 72 Hours

**Context:** A financial services org publishes `LedgerEntry__e`. A downstream reconciliation job runs every Sunday and needs to read the entire week of entries.

**Problem:** Platform event retention is a fixed platform property — 72 hours for high-volume events (all events defined after Spring '19), 24 hours for legacy standard-volume events. It is not configurable, and there is no publishable retention field on the event. A Sunday job that relies on `replayId` catch-up alone receives Thursday onward and silently loses four days.

**Solution — publish and persist in the same unit of work, then backfill from the ledger:**

```apex
// The Big Object is the durable record; the event is the low-latency notification.
// Composite index on LedgerEntry__b must be (EntryDate__c, AccountId__c) so the
// weekly reconciliation filter follows it left to right.
List<LedgerEntry__e> events = new List<LedgerEntry__e>();
List<LedgerEntry__b> ledgerRows = new List<LedgerEntry__b>();

for (Ledger__c ledger : ledgers) {
    String correlationId = ledger.Id + ':' + String.valueOf(ledger.SystemModstamp.getTime());

    events.add(new LedgerEntry__e(
        AccountId__c     = ledger.AccountId__c,
        Amount__c        = ledger.Amount__c,
        EntryDate__c     = ledger.EntryDate__c,
        CorrelationId__c = correlationId
    ));

    ledgerRows.add(new LedgerEntry__b(
        AccountId__c     = ledger.AccountId__c,
        Amount__c        = ledger.Amount__c,
        EntryDate__c     = ledger.EntryDate__c,
        CorrelationId__c = correlationId
    ));
}

Database.insertImmediate(ledgerRows);   // Big Object write — survives the 72h window
EventBus.publish(events);               // notification — expires after 72h
```

The Sunday job reads the ledger, not the event bus:

```apex
// Filters follow the composite index left to right (EntryDate__c first).
List<LedgerEntry__b> week = [
    SELECT AccountId__c, Amount__c, EntryDate__c, CorrelationId__c
    FROM LedgerEntry__b
    WHERE EntryDate__c >= :Date.today().addDays(-7)
];
```

**Why it works:** The event carries latency; the Big Object carries durability. `CorrelationId__c` is the join key, so a subscriber that processed Thursday's events live and then backfills the full week can deduplicate against what it already applied — which it needs anyway, because platform events are at-least-once. The reconciliation job's correctness no longer depends on any subscriber having stayed connected.

**What NOT to do:** Do not add a retention field to the event payload. `RetainUntilDate` is not a real field on any Platform Event; Salesforce ignores the unrecognized key and the publish succeeds, so the mistake produces no error at any point — only missing events days later.

---

## Anti-Pattern: Hardcoding Replay ID to `-1` on Every Subscribe

**What practitioners do:** A CometD subscriber always connects with replay ID `-1` (tip of the channel) because it "only cares about new events." This is implemented as a hardcoded constant in the connection setup.

**What goes wrong:** When the subscriber disconnects unexpectedly (network blip, deployment restart), it reconnects with `-1` and misses all events published during the outage. In a payment processing integration this silently drops payment notifications. The downstream system only discovers the gap during an end-of-day reconciliation, by which point the events are irretrievable.

**Correct approach:** Always load a stored `replayId` from durable state on startup. Use `-1` only in explicitly ephemeral consumers (dashboards, dev testing) where event loss is acceptable and documented. For any production integration, `-1` requires a written architectural decision explaining why event loss is acceptable.
