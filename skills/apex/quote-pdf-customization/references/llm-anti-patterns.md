# LLM Anti-Patterns — Quote PDF Customization

Common mistakes AI coding assistants make when generating or advising on Quote PDF Customization.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using `{!$Resource.Logo}` Directly in an `<img src>` Tag

**What the LLM generates:**
```xml
<img src="{!$Resource.CompanyLogo}" alt="Logo" />
```

**Why it happens:** LLMs are trained on many Visualforce examples that use `$Resource` for images in standard (browser-rendered) pages, where the relative URL works fine. The distinction that Flying Saucer (the PDF renderer) cannot resolve relative URLs is a Salesforce-specific behavior not consistently represented in training data.

**Correct pattern:**
```apex
// In Apex controller constructor — build an absolute URL
String resourceId = [
    SELECT Id FROM StaticResource WHERE Name = 'CompanyLogo' WITH USER_MODE LIMIT 1
].Id;
logoUrl = URL.getSalesforceBaseUrl().toExternalForm() + '/resource/' + resourceId + '/CompanyLogo.png';
```
```xml
<!-- In VF page — use the controller property that holds the absolute URL -->
<img src="{!logoUrl}" alt="Logo" />
```
Or embed the image as base64 in the CSS: `background-image: url('data:image/png;base64,...')`.

**Detection hint:** Any `<img src="{!$Resource.` in a page with `renderAs="pdf"` — the bare `$Resource` merge field without an absolute URL base is the signal.

---

## Anti-Pattern 2: Including `<script>` Tags for Dynamic Behavior in PDF Pages

**What the LLM generates:**
```xml
<apex:page renderAs="pdf">
  <script>
    // Dynamically calculate and show discount totals
    document.getElementById('discountTotal').innerText = calculateTotal();
  </script>
  <div id="discountTotal"></div>
</apex:page>
```

**Why it happens:** LLMs default to JavaScript for dynamic UI behavior because it is the dominant pattern for web pages. The restriction that VF PDF rendering skips JavaScript entirely is a Salesforce-specific platform constraint not well represented in general web development training data.

**Correct pattern:**
```apex
// All dynamic behavior must be computed server-side in the Apex controller
public Decimal discountTotal {
    get {
        Decimal total = 0;
        for (QuoteLineItem li : lineItems) {
            if (li.Discount != null) {
                total += li.TotalPrice * (li.Discount / 100);
            }
        }
        return total;
    }
}
```
```xml
<!-- Bind the pre-computed value directly in the VF markup -->
<apex:outputText value="{!discountTotal}" />
```

**Detection hint:** Any `<script>` tag inside a VF page with `renderAs="pdf"` is always wrong — the PDF renderer ignores it entirely.

---

## Anti-Pattern 3: Calling `getContentAsPDF()` Inside an Apex Trigger

**What the LLM generates:**
```apex
trigger QuoteTrigger on Quote (after update) {
    for (Quote q : Trigger.new) {
        if (q.Status == 'Approved') {
            PageReference pdfPage = Page.QuotePdf;
            pdfPage.getParameters().put('id', q.Id);
            Blob pdf = pdfPage.getContentAsPDF(); // WRONG — callout in trigger context
        }
    }
}
```

**Why it happens:** LLMs conflate "run when a record changes" with "put the logic in a trigger." The platform restriction that callouts cannot be made in a DML transaction (triggers always run inside one) is a Salesforce-specific constraint frequently missed.

**Correct pattern:**
```apex
trigger QuoteTrigger on Quote (after update) {
    for (Quote q : Trigger.new) {
        if (q.Status == 'Approved' && Trigger.oldMap.get(q.Id).Status != 'Approved') {
            System.enqueueJob(new QuotePdfAttachmentJob(q.Id)); // Defer to Queueable
        }
    }
}
```
The Queueable must implement `Database.AllowsCallouts`.

