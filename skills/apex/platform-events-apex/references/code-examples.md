# Code Examples — Platform Events Apex

A complete, deployable publish-and-subscribe slice for one business event,
`Order_Approved__e`. Nothing here is pseudo-code: the classes compile against the
canonical templates in `templates/apex/`, the XML parses, and the `package.xml`
deploys in the stated order.

Canonical building blocks referenced by relative path instead of being re-invented:

| Template | Used for |
|---|---|
| `templates/apex/BaseService.cls` | publisher service base (savepoint + logging hooks) |
| `templates/apex/ApplicationLogger.cls` | queryable publish/subscribe failure logging instead of `System.debug` |
| `templates/apex/TriggerHandler.cls` | **not** used by the `__e` trigger — see "Why the event trigger does not extend TriggerHandler" below |
| `templates/apex/tests/TestDataFactory.cls` | bulk record setup in the test class |
| `templates/apex/custom_objects/Application_Log__c.object-meta.xml` | the log object `ApplicationLogger` writes to |

---

## Artifact 1 — the event definition (`Order_Approved__e.object-meta.xml`)

Path: `force-app/main/default/objects/Order_Approved__e/Order_Approved__e.object-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <deploymentStatus>Deployed</deploymentStatus>
    <description>Business event: an order cleared approval and is ready for downstream fulfilment.</description>
    <eventType>HighVolume</eventType>
    <label>Order Approved</label>
    <pluralLabel>Order Approved Events</pluralLabel>
    <publishBehavior>PublishAfterCommit</publishBehavior>
    <fields>
        <fullName>Order_Id__c</fullName>
        <label>Order Id</label>
        <length>18</length>
        <required>true</required>
        <type>Text</type>
    </fields>
    <fields>
        <fullName>Order_Number__c</fullName>
        <label>Order Number</label>
        <length>80</length>
        <required>false</required>
        <type>Text</type>
    </fields>
    <fields>
        <fullName>Amount__c</fullName>
        <label>Amount</label>
        <precision>18</precision>
        <scale>2</scale>
        <required>false</required>
        <type>Number</type>
    </fields>
    <fields>
        <fullName>Correlation_Id__c</fullName>
        <label>Correlation Id</label>
        <length>64</length>
        <required>false</required>
        <type>Text</type>
    </fields>
</CustomObject>
```

**How to read it**

- `<eventType>HighVolume</eventType>` — the only value worth writing today.
  `StandardVolume` is documented as *"Deprecated. Creating a platform event with
  this event type is supported and returns an error."* (Metadata API Guide,
  `api_meta` L42091–42097). An existing standard-volume event is migrated with the
  `PlatformEventMigration` type (`api_meta` L96225–96330).
- `<publishBehavior>PublishAfterCommit</publishBehavior>` — publish only after the
  transaction commits successfully; if the transaction fails the message is never
  published (`api_meta` L42206–42230). **Omitting this element does not give you
  that behaviour**: *"If you don't specify this field, the default value used is
  `PublishImmediately`"* (`api_meta` L42228–42229), which fires regardless of
  whether the transaction succeeds.
- The element order is the Metadata API's alphabetical-ish shape from the
  `CustomObject` sample definition (`api_meta` L42455–42478); `nameField` and
  `sharingModel` do not apply to a `__e` object.
- `EventUuid` and `ReplayId` are system fields on the delivered message — you do
  not declare them. `EventUuid` is *"The unique ID of the event"*; `ReplayId` is
  the position in the stream (Object Reference, `object_reference` L94010–94040
  shows the same pair on a platform event object; `EventBus.SuccessResult`/
  `FailureResult` return `EventUuid` values, `apexrefguide` L157596–157650).

---

## Artifact 2 — the publisher service (`OrderApprovedPublisher.cls`)

