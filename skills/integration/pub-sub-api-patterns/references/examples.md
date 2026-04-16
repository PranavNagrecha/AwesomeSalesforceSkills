# Examples — Pub/Sub API Patterns

## Example 1: Subscribe to Change Data Capture Events via gRPC

**Context:** An ERP integration team needs to receive real-time notifications when Salesforce Account records are updated, to sync changes to their on-premises ERP system.

**Problem:** The team was using CometD/EMP Connector for CDC subscription, which was working but suffering from connection instability and reconnection complexity. They wanted to migrate to Pub/Sub API gRPC for improved reliability.

**Solution:**

```python
import grpc
from google.protobuf.json_format import MessageToJson
# Assumes generated stubs from pubsub_api.proto
from pubsub_api_pb2 import FetchRequest, ReplayPreset
from pubsub_api_pb2_grpc import PubSubStub

def create_metadata(access_token, instance_url, org_id):
    return [
        ("accesstoken", access_token),
        ("instanceurl", instance_url),
        ("tenantid", org_id),  # Must be 18-character org ID
    ]

def subscribe_to_cdc(access_token, instance_url, org_id, last_replay_id=None):
    metadata = create_metadata(access_token, instance_url, org_id)
    channel = grpc.secure_channel(
        "api.pubsub.salesforce.com:7443",
        grpc.ssl_channel_credentials()
    )
    stub = PubSubStub(channel)
    
    def fetch_requests():
        if last_replay_id:
            yield FetchRequest(
                topic_name="/data/AccountChangeEvent",
                replay_preset=ReplayPreset.CUSTOM,
                replay_id=last_replay_id,
                num_requested=100
            )
        else:
            yield FetchRequest(
                topic_name="/data/AccountChangeEvent",
                replay_preset=ReplayPreset.LATEST,
                num_requested=100
            )
        while True:
            yield FetchRequest(num_requested=100)
    
    for event_batch in stub.Subscribe(fetch_requests(), metadata=metadata):
        for event in event_batch.events:
            process_account_change(event)
            save_replay_id(event.replay_id)  # Persist for reconnect

def process_account_change(event):
    # Decode Avro payload and send to ERP
    pass

def save_replay_id(replay_id):
    # Persist to Redis or database for reconnect
    pass
```

**Why it works:** gRPC Subscribe with flow-controlled FetchRequests handles CDC events reliably. Persisting `replay_id` after each successful processing enables resume-from-last-position on reconnect.

---

## Example 2: Managed Subscription for Containerized Consumer

**Context:** A serverless event processing function (AWS Lambda) subscribes to Salesforce Platform Events for order processing. Each Lambda invocation is stateless — there is no persistent storage for replay ID tracking.

**Problem:** Standard Subscribe requires the consumer to track and persist replay IDs. In a stateless serverless environment, replay IDs would be lost on each cold start, causing events to be reprocessed from Earliest on every restart.

**Solution:**

1. Create a `ManagedEventSubscription` metadata record in Salesforce:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ManagedEventSubscription xmlns="http://soap.sforce.com/2006/04/metadata">
    <developerName>OrderProcessingSubscription</developerName>
    <eventChannel>/event/OrderCreated__e</eventChannel>
    <referenceData>order-processing-lambda-v1</referenceData>
</ManagedEventSubscription>
```

2. In the Lambda function, use `ManagedSubscribe` with the subscription name:

```python
def fetch_requests():
    yield ManagedFetchRequest(
        managed_subscription="OrderProcessingSubscription",
        num_requested=50
    )
    while True:
        yield ManagedFetchRequest(num_requested=50)

for batch in stub.ManagedSubscribe(fetch_requests(), metadata=metadata):
    for event in batch.events:
        process_order_event(event)
        # No need to persist replay_id — server tracks it
```

**Why it works:** ManagedSubscribe offloads replay ID tracking to the Salesforce server. The Lambda function can be restarted without losing its position in the event stream.

---

## Anti-Pattern: Using 15-Character Org ID as tenantid

**What practitioners do:** Copy the Org ID from Salesforce Setup (which displays 15 characters in some contexts) and use it directly as the `tenantid` gRPC header.

**What goes wrong:** All gRPC Subscribe calls authenticate successfully with the access token but return "Unauthorized" or "Tenant not found" errors because the `tenantid` requires the 18-character format.

**Correct approach:** Always retrieve the Org ID using SOQL: `SELECT Id FROM Organization` — this returns the 18-character version. Verify it is 18 characters before configuring it as `tenantid`.
