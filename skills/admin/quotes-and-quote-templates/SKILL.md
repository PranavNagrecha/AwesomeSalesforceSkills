---
name: quotes-and-quote-templates
description: "Use when configuring standard Salesforce Quotes, building quote templates for PDF generation, emailing quotes, syncing quotes to opportunity products, or setting up discount approvals on quotes. Triggers: 'create quote', 'quote template', 'quote PDF', 'email quote', 'quote sync', 'synced quote', 'discount approval', 'quote line items', 'QuoteSettings', 'enableQuote', 'QuoteStatus', 'allowEmail', 'SyncedQuoteId', 'IsSyncing', 'QuoteLineItem', 'QuoteDocument', 'GrandTotal', 'Pricebook2Id'. NOT for CPQ (SBQQ) quote templates — use admin/cpq-quote-templates. NOT for the end-to-end quote-to-cash process — use admin/quote-to-cash-requirements."
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
  - "quote templates isn't working"
  - "deploy quote templates from sandbox to production"
  - "quote pdf shows no line items"
  - "cannot email quote pdf button greyed out"
  - "flow cannot update quote discount field"
  - "field GrandTotal does not exist check spelling on quote formula"
  - "apex trigger cannot set SyncedQuoteId to start quote sync"
  - "quote statuses disappeared after deploying standard value set"
  - "quote line item quantity change not saving"
  - "cannot add products to quote no price book"
  - "enable quotes in setup quote settings metadata"
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
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Quotes and Quote Templates

Use this skill when a practitioner needs to configure standard Salesforce Quotes: creating quotes from opportunities, building PDF-ready quote templates, emailing quotes, managing quote sync with opportunity products, or wiring up a discount approval process. This skill does NOT cover CPQ (SBQQ) configuration — route those requests to the `architect/cpq-vs-standard-products-decision` skill.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Quotes must be enabled**: Confirm Quotes is turned on in Setup > Quote Settings. Without this, the Quotes related list will not appear on Opportunities and the Quote object will not be accessible.
- **Edition requirement**: Standard Quotes are available in Performance, Unlimited, Enterprise, and Developer editions; Professional Edition requires an add-on. Verify the org edition before designing any Quote-based workflow. UNVERIFIED (2026-09-05): the edition matrix is a help.salesforce.com table and is not stated in the Metadata API guide or the Object Reference; both simply describe `QuoteSettings.enableQuote` as the switch (`api_meta.txt` L124911). Confirm the edition against the org's own Company Information page rather than from memory.
- **CPQ vs Standard**: The most common wrong assumption is that standard Quotes and CPQ Quotes are the same product on the same object. Standard Quotes use `QuoteLineItem`; CPQ uses `SBQQ__QuoteLine__c`. Standard quote templates cannot render CPQ quote lines. Never mix them without explicit confirmation of which product is licensed.
- **Custom field gap**: Custom fields on `Opportunity` or `OpportunityLineItem` do NOT automatically appear on `Quote` or `QuoteLineItem`. There is no declarative mapping; you need custom Apex or a Record-Triggered Flow.
- **Sync constraint**: Only one quote per opportunity can be synced at a time. `Opportunity.SyncedQuoteID` holds that quote's ID; setting it starts sync, nulling it stops sync, and the ID "has to be for a quote that is a child of the opportunity" (`object_reference.txt` L192906–192912). The mirror flag on the quote side, `Quote.IsSyncing`, is read-only (`Defaulted on create, Filter`).
- **No template metadata type**: Quote templates cannot be deployed. `QuoteTemplate` appears in the Metadata API Developer Guide once, as a `SummaryLayoutStyle` enum value on `Layout` (`api_meta.txt` L83162–83170), not as a component. Everything *around* the template deploys; the template is rebuilt in Setup per org. Plan the manual step into the release — see `references/gotchas.md` Gotcha 11.
- **The discount you can write is on the line, not the header**: `Quote.Discount` is a derived roll-up with properties `Filter, Nillable, Sort` and no `Create`/`Update` (`object_reference.txt` L239578–239592). `QuoteLineItem.Discount` is the editable one, 0–100 (`object_reference.txt` L240758–240767). Any design that "resets the discount" must target the lines.

---

## Questions to Ask Before Configuring

