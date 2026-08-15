# Examples — Flow and Platform Events

Worked examples for the two Flow-side mechanics: publishing an event with a
Create Records element, and consuming one with a platform-event-triggered flow.

The canonical publisher shape — event field design, `eventId__c` idempotency key,
fault path, and the after-save requirement — lives in
[`templates/flow/PlatformEvent_Publisher_Flow.md`](../../../../templates/flow/PlatformEvent_Publisher_Flow.md).
Start there and specialize it; the examples below cover the parts that template
deliberately leaves to the skill: the subscriber's metadata shape, batch and
running-user configuration, allocation arithmetic, and what failure looks like
from the Flow side.

Deeper semantics — publish-after-commit guarantees, subscriber idempotency
design, fan-out failure domains — belong to `flow/flow-platform-events-integration`.

---

## Example 1: The Publish Element, and What It Costs

**Context:** An after-save record-triggered flow on Case publishes
`Case_Status_Changed__e` whenever Status changes.

**Problem:** Authors treat the publish as free. It is not: which governor budget
it draws from depends on a setting that lives on the event definition, not on
the flow.

**Solution:**

Publishing from Flow is a Create Records element whose `object` is the event's
API name. There is no dedicated "Publish Event" element.

```xml
<recordCreates>
    <name>Publish_Case_Status_Changed</name>
    <label>Publish Case Status Changed</label>
    <locationX>440</locationX>
    <locationY>276</locationY>
    <faultConnector>
        <targetReference>Log_Publish_Failure</targetReference>
    </faultConnector>
    <inputAssignments>
        <field>caseId__c</field>
        <value>
            <elementReference>$Record.Id</elementReference>
        </value>
    </inputAssignments>
    <inputAssignments>
        <field>newStatus__c</field>
        <value>
            <elementReference>$Record.Status</elementReference>
        </value>
    </inputAssignments>
    <inputAssignments>
        <field>oldStatus__c</field>
        <value>
            <elementReference>$Record__Prior.Status</elementReference>
        </value>
    </inputAssignments>
    <inputAssignments>
        <field>eventId__c</field>
        <value>
            <elementReference>varEventId</elementReference>
        </value>
    </inputAssignments>
    <object>Case_Status_Changed__e</object>
    <storeOutputAutomatically>false</storeOutputAutomatically>
</recordCreates>
```

Set `storeOutputAutomatically` to `false`. A publish does not return a record Id
you can use — the event has no queryable row — so storing the output buys
nothing and misleads the next reader into thinking they can reference it.

**Why it works, and what it costs:** The publish behaviour set on the event
definition decides the accounting:

| Publish Behavior | Delivered when | Governor budget consumed |
|---|---|---|
| Publish After Commit | Only if the transaction commits | Counts as one DML statement against the 150-DML limit |
| Publish Immediately | As soon as the element runs, even if the transaction later rolls back | A separate allocation of 150 publish-immediate calls |

That table is the whole reason a publish inside a loop is dangerous under
Publish After Commit and merely expensive under Publish Immediately: the first
shares the same 150-DML budget as every other write in the transaction.

**Before-save flows cannot publish.** Before-save record-triggered flows cannot
perform DML at all, and a publish is DML. Publishing is an after-save operation.

---

## Example 2: The Subscriber — A Platform-Event-Triggered Flow

**Context:** `Case_Status_Changed__e` needs to create a follow-up Task.

**Problem:** Authors reach for a record-triggered flow because the event "looks
like a record." An event is not a record and does not appear in the
record-trigger object picker; the flow is a separate trigger type with different
`$Record` semantics and a different running user.

