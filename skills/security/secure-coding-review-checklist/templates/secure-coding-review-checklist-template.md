# Secure Coding Review — Findings Report

**Project / Package:** (name of the managed package or project under review)

**Reviewer:** (name or agent identifier)

**Date:** YYYY-MM-DD

**Salesforce Code Analyzer Version:** (output of `sf scanner --version`)

---

## Scope

**Files reviewed:**

| Type | Count |
|---|---|
| Apex classes | |
| Apex triggers | |
| Visualforce pages | |
| Visualforce components | |
| LWC components | |
| Aura components | |

**Sharing model summary:**

| Class / Trigger | Sharing Declaration | Justification (if `without sharing`) |
|---|---|---|
| | | |

---

## Code Analyzer Results

**Total findings:** (number)

| Severity | Count | Resolved | Justified |
|---|---|---|---|
| Critical | | | |
| High | | | |
| Medium | | | |
| Low | | | |

**Unresolved Critical/High findings:**

| # | Rule | File:Line | Description | Remediation |
|---|---|---|---|---|
| 1 | | | | |

---

## CRUD/FLS Enforcement

- [ ] Every inline SOQL query uses `WITH USER_MODE`
- [ ] Every `Database.query()` / `Database.queryWithBinds()` result is wrapped in `Security.stripInaccessible()` or uses `AccessLevel.USER_MODE`
- [ ] Every DML statement operates on SObjects that have been checked for create/update/delete access
- [ ] No raw query results are returned directly from `@AuraEnabled` methods without FLS enforcement

**Findings:**

| # | File:Line | Issue | Severity | Remediation | Status |
|---|---|---|---|---|---|
| 1 | | | | | |

---

## SOQL / SOSL Injection

- [ ] No dynamic SOQL uses string concatenation with user-controlled input
- [ ] All dynamic queries use bind variables or `Database.queryWithBinds()`
- [ ] Where `String.escapeSingleQuotes()` is used, it is not the only defense for non-string contexts
- [ ] LIKE clause wildcards (`%`, `_`) from user input are escaped

**Findings:**

| # | File:Line | Issue | Severity | Remediation | Status |
|---|---|---|---|---|---|
| 1 | | | | | |

---

## Cross-Site Scripting (XSS)

- [ ] Visualforce merge fields in HTML body use `HTMLENCODE()`
- [ ] Visualforce merge fields in `<script>` blocks use `JSENCODE()`
- [ ] Visualforce merge fields in URL parameters use `URLENCODE()`
- [ ] No LWC uses `innerHTML` or `lwc:dom="manual"` with user-controlled data
- [ ] No Aura component uses `$A.util.createComponent` with unvalidated markup

**Findings:**

| # | File:Line | Issue | Severity | Remediation | Status |
|---|---|---|---|---|---|
| 1 | | | | | |

---

## CSRF and Open Redirects

- [ ] All redirect targets are validated against an allowlist or use relative paths
- [ ] Custom `@RestResource` endpoints performing state changes validate the session or use anti-CSRF tokens
- [ ] `@AuraEnabled` methods exposed to guest users have explicit authentication checks
- [ ] No `PageReference` URL is built from unvalidated user input

**Findings:**

| # | File:Line | Issue | Severity | Remediation | Status |
|---|---|---|---|---|---|
| 1 | | | | | |

---

## Access Control

- [ ] Every `@AuraEnabled` method performing sensitive operations checks custom permissions or profile
- [ ] Sharing declarations are explicit and intentional on all classes and trigger handlers
- [ ] Guest user access paths have been tested with an unauthenticated session
- [ ] Test classes include negative security scenarios (user without permissions)

**Findings:**

| # | File:Line | Issue | Severity | Remediation | Status |
|---|---|---|---|---|---|
| 1 | | | | | |

---

## Summary

| Category | Total Issues | Critical/High | Resolved | Remaining |
|---|---|---|---|---|
| CRUD/FLS | | | | |
| SOQL Injection | | | | |
| XSS | | | | |
| CSRF / Redirects | | | | |
| Access Control | | | | |
| **Total** | | | | |

**Review readiness:** READY / NOT READY

**Blocking issues:** (list any Critical/High issues that must be resolved before submission)

**Notes:** (any additional context, justifications for accepted risks, or follow-up items)
