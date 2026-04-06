# Examples — Visualforce Fundamentals

## Example 1: Custom Controller with FLS Enforcement and Transient List

**Context:** A Visualforce page displays a list of related Contacts for an Account and allows the user to update the Account's phone number. The page is accessible to internal users with varying field-level permissions.

**Problem:** A naive implementation queries all Contact fields without FLS checks, serializes the entire Contact list into view state, and allows the save action via a bookmarkable GET URL — exposing data and CSRF risk simultaneously.

**Solution:**

```apex
// AccountContactController.cls
public with sharing class AccountContactController {

    public Account acct { get; set; }

    // transient: rebuilt on each render, never serialized into view state
    public transient List<Contact> contacts { get; set; }

    public AccountContactController() {
        Id recordId = ApexPages.currentPage().getParameters().get('id');
        // WITH USER_MODE enforces FLS and CRUD for the running user automatically
        acct = [
            SELECT Id, Name, Phone
            FROM Account
            WHERE Id = :recordId
            WITH USER_MODE
            LIMIT 1
        ];
    }

    // Getter rebuilds the list on each render — zero view state cost
    public List<Contact> getContacts() {
        if (contacts == null) {
            contacts = [
                SELECT Id, FirstName, LastName, Email
                FROM Contact
                WHERE AccountId = :acct.Id
                WITH USER_MODE
                ORDER BY LastName
            ];
        }
        return contacts;
    }

    // POST-only action — safe against CSRF because only fired from <apex:commandButton>
    public PageReference save() {
        try {
            update acct; // runs in with sharing context; USER_MODE also covers DML
        } catch (DmlException e) {
            ApexPages.addMessages(e);
            return null; // stay on page, show error
        }
        return new PageReference('/' + acct.Id);
    }
}
```

```xml
<!-- AccountContacts.page -->
<apex:page controller="AccountContactController" showHeader="true" sidebar="false">
    <apex:form>
        <apex:pageMessages />
        <apex:pageBlock title="Account: {!acct.Name}">
            <apex:pageBlockSection>
                <apex:inputField value="{!acct.Phone}" />
            </apex:pageBlockSection>
            <apex:pageBlockButtons>
                <!-- commandButton fires a POST — CSRF-safe -->
                <apex:commandButton value="Save" action="{!save}" />
            </apex:pageBlockButtons>
        </apex:pageBlock>

        <apex:pageBlock title="Contacts">
            <apex:pageBlockTable value="{!contacts}" var="c">
                <apex:column value="{!c.FirstName}" />
                <apex:column value="{!c.LastName}" />
                <apex:column value="{!c.Email}" />
            </apex:pageBlockTable>
        </apex:pageBlock>
    </apex:form>
</apex:page>
```

**Why it works:** `WITH USER_MODE` on both queries delegates FLS and CRUD enforcement to the platform, so a user without read access to `Contact.Email` will not see that field. The `transient` keyword on the contacts list prevents it from being serialized into view state, which reduces view state size from potentially 50+ KB to near zero for that collection. The save action only fires via `<apex:commandButton>` inside `<apex:form>`, ensuring Salesforce's built-in `_formkey` CSRF token is validated on every submit.

---

## Example 2: PDF Generation from a Visualforce Page

**Context:** A business requires a formatted invoice PDF generated from an Opportunity record, with line items from OpportunityLineItem, downloadable by the account owner.

**Problem:** Developers attempt to use a JavaScript PDF library inside a VF page, which produces a blank PDF because the PDF renderer does not execute JavaScript. CSS classes loaded from external CDN URLs also fail to load in the rendering environment.

**Solution:**

```apex
// InvoicePdfController.cls
public with sharing class InvoicePdfController {

    public Opportunity opp { get; private set; }
    public List<OpportunityLineItem> lineItems { get; private set; }

    public InvoicePdfController() {
        Id oppId = ApexPages.currentPage().getParameters().get('id');
        opp = [
            SELECT Id, Name, CloseDate, Account.Name, Amount, Owner.Name
            FROM Opportunity
            WHERE Id = :oppId
            WITH USER_MODE
            LIMIT 1
        ];
        lineItems = [
            SELECT Id, Product2.Name, Quantity, UnitPrice, TotalPrice, Description
            FROM OpportunityLineItem
            WHERE OpportunityId = :oppId
            WITH USER_MODE
            ORDER BY Product2.Name
        ];
    }
}
```

```xml
<!-- InvoicePdf.page -->
<!-- renderAs="pdf" triggers Flying Saucer HTML-to-PDF conversion server-side -->
<apex:page controller="InvoicePdfController"
           renderAs="pdf"
           applyHtmlTag="false"
           showHeader="false"
           sidebar="false">
<html>
<head>
    <!-- Inline CSS only — external CDN stylesheets will not load in PDF renderer -->
    <style>
        body { font-family: Arial, sans-serif; font-size: 12px; }
        h1   { font-size: 18px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ccc; padding: 6px; text-align: left; }
        th { background-color: #f0f0f0; }
    </style>
</head>
<body>
    <h1>Invoice: {!opp.Name}</h1>
    <p>Account: {!opp.Account.Name} | Close Date: {!opp.CloseDate}</p>
    <p>Account Owner: {!opp.Owner.Name}</p>

    <table>
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
            <tr>
                <td>{!li.Product2.Name}</td>
                <td>{!li.Quantity}</td>
                <td>{!li.UnitPrice}</td>
                <td>{!li.TotalPrice}</td>
            </tr>
            </apex:repeat>
        </tbody>
    </table>

    <p><strong>Total: {!opp.Amount}</strong></p>
</body>
</html>
</apex:page>
```

**Why it works:** `renderAs="pdf"` instructs Salesforce to pass the rendered HTML output to the Flying Saucer PDF engine server-side — no JavaScript is involved in the rendering pipeline. All CSS is inline in a `<style>` block, which the renderer processes reliably. The controller uses `WITH USER_MODE` so the PDF is only generated with data the running user is permitted to see.

---

## Anti-Pattern: SOQL Inside a Rendered-Attribute Loop

**What practitioners do:** Place a SOQL query inside a getter that is invoked once per rendered component — typically inside an `<apex:repeat>` or `<apex:pageBlockTable>` iteration — to fetch child records for each row.

**What goes wrong:** Each row iteration calls the getter, which issues a new SOQL query. A table with 100 rows fires 100 SOQL queries, immediately hitting the 100 SOQL per transaction governor limit and producing a `System.LimitException: Too many SOQL queries: 101` error.

**Correct approach:** Query all child records in a single bulk query keyed by parent ID, store them in a `Map<Id, List<ChildObject>>` in the constructor or lazy-loaded getter, and reference the map in the page markup. The total SOQL count stays at 1 regardless of row count.

```apex
// WRONG — fires one query per row
public List<Contact> getContactsForAccount(Id accountId) {
    return [SELECT Id, Name FROM Contact WHERE AccountId = :accountId];
}

// CORRECT — one query, map lookup in page
public transient Map<Id, List<Contact>> contactsByAccount { get; private set; }

private void loadContactMap(List<Id> accountIds) {
    contactsByAccount = new Map<Id, List<Contact>>();
    for (Contact c : [
        SELECT Id, Name, AccountId FROM Contact
        WHERE AccountId IN :accountIds
        WITH USER_MODE
    ]) {
        if (!contactsByAccount.containsKey(c.AccountId)) {
            contactsByAccount.put(c.AccountId, new List<Contact>());
        }
        contactsByAccount.get(c.AccountId).add(c);
    }
}
```
