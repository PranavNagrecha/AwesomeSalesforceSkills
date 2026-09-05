# Well-Architected Notes — Quotes and Quote Templates

## Relevant Pillars

- **Reliability** — Quote sync is a bidirectional platform mechanism with a hard constraint of one synced quote per opportunity. A reliable quotes implementation must account for the sync state at all times to prevent opportunity product data from diverging from the customer-facing document. Discount approvals on Quote add a reliability gate to prevent unauthorized commercial commitments.
- **User Experience** — Quote templates directly determine the quality of the customer-facing deliverable. A poorly designed template produces unprofessional PDFs. The email quote flow must be tested end-to-end with real data, including edge cases like quotes with many line items that overflow the template body.
- **Operational Excellence** — Quote templates require maintenance governance: who can edit templates, what the change review process is, and whether template versioning is needed. Without governance, template edits in production can corrupt in-flight customer PDFs without anyone noticing until a customer complaint surfaces.
- **Security** — Discount approval processes on quotes enforce commercial governance at the platform level. Without them, any user with quote edit access can set any discount value. Quote record locking during approval is also a security boundary — the right users must retain edit access during review while others are blocked.
- **Scalability** — Standard Quotes and quote templates are designed for moderate-volume, sales-rep-driven quoting. If the business needs programmatic bulk quote generation or complex multi-document output, standard Quotes will hit limits and the architecture should consider CPQ or custom integration patterns.

## Architectural Tradeoffs

**Standard Quotes vs CPQ:** Standard Salesforce Quotes are sufficient for straightforward product catalog quoting with a defined price list. CPQ (Revenue Cloud) adds guided selling, dynamic pricing rules, quote line scheduling, contract generation, and amendment flows. Adopting CPQ for a simple catalog is over-engineering; continuing with standard Quotes when the business needs multi-tier pricing rules, bundles, or subscription amendments is under-engineering. Document the decision point explicitly.

**Declarative field mirroring vs Apex:** Custom fields on Opportunity that need to appear on quote PDFs require a mirroring strategy. Flow-based mirroring is declarative and maintainable but adds a DML operation per quote record change. Apex trigger-based mirroring is more efficient at volume but increases code maintenance overhead. For most orgs with standard sales volumes, Flow is the right default.

**Approval on Quote vs Approval on Opportunity:** Discount governance can be enforced on the Quote record or on the Opportunity stage. Enforcing on Quote is closer to the commercial document and prevents the PDF from being sent before approval. Enforcing on Opportunity stage may miss quote-level discounting that does not flow up cleanly. Best practice: enforce on Quote, and add a validation rule on Opportunity that prevents stage advancement if a related quote is pending approval.

## Anti-Patterns

1. **Editing opportunity products while a quote is synced** — Once sync is active, all line item edits must flow through the quote. Directly editing opportunity products while synced produces unpredictable behavior and risks data divergence between the quote document and the opportunity record used for forecasting.

2. **Using standard quote templates for CPQ quotes** — Standard templates render `QuoteLineItem` only. In a CPQ org, this produces blank PDF line item sections. Teams often discover this only when a customer asks why the quote PDF shows no products.

3. **Designing the approval's reject branch around `Quote.Discount`** — The field has properties `Filter, Nillable, Sort` and no `Create`/`Update`; it is a roll-up of the line items' discounted totals (`object_reference.txt` L239578–239592). A rejection that "resets the discount" must write `QuoteLineItem.Discount`. Also test as a non-admin user: an administrator can edit records that an approval process has locked, so an admin run never exercises the lock a rep will hit. UNVERIFIED (2026-09-05): this file previously asserted that SysAdmins bypass approval entry criteria; no source in the Metadata API guide or Object Reference documents such a bypass, and help.salesforce.com cannot be fetched — treat it as unproven.

4. **Deploying quote template changes during active quoting cycles** — Changing a live template mid-cycle means any rep who emails a quote after the change receives the updated template, even if they reviewed a PDF generated before the change. Establish a change freeze policy aligned with key sales calendar dates.

5. **Enforcing "do not send before approval" with a validation rule** — The platform ships the control: `allowEmail` on each `QuoteStatus` value "indicates whether this value lets users email a quote PDF" and "is only relevant for the Status field in quotes" (`api_meta.txt` L47538–47541). It is deployable, per status, and does not depend on the Email Quote action passing through a save-time rule.

6. **Assuming quote templates are part of the release** — There is no `QuoteTemplate` metadata type; the token appears once in the Metadata API guide as a `SummaryLayoutStyle` enum value (`api_meta.txt` L83162–83170). Every org needs a manual rebuild. Treating it as deployable puts an unbudgeted, error-prone manual step on the critical path at cutover.

