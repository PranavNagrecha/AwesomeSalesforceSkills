# Quotes and Quote Templates — Work Template

Use this template when working on a Quotes configuration task: quote template design, quote sync setup, PDF generation, email quote workflow, or discount approval on the Quote object.

## Scope

**Skill:** `quotes-and-quote-templates`

**Request summary:** (fill in what the user asked for)

**In scope (standard Quotes):**
- [ ] Quote template design / PDF layout
- [ ] Quote sync to opportunity setup or troubleshooting
- [ ] Email quote workflow
- [ ] Discount approval process on Quote
- [ ] Custom field mirroring from Opportunity/Account to Quote

**Out of scope — do NOT proceed, route elsewhere:**
- [ ] CPQ (SBQQ) quote configuration — route to `architect/cpq-vs-standard-products-decision`
- [ ] Quote line scheduling — CPQ feature, not standard Quotes
- [ ] Order management or contract generation

---

## Context Gathered

Fill in before starting work:

- **Quotes enabled in Setup?** Yes / No / Unknown
- **Org edition:** (e.g., Enterprise, Unlimited, Professional+add-on)
- **CPQ installed in this org?** Yes / No / Unknown — (if Yes, confirm standard vs CPQ quotes before proceeding)
- **Custom fields needed on PDF:** (list fields from Opportunity/Account not currently on Quote)
- **Sync requirement:** Is the opportunity revenue expected to sync bidirectionally from the quote? Yes / No
- **Discount approval needed?** Yes / No — if Yes: threshold %, approver routing, record lock requirement

---

## Approach

Which pattern from SKILL.md applies?

- [ ] Pattern: Single Synced Quote as Order of Record
- [ ] Pattern: Multi-Section Quote Template with Custom Header Fields
- [ ] Pattern: Discount Approval Gate on Quote
- [ ] Combination — describe:

**Reason:** (explain why this pattern fits the request)

---

## Field Mirroring Plan

| Salesforce Field Source | Target Quote Field | Population Mechanism |
|---|---|---|
| Opportunity.CloseDate | Quote.Close_Date_Mirror__c | Record-Triggered Flow |
| Account.BillingStreet | Quote.Billing_Street_Mirror__c | Record-Triggered Flow |
| (add rows as needed) | | |

---

## Quote Template Design

**Template name:**

| Section | Fields / Content | Notes |
|---|---|---|
| Header | Quote.Name, Quote.QuoteNumber, Quote.ExpirationDate, custom mirror fields | Add custom mirror fields as needed |
| Body (line items table) | Product Name, Quantity, Unit Price, Discount, Total Price | Confirm columns with business stakeholders |
| Footer | Terms and conditions text, signature block | Keep under 32,000 chars per text block |

---

## Approval Process Design (if applicable)

- **Object:** Quote
- **Entry criteria:** Quote.Discount > ____%
- **Record lock on submission:** Yes / No
- **Approver routing:** Named user / Manager hierarchy / Lookup field (specify)
- **Approval action:** Unlock record, set Quote.Status = 'Approved'
- **Rejection action:** Unlock record, reset Quote.Discount to threshold, email submitter

---

## Checklist

Copy from SKILL.md Review Checklist and tick off as completed:

- [ ] Quotes is enabled in Setup > Quote Settings and visible on the Opportunity page layout
- [ ] Quote template generates a valid PDF in sandbox with real opportunity and product data
- [ ] Any custom fields needed on the PDF are present on the Quote object and populated correctly
- [ ] Only one quote is ever set as synced at a time; process documented for switching sync
- [ ] Email Quote tested end-to-end: correct PDF attached, correct recipient, activity logged
- [ ] If discount approval configured: tested with a non-SysAdmin user, locking verified, rejection action reverts discount
- [ ] No CPQ QuoteLineItem assumption introduced in template or Flows
- [ ] Template character limits not exceeded (32,000 chars per Text/Image field)

---

## Notes

Record any deviations from the standard pattern and why:

- (e.g., "Used Apex trigger instead of Flow for field mirroring due to high quote volume and DML limit concerns")
- (e.g., "Discount approval threshold set to 20% per Sales VP request, not the standard 15% suggested in documentation")
