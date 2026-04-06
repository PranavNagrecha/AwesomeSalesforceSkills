# Quote-to-Cash Requirements — Work Template

Use this template when mapping, designing, or validating a quote-to-cash process on standard Salesforce Sales Cloud objects.

---

## Scope

**Skill:** `quote-to-cash-requirements`

**Request summary:** (fill in what the user asked for)

**In scope:**
- Standard Quote, QuoteLineItem, QuoteDocument objects
- Approval Process configuration for discount governance
- Quote Template design and PDF output requirements
- Order and OrderItem creation from accepted Quotes

**Out of scope (route to CPQ skills if present):**
- Salesforce CPQ / Revenue Cloud pricing rules, discount schedules, guided selling
- SBQQ__Quote__c or related custom CPQ objects

---

## Context Gathered

Answer these before proceeding:

- **Quotes enabled?** Setup > Quotes Settings > Enable Quotes: [ ] Yes / [ ] No / [ ] Unknown
- **CPQ/Revenue Cloud installed?** [ ] Yes (stop — route to CPQ skill) / [ ] No
- **Multi-currency enabled?** [ ] Yes / [ ] No — affects Pricebook assignment on Quote
- **Deal complexity:** Typical line item count per quote: _______ (flag if > 90)
- **Existing Pricebook(s):** List Pricebook names and currencies in use

---

## Approval Requirements

| Threshold | Approver | Approval Source | Notes |
|---|---|---|---|
| Discount >= ___% | _________________ | Manager / Named User / Queue | e.g., 10% to Manager |
| Discount >= ___% | _________________ | Manager / Named User / Queue | e.g., 25% to VP Sales |
| Amount >= $______ | _________________ | Manager / Named User / Queue | optional deal-size gate |

- **Rejection behavior:** Quote Status set to _______ / Email alert sent to _______
- **Record lock acknowledged by business?** [ ] Yes — communicate to reps that Quote is locked during approval
- **Recall process documented?** [ ] Yes — reps know to recall, not request a new Quote

---

## Quote Template Requirements

| Section | Content | Conditional? |
|---|---|---|
| Header | Logo, Quote Name, Date | No |
| Billing / Shipping Address | From Quote fields | No |
| Line Items | Product Name, Qty, Unit Price, Discount, Total | No |
| Legal Terms | Footer text | [ ] Yes — show only for certain record types |
| Signature Block | Rep name, contact | Optional |

- **Branding variations needed:** [ ] Yes (multiple templates) / [ ] No
- **Expected max line items per quote:** _______ — must be < 100 for standard template
- **Rich-text fields required in template?** [ ] Yes (not supported — use plain-text custom fields) / [ ] No

---

## Order Creation Requirements

- **Trigger:** [ ] Manual button click / [ ] Auto on Quote Status = Accepted (Flow required)
- **Fields to carry from Quote to Order:**
  - AccountId from Quote.Opportunity.AccountId
  - Pricebook2Id from Quote.Pricebook2Id
  - EffectiveDate from TODAY() or Quote.ExpirationDate
  - Status set to "Draft"
- **Fields to carry from QuoteLineItem to OrderItem:**
  - Product2Id, PricebookEntryId, Quantity, UnitPrice
- **Contract creation required after Order?** [ ] Yes / [ ] No

---

## Object and Field Model

List custom fields needed:

| Object | Field Label | Field Type | Purpose |
|---|---|---|---|
| Quote | Discount Override Justification | Long Text Area | Approval submission notes |
| Quote | Approved By | Lookup (User) | Auto-stamped on approval |
| QuoteLineItem | (standard fields sufficient) | — | — |
| Order | Source Quote | Lookup (Quote) | Set via Flow |

---

## Checklist

Copy from SKILL.md and verify before marking complete:

- [ ] Quotes feature enabled in Setup
- [ ] Approval process entry criteria match documented discount/amount thresholds
- [ ] Record lock behavior communicated to business stakeholders
- [ ] Quote Template tested with maximum expected line item count (confirmed < 100)
- [ ] Order creation (manual or Flow-automated) tested end-to-end in sandbox
- [ ] Multi-currency Pricebook entries consistent if multi-currency enabled
- [ ] Approval rejection path sets Quote Status and notifies rep via email alert
- [ ] Flow for Order creation handles zero-quantity or $0 line items without errors

---

## Gap Analysis — When Standard Quotes Are Insufficient

Flag these for CPQ/Revenue Cloud evaluation:

| Requirement | Standard Quote Capability | Gap |
|---|---|---|
| > 100 products per quote | Hard limit — PDF truncates | Evaluate CPQ |
| Bundle products with configuration logic | Not supported | Evaluate CPQ |
| Dynamic pricing rules or discount schedules | Not supported | Evaluate CPQ |
| Guided selling / product configurator | Not supported | Evaluate CPQ |
| Contract line items with amendments | Limited | Evaluate Revenue Cloud |

---

## Notes

Record any deviations from the standard pattern and why.
