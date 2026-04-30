# Examples — Visualforce to LWC Migration

## Example 1: Read-Only Account Summary VF Page → Wired LWC

**Context:** A VF page `AccountSummary.page` renders an Account record with computed KPIs (open opportunity total, last activity date, top contact). Used as a custom tab in Lightning Experience.

**Original Visualforce page:**

```xml
<apex:page controller="AccountSummaryController" tabStyle="Account">
    <apex:pageBlock title="Account Summary">
        <apex:outputText value="Account: {!account.Name}" />
        <apex:outputText value="Open Opp Total: {!totalOpenOpps}" />
        <apex:outputText value="Last Activity: {!lastActivityDate}" />
        <apex:outputText value="Top Contact: {!topContact.Name}" />
    </apex:pageBlock>
</apex:page>
```

**Original Apex controller:**

```apex
public with sharing class AccountSummaryController {
    public Account account { get; set; }
    public Decimal totalOpenOpps { get; set; }
    public Date lastActivityDate { get; set; }
    public Contact topContact { get; set; }

    public AccountSummaryController() {
        Id accountId = ApexPages.currentPage().getParameters().get('id');
        this.account = [SELECT Id, Name FROM Account WHERE Id = :accountId];
        // ...other queries fill in the rest
    }
}
```

**Migrated `@AuraEnabled` service:**

```apex
public with sharing class AccountSummaryService {
    public class Snapshot {
        @AuraEnabled public Account account;
        @AuraEnabled public Decimal totalOpenOpps;
        @AuraEnabled public Date lastActivityDate;
        @AuraEnabled public Contact topContact;
    }

    @AuraEnabled(cacheable=true)
    public static Snapshot getSnapshot(Id accountId) {
        Snapshot s = new Snapshot();
        s.account = [SELECT Id, Name FROM Account WHERE Id = :accountId WITH SECURITY_ENFORCED];
        s.totalOpenOpps = [SELECT SUM(Amount) total FROM Opportunity
                            WHERE AccountId = :accountId AND IsClosed = false WITH SECURITY_ENFORCED][0].get('total') == null
                            ? 0
                            : (Decimal) [SELECT SUM(Amount) total FROM Opportunity WHERE AccountId = :accountId AND IsClosed = false][0].get('total');
        // ...other queries with WITH SECURITY_ENFORCED
        return s;
    }
}
```

**Migrated LWC (`accountSummary.js`):**

```js
import { LightningElement, api, wire } from 'lwc';
import getSnapshot from '@salesforce/apex/AccountSummaryService.getSnapshot';

export default class AccountSummary extends LightningElement {
    @api recordId;
    @wire(getSnapshot, { accountId: '$recordId' }) snapshot;
}
```

**Migrated LWC template (`accountSummary.html`):**

```html
<template>
    <lightning-card title="Account Summary">
        <template if:true={snapshot.data}>
            <p>Account: {snapshot.data.account.Name}</p>
            <p>Open Opp Total: <lightning-formatted-number value={snapshot.data.totalOpenOpps} format-style="currency"></lightning-formatted-number></p>
            <p>Last Activity: <lightning-formatted-date-time value={snapshot.data.lastActivityDate}></lightning-formatted-date-time></p>
            <p>Top Contact: {snapshot.data.topContact.Name}</p>
        </template>
        <template if:true={snapshot.error}>
            <p class="slds-text-color_error">Failed to load summary.</p>
        </template>
    </lightning-card>
</template>
```

**Migrated `accountSummary.js-meta.xml`:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>62.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>lightning__RecordPage</target>
        <target>lightning__Tab</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="lightning__RecordPage">
            <objects>
                <object>Account</object>
            </objects>
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

**Why the wire:** `cacheable=true` + `@wire` means the same Account ID resolves from cache across components on the page. Imperative call would re-query every time.

---

## Example 2: VF Form (apex:inputField) → lightning-record-edit-form

**Context:** A VF page `EditCase.page` lets a user update a Case record with custom field-set selection.

**Original VF (excerpt):**

```xml
<apex:page standardController="Case" extensions="EditCaseController">
    <apex:form>
        <apex:pageBlock>
            <apex:pageBlockSection>
                <apex:inputField value="{!case.Subject}" />
                <apex:inputField value="{!case.Status}" />
                <apex:inputField value="{!case.Priority}" />
            </apex:pageBlockSection>
            <apex:commandButton value="Save" action="{!save}" />
        </apex:pageBlock>
    </apex:form>
</apex:page>
```

**Migrated LWC (`editCase.html`):**

```html
<template>
    <lightning-record-edit-form record-id={recordId} object-api-name="Case" onsuccess={handleSuccess} onerror={handleError}>
        <lightning-input-field field-name="Subject"></lightning-input-field>
        <lightning-input-field field-name="Status"></lightning-input-field>
        <lightning-input-field field-name="Priority"></lightning-input-field>
        <lightning-button type="submit" label="Save"></lightning-button>
    </lightning-record-edit-form>
</template>
```

