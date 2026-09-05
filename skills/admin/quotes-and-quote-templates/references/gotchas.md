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

## Gotcha 5: A Discount Approval Cannot Write Back to `Quote.Discount`

**What happens:** The approval process is designed so that rejection resets the discount to the allowed threshold via a field update on `Quote.Discount`. The field update cannot be created against that field, or it saves and then does nothing, and the quote keeps the discount the approver just rejected.

**When it occurs:** Whenever the rejection branch of a Quote approval is designed around the header discount rather than the line items — which is the natural reading of an entry criterion written as `Quote.Discount > 15`.

**How to avoid:** Read `Quote.Discount`, write `QuoteLineItem.Discount`. `Quote.Discount` is type `percent` with properties `Filter, Nillable, Sort` — no `Create`, no `Update` — and is defined as the difference between the QuoteLineItem subtotal and its discounted total, divided by that subtotal (`object_reference.txt` L239578–239592). It is a roll-up of the lines, so it is filterable in entry criteria but not writable by anything. The editable discount is `QuoteLineItem.Discount`, an editable number from 0 to 100 with `Create, Filter, Nillable, Sort, Update` (`object_reference.txt` L240758–240767), or the fixed-amount `QuoteLineItem.DiscountAmount` from API 59.0. Point the rejection action at the lines, or drive the reset from a flow that loops the quote's line items.

UNVERIFIED (2026-09-05): this skill previously stated that System Administrators bypass approval process entry criteria, so a SysAdmin test never fires the approval. Neither the Metadata API Developer Guide nor the Object Reference documents such a bypass, and help.salesforce.com cannot be fetched to confirm or refute it — treat the claim as unproven and do not repeat it as fact. The testing advice still stands for a separate reason: an administrator can edit records that an approval process has locked, so an admin's run never exercises the lock that a rep will hit.

---

## Gotcha 6: Quote Template Rich-Text Fields Have a 32,000-Character Limit Per Block

**What happens:** An admin pastes a long terms-and-conditions block into the Footer text block of a quote template. The save appears to succeed, but when the PDF is generated, the text is truncated or PDF generation fails with a generic error.

**When it occurs:** When legal or marketing teams provide lengthy boilerplate text for the quote PDF footer or header.

**How to avoid:** Split long text content across multiple Text/Image field blocks in the template rather than pasting one oversized block, and generate a PDF with full production-length content in a sandbox before the template goes live.

UNVERIFIED (2026-09-05): the 32,000-character per-block limit for quote template Text/Image fields is a Setup-UI limit documented only on help.salesforce.com, which cannot be fetched. The nearest grounded 32,000 in the Object Reference is `Quote.Description`, a textarea with "Limit: 32,000 characters" (`object_reference.txt` L239568–239574) — a different field on a different surface. The splitting advice is safe regardless of the exact number; do not quote the number to a customer as an API-documented limit.


---

## Gotcha 7: `Opportunity.SyncedQuoteID` Is Read-Only Inside an Apex Trigger

**What happens:** Someone writes a trigger to automate quote sync — start sync when a quote reaches Approved, stop it when the quote is superseded. The trigger compiles, deploys, and the assignment to `SyncedQuoteId` does nothing. Sync state never changes, and there is no error to chase.

**When it occurs:** Any attempt to make sync automatic from Apex trigger context, which is the obvious place to put it because both Quote and Opportunity trigger contexts are right there.

**How to avoid:** The Object Reference is explicit for this field: "Read only in an Apex trigger. The ID of the Quote that syncs with the opportunity. Setting this field lets you start and stop syncing between the opportunity and a quote. The ID has to be for a quote that is a child of the opportunity." (`object_reference.txt` L192906–192912). Outside trigger context the field is `Create, Filter, Nillable, Update`, and the guide's own Java samples start sync by setting `SyncedQuoteId` and stop it by nulling the field via `setFieldsToNull` (`object_reference.txt` L192968–193010). So: an API call, a Queueable, or an invocable action fired asynchronously works; the trigger body itself does not. The second half of that sentence bites too — the quote must already be a child of that opportunity, so a quote created without a parent (`enableQuotesWithoutOppEnabled`) can never be synced until it has one, and `Quote.OpportunityId` is `Create, Filter` only, with no `Update`, so it cannot be reparented after the fact.

