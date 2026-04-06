# LLM Anti-Patterns — Visualforce Fundamentals

Common mistakes AI coding assistants make when generating or advising on Visualforce pages and their Apex controllers. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: SOQL Inside a Loop Triggered by Page Rendering

**What the LLM generates:** A getter method that issues a SOQL query for each row rendered by `<apex:repeat>` or `<apex:pageBlockTable>`. The LLM writes a helper getter method (e.g., `getChildRecords(Id parentId)`) and calls it from the page markup for each parent row.

**Why it happens:** LLMs trained on general web patterns apply a "fetch on demand" mental model. In most web frameworks, lazy-loading child data per row is a valid optimization. In Salesforce, each getter call that issues SOQL counts against the 100 SOQL per-transaction governor limit, which is shared across the entire page render.

**Correct pattern:**

```apex
// WRONG — one query per row
public List<Contact> getContactsFor(Id accountId) {
    return [SELECT Id, Name FROM Contact WHERE AccountId = :accountId WITH USER_MODE];
}

// CORRECT — bulk load in constructor, map lookup at render time
public transient Map<Id, List<Contact>> contactsByAccount { get; private set; }

public MyController() {
    List<Id> accountIds = new List<Id>();
    for (Account a : accounts) { accountIds.add(a.Id); }
    contactsByAccount = new Map<Id, List<Contact>>();
    for (Contact c : [
        SELECT Id, Name, AccountId FROM Contact
        WHERE AccountId IN :accountIds WITH USER_MODE
    ]) {
        if (!contactsByAccount.containsKey(c.AccountId))
            contactsByAccount.put(c.AccountId, new List<Contact>());
        contactsByAccount.get(c.AccountId).add(c);
    }
}
```

**Detection hint:** Look for SOQL keywords (`SELECT`, `[SELECT`, `Database.query`) inside methods whose names start with `get` and accept an `Id` parameter, especially when the page markup calls them with `{!getXxx(record.Id)}`.

---

## Anti-Pattern 2: Assuming Standard Controller FLS Applies to Extension Getter Methods

**What the LLM generates:** A standard controller + extension combination where the extension fetches additional fields in a custom getter without `WITH USER_MODE`. The LLM reasons that "the page uses a standard controller so FLS is enforced."

**Why it happens:** The LLM correctly knows that standard controller bound fields (`{!account.Name}`) enforce FLS. It incorrectly extends that behavior to all Apex code in the same page context. FLS enforcement in standard controllers is scoped to the controller's own data binding — it does not extend to Apex methods in extensions.

**Correct pattern:**

```apex
// WRONG — assumes standard controller FLS covers extension queries
public with sharing class AccountExtension {
    public List<Contact> contacts { get; set; }
    public AccountExtension(ApexPages.StandardController sc) {
        contacts = [SELECT Id, Name, Email FROM Contact WHERE AccountId = :sc.getId()];
        // Email returned even if running user lacks FLS access to Contact.Email
    }
}

// CORRECT — explicit USER_MODE in extension SOQL
public AccountExtension(ApexPages.StandardController sc) {
    contacts = [
        SELECT Id, Name, Email FROM Contact
        WHERE AccountId = :sc.getId()
        WITH USER_MODE  // platform enforces FLS for running user
    ];
}
```

**Detection hint:** Search for `[SELECT` in extension classes that do NOT include `WITH USER_MODE` or `WITH SECURITY_ENFORCED`. Any such query bypasses FLS regardless of the controller type used in the page.

---

## Anti-Pattern 3: Using JavaScript for PDF Layout in `renderAs="pdf"` Pages

**What the LLM generates:** A Visualforce page with `renderAs="pdf"` that includes `<script>` tags, dynamic JS-driven content (e.g., Chart.js, jQuery manipulation), or external CSS loaded from CDN URLs.

**Why it happens:** The LLM treats `renderAs="pdf"` as a browser print-to-PDF instruction and assumes the JavaScript execution pipeline is the same as a normal page view. In reality, Salesforce uses the Flying Saucer library server-side — JS is never executed, and external CDN resources are often unreachable or ignored.

**Correct pattern:**

```xml
<!-- WRONG — JS and CDN CSS will not work in PDF -->
<apex:page renderAs="pdf">
    <apex:includeScript value="https://cdn.jsdelivr.net/npm/chart.js" />
    <apex:stylesheet value="https://cdn.example.com/styles.css" />
    <script>document.getElementById('chart').innerHTML = '...';</script>
</apex:page>

<!-- CORRECT — inline CSS, server-side data, no JS -->
<apex:page renderAs="pdf" applyHtmlTag="false" showHeader="false">
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; }
        table { border-collapse: collapse; width: 100%; }
    </style>
</head>
<body>
    <apex:repeat value="{!lineItems}" var="li">
        <p>{!li.Product2.Name}: {!li.TotalPrice}</p>
    </apex:repeat>
</body>
</html>
</apex:page>
```

