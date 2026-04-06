---
name: quote-pdf-customization
description: "Customizing Salesforce Quote PDFs using Visualforce: custom VF-based quote templates, dynamic section rendering, multi-language layouts, logo placement via static resources, and programmatic PDF generation with PageReference.getContentAsPDF(). Use when standard declarative quote templates are insufficient or when CPQ/OmniStudio is not licensed. NOT for LWC-based document generation (use omnistudio/document-generation-omnistudio). NOT for OmniStudio DocGen templates. NOT for standard quote template drag-and-drop editor."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "how do I generate a custom Quote PDF in Salesforce with a logo and conditional sections"
  - "standard quote template does not support CPQ line items in the PDF"
  - "how to programmatically attach a Quote PDF to the record when it reaches Approved stage"
  - "quote PDF rendering blank sections because of JavaScript or CSS not working"
  - "how to build a multi-language quote PDF in Salesforce"
tags:
  - quote-pdf
  - visualforce
  - pdf-rendering
  - quote-template
  - renderAs-pdf
  - pageReference
  - static-resource
  - multi-language
inputs:
  - "Quote record Id or SBQQ__Quote__c Id (for CPQ) — which object drives the template"
  - "Required line items: standard QuoteLineItem or custom object"
  - "Branding assets: logo image, fonts, color palette — whether hosted as static resources"
  - "Locale/language requirements: single-language or multi-language per customer"
  - "Delivery mechanism: rendered inline, emailed as attachment, or stored as ContentDocument"
outputs:
  - "Visualforce page (.page) with renderAs='pdf' and correct apex:page controller binding"
  - "Apex controller or extension class retrieving Quote + QuoteLineItem data with FLS enforcement"
  - "Static resource references for logo and CSS using absolute URLs"
  - "PageReference.getContentAsPDF() snippet for programmatic generation and attachment"
  - "Conditional section logic for dynamic layouts (discounts, multi-currency, language)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Quote PDF Customization

This skill activates when a Salesforce org needs to generate customized Quote PDFs that go beyond what the standard declarative quote template editor supports. It covers Visualforce-based template authoring, dynamic section rendering, logo and CSS placement, multi-language layouts, and programmatic PDF generation via `PageReference.getContentAsPDF()`.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Template mechanism in use:** Is the org using standard Salesforce Quotes (QuoteLineItem), Salesforce CPQ (SBQQ__QuoteLine__c), or a fully custom quoting object? Standard VF templates cannot render CPQ line items — a custom VF page is required.
- **Static resource setup:** Logos and background images in PDF output must be referenced by absolute URL (e.g., `{!$Resource.CompanyLogo}` resolves to a relative path that the PDF renderer cannot follow). Use an absolute URL built in Apex, or embed images as base64 data URIs.
- **JavaScript restriction:** The VF PDF renderer (Flying Saucer / iText) does not execute JavaScript. Any dynamic behavior relying on JS (charts, lazy-loaded sections, DOM manipulation) will silently disappear in the PDF output.
- **CSS capability:** Only a subset of CSS 2.1 is supported. CSS Grid, Flexbox, and CSS variables are not rendered. Use table-based or float-based layouts for reliable column alignment.
- **Delivery mechanism:** Determine upfront whether the PDF is rendered on-demand (browser download), emailed as an attachment, or stored as a `ContentVersion` linked to the Quote. The generation code differs meaningfully between these paths.

---

## Core Concepts

### Concept 1: Visualforce renderAs="pdf" and the Flying Saucer Renderer

Adding `renderAs="pdf"` to `<apex:page>` causes Salesforce to pass the rendered HTML through the Flying Saucer library (based on iText) before returning the response to the browser. The critical consequences are:

- **JavaScript does not run.** All layout and data must be resolved server-side in Apex.
- **Only CSS 2.1 is supported.** Modern layout primitives (Flexbox, Grid, CSS custom properties) are silently ignored.
- **External HTTP resources (images, fonts) loaded by URL must be publicly accessible** or embedded inline. The renderer makes its own HTTP requests; it cannot follow authenticated Salesforce URLs or relative paths.
- **Page breaks** are controlled via `page-break-before`, `page-break-after`, and `page-break-inside` CSS properties.
- The `showHeader="false"` and `sidebar="false"` attributes on `<apex:page>` are required for PDF output to suppress the Salesforce chrome.

### Concept 2: Controller Choices — Standard Controller vs. Custom Apex

A VF quote PDF page can use either a standard controller (`standardController="Quote"`) with an extension, or a fully custom controller.

| Controller Type | Use When | What You Get |
|---|---|---|
| Standard Controller + Extension | Standard Quote + QuoteLineItem; simple branded layout | Record context auto-bound from URL Id; FLS on bound fields; less boilerplate |
| Custom Apex Controller | CPQ Quotes (SBQQ__QuoteLine__c); complex aggregation; multi-object data | Full SOQL flexibility; must manually enforce FLS/CRUD |