Ask these before opening Setup. Each one maps to a documented platform behaviour that silently changes the design, and each maps to a gotcha in `references/gotchas.md`.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which quote statuses is a rep allowed to email a PDF from?" | `allowEmail` on each `QuoteStatus` value is the platform gate on the Email Quote action, not a permission or a validation rule (Gotcha 13) | The `QuoteStatus` standard value set you deploy, with `allowEmail` set true/false per status |
| "Is CPQ installed, and which quote-line object does this org actually use?" | Standard templates render `QuoteLineItem`; CPQ lines are `SBQQ__QuoteLine__c` and come out blank (Gotcha 2) | A yes/no that decides whether this skill applies at all, or whether to route to `admin/cpq-quote-templates` |
| "Which Opportunity or Account values must appear on the customer-facing PDF?" | Nothing maps from Opportunity to Quote automatically; each value needs a mirror field plus a flow (Gotcha 3) | The mirror-field list and the trigger contexts (create *and* update) the flow needs |
| "Do any of these products carry a quantity or revenue schedule?" | Sync ignores `Quantity`, `TotalPrice` and `GrandTotal` writes on scheduled lines without raising an error (Gotcha 8) | An explicit editability boundary, and `HasQuantitySchedule` / `HasRevenueSchedule` on the line item related list |
| "Where does the discount live — one header number, or per line?" | `Quote.Discount` is read-only; approval rejection actions cannot write it (Gotcha 5) | An approval design whose reject branch targets `QuoteLineItem.Discount`, so rejection actually reverses something |
| "How does this template get from sandbox to production, and who owns it?" | There is no `QuoteTemplate` metadata type; the rebuild is manual every time (Gotcha 11) | A named owner, a `templates/quote-template-checklist.json` in the repo, and the rebuild booked into the release plan |
| "Should reps be able to create a quote with no opportunity behind it?" | `enableQuotesWithoutOppEnabled` gates `QuoteAccountId`, and turning it back off requires deleting existing standalone quotes first (`api_meta.txt` L124913–124919) | A settings decision made once, deliberately, instead of discovered during a rollback |

What a proper configuration adds over just enabling Quotes and drawing a template: the statuses that may email a PDF are declared in deployable metadata rather than enforced by a validation rule that the Email Quote action can route around, the approval's reject branch writes to a field that is actually writable, the manual template rebuild is a scheduled release task instead of a cutover surprise, and the synced quote can be reconciled against the opportunity's products with a query rather than by eye.

---

## Core Concepts

### Quote Sync and the SyncedQuoteId Field

Quote sync is the mechanism by which quote line items and opportunity products stay in alignment. When a quote is synced to its parent opportunity, the `Opportunity.SyncedQuoteId` is set to the quote's ID. From that point:

- Changes to quote line items flow down to opportunity products (OpportunityLineItem).
- Changes to opportunity products flow back up to quote line items.
- The sync is **bidirectional** but only for the single synced quote.

Only one quote can be synced to an opportunity at a time. If you start syncing a second quote, sync on the first quote stops and the first quote's lines diverge from the opportunity from that moment forward. This is a platform constraint, not a configuration option.

Stopping sync does not delete or revert data — it simply stops the bidirectional update. The opportunity's product lines remain as they were at the time sync was stopped.

Two things about this mechanism are not obvious from the data model:

| Field | Properties | What it constrains |
|---|---|---|
| `Opportunity.SyncedQuoteID` | `Create, Filter, Nillable, Update` — but **"Read only in an Apex trigger"** (`object_reference.txt` L192906–192912) | Sync cannot be started or stopped from trigger context. Set it via API, an async path, or the UI button. |
| `Quote.IsSyncing` | `Defaulted on create, Filter` (`object_reference.txt` L239641–239648) | Read-only. Use it to *detect* the synced quote in a query or entry criterion, never to set one. |
| `QuoteLineItem.OpportunityLineItemId` | `Create, Filter, Group, Nillable, Sort`, "populated by the API during creation... Not editable", API 40.0+ (`object_reference.txt` L240990–240998) | This is the join used to reconcile a synced quote against the opportunity's products. A null on a syncing quote is the drift to chase. |
| `QuoteLineItem.HasQuantitySchedule` / `HasRevenueSchedule` | Read-only booleans reporting on the synced opportunity line item (`object_reference.txt` L240848–240870) | When true, updates to `Quantity`, `TotalPrice` or `GrandTotal` are **ignored without being rejected**. |

