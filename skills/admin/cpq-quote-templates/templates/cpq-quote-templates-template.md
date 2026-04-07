# CPQ Quote Templates — Work Template

Use this template when working on CPQ (SBQQ) quote template design or troubleshooting tasks.

## Scope

**Skill:** `admin/cpq-quote-templates`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record answers to the Before Starting questions from SKILL.md:

- **CPQ package confirmed installed?** (yes / no — if no, stop and verify before proceeding)
- **Existing templates:** (list any SBQQ__QuoteTemplate__c records already in the org)
- **Line fields needed in table:** (list the SBQQ__QuoteLine__c API field names)
- **Conditional sections required:** (list section name → controlling field name)
- **Multi-language requirement:** (yes / no — if yes, list languages)
- **Branding assets:** (logo file size, max dimensions, color hex codes)

## Approach

Which pattern from SKILL.md applies?

- [ ] Pattern 1: Branded Cover Page with Company Logo
- [ ] Pattern 2: Conditional Discount Summary Section
- [ ] Pattern 3: Multi-Language Templates via Flow
- [ ] Custom approach — describe below:

**Reason for chosen approach:**

## Object Hierarchy Plan

```
SBQQ__QuoteTemplate__c: "[Template Name]"
  │
  ├── SBQQ__TemplateSection__c: "Cover Page"
  │     Type: Cover Page | Order: 1 | Conditional: (none)
  │     └── SBQQ__TemplateContent__c: "Cover HTML"
  │           Type: HTML
  │
  ├── SBQQ__TemplateSection__c: "Header"
  │     Type: Header | Order: 2 | Conditional: (none)
  │     └── SBQQ__TemplateContent__c: "Header HTML"
  │           Type: HTML
  │
  ├── SBQQ__TemplateSection__c: "Products"
  │     Type: Body | Order: 3 | Conditional: (none)
  │     └── SBQQ__TemplateContent__c: "Line Items Table"
  │           Type: Line Items
  │           └── SBQQ__LineColumn__c: [field list — see below]
  │
  ├── SBQQ__TemplateSection__c: "[Conditional Section Name]"
  │     Type: Body | Order: 4 | Conditional: [Field_API_Name__c]
  │     └── SBQQ__TemplateContent__c: "Section HTML"
  │           Type: HTML
  │
  └── SBQQ__TemplateSection__c: "Footer"
        Type: Footer | Order: 5 | Conditional: (none)
        └── SBQQ__TemplateContent__c: "Footer HTML"
              Type: HTML
```

## Line Column Plan

| Column Name | SBQQ__FieldName__c | Heading | Width % | Alignment | Format |
|---|---|---|---|---|---|
| Product Name | SBQQ__ProductName__c | Product | 35 | Left | — |
| Quantity | SBQQ__Quantity__c | Qty | 10 | Right | Decimal |
| Unit Price | SBQQ__UnitPrice__c | Unit Price | 20 | Right | Currency |
| Discount | SBQQ__Discount__c | Disc % | 10 | Right | Percent |
| Net Total | SBQQ__NetTotal__c | Net Total | 25 | Right | Currency |
| **Total** | | | **100** | | |

(Adjust columns and widths for this engagement — widths MUST sum to 100)

## Checklist

Copy from SKILL.md review checklist and tick items as you complete them:

- [ ] CPQ managed package (SBQQ) confirmed installed; NOT using Setup > Quote Templates
- [ ] All `SBQQ__TemplateSection__c` records have correct `SBQQ__Type__c` and `SBQQ__DisplayOrder__c`
- [ ] All conditional sections have a valid `SBQQ__ConditionalPrintField__c` pointing to a real field on `SBQQ__Quote__c`
- [ ] Line Items content type has corresponding `SBQQ__LineColumn__c` records; column widths sum to 100
- [ ] All HTML content uses inline styles only (no `<style>` blocks, no CSS classes)
- [ ] All images are under 5 MB; logo renders correctly in Preview
- [ ] "Preview" button used to verify the PDF before deploying; line items table is not empty
- [ ] Multi-language templates (if needed) each have a separate `SBQQ__QuoteTemplate__c`; Flow assigns the correct template

## Notes

Record any deviations from the standard pattern and why:

(e.g., "Using Custom (Visualforce) content type for the pricing table because the customer requires Apex-calculated bundle pricing rollups that are not available as formula fields on SBQQ__QuoteLine__c")
