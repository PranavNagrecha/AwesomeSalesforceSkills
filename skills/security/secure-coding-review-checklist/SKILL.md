---
name: secure-coding-review-checklist
description: "Use this skill to audit Apex, Visualforce, LWC, and Aura code for Salesforce security review readiness — covering CRUD/FLS enforcement, SOQL injection, XSS, CSRF, and open redirects. NOT for network-level penetration testing, Shield Platform Encryption key management, or general org permission set design."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "how do I pass the Salesforce AppExchange security review"
  - "check my Apex code for CRUD/FLS enforcement gaps"
  - "review this code for SOQL injection vulnerabilities"
tags:
  - secure-coding-review-checklist
  - crud-fls
  - soql-injection
  - xss
  - security-review
  - appexchange
  - code-analyzer
inputs:
  - "Apex classes, triggers, Visualforce pages, LWC/Aura components to review"
  - "AppExchange security review submission context (new or re-review)"
outputs:
  - "Prioritized list of security findings with line-level remediation guidance"
  - "Security review readiness checklist with pass/fail status per category"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Secure Coding Review Checklist

This skill activates when a practitioner needs to audit Salesforce custom code for security vulnerabilities before an AppExchange security review, internal security audit, or ISV partner submission. It produces a structured, prioritized set of findings covering the vulnerability categories that cause the most review failures: CRUD/FLS gaps, SOQL/SOSL injection, cross-site scripting (XSS), CSRF, and open redirects.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether the code runs in a managed package context (namespace prefix) or unmanaged, as this changes sharing and access enforcement defaults.
- Identify the Apex sharing model: classes declared `with sharing`, `without sharing`, `inherited sharing`, or no keyword (defaults to `without sharing` in triggers, `inherited sharing` in newer contexts).
- Determine if the org has Salesforce Code Analyzer (formerly PMD + Graph Engine) results available, since the review team will run these scans themselves and any flagged items must be justified or fixed.

---

## Core Concepts

### CRUD/FLS Enforcement

CRUD (Create, Read, Update, Delete) and FLS (Field-Level Security) enforcement is the number-one cause of AppExchange security review failures. Every SOQL query and every DML statement must respect the running user's object and field permissions. In Spring '20+, the platform introduced `WITH USER_MODE` for SOQL and `Security.stripInaccessible()` for DML results. Prior patterns using `Schema.DescribeSObjectResult.isAccessible()` are still valid but verbose and error-prone. Code that queries or writes data without any CRUD/FLS enforcement will be flagged by both the Salesforce Code Analyzer and the Checkmarx source scanner.

### SOQL and SOSL Injection

SOQL injection occurs when user-controlled input is concatenated directly into a dynamic SOQL or SOSL string. Unlike SQL injection, SOQL injection cannot drop tables, but it can expose records the user should not see or bypass WHERE clause filters entirely. The fix is to use bind variables (`:variableName`) in inline SOQL, or `String.escapeSingleQuotes()` for dynamic queries built with `Database.query()`. The Code Analyzer PMD rule `ApexSOQLInjection` catches the most common forms, but it misses indirect flows where user input passes through helper methods before reaching the query string.

### Cross-Site Scripting (XSS) in Visualforce and LWC

Stored XSS is the second-most common review failure after CRUD/FLS. In Visualforce, any `{!expression}` inside raw HTML context (outside of standard components) is unescaped by default. The `JSENCODE()`, `HTMLENCODE()`, and `URLENCODE()` functions must be used in the correct context. LWC is safer by default because the template compiler escapes expressions, but developers who use `lwc:dom="manual"` or `innerHTML` bypass this protection. Aura components using `$A.util.createComponent` with unvalidated data are also vulnerable.

### Open Redirects and CSRF

Open redirects occur when a `PageReference` URL, `NavigationMixin` target, or Visualforce `action` attribute accepts user-controlled input without validation. Attackers chain open redirects with phishing to steal session tokens. CSRF protection is built into Visualforce postbacks via the `ViewStateCSRF` mechanism, but custom REST endpoints (Apex `@RestResource`) and `@AuraEnabled` methods exposed to guest users have no automatic CSRF protection. Any state-changing operation exposed to unauthenticated contexts must implement its own anti-CSRF token or use platform session validation.

---

## Common Patterns

### USER_MODE for All SOQL Queries

**When to use:** Any SOQL query where you want the platform to automatically enforce CRUD, FLS, and sharing rules in a single keyword.

**How it works:**

```apex
// Spring '20+ pattern — enforces sharing, CRUD, and FLS in one shot
List<Account> accounts = [
    SELECT Id, Name, AnnualRevenue
    FROM Account
    WHERE Industry = :industryFilter
    WITH USER_MODE
];
```

If the running user lacks read access to `AnnualRevenue`, the query throws a `System.FlsException` rather than silently returning the field. This is the preferred pattern because it is declarative and cannot be accidentally omitted field-by-field.

**Why not the alternative:** The older `Schema.SObjectType.Account.fields.AnnualRevenue.getDescribe().isAccessible()` pattern requires a check for every field in the query and every object in a relationship traversal. Developers routinely forget to update the checks when adding new fields, creating silent FLS gaps.

### stripInaccessible for DML Results

