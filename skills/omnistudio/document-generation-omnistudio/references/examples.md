# Examples — Document Generation OmniStudio

## Example 1: Client-Side Quote PDF Generation via OmniScript

**Context:** A sales team needs to generate branded quote PDFs during customer calls. The rep selects a quote record, reviews line items, and generates the PDF in real time from an OmniScript embedded on the Quote record page.

**Problem:** Without proper token mapping, the template renders blank fields or misaligned repeating rows. The OmniDataTransform output JSON must match the template token structure exactly, including nested paths for line items.

**Solution:**

Template tokens in the .docx file:
```text
Quote Number: {{QuoteNumber}}
Account: {{AccountName}}
Date: {{QuoteDate}}

{{#LineItems}}
| {{ProductName}} | {{Quantity}} | {{UnitPrice}} | {{TotalPrice}} |
{{/LineItems}}

Total: {{GrandTotal}}
```

OmniDataTransform output JSON structure:
```json
{
  "QuoteNumber": "Q-00123",
  "AccountName": "Acme Corp",
  "QuoteDate": "2026-04-05",
  "LineItems": [
    {
      "ProductName": "Widget A",
      "Quantity": 10,
      "UnitPrice": "$50.00",
      "TotalPrice": "$500.00"
    },
    {
      "ProductName": "Widget B",
      "Quantity": 5,
      "UnitPrice": "$100.00",
      "TotalPrice": "$500.00"
    }
  ],
  "GrandTotal": "$1,000.00"
}
```

OmniScript structure:
```text
Step 1: DataRaptor Extract — pulls Quote + QuoteLineItems, outputs JSON
Step 2: DocGen Document — references Document Generation Setting, receives JSON
Step 3: fndMultiPDFConvertLwc — converts .docx output to PDF
Step 4: Save — stores ContentVersion linked to Quote record
```

**Why it works:** The JSON key names match the template tokens exactly (case-sensitive). The `LineItems` key is an array, which the `{{#LineItems}}...{{/LineItems}}` repeating section iterates over. The PDF conversion is an explicit separate step after DocGen.

---

## Example 2: Server-Side Batch Invoice Generation via Integration Procedure

**Context:** A billing system generates monthly invoices for all active accounts. An Apex scheduled job triggers an Integration Procedure for each account, which generates the invoice document and attaches it as a file.

**Problem:** Using client-side generation would require a user session and could only process one document at a time. Server-side generation handles the batch volume asynchronously.

**Solution:**

Integration Procedure structure:
```text
IP: GenerateMonthlyInvoice
  Input: AccountId (String)

  Step 1: DataRaptor Extract — "InvoiceDataExtract"
    - Input: AccountId
    - Output: JSON with invoice header + line items

  Step 2: DocGen Action — "GenerateInvoiceDoc"
    - Document Generation Setting: "MonthlyInvoiceSetting"
    - Input: JSON from Step 1
    - Output: ContentVersionId

  Step 3: DataRaptor Post — "LinkInvoiceToAccount"
    - Creates ContentDocumentLink to attach file to Account
```

Apex trigger (simplified):
```apex
// Scheduled Apex calls the IP for each active account
for (Account acc : activeAccounts) {
    Map<String, Object> ipInput = new Map<String, Object>{
        'AccountId' => acc.Id
    };
    // Call Integration Procedure
    omnistudio.IntegrationProcedureService.runIntegrationService(
        'GenerateMonthlyInvoice', ipInput, new Map<String, Object>()
    );
}
```

**Why it works:** Server-side generation runs asynchronously on Salesforce compute resources, not in a browser. The Integration Procedure handles data extraction, document generation, and file linking in a single orchestrated flow. No image or rich text tokens are used, which is required for server-side mode.

---

## Example 3: Conditional Sections for Multi-Region Compliance

**Context:** A global company generates compliance documents that include region-specific legal clauses. The same template handles US, EU, and APAC regions using conditional sections.

**Solution:**

Template with conditional tokens:
```text
{{#if IsUS}}
This agreement is governed by the laws of the State of Delaware.
{{/if}}

{{#if IsEU}}
This agreement complies with GDPR requirements under EU regulation 2016/679.
Data processing is subject to the attached Data Processing Agreement.
{{/if}}

{{#if IsAPAC}}
This agreement is subject to the laws of Singapore.
{{/if}}
```

OmniDataTransform formula mappings:
```text
IsUS    = IF(Account.BillingCountry = "US", true, false)
IsEU    = IF(CONTAINS("DE,FR,IT,ES,NL", Account.BillingCountry), true, false)
IsAPAC  = IF(CONTAINS("SG,AU,JP,KR", Account.BillingCountry), true, false)
```

**Why it works:** The conditional `{{#if}}` tokens evaluate boolean values in the JSON. The Data Mapper computes the boolean flags from the Account's billing country, so the template renders only the relevant legal clause.

---

## Anti-Pattern: Hardcoding Token Values in OmniScript Instead of Using Data Mapper

**What practitioners do:** Instead of building an OmniDataTransform to map tokens, they use Set Values actions in the OmniScript to manually construct the JSON payload with hardcoded field references and string concatenation.

**What goes wrong:** The JSON structure becomes fragile and unmaintainable. When the template changes (tokens added, renamed, or restructured), the Set Values actions must be manually updated in multiple places. There is no automatic token extraction or validation. Repeating sections are especially error-prone because the practitioner must manually build the JSON array.

**Correct approach:** Always use an OmniDataTransform (Mapping Data Mapper) as the single source of truth for token-to-field mapping. The Data Mapper can auto-extract tokens from the template, provides a visual mapping interface, and ensures the JSON structure matches the template. Use Set Values only for simple overrides or user-entered values that supplement the Data Mapper output.