---

## Gotcha 8: Quote Sync Silently Discards Quantity and Price Edits on Scheduled Lines

**What happens:** A rep edits the quantity on a synced quote line. The record saves with no error. The value reverts, or never changes at all, and the opportunity keeps the old number. Nobody sees a failure because there was no failure.

**When it occurs:** When the opportunity line item that the quote line is synced with carries a quantity schedule or a revenue schedule — common in subscription, milestone-billing and multi-shipment deals.

**How to avoid:** Check `QuoteLineItem.HasQuantitySchedule` and `QuoteLineItem.HasRevenueSchedule` before promising editability. Both are read-only booleans that report on the *synced opportunity line item*, and the Object Reference states the consequence plainly: with a revenue schedule the `GrandTotal` and `TotalPrice` fields can't be updated, with a quantity schedule the `Quantity` field can't be updated, and "The system ignores any attempt to update this field. The update isn't rejected but the updated value is ignored." (`object_reference.txt` L240848–240870). `QuoteLineItem.TotalPrice` repeats it: "This field is read only if the quote line item has a revenue schedule." (`object_reference.txt` L241688–241697). Surface these two booleans on the quote line item related list so the condition is visible before someone spends an afternoon on it.

---

## Gotcha 9: `Quote.GrandTotal` Cannot Be Referenced in a Formula Field on Quote

**What happens:** An admin builds a formula field on Quote — a banding field, a margin check, a discount-tier label — that references `GrandTotal`. The formula editor rejects it with a spelling error for a field that is plainly on the page layout in front of them.

**When it occurs:** Any time quote-total logic is pushed into a Quote formula field, which is the first thing anyone reaches for when the requirement is "flag quotes over $250k".

**How to avoid:** The Object Reference documents this as a property of the field, not a bug: "The GrandTotal is a system-calculated summary field and is not directly referenceable or usable in custom formula fields on the Quote object. Attempts to do so result in an error message. For example, 'Error: Field GrandTotal does not exist. Check spelling.' To perform calculations based on the total value of a quote, consider using a Roll-Up Summary field from related Quote Line Items or performing calculations directly on the QuoteLineItem object." (`object_reference.txt` L239630–239637). Take the guide's own advice: roll up from `QuoteLineItem`, or compute on the line. Note that the error message names the wrong cause — it reads as a typo, which is why this one burns an hour before anyone looks it up.

---

## Gotcha 10: Deploying a Partial `QuoteStatus` Value Set Deactivates Every Status You Left Out

**What happens:** An admin needs to add one status, so they hand-write a `QuoteStatus.standardValueSet-meta.xml` containing that one value plus the two or three they care about, and deploy. The deploy succeeds. Every other standard status in the target org is now inactive: existing quotes show blanks, `ISPICKVAL` formulas stop matching, and flows that set a dropped status start failing.

**When it occurs:** Whenever a standard value set is authored from scratch rather than retrieved, edited and redeployed — which is exactly what happens when someone copies a two-value sample out of a doc.

**How to avoid:** Retrieve first, always: `sf project retrieve start --metadata "StandardValueSet:QuoteStatus"`. The Metadata API guide states the rule under CustomValue: "If picklist values are missing from a component definition, they get deactivated when deployed. Deactivation occurs for picklist values of both standard and custom fields." (`api_meta.txt` L47481–47483). The standard `Quote.Status` options are `Draft`, `Needs Review`, `In Review`, `Approved`, `Rejected`, `Presented`, `Accepted` and `Denied` (`object_reference.txt` L239996–240005); a deployed file must carry all of the ones the org still uses. Two related traps sit next to this one: `StandardValueSet` refuses the `*` wildcard in `package.xml` (`api_meta.txt` L130830–130832), so the member must be named explicitly, and a value set deployed with an empty `standardValue` array is a hard error (`api_meta.txt` L130770–130774). `scripts/check_quotes_and_quote_templates.py` fails the manifest when standard statuses are missing.

---

