# Examples — CPQ Quote Templates

## Example 1: Building a Line Items Section with Custom Columns

**Context:** A sales ops team needs CPQ quote PDFs to display Product Name, Quantity, Unit Price, Discount Percent, and Net Total for each line item. The standard template only showed Product Name and Total Price.

**Problem:** The practitioner created a standard Salesforce quote template in Setup > Quote Templates and mapped fields from `QuoteLineItem`. The PDF always had an empty line items table because the org uses Salesforce CPQ and all lines are stored in `SBQQ__QuoteLine__c`, not `QuoteLineItem`.

**Solution:**

1. Create a `SBQQ__QuoteTemplate__c` record named "Standard CPQ Quote".
2. Create a `SBQQ__TemplateSection__c` child with `SBQQ__Type__c = Body` and `SBQQ__DisplayOrder__c = 2`.
3. Create a `SBQQ__TemplateContent__c` child of that section with `SBQQ__Type__c = Line Items`.
4. Create `SBQQ__LineColumn__c` records linked to the Line Items content:

```
SBQQ__LineColumn__c records:

Name: "Product Name"
  SBQQ__FieldName__c = SBQQ__ProductName__c
  SBQQ__Heading__c   = "Product"
  SBQQ__DisplayWidth__c = 40
  SBQQ__Alignment__c = Left

Name: "Quantity"
  SBQQ__FieldName__c = SBQQ__Quantity__c
  SBQQ__Heading__c   = "Qty"
  SBQQ__DisplayWidth__c = 10
  SBQQ__Alignment__c = Right
  SBQQ__FormatType__c = Decimal

Name: "Unit Price"
  SBQQ__FieldName__c = SBQQ__UnitPrice__c
  SBQQ__Heading__c   = "Unit Price"
  SBQQ__DisplayWidth__c = 20
  SBQQ__Alignment__c = Right
  SBQQ__FormatType__c = Currency

Name: "Discount"
  SBQQ__FieldName__c = SBQQ__Discount__c
  SBQQ__Heading__c   = "Disc %"
  SBQQ__DisplayWidth__c = 10
  SBQQ__Alignment__c = Right
  SBQQ__FormatType__c = Percent

Name: "Net Total"
  SBQQ__FieldName__c = SBQQ__NetTotal__c
  SBQQ__Heading__c   = "Net Total"
  SBQQ__DisplayWidth__c = 20
  SBQQ__Alignment__c = Right
  SBQQ__FormatType__c = Currency
```

5. Open any CPQ quote, set `SBQQ__Template__c` to the new template, and click Preview. All five columns appear with correct values from `SBQQ__QuoteLine__c`.

**Why it works:** `SBQQ__LineColumn__c` records read directly from `SBQQ__QuoteLine__c` at PDF generation time. The CPQ engine knows which object to query because this is a CPQ-native template — it is not the standard Salesforce quote template path that queries `QuoteLineItem`.

---

## Example 2: Conditional Discount Summary Section

**Context:** The contract team wants a "Special Pricing Terms" section to appear in the PDF only when the quote has been approved for a discount greater than 20%. For standard quotes the section must not print at all.

**Problem:** The first attempt used CSS `display:none` toggled by a merge field value inside the HTML content block. The CSS was silently ignored by the XSL-FO renderer and the section always printed regardless of the discount level.

**Solution:**

1. Add a custom checkbox field `Show_Special_Pricing__c` to `SBQQ__Quote__c`.
2. Create a CPQ Price Rule (or Record-Triggered Flow on `SBQQ__Quote__c`) that sets `Show_Special_Pricing__c = true` when any line has `SBQQ__Discount__c > 20`.
3. Create a `SBQQ__TemplateSection__c` with:
   - `SBQQ__Type__c = Body`
   - `SBQQ__DisplayOrder__c = 4`
   - `SBQQ__ConditionalPrintField__c = Show_Special_Pricing__c`
4. Add an HTML `SBQQ__TemplateContent__c` child with the "Special Pricing Terms" copy styled with inline CSS only.
5. On a quote with no discount, the section does not appear in the Preview PDF. On a quote with >20% discount, the section prints.

**Why it works:** `SBQQ__ConditionalPrintField__c` is evaluated server-side before XSL-FO rendering begins. When the controlling checkbox is `false`, the entire section is excluded from the document tree before the PDF engine runs — CSS never has an opportunity to override this.

---

## Example 3: Branded Cover Page with Inline Logo

**Context:** A company wants the first page of every CPQ quote PDF to show the company logo, the account name, the quote number, and the expiry date in a clean layout before the product table begins.

**Problem:** Placing the logo in the Header section caused it to repeat on every page. The team wanted it only on the first page.

**Solution:**

Create a Cover Page section with HTML content using inline styles and CPQ merge fields:

```html
<table style="width:100%; border-collapse:collapse; font-family:Arial, sans-serif;">
  <tr>
    <td style="width:60%; vertical-align:top; padding:20px 0;">
      <img src="data:image/png;base64,{{BASE64_LOGO_STRING}}"
           style="width:180px; height:auto;" alt="Company Logo" />
    </td>
    <td style="width:40%; vertical-align:top; padding:20px 0;
               text-align:right; font-size:12px; color:#333333;">
      <strong style="font-size:18px; color:#003366;">QUOTE</strong><br/>
      <span style="font-size:11px;">No: {!Quote.Name}</span><br/>
      <span style="font-size:11px;">Expires: {!Quote.SBQQ__ExpirationDate__c}</span>
    </td>
  </tr>
  <tr>
    <td colspan="2" style="padding-top:30px; font-size:14px; color:#003366;">
      Prepared for: <strong>{!Quote.SBQQ__Account__r.Name}</strong>
    </td>
  </tr>
</table>
```

Set the section `SBQQ__Type__c = Cover Page` and `SBQQ__PageBreakBefore__c = false`.

**Why it works:** The Cover Page section type prints exactly once as the first page of the document. Table-based layout with inline styles is the safest approach because the XSL-FO engine honors `<table>` structure and inline `style=""` attributes reliably, whereas floats, flex, or CSS grid are not supported.

---

## Anti-Pattern: Using Setup > Quote Templates in a CPQ Org

**What practitioners do:** Navigate to Setup > Quote Templates, create a template, add a line items table, and activate it. Then set the quote's template lookup to this record.

**What goes wrong:** The line items table in the PDF is completely empty. The rest of the template (header, custom text) renders fine, but no product lines appear. This happens because the standard quote template engine queries `QuoteLineItem` for line data. In a CPQ org, all quote lines are stored in `SBQQ__QuoteLine__c`. The two objects are not the same and the standard engine has no knowledge of the CPQ object.

**Correct approach:** Use the CPQ-native template hierarchy: `SBQQ__QuoteTemplate__c` → `SBQQ__TemplateSection__c` → `SBQQ__TemplateContent__c` with `SBQQ__LineColumn__c` records for the line items table. Access this from the CPQ app, not from Setup > Quote Templates.
