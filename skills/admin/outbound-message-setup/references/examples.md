# Examples — Outbound Message Setup

## Example 1: External System Receiving Duplicate Messages

**Context:** A middleware platform is receiving Outbound Messages from Salesforce when Opportunities reach "Closed Won." The middleware processes the messages correctly. After a few days, the middleware logs show the same Opportunity message arriving hundreds of times over a 24-hour period.

**Problem:** The middleware returns HTTP 200 with a JSON body confirming receipt: `{"status": "received", "id": "OP-12345"}`. Salesforce treats this as a failed delivery because the response body is not a SOAP acknowledgment. It retries every few minutes for 24 hours, delivering the same message approximately 200+ times.

**Solution:**

The middleware endpoint must return an HTTP 200 response with the following SOAP body:

```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <notificationsResponse xmlns="http://soap.sforce.com/2005/09/outbound">
      <Ack>true</Ack>
    </notificationsResponse>
  </soapenv:Body>
</soapenv:Envelope>
```

The Content-Type header should be `text/xml; charset=UTF-8`.

After updating the middleware to return this response, Salesforce marks the message as Delivered after the first successful delivery. No more duplicates.

**Why it works:** `notificationsResponse` is "the schema for sending an acknowledgment (ack) response to Salesforce" and its entire content is one boolean, `<element name="Ack" type="xsd:boolean"/>` ([Understanding Outbound Messaging](https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_om_outboundmessaging_understanding.htm)). `Ack` is a value in the response body; HTTP 200 is the transport reporting that the bytes arrived. The middleware was answering a different question than the one Salesforce asked.

**The duplicate that this fix does not remove.** Redelivery is normal even for a correct listener, so idempotency is the listener's job, and the guide names the key to use: each `Notification` carries the object `Id` alongside the `sObject`, and "use the object ID to track redelivery attempts of notifications you've already processed."

There is a second, quieter duplicate-handling trap in the same envelope. `Notification` is declared `maxOccurs="100"`, so one message can carry up to 100 records — but the response carries one `Ack` for the whole message:

```
notifications                       notificationsResponse
├── OrganizationId                  └── Ack : boolean      <- ONE, for the whole message
├── ActionId
├── SessionId (nillable)
├── EnterpriseUrl
├── PartnerUrl
└── Notification  x1..100
    ├── Id                          <- the idempotency key
    └── sObject (selected fields)
```

A middleware that loops the notifications, fails on record 61, and returns `Ack=true` anyway has told Salesforce all 100 were handled. The other 40 are gone, and the delivery status page records a success. Persist the processed object IDs *before* acknowledging, and return `Ack=false` on partial failure so the whole message redelivers — see gotcha 10.

---

## Example 2: Monitoring and Requeuing Stuck Outbound Messages

**Context:** An integration team is notified by an external partner that their system has not received any Salesforce notifications for the past 6 hours. The partner's endpoint was temporarily down for maintenance.

**Problem:** Outbound Messages sent during the maintenance window are stuck in the retry queue. With exponential backoff, the messages are now retrying every 60 minutes. If 18 hours have already passed, the messages will be permanently dropped in 6 hours.

**Solution:**

1. Navigate to Setup > Process Automation > Outbound Messages.
2. Click the "Pending" tab — view messages waiting for delivery.
3. Select all messages for the affected endpoint.
4. Click "Retry" — this resets the 24-hour delivery window for the selected messages, giving the integration team time to resolve the endpoint issue.
5. After the partner endpoint is restored and tested, confirm the messages move to the "Delivered" tab.

If messages were already dropped (past the 24-hour window), re-trigger by re-saving the affected records or by running a batch process that updates a dummy field to trigger the Workflow Rule again.

UNVERIFIED (2026-09-05): the 24-hour window, the retry cadence and the requeue-resets-the-window behaviour are documented on help.salesforce.com, which cannot be fetched. Re-confirm the cadence before scheduling around it. What is grounded is the durability lever below.

**The durability question this outage exposes.** The platform's own answer to "normal delivery fails" is `useDeadLetterQueue`, which "is only available for organizations with dead letter queue permissions turned on" (api_meta.txt L140368–140371). Before the next outage, settle which of the two states the org is in, and make the answer visible in source rather than in someone's memory. That is a metadata question, so it has a deterministic check:

