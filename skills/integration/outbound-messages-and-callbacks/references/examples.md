# Examples — Outbound Messages and Callbacks

## Example 1: Configuring a SOAP Endpoint to Correctly Acknowledge Outbound Messages

**Context:** A financial services company uses a Workflow Rule on the `Opportunity` object to notify a loan origination system whenever an opportunity reaches the `Closed Won` stage. The loan origination system is Java-based and was implemented by a team unfamiliar with the Salesforce SOAP acknowledgment contract.

**Problem:** After go-live, the delivery queue in Setup showed every message in a perpetual retry state. The loan origination system's logs showed it was receiving the same Opportunity record data hundreds of times per day. The system was returning HTTP 200 to every request, but it was returning a plain JSON body: `{"status": "received"}`. Salesforce treated every response as a delivery failure because the response body did not match the expected SOAP acknowledgment structure. The result was a 24-hour retry storm for every triggered message.

**Solution:**

The Java endpoint needed to return a SOAP 1.1 response body regardless of the content type of the inbound request processing. The minimum correct implementation:

```java
// Java servlet example — return SOAP acknowledgment after processing
response.setContentType("text/xml; charset=utf-8");
response.setStatus(200);
PrintWriter out = response.getWriter();
out.println("<?xml version=\"1.0\" encoding=\"UTF-8\"?>");
out.println("<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\">");
out.println("  <soapenv:Body>");
out.println("    <notificationsResponse xmlns=\"http://soap.sforce.com/2005/09/outbound\">");
out.println("      <Ack>true</Ack>");
out.println("    </notificationsResponse>");
out.println("  </soapenv:Body>");
out.println("</soapenv:Envelope>");
out.flush();
```

Additionally, the endpoint added idempotency by storing a hash of `{opportunityId}:{stageName}:{amount}` in a processing log table. Before processing, it checks whether that hash already exists — if so, it returns `<Ack>true</Ack>` immediately without reprocessing.

**Why it works:** Salesforce's delivery confirmation logic checks both the HTTP status code and the response body structure. Returning the exact SOAP namespace and `<Ack>true</Ack>` tells Salesforce the message was received and processed successfully, ending the retry cycle. The idempotency layer ensures that legitimate duplicate deliveries (which occur even under normal operation) do not create duplicate loan records.

---

## Example 2: Session ID Callback to Fetch Related Data Not Available in the Outbound Message Payload

**Context:** A manufacturing company uses a Workflow Rule on the `Case` object to notify a field service dispatch system when a case reaches `Escalated` status. The dispatch system needs the customer's shipping address, the account's assigned territory, and the list of open cases for the same account to determine dispatcher priority. None of these fields are on the Case object directly — they come from the related Account and from a SOQL query.

**Problem:** The Outbound Message field selector only allows fields on the Case object (and its directly selectable related fields). The dispatch system was receiving case data without the account information it needed to route the dispatch correctly, causing manual lookups that defeated the purpose of the automation.

**Solution:**

The Outbound Message was configured to send `CaseNumber`, `Subject`, `Status`, `AccountId`, and the `SessionId` (always included automatically). The dispatch system used a two-step callback:

Step 1 — Receive and parse the Outbound Message:

```python
# Python Flask endpoint example
from flask import Flask, request, Response
import xml.etree.ElementTree as ET
import requests

app = Flask(__name__)
SF_NAMESPACE = "http://soap.sforce.com/2005/09/outbound"
SF_API_VERSION = "v63.0"

@app.route("/case-escalation", methods=["POST"])
def handle_outbound_message():
    tree = ET.fromstring(request.data)
    ns = {"sf": SF_NAMESPACE}

    # Extract session ID and record ID from SOAP body
    session_id = tree.find(".//sf:SessionId", ns).text
    case_id = tree.find(".//sf:Id", ns).text
    account_id = tree.find(".//sf:AccountId", ns).text

    # Step 2 — Callback to Salesforce REST API for enriched data
    sf_instance = "https://myorg.my.salesforce.com"
    headers = {"Authorization": f"Bearer {session_id}"}

    account_data = requests.get(
        f"{sf_instance}/services/data/{SF_API_VERSION}/sobjects/Account/{account_id}"
        "?fields=BillingStreet,BillingCity,BillingState,Territory__c",
        headers=headers
    ).json()

    open_cases = requests.get(
        f"{sf_instance}/services/data/{SF_API_VERSION}/query"
        f"?q=SELECT+Id,Subject+FROM+Case+WHERE+AccountId='{account_id}'+AND+Status!='Closed'",
        headers=headers
    ).json()

    # Dispatch routing logic using enriched data
    dispatch_priority(case_id, account_data, open_cases["records"])

    # Return SOAP acknowledgment
    ack = """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <notificationsResponse xmlns="http://soap.sforce.com/2005/09/outbound">
      <Ack>true</Ack>
    </notificationsResponse>
  </soapenv:Body>
</soapenv:Envelope>"""
    return Response(ack, content_type="text/xml; charset=utf-8", status=200)
```

