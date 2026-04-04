# Examples — Pause Elements and Wait Events

## Example 1: Multi-Day Approval Reminder with Automatic Escalation

**Context:** A professional services org has a custom approval object (`Approval_Request__c`). When a record is created the assigned approver receives an initial notification. If no action is taken within 3 days, a reminder is sent. If still unanswered after 7 days, an escalation email goes to the approver's manager. The process should stop as soon as the approver acts.

**Problem:** A scheduled path on a record-triggered flow can handle one future time offset per path but cannot carry variable state across multiple windows. Wiring three separate record-triggered flows together creates deployment complexity, makes debugging difficult, and still cannot stop cleanly when the approver acts mid-interval.

**Solution:**

Flow design (auto-launched flow, triggered when `Approval_Request__c` is created):

```text
[Start: Record-Triggered, Approval_Request__c, After Save, Created]
  |
[Action: Send Initial Email Alert to Approver]
  |
[Pause Element: "Wait for Approver Response or Timeout"]
  ├── Wait Event 1 — Alarm
  │     Base date: {!$Record.CreatedDate}
  │     Offset: 3 Days
  │     Output: Send Reminder Email → loop back to Pause Element
  │
  ├── Wait Event 2 — Alarm
  │     Base date: {!$Record.CreatedDate}
  │     Offset: 7 Days
  │     Output: Send Escalation Email to Manager → End
  │
  └── Wait Event 3 — Platform Event: ApprovalDecision__e
        Resume condition: RequestId__c = {!$Record.Id}
        Output: [Decision: Status = Approved / Rejected] → End
```

To publish a test event for manual verification:

```apex
// Developer Console: anonymous Apex to simulate an approval decision
ApprovalDecision__e evt = new ApprovalDecision__e(
    RequestId__c = 'a0X000000EXAMPLE',
    Decision__c  = 'Approved'
);
Database.SaveResult sr = EventBus.publish(evt);
System.debug('Published: ' + sr.isSuccess());
```

**Why it works:** The Pause element's first-wins race means the Platform Event path exits the loop the moment the approver acts, regardless of which alarm interval is currently active. Variable state (the record ID used in resume conditions) is preserved across the pause boundary because the interview is persisted to the database, not discarded.

---

## Example 2: Integration Callback — Flow Waits for External Confirmation

**Context:** An order management flow calls an external fulfillment API via an Apex action. The API call returns a correlation ID synchronously but the actual fulfillment confirmation arrives asynchronously minutes or hours later as a platform event (`FulfillmentCallback__e`). The flow must wait for the callback before updating the order status.

**Problem:** Without a Pause element, developers often resort to polling: a scheduled Apex job or a scheduled flow that repeatedly queries a staging object populated by the callback webhook. Polling introduces latency (up to the polling interval), wastes query limits, and requires maintaining a separate coordination record.

**Solution:**

```text
[Start: Auto-Launched, invoked from Order record-triggered flow]
  |
[Apex Action: CallFulfillmentAPI]
    Inputs:  {!orderId}
    Outputs: {!correlationId}   ← unique ID returned by fulfillment API
  |
[Pause Element: "Wait for Fulfillment Callback or Timeout"]
  ├── Wait Event 1 — Platform Event: FulfillmentCallback__e
  │     Resume conditions:
  │       CorrelationId__c = {!correlationId}    ← exact match to this order
  │     Stores event in record variable: {!callbackEvent}
  │     Output:
  │       [Decision] {!callbackEvent.Status__c} = 'SUCCESS'
  │         → Update Order.Status = 'Fulfilled'
  │       else
  │         → Update Order.Status = 'Fulfillment Failed', Log Error
  │
  └── Wait Event 2 — Alarm (timeout watchdog)
        Base date: {!$Flow.CurrentDateTime}
        Offset: 24 Hours
        Output: Update Order.Status = 'Timeout - Manual Review', Send Alert
```

Resume condition detail — the `CorrelationId__c` filter is critical. Without it, every `FulfillmentCallback__e` event published in the org (for any order) would attempt to resume this interview. With it, only the callback carrying the exact ID issued for this specific order resumes this specific interview.

**Why it works:** The interview is suspended at zero cost to CPU and query limits. When the fulfillment system publishes the callback event, Salesforce delivers it to the subscribed interview within seconds. The correlation ID filter ensures no cross-contamination between concurrent interviews. The 24-hour alarm acts as a safety net, preventing permanently stranded interviews if the external system never calls back.

---

## Example 3: Multi-Step Onboarding Flow Waiting for Document Upload

**Context:** A customer onboarding flow sends a document request email and then needs to pause until a customer uploads required documents (signaled via a `DocumentReceived__e` platform event from an external document management system).

**Problem:** Building this as polling logic inside a scheduled flow requires the scheduled flow to repeatedly check whether the document has arrived and creates coordination complexity when the document arrives between polling windows.

**Solution:**

```text
[Start: Auto-Launched]
  |
[Send Email: Document Request with Upload Link]
  |
[Pause Element: "Await Document Upload"]
  ├── Wait Event 1 — Platform Event: DocumentReceived__e
  │     Resume conditions:
  │       AccountId__c  = {!accountId}
  │       DocType__c    = 'ONBOARDING_PACKAGE'
  │     Output: Update Onboarding_Status__c = 'Documents Received'
  │             → Continue onboarding steps
  │
  └── Wait Event 2 — Alarm (reminder)
        Base date: {!$Flow.CurrentDateTime}
        Offset: 3 Days
        Output: Send Reminder Email → loop back to Pause Element
                (loop max: checked by Decision element counting iterations)
```

**Why it works:** Two resume conditions (`AccountId__c` and `DocType__c`) together ensure the resume is unambiguous — only the document upload event for this specific account and document type resumes this interview, not uploads for other accounts or other document types.

---

## Anti-Pattern: Leaving Platform Event Resume Conditions Blank

**What practitioners do:** In Flow Builder, they add a Platform Event wait event and leave the "Resume Conditions" section empty, assuming that filtering will happen elsewhere (perhaps in a Decision element after resume).

**What goes wrong:** With no resume conditions, every published message of that platform event type attempts to resume every paused flow interview subscribed to it. In an org with 50 concurrent paused interviews and 100 inbound platform event messages per day, this generates 5,000 spurious resume attempts daily. Interviews resume on the wrong event, record variables are populated with unrelated data, and downstream DML operations corrupt records.

**Correct approach:** Always add at least one resume condition that uniquely links the event message to the specific interview. The most common pattern is a record ID field on the event that matches the record the interview is operating on:

```text
Resume condition: OrderId__c = {!$Record.Id}
```

If the platform event does not carry a unique identifier for the flow interview context, design the event schema to include one before implementing the Pause element.
