# Examples — Change Data Capture Integration

## Example 1: EMP Connector CometD Subscription with Durable Replay

**Context:** A Java-based integration service needs to subscribe to Account change events using the open-source EMP Connector (Salesforce's CometD reference implementation) and resume from the last processed event after a restart.

**Problem:** Without persisting the replay ID, after every restart the service either misses events (tip-only) or replays the full 72-hour window, causing duplicate processing in the downstream system.

**Solution:**

```java
// EMP Connector subscription with stored replay ID
// Requires: salesforce/EMP-Connector from GitHub

import com.salesforce.emp.connector.BayeuxParameters;
import com.salesforce.emp.connector.EmpConnector;
import com.salesforce.emp.connector.TopicSubscription;

long storedReplayId = loadReplayIdFromExternalStore(); // -2 for initial full catch-up
String channel = "/data/AccountChangeEvent";

BayeuxParameters params = new BayeuxParameters() {
    @Override public String bearerToken() { return accessToken; }
    @Override public URL host() { return new URL("https://MyOrg.my.salesforce.com"); }
};

EmpConnector connector = new EmpConnector(params);
connector.start();

TopicSubscription subscription = connector.subscribe(
    channel,
    storedReplayId,
    event -> {
        Map<String, Object> header = (Map<String, Object>)
            ((Map<String, Object>) event.get("data")).get("payload");
        Map<String, Object> changeHeader = (Map<String, Object>) header.get("ChangeEventHeader");
        String changeType = (String) changeHeader.get("changeType");

        if (changeType.startsWith("GAP_")) {
            // Gap event — fetch record from REST API
            List<String> recordIds = (List<String>) changeHeader.get("recordIds");
            handleGapEvent(recordIds, changeType);
        } else {
            processChangeEvent(event);
        }

        // Persist replay ID after successful processing
        long replayId = (long) event.get("replayId");
        persistReplayIdToExternalStore(replayId);
    }
).get();
```

**Why it works:** The replay ID is persisted to external state after each successfully processed event. On restart, the connector loads the last stored replay ID and passes it to `subscribe()`. Salesforce resumes delivery from that position within the 72-hour retention window. Gap detection prevents silent data drift when Salesforce cannot generate a full change event.

---

## Example 2: Pub/Sub API gRPC Subscription (Python) with changedFields Delta

**Context:** A Python integration service needs to sync only the fields that changed on Contact records to an external CRM. The team wants field-level delta without comparing full snapshots.

**Problem:** CometD delivers the full record payload, not just deltas. Building diff logic against a local cache is fragile and expensive. Pub/Sub API provides `changedFields` in the header natively.

**Solution:**

```python
# Pub/Sub API subscriber — requires salesforce/pub-sub-api Python client
# pip install salesforce-pubsub-api-client (reference client)
import pubsub_api_pb2 as pb2
import pubsub_api_pb2_grpc as pb2_grpc
import grpc, json

TOPIC_NAME = "/data/ContactChangeEvent"
REPLAY_ID = load_replay_id()  # bytes or None for tip

def fetch_events(stub, replay_id):
    fetch_req = pb2.FetchRequest(
        topic_name=TOPIC_NAME,
        replay_preset=pb2.ReplayPreset.LATEST if replay_id is None else pb2.ReplayPreset.CUSTOM,
        replay_id=replay_id,
        num_requested=100,
    )
    for response in stub.Subscribe(iter([fetch_req])):
        for event in response.events:
            decoded = decode_avro(event.event.payload, response.schema_id)
            header = decoded["ChangeEventHeader"]
            change_type = header["changeType"]

            if change_type.startswith("GAP_"):
                for record_id in header["recordIds"]:
                    mark_dirty_and_queue_fetch(record_id)
            elif change_type == "UPDATE":
                # changedFields is available in Pub/Sub API — base64-encoded bitmap
                changed = decode_changed_fields(header["changedFields"], decoded)
                sync_changed_fields_to_external_crm(header["recordIds"][0], changed)
            else:
                sync_full_record(header["recordIds"][0], decoded)

            save_replay_id(event.replay_id)
```

**Why it works:** Pub/Sub API surfaces `changedFields` in the `ChangeEventHeader`, allowing the subscriber to process only the fields that changed in an UPDATE. This eliminates the need for snapshot comparison and reduces the volume of writes to the external CRM. Gap events are detected by the `GAP_` prefix and routed to a fallback REST fetch.

---

## Example 3: MuleSoft CDC Subscriber with Custom Channel

**Context:** A MuleSoft integration flow subscribes to a custom CDC channel that delivers Order change events enriched with Account.Name — avoiding a follow-up query to Salesforce per event.

**Problem:** Using the default `ChangeEvents` channel delivers events for all selected objects. Adding Account.Name to the Order change event requires event enrichment, which is only supported on custom channels.

**Solution — Metadata API setup:**

```xml
<!-- PlatformEventChannel -->
<PlatformEventChannel xmlns="http://soap.sforce.com/2006/04/metadata">
    <channelType>data</channelType>
    <label>ERP Order Sync</label>
</PlatformEventChannel>
<!-- Filename: ERP_Order_Sync__chn.platformEventChannel -->

<!-- PlatformEventChannelMember with enrichment -->
<PlatformEventChannelMember xmlns="http://soap.sforce.com/2006/04/metadata">
    <eventChannel>ERP_Order_Sync__chn</eventChannel>
    <selectedEntity>Order</selectedEntity>
    <enrichedFields>
        <name>Account.Name</name>
    </enrichedFields>
</PlatformEventChannelMember>
```

**MuleSoft flow subscription URL:**
```
/data/ERP_Order_Sync__chn
```

**Why it works:** The custom channel scopes delivery to Order events only and enriches the payload with `Account.Name`. The MuleSoft connector subscribes to the isolated channel, reducing event delivery allocation consumption compared to the full `ChangeEvents` channel, and eliminating follow-up SOQL queries per event.

---

## Anti-Pattern: Polling REST API Instead of Using CDC

**What practitioners do:** Query Salesforce via REST API on a schedule (`LastModifiedDate > :lastRun`) to detect changed records and sync to an external system.

**What goes wrong:**
- Deletes are invisible — REST API cannot surface records that were deleted between polling intervals.
- Undeletes are missed unless the subscriber also queries the recycle bin.
- Field-level deltas are not available — the subscriber must compare full record snapshots.
- High query volume counts against API limits, especially for large orgs.
- Missed changes in the gap between polls create data drift that compounds over time.

**Correct approach:** Enable CDC for the target entities and subscribe via Pub/Sub API or CometD. CDC explicitly delivers `CREATE`, `UPDATE`, `DELETE`, and `UNDELETE` events with field-level change information. Reserve polling as a re-sync fallback for recovery after CDC retention window expiry, not as the primary integration mechanism.