### Quote Templates and PDF Generation

Quote templates control the layout of the PDF that is generated when a user clicks "Generate PDF" or "Save as PDF" on a quote. Templates are configured in Setup > Quote Templates and use a rich-text editor with distinct sections: Header, Body (line items table), and Footer.

**The template is not deployable.** The Metadata API Developer Guide has no `QuoteTemplate` component type — the token appears once, as a `SummaryLayoutStyle` enum value on `Layout` (`api_meta.txt` L83162–83170). Templates are rebuilt in Setup in every org. Track them with `templates/quote-template-checklist.json`, which `scripts/check_quotes_and_quote_templates.py` lints, and audit what actually shipped through `QuoteDocument.DocumentTemplate` — "The ID of the template used to generate the document" (`object_reference.txt` L240440–240448).

Key platform limits:
- Each Text/Image field block in a template has a **32,000-character limit**. UNVERIFIED (2026-09-05): this is a Setup-UI limit documented on help.salesforce.com, which cannot be fetched; the nearest grounded 32,000 is `Quote.Description` (`object_reference.txt` L239568–239574), a different field. Split long text regardless.
- Templates do **not** support right-to-left text rendering. UNVERIFIED (2026-09-05): help.salesforce.com only; no API-guide source.
- Templates do **not** support custom fonts or custom brand color hex codes natively — styling is limited to what the rich-text editor exposes. UNVERIFIED (2026-09-05): help.salesforce.com only; no API-guide source.
- The standard line items table in the template renders `QuoteLineItem` records only. It cannot render custom objects or CPQ's `SBQQ__QuoteLine__c` records.
- Line order in the PDF is controlled by `QuoteLineItem.SortOrder` — the value "determines the order in which a quote line item appears in the Quote Line Items related list and the Quote PDF" (`object_reference.txt` L241417–241425). It is writable (`Create, Filter, Group, Nillable, Sort, Update`), so line order is a configurable outcome, not luck.

The template can include standard and custom fields from the `Quote` object in the header/footer. Fields from `QuoteLineItem` are available in the body table columns. Fields from `Opportunity` are NOT automatically available — they must be mapped to a Quote field first. Note that `Quote.GrandTotal` cannot be used in a Quote formula field at all: it "is not directly referenceable or usable in custom formula fields on the Quote object" and the error names the wrong cause — "Field GrandTotal does not exist. Check spelling." (`object_reference.txt` L239630–239637). Roll up from `QuoteLineItem` instead.

### Emailing Quotes

A quote PDF can be emailed to the contact named on the quote directly from the quote record using the "Email Quote" button. The email uses the default quote email template unless customized. Key behaviors:

- The email is logged as an activity on both the Quote and the related Opportunity.
- The recipient defaults to the contact in the `Quote.ContactId` field.
- The attached PDF is re-generated at time of send, using the quote template currently selected on the quote record.
- Org-wide email settings (deliverability, from address) apply to quote emails exactly as they do to all outbound email.
- **Which statuses may email at all is declared per picklist value.** `StandardValue.allowEmail` on the `QuoteStatus` standard value set "indicates whether this value lets users email a quote PDF (true), or not (false). This field is only relevant for the Status field in quotes." Available in API version 18.0 and later (`api_meta.txt` L47538–47541). This is deployable metadata, it is the intended control, and it is the reason most "block sending before approval" validation rules are unnecessary. See `references/metadata-examples.md` §2.

### Discount Approvals on Quotes

Standard Approval Processes can be built on the `Quote` object using the same mechanism as any other object. Common patterns:

- Trigger approval when `Quote.Discount` exceeds a threshold. This works as an *entry criterion* because the field is filterable.
- Lock the quote record on submission so it cannot be edited during review.
- Drive approver routing from the quote owner's manager (Quote is an ownable object — `QuoteOwnerSharingRule` and `QuoteShare` exist from API 41.0, `object_reference.txt` L240148–240152) or from a named user.
- Set `Status` to a value whose `allowEmail` is `false` while the quote is in review, and to one whose `allowEmail` is `true` on approval. That is the send gate.

