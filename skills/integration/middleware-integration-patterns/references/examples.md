# Examples — Middleware Integration Patterns

## Example 1: ERP Order Sync Requiring Transformation — Choosing Between MuleSoft and Boomi

**Context:** A manufacturing company runs SAP S/4HANA as their ERP and Salesforce Sales Cloud as their CRM. When a sales order is created in Salesforce, it must be replicated to SAP as a purchase order, and the resulting SAP order confirmation number must be written back to the Salesforce Opportunity. The data model requires transformation: Salesforce Opportunity line items must be mapped to SAP BAPI call parameters, and the SAP RFC protocol must be translated to something Salesforce can respond to.

**Problem:** The integration team initially attempts to handle this with Apex callouts. They discover:
1. SAP RFC is not HTTP-accessible without an intermediate adapter — Apex cannot reach it.
2. The transformation from Salesforce Opportunity schema to SAP BAPI input structure involves 40+ field mappings with conditional logic.
3. The two-step write-back (SAP confirmation → Salesforce) cannot be handled in a single synchronous Apex transaction without blocking the user.

**Solution:**

The team evaluates MuleSoft Anypoint and Dell Boomi:

- **MuleSoft** provides a certified SAP Connector that speaks RFC natively, plus DataWeave for the 40-field transformation. The existing enterprise MuleSoft license covers the SAP Connector. API-led architecture puts the SAP interaction behind a System API.
- **Boomi** also provides an SAP connector and a low-code mapping canvas. If the team does not have a MuleSoft license, Boomi delivers faster time-to-value for this pattern at lower cost.

Selected approach (MuleSoft, existing license):

```
Salesforce Platform Event (OrderCreated) 
  → MuleSoft Pub/Sub subscriber 
  → DataWeave transform (Opportunity line items → SAP BAPI input) 
  → SAP System API (MuleSoft SAP Connector, RFC) 
  → SAP confirmation response 
  → DataWeave transform (confirmation number extraction) 
  → Salesforce REST API PATCH (Opportunity.SAP_Order_Number__c)
```

**Why it works:** The integration moves SAP RFC protocol conversion and complex transformation out of Salesforce's Apex runtime. The Pub/Sub subscriber decouples the write-back from the Salesforce transaction, eliminating the synchronous callout constraint. MuleSoft's DataWeave handles the 40-field transform concisely. The existing license justifies MuleSoft over Boomi here.

---

## Example 2: Real-Time vs Batch Decision — Workato Suitability for Salesforce-HubSpot Sync

**Context:** A mid-market SaaS company uses Salesforce for their sales team and HubSpot for marketing. They want to sync Contacts and Leads bidirectionally so that marketing engagement data (email opens, form fills) appears on the Salesforce Lead record, and Salesforce stage changes are reflected in HubSpot deal pipelines. The IT team is small and no dedicated integration developer is available.

**Problem:** The team evaluates three approaches:
1. Build native Salesforce-to-HubSpot sync using Apex callouts and HubSpot webhooks.
2. Use Workato, which the marketing team already licenses for other SaaS automations.
3. Procure MuleSoft for enterprise-grade iPaaS.

They discover that Workato's Salesforce trigger polls every 5 minutes minimum. For marketing engagement data (real-time notification when a prospect fills a demo form), 5-minute latency is acceptable. For the reverse direction — Salesforce stage change appearing in HubSpot — 5 minutes is also acceptable because sales reps update records throughout the day rather than in real time.

**Solution:**

Workato is selected because:
- Both sync directions tolerate 5-minute latency.
- The marketing team already owns the Workato license and has recipe-building skills.
- No protocol conversion, complex transformation, or durable queuing is required.
- MuleSoft would require an enterprise license, a Mule developer, and weeks of onboarding for a use case that Workato addresses in hours.

```
Workato Recipe 1 (HubSpot → Salesforce):
  Trigger: HubSpot form submission (webhook, real-time)
  Action 1: Search Salesforce Lead by email
  Action 2: If found → update Lead with HubSpot engagement data
            If not found → create new Lead

Workato Recipe 2 (Salesforce → HubSpot):
  Trigger: Salesforce record updated (polls every 5 min)
  Filter: Opportunity StageName changed
  Action: Update HubSpot deal stage via HubSpot API
```

**Why it works:** The scenario does not require middleware features beyond HTTP-based SaaS connectivity and simple conditional logic. Workato's recipe model delivers this with zero Apex and no infrastructure. The key validation step was confirming that Workato's 5-minute polling interval is acceptable — if sub-minute latency were required, Workato would be disqualified and Boomi or MuleSoft with a real-time Pub/Sub subscription would be needed.

---

## Example 3: Store-and-Forward Pattern for Offline Target System

**Context:** A healthcare logistics company integrates Salesforce Service Cloud with a legacy warehouse management system (WMS) that has a nightly maintenance window from 2 AM to 4 AM and occasional unplanned outages. Salesforce cases trigger fulfillment requests to the WMS when resolved. During the WMS maintenance window, Salesforce resolutions must be queued and delivered when the WMS comes back online.

**Problem:** The initial Apex-based solution fires an HTTP callout to the WMS REST endpoint when a Case status changes to "Resolved." During the 2-hour maintenance window, every callout fails with a 503 error. Apex retry logic cannot persist state across transactions; the team resorts to custom retry logic using scheduled Apex jobs and custom objects, which becomes difficult to maintain and monitor.

**Solution (Boomi selected — mid-market cost, existing relationship):**

```
Salesforce Platform Event (CaseFulfillmentRequest__e)
  → Boomi HTTP listener receives the event
  → Boomi process places message on Boomi Atom Queue (persistent, durable)
  → Boomi scheduled consumer reads from queue every 5 minutes
  → Attempt WMS REST API call
  → On 503/504: message retained in queue, retry after 10 min with backoff
  → On success: WMS confirmation ID written back to Salesforce Case via REST PATCH
  → After 24h with no successful delivery: message moves to dead-letter queue + alert fires
```

**Why it works:** The Boomi Atom Queue persists messages across the WMS maintenance window without relying on Salesforce Platform Event replay (which would expire in 72 hours but more critically would not retry automatically on WMS recovery). The retry logic is native to Boomi's process orchestration rather than custom Apex job machinery. The dead-letter queue provides an auditable failure record.

---

## Anti-Pattern: Using Apex Callouts for Multi-System Orchestration

**What practitioners do:** A developer places three callouts inside an Apex trigger: one to an ERP, one to a data warehouse, and one to a notification service. The trigger fires on Opportunity close.

**What goes wrong:** The three callouts consume 3 of the 100 callout slots per transaction, and the combined response time can exceed 10 seconds, causing the Salesforce transaction to time out. If the ERP callout succeeds but the data warehouse callout fails, the data warehouse is out of sync with no recovery path — the Apex transaction has already committed the Salesforce DML, but there is no retry mechanism for the failed callout. Adding error handling for partial failures inside Apex triggers creates code complexity that is fragile and untestable.

**Correct approach:** Publish a Platform Event on Opportunity close. Subscribe a middleware platform (MuleSoft, Boomi) to the event. Let middleware handle the fanout to ERP, data warehouse, and notification service with independent error handling per leg, dead-letter queuing, and correlation ID tracking.
