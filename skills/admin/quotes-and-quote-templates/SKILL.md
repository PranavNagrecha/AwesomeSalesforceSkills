---
name: quotes-and-quote-templates
description: "Use when configuring standard Salesforce Quotes, building or customizing quote templates for PDF generation, emailing quotes to customers, syncing quotes to opportunity products, or setting up discount approval processes on quotes. Triggers: 'create quote', 'quote template', 'quote PDF', 'email quote', 'quote sync', 'synced quote', 'discount approval', 'quote line items'. NOT for CPQ (Salesforce Revenue Cloud / SBQQ) quote configuration, quote line scheduling, or order management."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - User Experience
  - Operational Excellence
triggers:
  - "how do I create a quote PDF and email it to a customer"
  - "quote sync is not updating opportunity products correctly"
  - "my quote template is missing fields or showing wrong data"
  - "can only one quote be synced to an opportunity at a time"
  - "how do I set up a discount approval on a quote"
  - "quote line items not reflecting on the opportunity"
  - "how do I add custom fields to a quote or quote line item"
tags:
  - quotes
  - quote-templates
  - pdf-generation
  - quote-sync
  - discount-approval
  - opportunity-products
inputs:
  - "Salesforce org edition (Quotes require Performance, Unlimited, Enterprise, Developer, or Professional with add-on)"
  - "Whether Quotes is enabled in Setup > Quotes Settings"
  - "Existing opportunity and product catalog structure"
  - "Custom fields on Opportunity/OpportunityLineItem that need to appear on the quote"
  - "Whether discount approval workflow is needed and who approves"
outputs:
  - "Quote configuration guidance and template design"
  - "Quote sync setup and troubleshooting steps"
  - "PDF generation and email quote workflow"
  - "Discount approval process design on Quote object"
  - "Custom field mapping recommendations and Apex-based workarounds"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Quotes and Quote Templates

Use this skill when a practitioner needs to configure standard Salesforce Quotes: creating quotes from opportunities, building PDF-ready quote templates, emailing quotes, managing quote sync with opportunity products, or wiring up a discount approval process. This skill does NOT cover CPQ (SBQQ) configuration — route those requests to the `architect/cpq-vs-standard-products-decision` skill.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Quotes must be enabled**: Confirm Quotes is turned on in Setup > Quote Settings. Without this, the Quotes related list will not appear on Opportunities and the Quote object will not be accessible.
- **Edition requirement**: Standard Quotes are available in Performance, Unlimited, Enterprise, and Developer editions; Professional Edition requires an add-on. Verify the org edition before designing any Quote-based workflow.
- **CPQ vs Standard**: The most common wrong assumption is that standard Quotes and CPQ Quotes are the same product on the same object. Standard Quotes use `QuoteLineItem`; CPQ uses `SBQQ__QuoteLine__c`. Standard quote templates cannot render CPQ quote lines. Never mix them without explicit confirmation of which product is licensed.
- **Custom field gap**: Custom fields on `Opportunity` or `OpportunityLineItem` do NOT automatically appear on `Quote` or `QuoteLineItem`. There is no declarative mapping; you need custom Apex or a Record-Triggered Flow.
- **Sync constraint**: Only one quote per opportunity can be synced at a time. The opportunity's `SyncedQuoteId` field holds the ID of the synced quote. Changing the synced quote stops bidirectional sync on the previous quote immediately.

---

## Core Concepts

### Quote Sync and the SyncedQuoteId Field

Quote sync is the mechanism by which quote line items and opportunity products stay in alignment. When a quote is synced to its parent opportunity, the `Opportunity.SyncedQuoteId` is set to the quote's ID. From that point:

- Changes to quote line items flow down to opportunity products (OpportunityLineItem).
- Changes to opportunity products flow back up to quote line items.
- The sync is **bidirectional** but only for the single synced quote.

Only one quote can be synced to an opportunity at a time. If you start syncing a second quote, sync on the first quote stops and the first quote's lines diverge from the opportunity from that moment forward. This is a platform constraint, not a configuration option.

Stopping sync does not delete or revert data — it simply stops the bidirectional update. The opportunity's product lines remain as they were at the time sync was stopped.

### Quote Templates and PDF Generation

Quote templates control the layout of the PDF that is generated when a user clicks "Generate PDF" or "Save as PDF" on a quote. Templates are configured in Setup > Quote Templates and use a rich-text editor with distinct sections: Header, Body (line items table), and Footer.