**The trap in the reject branch:** you cannot write `Quote.Discount` back. It is `Filter, Nillable, Sort` with no `Create` and no `Update`, and is defined as a roll-up of the line items' discounted totals (`object_reference.txt` L239578–239592). Point the rejection field update at `QuoteLineItem.Discount` (`Create, Filter, Nillable, Sort, Update`, 0–100 — `object_reference.txt` L240758–240767) or at `QuoteLineItem.DiscountAmount`, or reset the lines from a flow. The same applies to `GrandTotal`, `Subtotal`, `TotalPrice`, `LineItemCount`, `QuoteNumber`, `IsSyncing` and `AccountId`; `Tax` and `ShippingHandling` *are* writable.

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
5. Hold `Status` on a value whose `allowEmail` is `false` (`In Review`) for the duration, so the PDF cannot be sent mid-approval.
6. On approval, unlock the quote and set `Status` to a value whose `allowEmail` is `true` (`Approved`).
7. On rejection, unlock the quote and reset the **line-level** discount — a flow over the quote's `QuoteLineItem` records writing `Discount` (or `DiscountAmount`), never a field update on `Quote.Discount`.

**Why not the alternative:** Doing this only on the Opportunity stage misses scenarios where the discount is embedded in the quote line items rather than the header discount field. And the naive version of step 7 — a field update on `Quote.Discount` — cannot be built: the field has no `Create` and no `Update` property because it is a roll-up of the lines (`object_reference.txt` L239578–239592). The header number moves only when the lines move.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need to produce a customer-facing PDF from an opportunity | Standard Quote + Quote Template | Built-in PDF generation; no code required |
| Opportunity has multiple pricing scenarios under evaluation | Create multiple quotes, sync only one | Only one quote can be synced; others remain as history |
| Custom fields from Opportunity must appear on PDF | Add custom fields to Quote object, populate via Flow | Template field picker only shows Quote fields |
| Need approval for discounts > a threshold | Approval Process on Quote, entry criterion on `Quote.Discount`, reject action on `QuoteLineItem.Discount` | `Quote.Discount` is filterable but not writable (`object_reference.txt` L239578–239592) |
| Reps must not email a quote PDF before approval | `allowEmail` = false on the pre-approval `QuoteStatus` values | Platform-native per-status gate on the Email Quote action (`api_meta.txt` L47538–47541) — no validation rule needed |
| Quote template must move sandbox → production | Manual Setup rebuild + `templates/quote-template-checklist.json` in the repo | No `QuoteTemplate` metadata type exists (`api_meta.txt` L83162–83170) |
| Need a "quote over $X" flag on the Quote record | Roll-up summary from QuoteLineItem, or compute on the line | `Quote.GrandTotal` is not referenceable in a Quote formula field (`object_reference.txt` L239630–239637) |
| Line order on the PDF matters | Set `QuoteLineItem.SortOrder` | It "determines the order in which a quote line item appears in the Quote Line Items related list and the Quote PDF" (`object_reference.txt` L241417–241425) |
| CPQ quote lines need to appear on the PDF | CPQ PDF template (not standard quote template) | Standard templates render QuoteLineItem only |
| Quote data must feed into an ERP or downstream system | Standard Quote/QuoteLineItem API or outbound integration via Flow | Standard objects are fully API-accessible |

---

## Recommended Workflow

