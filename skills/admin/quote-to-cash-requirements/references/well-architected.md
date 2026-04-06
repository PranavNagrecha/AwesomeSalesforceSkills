# Well-Architected Notes — Quote-to-Cash Requirements

## Relevant Pillars

- **Reliability** — The quote-to-cash chain spans multiple object transitions (Quote to Approval to Order). Each handoff must succeed reliably even when records are locked, flows fail mid-transaction, or approval processes are recalled. Error handling in the Order creation Flow is critical: if the Flow fails after Order creation but before OrderItem creation, partial Orders must be cleanly rolled back or detectable.

- **Operational Excellence** — The approval process and Order creation automation must be maintainable by admins without Apex access. Using declarative tools (Approval Process + Record-Triggered Flow) keeps the process auditable in the Setup UI, visible in Flow debug logs, and modifiable without a deployment. Avoid embedding quote-to-cash logic in Apex triggers unless the complexity truly requires it.

- **User Experience** — Record lock during approval is a significant UX friction point. Requirements must explicitly communicate to stakeholders that reps cannot edit a Quote while it is pending approval, and that the recall process is the only path to re-edit. In-app guidance banners on locked Quotes reduce support tickets.

- **Security** — Quote PDFs are stored as Salesforce Files (ContentDocument/ContentVersion) and follow standard Salesforce sharing rules. Reps should only have access to Quote PDFs for their own deals. Sharing settings on the Quote object and related ContentDocument sharing must be reviewed if the org uses private or controlled-by-parent sharing models.

- **Performance** — Quote Template PDF generation is synchronous and subject to governor limits on the generating transaction. Large templates with many conditional sections and custom formula fields increase generation time. High-volume PDF generation (e.g., bulk quote acceptance automation) can cause Apex CPU time limits. Validate PDF generation performance in sandbox with realistic line item volumes.

## Architectural Tradeoffs

**Single Approval Process vs. Chained Flows for approval routing:** Native Approval Processes are the correct tool for quote discount governance. They provide an audit trail (ApprovalHistory), a native lock mechanism, and a recall capability that is difficult to replicate in Flow. The tradeoff is inflexibility — Approval Processes cannot dynamically route based on run-time data in the way Flow can. For standard tiered discount routing, the native tool is sufficient and preferred. Custom routing logic (e.g., round-robin approvers, SLA-based escalation) requires Flow or Apex supplementing the Approval Process.

**Declarative Order creation (Flow) vs. Apex trigger:** For standard Order and OrderItem creation from a Quote, a Record-Triggered Flow is sufficient and preferred. Apex is only warranted when the Order creation requires complex error handling, integration callouts, or conditional logic that exceeds Flow capabilities. Apex triggers on Quote status changes are harder to debug, invisible to admins, and create deployment dependencies.

**Standard Quote Templates vs. Custom PDF generation via Apex/VF:** Standard Quote Templates are the right default. Custom Visualforce-based PDF generation should only be pursued when layout requirements (complex nested tables, pixel-perfect branding, digital signatures) are confirmed to be impossible in the standard template editor. Custom PDF generation adds Apex, VF pages, and rendering governor limit complexity.

## Anti-Patterns

1. **Using two separate Approval Processes for multi-tier discount routing** — Salesforce only activates one approval process at a time per record. A second process is never triggered when the first matches. The correct pattern is one process with multiple steps using step-entry criteria for each tier.

2. **Wiring Order creation into Approval Process Final Actions** — Final Approval/Rejection actions cannot create records. Attempting this leads to missing Orders with no error surfaced to the rep. Use a Record-Triggered Flow on Quote Status change instead.

3. **Ignoring the 100-line-item PDF limit in requirements** — Gathering requirements without asking about the largest expected quote leads to silently truncated PDFs in production. This limit must be explicitly validated against expected deal complexity before committing to standard Quotes.

## Official Sources Used

- Salesforce Help — Quotes Overview: https://help.salesforce.com/s/articleView?id=sf.quotes_overview.htm
- Salesforce Help — Syncing Quotes with Opportunities: https://help.salesforce.com/s/articleView?id=sf.quotes_syncing_overview.htm
- Salesforce Help — Setting Up Quotes: https://help.salesforce.com/s/articleView?id=sf.quotes_setup.htm
- Trailhead — Negotiate Enterprise Quotes: https://trailhead.salesforce.com/content/learn/modules/sales-cloud-platform-quick-look/negotiate-enterprise-quotes
- Trailhead — Build a Discount Approval Process: https://trailhead.salesforce.com/content/learn/projects/build-a-discount-approval-process
- Salesforce Help — Create Orders from Quotes: https://help.salesforce.com/s/articleView?id=sf.quotes_create_orders.htm
- Salesforce Help — Quote Template Limits: https://help.salesforce.com/s/articleView?id=sf.quotes_doc_limits.htm
- Object Reference — Quote: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_quote.htm
- Object Reference — Order: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_order.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
