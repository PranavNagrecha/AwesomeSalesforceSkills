# Well-Architected Notes — CPQ Quote Templates

## Relevant Pillars

- **Reliability** — The most critical reliability concern is ensuring that quote PDFs always contain accurate line item data. This means using CPQ-native template objects rather than standard Salesforce quote templates, which query the wrong object (`QuoteLineItem` instead of `SBQQ__QuoteLine__c`) and produce empty tables silently. Conditional section logic must be verified with the Preview button before deployment; silent rendering failures (blank images, empty tables) are the most common reliability failure mode.

- **User Experience** — Quote PDFs are often the primary customer-facing document in a deal cycle. Poor layout, missing branding, or incorrect line item display directly impacts how customers perceive the vendor. Using inline CSS and table-based layouts ensures consistent rendering across the XSL-FO PDF engine. Preview-driven iteration is essential — the PDF renderer behaves differently from a browser, and what looks correct in HTML may render differently in PDF.

- **Operational Excellence** — Multi-language template management creates ongoing maintenance overhead. Every change to shared copy (disclaimer text, section headers) must be replicated across all language variants manually. This should be documented in the template's admin notes and factored into change management. Template assignment Flows should be version-controlled in source alongside the template metadata.

- **Security** — Template content blocks can embed merge fields from `SBQQ__Quote__c` and related objects. Practitioners should ensure that sensitive fields (internal cost, negotiation notes) are not accidentally included in line columns or HTML content that is sent to customers. The "Preview" feature generates PDFs using the running user's record access, so a practitioner with access to sensitive fields could inadvertently include them in a customer-facing template.

- **Performance** — Line items templates with many `SBQQ__LineColumn__c` records referencing complex formula fields can slow PDF generation, particularly on quotes with 50+ lines. Formula fields that traverse multiple object relationships are the main culprit. Pre-populating values in custom fields via Flow is preferred over multi-hop formulas for performance-sensitive orgs.

## Architectural Tradeoffs

**HTML Content Type vs. Custom (Visualforce) Content Type:** HTML content blocks are declarative and maintainable by admins. Visualforce custom content allows Apex-driven layout, dynamic conditional logic, and data from related objects beyond `SBQQ__Quote__c` and `SBQQ__QuoteLine__c`. The tradeoff is complexity: Visualforce content requires developer involvement, adds deployment dependencies, and must handle the CPQ page rendering context correctly. Use HTML content unless the layout cannot be expressed declaratively.

**Single Template with Conditional Sections vs. Multiple Templates:** A single template with many conditional sections is easier to maintain when branding is consistent across segments. Multiple templates per language, product line, or customer tier are easier to reason about individually but multiply the maintenance burden. For language requirements, multiple templates are mandatory. For business-segment variations, conditional sections are preferred if the variation is limited to a few sections.

**Inline Base64 Images vs. Salesforce Files URL:** Base64-encoded images are self-contained and work reliably in sandboxes and production without sharing configuration. Salesforce Files URLs can break if file permissions change, the file is deleted, or the template is moved between orgs. Prefer base64 for logos under 3.7 MB (the pre-encoding threshold that keeps the encoded string under 5 MB). For larger brand assets, use an externally hosted CDN URL.

## Anti-Patterns

1. **Mixing standard and CPQ template infrastructure** — Using `Setup > Quote Templates` (standard) in a CPQ org because it is familiar. This always produces PDFs with empty line item tables. CPQ quote lines live in `SBQQ__QuoteLine__c`; standard templates only query `QuoteLineItem`. The two objects are independent and there is no cross-object join in the standard template engine.

2. **Class-based CSS in HTML content blocks** — Writing HTML with `<style>` blocks or class attributes and expecting visual fidelity in PDF output. The XSL-FO conversion layer does not process CSS class rules. Practitioners who build the HTML in a browser dev environment and paste it into the template are caught by this because the browser renders correctly but the PDF does not. Inline styles on every element are the only reliable approach.

3. **Skipping Preview before deployment** — Activating a template in production without testing it against a real quote via the Preview button. Rendering failures (empty sections, missing images, broken tables) are silent — the PDF is generated without error messages but with incorrect content. Always preview against a quote that exercises every conditional path in the template.

## Official Sources Used

- Salesforce CPQ Help: Building Your CPQ Documents with CPQ Templates — https://help.salesforce.com/s/articleView?id=sf.cpq_doc_building_cpq_doc.htm
- Salesforce CPQ Help: Conditionally Show Template Sections — https://help.salesforce.com/s/articleView?id=sf.cpq_doc_conditional_print.htm
- Salesforce CPQ Help: Template Line Columns — https://help.salesforce.com/s/articleView?id=sf.cpq_doc_line_columns.htm
- Trailhead: Structure a Customized Quote Template — https://trailhead.salesforce.com/content/learn/modules/cpq-quote-templates
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
