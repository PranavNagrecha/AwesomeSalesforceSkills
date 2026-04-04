# Gotchas — Outbound Messages and Callbacks

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: HTTP 200 Without a SOAP Acknowledgment Body Triggers Infinite Retries

**What happens:** Salesforce retries message delivery indefinitely (up to 24 hours) even when the external endpoint returns HTTP 200. The delivery queue shows the message as "pending" with an ever-increasing retry count, and the external endpoint receives the same payload repeatedly — potentially hundreds of times per message. Operations teams often misdiagnose this as a Salesforce bug or a network issue, spending hours on network traces while the actual cause is a missing or malformed response body.

**When it occurs:** When the external endpoint developer is not familiar with the SOAP acknowledgment contract and implements a REST-style response: HTTP 200 with a JSON body, an empty body, a plain text "OK" body, or a SOAP fault in the body. All of these are treated identically by Salesforce — as a delivery failure. This also occurs when the endpoint returns a valid SOAP envelope but uses the wrong namespace (e.g., a generic SOAP namespace instead of `http://soap.sforce.com/2005/09/outbound`).

**How to avoid:** Document and test the acknowledgment contract before any endpoint goes live. The response body must be:
```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <notificationsResponse xmlns="http://soap.sforce.com/2005/09/outbound">
      <Ack>true</Ack>
    </notificationsResponse>
  </soapenv:Body>
</soapenv:Envelope>
```
Test by posting a sample SOAP envelope to the endpoint and inspecting the raw response body — not just the HTTP status code. Add a Salesforce sandbox delivery test as part of endpoint acceptance criteria before production enablement.

---

## Gotcha 2: TLS Failures Are Silent — The Delivery Queue Shows "Pending" With No Error Detail

**What happens:** When the external endpoint's TLS certificate is expired, uses a self-signed certificate, or supports only TLS 1.0/1.1 (which Salesforce no longer accepts), Salesforce cannot establish a connection. The delivery queue shows the message as pending and retrying, but there is no error message or TLS failure detail visible in Setup. Operations teams see only "delivery failed" without knowing whether the failure is a connectivity issue, a certificate issue, or a response body issue.

**When it occurs:** During initial setup when the endpoint URL points to a development or staging server with a self-signed certificate; when a production TLS certificate expires; after a server migration that drops TLS 1.2 support; or when the external endpoint is behind a load balancer that terminates TLS with a certificate Salesforce's CA bundle does not trust.

**How to avoid:** Before configuring the Outbound Message, validate the endpoint URL using Salesforce's **Remote Site Settings** test (add the URL as a remote site and test connectivity from an Apex Execute Anonymous callout). This exercises the same TLS stack. Monitor certificate expiry dates independently — Salesforce does not send expiry alerts for Outbound Message endpoints. Use a certificate from a publicly trusted CA, not a self-signed or internal CA certificate.

---

## Gotcha 3: Bulk Operations Generate Individual SOAP Deliveries — No Batching or Throttling

**What happens:** Every record change that matches a Workflow Rule criteria generates a separate Outbound Message delivery. A bulk data load using Data Loader, Bulk API, or a mass field update that affects 10,000 records generates 10,000 individual SOAP POST requests to the external endpoint in rapid succession. If the external endpoint cannot handle this burst rate, it starts returning HTTP 429 (Too Many Requests) or HTTP 503 (Service Unavailable). Salesforce treats these HTTP errors as delivery failures and retries each message, compounding the volume. The retry storm can overwhelm an endpoint that was only briefly over capacity.

**When it occurs:** During data migration projects, mass status updates by admin users, or automated nightly batch jobs that touch large sets of records matching the Workflow Rule criteria. The behavior is particularly surprising because in testing, individual record updates work fine — the volume issue only becomes apparent under load.

**How to avoid:** Design the external endpoint to handle burst delivery gracefully. Returning `<Ack>false</Ack>` (not an HTTP error) instructs Salesforce to retry with backoff, giving the endpoint time to recover without triggering an amplification cascade. Implement a queue-based buffer on the external side so that SOAP requests are acknowledged immediately and processed asynchronously. For known bulk operations, consider temporarily deactivating the Workflow Rule before the load and using a compensating process to re-fire it after the load completes — this is often cleaner than designing for unbounded burst throughput.

---

## Gotcha 4: The Session ID Expires and Is Scoped to the Triggering User — Not a Service Account by Default

**What happens:** External systems that use the session ID for callbacks find the token expired when the callback is processed. This is especially common when the external system queues received SOAP payloads for asynchronous processing — by the time the worker processes the message (minutes or hours later), the triggering user's session has timed out. Additionally, if the Workflow Rule fires due to a record change by a user with a restricted profile, the session ID produces a callback with equally restricted access — missing data the external system expected to see.

**When it occurs:** When external systems implement asynchronous processing pipelines where SOAP payload ingestion and business logic execution are decoupled. Also occurs during off-hours automation: if a scheduled job or integration user triggers the Workflow Rule, that user's session may have a shorter timeout than expected. The issue is compounded when the integration is first built and tested by an admin (full access), but then fires in production under a restricted end-user session.

**How to avoid:** Process the session ID callback immediately upon receipt — do not queue the session ID for later use. If the external system requires delayed or batch processing, fetch the needed data immediately when the Outbound Message is received and store the data (not the session ID) for later processing. For consistent, predictable callback access, configure a dedicated Salesforce integration user (with a profile that has the required API and object access) and ensure Workflow Rules are designed to be triggered by actions that will use that integration user's context. Never store session IDs in plaintext logs.

---

## Gotcha 5: Outbound Messages Are Not Available in New Orgs Created After Spring '25

**What happens:** When a developer or architect designs an integration using Outbound Messages for a new Salesforce implementation, they discover that the "Outbound Messages" action type is not available when adding actions to Workflow Rules — because new Workflow Rules cannot be created in orgs provisioned after Spring '25. The Setup UI for Workflow Rules may still be accessible, but the "Create" button for new rules is absent or produces an error. Existing Workflow Rules (migrated via metadata) may still deploy but cannot be created through Setup.

**When it occurs:** Any time an Outbound Message-based integration is planned for a new Salesforce org or a newly provisioned sandbox. Also occurs when a Salesforce Partner is building a managed package that relies on Outbound Messages — the package may not install cleanly in new subscriber orgs.

**How to avoid:** Check the org's Salesforce version and provisioning date before designing an Outbound Message integration. For new orgs or new integrations in existing orgs where migration away from Workflow Rules is feasible, use Platform Events published from a Record-Triggered Flow. For existing orgs with existing Workflow Rules, the current Outbound Message setup continues to function and can be maintained. Document the org age check as the first step in any integration design that considers Outbound Messages.
