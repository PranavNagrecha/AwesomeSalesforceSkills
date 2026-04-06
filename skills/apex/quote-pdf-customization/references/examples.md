# Examples — Quote PDF Customization

## Example 1: Custom Branded Quote PDF with Standard Controller Extension

**Context:** A manufacturing company uses standard Salesforce Quotes. Their current quote template uses the declarative editor, but they need a custom header with a logo, conditional discount summary section, and page breaks between product groups.

**Problem:** The declarative template editor has no conditional section support and cannot render the company logo reliably (images often break in the PDF output). A JavaScript-based workaround fails silently because the PDF renderer ignores scripts.

**Solution:**

Visualforce page (`QuotePdf.page`):
```xml
<apex:page standardController="Quote"
           extensions="QuotePdfController"
           renderAs="pdf"
           showHeader="false"
           sidebar="false"
           contentType="application/pdf#QuotePdf.pdf">
  <head>
    <apex:stylesheet value="{!URLFOR($Resource.QuotePdfStyles)}"/>
  </head>
  <body>
    <!-- Header with embedded logo — logoUrl is an absolute URL from the Apex controller -->
    <div class="pdf-header">
      <img src="{!logoUrl}" alt="Company Logo" class="logo"/>
      <h1>Quote #{!quote.QuoteNumber}</h1>
    </div>

    <!-- Line items table using CSS 2.1 table layout -->
    <table class="line-items">
      <thead>
        <tr>
          <th>Product</th>
          <th>Qty</th>
          <th>Unit Price</th>
          <th>Total</th>
        </tr>
      </thead>
      <tbody>
        <apex:repeat value="{!lineItems}" var="li">
          <!-- page-break-inside: avoid on a div wrapper is more reliable than on tr -->
          <tr><td colspan="4" style="padding:0;">
            <div style="page-break-inside: avoid; display: table; width: 100%;">
              <div style="display: table-cell; padding: 4pt;"><apex:outputText value="{!li.Product2.Name}"/></div>
              <div style="display: table-cell; padding: 4pt;"><apex:outputText value="{!li.Quantity}"/></div>
              <div style="display: table-cell; padding: 4pt;"><apex:outputText value="{!li.UnitPrice}"/></div>
              <div style="display: table-cell; padding: 4pt;"><apex:outputText value="{!li.TotalPrice}"/></div>
            </div>
          </td></tr>
        </apex:repeat>
      </tbody>
    </table>

    <!-- Conditional discount section — excluded from DOM when showDiscounts is false -->
    <apex:outputPanel rendered="{!showDiscounts}">
      <div class="discount-section">
        <h3>Applied Discounts</h3>
        <apex:repeat value="{!discountLines}" var="dl">
          <p><apex:outputText value="{!dl.Product2.Name}"/> — <apex:outputText value="{!dl.Discount}"/>% discount</p>
        </apex:repeat>
      </div>
    </apex:outputPanel>
  </body>
</apex:page>
```

Apex extension (`QuotePdfController.cls`):
```apex
public with sharing class QuotePdfController {
    public Quote quote { get; private set; }
    public List<QuoteLineItem> lineItems { get; private set; }
    public List<QuoteLineItem> discountLines { get; private set; }
    public Boolean showDiscounts { get; private set; }
    public String logoUrl { get; private set; }

    public QuotePdfController(ApexPages.StandardController sc) {
        Id quoteId = sc.getId();

        // WITH USER_MODE enforces FLS automatically (Summer '23+)
        quote = [
            SELECT Id, QuoteNumber, ExpirationDate, TotalPrice
            FROM Quote
            WHERE Id = :quoteId
            WITH USER_MODE
            LIMIT 1
        ];

        lineItems = [
            SELECT Product2.Name, Quantity, UnitPrice, TotalPrice, Discount
            FROM QuoteLineItem
            WHERE QuoteId = :quoteId
            WITH USER_MODE
            ORDER BY SortOrder
        ];

        discountLines = new List<QuoteLineItem>();
        for (QuoteLineItem li : lineItems) {
            if (li.Discount != null && li.Discount > 0) {
                discountLines.add(li);
            }
        }
        showDiscounts = !discountLines.isEmpty();

        // Build absolute URL — relative $Resource paths fail in the Flying Saucer PDF renderer
        String resourceId = [
            SELECT Id FROM StaticResource WHERE Name = 'CompanyLogo' WITH USER_MODE LIMIT 1
        ].Id;
        logoUrl = URL.getSalesforceBaseUrl().toExternalForm()
                  + '/resource/' + resourceId + '/CompanyLogo.png';
    }
}
```