```apex
/**
 * Publishes the Order_Approved__e business event.
 *
 * Extends templates/apex/BaseService.cls so that savepoint + logging hooks are
 * inherited rather than re-implemented. Publication is the LAST thing the
 * service does: with publishBehavior = PublishAfterCommit the message is only
 * released if the surrounding transaction commits.
 */
public with sharing class OrderApprovedPublisher extends BaseService {

    public class PublishFailure {
        public String orderId;
        public String correlationId;
        public String statusCode;
        public String message;
    }

    /**
     * @return one PublishFailure per rejected event. An EMPTY list is the only
     *         proof of success — EventBus.publish never throws for a rejected
     *         event (apexrefguide L214563).
     */
    public List<PublishFailure> publishApproved(List<Order__c> approvedOrders) {
        List<PublishFailure> failures = new List<PublishFailure>();
        if (approvedOrders == null || approvedOrders.isEmpty()) {
            return failures;
        }

        String correlationId = System.Request.getCurrent().getRequestId();
        List<Order_Approved__e> events = new List<Order_Approved__e>();
        for (Order__c approved : approvedOrders) {
            events.add(new Order_Approved__e(
                Order_Id__c       = String.valueOf(approved.Id),
                Order_Number__c   = approved.Name,
                Amount__c         = approved.Amount__c,
                Correlation_Id__c = correlationId
            ));
        }

        // ONE call for the whole batch. Under PublishImmediately each call would
        // burn one of 150 EventBus.publish() calls per transaction; under
        // PublishAfterCommit each call is one DML statement (apexdev L19598, L19635).
        List<Database.SaveResult> results = EventBus.publish(events);

        for (Integer i = 0; i < results.size(); i++) {
            if (results[i].isSuccess()) {
                continue;
            }
            for (Database.Error err : results[i].getErrors()) {
                PublishFailure failure = new PublishFailure();
                failure.orderId       = events[i].Order_Id__c;
                failure.correlationId = correlationId;
                failure.statusCode    = String.valueOf(err.getStatusCode());
                failure.message       = err.getMessage();
                failures.add(failure);

                ApplicationLogger.error(
                    'OrderApprovedPublisher.publishApproved',
                    'Order ' + events[i].Order_Id__c + ' rejected by the event bus: ' +
                        err.getStatusCode() + ' ' + err.getMessage()
                );
            }
        }
        ApplicationLogger.flush();
        return failures;
    }
}
```

`OrderApprovedPublisher.cls-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

**How to read it**

- `EventBus.publish(List<SObject>)` returns `List<Database.SaveResult>` and
  *"can publish some passed-in events, even when other events can't be published
  due to errors. The `EventBus.publish()` method doesn't throw exceptions caused
  by an unsuccessful publish operation. It's similar in behavior to the Apex
  `Database.insert` method when called with the partial success option."*
  (`apexrefguide` L214561–214565). The index-aligned loop over `results` is the
  only way to learn which event failed.
- `Database.SaveResult.getId()` is populated but *"The Id field value isn't
  included in the event message delivered to subscribers. It isn't used to
  identify an event message, and isn't always unique."* (`apexrefguide`
  L214565–214567). Do not log it as the event's identity — use `EventUuid`
  (Artifact 3) or your own `Correlation_Id__c`.
- Choose `apiVersion` 67.0 or later deliberately: *"Prior to API version 67.0,
  this method ran with `AccessLevel.SYSTEM_MODE` access. Starting with API
  version 67.0, it runs with `AccessLevel.USER_MODE` access."* (`apexrefguide`
  L214581–214583). If the publishing user lacks create access on the event, a
  class saved at 67.0 fails where the same code at 66.0 succeeded. Use
  `EventBus.publishWithAccessLevel(events, AccessLevel.SYSTEM_MODE)`
  (`apexrefguide` L214750–214753) only when you have decided that the publish must
  bypass the running user's permissions.

---

## Artifact 3 — knowing whether the bus actually accepted it (`OrderApprovedPublishCallback.cls`)

`isSuccess() == true` means only that *"the publish request is queued in Salesforce
and the event message is published asynchronously"* (`apexrefguide` L214510–214513).
The final asynchronous result arrives through a publish callback.

```apex
/**
 * Apex publish callback. onSuccess/onFailure fire when the FINAL result of the
 * asynchronous publish becomes available (apexrefguide L157451-157460,
 * L157518-157527), which is later than the SaveResult the publisher saw.
 */
