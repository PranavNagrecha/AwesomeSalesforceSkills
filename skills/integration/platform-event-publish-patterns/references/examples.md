# Examples — Platform Event Publish Patterns

Two worked scenarios and one anti-pattern showing the canonical
Apex publish shape and the outbox alternative for business-critical
events. Each example chooses PublishBehavior deliberately based on
the event's semantics.

---

## Example 1: Bulk-safe publish from a record-triggered context with full result handling

**Context:** When `Order__c` records transition to `Status__c =
'Submitted'`, an external Order Management System needs to be
notified. The notification is delivered via Platform Event so that
multiple downstream subscribers (the warehouse system, the
analytics pipeline, an Agentforce action that emails the customer)
can react. A bulk import can submit up to 200 orders in one
transaction.

**Problem:** The naive
`EventBus.publish(new Order_Submitted__e(...))` inside a `for` loop
issues 200 separate publish calls, consumes 200 DML statements
(yes — publish counts against the DML limit), and the platform
caps at 150. Worse, a partial failure (e.g., one publish hits
EVENT_PUBLISH_FAILED_DUE_TO_DLQ) gives back a `Database.SaveResult`
that the developer hasn't checked, so the failure is silent.

**Solution:**

```apex
public with sharing class OrderSubmittedPublisher {

    public static void publishForSubmittedOrders(
        List<Order__c> newOrders,
        Map<Id, Order__c> oldMap
    ) {
        List<Order_Submitted__e> events = new List<Order_Submitted__e>();
        for (Order__c o : newOrders) {
            Order__c prior = oldMap?.get(o.Id);
            Boolean justSubmitted =
                o.Status__c == 'Submitted'
                && (prior == null || prior.Status__c != 'Submitted');
            if (!justSubmitted) continue;

            events.add(new Order_Submitted__e(
                Order_Id__c        = o.Id,
                Customer_Id__c     = o.AccountId,
                Total_Amount__c    = o.TotalAmount__c,
                Submitted_At__c    = Datetime.now(),
                Source_System__c   = 'salesforce-order-ui',
                Schema_Version__c  = '1'
            ));
        }
        if (events.isEmpty()) return;

        List<Database.SaveResult> results = EventBus.publish(events);
        List<Map<String, Object>> failures = new List<Map<String, Object>>();
        for (Integer i = 0; i < results.size(); i++) {
            Database.SaveResult sr = results[i];
            if (!sr.isSuccess()) {
                failures.add(new Map<String, Object>{
                    'orderId'   => events[i].Order_Id__c,
                    'errorCode' => sr.getErrors()[0].getStatusCode().name(),
                    'message'   => sr.getErrors()[0].getMessage()
                });
            }
        }
        if (!failures.isEmpty()) {
            ApplicationLogger.error(
                'OrderSubmittedPublisher',
                failures.size() + ' Order_Submitted__e publishes failed',
                JSON.serialize(failures)
            );
        }
    }
}
```

**Why it works:** One bulk `EventBus.publish(events)` call is 1
DML against the per-transaction limit, not 200. The
`Database.SaveResult` array is parallel to the input events, so a
positional loop maps failures back to source records — essential
for retry pipelines. The `Schema_Version__c` field is included so
subscribers can version-handle payload changes without breaking
backwards compatibility (see `well-architected.md` for the
versioning rationale).

The event's metadata is configured with `PublishBehavior:
PublishAfterCommit` (the safer default — set in the Platform Event
object's setup screen, NOT in this code). That means: if the
parent transaction rolls back, the event publishes never reach
subscribers. Combined with the trigger context (events queued
from a `Order__c` trigger handler), this gives exactly-once-on-
success-or-zero-on-failure semantics.

---

## Example 2: Outbox pattern for business-critical events

**Context:** Every customer signup event MUST reach the marketing
automation system — losing one means the customer doesn't receive
the welcome email. Direct `EventBus.publish` has a non-zero failure
rate (event allocation exhausted, transient platform issues, DLQ
overflows). The business requires durable, retryable publishes.

**Problem:** With direct publish, a `SaveResult.isSuccess() ==
false` result represents a permanently lost event — there is no
built-in retry. Even when retry is layered on, code that retries
inside the same transaction may itself fail; code that retries
asynchronously needs to know which events to retry, which
requires persisting them first.

**Solution:** Write the event payload to a custom object on the
"hot path," then have a scheduled Queueable publish from the table
with retry logic.

```apex
// Hot path: just record the intent, do not publish.
public with sharing class CustomerSignupPublisher {
    public static void recordSignupIntent(List<Account> newAccounts) {
        List<Event_Outbox__c> rows = new List<Event_Outbox__c>();
        for (Account a : newAccounts) {
            rows.add(new Event_Outbox__c(
                Event_Type__c     = 'Customer_Signup__e',
                Payload_JSON__c   = JSON.serialize(new Map<String,Object>{
                    'accountId'    => a.Id,
                    'email'        => a.PersonEmail,
                    'signedUpAt'   => Datetime.now()
                }),
                Status__c         = 'Pending',
                Attempt_Count__c  = 0
            ));
        }
        insert rows;
    }
}

