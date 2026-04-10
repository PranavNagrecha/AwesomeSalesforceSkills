# CPQ Integration with ERP — Work Template

Use this template when working on a CPQ-to-ERP integration design or troubleshooting task.

## Scope

**Skill:** `cpq-integration-with-erp`

**Request summary:** (fill in what the user asked for)

**ERP system:** (SAP S/4HANA / Oracle EBS / NetSuite / Microsoft Dynamics 365 / other)

**Middleware:** (MuleSoft / Dell Boomi / custom Apex callout / other)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- Order.Status value that means "ERP-ready":
- Pricing master (CPQ or ERP):
- Amendment and renewal orders in scope? (yes/no):
- Inventory availability check required during quoting? (yes/no):
- Multi-currency in use? (yes/no):

## Trigger Point Decision

Which event triggers ERP transmission?

- [ ] `Order.Status = [value]` via Record-Triggered Flow + Platform Event (recommended)
- [ ] Other (document why Order activation is not used):

## Pricing Sync Strategy

- [ ] Synchronous QCP callout to ERP pricing API at calculation time
- [ ] Scheduled batch sync to PricebookEntry (document frequency and staleness tolerance)
- [ ] CPQ is pricing master; ERP reads from Salesforce

Staleness tolerance: ___

Conflict detection approach: ___

## Amendment Routing

- [ ] Amendment detection implemented (checks `SBQQ__Quote__r.SBQQ__AmendedContract__c`)
- [ ] Amendment Orders routed to ERP delta-update API (not net-new Sales Order)
- [ ] New-business Orders routed to ERP new Sales Order creation API

ERP amendment API endpoint: ___

## Inventory Check Design

If inventory checks are required:

- [ ] Implemented as invocable Apex action (NOT a QCP callout)
- [ ] LWC button component added to CPQ quote page layout
- [ ] Inventory status stored on `SBQQ__QuoteLine__c` custom fields

Custom fields for inventory status: ___

## Data Mapping

| Salesforce Field | Object | ERP Field | ERP Document |
|---|---|---|---|
| ProductCode | Product2 | MaterialNumber | Sales Order Item |
| Quantity | OrderItem | OrderQuantity | Sales Order Item |
| UnitPrice | OrderItem | NetPrice | Sales Order Item |
| (add rows as needed) | | | |

## Error Handling

- Dead-letter / retry strategy:
- ERP order number writeback field on Order object:
- Alerting on sync failures:

## Checklist

Copy from SKILL.md Review Checklist and tick as complete:

- [ ] ERP trigger is set to Order activation status change, not quote close or Opportunity stage
- [ ] Integration queries `SBQQ__QuoteLine__c` for quote-line data, not `QuoteLineItem`
- [ ] Integration queries `OrderItem` on the activated Order for order transmission data
- [ ] Amendment orders detected and routed to ERP delta-update API
- [ ] Inventory checks implemented as async invocable actions with LWC button
- [ ] Pricing sync strategy documented with staleness tolerance
- [ ] ERP order number written back to Salesforce Order as external reference
- [ ] Middleware retry and dead-letter handling configured
- [ ] Multi-currency edge cases tested (if applicable)

## Notes

Record any deviations from the standard pattern and why.
