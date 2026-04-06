# LLM Anti-Patterns — Secure Coding Review Checklist

Common mistakes AI coding assistants make when generating or advising on Salesforce secure coding practices.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Omitting CRUD/FLS enforcement on SOQL queries

**What the LLM generates:** Bare SOQL queries without `WITH USER_MODE` or `Security.stripInaccessible()`:
```apex
List<Account> accts = [SELECT Id, Name FROM Account WHERE Industry = :ind];
```

**Why it happens:** Training data is dominated by Trailhead examples and blog posts that omit security enforcement for brevity. The LLM learns the simplified pattern as the default.

**Correct pattern:**
```apex
List<Account> accts = [SELECT Id, Name FROM Account WHERE Industry = :ind WITH USER_MODE];
```
Or for DML:
```apex
SObjectAccessDecision decision = Security.stripInaccessible(AccessType.READABLE, accts);
List<Account> sanitized = decision.getRecords();
```

**Detection hint:** SOQL query without `WITH USER_MODE` or `WITH SECURITY_ENFORCED` — regex: `\[SELECT.*FROM.*(?!WITH\s+(USER_MODE|SECURITY_ENFORCED))`

---

## Anti-Pattern 2: String concatenation in SOQL (injection vulnerability)

**What the LLM generates:** Dynamic SOQL built with string concatenation:
```apex
String query = 'SELECT Id FROM Account WHERE Name = \'' + userInput + '\'';
List<Account> results = Database.query(query);
```

**Why it happens:** The LLM pattern-matches from Java/SQL examples where parameterized queries use different syntax. Apex bind variables look different from JDBC PreparedStatement, so the model defaults to string concatenation.

**Correct pattern:**
```apex
String query = 'SELECT Id FROM Account WHERE Name = :userInput';
List<Account> results = Database.query(query);
```
Or use bind variables directly:
```apex
List<Account> results = [SELECT Id FROM Account WHERE Name = :userInput];
```

**Detection hint:** `Database.query(` combined with string concatenation (`+`) containing user-supplied variables — regex: `Database\.query\(.*\+`

---

## Anti-Pattern 3: Missing output encoding in Visualforce (XSS)

**What the LLM generates:** Unescaped merge fields in Visualforce or use of `escape="false"`:
```html
<apex:outputText value="{!userProvidedValue}" escape="false" />
```

**Why it happens:** LLMs generate code that "works" to display values, not code that is secure. The `escape="false"` pattern appears in training data for rendering rich HTML, and the model applies it broadly.

**Correct pattern:**
```html
<apex:outputText value="{!userProvidedValue}" />
```
Default escape is `true` — never set `escape="false"` on user-controlled data. For JavaScript contexts, use `JSENCODE()`:
```html
<script>var val = '{!JSENCODE(userProvidedValue)}';</script>
```

**Detection hint:** `escape="false"` or `escape='false'` in Visualforce pages — regex: `escape\s*=\s*["']false["']`

---

## Anti-Pattern 4: Sharing keyword omission on Apex classes

**What the LLM generates:** Classes without explicit sharing declaration:
```apex
public class AccountService {
    public List<Account> getAccounts() {
        return [SELECT Id, Name FROM Account];
    }
}
```

**Why it happens:** Java classes do not have a sharing keyword concept. LLMs trained on mixed Java/Apex data frequently omit `with sharing` because it has no Java analogue.

**Correct pattern:**
```apex
public with sharing class AccountService {
    public List<Account> getAccounts() {
        return [SELECT Id, Name FROM Account WITH USER_MODE];
    }
}
```
Use `with sharing` as the default. Only use `without sharing` with explicit justification (e.g., utility class that must see all records, wrapped in a `with sharing` caller).

**Detection hint:** Class declaration without sharing keyword — regex: `public\s+class\s+\w+` without preceding `with sharing` or `without sharing` or `inherited sharing`

---

## Anti-Pattern 5: Using PageReference with unvalidated external URLs (open redirect)

**What the LLM generates:** Redirects using user-supplied URL parameters:
```apex
PageReference redirect = new PageReference(ApexPages.currentPage().getParameters().get('retURL'));
return redirect;
```

**Why it happens:** LLMs generate functional redirect logic without considering that `retURL` could be an external malicious URL. The pattern is common in Visualforce controller training data.

**Correct pattern:**
```apex
String retURL = ApexPages.currentPage().getParameters().get('retURL');
if (retURL != null && retURL.startsWith('/')) {
    return new PageReference(retURL);
} else {
    return new PageReference('/home/home.jsp');
}
```
Always validate that redirect URLs are relative (start with `/`) and do not contain `://` to prevent open redirect attacks.

**Detection hint:** `new PageReference(` with parameter from `getParameters()` without URL validation — regex: `new\s+PageReference\(.*getParameters\(\)`

---

## Anti-Pattern 6: Hardcoding credentials or tokens in Apex

**What the LLM generates:** API keys or passwords embedded in source code:
```apex
Http h = new Http();
HttpRequest req = new HttpRequest();
req.setHeader('Authorization', 'Bearer sk-abc123secrettoken');
```

**Why it happens:** LLMs generate complete working examples and fill in placeholder values that look like real secrets. Training data includes blog posts with example tokens.

**Correct pattern:**
```apex
Http h = new Http();
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:My_Named_Credential/api/endpoint');
// Named Credential handles authentication automatically
```
Use Named Credentials for all external callout authentication. Never store secrets in code, Custom Labels, or Custom Settings (use Custom Metadata with protected visibility if Named Credentials are not feasible).

**Detection hint:** String literals matching token patterns in `setHeader` calls — regex: `setHeader\(.*['"]Authorization['"].*['"]Bearer\s+\w+`
