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

**Why it works:** Persisting the `replayId` only after successful downstream processing ensures that a crash mid-batch causes the subscriber to replay from the last confirmed position rather than advancing past unprocessed events. Starting with `-2` on first run replays all events in the 72-hour retention window, preventing loss on initial deployment.

---

## Example 3: High-Volume Platform Event with RetainUntilDate for Weekly Batch Reconciliation

**Context:** A financial services org publishes `LedgerEntry__e` as a High-Volume Platform Event. A downstream reconciliation job runs every Sunday and needs to replay the entire week of events.

**Problem:** Standard Platform Events have a fixed 72-hour (3-day) retention window, which is insufficient for a weekly reconciliation window. Using a standard event and relying on replay would lose 4 days of data.

**Solution:**

```apex
// Set RetainUntilDate when publishing from Apex
// (can also be set via REST from external systems as a field on the event)
LedgerEntry__e entry = new LedgerEntry__e(
    AccountId__c = ledger.AccountId,
    Amount__c = ledger.Amount,
    EntryDate__c = Date.today()
);
// RetainUntilDate is a standard field on High-Volume events
entry.RetainUntilDate = DateTime.now().addDays(8); // Retain for 8 days

EventBus.publish(entry);
```

```bash
# External publisher setting RetainUntilDate via REST
curl -X POST https://yourorg.salesforce.com/services/data/v61.0/sobjects/LedgerEntry__e/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "AccountId__c": "001xx000003GYkA",
    "Amount__c": 1500.00,
    "EntryDate__c": "2025-10-15T00:00:00Z",
    "RetainUntilDate": "2025-10-23T00:00:00Z"
  }'
```

**Why it works:** High-Volume Platform Events expose `RetainUntilDate` as a publishable field. Setting it to 8 days ahead ensures events survive the full weekly reconciliation window. Without this explicit field on a High-Volume event, events are subject to the default platform retention behavior, which may not cover the full replay window needed.

---

## Anti-Pattern: Hardcoding Replay ID to `-1` on Every Subscribe

**What practitioners do:** A CometD subscriber always connects with replay ID `-1` (tip of the channel) because it "only cares about new events." This is implemented as a hardcoded constant in the connection setup.

**What goes wrong:** When the subscriber disconnects unexpectedly (network blip, deployment restart), it reconnects with `-1` and misses all events published during the outage. In a payment processing integration this silently drops payment notifications. The downstream system only discovers the gap during an end-of-day reconciliation, by which point the events are irretrievable.

**Correct approach:** Always load a stored `replayId` from durable state on startup. Use `-1` only in explicitly ephemeral consumers (dashboards, dev testing) where event loss is acceptable and documented. For any production integration, `-1` requires a written architectural decision explaining why event loss is acceptable.
