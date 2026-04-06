---
name: sales-cloud-integration-patterns
description: "Use when designing or reviewing integrations between Sales Cloud and external systems such as ERP, marketing automation, CPQ, or partner portals. Triggers: 'sync Accounts and Products with ERP', 'integrate marketing leads with Salesforce', 'quote-to-order flow between Salesforce and ERP', 'CPQ integration patterns', 'partner portal data access design'. NOT for generic integration framework design (use architect/integration-framework-design), NOT for Apex HTTP callout mechanics (use apex/callouts-and-http-integrations), NOT for MuleSoft or middleware configuration."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
  - Scalability
tags:
  - sales-cloud
  - erp-integration
  - marketing-automation
  - cpq
  - quote-to-order
  - partner-portal
  - external-id
  - upsert
  - bidirectional-sync
triggers:
  - "how to sync Salesforce Accounts and Products with an ERP system"
  - "integrate marketing automation leads and campaigns with Sales Cloud"
  - "design a quote-to-order integration between Salesforce CPQ and ERP"
  - "what is the best pattern for bidirectional Account sync with an external system"
  - "partner portal integration patterns with Experience Cloud and Sales Cloud"
  - "how to handle Lead-to-Contact conversion in a marketing integration"
  - "map Opportunity line items to ERP order lines"
  - "how to integrate Sales Cloud with ERP for quote-to-order sync"
inputs:
  - "Source and target systems involved in the integration"
  - "Objects to sync (Account, Product, Opportunity, Lead, Campaign, Quote, Order)"
  - "Directionality requirements (unidirectional vs bidirectional)"
  - "Data volume and frequency expectations"
  - "Existing middleware or integration platform (if any)"
  - "Partner portal access and visibility requirements"
outputs:
  - "Integration architecture decision record with object-level data flow"
  - "External ID field strategy and upsert mapping"
  - "Sync directionality matrix per object"
  - "Quote-to-order object mapping and lifecycle design"
  - "Partner portal data access pattern with role hierarchy"
  - "Error handling and reconciliation strategy"
dependencies:
  - architect/integration-framework-design
  - apex/callouts-and-http-integrations
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Sales Cloud Integration Patterns

Use this skill when designing, building, or reviewing integrations between Salesforce Sales Cloud and external systems — ERP platforms, marketing automation tools, CPQ engines, or partner portals. This skill provides object-level guidance on sync directionality, data mapping, identity resolution, and lifecycle management specific to Sales Cloud's data model.

---

## Before Starting

Gather this context before working on anything in this domain:

- Which external systems are involved and what protocols do they support (REST, SOAP, file-based, event-driven)?
- Which Sales Cloud objects are in scope: Account, Contact, Lead, Opportunity, Product, PricebookEntry, Quote, QuoteLineItem, Order, OrderItem, Campaign, CampaignMember?
- What is the system of record for each object — does mastery sit in Salesforce, the external system, or is it shared?
- What data volumes are expected (initial load vs steady-state daily change volume)?
- Is there a middleware layer (MuleSoft, Dell Boomi, Informatica) or will integrations be point-to-point?

---

## Core Concepts

### External ID Fields and Upsert-Based Sync

Every integration between Sales Cloud and an external system must establish identity resolution. External ID fields on Salesforce objects hold the foreign key from the external system. The `upsert` operation uses this field to insert new records or update existing ones in a single DML call, eliminating the need for a separate query-then-insert-or-update pattern. External ID fields must be indexed (they are by default) and should be unique. When an ERP system owns Account numbers, create `ERP_Account_ID__c` as an External ID on Account. All inbound syncs reference this field.

### Sync Directionality Per Object

Not every object flows the same direction. A well-designed Sales Cloud integration defines directionality at the object level:

- **Account / Product**: Typically bidirectional. ERP may master the legal entity name and billing address; Salesforce may master sales-specific fields like account owner and territory.
- **Order**: Typically unidirectional from Salesforce to ERP. Once an order is placed in Salesforce (via Quote-to-Order or CPQ), it flows outbound. ERP returns status updates but does not create orders in Salesforce.
- **Lead / Campaign**: Marketing automation pushes leads into Salesforce; campaign membership and response data flow bidirectional. Lead scoring may originate externally.
- **Opportunity / OpportunityLineItem**: Usually Salesforce-mastered with summary data pushed to ERP for forecasting or pre-order visibility.

Documenting this matrix up front prevents field-level conflict and duplicate-record issues.

### Lead-to-Contact Conversion and ID Continuity

