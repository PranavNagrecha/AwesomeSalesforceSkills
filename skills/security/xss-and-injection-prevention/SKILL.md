---
name: xss-and-injection-prevention
description: "Use when writing or reviewing Visualforce pages, Apex controllers, or LWC components that output user-supplied data, build dynamic queries, or construct HTTP responses. Triggers: 'XSS in Visualforce', 'SOQL injection vulnerability'. NOT for Apex CRUD/FLS enforcement, Shield encryption, or AppExchange security review — use apex/soql-security."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
triggers:
  - "my Visualforce page renders user input directly and I am worried about XSS"
  - "how do I prevent SOQL injection in dynamic SOQL queries"
  - "should I use HTMLENCODE or JSENCODE in a Visualforce JavaScript block"
  - "how do I prevent open redirect vulnerabilities in Apex PageReference"
  - "LWC component displays data from an Apex method and I need to sanitize it"
  - "Checkmarx flagged a stored XSS finding in my Apex controller"
tags:
  - xss
  - injection-prevention
  - visualforce
  - apex-security
  - soql-injection
  - output-encoding
inputs:
  - "Visualforce page markup or Apex controller code under review"
  - "Description of how user-controlled data flows through the component"
  - "Whether the output context is HTML, JavaScript, or a URL"
outputs:
  - "Identified encoding gaps and the correct encoding function for each context"
  - "Corrected code using bind variables for SOQL and encoding functions for output"
  - "Open redirect fix using PageReference domain whitelisting"
dependencies: []
version: 1.0.2
author: Pranav Nagrecha
updated: 2026-10-20
---

# XSS and Injection Prevention

Use this skill when writing or reviewing Visualforce pages, Apex controllers, or LWC components that render user-supplied data, build dynamic queries, or construct redirect URLs. It covers the full set of Salesforce-specific encoding functions, the SOQL injection bind-variable pattern, CRLF injection prevention, and open redirect mitigation.

---

## Before Starting

Gather this context before working on anything in this domain:

- Identify how user input enters the system: URL parameters, form fields, Apex method parameters from external callers, or data stored in sObject fields.
- Identify the output context for each user input: HTML body, JavaScript block, URL parameter, HTTP response header. Each context requires a different encoding function.
- Determine whether any dynamic SOQL or dynamic SOSL constructs exist in the Apex code. These are the injection surface, not static queries with bind variables.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Where does each user-controlled value render — inside a standard `<apex:*>` component, as a bare `{!expr}` outside one, inside `<script>`, in an event-handler attribute, or in a URL? | Each context needs a different function, and bare expressions are not escaped (Gotcha 1, Core Concepts table). | The encoding function per output point. |
| Does any component set `escape="false"`? | That output is unfiltered and must be wrapped in `HTMLENCODE` (Core Concepts). | The list of tags to encode or to switch back to default escaping. |
| Is any SOQL built from user input at run time, and can it become a static query with a bind variable? | The guide's first defense is to avoid dynamic SOQL (SOQL Injection via String Concatenation). | Which queries become static, which keep binds, which need `escapeSingleQuotes`. |
| Is any SOSL built with `Search.query` or `Search.find` from a search box? | SOSL is a parallel injection surface (Gotcha 2). | The search terms to escape and the input rules to validate. |
| Does any LWC or Aura component set `innerHTML` or render rich text from Apex data? | Locker / Lightning Web Security isolation is not output encoding (Gotcha 3). | The components to move to template bindings or a sanitiser. |
| Does any Apex REST resource copy request data into response headers? | Header values built from input are an injection surface (Gotcha 4). | The `RestResponse.headers` / `addHeader` calls to validate. |
| Does any `PageReference` or redirect take its target from a URL parameter? | An unvalidated target is an open redirect (Whitelist PageReference Targets pattern). | The allowlist of internal paths and the fallback page. |

A proper configuration adds a per-output-point record of context and encoding, so a reviewer can confirm every finding is closed instead of re-reading the page.

---

## Core Concepts

### Output Context Determines Encoding Function

Salesforce provides four Visualforce encoding functions. Applying the wrong one is as bad as applying none:

| Output Context | Correct Function | Notes |
|---|---|---|
| HTML body | `HTMLENCODE()` | Standard `<apex:*>` components escape by default; a bare `{!expr}` outside a component, or any `escape="false"` output, is not escaped and needs it |
| JavaScript string in VF script block | `JSENCODE()` | `{!field}` inside `<script>` is NOT auto-encoded — #1 XSS vector |
| HTML attribute with JavaScript | `JSINHTMLENCODE()` | `HTMLENCODE` first, then `JSENCODE` — for inline event handlers like `onclick` |
| URL parameter | `URLENCODE()` | Use when constructing URLs with user data |

