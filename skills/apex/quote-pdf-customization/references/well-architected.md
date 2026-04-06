# Well-Architected Notes — Quote PDF Customization

## Relevant Pillars

- **Security** — The most critical pillar for this skill. Custom Apex controllers querying Quote and QuoteLineItem must enforce FLS/CRUD to prevent data exposure. The VF page URL (without `renderAs="pdf"`) exposes the HTML data model — conditional sections must use `rendered=` (server-side) not `display:none` (client-side CSS). `getContentAsPDF()` runs as the current user; ensure the running user has appropriate record access before generating.

- **Reliability** — `getContentAsPDF()` returns null on VF page errors rather than throwing. A production PDF generation pipeline must check for null explicitly and handle failure gracefully (log, alert, surface the error). Batch PDF generation jobs should use scope size of 1 to respect the 100-callout-per-transaction limit and avoid cascading failures across Quote records.

- **Performance** — `getContentAsPDF()` makes a platform-internal HTTP callout that can take several seconds for complex VF pages. Pages with many SOQL queries or large data sets should minimize query round-trips by prefetching all data in the controller constructor. CSS-heavy pages increase PDF rendering time; keep the CSS static resource lean.

- **Scalability** — Programmatic PDF generation does not scale linearly with synchronous execution. Use Queueable chaining or Batch Apex (scope=1) to generate PDFs at scale. Avoid generating PDFs inline within a trigger — this blocks the transaction and will fail on bulk updates.

- **Operational Excellence** — The VF page and its Apex controller are deployed artifacts subject to the normal release pipeline. Static resources containing fonts or CSS must be versioned alongside the VF page. Instrument the Queueable with error logging to a custom object so operations teams can diagnose generation failures without digging through debug logs.

## Architectural Tradeoffs

**Declarative template vs. custom VF page:** The standard quote template editor is zero-code and admin-maintainable, but it cannot support conditional sections, CPQ line items, complex CSS layouts, or programmatic generation. Once a VF page is required, the org takes on an Apex + Visualforce artifact in its release pipeline. This is the right tradeoff for orgs with branded or complex quote requirements.

**Standard controller extension vs. custom controller:** A standard controller extension inherits the standard controller's record context and FLS enforcement on bound fields, reducing boilerplate. A custom controller gives full SOQL flexibility and is required for CPQ. Custom controllers must manually enforce all access control.

**Inline PDF rendering vs. programmatic generation:** Inline rendering (navigating to the VF page URL) is simple and immediate but requires a user session. Programmatic generation via `getContentAsPDF()` enables automation but requires an async context and has more failure modes (null return on error, callout limits, timeout).

## Anti-Patterns

1. **Hiding sensitive data with CSS `display:none` instead of `rendered="false"`** — CSS hiding is not security. The hidden HTML is present in the VF page source and can be read by viewing the page without `renderAs="pdf"`. Use `rendered="{!showSection}"` to exclude the content from the server response entirely when it should not be visible.

2. **Calling `getContentAsPDF()` in a synchronous trigger** — This violates the platform's callout-after-DML restriction and throws a `CalloutException`. Even if refactored to avoid DML, synchronous PDF generation in a trigger blocks the transaction and will fail on bulk record updates. Always offload to a Queueable or Future method implementing `Database.AllowsCallouts`.

3. **Generating multiple PDFs in a single Batch execute() call with large scope** — Each `getContentAsPDF()` call is one callout. A batch with scope=50 would attempt 50 callouts per execute(), hitting the 100-callout limit partway through and failing the entire batch. Use scope=1 for PDF generation batches.

## Official Sources Used

- Visualforce Developer Guide: Rendering a Page as PDF — https://developer.salesforce.com/docs/atlas.en-us.pages.meta/pages/pages_output_pdf_content_type.htm
- Visualforce Developer Guide: PDF Rendering Considerations — https://developer.salesforce.com/docs/atlas.en-us.pages.meta/pages/pages_output_pdf_considerations.htm
- Apex Developer Guide: PageReference Class — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_System_PageReference.htm
- Apex Reference Guide: PageReference.getContentAsPDF() — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_System_PageReference_getContentAsPDF.htm
- Salesforce Help: Quote Templates — https://help.salesforce.com/s/articleView?id=sf.quotes_templates.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Apex Reference Guide — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm
