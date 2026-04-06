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

3. **Testing approval processes only as SysAdmin** — SysAdmins bypass approval entry criteria. A quote approval that appears to work in SysAdmin testing may never trigger for a standard Sales Rep in production. Always validate with a non-admin test user before deploying to production.

4. **Deploying quote template changes during active quoting cycles** — Changing a live template mid-cycle means any rep who emails a quote after the change receives the updated template, even if they reviewed a PDF generated before the change. Establish a change freeze policy aligned with key sales calendar dates.

## Official Sources Used

- Salesforce Help — Quotes Overview: https://help.salesforce.com/s/articleView?id=sf.quotes_overview.htm
- Salesforce Help — Quote Sync Overview: https://help.salesforce.com/s/articleView?id=sf.quotes_sync_overview.htm
- Salesforce Help — Quote Templates: https://help.salesforce.com/s/articleView?id=sf.quotes_template_overview.htm
- Salesforce Help — Quotes Limitations: https://help.salesforce.com/s/articleView?id=sf.quotes_limitations.htm
- Salesforce Object Reference — Quote: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_quote.htm
- Salesforce Object Reference — QuoteLineItem: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_quotelineitem.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Metadata API Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