The four functions and their order are the guide's: `JSINHTMLENCODE(x)` "is equivalent to JSENCODE(HTMLENCODE((x)))" — HTML-encode first, then JS-encode (apexdev 264 L13504-13516). The critical rule: escaping comes from the components, not from the expression language. "All standard Visualforce components, which start with <apex>, have anti-XSS filters" and "nearly all Visualforce tags escape" by default (apexdev 264 L13439, L13449), but with `escape="false"` or "when including formulas outside of a Visualforce component, output is unfiltered" and "the output that's generated by expressions isn't escaped during rendering" (L13480-13483). A `{!field}` in a `<script>` block is such a formula, so every JavaScript variable assignment from a VF expression must use `JSENCODE()` — the guide's own fix is `var ret = "{!JSENCODE($CurrentPage.parameters.retURL)}";` (L13543).

### SOQL Injection via String Concatenation

Dynamic SOQL built by string concatenation with user input is injectable. The attacker can escape the intended query structure and append arbitrary conditions.

**Vulnerable pattern:**
```apex
String query = 'SELECT Id FROM Account WHERE Name = \'' + userInput + '\'';
List<Account> results = Database.query(query);
```

**Safe pattern using bind variables:**
```apex
String query = 'SELECT Id FROM Account WHERE Name = :userInput';
List<Account> results = Database.query(query);
```

The guide ranks the defenses: "avoid using dynamic SOQL queries. Instead, use static queries and binding variables" (apexdev 264 L13661-13662); dynamic SOQL also accepts bind variables (`Database.query('... = :resolvedField1', AccessLevel.USER_MODE)`, L11644-11645) and, at API 57.0+, `Database.queryWithBinds` with a Map (L11647-11648). "If you must use dynamic SOQL, use the escapeSingleQuotes method" (L13677) — the guide presents it as the dynamic-SOQL and SOSL defense (L11679, L11763), and the reference entry says it "help[s] prevent SOQL injection" by escaping single quotation marks and backslashes (apexref 262 L235380, L235397). Escaping quotes does nothing for input placed outside a quoted literal (a field name, an `ORDER BY` column, a number), so those parts must come from an allowlist.

### LWC and Locker Service / Lightning Web Security

LWC runs inside Lightning Locker or Lightning Web Security depending on the org configuration — `SessionSettings.lockerServiceNext` true means Lightning Web Security protects LWC (api_meta 264 L129927-129930). These sandbox the DOM and prevent cross-component script access. However, they do not prevent stored XSS in data coming from Apex. If an Apex controller returns maliciously crafted HTML from a user-supplied field and the LWC renders it with `innerHTML`, the attack succeeds. Safe LWC patterns use template bindings `{field}` which are auto-escaped by the framework. UNVERIFIED (2026-10-20): the isolation scope of Locker / LWS, the `innerHTML` bypass and LWC template auto-escaping are LWC Developer Guide material with no corpus line.

---

## Common Patterns

### Encode All JavaScript Variable Assignments in Visualforce

**When to use:** Any Visualforce page that assigns Apex controller data into a JavaScript variable.

**How it works:**
```html
<!-- VULNERABLE: raw expression in script block -->
<script>
    var accountName = '{!account.Name}';
</script>

<!-- SAFE: JSENCODE applied -->
<script>
    var accountName = '{!JSENCODE(account.Name)}';
</script>
```

**Why not rely on auto-escape:** Escaping is a property of the `<apex:*>` components; an expression inside `<script>` is outside any component and is not escaped (apexdev 264 L13480-13483). JavaScript rendering receives the raw string.

### Always Use Bind Variables in Dynamic SOQL

**When to use:** Any Apex code that builds a SOQL string dynamically with user-supplied data.

**How it works:**
```apex
// SAFE: bind variable
public List<Contact> searchContacts(String lastName) {
    return Database.query(
        'SELECT Id, Name FROM Contact WHERE LastName = :lastName'
    );
}
```

### Whitelist PageReference Targets to Prevent Open Redirect

**When to use:** Any Apex controller that constructs a `PageReference` using URL parameters or user input.

