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

**Why it happens:** LLMs apply fault-handling advice uniformly across all flow types. Before-save record-triggered flows do not support fault connectors — they have no DML elements and run in the same transaction as the triggering save.

**Correct pattern:**

Before-save flows fail by adding an error to `$Record` using an Assignment element with a custom error message formula:

```
[Decision: Is data valid?]
  No --> [Assignment: Add error to $Record] --> (Flow ends — record save is blocked)
  Yes --> [Assignment: Set field values on $Record]
```

Fault connectors are only available in after-save and autolaunched flows that contain DML.

**Detection hint:** Advice to add fault connectors in a flow described as "before-save" or "fast field update."

---

## Anti-Pattern 4: Not considering rollback scope in after-save flows

**What the LLM generates:**

```
If the Create Task element fails, the fault connector will catch the error
and the original record save will still succeed.
```

**Why it happens:** LLMs assume fault connectors isolate errors. In after-save record-triggered flows, an unhandled fault rolls back the entire transaction, including the triggering record save. Fault connectors prevent the rollback only if the fault path completes without re-throwing.

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

A separate Platform Event-triggered flow then sends the email. Platform Events are committed independently and survive rollbacks.

**Detection hint:** `Send Email` action inside a fault path of a record-triggered after-save flow.

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