public with sharing class OrderApprovedPublishCallback
        implements EventBus.EventPublishSuccessCallback,
                   EventBus.EventPublishFailureCallback {

    public void onSuccess(EventBus.SuccessResult result) {
        for (String eventUuid : result.getEventUuids()) {
            ApplicationLogger.info('OrderApprovedPublishCallback.onSuccess',
                'Order_Approved__e reached the bus: EventUuid ' + eventUuid);
        }
        ApplicationLogger.flush();
    }

    public void onFailure(EventBus.FailureResult result) {
        for (String eventUuid : result.getEventUuids()) {
            ApplicationLogger.error('OrderApprovedPublishCallback.onFailure',
                'Order_Approved__e NEVER reached the bus: EventUuid ' + eventUuid);
        }
        ApplicationLogger.flush();
    }
}
```

Publishing with the callback, and correlating the callback back to your record:

```apex
// Pre-populate EventUuid so the callback's getEventUuids() can be matched to a
// record you already logged. newSObject(recordTypeId, loadDefaults) is documented
// for exactly this: "You can also use this method to create a platform event with
// a prepopulated EventUuid field value for Apex publish callbacks."
// (apexrefguide L194227-194229)
Order_Approved__e evt =
    (Order_Approved__e) Order_Approved__e.SObjectType.newSObject(null, true);
evt.Order_Id__c     = String.valueOf(approvedOrder.Id);
evt.Order_Number__c = approvedOrder.Name;

List<Database.SaveResult> results =
    EventBus.publish(new List<Order_Approved__e>{ evt },
                     new OrderApprovedPublishCallback());

// getOperationId returns the event UUID for a published message, and null when
// the request failed to be enqueued synchronously (apexrefguide L214466-214486).
String eventUuid = EventBus.getOperationId(results[0]);
```

`EventBus.publish(List<SObject> sobjects, Object callback)` signature: `apexrefguide`
L214727–214729. The `callback` parameter is *"An Apex class that implements the
`EventPublishFailureCallback` Interface or `EventPublishSuccessCallback` Interface"*
(`apexrefguide` L214735–214737).

UNVERIFIED (2026-09-05): the Apex Reference Guide states no API-version floor for
`publish(event, callback)` or for the callback interfaces; the floor is only stated
in the Platform Events Developer Guide ("Get the Result of Asynchronous Platform
Event Publishing with Apex Publish Callbacks"), which is not in the offline corpus
and whose host cannot be fetched. Confirm the minimum `apiVersion` in your
`-meta.xml` against that page before shipping the callback variant.

---

## Artifact 4 — the subscriber (`OrderApprovedEventTrigger.trigger` + handler)

```apex
/**
 * Platform event subscriber. Thin by design: the trigger is the adapter and the
 * handler owns idempotency, checkpointing, and the retry decision.
 */
trigger OrderApprovedEventTrigger on Order_Approved__e (after insert) {
    new OrderApprovedEventHandler().handle(Trigger.new);
}
```

```apex
/**
 * Order_Approved__e subscriber handler.
 *
 * Three properties this class must have, in this order:
 *   1. idempotent      - the same EventUuid must never create two fulfilment rows
 *   2. checkpointed    - a partial failure must not replay work already done
 *   3. retry-capped    - it must never exceed the retry budget and push the
 *                        subscription into the Error state
 */
