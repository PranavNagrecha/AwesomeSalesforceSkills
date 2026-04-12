# Commerce Integration Patterns — Architecture Template

Use this template when designing or documenting a Salesforce Commerce integration with external systems.

---

## Scope

**Skill:** `commerce-integration-patterns`

**Store type:** B2B Commerce / D2C Commerce _(circle one)_

**API version:** ___________________

**Request summary:** _(describe what the practitioner was asked to design or diagnose)_

---

## External Systems in Scope

List each external system and its integration role:

| System | Role | Integration Method | Real-Time Required? |
|---|---|---|---|
| _(e.g., SAP ERP)_ | Pricing / Inventory | CartExtension.PricingCartCalculator | Yes |
| _(e.g., Akeneo PIM)_ | Product catalog sync | Database.upsert with External ID | No (nightly batch) |
| _(e.g., FedEx)_ | Shipping rates | CartExtension.ShippingCartCalculator | Yes |
| _(e.g., Avalara)_ | Tax calculation | CartExtension.TaxCartCalculator | Yes |
| _(e.g., Stripe)_ | Payment authorization | CommercePayments.PaymentGatewayAdapter | Yes |
| _(e.g., SAP OMS)_ | Order fulfillment | Platform Event / outbound callout | Near real-time |

---

## Context Gathered

Answer before designing any extension point:

- **Existing RegisteredExternalService registrations for this store:**
  _(List EPN values already registered and which Apex classes handle them)_
  - CartExtension__Pricing: ___________________
  - CartExtension__Shipping: ___________________
  - CartExtension__Inventory: ___________________
  - CartExtension__Taxes: ___________________

- **SOM license confirmed:** Yes / No / Unknown
  _(If No or Unknown, document who owns capture and refund in the payment architecture)_

- **API version confirms CartExtension namespace availability (v55.0+):** Yes / No

- **Named Credentials already defined for each external system:** _(list or note gaps)_

---

## Extension Point Mapping

For each integration point, record the architect's decision:

### Pricing Integration

- **Decision:** ERP real-time callout / Batch sync to Salesforce price books / Price book only (no ERP)
- **Calculator class name:** ___________________
- **Named Credential:** ___________________
- **Fallback behavior on callout failure:** ___________________

### Shipping Integration

- **Decision:** Carrier real-time callout / Flat rate / Free shipping
- **Calculator class name:** ___________________
- **Named Credential:** ___________________
- **Fallback behavior on callout failure:** ___________________

### Inventory Integration

- **Decision:** ERP/WMS real-time callout / Batch inventory sync / Salesforce Inventory object
- **Calculator class name:** ___________________
- **Named Credential:** ___________________
- **Oversell prevention mechanism:** ___________________

### Tax Integration

- **Decision:** External tax engine callout / Salesforce built-in tax / Manual rates
- **Calculator class name:** ___________________
- **Tax engine and Named Credential:** ___________________

### Payment Integration

- **Decision:** Salesforce Payments (Stripe) / AppExchange package / Custom CommercePayments adapter
- **Adapter class name (if custom):** ___________________
- **Raw card data path:** Client-side iframe only — never transits Salesforce
- **Post-authorization capture owner:** SOM / Custom OMS callout / Payment gateway auto-capture

### PIM / Product Sync

- **PIM system:** ___________________
- **Sync frequency:** Real-time via Platform Event / Nightly batch / On-demand
- **External ID field on Product2:** ___________________
- **Upsert operation type:** `Database.upsert(list, Product2.<ExternalIdField>__c, false)`
- **Related objects requiring sync:** Product2 / ProductCategory / PricebookEntry / _(list others)_

---

## CartExtension Callout Safety Checklist

For each CartExtension calculator class in scope:

- [ ] All HTTP callouts are placed before any DML in the `calculate()` method
- [ ] Named Credential is used for the external endpoint — no hardcoded URLs or API keys
- [ ] Callout timeout is configured and documented
- [ ] Graceful fallback is implemented: if the callout fails, the calculator returns a safe default (not an exception)
- [ ] The class is the only registered class for its EPN on this store

---

## RegisteredExternalService Metadata Records

Document each metadata record to be deployed:

```
DeveloperName:               ___________________
ExtensionPointName:          CartExtension__Pricing / CartExtension__Shipping /
                             CartExtension__Inventory / CartExtension__Taxes
ExternalServiceProviderType: Extension
MasterLabel:                 ___________________
StoreIntegratedService:      (StoreIntegratedService record ID for the target store)
```

_Copy this block once per EPN being registered._

---

## Payment Architecture Notes

- **Tokenization path:** Provider-hosted iframe → opaque token → Apex adapter (token only)
- **PCI scope statement:** Raw card data (PAN, CVV, expiry) never transits Salesforce at any point
- **Capture and refund owner:** _(SOM / custom / gateway auto-capture)_

---

## Deviations From Standard Pattern

_(Record any decisions that diverge from the Recommended Workflow in SKILL.md and the rationale)_

---

## Validation Checklist

Before marking integration design complete:

- [ ] All EPNs audited — no duplicate registrations for the same EPN on the target store
- [ ] CartExtension callout-before-DML ordering confirmed in all calculator classes
- [ ] Product2 External ID field defined and upsert pattern validated
- [ ] Named Credentials defined for all external systems
- [ ] Raw card data confirmed to never transit Salesforce
- [ ] SOM license or alternative capture/refund owner documented
- [ ] End-to-end test order completed successfully through all integrated extension points
