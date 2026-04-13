# Gotchas — Outbound Message Setup

## Gotcha 1: HTTP 200 Without SOAP Acknowledgment Triggers Continuous Retries

**What happens:** The external endpoint returns HTTP 200 (success status) but with a non-SOAP body (JSON, empty, or plain text). Salesforce treats this as a delivery failure and begins retrying. Over 24 hours, the external system receives the same Outbound Message payload hundreds of times — approximately 200-300 deliveries before the message is permanently dropped.

**When it occurs:** Any external endpoint that acknowledges success with a non-SOAP response. Extremely common because most modern web services expect to return JSON for any HTTP response. The SOAP acknowledgment requirement is specific to Salesforce Outbound Messages and is not intuitive for developers building modern REST/JSON services.

**How to avoid:** Always provide the external development team with the exact SOAP acknowledgment template before they build the receiving endpoint. Require them to test with the correct response format in a staging environment before going live. The SOAP response must include `<Ack>true</Ack>` inside a `<notifications>` element in the `http://soap.sforce.com/2005/09/outbound` namespace. Any deviation from this format — including the wrong XML namespace — results in continuous retries.

---

## Gotcha 2: Messages Are Permanently Dropped After 24 Hours With No Notification

**What happens:** Outbound Messages that fail to deliver for 24 hours disappear from the Pending queue without any alert, email notification, or log entry. The integration silently stops delivering data for the affected records. Business users discover the gap hours or days later when downstream data is stale.

**When it occurs:** Any sustained endpoint outage exceeding 24 hours. Also occurs when the acknowledgment issue (Gotcha 1) goes undetected for more than 24 hours — all messages in the retry queue are dropped simultaneously.

**How to avoid:** Implement proactive monitoring. Options include:
1. Schedule a daily report or alert that queries the Outbound Message Pending queue size via the Salesforce API.
2. If the External Service has its own logging, compare incoming Salesforce notification counts against the triggering Workflow event counts.
3. For critical integrations, implement record-level reconciliation — periodically compare the source Salesforce object's state against the external system's state and alert on discrepancies.
4. Use manual requeue before the 24-hour window expires for any known endpoint outage.

---

## Gotcha 3: New Outbound Message Actions Cannot Be Added to Flows

**What happens:** A developer attempts to add an Outbound Message as a Flow Action. The "Outbound Message" option is not available in the Flow Designer's element palette or action picker. The feature appears to be missing.

**When it occurs:** Any new Flow-based automation that requires external SOAP notification. As of Spring '23, Salesforce deprecated new Workflow Rule creation. Existing Workflow Rules and their Outbound Message actions still work, but new Flow implementations cannot use Outbound Messages directly.

**How to avoid:** For new integration automation that will be built in Flow, use Platform Events as the notification mechanism:
1. Define a Platform Event object with the fields to publish.
2. Use a "Create Records" element in Flow to publish the Platform Event (events are records in Salesforce).
3. Configure the external system to subscribe to the Salesforce Streaming API (CometD) to receive events.
Platform Events support JSON-compatible data structures and are the strategic replacement for Outbound Messages in Flow-first architectures.