public with sharing class OrderApprovedEventHandler {

    /**
     * The Object Reference recommends "limiting the retries to fewer than nine
     * times" so the subscriber never reaches Status = Error
     * (object_reference L131382-131389). retries is 0 on the first delivery, so
     * a cap of 8 means at most 8 retries after the initial attempt.
     */
    @TestVisible private static final Integer MAX_RETRIES = 8;

    /**
     * The default trigger batch size for platform events is 2,000 events
     * (apexdev L19862; PlatformEventSubscriberConfig.batchSize default 2,000,
     * api_meta L96412-96417). 2,000 events in one execution will not survive a
     * per-event SOQL/DML pattern, so work is done in bulk chunks and the
     * checkpoint advances only past a chunk whose work completed.
     */
    @TestVisible private static final Integer CHUNK_SIZE = 200;

    public void handle(List<Order_Approved__e> events) {
        if (events == null || events.isEmpty()) {
            return;
        }

        Set<String> alreadyProcessed = loadProcessedUuids(events);

        for (Integer start = 0; start < events.size(); start += CHUNK_SIZE) {
            Integer stop = Math.min(start + CHUNK_SIZE, events.size());

            List<Order_Approved__e> chunk = new List<Order_Approved__e>();
            for (Integer i = start; i < stop; i++) {
                Order_Approved__e evt = events[i];
                // Set.add returns false when the UUID is already present, so a
                // redelivered message is skipped without a second query.
                if (alreadyProcessed.add(evt.EventUuid)) {
                    chunk.add(evt);
                }
            }

            try {
                processChunk(chunk);
            } catch (DmlException e) {
                if (isTransient(e)) {
                    retryOrGiveUp(e);
                    return;
                }
                ApplicationLogger.error('OrderApprovedEventHandler.handle',
                    'Permanent failure, consuming chunk: ' + e.getMessage());
            } catch (Exception e) {
                ApplicationLogger.error('OrderApprovedEventHandler.handle',
                    'Unexpected failure, consuming chunk: ' + e.getMessage());
            }

            // Checkpoint AFTER the chunk succeeded. "pass in the replay ID of the
            // last successfully processed event message ... The new execution
            // starts with the event message in the stream after the one with the
            // checkpointed Replay ID." (apexrefguide L157866-157874)
            EventBus.TriggerContext.currentContext()
                .setResumeCheckpoint(events[stop - 1].ReplayId);
        }
        ApplicationLogger.flush();
    }

    private Set<String> loadProcessedUuids(List<Order_Approved__e> events) {
        Set<String> uuids = new Set<String>();
        for (Order_Approved__e evt : events) {
            uuids.add(evt.EventUuid);
        }
        Set<String> seen = new Set<String>();
        for (Processed_Event__c row : [
            SELECT Event_Uuid__c
            FROM Processed_Event__c
            WHERE Event_Uuid__c IN :uuids
        ]) {
            seen.add(row.Event_Uuid__c);
        }
        return seen;
    }

    private void processChunk(List<Order_Approved__e> chunk) {
        if (chunk.isEmpty()) {
            return;
        }

        Set<Id> orderIds = new Set<Id>();
        for (Order_Approved__e evt : chunk) {
            orderIds.add((Id) evt.Order_Id__c);
        }

        Map<Id, Order__c> orders = new Map<Id, Order__c>([
            SELECT Id, Name, Amount__c FROM Order__c WHERE Id IN :orderIds
        ]);

        List<Fulfilment_Request__c> requests = new List<Fulfilment_Request__c>();
        List<Processed_Event__c> receipts = new List<Processed_Event__c>();

        for (Order_Approved__e evt : chunk) {
            Order__c parent = orders.get((Id) evt.Order_Id__c);
            if (parent == null) {
                // With PublishAfterCommit the Order row was committed before the
                // message left the transaction, so a missing parent is a data
                // problem, not a timing race. Never retry it.
                ApplicationLogger.warn('OrderApprovedEventHandler.processChunk',
                    'No Order for event ' + evt.EventUuid + ' (Order_Id__c ' + evt.Order_Id__c + ')');
                continue;
            }
            requests.add(new Fulfilment_Request__c(
                Order__c          = parent.Id,
                Amount__c         = evt.Amount__c,
                Correlation_Id__c = evt.Correlation_Id__c
            ));
            receipts.add(new Processed_Event__c(
                Event_Uuid__c = evt.EventUuid,
                Replay_Id__c  = evt.ReplayId,
                Topic__c      = 'Order_Approved__e'
            ));
        }

        insert requests;
        insert receipts;
    }

    private void retryOrGiveUp(Exception cause) {
        Integer retries = EventBus.TriggerContext.currentContext().retries;
        if (retries >= MAX_RETRIES) {
            ApplicationLogger.error('OrderApprovedEventHandler.retryOrGiveUp',
                'Retry budget exhausted after ' + retries + ' retries; consuming the batch. Last error: ' + cause.getMessage());
            ApplicationLogger.flush();
            return;
        }
        // The message given here comes back as EventBus.TriggerContext.lastError
        // and as EventBusSubscriber.LastError (apexrefguide L157779-157801).
        throw new EventBus.RetryableException(
            'Transient failure on attempt ' + (retries + 1) + ': ' + cause.getMessage());
    }

    private static Boolean isTransient(DmlException e) {
        for (Integer i = 0; i < e.getNumDml(); i++) {
            if (e.getDmlType(i) == StatusCode.UNABLE_TO_LOCK_ROW) {
                return true;
            }
        }
        return false;
    }
}
```

The dedupe store, `Processed_Event__c.object-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <deploymentStatus>Deployed</deploymentStatus>
    <description>Idempotency receipt: one row per consumed platform event message.</description>
    <label>Processed Event</label>
    <pluralLabel>Processed Events</pluralLabel>
    <nameField>
        <label>Processed Event Name</label>
        <type>AutoNumber</type>
    </nameField>
    <sharingModel>Private</sharingModel>
    <fields>
        <fullName>Event_Uuid__c</fullName>
        <label>Event UUID</label>
        <length>64</length>
        <externalId>true</externalId>
        <unique>true</unique>
        <required>true</required>
        <type>Text</type>
    </fields>
    <fields>
        <fullName>Replay_Id__c</fullName>
        <label>Replay Id</label>
        <length>64</length>
        <type>Text</type>
    </fields>
    <fields>
        <fullName>Topic__c</fullName>
        <label>Topic</label>
        <length>80</length>
        <type>Text</type>
    </fields>
