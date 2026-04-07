# Gotchas — CPQ Quote Templates

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Standard Setup > Quote Templates Produces Empty Line Items in CPQ Orgs

**What happens:** A quote PDF is generated but the line items table is completely blank. The header, footer, and any HTML content blocks render fine. Products are definitely on the quote.

**When it occurs:** Any time a practitioner navigates to Setup > Quote Templates, creates or edits a template there, and applies it to a CPQ quote. The standard template engine queries `QuoteLineItem` for line data. CPQ stores all quote lines in `SBQQ__QuoteLine__c`. These are separate objects; standard templates have no access to CPQ lines regardless of how columns are configured.

**How to avoid:** Always use the CPQ-native template objects (`SBQQ__QuoteTemplate__c`, `SBQQ__TemplateSection__c`, `SBQQ__TemplateContent__c`). Access them from the CPQ app (App Launcher > Salesforce CPQ > Quote Templates), not from Setup > Quote Templates.

---

## Gotcha 2: CSS Classes Are Silently Stripped — Inline Styles Required

**What happens:** A carefully styled HTML content block with brand colors, custom fonts, and table borders renders as completely unstyled plain text in the PDF. No error is thrown during preview; the styling simply does not appear.

**When it occurs:** When the HTML content block uses a `<style>` tag, an external stylesheet reference, or `class=""` attributes. CPQ's PDF pipeline converts HTML to XSL-FO (Extensible Stylesheet Language — Formatting Objects) before passing it to a PDF renderer. The XSL-FO conversion step does not process CSS class rules — only inline `style=""` attributes on individual elements are mapped to XSL-FO properties.

**How to avoid:** Write every CSS property as an inline style on the specific element. For example: `<p style="font-family:Arial,sans-serif; font-size:12px; color:#333333;">` instead of `<p class="body-text">`. Never use `<style>` blocks or rely on class inheritance. Modern layout techniques like flexbox and CSS grid are also not supported — use `<table>` for all multi-column layouts.

---

## Gotcha 3: Conditional Print Field Text Check Is Exact and Case-Sensitive

**What happens:** A conditional section never appears in the PDF even though the controlling field on the quote clearly has a value. Or the section always appears even when it should be hidden.

**When it occurs:** When the `SBQQ__ConditionalPrintField__c` references a Text field and the field value is `"True"`, `"TRUE"`, `"Yes"`, `"1"`, or any value other than exactly the lowercase string `"true"`. The CPQ section visibility check for Text fields compares the raw string value to `"true"` with case sensitivity. Practitioners commonly assume any truthy-looking value will work.

**How to avoid:** If you need conditional visibility, prefer a Checkbox field on `SBQQ__Quote__c` as the controlling field. Checkbox fields follow the simpler rule: `true` shows, `false` hides. If you must use a Text field, ensure the Flow or Apex that sets it writes exactly `"true"` (lowercase). Document this constraint in the Flow description so future maintainers do not change the value.

---

## Gotcha 4: Images Over 5 MB Cause Silent PDF Generation Failure

**What happens:** The PDF generates but contains no images, or the entire PDF comes back empty, or the generation times out with a generic error. There is no specific error message pointing to the image size as the cause.

**When it occurs:** Any time an image embedded in an HTML content block (via `<img>` tag referencing Salesforce Files, an external URL, or a base64 data URI) exceeds 5 MB. This limit applies per image, not per template. High-resolution logos, background images, and product images are the most common offenders.

**How to avoid:** Compress and resize images to under 5 MB before referencing them in templates. For logos, 180–300 px wide at 72 dpi is sufficient for PDF output. If using base64 encoding, be aware that base64 increases file size by roughly 33%, so compress the source image to under ~3.7 MB before encoding. Test with the Preview button after adding any image.

---

## Gotcha 5: Column Widths Must Sum to Exactly 100 — Overflow Causes Layout Breaks

**What happens:** The line items table in the PDF overflows the page margin, columns overlap, or the rightmost column is clipped. Sometimes the table wraps to a second page unexpectedly.

**When it occurs:** When `SBQQ__LineColumn__c` records have `SBQQ__DisplayWidth__c` values that do not sum to exactly 100. CPQ distributes column widths as percentages of the available table width. If they sum to 110, the table is 10% wider than the content area and wraps or clips. If they sum to 90, the table has an unexplained right gap.

**How to avoid:** After creating or modifying line columns, sum all `SBQQ__DisplayWidth__c` values and confirm the total equals 100. Make this a step in every review checklist before deploying a template to production.

---

## Gotcha 6: Multi-Language Requires Separate Template Records — There Is No Translation Layer

**What happens:** A practitioner tries to build one template with translated text or to use Salesforce Translation Workbench to translate field labels in the template. The PDF always renders in the language the template was originally authored in regardless of the user's locale or the account's language.

**When it occurs:** Any time an org serves multiple languages and assumes CPQ templates will respect locale or Translation Workbench settings. CPQ's template content (HTML blocks, Quote Terms text, column headings) is stored as static text in the record fields. Translation Workbench does not apply to these fields.

**How to avoid:** Create one `SBQQ__QuoteTemplate__c` per language with all content authored in that language. Build a Record-Triggered Flow on `SBQQ__Quote__c` that sets the `SBQQ__Template__c` lookup to the correct template based on a language or locale field on the quote or account.
