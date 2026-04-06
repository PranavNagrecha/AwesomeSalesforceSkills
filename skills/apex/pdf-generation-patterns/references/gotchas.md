# Gotchas — PDF Generation Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: JavaScript Is Completely Ignored by the Flying Saucer Renderer

**What happens:** Any JavaScript in the Visualforce page — inline scripts, `<script src>` references, or `<apex:remoteAction>` calls — is silently skipped. The PDF is generated from the static HTML produced by server-side rendering only. Dynamic content driven by JS (populated tables, charts, lazy-loaded sections) is absent in the PDF with no error or warning.

**When it occurs:** Any time a VF page that works correctly in the browser (where JS executes) is viewed with `renderAs="pdf"`. The browser preview looks fine; the PDF is broken.

**How to avoid:** Load all data in the Apex controller constructor using SOQL. Use EL expressions (`{!property}`) and `<apex:repeat>` to bind data directly to markup. Never defer data loading to client-side JavaScript. Remove all `<script>` tags from the PDF template page.

---

## Gotcha 2: External CDN Stylesheets Are Not Fetched by the Renderer

**What happens:** `<link rel="stylesheet" href="https://cdn.example.com/style.css">` tags in the page are silently ignored. The renderer does not fetch external URLs when processing the HTML for PDF conversion. The PDF renders with no styling (or with only inline styles that were already present).

**When it occurs:** Whenever a VF page imports Bootstrap, Salesforce Lightning Design System (SLDS), Tailwind, or any other CDN-hosted stylesheet. This also affects Salesforce-served relative paths from external domains.

**How to avoid:** All CSS must be either: (a) in an inline `<style>` block within the page, or (b) uploaded as a Salesforce static resource and referenced with an absolute URL built in Apex. Do not import CSS from external hosts. Keep the CSS minimal — only CSS 2.1 properties are supported.

---

## Gotcha 3: `{!$Resource.LogoName}` in `<img src>` Produces a Broken Image

**What happens:** The expression `{!$Resource.CompanyLogo}` resolves to a relative URL like `/resource/1234567890/CompanyLogo`. The Flying Saucer renderer makes an independent HTTP request to resolve image URLs — it cannot resolve relative Salesforce paths without authentication context. The image renders as a broken placeholder in the PDF.

**When it occurs:** When a developer copies the standard pattern of using `$Resource` directly in an `<img>` src attribute, which works fine in a browser VF page but fails in PDF rendering.

**How to avoid:** Build the absolute image URL in the Apex controller:
```apex
logoUrl = URL.getSalesforceBaseUrl().toExternalForm() + '/resource/CompanyLogo';
```
Alternatively, embed the image as a base64 data URI inside the CSS or directly in the `<img src>` attribute. For static resources that are zip files, use the full subpath: `/resource/ResourceName/subfolder/image.png`.

---

## Gotcha 4: `getContentAsPDF()` Returns Null on VF Page Error — No Exception Thrown

**What happens:** If the Visualforce page referenced by `PageReference.getContentAsPDF()` throws an unhandled exception during rendering, the method does not propagate the exception — it returns `null` silently. Apex code that proceeds without a null check will either throw a NullPointerException when calling `blob.size()` or insert a 0-byte ContentVersion.

**When it occurs:** VF page throws on missing record Id, SOQL returns no rows and code accesses index 0, or the page encounters an unhandled governor limit. The caller has no indication of what went wrong.

**How to avoid:** Always null-check the result before use:
```apex
Blob pdf = pageRef.getContentAsPDF();
if (pdf == null) {
    // log error, notify, or re-queue
    return;
}
```
Also add defensive checks in the VF controller (e.g., check that the record exists before accessing its fields).

---

## Gotcha 5: Callout-After-DML Restriction Prevents Inline PDF Generation in Triggers

**What happens:** Calling `getContentAsPDF()` inside a trigger (or any synchronous context where DML has already been performed in the same transaction) throws `System.CalloutException: Callout from triggers are currently not supported.` The DML that fired the trigger (or any earlier DML in the transaction) blocks the callout.

**When it occurs:** Any trigger-based pattern that tries to call `getContentAsPDF()` synchronously — including helper classes called from triggers and Flow-invoked Apex actions that run synchronously in a record-save transaction.

**How to avoid:** Always invoke `getContentAsPDF()` from an async context: a Queueable implementing `Database.AllowsCallouts`, a `@future(callout=true)` method, or a Batch Apex class implementing `Database.AllowsCallouts`. Enqueue the job from the trigger handler or Flow, passing the record Id.

---

## Gotcha 6: CSS Flexbox and Grid Are Silently Ignored — Layouts Collapse

**What happens:** The Flying Saucer engine only supports CSS 2.1. `display: flex`, `display: grid`, CSS custom properties (`var(--x)`), and CSS animations are silently ignored. Elements that relied on Flexbox for alignment render as stacked blocks, destroying column layouts.

**When it occurs:** When a developer copies a modern responsive CSS layout into the VF PDF page, which renders correctly in a browser but collapses in the PDF because the layout properties are ignored.

**How to avoid:** Use CSS 2.1 table layout for columns: `display: table` on the container, `display: table-row` on rows, and `display: table-cell` on cells. For simpler single-column layouts, use `float: left` with explicit widths. Test the layout with `renderAs="pdf"` enabled, not just in browser preview mode.
