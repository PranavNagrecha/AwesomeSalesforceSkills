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

**Detection hint:** SOQL query without `WITH USER_MODE` — regex: `\[SELECT.*FROM.*(?!WITH\s+USER_MODE)` — then read the sibling `*-meta.xml` before scoring it. Below API 67.0 a bare query is unenforced and the finding stands; at 67.0+ the query already runs in user mode by default, so the finding drops to an advisory about stating intent. That applies to `.trigger` files as well as `.cls` — a trigger body's database operations run in user mode unless system mode is explicitly specified, so read `.trigger-meta.xml` and score a bare trigger query on the same version gate. Do not flag `WITH USER_MODE` inside a trigger as a defect; it is the documented pattern, and in a trigger it also overrides the implicit `without sharing` baseline, so record sharing is enforced on that operation too. The trigger-specific finding to look for is the reverse: a `WITH SYSTEM_MODE` / `as system` in a trigger body reverts to that baseline and returns all records regardless of the running user. Never score `WITH SECURITY_ENFORCED` as clean: it is the weaker construct below 67.0 and does not compile at 67.0+.

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

The severity of the omission is version-gated: a bare class runs `without sharing` at API 66.0 and below (a real exposure) but `with sharing` at 67.0+ (implicit, not absent). Two mistakes follow. Stating "a class with no keyword runs without sharing" unqualified is wrong for 67.0+ code; carrying the *sharing* half of the rule over to **triggers** is wrong at every version — a trigger cannot declare a sharing keyword and always runs implicitly `without sharing`, so there is no keyword to add and no version that changes it. Do not carry that conclusion across to the access mode, and do not conclude that a trigger body therefore enforces nothing: database operations in a trigger body run in **user mode** unless system mode is explicitly specified, gated on the trigger's own `.trigger-meta.xml` `<apiVersion>`, and user mode overrides the implicit `without sharing` baseline — enforcing object permissions, FLS, *and* the running user's sharing rules. It is the explicit `WITH SYSTEM_MODE` in a trigger that ignores object- and field-level permissions and reverts record access to that `without sharing` baseline, making all records visible. See [`AGENT_CONTRACT.md` § Apex security idiom by API version](../../../../agents/_shared/AGENT_CONTRACT.md#apex-security-idiom-by-api-version).

**Detection hint:** Class declaration without sharing keyword — regex: `public\s+class\s+\w+` without preceding `with sharing` or `without sharing` or `inherited sharing`. Resolve `<apiVersion>` from the sibling `.cls-meta.xml` before assigning severity, and skip `.trigger` files *for this check only* — they have no sharing keyword to check. Do not skip them for the access-mode check: resolve the sibling `.trigger-meta.xml` `<apiVersion>` and audit the trigger body's queries and DML like any other code.

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

---

## Anti-Pattern 7: Asserting That Bind Variables Do Not Work in Dynamic SOQL

**What the LLM generates:** A review rule or decision table row reading "Dynamic SOQL via `Database.query()` → use `String.escapeSingleQuotes()`; bind variables are unavailable in dynamic strings." Variants: "you can only bind in inline `[SELECT ...]` queries," "escapeSingleQuotes is the standard defence for `Database.query`," "parameterisation isn't possible once the query is a String."

**Why it happens:** Two reinforcing sources. (1) In most languages a query assembled as a string genuinely *is* unparameterised, so the model transfers the JDBC intuition. (2) Salesforce's own pre-2015 secure-coding material leaned heavily on `escapeSingleQuotes()`, and that vintage advice is over-represented in training data relative to the `queryWithBinds` documentation from Spring '23.

**Why this one is dangerous:** it fails in the *exposure* direction and it is stated by a security artefact. A reviewer who accepts it will pass code that escapes quotes and still splices attacker-controlled text into `LIMIT`, `ORDER BY`, a field name, or an unquoted numeric comparison — none of which `escapeSingleQuotes()` touches. The reviewer will also *reject* correctly-bound code as non-conforming.

**Correct pattern:**
```apex
// In-scope binding — works in Database.query(), available long before v57
String userInput = req.name;
List<Account> a = Database.query('SELECT Id FROM Account WHERE Name = :userInput');

// Map-based binding — Spring '23 / API v57 onward, no scoping constraint
Map<String, Object> binds = new Map<String, Object>{ 'nm' => req.name };
List<Account> b = Database.queryWithBinds(
    'SELECT Id FROM Account WHERE Name = :nm',
    binds,
    AccessLevel.USER_MODE
);
```
A bind variable substitutes a **literal value** only. If the user supplies a field name, object name, sort direction or `LIMIT`, no bind can help — allowlist that token against `Schema.getGlobalDescribe()` or a hardcoded set. `String.escapeSingleQuotes()` remains a defence-in-depth fallback, never the primary control.

**Detection hint:** flag any document where `escapeSingleQuotes` appears without `queryWithBinds` or `:` binding also appearing; flag the literal phrases `bind variables unavailable`, `bind variables are not supported in dynamic`, `cannot bind in Database.query`. In code, `Database.query(` whose argument contains `escapeSingleQuotes(` **and** no `:` token is the executable form.

---

## Anti-Pattern 8: Misdating `WITH USER_MODE` to Spring '20

**What the LLM generates:** "In Spring '20+, the platform introduced `WITH USER_MODE` for SOQL and `Security.stripInaccessible()` for DML results." Also seen as "`queryWithBinds` is unavailable pre-Spring '21."

**Why it happens:** `Security.stripInaccessible()` really did go GA in Spring '20, and the model attaches the nearest remembered release date to the whole cluster of CRUD/FLS features it recalls together. Release-version claims are unusually prone to this because the model has a plausible date in context and no signal that it belongs to a sibling feature.

**Correct pattern:**
```
Security.stripInaccessible()                  GA Spring '20  (API v48)
WITH SECURITY_ENFORCED                        earlier still
WITH USER_MODE / WITH SYSTEM_MODE             Spring '23     (API v57)
AccessLevel on Database.* methods             Spring '23     (API v57)
Database.queryWithBinds / getQueryLocatorWithBinds
  / countQueryWithBinds                       Spring '23     (API v57)
User mode as the DEFAULT access mode, and
  `with sharing` as the default for a bare
  class; WITH SECURITY_ENFORCED removed       Summer '26     (API v67)
```
Below v57, use in-scope `:var` binding plus `WITH SECURITY_ENFORCED` and `stripInaccessible()`.

**Detection hint:** any sentence pairing `USER_MODE` with a release earlier than Spring '23 or an API version below 57 is wrong. Mechanically: in a class's `*.cls-meta.xml`, `<apiVersion>` below `57.0` in a class body containing `USER_MODE`, `SYSTEM_MODE`, `queryWithBinds` or `AccessLevel.` will not compile — that pairing is a hard, checkable contradiction.
