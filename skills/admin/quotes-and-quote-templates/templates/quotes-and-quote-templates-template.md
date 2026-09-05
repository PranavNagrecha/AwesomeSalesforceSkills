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
| Header | Quote.Name, Quote.QuoteNumber, Quote.ExpirationDate, custom mirror fields | Only Quote fields merge here; mirror Opportunity/Account values first |
| Body (line items table) | Product Name, Quantity, Unit Price, Discount, Total Price | Confirm columns with business stakeholders; line order comes from QuoteLineItem.SortOrder |
| Footer | Terms and conditions text, signature block | Split long text across blocks rather than one oversized block |

**Template is NOT deployable** — there is no QuoteTemplate metadata type. Record the build in
`quote-template-checklist.json` and name the owner of the manual rebuild in each target org:

- **Checklist file committed at:** ______________________
- **Rebuild owner (per org):** ______________________

## Email Gate (allowEmail)

`allowEmail` on each QuoteStatus value decides whether the Email Quote action is available.
Fill this in before deploying the standard value set:

| Status | allowEmail | Why |
|---|---|---|
| Draft | false | |
| Needs Review | false | |
| In Review | false | |
| Approved | true | |
| Rejected | false | |
| Presented | true | |
| Accepted | true | |
| Denied | false | |

---

## Approval Process Design (if applicable)

- **Object:** Quote
- **Entry criteria:** Quote.Discount > ____%  (read-only field, but filterable — valid as a criterion)
- **Record lock on submission:** Yes / No
- **Approver routing:** Named user / Manager hierarchy / Lookup field (specify)
- **Approval action:** Unlock record, set Quote.Status = 'Approved' (a status with allowEmail = true)
- **Rejection action:** Unlock record, set Quote.Status = 'Rejected' (allowEmail = false), email submitter,
  and reset **QuoteLineItem.Discount** on the lines — NOT Quote.Discount, which has no Create/Update
  property and cannot be the target of a field update.
- **Non-admin test user for the lifecycle test:** ______________________

---

## Checklist

Copy from SKILL.md Review Checklist and tick off as completed:

- [ ] Quotes is enabled in Setup > Quote Settings and visible on the Opportunity page layout
- [ ] Quote template generates a valid PDF in sandbox with real opportunity and product data
- [ ] Any custom fields needed on the PDF are present on the Quote object and populated correctly
- [ ] Only one quote is ever set as synced at a time; process documented for switching sync
- [ ] Email Quote tested end-to-end: correct PDF attached, correct recipient, activity logged
- [ ] If discount approval configured: tested with a non-admin user, locking verified, rejection resets QuoteLineItem.Discount
- [ ] No CPQ QuoteLineItem assumption introduced in template or Flows
- [ ] Template character limits not exceeded (32,000 chars per Text/Image field)
- [ ] QuoteStatus standard value set retrieved, edited and redeployed **complete** (partial deploys deactivate omitted statuses)
- [ ] `python3 scripts/check_quotes_and_quote_templates.py --manifest-dir <dir>` returns no ERROR lines
- [ ] Reconciliation queries run (see references/metadata-examples.md section 8b)

---

## Notes

Record any deviations from the standard pattern and why:

- (e.g., "Used Apex trigger instead of Flow for field mirroring due to high quote volume and DML limit concerns")
- (e.g., "Discount approval threshold set to 20% per Sales VP request, not the standard 15% suggested in documentation")
