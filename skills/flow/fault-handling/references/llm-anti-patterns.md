# LLM Anti-Patterns — Fault Handling

Common mistakes AI coding assistants make when generating or advising on Salesforce Flow fault handling.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Adding fault connectors only to the first DML element

**What the LLM generates:**

```
[Get Records] --> [Update Records (has fault connector)] --> [Create Task] --> [Send Email]
                                                              ^^ No fault path    ^^ No fault path
```

**Why it happens:** LLMs add a fault connector to the most obvious failure point and skip the rest. Every DML element (Create, Update, Delete) and external callout can fail and needs its own fault path.

**Correct pattern:**

```
[Get Records] --> [Update Records] --fault--> [Log Error + Screen/Email]
                       |
                       v
                  [Create Task] --fault--> [Log Error + Screen/Email]
                       |
                       v
                  [Send Email] --fault--> [Log Error + Screen/Email]
```

Every DML and callout element should have a fault connector, even if they all route to the same error-handling subflow.

**Detection hint:** Flow with multiple DML elements but fault connectors on only one of them.

---

## Anti-Pattern 2: Using $Flow.FaultMessage directly in a screen shown to end users

**What the LLM generates:**

```
[Screen Element]
  Display Text: "Error: {!$Flow.FaultMessage}"
```

**Why it happens:** LLMs use `$Flow.FaultMessage` because it is the built-in error variable. But raw fault messages often contain technical details (SOQL errors, field-level security messages, Apex exception traces) that confuse end users.

**Correct pattern:**

```
[Assignment: Set userFriendlyError = "We could not save your changes. Please try again or contact support."]
[Assignment: Set technicalError = $Flow.FaultMessage]
[Screen: Display {!userFriendlyError}]
[Create Record: Log technicalError to Error_Log__c]
```

Show a user-friendly message on screen. Log the technical details for admin diagnosis.

**Detection hint:** `$Flow.FaultMessage` referenced directly in a Screen element Display Text.

---

## Anti-Pattern 3: Advising fault handling for before-save record-triggered flows

**What the LLM generates:**

```
Add a fault connector to the Assignment element in your before-save flow.
```

**Why it happens:** LLMs apply fault-handling advice uniformly across all flow types. A before-save (Fast Field Updates) flow contains no DML elements — it mutates `$Record` in memory before the save — so there is no failing element for a fault connector to hang off.

**Correct pattern:**

Use the **Custom Error** element. It is a real Flow Builder element (metadata: `customErrors` on the `Flow` type) that "shows an error message of your design to the user, and rolls back the current transaction" — which in a before-save flow means the triggering save is blocked and the user sees your message.

```
[Decision: Is data valid?]
  No  --> [Custom Error: "Close Date can't be in the past"] --> (save blocked, txn rolled back)
  Yes --> [Assignment: Set field values on $Record]
```

The Custom Error element can target the whole record (a page-level error window) or a specific field (an inline field error), which is what makes it a replacement for a validation rule rather than just a logging device.

**There is no "add an error to `$Record` via an Assignment element" mechanism.** Assignment sets variable and field values; it has no error-message capability and no custom-error formula. Generated instructions of the form "use an Assignment element with a custom error message formula" describe a Flow Builder that does not exist — the admin follows them, finds no such option, and loses the afternoon.

Also do not state that fault connectors exist only in "after-save and autolaunched flows that contain DML" — fault paths attach to any element that can fail at run time (Get Records, DML, Action, Apex, Subflow), which includes screen flows. The accurate constraint is narrower: a before-save flow has no such elements to attach one to.

**Detection hint:** in flow guidance, grep for `Assignment` within three lines of `error` — Assignment has no error semantics, so the pairing is always wrong. Separately, flag any before-save / "fast field update" guidance that mentions "fault connector" or "fault path", and any guidance that blocks a save without naming the Custom Error element.

---

## Anti-Pattern 4: Not considering rollback scope in after-save flows

**What the LLM generates:**

```
If the Create Task element fails, the fault connector will catch the error
and the original record save will still succeed.
```

**Why it happens:** LLMs assume fault connectors isolate errors. After-save record-triggered flows execute at save-order step 14, and the record is not durable until step 19, "Commits all DML operations to the database" (`apexdev.txt` L15470, L15478). Everything between those steps is one transaction, so an interview that ends on an unhandled fault takes the triggering save down with it. Fault connectors prevent that only if the fault path itself completes.

**Correct pattern:**

```
[Update Records] --fault--> [Log Error to Error_Log__c]
                                    |
                                    v
                             [Flow ends normally — no re-throw]
```