7. **Hand-writing a `QuoteStatus` standard value set instead of retrieving it** — "If picklist values are missing from a component definition, they get deactivated when deployed." (`api_meta.txt` L47481–47483). A two-value file authored from a doc sample deactivates every other status in the target org, on a deploy that reports success.

## Official Sources Used

Verified against the Summer '26 (v66) PDFs on 2026-09-05. Line references are into the
extracted plain text of those PDFs.

- **Object Reference for the Salesforce Platform — `Quote`** (`object_reference.txt` L239236–240176) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf — field properties for `Discount`, `GrandTotal`, `Subtotal`, `TotalPrice`, `IsSyncing`, `Status`, `LineItemCount`, `QuoteAccountId`, `Pricebook2Id`, and the standard `Status` options (supports the "read the header, write the line" tradeoff and the read-only field table in SKILL.md).
- **Object Reference — `Opportunity.SyncedQuoteID`** (`object_reference.txt` L192906–193010) — "Read only in an Apex trigger", the child-quote constraint, and the guide's own start/stop-sync samples (supports Gotcha 7 and the sync section of Core Concepts).
- **Object Reference — `QuoteLineItem`** (`object_reference.txt` L240633–241812) — `Discount` 0–100 writable, `SortOrder` controlling PDF line order, `OpportunityLineItemId` not editable, `HasQuantitySchedule` / `HasRevenueSchedule` silently ignoring updates, and the Usage rule that a quote needs a `Pricebook2` before it can hold lines (supports Gotchas 8 and 12).
- **Object Reference — `QuoteDocument`** (`object_reference.txt` L240388–240500) — `Document`, `DocumentTemplate`, `Discount`, `GrandTotal` and the `Status` picklist including `Failed` (supports the "which template produced which PDF" audit query in `references/metadata-examples.md` §8c).
- **Metadata API Developer Guide — `QuoteSettings`** (`api_meta.txt` L124883–124942) — `enableQuote`, `enableQuotesWithoutOppEnabled`, the `Quote.settings` file location, the package sample, and the no-wildcard rule for feature settings (supports `references/metadata-examples.md` §1 and check 1 of the checker).
- **Metadata API Developer Guide — `StandardValue` / `CustomValue`** (`api_meta.txt` L47474–47545) — `allowEmail` "only relevant for the Status field in quotes", and "If picklist values are missing from a component definition, they get deactivated when deployed" (supports Gotchas 10 and 13, and checks 2 and 5 of the checker).
- **Metadata API Developer Guide — `StandardValueSet`** (`api_meta.txt` L130740–130832) — file suffix, `sorted`, the non-empty `standardValue` requirement, and the no-wildcard rule; plus the `QuoteStatus` → `Quote.Status` mapping at L142923.
- **Metadata API Developer Guide — `ValidationRule` and `CustomField`** (`api_meta.txt` L45363–45440, L43204–43700) — required elements, the 255-character `errorMessage` cap, `errorDisplayField` fallback behaviour, and the `precision`/`scale`/`trackHistory` element names used in `references/metadata-examples.md` §3–§4.
- **Metadata API Developer Guide — `Layout` / `SummaryLayout`** (`api_meta.txt` L82275–83400) — the layout sample structure used in §6, and the negative result that `QuoteTemplate` exists only as a `SummaryLayoutStyle` enum value (L83162–83170), which is the basis of §0 and Gotcha 11.
- **Apex Developer Guide** (`salesforce_apex_developer_guide.pdf`, `apexdev.txt` L8249) — quote-to-opportunity lookups are among the relationships restored by `undelete`, the only Quote-specific behaviour the Apex guides document. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- **Salesforce Well-Architected** — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html — pillar framing for the tradeoffs above.

### Negative results (searched, not found)

Recording these so the next author does not repeat the search:

- No `QuoteTemplate` metadata type. `api_meta.txt` contains the token once, as a `SummaryLayoutStyle` enum value (L83165).
- No Quote- or QuoteDocument-specific PDF-generation API in the Apex Developer Guide or Apex Reference Guide. `PlaceQuote` and `RevSalesTrxn` namespaces exist (`apexrefguide.txt` L1097–1120) but belong to Revenue Cloud transaction processing, not standard quote PDF generation.
- No quote-related entry in the Salesforce App Limits Cheat Sheet — a grep for "quote" in `salesforce_app_limits_cheatsheet.txt` returns nothing, so the quote-template character limits in this skill have no cheat-sheet grounding.
- No `IsClosed` field on `Quote` in the Object Reference field table, and no `VersionNumber` on `QuoteDocument` (it carries `ContentVersionDocumentId` instead).
- `Quote.OwnerId` is not listed in the Object Reference `Quote` field table in the v66 extraction, although `QuoteOwnerSharingRule` and `QuoteShare` are listed as associated objects from API 41.0 — so Quote is ownable, but do not cite a field-table property for `OwnerId`.