CSS static resource (`QuotePdfStyles.css`) — CSS 2.1 only:
```css
body { font-family: Arial, sans-serif; font-size: 10pt; }
.pdf-header { border-bottom: 2pt solid #003366; margin-bottom: 12pt; overflow: hidden; }
.logo { height: 48pt; float: right; }
table.line-items { width: 100%; border-collapse: collapse; }
table.line-items th { background-color: #003366; color: white; padding: 4pt; text-align: left; }
table.line-items td { padding: 0; border-bottom: 0.5pt solid #cccccc; }
.discount-section { margin-top: 12pt; border-top: 1pt solid #cccccc; padding-top: 8pt; }
```

**Why it works:** `WITH USER_MODE` enforces FLS on the SOQL without manual `Schema` checks. `rendered="{!showDiscounts}"` suppresses the discount section at the server level — the HTML is never sent to the PDF renderer, so no hidden data can leak. The absolute logo URL constructed from the static resource Id bypasses the relative-path limitation of the Flying Saucer renderer.

---

## Example 2: Programmatic PDF Generation and Attachment via Queueable

**Context:** A financial services firm needs Quote PDFs automatically generated and attached to the Quote record the moment a rep moves the status to "Approved". A Flow triggers the process, but the PDF attachment must happen server-side without user interaction.

**Problem:** Calling `PageReference.getContentAsPDF()` inside an Apex trigger throws a `CalloutException` ("You have uncommitted work pending. Please commit or rollback before calling out"). The PDF generation must be offloaded to an async context.

**Solution:**

Flow or trigger enqueues the Queueable:
```apex
// Called from a trigger or Invocable method — enqueue, never call inline
System.enqueueJob(new QuotePdfAttachmentJob(quoteId));
```

Queueable class (`QuotePdfAttachmentJob.cls`):
```apex
public class QuotePdfAttachmentJob implements Queueable, Database.AllowsCallouts {
    private Id quoteId;

    public QuotePdfAttachmentJob(Id quoteId) {
        this.quoteId = quoteId;
    }

    public void execute(QueueableContext ctx) {
        PageReference pdfPage = Page.QuotePdf;
        pdfPage.getParameters().put('id', quoteId);

        Blob pdfBlob;
        if (Test.isRunningTest()) {
            // getContentAsPDF() is not supported in test context — use a placeholder
            pdfBlob = Blob.valueOf('PDF_PLACEHOLDER');
        } else {
            pdfBlob = pdfPage.getContentAsPDF();
        }

        // CRITICAL: getContentAsPDF() returns null if the VF page throws an exception
        // Never skip this null check — a null blob causes a DmlException on insert
        if (pdfBlob == null) {
            System.debug(LoggingLevel.ERROR,
                'QuotePdfAttachmentJob: getContentAsPDF() returned null for Quote ' + quoteId
                + '. Check debug logs for errors on the QuotePdf VF page.');
            return;
        }

        Quote q = [SELECT QuoteNumber FROM Quote WHERE Id = :quoteId WITH USER_MODE LIMIT 1];

        ContentVersion cv = new ContentVersion(
            Title       = 'Quote_' + q.QuoteNumber + '.pdf',
            PathOnClient = 'Quote_' + q.QuoteNumber + '.pdf',
            VersionData  = pdfBlob,
            IsMajorVersion = true
        );
        insert cv;

        // Retrieve the ContentDocumentId created by the insert
        Id contentDocId = [
            SELECT ContentDocumentId FROM ContentVersion WHERE Id = :cv.Id LIMIT 1
        ].ContentDocumentId;

        ContentDocumentLink link = new ContentDocumentLink(
            LinkedEntityId  = quoteId,
            ContentDocumentId = contentDocId,
            ShareType       = 'V',
            Visibility      = 'AllUsers'
        );
        insert link;
    }
}
```

**Why it works:** `Database.AllowsCallouts` is required for a Queueable that makes callouts — `getContentAsPDF()` is an internal platform callout and requires this interface. The explicit null check prevents a silent 0-byte file from being attached when the VF page fails. `Test.isRunningTest()` allows unit tests to run without a real VF page render.

---

## Anti-Pattern: Using CSS `display:none` to Hide Sensitive Quote Sections

**What practitioners do:** A developer wants to conditionally hide a "Confidential Pricing" section in the PDF. They add `style="display:none"` to a `<div>` in the VF markup instead of using `rendered="{!showSection}"`.

**What goes wrong:** `display:none` is a CSS instruction processed by the browser's rendering engine. The Flying Saucer PDF renderer handles CSS differently from browsers, and its support for `display:none` is inconsistent. More critically, the hidden HTML is still present in the VF page source — any user who navigates to the VF page URL (without `renderAs="pdf"`) can read the hidden content directly in the browser or page source.

**Correct approach:** Use Visualforce's server-side `rendered="{!showSection}"` attribute on `<apex:outputPanel>` or any VF component. When `rendered` is `false`, the component is never included in the HTML output — it does not exist in the DOM, in the page source, or in the PDF input. This is the only safe way to conditionally exclude sensitive content from a VF-rendered page.
