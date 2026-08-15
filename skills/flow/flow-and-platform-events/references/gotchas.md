# Gotchas — Flow and Platform Events

Non-obvious platform behaviours that bite when Flow is on either end of the
event bus.

---

## Gotcha 1: A Platform-Event-Triggered Flow Is Batched, Up to 200 Messages

**What happens:** A subscriber flow that does one Get Records and one Update per
event works perfectly in testing and starts throwing `Too many SOQL queries: 101`
in production without any change to the flow.

**When it occurs:** As soon as the publisher emits events faster than the
subscriber drains them. Platform-event-triggered flows process a batch of event
messages — the maximum is 200 — and the whole batch shares one transaction's
governor budget. One query per event is 200 queries against a synchronous limit
of 100.

**How to avoid:** Bulkify the subscriber the way you would bulkify any
record-triggered flow: build a collection of Ids across the batch, one Get
Records with an `In` filter, one Update Records against the collection. Lowering
the flow's maximum batch size is a mitigation you reach for when the per-event
work is irreducibly expensive; it trades drain rate for headroom and moves the
cliff rather than removing it.

---

## Gotcha 2: The Apex Batch Size and the Flow Batch Size Differ by 10×

**What happens:** A subscriber is ported between an Apex trigger and a
platform-event-triggered flow and its per-transaction cost changes by an order
of magnitude, with no change in logic.

**When it occurs:** On every such port. The default batch for a platform-event
*Apex trigger* is 2,000 event messages — far larger than the 200 of an ordinary
object trigger — and configurable through `PlatformEventSubscriberConfig`. A
platform-event-triggered *flow* maxes out at 200.

**How to avoid:** Treat the batch size as part of the port, not an
implementation detail. Moving Apex → Flow makes each transaction ten times
smaller (more transactions, each safer). Moving Flow → Apex makes each ten times
bigger, and an Apex subscriber written against Flow's assumptions will breach
limits immediately unless `PlatformEventSubscriberConfig` is set.

---

## Gotcha 3: Publish Behaviour Decides Which Governor Budget You Spend

**What happens:** The same publish element is cheap in one org and blows the DML
limit in another. The flow is identical; the event definition is not.

**When it occurs:** Publish Behavior is a property of the platform event
definition, not of the flow. Under **Publish After Commit**, a publish counts as
one DML statement against the 150-statement per-transaction limit, shared with
every other write. Under **Publish Immediately**, publishes draw on a separate
allocation of 150 publish-immediate calls and are delivered even if the
transaction subsequently rolls back.