1. **Establish which quoting product this org runs, then read the guides.** `ls` for `SBQQ__*` in the source, or query `SBQQ__Quote__c`. If CPQ owns the quote lines, stop and route to `admin/cpq-quote-templates` or `architect/cpq-vs-standard-products-decision` — standard templates render `QuoteLineItem` and produce an empty body for CPQ quotes. If standard Quotes, read `references/gotchas.md` before designing anything; Gotchas 5, 8, 9, 11 and 13 each invalidate a design that looks correct on paper.
2. **Answer the seven questions above and write the answers down.** The `allowEmail` question and the schedule question in particular change what you build, not just how you build it. Fill in `templates/quotes-and-quote-templates-template.md` as you go.
3. **Build the deployable layer from `references/metadata-examples.md`.** In order: `settings/Quote.settings-meta.xml` (§1) → the **complete** `QuoteStatus` standard value set with `allowEmail` per status (§2) → custom mirror fields on Quote (§3) → validation rules (§4) → layout (§6) → permission-set FLS. Retrieve `StandardValueSet:QuoteStatus` before editing it; a partial file deactivates every status you omit.
4. **Build the template by hand in a sandbox and record it in `templates/quote-template-checklist.json`.** There is no metadata type, so this JSON file *is* the reviewable artefact. Set `sections.line_items.sort_field` to `SortOrder`, list the header's Quote fields, and leave `verified_in_org.*` false until each has actually been done in an org.
5. **Run the checker against the manifest.** `python3 scripts/check_quotes_and_quote_templates.py --manifest-dir force-app/main/default`. It fails the manifest on: `enableQuote` not true when Quote metadata ships; standard statuses omitted from the value set; statuses referenced by rules or flows that the value set does not define; `GrandTotal` in a Quote formula; flows writing read-only Quote fields; a stray `*.quoteTemplate-meta.xml`; and a checklist whose `statuses_allowing_email` disagrees with the deployed `allowEmail` values. Use `--quiet` in CI to gate on ERROR only.
6. **Test the three things that fail silently.** (a) Email Quote from a status with `allowEmail` false — the action must not be offered. (b) Edit `Quantity` on a synced line whose `HasQuantitySchedule` is true — confirm with the reconciliation SOQL in `references/metadata-examples.md` §8b that the value did not move, and that nobody got an error. (c) Submit and reject a discount approval as a non-admin user, then verify the discount actually reversed on `QuoteLineItem`, not just on the header roll-up.
7. **Reconcile and hand over.** Run the three queries in §8b (synced quote vs. opportunity products; quote lines with a null `OpportunityLineItemId`; more than one quote claiming to sync per opportunity) and the `QuoteDocument` audit query in §8c. Deliver the Review Checklist, the filled checklist JSON, and a named owner for the next template rebuild.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Quotes is enabled in Setup > Quote Settings and visible on the Opportunity page layout
- [ ] Quote template generates a valid PDF in sandbox with real opportunity and product data
- [ ] Any custom fields needed on the PDF are present on the Quote object and populated correctly (via formula or Flow)
- [ ] Only one quote is ever set as synced at a time; process documented for switching sync
- [ ] Email Quote tested end-to-end: correct PDF attached, correct recipient, activity logged on both Quote and Opportunity
- [ ] If discount approval is configured: tested with a non-admin user, record locking verified, and the rejection action writes `QuoteLineItem.Discount` — not `Quote.Discount`, which is read-only
- [ ] No CPQ-related QuoteLineItem assumption introduced (standard templates do not render SBQQ__QuoteLine__c)
- [ ] Template character limits not exceeded (32,000 chars per Text/Image field)
- [ ] `QuoteStatus` value set deployed **complete**, with `allowEmail` set explicitly on every status
- [ ] `python3 scripts/check_quotes_and_quote_templates.py --manifest-dir <dir>` returns no ERROR lines
- [ ] `templates/quote-template-checklist.json` filled in, no `REPLACE ME` placeholders, `verified_in_org` all true
- [ ] Manual template rebuild booked into the release plan for every target org (no metadata type exists)
- [ ] Reconciliation queries run: no quote line on a syncing quote has a null `OpportunityLineItemId`, and no opportunity has two quotes claiming to sync

---

## Salesforce-Specific Gotchas

