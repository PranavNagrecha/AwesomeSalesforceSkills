# Sales Cloud Integration Patterns — Work Template

Use this template when designing or reviewing an integration between Sales Cloud and an external system.

## Scope

**Skill:** `sales-cloud-integration-patterns`

**Request summary:** (fill in what the user asked for)

**External system(s):** (ERP name, marketing platform, CPQ system, etc.)

**Integration platform:** (MuleSoft, Dell Boomi, point-to-point Apex, etc.)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- External systems and protocols:
- Sales Cloud objects in scope:
- System of record per object:
- Expected data volumes (initial load / steady state):
- Middleware in use:

## Object Directionality Matrix

| Object | Direction | System of Record | Trigger Mechanism | External ID Field |
|---|---|---|---|---|
| Account | Bidirectional / Inbound / Outbound | SF / External / Shared | CDC / Event / Schedule | |
| Contact | | | | |
| Lead | | | | |
| Opportunity | | | | |
| Product2 | | | | |
| PricebookEntry | | | | |
| Quote | | | | |
| Order | | | | |
| OrderItem | | | | |
| Campaign | | | | |
| CampaignMember | | | | |

## Field-Mastery Matrix

For bidirectional objects, list which fields are mastered by which system.

| Object | Field | Mastered By | Sync Direction | Notes |
|---|---|---|---|---|
| Account | Name | | | |
| Account | BillingAddress | | | |
| Account | OwnerId | Salesforce | Never inbound | |
| | | | | |

## Lifecycle Transitions

Document what happens at each lifecycle boundary.

### Lead Conversion
- How is the external system notified?
- What ID mapping changes?
- What object does the sync target post-conversion?

### Quote-to-Order
- Standard Quotes or CPQ?
- What triggers Order creation?
- At what Order status does ERP transmission occur?
- How does ERP confirmation flow back?

## Pattern Selection

Which pattern from SKILL.md applies? Why?

- [ ] Bidirectional Account/Product Sync with Field-Level Mastery
- [ ] Marketing Lead Sync with Conversion Handling
- [ ] Unidirectional Quote-to-Order to ERP
- [ ] Other (describe):

## Error Handling Design

- Retry mechanism:
- Dead-letter queue:
- Reconciliation job frequency:
- Alerting threshold:

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

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

## Notes

Record any deviations from the standard pattern and why.
