# LLM Anti-Patterns — CPQ Quote Templates

Common mistakes AI coding assistants make when generating or advising on Salesforce CPQ quote templates.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Directing Users to Setup > Quote Templates for CPQ Line Items

**What the LLM generates:** Instructions to navigate to Setup > Quote Templates, create a new template, add a "Line Items" section, and configure columns to display product information for a CPQ org.

**Why it happens:** Standard Salesforce Quote Templates are prominently documented and appear first in most search results about "Salesforce quote templates." LLMs trained on general Salesforce documentation default to this path without distinguishing between standard Quotes and CPQ. The CPQ-specific template objects (`SBQQ__QuoteTemplate__c`) are in a managed package namespace and appear less frequently in training data.

**Correct pattern:**

```
CPQ orgs must use the CPQ-native template hierarchy:
  SBQQ__QuoteTemplate__c  →  SBQQ__TemplateSection__c  →  SBQQ__TemplateContent__c

Access via: App Launcher > Salesforce CPQ > Quote Templates

Standard Setup > Quote Templates queries QuoteLineItem.
CPQ stores lines in SBQQ__QuoteLine__c.
Mixing these paths always produces empty line item tables.
```

**Detection hint:** Any recommendation to go to `Setup > Quote Templates` in the context of a CPQ (SBQQ) org should be flagged as incorrect. Look for the phrases "Setup > Quote Templates", "standard quote template", or references to `QuoteLineItem` in a CPQ context.

---

## Anti-Pattern 2: Using CSS Classes or Style Blocks in HTML Content

**What the LLM generates:** HTML content for a CPQ template that includes a `<style>` block at the top, or elements with `class="brand-header"` attributes, or Bootstrap-like class utilities.

```html
<!-- Wrong: LLM-generated HTML with a style block and classes -->
<style>
  .brand-header { font-family: Arial; color: #003366; font-size: 18px; }
  .line-table td { border: 1px solid #ccc; padding: 4px; }
</style>
<h1 class="brand-header">Quote Document</h1>
<table class="line-table">...</table>
```

**Why it happens:** LLMs learn HTML best practices from web development content, where external stylesheets and class-based CSS are standard. The XSL-FO rendering pipeline used by CPQ for PDF generation is not well-represented in training data, and the constraint that only inline styles work is counterintuitive compared to normal web development.

**Correct pattern:**

```html
<!-- Correct: all styles inline on every element -->
<h1 style="font-family:Arial,sans-serif; color:#003366; font-size:18px;">Quote Document</h1>
<table style="width:100%; border-collapse:collapse;">
  <tr>
    <td style="border:1px solid #cccccc; padding:4px; font-family:Arial,sans-serif;">
      Cell content
    </td>
  </tr>
</table>
```

**Detection hint:** Look for `<style>` tags anywhere in HTML content blocks, or `class="..."` attributes on HTML elements within CPQ template content. Both are wrong in this context.

---

## Anti-Pattern 3: Using CSS `display:none` for Conditional Section Visibility

**What the LLM generates:** HTML content that wraps a section in a `<div style="display:none;">` or uses a merge field to dynamically toggle display, expecting this to control visibility in the PDF.

```html
<!-- Wrong: conditional visibility via CSS -->
<div style="display: {!IF(Quote.Show_Discount__c, 'block', 'none')};">
  <h2>Discount Summary</h2>
  <!-- discount table here -->
</div>
```

**Why it happens:** CSS `display:none` is the standard web mechanism for hiding elements. LLMs trained on HTML/CSS documentation generate this naturally. The CPQ template conditional system using `SBQQ__ConditionalPrintField__c` is a proprietary declarative mechanism that is not widely documented in public training data.

**Correct pattern:**

```
Use SBQQ__TemplateSection__c.SBQQ__ConditionalPrintField__c:
  - Set it to the API name of a Checkbox field on SBQQ__Quote__c
  - The section prints when the checkbox = true
  - The section is excluded from the document tree when false
  - CSS visibility properties are not evaluated by the PDF renderer
```