**Migrated LWC (`editCase.js`):**

```js
import { LightningElement, api } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

export default class EditCase extends LightningElement {
    @api recordId;

    handleSuccess() {
        this.dispatchEvent(new ShowToastEvent({
            title: 'Saved',
            variant: 'success'
        }));
    }

    handleError(event) {
        this.dispatchEvent(new ShowToastEvent({
            title: 'Save failed',
            message: event.detail.message,
            variant: 'error'
        }));
    }
}
```

**What disappeared:** The `EditCaseController.save()` Apex method, the viewstate that held the in-progress field values, and the markup for every `apex:inputField`. `lightning-record-edit-form` honors validation rules, FLS, and lookup search automatically.

---

## Example 3: PDF VF Page Stays — LWC Triggers the Download

**Context:** A VF page `InvoicePdf.page` uses `renderAs="pdf"` to produce an invoice document. A new LWC needs to provide a "Download Invoice" button.

**VF page (retained, not migrated):**

```xml
<apex:page controller="InvoicePdfController" renderAs="pdf" applyHtmlTag="false">
    <html>
        <body>
            <h1>Invoice {!invoice.Name}</h1>
            <!-- invoice line items -->
        </body>
    </html>
</apex:page>
```

**Apex bridge for LWC:**

```apex
public with sharing class InvoicePdfService {
    @AuraEnabled
    public static String getInvoicePdfBase64(Id invoiceId) {
        PageReference pr = Page.InvoicePdf;
        pr.getParameters().put('id', invoiceId);
        Blob pdf = pr.getContentAsPDF();
        return EncodingUtil.base64Encode(pdf);
    }
}
```

**LWC trigger (`invoiceDownload.js`):**

```js
import { LightningElement, api } from 'lwc';
import getInvoicePdfBase64 from '@salesforce/apex/InvoicePdfService.getInvoicePdfBase64';

export default class InvoiceDownload extends LightningElement {
    @api recordId;

    async handleDownload() {
        const base64 = await getInvoicePdfBase64({ invoiceId: this.recordId });
        const link = document.createElement('a');
        link.href = `data:application/pdf;base64,${base64}`;
        link.download = `Invoice-${this.recordId}.pdf`;
        link.click();
    }
}
```

**Outcome:** The VF page survives because PDF rendering has no LWC equivalent. The LWC owns the user-facing surface; the VF page is now a backend service.

---

## Example 4: Lightning Out Wrapper for a Hardcoded Button URL

**Context:** A button on the Account page hardcodes a URL `/apex/RenewContract?id={!Account.Id}`. The button is referenced from an external email-marketing system that cannot be updated within the migration window.

**Lightning Out wrapper VF (`RenewContract.page`):**

```xml
<apex:page sidebar="false" showHeader="false" standardStylesheets="false">
    <apex:includeLightning />
    <div id="lwc-renew-contract" />
    <script>
        var accountId = "{!$CurrentPage.parameters.id}";
        $Lightning.use("c:renewContractLightningOutApp", function() {
            $Lightning.createComponent(
                "c:renewContract",
                { recordId: accountId },
                "lwc-renew-contract",
                function(cmp) { /* mounted */ }
            );
        });
    </script>
</apex:page>
```

**Lightning Out app (`renewContractLightningOutApp.app`):**

```xml
<aura:application access="GLOBAL" extends="ltng:outApp">
    <aura:dependency resource="c:renewContract" />
</aura:application>
```

**Outcome:** The button URL contract is preserved; the implementation under the hood is now an LWC. The wrapper VF and the Aura `outApp` should be tracked for removal once the upstream button caller is updated.

---

## Example 5: URL Parameter Translation

**Context:** A VF page `ProductSearch.page` reads `?category=hardware&inStock=true` from the URL.

**Original VF controller pattern:**

```apex
String category = ApexPages.currentPage().getParameters().get('category');
Boolean inStock = Boolean.valueOf(ApexPages.currentPage().getParameters().get('inStock'));
```

**Migrated LWC (`productSearch.js`):**

```js
import { LightningElement, wire } from 'lwc';
import { CurrentPageReference } from 'lightning/navigation';

export default class ProductSearch extends LightningElement {
    category;
    inStock;

    @wire(CurrentPageReference)
    setParams(pageRef) {
        if (pageRef && pageRef.state) {
            this.category = pageRef.state.c__category;
            this.inStock = pageRef.state.c__inStock === 'true';
        }
    }
}
```

**Critical:** the `c__` prefix on URL params for App Builder pages. External callers passing `?category=hardware` must be updated to `?c__category=hardware` — or the LWC must accept both during the transition.