**Detection hint:** `getContentAsPDF()` appearing inside a trigger class body (file with `trigger` keyword) or inside a method called synchronously from a trigger.

---

## Anti-Pattern 4: Using Flexbox or CSS Grid for Layout in the PDF Page

**What the LLM generates:**
```css
.line-items-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.line-item-col {
    flex: 1;
}
```

**Why it happens:** Flexbox is the default modern layout primitive. LLMs trained on web development content use it automatically for multi-column layouts. Flying Saucer (CSS 2.1) silently ignores unsupported CSS properties, causing all columns to collapse into a single block with no visible error.

**Correct pattern:**
```css
/* Use CSS 2.1 table-based layout for reliable multi-column rendering in PDFs */
.line-items-container {
    display: table;
    width: 100%;
}
.line-item-col {
    display: table-cell;
    padding: 4pt;
    vertical-align: top;
}
```

**Detection hint:** `display: flex`, `display: grid`, `flex:`, `grid-template`, `align-items:`, or `justify-content:` in CSS associated with a VF PDF page.

---

## Anti-Pattern 5: Skipping the Null Check After `getContentAsPDF()`

**What the LLM generates:**
```apex
Blob pdf = pdfPage.getContentAsPDF();
// Immediately use the blob without a null check
ContentVersion cv = new ContentVersion(
    Title        = 'Quote.pdf',
    PathOnClient = 'Quote.pdf',
    VersionData  = pdf  // NullPointerException or 0-byte file if pdf is null
);
insert cv;
```

**Why it happens:** LLMs model `getContentAsPDF()` as analogous to other getter methods that either return a value or throw. The silent null-return-on-VF-error behavior is a non-standard API contract that is Salesforce-specific and poorly represented in training data.

**Correct pattern:**
```apex
Blob pdf = pdfPage.getContentAsPDF();
if (pdf == null) {
    System.debug(LoggingLevel.ERROR,
        'PDF generation returned null for Quote ' + quoteId
        + '. Check debug logs for errors in the QuotePdf VF page controller.');
    return; // or throw, or log a failure record
}
ContentVersion cv = new ContentVersion(
    Title        = 'Quote_' + quoteNumber + '.pdf',
    PathOnClient = 'Quote_' + quoteNumber + '.pdf',
    VersionData  = pdf
);
insert cv;
```

**Detection hint:** `getContentAsPDF()` assignment immediately followed by `ContentVersion` instantiation or `insert` with no intervening `if (... == null)` check.

---

## Anti-Pattern 6: Referencing Standard `QuoteLineItem` in a CPQ Quote PDF Controller

**What the LLM generates:**
```apex
// Querying standard QuoteLineItem for a CPQ org
List<QuoteLineItem> lines = [
    SELECT Product2.Name, Quantity, UnitPrice
    FROM QuoteLineItem
    WHERE QuoteId = :quoteId
    WITH USER_MODE
];
// Result: empty list — CPQ stores lines in SBQQ__QuoteLine__c, not QuoteLineItem
```

**Why it happens:** LLMs default to the standard `QuoteLineItem` object because it is well-documented in public Salesforce help. CPQ's managed package objects (`SBQQ__QuoteLine__c`) are less represented in training data, and the distinction between standard and CPQ quoting is frequently missed.

**Correct pattern:**
```apex
// For CPQ quotes, query the CPQ line object
List<SBQQ__QuoteLine__c> cpqLines = [
    SELECT SBQQ__ProductName__c, SBQQ__Quantity__c, SBQQ__NetPrice__c,
           SBQQ__ListPrice__c, SBQQ__Discount__c, SBQQ__Number__c
    FROM SBQQ__QuoteLine__c
    WHERE SBQQ__Quote__c = :quoteId
    WITH USER_MODE
    ORDER BY SBQQ__Number__c
];
```

**Detection hint:** A VF PDF page described as being for "CPQ quotes" that queries `FROM QuoteLineItem` instead of `FROM SBQQ__QuoteLine__c`.