```console
$ python3 skills/admin/outbound-message-setup/scripts/check_outbound_message_setup.py \
    --manifest-dir force-app/main/default
WARN: Account.workflow-meta.xml outboundMessages[Notify_Partner_Of_Order]: No <useDeadLetterQueue>.
  Undelivered messages have no landing place. The element only works in orgs with dead letter queue
  permissions turned on (api_meta.txt L140368-140371) -- either set it, or record the reconciliation
  plan that replaces it.
WARN: Account.workflow-meta.xml outboundMessages[Notify_Partner_Of_Order]: <includeSessionId> is true:
  the payload carries a live Salesforce session for the integration user (api_meta.txt L140354-140357).
Scanned 1 workflow file(s): 0 error(s), 2 warning(s).
```

Two warnings, two decisions to record. The first is the one this outage is about; the second is the one the next security review will be about. Run the checker with `--strict` in CI once both are settled, so a later edit that drops `<useDeadLetterQueue>` fails the build instead of resurfacing during an incident.

**Why it works:** Manual requeue resets the delivery window, giving additional time for the endpoint to recover. Always check the Pending queue proactively for integrations with known maintenance windows — and treat the queue check as a stopgap for a durability gap the metadata can make explicit.

---

## Example 3: An Outbound Message With No Workflow Rule

**Context:** An admin is cleaning up an Account object. `workflows/Account.workflow` contains an outbound message named `Notify_ERP_Of_Tier_Rejection` that no rule in the file references. The object has no active workflow rules at all. The admin deletes the whole `.workflow` file from source and deploys.

**Problem:** The ERP stops receiving rejection notifications, and the approval process that sent them starts failing to deploy between orgs. The outbound message was never orphaned — outbound messages are "workflow **and approval** actions" (api_meta.txt L140313–140315), and an approval process references one exactly the way a workflow rule does:

```xml
<!-- approvalProcesses/Account.Tier_Upgrade.approvalProcess-meta.xml (excerpt) -->
<finalRejectionActions>
    <action>
        <name>Notify_ERP_Of_Tier_Rejection</name>
        <type>OutboundMessage</type>
    </action>
</finalRejectionActions>
```

The definition, however, has only one home: the `outboundMessages` array of `workflows/<Object>.workflow` (L139931). Deleting the workflow file deleted the approval process's action target. Nothing in the approval process file carries the endpoint URL, the field list or the integration user, so grepping the approval process for any of them finds nothing.

**Solution:**

1. Restore the `outboundMessages` element to `workflows/Account.workflow` — the rest of the file may legitimately be empty of rules.
2. Before deleting anything from a `.workflow` file again, grep the approval processes for the `fullName`. The reference is a plain string and nothing enforces it from the workflow side:

```bash
grep -rn "Notify_ERP_Of_Tier_Rejection" force-app/main/default/approvalProcesses/
```

3. Deploy `Workflow` and `ApprovalProcess` in the same manifest, so the action name always resolves:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Account</members>
        <name>Workflow</name>
    </types>
    <types>
        <members>Account.Tier_Upgrade</members>
        <name>ApprovalProcess</name>
    </types>
    <version>62.0</version>
</Package>
```

**Why it works:** The dependency runs one way — the approval process names a string the workflow file must define — and only the manifest can express it. Naming approval-only messages so they read as intentional (`Notify_ERP_Of_Tier_Rejection`, not `Notify_ERP`) makes the next cleanup pass hesitate before it deletes.

---

## Anti-Pattern: Configuring Outbound Messages for Flow-Triggered Events

**What practitioners do:** A new integration requirement specifies that a notification should be sent to an external system when a Flow completes a specific step. The admin attempts to create an Outbound Message as a Flow Action.

**What goes wrong:** Outbound Messages are not available as Flow Actions. They are exclusively Workflow Rule actions. The Outbound Message option does not appear in the Flow Action selector.

**Correct approach:** For Flow-triggered external notifications, use Platform Events. Create a Platform Event object, publish it from a Flow "Create Records" action (Platform Events are records), and configure the external system to subscribe to the Salesforce Streaming API (CometD) to receive the event. Platform Events support JSON payloads and are Flow/Apex native. Outbound Messages are Workflow Rule and approval actions only (api_meta.txt L140313–140315, L139961) and are not being extended to Flow — `FlowAction` is a separate `WorkflowActionType` value whose "pilot program for flow trigger workflow actions is closed" (L139962–139966).
