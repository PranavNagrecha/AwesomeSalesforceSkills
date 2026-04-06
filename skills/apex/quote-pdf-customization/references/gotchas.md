# Gotchas — Quote PDF Customization

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: `{!$Resource.Logo}` Produces a Relative URL the PDF Renderer Cannot Resolve

**What happens:** The logo image does not appear in the generated PDF. The cell in the PDF is blank or shows a broken-image placeholder, even though the logo displays correctly when viewing the VF page in a browser.

**When it occurs:** Any time `<img src="{!$Resource.Logo}">` is used in a VF page with `renderAs="pdf"`. The expression `{!$Resource.Logo}` resolves to a relative path such as `/resource/1234567890000/Logo.png`. The Flying Saucer renderer makes a separate HTTP request for each asset and treats relative paths as local filesystem references — it cannot resolve them against the Salesforce domain.

**How to avoid:** Two options:
1. Build an absolute URL in the Apex controller:
   ```apex
   String resourceId = [SELECT Id FROM StaticResource WHERE Name = 'CompanyLogo' WITH USER_MODE LIMIT 1].Id;
   logoUrl = URL.getSalesforceBaseUrl().toExternalForm() + '/resource/' + resourceId + '/CompanyLogo.png';
   ```
2. Embed the image as a base64 data URI in the CSS static resource:
   ```css
   .logo { background-image: url('data:image/png;base64,<base64-string>'); }
   ```

---

## Gotcha 2: `getContentAsPDF()` Returns `null` on VF Page Errors Instead of Throwing

**What happens:** The programmatic PDF generation appears to succeed (no exception is thrown), but the `ContentVersion` inserted downstream has `VersionData` set to null, causing a `DmlException` or a 0-byte file attached to the Quote.

**When it occurs:** When the Visualforce page referenced by the `PageReference` throws an unhandled Apex exception or produces an error page (SOQL error, null pointer, permission error). The platform swallows the inner error and returns `null` from `getContentAsPDF()`.

**How to avoid:** Always assert the return value:
```apex
Blob pdfBlob = pdfPage.getContentAsPDF();
if (pdfBlob == null) {
    throw new CalloutException(
        'PDF generation failed for Quote: ' + quoteId
        + ' — VF page returned null. Check debug logs for QuotePdf page errors.');
}
```
Instrument the VF page's Apex controller with try/catch blocks that write to a custom log object so the inner error is surfaced independently.

---

## Gotcha 3: Standard VF Controller Cannot Access CPQ Quote Line Items

**What happens:** The PDF renders the header and totals correctly but the line items section is empty, or only shows standard `QuoteLineItem` records that are not the CPQ lines the rep configured.

**When it occurs:** When an org uses Salesforce CPQ and the PDF template uses `standardController="Quote"` or the standard Salesforce quote template system. CPQ stores configured line items in `SBQQ__QuoteLine__c`, not `QuoteLineItem`. A standard-controller VF page never sees these records.

**How to avoid:** Build the VF page with a fully custom Apex controller querying CPQ objects directly:
```apex
List<SBQQ__QuoteLine__c> cpqLines = [
    SELECT SBQQ__ProductName__c, SBQQ__Quantity__c, SBQQ__NetPrice__c
    FROM SBQQ__QuoteLine__c
    WHERE SBQQ__Quote__c = :quoteId
    WITH USER_MODE
    ORDER BY SBQQ__Number__c
];
```

---

## Gotcha 4: `page-break-inside: avoid` Is Unreliable on `<tr>` Elements

**What happens:** Line-item rows in the PDF are split in the middle across page boundaries. The CSS property `page-break-inside: avoid` is present on the `<tr>` elements but has no effect.

**When it occurs:** Flying Saucer has inconsistent support for `page-break-inside: avoid` on table rows (`<tr>`). It is more reliably honored on block-level elements (`<div>`, `<p>`).

**How to avoid:** Wrap each row's content in a `<div style="page-break-inside: avoid;">` inside the `<apex:repeat>`, using `display:table` / `display:table-cell` CSS to simulate columns:
```xml
<apex:repeat value="{!lineItems}" var="li">
  <div style="display:table; width:100%; page-break-inside: avoid;">
    <div style="display:table-cell; width:50%;">
      <apex:outputText value="{!li.Product2.Name}"/>
    </div>
    <div style="display:table-cell; width:25%; text-align:right;">
      <apex:outputText value="{!li.Quantity}"/>
    </div>
    <div style="display:table-cell; width:25%; text-align:right;">
      <apex:outputText value="{!li.TotalPrice}"/>
    </div>
  </div>
</apex:repeat>
```

---

## Gotcha 5: `getContentAsPDF()` Counts Against the 100-Callout-Per-Transaction Limit

**What happens:** A batch job that generates PDFs for multiple Quotes fails with `System.CalloutException: Callout loop detected` or exhausts the 100-callout limit mid-batch.

**When it occurs:** Each call to `getContentAsPDF()` is an internal HTTP callout. A Queueable or Batch `execute()` method that loops over multiple Quotes and calls `getContentAsPDF()` once per record will hit the limit at 100 records.

**How to avoid:** Generate exactly one PDF per Queueable or Batch `execute()` invocation. Use `executeBatch(job, 1)` (scope size of 1) for Batch Apex to ensure each transaction processes exactly one Quote and makes one callout.

---

## Gotcha 6: Non-Latin Characters Render as Boxes When Font Coverage Is Missing

**What happens:** A multi-language quote PDF shows question marks or empty boxes instead of Chinese, Japanese, Arabic, or Cyrillic characters, even though `<apex:page language="zh">` is set correctly.

**When it occurs:** Flying Saucer uses the JVM's available fonts. Salesforce's server JVM does not include comprehensive Unicode font coverage for CJK or right-to-left scripts by default.

**How to avoid:** Embed a Unicode font using `@font-face` in the CSS static resource with the font file encoded as a base64 data URI:
```css
@font-face {
    font-family: 'NotoSans';
    src: url('data:font/truetype;base64,<base64-font-data>') format('truetype');
}
body { font-family: 'NotoSans', Arial, sans-serif; }
```
Google's Noto Sans family provides comprehensive multilingual coverage and is freely licensed. Keep font file sizes in mind — large base64 fonts increase the static resource size and PDF rendering time.