Key platform limits:
- Each Text/Image field block in a template has a **32,000-character limit**.
- Templates do **not** support right-to-left text rendering.
- Templates do **not** support custom fonts or custom brand color hex codes natively — styling is limited to what the rich-text editor exposes.
- The standard line items table in the template renders `QuoteLineItem` records only. It cannot render custom objects or CPQ's `SBQQ__QuoteLine__c` records.

The template can include standard and custom fields from the `Quote` object in the header/footer. Fields from `QuoteLineItem` are available in the body table columns. Fields from `Opportunity` are NOT automatically available — they must be mapped to a Quote field first.

### Emailing Quotes

A quote PDF can be emailed to the contact named on the quote directly from the quote record using the "Email Quote" button. The email uses the default quote email template unless customized. Key behaviors:

- The email is logged as an activity on both the Quote and the related Opportunity.
- The recipient defaults to the contact in the `Quote.ContactId` field.
- The attached PDF is re-generated at time of send, using the quote template currently selected on the quote record.
- Org-wide email settings (deliverability, from address) apply to quote emails exactly as they do to all outbound email.

### Discount Approvals on Quotes

Standard Approval Processes can be built on the `Quote` object using the same mechanism as any other object. Common patterns:

- Trigger approval when `Quote.Discount` exceeds a threshold.
- Lock the quote record on submission so it cannot be edited during review.
- Drive approver routing from a lookup field on the quote (e.g., `Quote.OwnerId` manager) or from a named user.

Because Quotes are children of Opportunities, consider whether the approval should block the opportunity stage progression too — if so, add a validation rule on Opportunity that prevents stage advancement while the related quote is pending approval.

---

## Common Patterns

### Pattern: Single Synced Quote as Order of Record

**When to use:** An opportunity has multiple quote drafts explored across different pricing scenarios, and the team wants one canonical quote that drives opportunity revenue.

**How it works:**
1. Create multiple quote records from the opportunity for different scenarios.
2. When a scenario is selected, click "Start Sync" on that quote. This sets `Opportunity.SyncedQuoteId`.
3. All line item edits from this point happen on the synced quote, and the opportunity products update automatically.
4. Before closing the opportunity, confirm the synced quote reflects the final agreed terms.
5. Optionally generate the PDF and email it to the customer from the same quote record.

**Why not the alternative:** Editing opportunity products directly while a quote is synced can cause conflicts. Always edit from the synced quote's line items when sync is active.

### Pattern: Multi-Section Quote Template with Custom Header Fields

**When to use:** The business wants the quote PDF to include information from the related Opportunity or Account (e.g., Account Industry, Opportunity source, custom agreement terms).

**How it works:**
1. Create custom fields on the `Quote` object that mirror the Opportunity/Account fields needed.
2. Populate those fields via a Flow triggered on Quote creation/update from the parent Opportunity.
3. In Setup > Quote Templates, add those custom Quote fields to the Header section of the template.
4. The PDF will render the latest values of those fields at generation time.

**Why not the alternative:** You cannot reference `Opportunity.Account.Industry` directly in a quote template field merge. The template's field picker only surfaces `Quote` and `QuoteLineItem` fields. Formula fields on Quote that reference parent objects work for simple cases, but complex cases require the Flow-based population approach.

### Pattern: Discount Approval Gate on Quote

**When to use:** Sales reps can offer discounts up to a threshold (e.g., 10%) without approval; anything above that requires manager sign-off.

**How it works:**
1. Build a standard Approval Process on the `Quote` object.
2. Entry criteria: `Quote.Discount > 10`.
3. Lock the record on submission.
4. Route to the quote owner's manager or a specific approver queue.
5. On approval, unlock the quote and optionally trigger a Flow to advance the opportunity stage.
6. On rejection, unlock the quote and revert the discount field to the threshold value using a field update action.

