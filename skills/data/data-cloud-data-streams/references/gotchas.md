# Gotchas — Data Cloud Data Streams

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Individual DMO Mapping Alone Does Not Unlock Identity Resolution

**What happens:** A data stream is mapped to the Individual DMO with `Individual ID`, `First Name`, and `Last Name` all populated. The mapping appears complete in the UI and there are no validation errors. However, when navigating to Identity Resolution to create a ruleset, the "New" button is inactive or the source object is missing from the match rule picklist.

**When it occurs:** Any time a data stream is mapped only to the Individual DMO without a corresponding Contact Point DMO (Email, Phone, Address, or App) or Party Identification DMO mapping. This is the default state immediately after creating a CRM or Ingestion API data stream if the practitioner stops after the Individual mapping step.

**How to avoid:** Always complete both mappings before declaring a data stream ready for identity resolution: (1) Individual DMO with primary key and name fields, and (2) at least one Contact Point DMO with the identity attribute field (email address, phone number) and the `Individual ID` foreign key linking back to the Individual DMO. Treat these as a pair, not as optional additions.

---

## Gotcha 2: Ingestion API Does Not Support Record Deletions

**What happens:** A team builds a data pipeline that sends creates, updates, and deletes from their source system to the Ingestion API. Create and update operations succeed. Delete operations either return an HTTP 400 error or appear to succeed but leave the record in the DLO unchanged, depending on the payload structure used.

**When it occurs:** Whenever a delete payload is submitted to the Ingestion API endpoint. The Ingestion API supports only `append` and `upsert` operations. This is a documented platform constraint, but it is not prominently surfaced in the connector configuration UI.

**How to avoid:** Audit the source system integration spec before building the pipeline. If deletions are required, plan a separate deletion mechanism using the Data Cloud bulk delete facility (accessible via the Data Cloud admin UI or the Data Cloud Bulk API). Do not attempt to handle deletions through the Ingestion API. Document this constraint in the integration design document so that future maintainers do not attempt to add delete support to the Ingestion API integration.

---

## Gotcha 3: Two Identity Resolution Rulesets Is the Absolute Org Limit

**What happens:** An org that already has 2 identity resolution rulesets reaches the platform limit. Attempts to create a third ruleset are blocked with a platform error. This affects multi-BU implementations where different business units want independent rulesets for their respective data populations.

**When it occurs:** Any org that has created 2 identity resolution rulesets is at the limit. The limit applies to the entire org, not per user, not per data stream, and not per business unit. Starter Data Bundles that include auto-created rulesets count against this limit.

**How to avoid:** Before the implementation begins, inventory all rulesets that will be needed across all business units and data sources in the org. If 3 or more rulesets are required, consult Salesforce account team about org architecture options. Design rulesets to be broad enough to cover all required match scenarios within the 2-ruleset constraint — for example, a single ruleset that includes both email and phone match rules rather than two separate rulesets split by channel.

---

## Gotcha 4: Party Identification ID Is a System Key, Not an External ID Field

**What happens:** A practitioner mapping a loyalty program ID or an ERP customer number to the Party Identification DMO maps the external ID value directly to the `Party Identification ID` field. The mapping saves without error. Identity resolution runs, but match counts are unexpectedly low or records are overwritten on subsequent ingestion runs.

**When it occurs:** During initial DMO mapping when the practitioner mistakes `Party Identification ID` (the DMO's internal system-generated primary key) for the field that stores external identifiers. The field label is ambiguous.

**How to avoid:** Map external identifiers to the `Identification Number` field on the Party Identification DMO, not to `Party Identification ID`. Also map `Identification Type` to a value that describes the ID type (e.g., `Loyalty ID`, `ERP Customer Number`). The `Party Identification ID` field should always be left blank or auto-populated by Data Cloud.

---

## Gotcha 5: Calculated Insights Reflect the Last Run, Not the Current Ingest State

**What happens:** A segment built on a Calculated Insight field (e.g., `purchase_count_90d`) shows a population count that is stale — it does not reflect purchases that arrived in the DLO since the last Calculated Insight run. Marketing sends go to a smaller (or larger) audience than expected because the metric has not refreshed.

**When it occurs:** Any time a Calculated Insight is used in a segment and the insight's scheduled run has not yet completed after new data was ingested. Calculated Insights run on a configured batch schedule (daily, every 12 hours, etc.) and are not updated incrementally as records flow in. High-frequency ingestion via the Ingestion API does not trigger a Calculated Insight refresh.

**How to avoid:** Document the Calculated Insight refresh schedule in the segment design. Schedule high-value insights (e.g., recency/frequency metrics used for priority segments) at a frequency that matches the business's staleness tolerance. For truly real-time behavioral signals, use Streaming Insights via the Web or Mobile SDK instead of Calculated Insights. Do not present Calculated Insight-backed segments to stakeholders as "real-time" — they are batch metrics with a defined lag.

---

## Gotcha 6: Starter Data Bundle Mappings Can Conflict with Custom Mappings

**What happens:** An org uses a Salesforce Starter Data Bundle (e.g., the Marketing Cloud Starter Bundle) which auto-creates DLO-to-DMO mappings for standard objects. When the practitioner later creates a custom data stream from an external source and attempts to map to the same Individual or Contact Point DMO, duplicate or conflicting mappings appear. Identity resolution produces unexpected merge results.

**When it occurs:** When custom data stream mappings are created for a DMO that already has Starter Data Bundle auto-mappings. The bundle's auto-mappings are not always surfaced prominently in the UI, so practitioners may not realize the DMO is already populated from another source.

**How to avoid:** Before creating any custom DMO mappings, open the Individual DMO and each Contact Point DMO in the Data Cloud Schema UI and inspect existing mappings. Understand which data streams are already contributing to each DMO via bundle mappings. Ensure that custom mappings use the same `Individual ID` primary key pattern so that identity resolution can join records across bundle-sourced and custom-sourced streams correctly.