## Gotcha 11: There Is No `QuoteTemplate` Metadata Type, So Templates Do Not Deploy

**What happens:** A team builds and tests a quote template in a full sandbox, then tries to promote it with the rest of the release. The template is not in the retrieve, not in `package.xml`, and not in the org after the deploy. Someone rebuilds it by hand in production against the clock, and the production PDF quietly differs from the one that was signed off.

**When it occurs:** On the first release that includes a quote template, in any org with a source-controlled deployment pipeline.

**How to avoid:** Plan for it up front rather than discovering it at cutover. The Metadata API Developer Guide contains the token `QuoteTemplate` exactly once, and it is a value of the `SummaryLayoutStyle` enumeration on `Layout.SummaryLayout`, not a component type — no file suffix, no directory location, no field table, no sample definition (`api_meta.txt` L83162–83170). The deployable surface around the template is real and should carry the release: `QuoteSettings`, the `QuoteStatus` value set, custom fields on Quote, validation rules and layouts. The template itself needs a Setup rebuild plus a reviewable artefact — `templates/quote-template-checklist.json`, linted by the skill's checker — and an after-the-fact audit trail via `QuoteDocument.DocumentTemplate`, "The ID of the template used to generate the document" (`object_reference.txt` L240440–240448). Budget the manual rebuild into the release plan; do not let it be a surprise at 2 a.m.

---

## Gotcha 12: A Quote Cannot Hold Line Items Until It Has a Price Book, and Lines Cannot Be Repointed

**What happens:** A data load or a Flow creates quotes, then fails to insert quote line items. Or lines insert against the wrong products and an admin tries to fix them in place by updating `Product2Id` — which is rejected.

**When it occurs:** Quote creation by API, Flow or data load, where the price book is assumed to come along automatically; and any remediation of already-created lines.

**How to avoid:** Two grounded constraints. First: "A quote record can have QuoteLineItem records only if the quote has a Pricebook2. A QuoteLineItem must correspond to a Product2 that is listed in the quote's Pricebook2." and "When you create or update a QuoteLineItem, the API verifies that the line item corresponds to a PricebookEntry in the Pricebook2 associated with the quote." (`object_reference.txt` L241790–241812). So `Quote.Pricebook2Id` (`Create, Filter, Nillable, Update`) must be populated before any line insert, and the price book must actually contain the products. Second: `QuoteLineItem.PricebookEntryId`, `Product2Id` and `QuoteId` are all `Create, Filter, Group, Sort` with no `Update` (`object_reference.txt` L241300–241320, L241090–241100) — you cannot swap a line's product or move it to another quote. Delete and recreate. Multicurrency adds a third: `CurrencyIsoCode` on the line "comes from the related quote and can't be changed", and the quote's own currency "is copied from the related Opportunity and can't be changed" (`object_reference.txt` L241800–241806, L239560–239566), so a currency mismatch is fixed on the opportunity, not on the quote.

---

## Gotcha 13: `allowEmail` on the Status Value — Not a Permission — Decides Who Can Email a Quote PDF

**What happens:** A team builds a validation rule to stop reps emailing an unapproved quote, and it fires on the wrong saves, or it does not fire at all because the Email Quote action does not go through the save path they guarded. Meanwhile the actual control sits unset in a value set nobody has opened.

**When it occurs:** Whenever "prevent sending before approval" is specified, and the implementer reaches for validation rules, permission sets or a locked layout because they have never seen the real switch.

**How to avoid:** Use `allowEmail` on the individual `QuoteStatus` value. The Metadata API guide describes it as a `StandardValue` boolean: "Indicates whether this value lets users email a quote PDF (true), or not (false). This field is only relevant for the Status field in quotes." Available in API version 18.0 and later (`api_meta.txt` L47538–47541). It is per status value, it is deployable in the `QuoteStatus` standard value set, and it needs no formula. Set it false on `Draft`, `Needs Review`, `In Review`, `Rejected` and `Denied`, and true on the statuses that represent an approved, sendable quote. `references/metadata-examples.md` §2 has the full file. The single most instructive part of this gotcha is that the control is invisible in the Setup picklist editor's normal view, which is why almost every org reimplements it badly in a validation rule.