Use `WITH USER_MODE` on SOQL queries (available Summer '23+) to enforce FLS at the database level automatically and avoid manual `Schema` checks.

### Concept 3: Programmatic PDF Generation with PageReference

`PageReference.getContentAsPDF()` allows server-side Apex code to generate a PDF binary from a VF page and store or email it without user interaction. This is used in scheduled batch jobs, trigger-initiated quote finalization, or Send Quote button overrides.

Key behaviors:
- `getContentAsPDF()` performs an HTTP callout to the VF page URL from within the Salesforce platform. It counts against callout limits and is subject to a 120-second timeout.
- The method cannot be called from a trigger context directly — it must be invoked from a Queueable, Future method, or Batch class to satisfy the callout-within-DML restriction.
- The returned `Blob` can be wrapped in a `ContentVersion` and linked to the Quote via `ContentDocumentLink`.
- **Critical:** `getContentAsPDF()` returns `null` (not an exception) when the referenced VF page throws an error. Always check for null before using the blob.

### Concept 4: Multi-Language and Conditional Section Rendering

Enterprise quote PDFs often require per-customer language variants and conditional sections (e.g., show discount table only if any line has a non-zero discount).

Implement this using:
- Apex `Boolean` properties exposed on the controller and bound via `rendered="{!showDiscountSection}"` on `<apex:outputPanel>` blocks — content excluded by `rendered="false"` is never sent to the browser or PDF renderer.
- Custom Labels (which support Translation Workbench translations) for all user-facing text strings.
- `<apex:page language="{!pageLanguage}">` where `pageLanguage` is resolved from the Contact's preferred language field.
- For non-Latin scripts (Arabic, Chinese, Japanese), embed a Unicode font via `@font-face` with a base64-encoded font file in a CSS static resource.

---

## Common Patterns

### Pattern 1: Custom VF Quote Template with Standard Controller Extension

**When to use:** The org uses standard Salesforce Quotes (not CPQ) and needs a branded, formatted PDF beyond what the declarative template editor supports.

**How it works:**
1. Create a Visualforce page with `<apex:page standardController="Quote" extensions="QuotePdfController" renderAs="pdf" showHeader="false" sidebar="false">`.
2. In `QuotePdfController`, query `QuoteLineItem` records with `WITH USER_MODE` and expose Boolean section-toggle properties.
3. Build the logo URL as an absolute URL in Apex — do not use `{!$Resource.Logo}` directly in `<img src>`.
4. Use inline CSS table layout for line-item columns (avoid Flexbox/Grid).
5. Use `rendered="{!property}"` on conditional sections — never `display:none`.

**Why not the alternative:** The standard declarative quote template editor does not support conditional sections, custom grouping logic, or CPQ line items. JavaScript for dynamic behavior produces blank sections in the PDF because the renderer skips JS entirely.

### Pattern 2: Programmatic PDF Attachment via Queueable

**When to use:** The PDF must be automatically generated and attached to the Quote when it reaches a certain stage, without user interaction.

**How it works:**
1. A process (Flow or trigger) enqueues a `QuotePdfAttachmentJob` Queueable class implementing `Database.AllowsCallouts`, passing the Quote Id.
2. The Queueable builds a `PageReference` to the VF page, calls `.getContentAsPDF()`, checks for null, creates a `ContentVersion`, and links it to the Quote via `ContentDocumentLink`.
3. Error handling must log failures — check for null blob explicitly before inserting.

**Why not the alternative:** Calling `getContentAsPDF()` inside a trigger violates the callout-after-DML restriction and throws a `CalloutException`. It must be offloaded to an async context.

### Pattern 3: Multi-Language Quote PDF

**When to use:** Sales operates across multiple countries and each quote must be rendered in the customer's language.

**How it works:**
1. Store all label strings in Salesforce Custom Labels. Enable Translation Workbench and add translations per supported locale.
2. Reference labels via `{!$Label.QuoteTemplate_ProductColumn}` — Salesforce renders the label in the page's locale context.
3. Set the page locale dynamically: `<apex:page language="{!pageLanguage}">` where `pageLanguage` is resolved in Apex from the Contact's `LanguageLocaleKey` or a custom field.
4. For non-Latin scripts, embed a Unicode font (`@font-face` + base64) in a CSS static resource.

**Why not the alternative:** Hard-coding label text in the VF markup creates one template per language, multiplying maintenance burden. Custom Labels with Translation Workbench keep all text in a single template that adapts at render time.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Standard Quote, basic branding | Standard Controller + VF extension, `renderAs="pdf"` | Minimal complexity; FLS on bound fields handled automatically |
| CPQ Quote with SBQQ__QuoteLine__c | Custom Apex controller querying CPQ objects | Standard controller cannot traverse CPQ line objects |
| Auto-attach PDF on stage change | Queueable implementing `Database.AllowsCallouts` | Callouts not allowed in trigger context; async required |
| Multi-language output | Custom Labels + Translation Workbench + `<apex:page language=...>` | Single template, platform-managed translations |
| Logo not appearing in PDF | Embed as base64 data URI or build absolute URL in Apex | PDF renderer cannot follow relative Salesforce resource URLs |
| Complex column layout needed | CSS table layout (`display:table`, `display:table-cell`) | Flexbox and Grid not supported by Flying Saucer renderer |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm the quoting object** — Determine whether the org uses standard `Quote` + `QuoteLineItem` or Salesforce CPQ `SBQQ__Quote__c` + `SBQQ__QuoteLine__c`. This controls which controller pattern is required.
2. **Design the controller** — For standard Quotes, scaffold a `standardController="Quote"` page with a read-only Apex extension. For CPQ Quotes, write a custom controller. Use `WITH USER_MODE` in all SOQL to enforce FLS automatically.
3. **Set up static resources** — Upload logo images and custom fonts as static resources. Plan to embed images as base64 data URIs inside a CSS static resource, or build an absolute URL in Apex pointing to the static resource.
4. **Author the VF page** — Add `renderAs="pdf" showHeader="false" sidebar="false"` to `<apex:page>`. Use CSS 2.1 table-based layout. Add `rendered="{!booleanProp}"` on conditional sections. Include no `<script>` tags.
5. **Test PDF output iteratively** — Append `?id=<QuoteId>` to the VF page URL and view in a browser. Toggle `renderAs="pdf"` on and off to compare HTML vs. PDF rendering. Verify logo visibility, column alignment, and page break behavior.
6. **Implement delivery mechanism** — If the PDF must be programmatically generated, build a Queueable implementing `Database.AllowsCallouts` that calls `getContentAsPDF()`, checks for a non-null blob, and inserts a `ContentVersion` + `ContentDocumentLink` linked to the Quote.
7. **Validate with a non-admin user** — Run the page as a user with only the minimum Quote Read permission. Confirm no data leaks through the controller and no FLS violations appear in debug logs.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] `<apex:page>` includes `renderAs="pdf" showHeader="false" sidebar="false"`
- [ ] No `<script>` tags present in the VF page — all logic is server-side Apex
- [ ] SOQL uses `WITH USER_MODE` or explicit FLS checks; no string-concatenated query predicates
- [ ] Logo and images referenced by absolute URL or embedded as base64 data URIs
- [ ] Layout uses CSS 2.1 (tables/floats) — no Flexbox, Grid, or CSS custom properties
- [ ] Conditional sections use `rendered="{!property}"` — no CSS `display:none` hiding sensitive data
- [ ] If programmatic: `getContentAsPDF()` is called from a Queueable or Future method implementing `Database.AllowsCallouts`
- [ ] `getContentAsPDF()` return value checked for null before inserting ContentVersion
- [ ] PDF tested with a non-admin user to verify record access and FLS compliance

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **`{!$Resource.Logo}` produces a relative URL — the PDF renderer cannot follow it** — `$Resource.Logo` resolves to a path like `/resource/1234/Logo.png`. The Flying Saucer renderer treats this as a local file reference and fails silently. Build an absolute URL in Apex using `URL.getSalesforceBaseUrl().toExternalForm()` or embed the image as a base64 data URI.
2. **`getContentAsPDF()` returns null without throwing when the VF page errors** — If the VF page throws an unhandled exception, `getContentAsPDF()` returns null instead of re-throwing. Code that skips the null check will silently insert a 0-byte ContentVersion. Always assert `blob != null` before proceeding.
3. **Standard Quote templates cannot render CPQ line items** — The standard VF template or `standardController="Quote"` only sees `QuoteLineItem`. CPQ stores lines in `SBQQ__QuoteLine__c`. A custom Apex controller is mandatory for any CPQ quote PDF.
4. **`page-break-inside: avoid` is unreliable on `<tr>` elements** — Flying Saucer inconsistently honors this property on table rows. Wrap each repeated row's content in a `<div style="page-break-inside: avoid;">` inside the `<apex:repeat>` to prevent mid-row page breaks.
5. **`getContentAsPDF()` counts as a callout against the 100-callout limit** — Each call counts as one callout. Batch generation in a single transaction will hit this cap. Use scope size of 1 in Batch Apex or chain Queueables so each transaction generates only one PDF.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Visualforce page | `.page` file with `renderAs="pdf"`, conditional sections, and CSS table layout |
| Apex controller/extension | Class querying Quote + lines with FLS-safe SOQL and Boolean section-toggle properties |
| CSS static resource | Stylesheet with table-based layout, `@font-face` for non-Latin scripts, and logo as base64 |
| Queueable PDF attachment class | Async Apex calling `getContentAsPDF()`, checking null, and linking a `ContentVersion` to the Quote |
| Checker script output | List of metadata issues found by `check_quote_pdf_customization.py` |

---

## Related Skills

- `apex/visualforce-fundamentals` — Core VF rendering concepts, view state, controller types, and LEX iframe compatibility that underpin this skill
- `omnistudio/document-generation-omnistudio` — Alternative document generation when OmniStudio is licensed; supports LWC-based templates and server-side Word/PDF generation
- `architect/cpq-vs-standard-products-decision` — Decision guidance for whether to use CPQ vs. standard quoting, which directly determines the quote PDF controller architecture
- `apex/apex-queueable-patterns` — Queueable patterns for async PDF generation and ContentVersion attachment
