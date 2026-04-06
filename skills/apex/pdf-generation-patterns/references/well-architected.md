# Well-Architected Notes — PDF Generation Patterns

## Relevant Pillars

- **Security** — PDF generation often surfaces sensitive data (financial figures, personal details). FLS must be enforced in the Apex controller using `WITH USER_MODE` or explicit `Schema` checks. Conditional sections using CSS `display:none` must be replaced with `rendered="{!false}"` — hidden HTML elements are still present in the page source and visible if the raw HTML is inspected. ContentDocumentLink `ShareType` must be set to the minimum required access level.
- **Performance** — `PageReference.getContentAsPDF()` is an HTTP callout with a 120-second timeout. VF controllers must minimize SOQL row count and avoid N+1 query patterns inside `<apex:repeat>`. Large PDFs (50+ line items, embedded images) should be tested for rendering time before production deployment.
- **Scalability** — Bulk PDF generation is bounded by the 100-callout-per-transaction limit. Batch Apex with scope=1 or Queueable chaining is required for generating PDFs across many records. Synchronous generation inside a trigger fails immediately on the callout-after-DML restriction.
- **Reliability** — `getContentAsPDF()` returns null on VF page error without throwing. Null checks and error logging are mandatory to prevent silent failures and empty ContentVersion records. The Queueable that generates the PDF should implement retry logic or at minimum write a log record when the blob is null.
- **Operational Excellence** — PDF template VF pages should be deployed as metadata (`.page` files in a scratch org or sandbox), not created in production Setup. The Apex controller should be unit-tested with a mock blob to validate the ContentVersion insertion logic independently of the renderer. `Test.isRunningTest()` guards around `getContentAsPDF()` calls enable full code coverage.

## Architectural Tradeoffs

**Synchronous (browser download) vs. Asynchronous (ContentVersion storage):** Browser-download PDF rendering is simpler and requires no async plumbing, but it ties the PDF to a user session and does not persist the file. Asynchronous generation (Queueable) persists the PDF as a record-linked File but introduces async complexity, error handling, and retry concerns. Choose based on whether the PDF needs to be retrievable after the session ends.

**Custom Apex controller vs. Standard Controller + Extension:** A fully custom controller gives maximum SOQL flexibility (cross-object, CPQ, custom objects) but requires explicit FLS enforcement. A standard controller extension has FLS on bound standard fields automatically but cannot reach non-standard objects. Use a custom controller for anything beyond basic standard object queries.

**Inline CSS vs. Static Resource CSS:** Inline `<style>` blocks are simpler and self-contained, but they grow large when fonts or base64 images are embedded. A CSS static resource separates concerns and can be cached, but requires an absolute URL and adds one more deployment artifact to manage. For most PDF templates, inline CSS is the pragmatic choice.

## Anti-Patterns

1. **Loading data client-side with JavaScript** — Using `<apex:remoteAction>` or `window.fetch` to populate table rows after the page loads produces empty tables in the PDF. The Flying Saucer renderer captures the static HTML; no JS executes. All data must be bound server-side in the Apex controller before the page is returned.

2. **Using CSS `display:none` to hide sensitive sections** — Hidden HTML is still present in the raw page source. A user who intercepts the HTML response or views the VF page without `renderAs="pdf"` can see all data marked `display:none`. Use `rendered="{!showSection}"` where `showSection` is a server-side Boolean to exclude the HTML entirely.

3. **Generating PDFs synchronously in a trigger** — `PageReference.getContentAsPDF()` is a callout. Any DML in the triggering transaction blocks it with a `CalloutException`. Bulk insert/update operations will fail entirely. Always enqueue a Queueable from the trigger handler and generate the PDF in the async context.

## Official Sources Used

- Visualforce Developer Guide: Rendering a Page as PDF — https://developer.salesforce.com/docs/atlas.en-us.pages.meta/pages/pages_output_pdf_rendering.htm
- Visualforce Developer Guide: PDF Rendering Considerations — https://developer.salesforce.com/docs/atlas.en-us.pages.meta/pages/pages_output_pdf_considerations.htm
- Apex Reference Guide: PageReference.getContentAsPDF() — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_System_PageReference_getContentAsPDF.htm
- Apex Developer Guide: PageReference Class — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_system_pageReference.htm
- ContentVersion Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_contentversion.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