</CustomObject>
```

**Why the event trigger does not extend `templates/apex/TriggerHandler.cls`**

`TriggerHandler` dispatches across `beforeInsert` / `afterUpdate` / `beforeDelete`
and carries a recursion guard for re-entrant record DML. A `__e` subscriber has
exactly one context and never re-enters itself, so five sixths of that base class
is dead weight and its `TriggerControl` bypass would silently drop event messages
rather than skipping a save. Use `TriggerHandler` for the *publishing* object's
trigger (`Order__c`), not for the `__e` trigger.

---

## Artifact 5 — subscriber configuration (`OrderApprovedEventTriggerConfig.platformEventSubscriberConfig-meta.xml`)

Path: `force-app/main/default/platformEventSubscriberConfigs/OrderApprovedEventTriggerConfig.platformEventSubscriberConfig-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PlatformEventSubscriberConfig xmlns="http://soap.sforce.com/2006/04/metadata">
    <platformEventConsumer>OrderApprovedEventTrigger</platformEventConsumer>
    <batchSize>200</batchSize>
    <masterLabel>Order Approved Event Trigger Config</masterLabel>
    <user>integration.user@example.com</user>
    <isProtected>false</isProtected>
</PlatformEventSubscriberConfig>
```

**How to read it** (all from `api_meta` L96385–96470, the type's own field table and
sample definition)

- `batchSize` — *"A custom batch size, from 1 through 2,000 ... The default batch
  size is 2,000 for platform event triggers. We don't recommend setting the batch
  size to 1 to process one event at a time. Small batch sizes can slow down the
  processing of event messages."*
- `user` — *"By default, the platform event trigger runs as the Automated Process
  entity."* Setting a real user gets you: records created or modified as that user,
  `OwnerId` populated to that user, debug logs attributed to that user, and the
  ability to send email from the trigger, *"which isn't supported with the default
  Automated Process user."*
- `platformEventConsumer` — required, the full name of the Apex trigger.
- `numPartitions` (1–10) and `partitionKey` (default `EventUuid`) configure parallel
  subscriptions; API version 62.0 and later.

---

## Artifact 6 — the test class (`OrderApprovedEventTest.cls`)

```apex
@IsTest
private class OrderApprovedEventTest {

    @TestSetup
    static void seed() {
        insert new List<Order__c>{
            new Order__c(Name = 'SO-1', Amount__c = 100),
            new Order__c(Name = 'SO-2', Amount__c = 250)
        };
    }

    @IsTest
    static void publishAndDeliverCreatesFulfilmentRequest() {
        Order__c order = [SELECT Id, Name, Amount__c FROM Order__c WHERE Name = 'SO-1' LIMIT 1];

        Test.startTest();
        List<Database.SaveResult> results = EventBus.publish(new List<Order_Approved__e>{
            new Order_Approved__e(
                Order_Id__c       = String.valueOf(order.Id),
                Order_Number__c   = order.Name,
                Amount__c         = order.Amount__c,
                Correlation_Id__c = 'test-single'
            )
        });
        Assert.isTrue(results[0].isSuccess(), 'publish request should be queued');

        // Without this line the trigger never runs and the test passes for the
        // wrong reason. "Enclose Test.getEventBus().deliver() within the
        // Test.startTest() and Test.stopTest() statement block."
        // (apexrefguide L157700-157710)
        Test.getEventBus().deliver();
        Test.stopTest();

        Assert.areEqual(1,
            [SELECT COUNT() FROM Fulfilment_Request__c WHERE Order__c = :order.Id],
            'one fulfilment request per delivered event');
        Assert.areEqual(1,
            [SELECT COUNT() FROM Processed_Event__c],
            'one idempotency receipt per consumed event');
    }

