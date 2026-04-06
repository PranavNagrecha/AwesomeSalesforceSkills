# LLM Anti-Patterns — PDF Generation Patterns

Common mistakes AI coding assistants make when generating or advising on PDF generation in Salesforce.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using `{!$Resource.LogoName}` Directly in `<img src>`

**What the LLM generates:** `<img src="{!$Resource.CompanyLogo}" />` inside a VF PDF page.

**Why it happens:** This is the correct pattern for non-PDF Visualforce pages and the LLM correctly recalls it from training data — but the PDF renderer behavior is a rarely documented exception.

**Correct pattern:**

```apex
// In the Apex controller constructor:
logoUrl = URL.getSalesforceBaseUrl().toExternalForm() + '/resource/CompanyLogo';
```
```xml
<!-- In the VF page: -->
<img src="{!logoUrl}" />
```

**Detection hint:** Look for `{!$Resource.` inside an `<img src=` attribute on a page with `renderAs="pdf"`. Flag it as a broken image pattern.

---

## Anti-Pattern 2: Loading Data via JavaScript or Remote Actions in a PDF Page

**What the LLM generates:** A VF page with `renderAs="pdf"` that includes `<apex:remoteAction>`, `<script>` tags with `fetch()` calls, or `window.onload` callbacks to populate the page content dynamically.

**Why it happens:** LLMs trained on general VF patterns correctly know that remote actions work in browser-rendered VF pages. The PDF rendering engine's lack of JS support is a platform-specific constraint that is underrepresented in training data.

**Correct pattern:**

```apex
// Load data in the controller constructor — no JS callbacks needed
public InvoicePdfController() {
    Id recId = ApexPages.currentPage().getParameters().get('id');
    lineItems = [SELECT Id, Name, Quantity, TotalPrice
                 FROM OpportunityLineItem
                 WHERE OpportunityId = :recId
                 WITH USER_MODE];
}
```

**Detection hint:** Any `<script>` tag, `onclick`, `apex:remoteAction`, or JavaScript variable assignment inside a VF page that has `renderAs="pdf"` is an anti-pattern. Flag and remove.

---

## Anti-Pattern 3: Calling `getContentAsPDF()` Inside a Trigger

**What the LLM generates:** A trigger handler method that calls `pageRef.getContentAsPDF()` synchronously after updating a record.

**Why it happens:** The LLM correctly knows that `getContentAsPDF()` exists and should be called after the record is set up, but does not apply the callout-after-DML restriction consistently.

**Correct pattern:**

```apex
// Trigger handler — enqueue, don't call directly
if (opp.StageName == 'Closed Won' && oldOpp.StageName != 'Closed Won') {
    System.enqueueJob(new OpportunityPdfJob(opp.Id));
}

// Queueable — safe callout context
public class OpportunityPdfJob implements Queueable, Database.AllowsCallouts {
    public void execute(QueueableContext ctx) {
        Blob pdf = Page.MyPdfPage.getContentAsPDF(); // safe here
    }
}
```

**Detection hint:** Search for `getContentAsPDF()` in a trigger class or in a method called from a trigger without an intervening `System.enqueueJob` or `@future` boundary.

---

## Anti-Pattern 4: Skipping the Null Check on `getContentAsPDF()`

**What the LLM generates:** Code that calls `getContentAsPDF()` and immediately uses the result without a null check — e.g., `cv.VersionData = pageRef.getContentAsPDF();`.

**Why it happens:** Most API methods in Apex throw exceptions on failure; the silent null-return behavior of `getContentAsPDF()` is counter-intuitive and specific to this method.

**Correct pattern:**

```apex
Blob pdf = pageRef.getContentAsPDF();
if (pdf == null) {
    // Log the failure; the VF page threw an exception silently
    System.debug(LoggingLevel.ERROR, 'PDF generation returned null for Id: ' + recordId);
    return;
}
ContentVersion cv = new ContentVersion(
    VersionData  = pdf,
    Title        = 'Generated Report',
    PathOnClient = 'report.pdf'
);
insert cv;
```

**Detection hint:** Search for `.getContentAsPDF()` followed by immediate use without a `!= null` or `== null` guard. Flag any direct assignment to `VersionData` or `blob.size()` call without null checking.

---

## Anti-Pattern 5: Using CSS `display:none` to Hide Sensitive Content in a PDF

**What the LLM generates:** A VF PDF template where sections meant for certain users are hidden with `style="display:none"` or a CSS class that applies `display:none`.

**Why it happens:** CSS visibility toggling is idiomatic in web development. The LLM applies this pattern without considering that the hidden HTML is still present in the page source and visible to anyone who views the raw HTML (e.g., by accessing the VF page without `renderAs="pdf"`).

**Correct pattern:**

```xml
<!-- Server-side exclusion — the HTML is never emitted if rendered=false -->
<apex:outputPanel rendered="{!showConfidentialSection}">
    <p>Confidential financial data here.</p>
</apex:outputPanel>
```
```apex
// Controller
public Boolean showConfidentialSection {
    get { return UserInfo.getUserType() == 'Standard'; }
}
```

**Detection hint:** Search for `display:none` or `visibility:hidden` on elements that contain record data in a PDF page. Flag as a potential data exposure issue and replace with `rendered="{!condition}"`.

---

## Anti-Pattern 6: Suggesting LWC Can Render PDF Natively

**What the LLM generates:** Advice to add `renderAs="pdf"` to an LWC component, or to use a client-side JS library (jsPDF, html2canvas) as the primary Salesforce PDF generation solution.

**Why it happens:** LWC and Aura components share some conceptual space with Visualforce in training data. LLMs sometimes conflate them or assume modern component frameworks have equivalent PDF capabilities.

**Correct pattern:** LWC cannot render as PDF. The correct patterns are:
1. Navigate to a Visualforce page URL from the LWC (browser download).
2. Call an `@AuraEnabled` Apex method from the LWC that enqueues a Queueable to generate and store the PDF as a ContentVersion.

**Detection hint:** Any suggestion to use `renderAs="pdf"` on an LWC, or to use `jsPDF`, `html2canvas`, or `window.print()` as the production PDF generation mechanism in Salesforce.