When a marketing automation platform syncs Leads into Salesforce, the Lead ID is the external reference. Upon Lead conversion, Salesforce creates a Contact (and optionally Account and Opportunity) with new IDs. The original Lead ID becomes inaccessible for updates. Integrations must handle this transition by: (1) subscribing to the `LeadConvertedContactId` field or a platform event on conversion, (2) updating the external system's reference to point to the new Contact ID, and (3) ensuring subsequent sync operations target the Contact object post-conversion. Failing to handle this causes orphaned records in the marketing platform.

### Quote-to-Order Object Mapping

Salesforce supports two quote-to-order paths. The standard path uses Quote and QuoteLineItem objects, with a manual or automated "Create Order" action that generates Order and OrderItem records. Salesforce CPQ uses SBQQ__Quote__c and SBQQ__QuoteLine__c, with contracted orders created via the CPQ contract process. In both cases, the Order object is the handoff point to ERP. QuoteLineItems or CPQ Quote Lines map to ERP order lines. Product2 and PricebookEntry provide the product catalog linkage. The integration must respect the lifecycle: Draft Quote, Approved Quote, Contracted Order, Activated Order.

---

## Common Patterns

### Bidirectional Account/Product Sync with Field-Level Mastery

**When to use:** The ERP system owns financial and legal data (billing address, payment terms, tax ID) while Salesforce owns sales data (owner, territory, engagement score). Both systems need a complete Account record.

**How it works:**
1. Define field-level mastery: each field has exactly one system of record.
2. Create External ID fields in both directions (`ERP_Account_ID__c` in Salesforce, Salesforce Account ID stored in ERP).
3. Inbound sync (ERP to SF): Upsert on `ERP_Account_ID__c`, updating only ERP-mastered fields. Use a field set or integration-specific field list to prevent overwriting Salesforce-mastered fields.
4. Outbound sync (SF to ERP): Trigger on Salesforce-mastered field changes only. Push via platform event or outbound message.
5. Implement a last-modified timestamp comparison to prevent ping-pong updates.

**Why not the alternative:** A single-master approach forces one system to be the sole source of truth, requiring manual re-entry or constant full-record pushes that overwrite legitimate local changes.

### Marketing Lead Sync with Conversion Handling

**When to use:** A marketing automation platform (Marketo, Pardot, HubSpot) syncs leads bidirectionally with Salesforce, and the integration must survive Lead-to-Contact conversion.

**How it works:**
1. Marketing platform creates/updates Leads in Salesforce using an External ID (`Marketing_Lead_ID__c`).
2. Subscribe to Lead conversion events via a trigger or Change Data Capture on Lead (monitoring `IsConverted`, `ConvertedContactId`).
3. On conversion, fire an outbound notification to the marketing platform with the new Contact ID mapped to the original Marketing Lead ID.
4. Marketing platform updates its reference from Lead to Contact.
5. Post-conversion syncs target Contact and CampaignMember objects.

**Why not the alternative:** Ignoring the conversion event causes the marketing platform to continue pushing updates to a converted Lead, which Salesforce rejects. This creates a growing backlog of sync failures.

### Unidirectional Quote-to-Order to ERP

**When to use:** Salesforce is the quoting system (standard Quotes or CPQ). Approved quotes become orders that must be transmitted to an ERP system for fulfillment.

**How it works:**
1. Quote reaches "Approved" status. An automated process (Flow, Process Builder, or CPQ contract action) creates an Order with OrderItems.
2. Order activation triggers an outbound integration (platform event, Apex callout, or middleware polling).
3. The payload maps: Order fields to ERP order header, OrderItem fields to ERP order lines, Product2.ProductCode to ERP SKU.
4. ERP returns an order confirmation number, stored as `ERP_Order_ID__c` on the Salesforce Order.
5. Subsequent ERP status updates (shipped, invoiced) flow back via a scheduled inbound sync updating Order.Status and custom status fields.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Account/Product sync with shared ownership | Bidirectional with field-level mastery | Prevents overwrite conflicts; each system updates only its owned fields |
| Lead sync from marketing automation | Bidirectional with conversion event handling | Lead-to-Contact ID change breaks sync without explicit handling |
| Order transmission to ERP | Unidirectional SF-to-ERP with status callback | ERP is the fulfillment system of record; SF only needs status back |
| Partner needs to see/edit Opportunities | Experience Cloud portal with sharing rules | Role-based OWD and sharing sets control visibility without custom API |
| High-volume initial data load (>500K records) | Bulk API 2.0 with External ID upsert | Avoids governor limits; External ID eliminates separate lookup step |
| Real-time sync requirement (<5 second latency) | Platform Events or Change Data Capture | Event-driven avoids polling overhead; near-real-time delivery |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner designing a Sales Cloud integration:

