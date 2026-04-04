# Outbound Messages and Callbacks — Work Template

Use this template when implementing, configuring, or troubleshooting an Outbound Message integration. Fill in each section before writing code or metadata.

---

## Scope

**Skill:** `outbound-messages-and-callbacks`

**Request summary:** (describe what was asked — e.g., "configure Outbound Message to notify billing system when Opportunity closes", "debug retry loop on existing Outbound Message", "implement session ID callback for Account enrichment")

---

## Prerequisites Verified

Answer each question before proceeding. A "No" answer to any of the first three questions may block implementation — note the blocker and the alternative approach.

| Question | Answer | Notes |
|---|---|---|
| Is this an existing Salesforce org provisioned before Spring '25? | Yes / No | New orgs cannot create Workflow Rules — use Platform Events instead |
| Does a Workflow Rule already exist for this trigger condition? | Yes / No / Needs creation | Note the Workflow Rule name if it exists |
| Can the external endpoint accept SOAP 1.1 over HTTPS? | Yes / No | If No, Outbound Messages are not viable — evaluate Apex callout or Platform Events |
| Does the external endpoint use TLS 1.2 or higher? | Yes / No | Salesforce enforces TLS 1.2 minimum |
| Is the endpoint URL publicly reachable from Salesforce IP ranges? | Yes / No | Firewall allowlist required if No |
| Has idempotency been designed for the receiving endpoint? | Yes / No / In progress | Required — duplicates will occur |

---

## Outbound Message Configuration

Complete this section when configuring the Outbound Message in Setup or in metadata.

**Object:** (e.g., Opportunity, Case, Account)

**Workflow Rule name:** (name of the Workflow Rule this Outbound Message is attached to)

**Workflow Rule criteria:** (describe the criteria — e.g., "Status equals Closed Won", "Priority changed to High")

**Trigger type:** (Created, Edited, Created and every time edited — note high-volume risk if "every time edited")

**Endpoint URL:** `https://` (must be HTTPS — never HTTP)

**Fields included in payload:**

| Field API Name | Reason included |
|---|---|
| Id | Always implicit |
| (add fields) | (why the endpoint needs this field) |

**Session ID required for callback?** Yes / No

---

## External Endpoint Design

**Endpoint URL (confirm matches above):** `https://`

**Technology / language of endpoint implementation:** (Java, Python, Node.js, .NET, etc.)

**SOAP parsing approach:** (e.g., xml.etree.ElementTree, JAXB, XDocument — must handle SOAP 1.1 namespace `http://soap.sforce.com/2005/09/outbound`)

**Acknowledgment response:** Confirm endpoint returns exactly:
```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <notificationsResponse xmlns="http://soap.sforce.com/2005/09/outbound">
      <Ack>true</Ack>
    </notificationsResponse>
  </soapenv:Body>
</soapenv:Envelope>
```

**Idempotency key design:** (e.g., record Id + Status field value, hash of payload body, combination of Id + LastModifiedDate)

**Idempotency store:** (e.g., database deduplication table, Redis cache with TTL, in-memory set — note TTL and expected max requeue window)

---

## Session ID Callback Plan (if applicable)

**Why callback is needed:** (what data cannot be included in the Outbound Message field list)

**REST API calls planned:**

| API Call | Endpoint | Fields / Query |
|---|---|---|
| Example | GET /services/data/v63.0/sobjects/Account/{id} | BillingStreet, Territory__c |
| (add rows) | | |

**Session expiry risk:** (will the callback be made synchronously on receipt, or deferred? If deferred, document the maximum expected latency and whether session expiry is a concern)

**Credential handling:** Confirm session ID is NOT stored in plaintext logs or database: Yes / No

---

## Testing Plan

**Sandbox Workflow Rule criteria test:**
- [ ] Modify a record in sandbox matching the criteria and verify the Workflow Rule fires
- [ ] Navigate to Setup > Outbound Messages delivery queue and confirm message shows as delivered
- [ ] Inspect external endpoint logs for the expected SOAP payload

**Acknowledgment test:**
- [ ] POST a sample SOAP envelope to the endpoint and inspect the raw response body (not just status code)
- [ ] Confirm response body matches the required SOAP acknowledgment structure
- [ ] Confirm Content-Type response header is `text/xml`

**Idempotency test:**
- [ ] Send the same SOAP payload twice to the endpoint
- [ ] Confirm the second delivery is detected as a duplicate and discarded without creating duplicate records or processing

**Session ID callback test (if applicable):**
- [ ] Extract session ID from a sandbox delivery and make a test REST API call
- [ ] Confirm data returned matches the triggering user's access level

**Load test (if bulk operations are expected):**
- [ ] Simulate burst delivery (multiple rapid record changes) and confirm endpoint handles without HTTP errors
- [ ] Confirm endpoint returns `<Ack>false</Ack>` under load rather than HTTP 429/503

---

## Operations Runbook

**Delivery queue location:** Setup > Process Automation > Outbound Messages

**Monitoring approach:** (how will the team detect pending or failed messages — Setup UI, Tooling API query, third-party monitoring)

**Alert threshold:** (e.g., alert if messages remain in queue > 4 hours)

**Manual requeue procedure:**
1. Navigate to Setup > Process Automation > Outbound Messages
2. Filter for messages in "Failed" or "Pending" state
3. Confirm external endpoint is operational and returning correct SOAP acknowledgments
4. Select failed messages and click "Requeue"
5. Monitor delivery queue for the next 30 minutes to confirm requeued messages deliver successfully

**Compensating batch procedure (for high-volume expiry):**
- Trigger an Apex batch job that performs a no-op field update on the affected records to re-fire the Workflow Rule
- Coordinate with external endpoint team to confirm capacity before running the batch
- Batch query: (write the SOQL that selects records affected by the outage window)

---

## Review Checklist

Complete before marking this work done:

- [ ] External endpoint URL uses HTTPS with TLS 1.2 or higher certificate from a publicly trusted CA
- [ ] Outbound Message is configured on the correct object with the correct fields selected
- [ ] Workflow Rule criteria tested in sandbox — fires as expected, does not over-fire
- [ ] External endpoint returns the exact SOAP acknowledgment structure (not just HTTP 200)
- [ ] Endpoint deduplicates by record ID or payload hash before processing side effects
- [ ] Session ID is not logged in plaintext (if callback pattern is used)
- [ ] Delivery queue shows successful delivery in sandbox before production activation
- [ ] Operations runbook is documented and shared with the team responsible for this integration
- [ ] Salesforce IP ranges are allowlisted on the receiving endpoint's firewall
- [ ] Alert is configured for messages remaining in delivery queue beyond the threshold

---

## Notes and Deviations

(Record any deviations from the standard Outbound Message pattern, decisions made during implementation, and the reasoning behind non-standard approaches.)