**Detection hint:** Any `display:none`, `visibility:hidden`, or merge-field-based conditional CSS in a CPQ template HTML block. Also flag attempts to use `{!IF(...)}` merge syntax inside `style` attributes for conditional rendering.

---

## Anti-Pattern 4: Recommending `QuoteLineItem` SOQL in a CPQ Context

**What the LLM generates:** SOQL queries or Apex code that queries `QuoteLineItem` to populate line column data, or recommendations to map `QuoteLineItem` fields to line columns.

```apex
// Wrong: querying QuoteLineItem in a CPQ org for PDF data
List<QuoteLineItem> lines = [
    SELECT Product2.Name, Quantity, UnitPrice, Discount
    FROM QuoteLineItem
    WHERE QuoteId = :quoteId
];
```

**Why it happens:** `QuoteLineItem` is the standard Salesforce object for quote products and is very prominent in documentation and training data. `SBQQ__QuoteLine__c` is a managed package object that appears less frequently. LLMs conflate the two unless specifically prompted about CPQ.

**Correct pattern:**

```apex
// Correct: query SBQQ__QuoteLine__c for CPQ line data
List<SBQQ__QuoteLine__c> lines = [
    SELECT SBQQ__ProductName__c, SBQQ__Quantity__c,
           SBQQ__UnitPrice__c, SBQQ__Discount__c, SBQQ__NetTotal__c
    FROM SBQQ__QuoteLine__c
    WHERE SBQQ__Quote__c = :quoteId
    ORDER BY SBQQ__Number__c
];
```

**Detection hint:** Any mention of `QuoteLineItem` in a CPQ (SBQQ) context. Also watch for `QuoteId` as the lookup field name — CPQ lines use `SBQQ__Quote__c`, not `QuoteId`.

---

## Anti-Pattern 5: Assuming Multi-Language Is Handled by Translation Workbench

**What the LLM generates:** Instructions to go to Setup > Translation Workbench, translate field labels and picklist values on the CPQ template objects, and expect the PDF to render in the user's language automatically.

**Why it happens:** Salesforce Translation Workbench is the correct tool for translating UI labels, picklist values, and field labels across most of the platform. LLMs generalize this capability to all content. The fact that CPQ template HTML content, Quote Terms text, and line column headings are stored as raw text in record fields — and are therefore outside the Translation Workbench scope — is a specific limitation not well-documented relative to the general translation feature.

**Correct pattern:**

```
CPQ template translation strategy:
1. Create one SBQQ__QuoteTemplate__c per language
   (e.g., "Standard Quote – English", "Standard Quote – French")
2. Author all HTML content, Quote Terms, and column headings in the target language
3. Build a Record-Triggered Flow on SBQQ__Quote__c:
   - Trigger: when Quote_Language__c or Account BillingCountry changes
   - Decision: branch by language
   - Assignment: set SBQQ__Quote__c.SBQQ__Template__c to the correct template ID
```

**Detection hint:** Any recommendation to use Translation Workbench for CPQ template content. Also flag suggestions that a single template can serve multiple languages through Salesforce's translation layer.

---

## Anti-Pattern 6: Not Accounting for 5 MB Image Limit

**What the LLM generates:** Instructions to add a company logo to a CPQ template by uploading a high-resolution PNG or JPEG from brand assets, without any mention of file size constraints.

**Why it happens:** The 5 MB per-image limit for CPQ templates is a product-specific constraint not commonly documented alongside general image handling guidance. LLMs do not spontaneously apply size limits when describing image embedding unless the constraint appears in their training data for this specific feature.

**Correct pattern:**

```
Before embedding any image in a CPQ quote template:
  1. Check file size: must be under 5 MB
  2. If base64-encoding: the source file must be under ~3.7 MB
     (base64 encoding adds ~33% size overhead)
  3. Recommended: compress logo to 180-300px wide at 72dpi
  4. Always test with Preview after adding an image
  5. If PDF generates blank after adding image: image size is the first thing to check
```

**Detection hint:** Any image embedding instructions that do not mention the 5 MB limit. Also flag base64-encoding recommendations that do not account for the encoding overhead when advising on source file size.