**Why it works:** The session ID in every Outbound Message payload is a fully valid Salesforce API session token. Using it as a Bearer token in standard REST API calls gives the external system on-demand access to any data the triggering user can see — related objects, child records, and aggregate queries — without requiring a separate Connected App, OAuth flow, or named credential. The callback completes in milliseconds, well within the session validity window.

---

## Example 3: Compensating Batch Recovery After 24-Hour Retry Window Expiry

**Context:** A logistics company's Outbound Message integration with a shipping carrier API was silently failing for 36 hours due to an expired TLS certificate on the carrier's endpoint. When the certificate was renewed and the endpoint came back online, the Salesforce delivery queue showed 4,200 permanently failed messages — all had exceeded the 24-hour retry window.

**Problem:** Manually requeueing 4,200 individual messages from Setup was impractical and would take hours of click-work. The company needed a way to re-trigger the integration for all affected shipment records within a reasonable time window.

**Solution:**

An Apex batch class was written to perform a no-op field update on the affected records, which re-fired the Workflow Rule and generated fresh Outbound Message delivery attempts:

```apex
// Apex Batch — re-fires Workflow Rule by updating a tracking field
// Prerequisite: add a helper field Resync_Timestamp__c (DateTime) to the object
// and ensure the Workflow Rule criteria fires on field change or "every time"

global class RequeueShipmentBatch implements Database.Batchable<SObject> {

    private final DateTime failureStart;
    private final DateTime failureEnd;

    global RequeueShipmentBatch(DateTime start, DateTime end) {
        this.failureStart = start;
        this.failureEnd = end;
    }

    global Database.QueryLocator start(Database.BatchableContext ctx) {
        // Query records whose Workflow Rule fired during the outage window
        return Database.getQueryLocator([
            SELECT Id, Resync_Timestamp__c
            FROM Shipment__c
            WHERE Status__c = 'Ready_to_Ship'
              AND LastModifiedDate >= :failureStart
              AND LastModifiedDate <= :failureEnd
        ]);
    }

    global void execute(Database.BatchableContext ctx, List<Shipment__c> scope) {
        for (Shipment__c s : scope) {
            s.Resync_Timestamp__c = System.now(); // touches the record to re-fire WFR
        }
        update scope;
    }

    global void finish(Database.BatchableContext ctx) {}
}

// Execute from Anonymous Apex:
// DateTime outageStart = DateTime.newInstance(2026, 3, 15, 8, 0, 0);
// DateTime outageEnd   = DateTime.newInstance(2026, 3, 17, 8, 0, 0);
// Database.executeBatch(new RequeueShipmentBatch(outageStart, outageEnd), 200);
```

**Why it works:** Touching the record re-evaluates all active Workflow Rules against it. Because the Workflow Rule is configured to fire "every time" the criteria are met (not just "when created or edited to meet"), it fires again and generates a new Outbound Message delivery attempt with a fresh 24-hour window. This avoids clicking through thousands of records in Setup and recovers the integration without manual intervention at scale.

---

## Anti-Pattern: Assuming Outbound Messages Can Be Triggered from Flow or Apex

**What practitioners do:** A developer needs a notification to fire when a record is updated by an Apex trigger (not a Workflow Rule). They configure an Outbound Message on the object and expect it to fire. Some practitioners try to "call" an Outbound Message from a Flow using a Record-Triggered Flow with a Send Email or Apex action, not realizing that Outbound Messages are not a callable action type.

**What goes wrong:** The Outbound Message never fires because there is no Workflow Rule evaluating the triggering condition. The developer may spend hours debugging the endpoint, the delivery queue, and the network connectivity before realizing the Outbound Message simply has no trigger attached to it. In some cases, practitioners create a Workflow Rule with a criteria that overlaps the Apex logic, which causes double-processing when both the Apex code and the Workflow Rule fire on the same record change.

**Correct approach:** Outbound Messages are attached exclusively to Workflow Rule actions. If the triggering automation is a Flow, use a Platform Event instead: publish the Platform Event from the Flow using the Publish Platform Event action, and configure the external system to subscribe via the Pub/Sub API or CometD. If the triggering automation is Apex and the external endpoint is SOAP, make a synchronous Apex callout or use a Queueable to make the callout asynchronously — Outbound Messages cannot be invoked programmatically from Apex.