The fault path must complete successfully (e.g., log the error) to prevent the entire transaction from rolling back. If the fault path also fails, the original save is rolled back.

**Detection hint:** Documentation claiming fault connectors "isolate" the error without mentioning that the fault path must itself succeed.

---

## Anti-Pattern 5: Sending email alerts from within the fault path of a record-triggered flow

**What the LLM generates:**

```
[Update Records] --fault--> [Send Email Alert: Notify admin of failure]
```

**Why it happens:** Email is the first notification mechanism LLMs suggest. But if the fault path is inside a record-triggered flow and the transaction rolls back, the email send is also rolled back. Emails sent via `Send Email` action participate in the transaction.

**Correct pattern:**

Use a Platform Event to send the notification outside the transaction:

```
[Update Records] --fault--> [Create Records: Publish Error_Event__e]
```

A separate Platform Event-triggered flow then sends the email.

Platform events survive the rollback **only when the event definition's `publishBehavior`
is `PublishImmediately`** — "published when the publish call executes, regardless of
whether the transaction succeeds" — as against `PublishAfterCommit`, where "if the
transaction fails, the event message isn't published" (`api_meta.txt` L42206–L42229,
API 46.0 and later). `PublishImmediately` is the default when the field is omitted, but it
is a field on the `CustomObject` metadata for the event, not on the flow, so a reviewer
checking only the flow cannot see it. Generated advice that says "use a platform event, it
survives rollback" without naming `publishBehavior` is right by luck.

Note also *why* the email is lost: sending email is post-commit work, step 20 of the save
order, after the commit at step 19 (`apexdev.txt` L15478–L15487). A rolled-back transaction
never reaches step 19.

**Detection hint:** `Send Email` action inside a fault path of a record-triggered after-save flow; or a platform-event notification pattern whose write-up never mentions `publishBehavior`.

---

## Anti-Pattern 6: Ignoring bulk failure scenarios in fault path design

**What the LLM generates:**

```
The fault path logs the error to a custom object and notifies the admin.
```

**Why it happens:** LLMs design fault handling for single-record scenarios. When a data loader updates 200 records and one fails, the fault fires 200 times if the flow is not bulkified, potentially hitting email or DML limits in the fault path itself.

**Correct pattern:**

Design fault paths to be bulk-safe:
- Use collection variables to accumulate errors across the batch
- Perform a single DML at the end to log all errors
- Send one summary notification rather than one per failure
- Consider using a scheduled flow to process error logs instead of real-time notifications

**Detection hint:** Fault path that creates records or sends emails without considering that it may execute 200 times in a single transaction.

---

## Anti-Pattern 7: Telling the reader to put a fault connector on a Subflow element

**What the LLM generates:**

```
Add a fault connector to every DML, Action, and Subflow element in the flow.
```

Or, in XML:

```xml
<subflows>
    <name>Call_Routing_Child</name>
    <flowName>Resolve_Case_Routing</flowName>
    <faultConnector>
        <targetReference>Log_Subflow_Failure</targetReference>
    </faultConnector>
</subflows>
```

**Why it happens:** "DML, Action and Subflow" reads like a natural group — all three hand
control somewhere and all three can fail — and the phrase appears verbatim in a lot of
community guidance. But `FlowSubflow`'s documented field list is `connector`, `flowName`,
`inputAssignments`, `outputAssignments`, `storeOutputAutomatically` (`api_meta.txt`
L72625–L72660). There is no `faultConnector`. The admin goes looking for a connector Flow
Builder never draws, and the generated XML does not match the schema.

**Correct pattern:**

Handle the failure inside the child flow, on the child's own fault-capable elements, and
return the outcome as a value the parent branches on:

```xml
<subflows>
    <name>Call_Routing_Child</name>
    <flowName>Resolve_Case_Routing</flowName>
    <connector>
        <targetReference>Check_Child_Outcome</targetReference>
    </connector>
    <outputAssignments>
        <assignToReference>childOutcome</assignToReference>
        <name>outcome</name>
    </outputAssignments>
</subflows>
```

The parent's Decision on `childOutcome` is the fault path. The same applies to
`FlowOrchestratedStage`, which *does* accept a `faultConnector` but whose documentation for
that field is the single word "Not used." (`api_meta.txt` L70803) — a connector that
deploys and never fires is worse than one that does not exist.

**Detection hint:** the literal string `faultConnector` inside a `<subflows>` block; or
prose that lists "DML, Action, and Subflow" as the elements needing fault connectors.