**Detection hint:** Any `<script>` tag or external `<apex:stylesheet>` referencing an http/https URL inside a page with `renderAs="pdf"` is a bug waiting to produce a blank PDF.

---

## Anti-Pattern 4: Non-Transient Display Collections Bloating View State

**What the LLM generates:** A controller with `public List<Account> accounts { get; set; }` populated in the constructor, without marking it `transient`. The LLM treats it as a normal property with no serialization concern.

**Why it happens:** LLMs are familiar with server-side MVC frameworks where model properties passed to views are not serialized into the HTTP response. In Visualforce, every non-transient, non-static instance variable is serialized into `__VIEWSTATE` on every postback. A 200-record list can easily consume 40–80 KB, pushing complex pages over the 170 KB hard limit.

**Correct pattern:**

```apex
// WRONG — 200 accounts serialized on every postback
public List<Account> accounts { get; set; }

public MyController() {
    accounts = [SELECT Id, Name, Industry FROM Account WITH USER_MODE LIMIT 200];
}

// CORRECT — transient; rebuilt from DB on each render, zero view state cost
public transient List<Account> accounts { get; set; }

public List<Account> getAccounts() {
    if (accounts == null) {
        accounts = [SELECT Id, Name, Industry FROM Account WITH USER_MODE LIMIT 200];
    }
    return accounts;
}
```

**Detection hint:** Any controller property declared as `List<SObject>`, `Map<...>`, or other large collection without the `transient` keyword is a candidate for view state bloat. Check whether the property value is ever submitted back to the server — if not, it must be `transient`.

---

## Anti-Pattern 5: DML in a Method Called via Page `action` Attribute

**What the LLM generates:** An initialization method attached to `<apex:page action="{!initialize}">` that performs DML (insert, update, or delete) to set up data for the page.

**Why it happens:** The LLM models the `action` attribute as a constructor callback or an initialization hook that fires once. It does not account for the fact that this method fires on every GET request to the page URL, including refreshes, back-button navigation, and direct URL access — and that this is exploitable as a CSRF vector (anyone who can craft a URL can trigger the DML).

**Correct pattern:**

```apex
// WRONG — DML fires on every page load, including URL-crafted CSRF attacks
public PageReference initialize() {
    insert new Task(Subject = 'Created by page load', WhoId = userId);
    return null;
}
// VF page: <apex:page action="{!initialize}">

// CORRECT — page action only fetches data; DML only in response to explicit POST
public PageReference loadPageData() {
    // read-only: safe to fire on GET
    account = [SELECT Id, Name FROM Account WHERE Id = :recordId WITH USER_MODE LIMIT 1];
    return null;
}

public PageReference createTask() {
    // DML only fires when user clicks a <apex:commandButton> inside <apex:form>
    insert new Task(Subject = 'User-initiated', WhoId = userId);
    return null;
}
```

**Detection hint:** Search for `insert`, `update`, `delete`, `upsert`, `merge`, or `Database.insert/update/delete` inside any method that is referenced by `<apex:page action="{!...}">` in the markup. Any match is a potential CSRF and unintended-side-effect risk.

---

## Anti-Pattern 6: Using Classic JavaScript Navigation in Lightning Experience

**What the LLM generates:** `window.location = '/' + recordId;` or `window.top.location.href = url;` for in-page navigation on a Visualforce page intended to run inside Lightning Experience.

**Why it happens:** This pattern works correctly in Salesforce Classic. The LLM generates it because it appears frequently in training data for Visualforce pages. In LEX, VF pages load in a cross-origin iframe; `window.top` access is blocked by the browser same-origin policy.

**Correct pattern:**

```javascript
// WRONG — throws SecurityError in LEX iframe
window.top.location.href = '/' + recordId;
window.parent.location = sfdcBaseUrl + recordId;

// CORRECT — use sforce.one API for LEX-safe navigation
sforce.one.navigateToSObject(recordId);
sforce.one.navigateToURL('/apex/MyPage?id=' + recordId);
sforce.one.back(true); // go back and refresh
```

**Detection hint:** Search VF page `<script>` blocks and `<apex:includeScript>` references for `window.top`, `window.parent`, `window.location =`, or `parent.document`. Any of these require replacement with `sforce.one.*` calls for LEX compatibility.