1. **Inventory objects and fields** — List every Sales Cloud object in scope. For each, identify the external system counterpart and which fields need to sync.
2. **Define system of record per field** — Build a field-mastery matrix. For each field on each object, declare whether Salesforce, the external system, or neither is the master. Shared mastery requires conflict resolution rules.
3. **Map External ID fields** — Create or identify External ID fields on each Salesforce object that will hold the foreign key. Ensure uniqueness constraints are set. Document the corresponding ID in the external system.
4. **Design directionality and triggers** — For each object, decide: inbound only, outbound only, or bidirectional. Choose the trigger mechanism: Change Data Capture, platform events, polling schedule, or Apex triggers with @future/Queueable callouts.
5. **Handle lifecycle transitions** — Document what happens during Lead conversion, Quote-to-Order creation, and Opportunity close. Each transition changes the target object and may invalidate existing external references.
6. **Build error handling and reconciliation** — Design retry logic, dead-letter queues, and a reconciliation job that periodically compares record counts and checksums between systems.
7. **Validate with realistic volumes** — Test with production-scale data volumes. Verify that bulk operations stay within governor limits, that External ID upserts handle both insert and update paths, and that bidirectional sync does not create update loops.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] External ID fields exist on every Salesforce object that receives inbound records
- [ ] Field-mastery matrix is documented — no field has ambiguous ownership
- [ ] Sync directionality is defined per object (not assumed to be the same for all)
- [ ] Lead-to-Contact conversion is handled if marketing integration is in scope
- [ ] Quote-to-Order lifecycle is mapped with clear handoff point to ERP
- [ ] Partner portal data access uses sharing rules or sharing sets, not wide-open OWD
- [ ] Error handling includes retry, dead-letter, and reconciliation mechanisms
- [ ] Bulk data load path uses Bulk API 2.0 with External ID upsert
- [ ] No integration overwrites fields owned by the other system
- [ ] Ping-pong prevention is in place for bidirectional syncs (timestamp or flag)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Lead conversion deletes the Lead ID** — After conversion, the Lead record still exists but is read-only and no longer updatable via API. Integrations that reference `Lead.Id` post-conversion will fail silently or error. Always plan for ID continuity through `ConvertedContactId`.
2. **Upsert with External ID is case-insensitive but not null-safe** — If an External ID field has a null value, upsert treats it as an insert every time, creating duplicates. Ensure the External ID is always populated before sync.
3. **Order activation is irreversible** — Once an Order's `StatusCode` is set to "Activated," most fields become read-only. Integrations that need to update order details after activation must use draft-status orders and activate only after ERP confirms receipt.
4. **Bidirectional sync triggers infinite loops** — An inbound update fires a trigger that sends an outbound update, which triggers another inbound update. Prevent this with a static Boolean flag in Apex (`IntegrationContext.isInbound`) or by comparing `LastModifiedBy` to the integration user.
5. **PricebookEntry requires a standard pricebook entry first** — You cannot create a PricebookEntry in a custom pricebook unless the Product already has an entry in the standard pricebook. Integrations that skip this step will fail with a cryptic error.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Field-mastery matrix | Spreadsheet or table mapping every synced field to its system of record and sync direction |
| External ID field inventory | List of External ID fields per object with uniqueness and indexing confirmation |
| Object directionality diagram | Visual showing each object with arrows indicating sync direction between systems |
| Quote-to-Order lifecycle map | State diagram showing Quote approval through Order activation and ERP handoff |
| Reconciliation job specification | Design for the periodic job that detects and resolves sync drift between systems |

---

## Related Skills

- architect/integration-framework-design — Use when building a reusable Apex callout framework that this integration will use
- apex/callouts-and-http-integrations — Use for the Apex-level HTTP callout mechanics within these integration patterns
- architect/sales-cloud-architecture — Use for broader Sales Cloud data model and configuration decisions outside integration

---

## Official Sources Used

- Salesforce Integration Patterns and Practices — https://developer.salesforce.com/docs/atlas.en-us.integration_patterns_and_practices.meta/integration_patterns_and_practices/integ_pat_intro.htm
- Sales Cloud Overview — https://help.salesforce.com/s/articleView?id=sf.sales_core.htm