1. **Only one synced quote per opportunity** — The `Opportunity.SyncedQuoteId` can hold exactly one quote ID. Starting sync on a second quote silently stops sync on the first. Teams often discover this mismatch only when closing the opportunity.
2. **Standard quote templates cannot render CPQ quote lines** — If CPQ is installed, quote lines live in `SBQQ__QuoteLine__c`, not `QuoteLineItem`. A standard template on a CPQ quote generates a PDF with a blank line items section.
3. **Custom fields on Opportunity/OpportunityLineItem do not auto-map to Quote/QuoteLineItem** — There is no declarative field mapping. Creating a custom field on Opportunity and expecting it to copy to Quote will not work without custom Apex or a Flow.
4. **`Quote.Discount` cannot be written** — It is a derived roll-up (`Filter, Nillable, Sort`; `object_reference.txt` L239578–239592). An approval rejection that "resets the discount" must target `QuoteLineItem.Discount`. UNVERIFIED (2026-09-05): this skill previously claimed System Administrators bypass approval entry criteria; no source in the Metadata API guide or Object Reference supports that, so do not repeat it. Still test as a non-admin — admins can edit approval-locked records, so an admin run never exercises the lock.
5. **Quote PDF re-generates at email send time** — If a quote template is modified after a PDF was saved on the record, clicking "Email Quote" generates a NEW PDF using the updated template. Lock the template before PDFs are sent to customers.
6. **`SyncedQuoteID` is read-only in an Apex trigger** — "Read only in an Apex trigger" (`object_reference.txt` L192906–192912). Trigger-based sync automation compiles, deploys, and does nothing.
7. **Scheduled lines swallow edits** — With a quantity or revenue schedule on the synced opportunity line, "the update isn't rejected but the updated value is ignored" (`object_reference.txt` L240848–240870).
8. **A partial `QuoteStatus` deploy deactivates omitted statuses** — "If picklist values are missing from a component definition, they get deactivated when deployed" (`api_meta.txt` L47481–47483). Always retrieve first.
9. **There is no `QuoteTemplate` metadata type** — Templates are Setup-only and rebuilt per org (`api_meta.txt` L83162–83170).

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Quote template configuration | Header/body/footer layout, field selection, and styling decisions for the quote template |
| Quote sync process doc | Documented rules for when to sync, how to switch synced quotes, and what happens to lines when sync stops |
| Discount approval design | Entry criteria, approver routing, record lock behavior, and approval/rejection actions on the Quote object |
| Custom field mapping plan | List of Opportunity/Account fields needed on the PDF and the mechanism (formula or Flow) used to populate them on Quote |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | You are about to write or deploy anything — QuoteSettings, the QuoteStatus value set with `allowEmail`, a Quote custom field, a validation rule, the layout, `package.xml`, deploy order, the template checklist schema, and the reconciliation SOQL all live here. Start with §0, the "no QuoteTemplate metadata type" result. |
| `references/gotchas.md` | Before designing sync, approvals or a template — 13 platform behaviours, each with what happens / when it occurs / how to avoid, and the two corrections to claims this skill used to make. |
| `references/examples.md` | You want a worked end-to-end walkthrough — starting sync and reconciling it, mirroring Opportunity/Account values onto Quote with a verification query, and a discount approval whose reject branch actually reverses the discount. |
| `references/llm-anti-patterns.md` | You are reviewing AI-generated quote guidance, or self-checking your own output before returning it. |
| `references/well-architected.md` | You are making the Standard-Quotes-vs-CPQ call, choosing Flow vs Apex for field mirroring, or deciding whether discount governance belongs on Quote or Opportunity. |
| `templates/quotes-and-quote-templates-template.md` | You are starting a Quotes engagement and need the scoping, field-mirroring and approval-design worksheet. |
| `templates/quote-template-checklist.json` | You are building or changing a quote template — this is the reviewable artefact that stands in for the metadata that does not exist. Linted by the checker. |
| `scripts/check_quotes_and_quote_templates.py` | Before every deploy, and in CI with `--quiet`. Six checks over `--manifest-dir`. |

---

## Related Skills

- `admin/cpq-quote-templates` — Use when the org's quote lines are `SBQQ__QuoteLine__c` and the document is produced by a CPQ Document Template. NOT for `QuoteLineItem` or Setup > Quote Templates.
- `admin/quote-to-cash-requirements` — Use when the question spans quote → order → contract → invoice rather than the quote artefact itself.
- `architect/cpq-vs-standard-products-decision` — Use when the org is evaluating CPQ vs standard Quotes, or when CPQ is already installed and quote line rendering on PDFs is failing. NOT for standard Quotes configuration.
- `admin/approval-processes` — Use when the discount approval process on quotes becomes complex (multi-step, exception paths, delegation). NOT for quote sync or template design.
- `admin/products-and-pricebooks` — Use when the product catalog, pricebook structure, or pricing rules are the root cause of incorrect quote line item amounts. NOT for quote template layout.
- `admin/email-templates-and-alerts` — Use when the quote email template itself needs redesign or the email deliverability configuration is the issue. NOT for quote PDF template layout.
- `admin/opportunity-management` — Use when the relationship between opportunities, products, and quote sync needs architectural review as part of a broader sales process redesign.
