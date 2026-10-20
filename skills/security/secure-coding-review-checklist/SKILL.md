---
name: secure-coding-review-checklist
description: "Use this skill to audit Apex, Visualforce, LWC, and Aura code for Salesforce security review readiness — covering CRUD/FLS enforcement, SOQL injection, XSS, CSRF, and open redirects. NOT for network-level penetration testing or Shield Platform Encryption key management — use security/platform-encryption. NOT for fixing a single query's injection or FLS gap — use apex/soql-security."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "how do I pass the Salesforce AppExchange security review"
  - "check my Apex code for CRUD/FLS enforcement gaps"
  - "review this code for SOQL injection vulnerabilities"
  - "audit my apex classes before appexchange security review"
  - "find xss and csrf risks in my visualforce pages"
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
version: 1.1.2
author: Pranav Nagrecha
updated: 2026-10-20
---

# Secure Coding Review Checklist

This skill activates when a practitioner needs to audit Salesforce custom code for security vulnerabilities before an AppExchange security review, internal security audit, or ISV partner submission. It produces a structured, prioritized set of findings covering the vulnerability categories that cause the most review failures: CRUD/FLS gaps, SOQL/SOSL injection, cross-site scripting (XSS), CSRF, and open redirects.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether the code runs in a managed package context (namespace prefix) or unmanaged, as this changes sharing and access enforcement defaults.
- Identify the Apex sharing model per class: `with sharing`, `without sharing`, `inherited sharing`, or no keyword. With no keyword the default is **version-gated**. A class saved at API **67.0+** runs `with sharing` (apexdev 264 L11930). At **66.0 and below** it depends on four factors, in order: a class in an *inheritance* chain where any class is saved at 67.0+ runs `with sharing`; an Aura controller or an `@AuraEnabled` method called from LWC runs `with sharing`; a class that isn't an Apex entry point takes the caller's mode; otherwise it runs `without sharing` (L11931-11937). An earlier version of this skill said "66.0 and below runs without sharing" and "call chain" — both were wrong. The gate is the `<apiVersion>` in each class's `.cls-meta.xml`, not the org's release, so collect that value alongside the keyword. Triggers are a special case, but not the one usually assumed: they cannot carry a sharing *keyword* at any version, yet their database operations still take an access mode per statement, and at 67.0+ a bare one runs in user mode — which overrides the implicit `without sharing` and enforces sharing, FLS and CRUD. Record the trigger's own `.trigger-meta.xml` apiVersion and read each query's access mode; do not infer "unenforced" from the missing keyword (Gotcha 1 below). Full table: [`agents/_shared/AGENT_CONTRACT.md` § Apex security idiom by API version](../../../agents/_shared/AGENT_CONTRACT.md#apex-security-idiom-by-api-version).
- Determine if the org has Salesforce Code Analyzer results available (pkg2_dev 264 L23353-23355 recommends it while you develop). UNVERIFIED (2026-10-20): that the review team runs the same scans and requires every flagged item to be justified is Help-only.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| What `<apiVersion>` does each class and trigger declare? | At 67.0+ database operations run in user mode by default and `WITH SECURITY_ENFORCED` can't be used (apexdev 264 L11926-11929) — gotchas.md Gotcha 2 | A per-file version column, so every finding is scored against the right default |
| For bare classes at 66.0 and below, are they entry points, Aura/`@AuraEnabled` controllers, or in an inheritance chain with a 67.0+ class? | Those factors decide the sharing mode (apexdev 264 L11931-11937) — Before Starting | The effective sharing mode per class instead of a guess from the keyword |
| Which queries take user input, and where does it land — a value, a field name, an ORDER BY or a LIMIT? | Bind variables cover values only; `escapeSingleQuotes` escapes only single quotes and backslashes (apexref 262 L235380) — gotchas.md Gotcha 3 | A bind or an allowlist per injection point |
| How should a user without field access experience the failure? | User-mode SOQL throws `QueryException` (apexref 262 L215180-215192) — gotchas.md Gotcha 1 | A caught exception or `stripInaccessible` chosen per entry point |
| Where do Visualforce merge fields land — HTML body, `<script>`, a URL, or JavaScript inside an HTML tag? | Each context has its own function, and `JSINHTMLENCODE` is `JSENCODE(HTMLENCODE(x))` (apexdev 264 L13504-13516) — gotchas.md Gotcha 4 | One encoder per merge field, matched to its context |
| Which profiles and permission sets have Apex class access to each `@AuraEnabled` controller? | Class security applies to `@AuraEnabled` methods called from LWC (apexdev 264 L12507-12516) — gotchas.md Gotcha 5 | Access granted by class access and checked inside the method, not by component visibility |
| Do any custom action methods change data on page load? | They bypass the Visualforce anti-CSRF token (apexdev 264 L13593-13596) — Core Concepts, Open Redirects and CSRF | A confirmation step or POST-only action for each state change |

A proper review adds a version-aware finding per file with the exact control to change; "just running the scanner" scores bare queries and sharing keywords against the wrong default.

---

## Core Concepts

### CRUD/FLS Enforcement

CRUD (Create, Read, Update, Delete) and FLS (Field-Level Security) enforcement is a leading cause of AppExchange security review failures (UNVERIFIED (2026-10-20): the ranking is not in the corpus). Every SOQL query and every DML statement must respect the running user's object and field permissions. The `accessLevel` parameter on `Database.query` is **API 55.0 and later** (apexdev 264 L11609) and `Database.queryWithBinds` is **API 57.0 and later** (L11647). UNVERIFIED (2026-10-20): the releases that introduced `Security.stripInaccessible()` (Spring '20) and the `WITH USER_MODE` clause (Spring '23) are blog/Help claims, not corpus lines. Check the **class's** `<apiVersion>` before recommending an access-mode idiom; `WITH SECURITY_ENFORCED` is not recommended below API 45.0 (L45412-45413). At **API 67.0+** the default inverted: "Apex runs in user context by default" (L45133-45135), and "you can't use the WITH SECURITY_ENFORCED clause" (L11926). The gate is the `.cls-meta.xml` value, not the org's release — a class pinned to 58.0 keeps the old system-mode default inside a Summer '26 org, so read the meta file before judging any query. Version table: [`AGENT_CONTRACT.md` § Apex security idiom by API version](../../../agents/_shared/AGENT_CONTRACT.md#apex-security-idiom-by-api-version). Prior patterns using `Schema.DescribeSObjectResult.isAccessible()` are still valid but verbose and error-prone. UNVERIFIED (2026-10-20): that Code Analyzer and Checkmarx both flag unenforced queries is not in the corpus; the guide notes only that Checkmarx can raise false positives for the newer `AccessLevel.withPermissionSetId()` feature (apexdev 264 L12271-12272).

### SOQL and SOSL Injection

SOQL injection occurs when user-controlled input is concatenated directly into a dynamic SOQL or SOSL string. Unlike SQL injection, SOQL injection cannot drop tables, but it can expose records the user should not see or bypass WHERE clause filters entirely. The fix is bind variables in **both** cases. Inline SOQL takes `:variableName` directly. Dynamic SOQL also takes bind variables: `Database.query('... WHERE Name = :userInput')` resolves `:userInput` from an in-scope Apex variable, and `Database.queryWithBinds(query, bindMap, AccessLevel.USER_MODE)` resolves them from an explicit `Map<String, Object>` with no scoping constraint. `String.escapeSingleQuotes()` is a **secondary measure only** — it neutralises quote-breakout but does nothing for an injected `LIMIT`, `ORDER BY`, field name, or object name, and it cannot be applied to a value spliced in unquoted. `escapeSingleQuotes` "adds the escape character (`\`) to all single quotation marks" (apexdev 264 L11679-11681), and its reference entry adds backslashes — "before any single quotation mark (') or backslash (\)" (apexref 262 L235380) — and nothing else. UNVERIFIED (2026-10-20): the PMD rule name `ApexSOQLInjection` and its blind spots are not in the corpus.

### Cross-Site Scripting (XSS) in Visualforce and LWC

"By default, nearly all Visualforce tags escape the XSS-vulnerable characters"; `escape="false"` turns that off (apexdev 264 L13449-13452), and custom JavaScript and `<apex:includeScript>` have no built-in protection (L13456). Use `HTMLENCODE` for HTML, `JSENCODE` for JavaScript, `JSINHTMLENCODE` for JavaScript inside HTML tags, and `URLENCODE` for URLs (L13504-13516). UNVERIFIED (2026-10-20): the review-failure ranking, the escaping of a bare `{!expression}` in raw HTML, and the LWC (`lwc:dom="manual"`, `innerHTML`) and Aura (`$A.util.createComponent`) claims are not in the corpus.

### Open Redirects and CSRF

Open redirects occur when a `PageReference` URL, `NavigationMixin` target, or Visualforce `action` attribute accepts user-controlled input without validation. Attackers chain open redirects with phishing to steal session tokens. Visualforce pages carry an anti-CSRF token as a hidden form field, which "protects you when using all of the standard controllers and methods" (apexdev 264 L13568-13571); a custom action method that reads a parameter and changes data on page load bypasses it (L13593-13596). UNVERIFIED (2026-10-20): the `ViewStateCSRF` name and the CSRF posture of `@RestResource` and guest `@AuraEnabled` methods are not in the corpus — treat every state-changing unauthenticated operation as unprotected until shown otherwise.

---

## Common Patterns

### USER_MODE for All SOQL Queries

**When to use:** Any SOQL query where you want the platform to automatically enforce CRUD, FLS, and sharing rules in a single keyword.

**How it works:**

```apex
// User mode enforces object permissions, FLS and sharing (apexdev 264 L11612-11613)
List<Account> accounts = [
    SELECT Id, Name, AnnualRevenue
    FROM Account
    WHERE Industry = :industryFilter
    WITH USER_MODE
];
```

If the running user lacks read access to `AnnualRevenue`, the query throws a `QueryException`; `getInaccessibleFields()` lists the fields (apexref 262 L215176-215192; apexdev 264 L12158). This is the preferred pattern because it is declarative and cannot be accidentally omitted field-by-field. At **API 67.0+** the same enforcement is the default with no keyword, so keep writing `WITH USER_MODE` to state the intent explicitly rather than because it is load-bearing — and keep reviewing bare queries in classes at **66.0 and below**, where the default is still system mode.

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
| Dynamic SOQL via `Database.query()` | `Database.queryWithBinds(q, bindMap, AccessLevel.USER_MODE)` — or `:inScopeVar` binding inside the query string | Bind variables **are** supported in dynamic SOQL and are the primary injection defence; `AccessLevel.USER_MODE` adds CRUD/FLS in the same call |
| Dynamic SOQL where the *identifier* is user-supplied (field, object, ORDER BY) | Allowlist against `Schema.getGlobalDescribe()` / describe results | A bind variable can only stand in for a literal value, never for an identifier — allowlisting is the only control |
| Class pinned below API v57, so `queryWithBinds` is unavailable | `:inScopeVar` binding + `Database.query(q, AccessLevel.USER_MODE)` at 55.0+ (apexdev 264 L11609); below 55.0, `WITH SECURITY_ENFORCED` + `Security.stripInaccessible()` | In-scope binding predates v57 (L11623-11627); `escapeSingleQuotes()` alone is a fallback, not a fix |
| Visualforce expression in HTML context | Standard tag with escaping on, or `HTMLENCODE({!value})` | Tags escape by default unless `escape="false"` (apexdev 264 L13449-13452) |
| Visualforce expression in JS context | `JSENCODE({!value})` | HTMLENCODE does not prevent script injection inside `<script>` blocks |
| LWC needing raw HTML rendering | Avoid `innerHTML`; use template iteration | `lwc:dom="manual"` bypasses LWC auto-escaping |
| Apex REST endpoint changing state | Validate session or implement CSRF token | `@RestResource` has no built-in CSRF protection |

UNVERIFIED (2026-10-20): the LWC and `@RestResource` rows above are not in the corpus (no LWC guide or Apex REST CSRF statement is in it).

---

## Recommended Workflow

Step-by-step instructions for auditing code before a Salesforce security review submission:

1. **Inventory all custom code** — List every Apex class, trigger, Visualforce page, Aura component, and LWC in scope. Record each Apex file's sharing keyword *and* its `.cls-meta.xml` `<apiVersion>`: a bare class runs `with sharing` at 67.0+, and at 66.0 and below its mode depends on inheritance, entry-point type and caller (apexdev 264 L11930-11937), so the keyword alone does not tell you what the class does.
2. **Run Salesforce Code Analyzer and the skill checker** — run Code Analyzer (UNVERIFIED (2026-10-20): the CLI command and engine names are not in the corpus; use the plugin's current `--help`), then `python3 scripts/check_secure_coding_review_checklist.py --manifest-dir ./force-app`. Triage every High or Critical finding.
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
- [ ] Sharing declarations (`with sharing`, `without sharing`, `inherited sharing`) are intentional on every Apex class, judged against that class's `<apiVersion>`; triggers cannot declare one, so the check there is that the trigger delegates to a handler class that does
- [ ] Sensitive operations exposed to guest users have explicit CSRF protection
- [ ] Test class coverage includes negative security scenarios (user without permissions)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **A trigger's sharing *declaration* is fixed; what its body *enforces* is not** — the two are not the same thing, and conflating them is the commonest review error here. A trigger cannot carry a sharing keyword: per the Apex Developer Guide it "always run[s] implicitly in a without sharing context". But that is only the baseline. The same page continues: "database operations within trigger bodies, including SOQL queries, SOSL queries, DML statements, and Database methods, run in **user mode** unless system mode is explicitly specified", and "**user mode overrides the trigger's without sharing context** and effectively enforces a with sharing context in the trigger body". So a bare SOQL in a trigger saved at API 67.0+ returns only the rows the running user can see, and enforces FLS and object permissions too — it is enforced on all three, not none. Only an explicit `WITH SYSTEM_MODE` / `as system` / `AccessLevel.SYSTEM_MODE` falls back to the baseline, and then object- and field-level permissions are ignored *and* all records are visible. **Never read the implicit `without sharing` as proof that a given trigger query bypassed sharing — read that query's access mode.** Below 67.0 the old default holds and a bare trigger-body operation does run in system mode; the gate is the `<apiVersion>` in the trigger's own `.trigger-meta.xml`. See [`references/gotchas.md`](references/gotchas.md) Gotcha 2 for the worked example.
2. **`WITH USER_MODE` throws exceptions, not empty results** — Unlike the older `isAccessible()` pattern that let you gracefully degrade, a user-mode query throws `QueryException` (apexref 262 L215180-215192) and a user-mode DML without the object permission throws the `SecurityException` the guide's own test catches (apexdev 264 L12233-12236). Your code must catch these or the user sees an unhandled error.
3. **`HTMLENCODE` in Visualforce does not protect JavaScript contexts** — Developers often apply `HTMLENCODE()` everywhere, but inside a `<script>` tag, HTML-encoded output can still execute as JavaScript. The correct function for JS context is `JSENCODE()`. Using the wrong encoder is a guaranteed review failure.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Security findings report | Categorized list of vulnerabilities found, severity-ranked, with line-level code references and remediation steps |
| Review readiness checklist | Pass/fail status for each major security category (CRUD/FLS, Injection, XSS, CSRF, Sharing) |

---

## Related Skills

- `security/experience-cloud-security` — Use alongside this skill when the code under review powers an Experience Cloud site with guest user access, which adds unauthenticated attack surface.
