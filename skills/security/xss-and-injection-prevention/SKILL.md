---
name: xss-and-injection-prevention
description: "Use when writing or reviewing Visualforce pages, Apex controllers, or LWC components that output user-supplied data, build dynamic queries, or construct HTTP responses. Triggers: 'XSS in Visualforce', 'SOQL injection vulnerability', 'how to encode output in Apex', 'JSENCODE Visualforce', 'open redirect prevention'. NOT for Apex CRUD/FLS enforcement (use soql-security or apex-crud-and-fls), NOT for Shield encryption (use shield-encryption-key-management), NOT for AppExchange security review process (use secure-coding-review-checklist)."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
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

## Core Concepts

### Output Context Determines Encoding Function

Salesforce provides four Visualforce encoding functions. Applying the wrong one is as bad as applying none:

| Output Context | Correct Function | Notes |
|---|---|---|
| HTML body | `HTMLENCODE()` | Auto-applied to `{!field}` in HTML body — explicit for string expressions |
| JavaScript string in VF script block | `JSENCODE()` | `{!field}` inside `<script>` is NOT auto-encoded — #1 XSS vector |
| HTML attribute with JavaScript | `JSINHTMLENCODE()` | Encodes for JS first, then HTML — for inline event handlers like `onclick` |
| URL parameter | `URLENCODE()` | Use when constructing URLs with user data |

The critical rule: Visualforce auto-escapes `{!field}` in HTML context only. Inside a `<script>` block, `{!field}` is rendered raw. Every JavaScript variable assignment from a VF expression must use `JSENCODE()`.

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

Bind variables (`:varName`) prevent injection because the platform treats the bound value as a literal data value, never as query syntax. This is the authoritative solution for dynamic SOQL. `String.escapeSingleQuotes()` is a secondary measure only — it does not fully prevent injection in all edge cases.

### LWC and Locker Service / Lightning Web Security

LWC runs inside Lightning Locker Service or Lightning Web Security depending on the org configuration. These sandbox the DOM and prevent cross-component script access. However, they do not prevent stored XSS in data coming from Apex. If an Apex controller returns maliciously crafted HTML from a user-supplied field and the LWC renders it with `innerHTML`, the attack succeeds. Safe LWC patterns use template bindings `{field}` which are auto-escaped by the framework.

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

**Why not rely on auto-escape:** Auto-escaping only applies to HTML contexts. JavaScript rendering receives the raw string before HTML interpretation.

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
| VF variable in HTML body | `{!field}` auto-encoding sufficient | Auto-escaped in HTML context |
| VF variable in `<script>` block | `{!JSENCODE(field)}` mandatory | Auto-encoding does not apply in JS context |
| VF variable in onclick attribute | `{!JSINHTMLENCODE(field)}` | Double-encoding: JS first, then HTML |
| Dynamic SOQL with user input | Bind variable `:varName` | Primary injection prevention |
| LWC template expression | `{field}` binding | Framework auto-escapes template bindings |
| LWC with innerHTML | Sanitize or avoid user data | innerHTML bypasses framework protection |
| PageReference from user input | Allowlist validation | No platform-level redirect protection |

---

## Recommended Workflow

Step-by-step instructions for reviewing code for XSS and injection issues:

1. **Identify all input sources.** Find every place user-controlled data enters the system: URL params, form fields, Apex REST endpoints, externally-loaded data. Map them to the data flow.
2. **Identify all output points.** For each input source, trace where the data is eventually rendered — HTML block, JavaScript block, HTML attribute, URL, or HTTP header.
3. **Apply the correct encoding function for each output context.** Use the context table above. Pay special attention to `<script>` blocks — they are the most common XSS location.
4. **Audit all dynamic SOQL and SOSL.** Search for `Database.query(` with string concatenation. Every such query must use bind variables for user input.
5. **Audit PageReference construction.** Any `new PageReference(url)` where the URL is derived from user input must be validated against an allowlist.
6. **Check for CRLF injection.** If the code sets HTTP response headers using user input, verify `\r` and `\n` characters are stripped before use.
7. **Validate with Salesforce Code Analyzer.** Run `sf scanner run` with PMD rules — it includes ApexXSSFromURLParam, ApexSOQLInjection, and ApexOpenRedirect rules.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All `<script>` block variable assignments from Apex use `{!JSENCODE(field)}`
- [ ] No dynamic SOQL/SOSL uses string concatenation with user input — bind variables used
- [ ] All PageReference targets from user input validated against allowlist
- [ ] LWC components do not use `innerHTML` with user-sourced data
- [ ] HTTP response headers do not include user-supplied values without stripping `\r\n`
- [ ] Salesforce Code Analyzer (PMD) runs clean with no XSS or injection findings
- [ ] Stored user data rendered in Visualforce uses encoding appropriate for its output context

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **`{!field}` is NOT auto-encoded in JavaScript contexts** — The single most common XSS vector in Visualforce. Every Apex expression inside a `<script>` block needs `{!JSENCODE(...)}` explicitly.
2. **`String.escapeSingleQuotes()` does not fully prevent SOQL injection** — It handles the common case but does not cover all edge cases. Always use bind variables as the primary defense.
3. **LWC Locker Service does not sanitize Apex-returned HTML** — Locker Service protects the DOM from cross-component access, not from XSS in Apex-returned data rendered via `innerHTML`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Code review findings | List of each XSS/injection finding with file, input source, output context, and correct fix |
| Corrected code snippets | The unsafe code with the encoding function or bind variable fix applied |

---

## Related Skills

- soql-security — CRUD/FLS enforcement in SOQL queries (sharing model, not injection)
- secure-coding-review-checklist — AppExchange security review and Checkmarx patterns
