# Examples — PDF Generation Patterns

## Example 1: On-Demand Invoice PDF with Absolute Logo URL

**Context:** A professional services org needs an "Download Invoice PDF" button on the Opportunity record page. Clicking it opens a formatted PDF with the company logo, opportunity details, and a line-item table. No file storage is needed — just a browser download.

**Problem:** The initial implementation used `{!$Resource.CompanyLogo}` directly in an `<img src>` tag and loaded line-item data through an `<apex:remoteAction>` JavaScript call. The resulting PDF showed a broken image placeholder and an empty table — the logo URL was relative (unresolvable by Flying Saucer) and the JS remote action never executed.

**Solution:**

```apex
// InvoicePdfController.cls
public with sharing class InvoicePdfController {
    public Opportunity opp { get; private set; }
    public List<OpportunityLineItem> lineItems { get; private set; }
    public String logoUrl { get; private set; }

    public InvoicePdfController() {
        Id oppId = ApexPages.currentPage().getParameters().get('id');
        opp = [
            SELECT Id, Name, CloseDate, Amount, Account.Name, Owner.Name
            FROM Opportunity
            WHERE Id = :oppId
            WITH USER_MODE
            LIMIT 1
        ];
        lineItems = [
            SELECT Id, Quantity, UnitPrice, TotalPrice, PricebookEntry.Name
            FROM OpportunityLineItem
            WHERE OpportunityId = :oppId
            WITH USER_MODE
            ORDER BY CreatedDate ASC
        ];
        // Build absolute URL — relative $Resource path is unresolvable by the PDF renderer
        logoUrl = URL.getSalesforceBaseUrl().toExternalForm()
            + '/resource/CompanyLogo';
    }
}
```

```xml
<!-- InvoicePdf.page -->
<apex:page controller="InvoicePdfController"
           renderAs="pdf"
           showHeader="false"
           sidebar="false"
           contentType="application/pdf">
    <head>
        <style>
            body { font-family: Arial, sans-serif; font-size: 10pt; }
            table { width: 100%; border-collapse: collapse; }
            th, td { border: 1px solid #ccc; padding: 4px 8px; }
            th { background-color: #f5f5f5; }
            .header-logo { width: 120px; }
        </style>
    </head>
    <body>
        <img src="{!logoUrl}" class="header-logo" />
        <h2>Invoice: {!opp.Name}</h2>
        <p>Account: {!opp.Account.Name} | Close Date: {!opp.CloseDate}</p>
        <table>
            <tr><th>Product</th><th>Qty</th><th>Unit Price</th><th>Total</th></tr>
            <apex:repeat value="{!lineItems}" var="li">
                <tr>
                    <td>{!li.PricebookEntry.Name}</td>
                    <td>{!li.Quantity}</td>
                    <td>{!li.UnitPrice}</td>
                    <td>{!li.TotalPrice}</td>
                </tr>
            </apex:repeat>
        </table>
    </body>
</apex:page>
```

**Why it works:** All data (opportunity and line items) is loaded in the controller constructor before the page renders. The logo URL is an absolute HTTPS URL, which the Flying Saucer renderer can request directly. There are no `<script>` tags. CSS is inlined and uses only CSS 2.1 table properties supported by the engine.

---

## Example 2: Programmatic PDF Attachment via Queueable on Stage Change

**Context:** A financial services org requires that when an Opportunity reaches the "Closed Won" stage, a summary PDF is automatically generated and saved to the record's Files (ContentVersion) for audit purposes. The trigger fires on update.

**Problem:** The first implementation called `PageReference.getContentAsPDF()` directly inside the Apex trigger. This threw `System.CalloutException: Callout from triggers are currently not supported.` because a DML (the Opportunity update) had occurred before the callout in the same transaction.

**Solution:**

```apex
// OpportunityTriggerHandler.cls — called from trigger
public class OpportunityTriggerHandler {
    public static void afterUpdate(Map<Id, Opportunity> oldMap, List<Opportunity> newList) {
        List<Id> toGenerate = new List<Id>();
        for (Opportunity opp : newList) {
            if (opp.StageName == 'Closed Won'
                    && oldMap.get(opp.Id).StageName != 'Closed Won') {
                toGenerate.add(opp.Id);
            }
        }
        if (!toGenerate.isEmpty()) {
            System.enqueueJob(new OpportunityPdfJob(toGenerate[0]));
        }
    }
}

// OpportunityPdfJob.cls
public class OpportunityPdfJob implements Queueable, Database.AllowsCallouts {
    private Id oppId;
    public OpportunityPdfJob(Id oppId) { this.oppId = oppId; }

    public void execute(QueueableContext ctx) {
        PageReference pageRef = Page.OpportunityPdf;
        pageRef.getParameters().put('id', oppId);
        // Must be in a test context check for testability
        Blob pdfBlob = Test.isRunningTest()
            ? Blob.valueOf('test-pdf')
            : pageRef.getContentAsPDF();

        if (pdfBlob == null) {
            // Log the failure — VF page threw an error silently
            System.debug(LoggingLevel.ERROR,
                'PDF generation returned null for Opportunity: ' + oppId);
            return;
        }

        ContentVersion cv = new ContentVersion(
            Title       = 'Opportunity Summary',
            PathOnClient = 'OpportunitySummary_' + oppId + '.pdf',
            VersionData = pdfBlob,
            IsMajorVersion = true
        );
        insert cv;

        Id contentDocId = [
            SELECT ContentDocumentId FROM ContentVersion WHERE Id = :cv.Id LIMIT 1
        ].ContentDocumentId;

        ContentDocumentLink cdl = new ContentDocumentLink(
            ContentDocumentId = contentDocId,
            LinkedEntityId    = oppId,
            ShareType         = 'V',
            Visibility        = 'AllUsers'
        );
        insert cdl;
    }
}
```

**Why it works:** The Queueable implements `Database.AllowsCallouts`, which enables HTTP callouts in a fresh transaction separate from the DML that fired the trigger. The null check on `pdfBlob` prevents a NullPointerException when the VF page encounters an error. `ContentDocumentLink.ShareType = 'V'` grants view access on the linked record.

---

## Anti-Pattern: Using JavaScript to Load Data in a VF PDF Page

**What practitioners do:** They write a Visualforce page that uses `<apex:remoteAction>` or `window.onload` JavaScript to fetch data after the page loads, then populate table rows or chart elements dynamically.

**What goes wrong:** The Flying Saucer PDF renderer has no JavaScript engine. The page HTML is captured immediately after server-side rendering, before any client-side JS would execute. The result is an empty table or missing chart with no error — the PDF silently omits all JS-driven content.

**Correct approach:** Load all data in the Apex controller constructor and bind it directly to `<apex:repeat>`, `<apex:outputText>`, or standard HTML elements with EL expressions (`{!variable}`). There is no workaround for JS execution in VF PDF pages — the constraint is the Flying Saucer engine, not a configuration choice.