**How it works:**
```apex
private static final Set<String> ALLOWED_PATHS = new Set<String>{
    '/home/home.jsp',
    '/lightning/page/home'
};

public PageReference redirect() {
    String retUrl = ApexPages.currentPage().getParameters().get('retUrl');
    if (retUrl != null && ALLOWED_PATHS.contains(retUrl)) {
        return new PageReference(retUrl);
    }
    return Page.DefaultLanding; // safe fallback
}
```

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| VF value inside a standard `<apex:*>` tag (default `escape`) | Component escaping sufficient | Standard components filter XSS characters |
| Bare `{!field}` outside a component, or `escape="false"` | `{!HTMLENCODE(field)}` | Expression output is not escaped |
| VF variable in `<script>` block | `{!JSENCODE(field)}` mandatory | Auto-encoding does not apply in JS context |
| VF variable in onclick attribute | `{!JSINHTMLENCODE(field)}` | Double-encoding: HTML first, then JS |
| Dynamic SOQL with user input | Bind variable `:varName` | Primary injection prevention |
| LWC template expression | `{field}` binding | Framework auto-escapes template bindings |
| LWC with innerHTML | Sanitize or avoid user data | innerHTML bypasses framework protection |
| PageReference from user input | Allowlist validation | No platform-level redirect protection |

The Visualforce rows follow apexdev 264 L13439-13516 and the SOQL row L13661-13662. UNVERIFIED (2026-10-20): the LWC rows and "No platform-level redirect protection" have no corpus line; the corpus discusses open redirects only through static resources (apexdev 264 L13379-13382).

---

## Recommended Workflow

Step-by-step instructions for reviewing code for XSS and injection issues:

1. **Identify all input sources.** Find every place user-controlled data enters the system: URL params, form fields, Apex REST endpoints, externally-loaded data. Map them to the data flow.
2. **Identify all output points.** For each input source, trace where the data is eventually rendered — HTML block, JavaScript block, HTML attribute, URL, or HTTP header.
3. **Apply the correct encoding function for each output context.** Use the context table above. Pay special attention to `<script>` blocks — they are the most common XSS location.
4. **Audit all dynamic SOQL and SOSL.** Search for `Database.query(` with string concatenation. Every such query must use bind variables for user input.
5. **Audit PageReference construction.** Any `new PageReference(url)` where the URL is derived from user input must be validated against an allowlist.
6. **Check for CRLF injection.** If the code sets HTTP response headers using user input, verify `\r` and `\n` characters are stripped before use.
7. **Validate with Salesforce Code Analyzer.** Run it with PMD rules and look for ApexXSSFromURLParam, ApexSOQLInjection, and ApexOpenRedirect findings, then run `scripts/check_xss_and_injection_prevention.py --manifest-dir <dir>`. UNVERIFIED (2026-10-20): the corpus names Salesforce Code Analyzer (sfdx 264 L12804) but not the `sf scanner run` command or these rule names.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All `<script>` block variable assignments from Apex use `{!JSENCODE(field)}`
- [ ] No dynamic SOQL/SOSL uses string concatenation with user input — bind variables used
- [ ] All PageReference targets from user input validated against allowlist
- [ ] LWC components do not use `innerHTML` with user-sourced data
- [ ] HTTP response headers do not include user-supplied values without stripping `\r\n`
- [ ] Salesforce Code Analyzer (PMD) runs clean with no XSS or injection findings (rule names UNVERIFIED (2026-10-20), see step 7)
- [ ] Stored user data rendered in Visualforce uses encoding appropriate for its output context

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **`{!field}` is NOT auto-encoded in JavaScript contexts** — expression output outside a component "isn't escaped during rendering" (apexdev 264 L13483). Every Apex expression inside a `<script>` block needs `{!JSENCODE(...)}` explicitly.
2. **`String.escapeSingleQuotes()` is the fallback, not the first defense** — the guide's first choice is a static query with a bind variable; escaping is for dynamic SOQL/SOSL you cannot avoid (apexdev 264 L13661, L13677). It escapes only quotes and backslashes (apexref 262 L235380), so identifiers and unquoted values still need an allowlist.
3. **LWC Locker Service does not sanitize Apex-returned HTML** — Locker Service protects the DOM from cross-component access, not from XSS in Apex-returned data rendered via `innerHTML` (UNVERIFIED (2026-10-20): not in the corpus).

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Code review findings | List of each XSS/injection finding with file, input source, output context, and correct fix |
| Corrected code snippets | The unsafe code with the encoding function or bind variable fix applied |

---

## Related Skills

- apex/soql-security — CRUD/FLS enforcement in SOQL queries (sharing model, not injection)
- security/secure-coding-review-checklist — AppExchange security review and Checkmarx patterns
- security/visualforce-security-and-modernization — CSRF, view state and FLS for legacy Visualforce pages
