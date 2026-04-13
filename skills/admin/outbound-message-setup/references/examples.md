# Examples — Outbound Message Setup

## Example 1: External System Receiving Duplicate Messages

**Context:** A middleware platform is receiving Outbound Messages from Salesforce when Opportunities reach "Closed Won." The middleware processes the messages correctly. After a few days, the middleware logs show the same Opportunity message arriving hundreds of times over a 24-hour period.

**Problem:** The middleware returns HTTP 200 with a JSON body confirming receipt: `{"status": "received", "id": "OP-12345"}`. Salesforce treats this as a failed delivery because the response body is not a SOAP acknowledgment. It retries every few minutes for 24 hours, delivering the same message approximately 200+ times.

**Solution:**

The middleware endpoint must return an HTTP 200 response with the following SOAP body:

```xml
<soapenv:Envelope 
  xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <notifications xmlns="http://soap.sforce.com/2005/09/outbound">
      <Ack>true</Ack>
    </notifications>
  </soapenv:Body>
</soapenv:Envelope>
```

The Content-Type header should be `text/xml; charset=UTF-8`.

After updating the middleware to return this response, Salesforce marks the message as Delivered after the first successful delivery. No more duplicates.

**Why it works:** Outbound Message delivery confirmation requires a SOAP acknowledgment in the specific Salesforce outbound namespace. HTTP 200 alone is not confirmation — only the `<Ack>true</Ack>` in the correct namespace signals successful receipt.

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

**Why it works:** Manual requeue resets the 24-hour window, giving additional time for the endpoint to recover. Always check the Pending queue proactively for integrations with known maintenance windows.

---

## Anti-Pattern: Configuring Outbound Messages for Flow-Triggered Events

**What practitioners do:** A new integration requirement specifies that a notification should be sent to an external system when a Flow completes a specific step. The admin attempts to create an Outbound Message as a Flow Action.

**What goes wrong:** Outbound Messages are not available as Flow Actions. They are exclusively Workflow Rule actions. The Outbound Message option does not appear in the Flow Action selector.

**Correct approach:** For Flow-triggered external notifications, use Platform Events. Create a Platform Event object, publish it from a Flow "Create Records" action (Platform Events are records), and configure the external system to subscribe to the Salesforce Streaming API (CometD) to receive the event. Platform Events support JSON payloads and are Flow/Apex native. Outbound Messages are legacy Workflow Rule-only and are not being extended to Flow.
