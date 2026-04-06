# Gotchas — Quotes and Quote Templates

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Only One Quote Can Be Synced Per Opportunity at a Time

**What happens:** When a user clicks "Start Sync" on a second quote, Salesforce updates `Opportunity.SyncedQuoteId` to point to the new quote and silently stops syncing the first quote. The first quote's line items are frozen at the values they had when sync stopped.

**When it occurs:** Any time a rep creates a revised quote and starts sync on it without explicitly stopping sync on the previous quote first.

**How to avoid:** Establish a clear process: before starting sync on a new quote, the rep must click "Stop Sync" on the currently synced quote and confirm which quote is the active version. Consider a Flow that warns the rep if another quote on the same opportunity already has `Quote.IsSyncing = true`.

---

## Gotcha 2: Standard Quote Templates Cannot Render CPQ Quote Lines

**What happens:** If Salesforce CPQ (SBQQ) is installed, quote lines are stored in `SBQQ__QuoteLine__c`, not the standard `QuoteLineItem` object. The standard quote template body table is hard-coded to query `QuoteLineItem`. When a standard template is applied to a CPQ quote, the PDF body line items section is blank.

**When it occurs:** When an org runs both standard Quotes and CPQ simultaneously — which happens during CPQ migrations or when only some product lines use CPQ.

**How to avoid:** Never use standard Salesforce quote templates for CPQ quotes. CPQ has its own template system (SBQQ Document Templates). Maintain separate template configurations per quote type and clearly label which template is for which.

---

## Gotcha 3: Custom Fields on Opportunity/OpportunityLineItem Do Not Map to Quote/QuoteLineItem Automatically

**What happens:** An admin creates a custom field on `Opportunity` or `OpportunityLineItem` and expects it to appear on the related `Quote` or `QuoteLineItem` when a quote is created. Nothing copies over.

**When it occurs:** Any time the data model includes custom fields on the opportunity side that need to appear on customer-facing quote documents.

**How to avoid:** Explicitly create matching custom fields on `Quote` and/or `QuoteLineItem`. Populate them via a Record-Triggered Flow on Quote creation and update, or via custom Apex. There is no platform-native "Quote Field Mapping" configuration equivalent to Lead Conversion Field Mapping.

---

## Gotcha 4: Quote PDF Re-Generates Using the Current Template at Email Send Time

**What happens:** A user generates a PDF and reviews it — it looks correct. The admin then modifies the quote template. The user clicks "Email Quote" and Salesforce generates a fresh PDF at that moment using the now-modified template. If the template change introduced a defect, the customer receives a broken PDF.

**When it occurs:** Any time the quote template is modified between PDF review and PDF delivery to the customer.

**How to avoid:** Finalize and lock the quote template before any customer-facing PDF delivery window. If the reviewed PDF must be exactly what is delivered, save the PDF as a Salesforce File on the quote record, then email it as a manual attachment rather than using the auto-generate behavior of the "Email Quote" button.

---

## Gotcha 5: System Administrators Bypass Approval Processes

**What happens:** A SysAdmin tests the discount approval process and submits a quote with a 25% discount. The approval appears to route correctly. But in production, sales reps submitting the same quote never trigger the approval.

**When it occurs:** Any time approval process testing is done exclusively with a System Administrator profile.

**How to avoid:** Always test approval processes with a user profile that mirrors the actual submitter — typically a Sales Representative profile without administrative permissions. Create a dedicated test user with the correct profile and test the full lifecycle (submit, approve, reject, recall) as that user.

---

## Gotcha 6: Quote Template Rich-Text Fields Have a 32,000-Character Limit Per Block

**What happens:** An admin pastes a long terms-and-conditions block into the Footer text block of a quote template. The save appears to succeed, but when the PDF is generated, the text is truncated or PDF generation fails with a generic error.

**When it occurs:** When legal or marketing teams provide lengthy boilerplate text for the quote PDF footer or header.

**How to avoid:** Split long text content across multiple Text/Image field blocks in the template — each block has an independent 32,000-character limit. Test PDF generation with full production-length content in a sandbox before deploying the template.
