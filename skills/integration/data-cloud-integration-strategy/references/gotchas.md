# Gotchas — Data Cloud Integration Strategy

## Gotcha 1: Streaming Is Near-Real-Time, Not Real-Time

**What happens:** Data ingested via Streaming Ingestion API is not immediately available for segmentation or activation. The platform processes streaming micro-batches approximately every 3 minutes and there is no sub-minute SLA.

**When it occurs:** Any time a practitioner builds a use case that requires data to be available in Data Cloud within seconds of an external system event.

**How to avoid:** Communicate the ~3-minute minimum latency (plus DSO → DLO → DMO pipeline lag) to stakeholders before committing to SLAs. For sub-minute requirements, Data Cloud Ingestion API streaming is not the right architecture — source-system direct queries or a separate edge caching layer is needed.

---

## Gotcha 2: Bulk Ingestion Is Full-Replace Only — No Patch/Upsert

**What happens:** A bulk job that sends only changed records (delta batch) instead of the full dataset causes the remaining records to be deleted from the DLO, resulting in data loss.

**When it occurs:** When practitioners familiar with Salesforce upsert semantics assume bulk ingestion supports partial updates. Bulk Ingestion API replaces the full dataset for the objects in scope.

**How to avoid:** Always send the complete dataset in bulk jobs. For delta/append ingestion, use streaming mode. Design batch exports to include ALL records, not just changes.

---

## Gotcha 3: Schema Deployed to Ingestion API Is Effectively Immutable

**What happens:** After an Ingestion API schema is deployed (OpenAPI 3.0.x YAML), fields cannot be removed, field types cannot be changed, and objects cannot be deleted. Attempts to modify deployed schemas fail.

**When it occurs:** When schema requirements change after initial deployment — a very common scenario in early-phase implementations.

**How to avoid:** Invest in schema design before deploying. Review with data architects and downstream consumers. Add all anticipated fields upfront. Additive changes (adding new optional fields) are generally supported; destructive changes are not.

---

## Gotcha 4: MuleSoft Direct Requires Separate MuleSoft Licensing

**What happens:** A connector design based on MuleSoft Direct fails because the org lacks MuleSoft licensing. The connector type is visible in Data Cloud Setup but cannot be fully configured without the license.

**When it occurs:** When practitioners select MuleSoft Direct as the connector for unstructured content sources (SharePoint, Confluence) without confirming MuleSoft licensing with the customer.

**How to avoid:** Always confirm MuleSoft Anypoint Platform licensing before proposing MuleSoft Direct as a connector. If MuleSoft is not licensed, cloud storage connectors or custom Ingestion API are alternatives.

---

## Gotcha 5: Multi-Hop Pipeline Lag Before Segmentation Availability

**What happens:** Data ingested at 10:00 AM is expected to appear in segment results by 10:05 AM. It does not appear until 10:30 AM or later because the DSO → DLO → DMO pipeline introduces cumulative processing lag beyond the initial ingestion batch window.

**When it occurs:** Any time stakeholders measure "time to segment availability" from the moment an event reaches the Ingestion API endpoint.

**How to avoid:** Model the full pipeline latency: ingestion batch (~3 min for streaming) + DSO-to-DLO processing + DLO-to-DMO mapping + identity resolution run (~15 min minimum). The end-to-end minimum for a new streaming event to appear in a segment is typically 20-45 minutes, not 3 minutes.
