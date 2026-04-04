# Examples — Streaming API and PushTopic

## Example 1: Subscribing to Opportunity Stage Changes from a Java Integration Service

**Context:** A revenue operations team has a Java-based analytics service that must update a data warehouse in real time whenever a Salesforce Opportunity moves to `Closed Won` or `Closed Lost`. The service runs as a daemon and must survive nightly restarts without losing events.

**Problem:** Without replay, a nightly restart causes the service to miss all events that fired while it was down. Setting replay to `-1` on every start would cause a replay storm of the entire 24-hour backlog on each restart.

**Solution:**

Step 1 — Create the PushTopic (run once, via Developer Console or Apex script):

```apex
PushTopic pt = new PushTopic();
pt.Name = 'ClosedOpportunities';
pt.Query = 'SELECT Id, Name, StageName, Amount, CloseDate, OwnerId '
         + 'FROM Opportunity '
         + 'WHERE StageName IN (\'Closed Won\', \'Closed Lost\')';
pt.ApiVersion = 60.0;
pt.NotifyForOperationCreate = false;
pt.NotifyForOperationUpdate = true;
pt.NotifyForOperationDelete = false;
pt.NotifyForOperationUndelete = false;
pt.NotifyForFields = 'Referenced';
insert pt;
// Channel: /topic/ClosedOpportunities
```

Step 2 — Java service using the Salesforce EMP Connector library:

```java
import com.salesforce.emp.connector.BayeuxParameters;
import com.salesforce.emp.connector.EmpConnector;
import com.salesforce.emp.connector.LoginHelper;
import com.salesforce.emp.connector.TopicSubscription;

import java.net.URL;
import java.util.Map;
import java.util.concurrent.atomic.AtomicLong;
import java.util.function.Consumer;

public class OpportunityStreamingClient {

    private static final String TOPIC = "/topic/ClosedOpportunities";
    private final AtomicLong lastReplayId;
    private final ReplayStore replayStore;

    public OpportunityStreamingClient(ReplayStore store) {
        this.replayStore = store;
        // Load persisted replay ID; default to -2 (new events only) on first run
        this.lastReplayId = new AtomicLong(store.load(TOPIC, -2L));
    }

    public void start(String loginUrl, String username, String password) throws Exception {
        BayeuxParameters params = LoginHelper.login(new URL(loginUrl), username, password);
        EmpConnector connector = new EmpConnector(params);
        connector.start().get();

        long replayFrom = lastReplayId.get();
        Consumer<Map<String, Object>> consumer = event -> {
            // Persist replay ID BEFORE processing to guarantee at-least-once delivery
            long replayId = (Long) ((Map<?, ?>) event.get("event")).get("replayId");
            replayStore.save(TOPIC, replayId);
            lastReplayId.set(replayId);
            processEvent(event);
        };

        TopicSubscription sub = connector.subscribe(TOPIC, replayFrom, consumer).get();
        System.out.println("Subscribed: " + sub);
    }

    private void processEvent(Map<String, Object> event) {
        Map<?, ?> sobject = (Map<?, ?>) event.get("sobject");
        System.out.println("Opportunity updated: " + sobject.get("Name")
            + " Stage=" + sobject.get("StageName")
            + " Amount=" + sobject.get("Amount"));
        // Forward to data warehouse ...
    }
}
```

**Why it works:** The `replayStore` persists the last seen `replayId` to durable storage (e.g., a local file or database) before the event is processed. On restart the service reads that ID and passes it to `subscribe`, so it replays only events missed while offline — not the full 24-hour backlog.

---

## Example 2: Generic Streaming Channel for Custom UI Refresh Notifications

**Context:** A warehouse management team has a custom Lightning page that displays live pick-list status. A Java batch process running in the data center updates pick records in bulk via the Bulk API. The Lightning page needs to refresh automatically when the batch finishes, without polling from the browser.

**Problem:** Using a PushTopic on the `Pick__c` object would fire one streaming event per individual record update during the bulk load — potentially thousands of events per batch run. The UI only needs a single "batch complete" signal, not per-record notifications.

**Solution:**

Step 1 — Create a Generic Streaming Channel (run once):

```apex
StreamingChannel sc = new StreamingChannel();
sc.Name = '/u/WarehouseBatchComplete';
insert sc;
// Note the channel Id for use by the publisher
System.debug('Channel Id: ' + sc.Id);
```

Step 2 — Java batch process publishes a single event when the bulk load finishes:

```java
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;

public class BatchCompletePublisher {

    private final String instanceUrl;
    private final String accessToken;
    private final String channelId;

    public void publishBatchComplete(String batchId, int recordCount) throws Exception {
        String payload = String.format(
            "{\"pushEvents\":[{\"payload\":\"{\\\"batchId\\\":\\\"%s\\\",\\\"count\\\":%d}\",\"userIds\":[]}]}",
            batchId, recordCount
        );

        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(instanceUrl
                + "/services/data/v60.0/sobjects/StreamingChannel/"
                + channelId + "/push"))
            .header("Authorization", "Bearer " + accessToken)
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(payload))
            .build();

        HttpResponse<String> response = HttpClient.newHttpClient()
            .send(request, HttpResponse.BodyHandlers.ofString());

        System.out.println("Publish response: " + response.statusCode() + " " + response.body());
    }
}
```

Step 3 — Lightning Web Component subscribes via `empApi`:

```javascript
import { LightningElement, wire } from 'lwc';
import { subscribe, onError } from 'lightning/empApi';

export default class WarehouseStatusPanel extends LightningElement {
    channelName = '/u/WarehouseBatchComplete';
    subscription = {};

    connectedCallback() {
        onError(error => console.error('EmpApi error', JSON.stringify(error)));
        subscribe(this.channelName, -1, (message) => {
            const data = JSON.parse(message.data.payload);
            this.dispatchEvent(new CustomEvent('batchcomplete', { detail: data }));
        }).then(response => {
            this.subscription = response;
        });
    }
}
```

**Why it works:** Generic Streaming decouples the event schema from any sObject. The Java process publishes one coarse-grained signal; the Lightning component reacts without per-record event overhead. The `userIds: []` broadcast sends to all current subscribers of the channel.

---

## Anti-Pattern: Polling Streaming API REST Endpoint Instead of Maintaining a Long-Poll Loop

**What practitioners do:** Some integrations call the CometD `/connect` endpoint on a timer (e.g., every 10 seconds via a cron job) instead of immediately re-issuing `connect` after each server response.

**What goes wrong:** The Salesforce CometD server interprets any gap in the long-poll loop as a disconnection. After the timeout elapses (typically 40 seconds on Salesforce), it invalidates the `clientId`. The next `connect` attempt returns `402::Unknown client`. The client must re-handshake, re-subscribe, and loses all events that arrived during the gap if no replay ID was stored.

**Correct approach:** After receiving any response from the `/connect` poll (whether it contains events or is an empty heartbeat), immediately re-issue the `/connect` request. The EMP Connector handles this automatically. When building a custom CometD client, implement the re-connect as a callback triggered on every response, not on a timer.