**Solution:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <description>Creates a follow-up Task when a Case status change event arrives.</description>
    <environments>Default</environments>
    <interviewLabel>Case Status Changed Subscriber {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Case Status Changed Subscriber</label>
    <processType>AutoLaunchedFlow</processType>
    <runInMode>DefaultMode</runInMode>
    <start>
        <locationX>50</locationX>
        <locationY>50</locationY>
        <connector>
            <targetReference>Create_Follow_Up_Task</targetReference>
        </connector>
        <object>Case_Status_Changed__e</object>
        <triggerType>PlatformEvent</triggerType>
    </start>
    <status>Active</status>

    <recordCreates>
        <name>Create_Follow_Up_Task</name>
        <label>Create Follow Up Task</label>
        <locationX>176</locationX>
        <locationY>50</locationY>
        <faultConnector>
            <targetReference>Log_Subscriber_Failure</targetReference>
        </faultConnector>
        <inputAssignments>
            <field>Subject</field>
            <value>
                <stringValue>Confirm status change with customer</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>WhatId</field>
            <value>
                <elementReference>$Record.caseId__c</elementReference>
            </value>
        </inputAssignments>
        <object>Task</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordCreates>
</Flow>
```

**Why it works:** `<triggerType>PlatformEvent</triggerType>` with the event's API
name as `<object>` is what makes this a subscriber. Inside the flow, `$Record`
holds the event message's field values — not a Case. To touch the Case you have
to Get Records on `Case` filtered by `$Record.caseId__c`; there is no relationship
to traverse, because the event carries an Id in a Text field, not a lookup.

Three properties of this flow that differ from a record-triggered flow:

- **It runs asynchronously, in its own transaction.** The publishing
  transaction has already finished. Nothing this flow does can roll the
  publisher back.
- **It runs as Automated Process by default.** Since Spring '24 you can instead
  configure event-triggered flows to run as the Workflow User, which is the fix
  when the subscriber needs record access that Automated Process does not have.
- **It is batched.** See Example 3.

---

## Example 3: Batch Size — Wrong vs Right

**Wrong (the assumption):** "One event message, one flow interview, so my
governor budget is per event."

**Right (the behaviour):** A platform-event-triggered flow processes a *batch*
of event messages. The maximum batch size is 200, and every interview in that
batch shares one transaction's governor budget. A subscriber that issues one
Get Records and one Update per event is fine at one event and is at 200 SOQL
queries — twice the synchronous ceiling of 100 — at a full batch.

This is the single most common way a platform-event subscriber that "worked in
testing" fails in production: testing published one event at a time, and
production published two hundred.

**The fix in the flow, not in the event:**

Aggregate before you act. Rather than Get-and-Update per event, the subscriber
should collect the Ids from the batch, run one Get Records with an `In`
filter, and one Update Records against the resulting collection. That is
ordinary Flow bulkification — see `flow/flow-bulkification` — applied to a
trigger source most authors do not think of as bulk.

**The fix in the configuration:** platform-event-triggered flows expose a
maximum batch size, capped at 200. Lowering it trades throughput for governor
headroom: smaller batches are less likely to breach limits and slower to drain
a backlog. Lower it when the subscriber's per-event work is irreducibly
expensive; bulkify when it is not. Lowering the batch size is a mitigation, not
a fix — it moves the cliff rather than removing it.

Note the Apex asymmetry when you are reading code and flows side by side: the
default batch for a platform-event *Apex trigger* is 2,000 event messages
(configurable through `PlatformEventSubscriberConfig`), against 200 for object
triggers and 200 as the flow maximum. A team that ported a subscriber from Apex
to Flow, or the reverse, has changed its batch size by an order of magnitude
without touching a line of logic.

---

## Example 4: Sizing Against the Allocations Before You Build

**Context:** A team proposes replacing a nightly integration with a
per-record Platform Event published from a record-triggered flow on Contact.
Contact sees roughly 40,000 updates on a heavy day, concentrated between 09:00
and 11:00 when the upstream sync runs.

**Problem:** The daily total looks comfortable. The hourly peak is what breaks.

**Solution:** Do the arithmetic against the published allocations before
building.

| Allocation | Value (Enterprise) | Applies to |
|---|---|---|
| Event publishing, per hour | 250,000 | All publishing methods combined |
| Event delivery, per 24 hours | 25,000 | Pub/Sub API, CometD, empApi, and event relays — **not** Apex triggers, flows, or Process Builder |
| Event message size | 1 MB max | Per event |
| Retention in the event bus | 72 hours | High-volume events |
| Platform event definitions | 50 | Per org |
| Flow / Process Builder subscriptions per event | 4,000 total, 2,000 active | Per event definition |

Developer Edition publishes at 50,000 per hour; Performance and Unlimited match
Enterprise's 250,000. Check your edition rather than the number you remember.

Two conclusions that fall out of this table and are routinely missed:

1. **The delivery allocation does not constrain Flow subscribers.** Flows, Apex
   triggers, and Process Builder draw on the *publishing* allocation, not the
   delivery one. The 25,000-per-day delivery figure people cite as a blocker
   applies to external subscribers over Pub/Sub API, CometD, empApi, and event
   relays. An internal Flow-to-Flow pattern is bounded by publishing, not
   delivery.
2. **Peak, not average, is the constraint.** 40,000 events across two hours is
   20,000 per hour against a 250,000 ceiling — fine. The same 40,000 released by
   a single bulk data load in one minute is a different question, and the answer
   depends on how the load is chunked, not on the daily total.

**Where to watch it in the org:** Setup → Quick Find `Platform Events` →
**Platform Events**, and the Event Monitoring / usage entitlement views for
published and delivered counts.

---

## Example 5: The Failure You Will Not See

**Context:** A subscriber flow started throwing after a validation rule was
added to Task. Nobody noticed for four days.

**Problem:** The publisher's users saw nothing, because the publisher's
transaction had already committed and the subscriber runs later in its own
transaction. The subscriber runs as Automated Process, so there is no user on
screen. And the flow error email went to whoever last modified the subscriber
flow.

**Solution:** Instrument the subscriber as if nobody is watching, because
nobody is.

1. Route flow error emails off the last modifier: Setup → **Process Automation
   Settings** → **Send Process or Flow Error Email to** → **Apex Exception Email
   Recipients**. See `flow/flow-interview-debugging` for the full treatment.
2. Fault-connector every DML and Action element in the subscriber onto a log
   record that captures `$Flow.FaultMessage`, `$Flow.InterviewGuid`, and the
   event's own correlation field (`$Record.eventId__c`). The event correlation
   field is what lets you answer "which published events never landed" — the
   interview GUID alone cannot, because it is generated on the subscriber side.
3. Alert on a *rate*, not on individual failures. At-least-once delivery means
   occasional duplicates and occasional retries are normal; a step change in
   volume is the signal.

**Why it works:** It converts an invisible class of failure into a countable
one. The correlation field is the load-bearing part: without it, a subscriber
failure and a publish failure look identical from the log.

---

## Anti-Pattern: Publishing Inside a Loop

**What practitioners do:** Loop a collection and publish one event per
iteration, mirroring how they would write it in Apex without bulkification.

**What goes wrong:** Under Publish After Commit, each publish is a DML
statement. Two hundred iterations is 200 DML statements against a limit of 150,
and the interview dies partway through — having already published some events.
The downstream state is now partially notified, which is worse than not notified
at all, because the subscriber-side reconciliation has no way to know the set
was truncated.

**Correct approach:** Build a collection of event records in the loop with an
Assignment, then publish the whole collection with one Create Records element
after the loop. One DML statement, one publish, no partial fan-out. This is the
same shape as any other bulkified Flow write — the only special thing about
events is that the failure mode is silent.

---

## Anti-Pattern: Using an Event to Talk to Yourself in the Same Transaction

**What practitioners do:** Publish an event and expect the subscriber's work to
be visible before the publishing flow's next element runs, or expect a
subscriber failure to roll the publisher back.

**What goes wrong:** Neither happens. The subscriber runs in a separate,
later transaction. The publisher has already committed and returned to the
user. A subscriber that throws produces no signal on the publisher's side at
all — no error email to the publishing user, no rollback, nothing.

**Correct approach:** If you need the result of the work before continuing,
you do not need an event; you need a subflow or invocable Apex in the same
transaction. Events are for work whose failure the publisher is deliberately
not responsible for. If you find yourself designing compensating logic to
recover from subscriber failure inside the publisher, the decision to use an
event was wrong — re-run
`standards/decision-trees/automation-selection.md` and
`standards/decision-trees/async-selection.md`.

---

## Anti-Pattern: One Fat Event for Everything

**What practitioners do:** Define `Business_Event__e` with a `type__c` field and
a JSON blob, then have every subscriber branch on `type__c` and ignore the
messages meant for someone else.

**What goes wrong:** Every subscriber is woken for every message, so a
low-frequency subscriber inherits the highest-frequency publisher's volume, and
each of them burns a batch of governor budget on a Decision that discards the
payload. Publishing volume is charged once, but subscriber cost multiplies by
the number of flows. Schema changes for one consumer force a review of all of
them, and the org's cap on platform event definitions — 50 on Enterprise — was
never the binding constraint people imagined it was.

**Correct approach:** One event definition per meaningful business fact, with
typed fields. If you genuinely have more distinct facts than your edition's
definition allocation allows, that is a signal to consolidate at the domain
level (one event per aggregate, carrying a small enum of state transitions),
not to collapse everything into a single envelope.