**When to use:** When you need to sanitize query results before returning them to a caller (e.g., `@AuraEnabled` methods), especially when you cannot use `WITH USER_MODE` because the query is dynamic.

**How it works:**

```apex
List<Contact> contacts = Database.query(dynamicQuery);
SObjectAccessDecision decision = Security.stripInaccessible(
    AccessType.READABLE, contacts
);
List<Contact> safeContacts = decision.getRecords();
// Fields the user cannot read are physically removed from the SObject map
```

**Why not the alternative:** Returning raw query results from an `@AuraEnabled` method exposes field values the user's profile does not grant. Even if the LWC template does not display them, the wire response is visible in browser DevTools.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Standard inline SOQL in Apex | `WITH USER_MODE` | Single keyword enforces sharing + CRUD + FLS; least error-prone |
| Dynamic SOQL via `Database.query()` | `String.escapeSingleQuotes()` + `Security.stripInaccessible()` | Bind variables unavailable in dynamic strings; stripInaccessible cleans results |
| Visualforce expression in HTML context | `HTMLENCODE({!value})` | Default Visualforce merge syntax is unescaped in raw HTML |
| Visualforce expression in JS context | `JSENCODE({!value})` | HTMLENCODE does not prevent script injection inside `<script>` blocks |
| LWC needing raw HTML rendering | Avoid `innerHTML`; use template iteration | `lwc:dom="manual"` bypasses LWC auto-escaping |
| Apex REST endpoint changing state | Validate session or implement CSRF token | `@RestResource` has no built-in CSRF protection |

---

## Recommended Workflow

Step-by-step instructions for auditing code before a Salesforce security review submission:

1. **Inventory all custom code** — List every Apex class, trigger, Visualforce page, Aura component, and LWC in scope. Note which run `without sharing` or have no sharing keyword declared.
2. **Run Salesforce Code Analyzer** — Execute `sf scanner run --target ./force-app --format csv` to get the PMD and Graph Engine results. Triage every finding rated High or Critical; these will be flagged in the review.
3. **Audit CRUD/FLS enforcement** — For every SOQL query, confirm `WITH USER_MODE` is present or that `stripInaccessible()` wraps the results. For every DML statement, confirm the operation respects field-level permissions.
4. **Check for injection vectors** — Search for `Database.query(`, `Database.countQuery(`, and `Search.query(` calls. Verify every variable concatenated into the query string is escaped with `String.escapeSingleQuotes()` or replaced with bind variables.
5. **Scan for XSS in Visualforce and components** — In Visualforce, search for `{!` expressions outside standard components and confirm encoding functions are applied. In LWC, search for `innerHTML` and `lwc:dom="manual"`. In Aura, search for `$A.util.createComponent` with dynamic markup.
6. **Validate redirect targets** — Check every `PageReference`, `NavigationMixin.Navigate`, and Visualforce `action` attribute for user-controlled URL parameters. Confirm redirect targets are validated against an allowlist or use relative paths.
7. **Generate the findings report** — Use the output template to record each finding with severity, file location, code snippet, and remediation. Group by category (CRUD/FLS, Injection, XSS, CSRF/Redirect, Other).

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every SOQL query uses `WITH USER_MODE` or results are wrapped in `Security.stripInaccessible()`
- [ ] Every DML operation respects CRUD/FLS — no raw insert/update of user-supplied SObjects without permission checks
- [ ] No dynamic SOQL concatenates user input without `String.escapeSingleQuotes()`
- [ ] Visualforce merge fields in raw HTML use `HTMLENCODE()`, JS context uses `JSENCODE()`, URL context uses `URLENCODE()`
- [ ] No LWC or Aura components use `innerHTML` or `lwc:dom="manual"` with user-controlled data
- [ ] All redirect targets are validated against an allowlist or restricted to relative paths
- [ ] Salesforce Code Analyzer reports zero High/Critical findings or each is documented with justification
- [ ] Sharing declarations (`with sharing`, `without sharing`, `inherited sharing`) are intentional on every Apex class and trigger
- [ ] Sensitive operations exposed to guest users have explicit CSRF protection
- [ ] Test class coverage includes negative security scenarios (user without permissions)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **`without sharing` is the default in triggers** — Apex triggers that omit the sharing keyword run in system context with full data visibility. Code Analyzer flags this, and the security review team requires an explicit justification for every trigger without `with sharing`.
2. **`WITH USER_MODE` throws exceptions, not empty results** — Unlike the older `isAccessible()` pattern that let you gracefully degrade, `WITH USER_MODE` throws `System.FlsException` or `System.CrudException` at runtime. Your code must catch these or the user sees an unhandled error.
3. **`HTMLENCODE` in Visualforce does not protect JavaScript contexts** — Developers often apply `HTMLENCODE()` everywhere, but inside a `<script>` tag, HTML-encoded output can still execute as JavaScript. The correct function for JS context is `JSENCODE()`. Using the wrong encoder is a guaranteed review failure.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Security findings report | Categorized list of vulnerabilities found, severity-ranked, with line-level code references and remediation steps |
| Review readiness checklist | Pass/fail status for each major security category (CRUD/FLS, Injection, XSS, CSRF, Sharing) |

---

## Related Skills

- experience-cloud-security — Use alongside this skill when the code under review powers an Experience Cloud site with guest user access, which adds unauthenticated attack surface.