**How to avoid:** Read the event definition before reasoning about the flow's
budget. A publish inside a loop is fatal under After Commit (it competes with
the loop's other DML) and merely expensive under Immediately. Whichever it is,
build the collection in the loop and publish once after it.

---

## Gotcha 4: Before-Save Flows Cannot Publish

**What happens:** An author moves a publish into a before-save record-triggered
flow for speed and the element is not available, or the flow fails to save.

**When it occurs:** Always. Before-save record-triggered flows cannot perform
DML, and publishing an event is DML — the publish element is a Create Records on
the event object.

**How to avoid:** Publish from after-save. If the reason for wanting before-save
was performance, note that the publish is the expensive part and moving it
earlier would not have helped; if the reason was ordering, an event published
before the record commits is precisely the phantom-event case Publish After
Commit exists to prevent.

---

## Gotcha 5: `$Record` in a Subscriber Is the Event, Not the Record

**What happens:** An author writes `$Record.Status` in a subscriber flow and
gets nothing, or writes `$Record.Case__r.Subject` and cannot save the flow.

**When it occurs:** Always. In a platform-event-triggered flow, `$Record` holds
the event message's fields. Events carry Ids in Text fields, not lookups, so
there is no relationship to traverse and no cross-object dot notation available.

**How to avoid:** Get Records on the real object, filtered by the Id field the
event carried. And expect the record to have moved on: the subscriber runs
later, so the record's state at subscribe time may not match the state that
triggered the publish. If the subscriber's decision depends on the *change*,
the event has to carry the before and after values — the record cannot tell you
what it used to be.

---

## Gotcha 6: The Delivery Allocation Does Not Apply to Flows

**What happens:** A team abandons an internal Flow-to-Flow event design because
"we only get 25,000 deliveries a day and we have 40,000 records."

**When it occurs:** Whenever the delivery allocation is read as a global cap.
The event delivery allocation — 50,000 per 24 hours on Performance and
Unlimited, 25,000 on Enterprise, 10,000 on Developer — applies to Pub/Sub API,
CometD, empApi, and event relays. Apex triggers, flows, and Process Builder are
explicitly excluded; those subscribers consume the *publishing* allocation
instead.

**How to avoid:** Size internal subscribers against the publishing allocation —
250,000 events per hour on Enterprise, Performance, and Unlimited; 50,000 on
Developer — and reserve the delivery arithmetic for external consumers. Getting
this backwards has killed workable designs and waved through unworkable ones.

---

## Gotcha 7: There Is No Standard-Volume Choice Left to Make

**What happens:** Guidance says "use high-volume platform events if you expect
more than N per day," and the author goes looking for the setting.

**When it occurs:** On any org creating an event today. Event definitions
created at API version 45.0 and later are high-volume by default and
standard-volume events can no longer be defined; the remaining standard-volume
events are legacy definitions from API 44.0 and earlier, and Salesforce has
announced their retirement.

**How to avoid:** Drop the volume-type decision from the design entirely for new
events. The one place the distinction still matters is retention on legacy
definitions: high-volume messages are retained in the event bus for 72 hours,
legacy standard-volume for 24. If an old event's replay window seems half what
you expected, that is why — and the fix is to define a new high-volume event, not
to change a setting.

---

## Gotcha 8: The Subscriber's Failure Is Invisible From the Publisher

**What happens:** A subscriber has been failing for days. The publishing users
saw nothing. No error appeared on any record.

**When it occurs:** Always. The publisher's transaction commits and returns
before the subscriber runs. A subscriber exception produces no rollback of the
publisher, no error on the triggering record, and no notification to the
publishing user. The subscriber's own flow error email goes to whoever last
modified the *subscriber* flow — a different person from whoever owns the
business process.

**How to avoid:** Instrument the subscriber on the assumption that nobody is
watching. Route error emails to a monitored alias, fault-connector every DML and
Action element onto a log record, and include the event's own correlation field
on the log row. Without the correlation field you cannot distinguish "the event
never published" from "the event published and the subscriber dropped it".

---

## Gotcha 9: An Apex Subscriber That Exhausts Its Retries Stops Consuming Entirely

**What happens:** One poison message takes an entire Apex subscriber offline.
Events keep publishing; nothing processes them; the backlog ages out of the
72-hour retention window and is gone.

**When it occurs:** When an Apex platform-event trigger uses
`EventBus.RetryableException` and runs out of attempts. A trigger can execute up
to ten times in total — the initial run plus nine retries — and after the ninth
retry it moves to an error state and stops processing new events until the
trigger is fixed and saved. `EventBus.TriggerContext.currentContext().retries`
reports the current count, and the documentation advises keeping retries below
nine so you can handle exhaustion yourself.

**How to avoid:** This is Apex-side behaviour, but it is the failure mode a Flow
publisher inherits when the fan-out includes an Apex subscriber, so it belongs
in the publisher's risk assessment. Cap retries below the platform maximum, log
and skip a poison message rather than retrying it forever, and monitor for a
subscriber sitting in error state. `<!-- UNVERIFIED: whether a
platform-event-triggered *flow* has an equivalent retry-and-error-state model,
and what its retry count is, is not stated in the Apex retry documentation.
Salesforce documents flow retries separately under "Troubleshooting Flow
Retries"; do not assume the Apex numbers transfer. -->`

---

## Gotcha 10: Automated Process Is Not a User With Permissions You Can Reason About

**What happens:** A subscriber flow's Get Records returns nothing, or its Update
fails, for records the business owner can see perfectly well.

**When it occurs:** Platform-event-triggered flows run as Automated Process by
default. Automated Process has no profile and no permission set assignments, so
`$Permission.X` evaluates false for every X, sharing behaves differently from any
real user, and record access is not the access the process owner assumed.

**How to avoid:** Since Spring '24, event-triggered flows can be configured to
run as the Workflow User instead, which is the correct fix when the subscriber
genuinely needs a real user's record access. Do not gate subscriber logic on
`$Permission` — use a Custom Metadata feature flag, or carry the decision in the
event payload where the publisher (which did run as a real user) could evaluate
it.

---

## Gotcha 11: Retention Is 72 Hours and Replay Is Not a Flow Feature

**What happens:** A subscriber is disabled for a long weekend and the team plans
to "replay the missed events on Monday."

**When it occurs:** High-volume event messages are retained in the event bus for
72 hours. A long weekend plus a Monday morning is inside that window; a week is
not. And Flow has no replay affordance at all — replaying from a Replay Id
requires a Pub/Sub API or CometD client, which is an integration build, not a
flow.

**How to avoid:** Treat "we can replay it later" as false for any Flow-only
design. If the business genuinely needs recovery from a multi-day subscriber
outage, the durable record has to be a record in Salesforce that the subscriber
marks as processed — not the event bus. That design belongs to
`flow/flow-platform-events-integration` and
`integration/platform-events-integration`.

---

## Gotcha 12: Publishing Is at-Least-Once, So the Subscriber Must Tolerate a Repeat

**What happens:** A subscriber creates a Task per event. Occasionally two
identical Tasks appear.

**When it occurs:** Platform event delivery is at-least-once. A subscriber
transaction that fails partway and is retried can re-run work that already
committed elsewhere, and an Apex retry re-delivers the same batch.

**How to avoid:** Carry a deterministic correlation key on the event —
`templates/flow/PlatformEvent_Publisher_Flow.md` calls it `eventId__c` — and have
the subscriber check-then-act against a processed-events record before doing
anything with a side effect. The idempotency design itself is scoped to
`flow/flow-platform-events-integration`; what belongs here is knowing that the
Flow subscriber has no built-in dedupe and will happily do the work twice.