// Cold path: drained by a scheduled Queueable every 1-5 minutes.
public class OutboxDrainQueueable implements Queueable, Database.AllowsCallouts {
    public void execute(QueueableContext ctx) {
        List<Event_Outbox__c> batch = [
            SELECT Id, Event_Type__c, Payload_JSON__c, Attempt_Count__c
              FROM Event_Outbox__c
             WHERE Status__c = 'Pending'
               AND Attempt_Count__c < 5
             ORDER BY CreatedDate
             LIMIT 200
            FOR UPDATE
        ];
        if (batch.isEmpty()) return;

        List<Customer_Signup__e> events = new List<Customer_Signup__e>();
        for (Event_Outbox__c row : batch) {
            Map<String,Object> payload =
                (Map<String,Object>) JSON.deserializeUntyped(row.Payload_JSON__c);
            events.add(new Customer_Signup__e(
                Account_Id__c = (String) payload.get('accountId'),
                Email__c      = (String) payload.get('email'),
                Signed_Up_At__c = (Datetime) JSON.deserialize(
                    JSON.serialize(payload.get('signedUpAt')), Datetime.class)
            ));
        }

        List<Database.SaveResult> results = EventBus.publish(events);
        for (Integer i = 0; i < results.size(); i++) {
            if (results[i].isSuccess()) {
                batch[i].Status__c = 'Published';
                batch[i].Published_At__c = Datetime.now();
            } else {
                batch[i].Attempt_Count__c += 1;
                batch[i].Last_Error__c = results[i].getErrors()[0].getMessage();
                if (batch[i].Attempt_Count__c >= 5) {
                    batch[i].Status__c = 'Failed';
                }
            }
        }
        update batch;
    }
}
```

**Why it works:** The hot path is a single `INSERT` — fastest possible
operation, fully transactional with the originating DML. If the
parent transaction rolls back, the outbox row rolls back too, so
there's no "ghost event waiting to fire." The cold-path Queueable
runs on its own cadence (scheduled every 1–5 minutes), picks up
pending rows, publishes them, and updates `Status__c` based on the
result. Failed events are retried up to 5 times; permanent
failures are surfaced to ops via an `Outbox_Failures__c` report
that runs against `Status__c = 'Failed'`. This pattern is the
Salesforce-side equivalent of the [Outbox pattern from microservices
architecture](https://microservices.io/patterns/data/transactional-outbox.html),
adapted for Apex transaction semantics.

The `FOR UPDATE` clause on the SOQL is essential — without it,
two concurrent Queueable runs (e.g., the scheduled run and a
manually triggered one) could both pull the same batch and
double-publish.

---

## Anti-Pattern: Publishing from a `@future` method to "ensure delivery"

**What practitioners do:**

```apex
public class OrderService {
    public static void submit(Order__c order) {
        update order;
        // "Make sure the event publishes even if this transaction is rolled back later"
        publishAsync(order.Id);
    }
    @future
    static void publishAsync(Id orderId) {
        EventBus.publish(new Order_Submitted__e(Order_Id__c = orderId));
    }
}
```

**What goes wrong:** Several things, each painful:

1. **The `@future` doesn't run if the outer transaction rolls
   back.** The `@future` call is enqueued at the time of invocation,
   but it executes only after the transaction commits. So this
   pattern doesn't actually deliver the "fire even on rollback"
   guarantee the developer wanted — it gives the same semantics as
   `PublishAfterCommit` but with extra latency and a separate
   governor budget burned.
2. **`@future` invocations don't see the latest DML.** The future
   re-queries `Order__c` by Id to get fresh data; if the trigger
   that called `submit()` rolled back the update, the future sees
   the old `Status__c` and publishes a misleading event.
3. **`@future` adds latency** (typically seconds, sometimes
   minutes under platform load) between the user's action and the
   downstream subscriber's reaction. For UX-sensitive flows
   (e.g., a "thank you, your order will be processed shortly"
   page that depends on the subscriber having reacted), this
   latency is visible.
4. **`@future` can't be chained** — if the publish itself fails
   transiently, the future can't enqueue another future to retry.
   You need a Queueable for that.

**Correct approach:** Use `PublishImmediately` if the semantics
really are "fire even if the transaction rolls back" (most
telemetry / audit events). Use `PublishAfterCommit` (the default)
if the semantics are "fire only on commit" (most business events).
For "must deliver with retry," use the outbox pattern from
Example 2 — it's more code but gives genuine at-least-once
delivery with bounded latency. `@future` is the wrong tool for
event publishing in every scenario I've seen in production code
review.