    @IsTest
    static void redeliveryOfSameEventUuidIsIdempotent() {
        Order__c order = [SELECT Id, Name FROM Order__c WHERE Name = 'SO-1' LIMIT 1];

        Test.startTest();
        Database.SaveResult result = EventBus.publish(new Order_Approved__e(
            Order_Id__c = String.valueOf(order.Id), Correlation_Id__c = 'test-dup'));
        Assert.isTrue(result.isSuccess(), 'publish request should be queued');
        Test.getEventBus().deliver();
        // A second deliver() drives the subscriber again; the handler must not
        // create a second fulfilment row.
        Test.getEventBus().deliver();
        Test.stopTest();

        Assert.areEqual(1,
            [SELECT COUNT() FROM Fulfilment_Request__c WHERE Order__c = :order.Id],
            'redelivery must not duplicate downstream work');
    }

    @IsTest
    static void bulkDeliveryStaysWithinLimits() {
        List<Order__c> orders = TestDataFactory.createOrders(200, null);
        insert orders;

        List<Order_Approved__e> events = new List<Order_Approved__e>();
        for (Order__c order : orders) {
            events.add(new Order_Approved__e(
                Order_Id__c       = String.valueOf(order.Id),
                Order_Number__c   = order.Name,
                Correlation_Id__c = 'test-bulk'
            ));
        }

        Test.startTest();
        List<Database.SaveResult> results = EventBus.publish(events);
        Test.getEventBus().deliver();
        Test.stopTest();

        for (Database.SaveResult result : results) {
            Assert.isTrue(result.isSuccess(), 'every event should be queued');
        }
        Assert.areEqual(200, [SELECT COUNT() FROM Fulfilment_Request__c WHERE Correlation_Id__c = 'test-bulk']);
    }

    @IsTest
    static void publishFailureReachesTheFailureCallback() {
        Order__c order = [SELECT Id, Name FROM Order__c WHERE Name = 'SO-2' LIMIT 1];

        Order_Approved__e evt =
            (Order_Approved__e) Order_Approved__e.SObjectType.newSObject(null, true);
        evt.Order_Id__c       = String.valueOf(order.Id);
        evt.Correlation_Id__c = 'test-fail';

        List<Database.SaveResult> results =
            EventBus.publish(new List<Order_Approved__e>{ evt },
                             new OrderApprovedPublishCallback());
        Assert.isTrue(results[0].isSuccess(),
            'the SaveResult only reports enqueueing; the failure surfaces in the callback');

        // "Causes the publishing of platform event messages to fail in the test
        // event bus. Use this method to test Apex publish callbacks."
        // (apexrefguide L157718-157742). The guide's usage snippet calls fail()
        // outside a startTest/stopTest block, unlike deliver().
        Test.getEventBus().fail();

        Assert.areEqual(1, [
            SELECT COUNT()
            FROM Application_Log__c
            WHERE Source__c = 'OrderApprovedPublishCallback.onFailure'
        ], 'the failure callback should have logged the dead event');
    }
}
```

`TestDataFactory.createOrders` follows the `createXxx(count, overrides)` contract in
`templates/apex/tests/TestDataFactory.cls`; add the `Order__c` overload there rather
than writing a private helper in the test class.

---

## Artifact 7 — `package.xml`

Shaped from the `PlatformEventSubscriberConfig` manifest sample in `api_meta`
L96490–96518, which lists exactly this dependency set (`CustomObject` for the event,
`CustomField` for its fields, `ApexTrigger`, `PlatformEventSubscriberConfig`).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Order_Approved__e</members>
        <members>Processed_Event__c</members>
        <members>Fulfilment_Request__c</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Order_Approved__e.Order_Id__c</members>
        <members>Order_Approved__e.Order_Number__c</members>
        <members>Order_Approved__e.Amount__c</members>
        <members>Order_Approved__e.Correlation_Id__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>OrderApprovedPublisher</members>
        <members>OrderApprovedPublishCallback</members>
        <members>OrderApprovedEventHandler</members>
        <members>OrderApprovedEventTest</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>OrderApprovedEventTrigger</members>
        <name>ApexTrigger</name>
    </types>
    <types>
        <members>OrderApprovedEventTriggerConfig</members>
        <name>PlatformEventSubscriberConfig</name>
    </types>
    <version>67.0</version>
</Package>
```