**Why not the alternative:** Doing this only on the Opportunity stage misses scenarios where the discount is embedded in the quote line items rather than the header discount field.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need to produce a customer-facing PDF from an opportunity | Standard Quote + Quote Template | Built-in PDF generation; no code required |
| Opportunity has multiple pricing scenarios under evaluation | Create multiple quotes, sync only one | Only one quote can be synced; others remain as history |
| Custom fields from Opportunity must appear on PDF | Add custom fields to Quote object, populate via Flow | Template field picker only shows Quote fields |
| Need approval for discounts > a threshold | Approval Process on Quote object | Standard mechanism; locks record during review |
| CPQ quote lines need to appear on the PDF | CPQ PDF template (not standard quote template) | Standard templates render QuoteLineItem only |
| Quote data must feed into an ERP or downstream system | Standard Quote/QuoteLineItem API or outbound integration via Flow | Standard objects are fully API-accessible |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm prerequisites** — Verify Quotes is enabled in Setup > Quote Settings, confirm the org edition supports Quotes, and establish whether this is a standard Quotes or CPQ request. If CPQ is involved, stop and route to the `architect/cpq-vs-standard-products-decision` skill.
2. **Map the requirements to objects** — Determine which fields need to appear on the quote PDF and identify gaps (custom fields on Opportunity/Account that do not exist on Quote). Design a field mirroring strategy using formula fields or Flow-based population.
3. **Design the quote template** — In Setup > Quote Templates, build a template with Header (company/customer info, custom Quote fields), Body (QuoteLineItem table with required columns), and Footer (terms, signature block). Stay within the 32,000-character-per-field limit. Test PDF generation in a sandbox with realistic data before deploying.
4. **Configure quote sync behavior** — Communicate to users that only one quote can be synced at a time and document the process for switching sync between quotes. If the business needs to lock a quote once sent, add a status-based validation rule to prevent edits after the quote reaches "Presented" status.
5. **Set up email quote workflow** — Confirm the quote email template is configured and the org email deliverability settings allow outbound email. Test the "Email Quote" flow end-to-end from a test quote with a real PDF attachment.
6. **Build discount approval if required** — Create the Approval Process on Quote, define entry criteria, configure record locking, set up approver routing, and define approval/rejection actions. Test with a user who does NOT have the "Modify All Data" permission.
7. **Validate and document** — Run the checker script, verify against the Review Checklist, document any custom field mapping decisions, and confirm sync behavior is understood by the sales ops team.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Quotes is enabled in Setup > Quote Settings and visible on the Opportunity page layout
- [ ] Quote template generates a valid PDF in sandbox with real opportunity and product data
- [ ] Any custom fields needed on the PDF are present on the Quote object and populated correctly (via formula or Flow)
- [ ] Only one quote is ever set as synced at a time; process documented for switching sync
- [ ] Email Quote tested end-to-end: correct PDF attached, correct recipient, activity logged on both Quote and Opportunity
- [ ] If discount approval is configured: tested with a non-SysAdmin user, record locking verified, rejection action reverts discount field
- [ ] No CPQ-related QuoteLineItem assumption introduced (standard templates do not render SBQQ__QuoteLine__c)
- [ ] Template character limits not exceeded (32,000 chars per Text/Image field)

---

## Salesforce-Specific Gotchas

1. **Only one synced quote per opportunity** — The `Opportunity.SyncedQuoteId` can hold exactly one quote ID. Starting sync on a second quote silently stops sync on the first. Teams often discover this mismatch only when closing the opportunity.
2. **Standard quote templates cannot render CPQ quote lines** — If CPQ is installed, quote lines live in `SBQQ__QuoteLine__c`, not `QuoteLineItem`. A standard template on a CPQ quote generates a PDF with a blank line items section.
3. **Custom fields on Opportunity/OpportunityLineItem do not auto-map to Quote/QuoteLineItem** — There is no declarative field mapping. Creating a custom field on Opportunity and expecting it to copy to Quote will not work without custom Apex or a Flow.
4. **SysAdmins bypass approval processes** — Testing a discount approval as a System Administrator will always appear to work. Test with a standard Sales Rep profile user to validate actual approval routing.
5. **Quote PDF re-generates at email send time** — If a quote template is modified after a PDF was saved on the record, clicking "Email Quote" generates a NEW PDF using the updated template. Lock the template before PDFs are sent to customers.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Quote template configuration | Header/body/footer layout, field selection, and styling decisions for the quote template |
| Quote sync process doc | Documented rules for when to sync, how to switch synced quotes, and what happens to lines when sync stops |
| Discount approval design | Entry criteria, approver routing, record lock behavior, and approval/rejection actions on the Quote object |
| Custom field mapping plan | List of Opportunity/Account fields needed on the PDF and the mechanism (formula or Flow) used to populate them on Quote |

---

## Related Skills

- `architect/cpq-vs-standard-products-decision` — Use when the org is evaluating CPQ vs standard Quotes, or when CPQ is already installed and quote line rendering on PDFs is failing. NOT for standard Quotes configuration.
- `admin/approval-processes` — Use when the discount approval process on quotes becomes complex (multi-step, exception paths, delegation). NOT for quote sync or template design.
- `admin/products-and-pricebooks` — Use when the product catalog, pricebook structure, or pricing rules are the root cause of incorrect quote line item amounts. NOT for quote template layout.
- `admin/email-templates-and-alerts` — Use when the quote email template itself needs redesign or the email deliverability configuration is the issue. NOT for quote PDF template layout.
- `admin/opportunity-management` — Use when the relationship between opportunities, products, and quote sync needs architectural review as part of a broader sales process redesign.