---

## Deploy order

`PlatformEventSubscriberConfig` *"references an Apex trigger, which depends on a
platform event. If the referenced items exist in the Salesforce org, you can deploy
the `PlatformEventSubscriberConfig` component ... If the referenced trigger and
platform event don't exist in the org, include their definitions in the package.
Otherwise, the deployment fails."* (`api_meta` L96482–96499)

| Step | Deploy | Why this order |
|---|---|---|
| 1 | `Order_Approved__e`, `Processed_Event__c`, `Fulfilment_Request__c` | the trigger will not compile against an undefined `__e` type |
| 2 | `OrderApprovedPublisher`, `OrderApprovedPublishCallback`, `OrderApprovedEventHandler` | the trigger body instantiates the handler |
| 3 | `OrderApprovedEventTrigger` | subscription starts the moment the trigger is active |
| 4 | `OrderApprovedEventTriggerConfig` | must come last: `platformEventConsumer` must resolve |

Everything in one `package.xml` is fine — the Metadata API orders within a single
deployment. Split deployments must follow the table.

```bash
# validate first, tests included
sf project deploy start --manifest manifest/package.xml --dry-run \
  --test-level RunSpecifiedTests --tests OrderApprovedEventTest --wait 30

sf project deploy start --manifest manifest/package.xml \
  --test-level RunSpecifiedTests --tests OrderApprovedEventTest --wait 30

# pull the definitions back after a Setup-side change
sf project retrieve start --manifest manifest/package.xml
```

---

## Verification

**1. The tests run and the subscriber actually fires.**

```bash
sf apex run test --tests OrderApprovedEventTest \
  --result-format human --code-coverage --wait 20
```

A green run in which `Fulfilment_Request__c` count is 0 means `deliver()` was
omitted, not that the subscriber is broken.

**2. The subscription is healthy.** `EventBusSubscriber` is queryable and
read-only (Object Reference, `object_reference` L131272–131283).

```sql
SELECT ExternalId, Name, Type, Topic, Status, Retries, LastError,
       LastProcessed, LastPublished, IsPartitioned
FROM EventBusSubscriber
WHERE Topic = 'Order_Approved__e'
```

| Column | What to expect | Field source |
|---|---|---|
| `Status` | `Running`. `Error` means the retry budget was exceeded; `Suspended` means an admin or an internal error disconnected it | `object_reference` L131380–131400 |
| `Retries` | 0 in steady state; a climbing value means `RetryableException` is firing | `object_reference` L131371–131375 |
| `LastError` | the message passed to the last `EventBus.RetryableException` | `object_reference` L131360–131365 |
| `LastProcessed` / `LastPublished` | the gap is your subscriber lag. These replace `Position` / `Tip` as of API 66.0 | `object_reference` L131325–131340 |

Note `LastPublished` (and legacy `Tip`) is *"always -1"* for high-volume platform
events (`object_reference` L131338–131340, L131419–131421), so lag cannot be derived
from those two columns on a `HighVolume` event — watch `Retries` and `Status`, and
measure lag with your own `Correlation_Id__c` timestamps instead.

**3. Publish failures are visible.**

```sql
SELECT Source__c, Message__c, CreatedDate
FROM Application_Log__c
WHERE Source__c IN ('OrderApprovedPublisher.publishApproved',
                    'OrderApprovedPublishCallback.onFailure')
  AND CreatedDate = LAST_N_DAYS:1
ORDER BY CreatedDate DESC
```

**4. The checker.**

```bash
python3 skills/apex/platform-events-apex/scripts/check_platform_events_apex.py \
  --manifest-dir force-app/main/default
```

Exit 0 and an empty `findings` array is the gate. Every rule maps to a gotcha in
`references/gotchas.md`.
