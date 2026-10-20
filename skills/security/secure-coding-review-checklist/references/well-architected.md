# Well-Architected Notes — Secure Coding Review Checklist

## Relevant Pillars

- **Security** — This is the primary pillar. Every check in this skill directly enforces the principle that custom code must respect platform security controls: CRUD/FLS, sharing rules, input validation, and output encoding. The Salesforce Well-Architected Security pillar requires that solutions "protect the confidentiality, integrity, and availability of data" and that developers leverage platform-native security mechanisms rather than building custom authorization logic.

- **Trusted** — The Salesforce Trusted pillar emphasizes that solutions must maintain user trust through transparent, secure data handling. Failing a security review erodes trust with both Salesforce and end customers. Code that silently bypasses FLS or sharing rules violates the Trusted principle even if the data exposure is unintentional — users expect their permission model to be enforced everywhere.

- **Reliability** — Security defects cause production failures: unhandled `QueryException` from `WITH USER_MODE` (apexref 262 L215180-215192), SOQL injection that returns unexpected result sets, or XSS payloads that break page rendering. Secure coding practices overlap with reliability because they force explicit error handling, input validation, and defensive programming patterns that also prevent non-security runtime failures.

- **Operational Excellence** — Maintaining security review readiness is an ongoing operational concern. AppExchange partners face periodic re-reviews, and every code change risks introducing new vulnerabilities. Embedding security checks into CI/CD (Salesforce Code Analyzer in deployment pipelines) transforms security from a one-time gate to a continuous quality signal.

## Architectural Tradeoffs

The primary tradeoff is between strict enforcement and graceful degradation. `WITH USER_MODE` is the strictest approach — it throws exceptions when access is denied, ensuring no data leaks but requiring careful error handling to avoid crashing the user experience. `Security.stripInaccessible()` offers graceful degradation — it silently removes inaccessible fields, which is friendlier for the user but can cause confusing behavior if a component relies on a field that gets stripped. Architects must decide per-use-case: for data display, graceful degradation via `stripInaccessible()` is usually better; for data mutation, strict enforcement via `WITH USER_MODE` or explicit `isCreateable()`/`isUpdateable()` checks is safer because silent field removal during DML can cause data loss.

A secondary tradeoff is performance vs. security granularity. The older describe-check pattern (`isAccessible()` per field) requires Schema describe calls that consume CPU time and governor limits. `WITH USER_MODE` delegates enforcement to the query engine with negligible overhead, making it both more secure and more performant.

## Anti-Patterns

1. **Security-through-obscurity via UI-only restriction** — Restricting component visibility via page layouts or app assignments without enforcing access in the Apex layer. Any user with Apex class access to the controller can call its `@AuraEnabled` methods directly (class security, apexdev 264 L12507-12516), so UI-level restrictions provide no real security. The correct approach is to enforce permissions inside the Apex method and treat UI visibility as a convenience, not a control.

2. **One-time security audit with no CI integration** — Running Salesforce Code Analyzer manually before submission, fixing the findings, then never scanning again. New code changes introduce new vulnerabilities, and AppExchange partners face periodic re-reviews. The correct approach is to integrate Code Analyzer into the CI/CD pipeline so every pull request is scanned automatically.

3. **Blanket `without sharing` with post-hoc filtering** — Declaring a class `without sharing` to query all records, then filtering in Apex based on the user's role or profile. This is fragile, bypasses platform sharing optimizations, and is a guaranteed security review failure. The correct approach is to use `with sharing` and let the platform enforce sharing rules at the database level.

## Official Sources Used

- Apex Developer Guide (264) — sharing defaults by API version and the four 66.0 factors (apexdev 264 L11926-11937); trigger sharing and access mode (L4905-4947); versioned changes at 67.0 (L45132-45147); `WITH SECURITY_ENFORCED` below 45.0 (L45412-45413).
- Apex Developer Guide (264) — dynamic SOQL `accessLevel` from API 55.0 (apexdev 264 L11609-11613), in-scope binds (L11623-11627), `queryWithBinds` from 57.0 (L11647-11656), SOQL injection and `escapeSingleQuotes` (L11676-11681); user-mode exceptions in DML (L12167-12168, L12233-12236); Checkmarx note (L12271-12272).
- Apex Developer Guide (264) — Visualforce XSS defences and `HTMLENCODE` / `JSENCODE` / `JSINHTMLENCODE` / `URLENCODE` (apexdev 264 L13433-13543); anti-CSRF token and the custom action bypass (L13568-13599); Apex class security for `@AuraEnabled` entry points (L12506-12522); cacheable methods (L5096).
- Apex Reference Guide (262) — `QueryException.getInaccessibleFields()` for user-mode queries (apexref 262 L215176-215200).
- Not corpus, used only for claims marked UNVERIFIED: ISVforce Security Review — https://developer.salesforce.com/docs/atlas.en-us.packagingGuide.meta/packagingGuide/security_review_prepare.htm ; Secure Coding Guide, SOQL Injection — https://developer.salesforce.com/docs/atlas.en-us.secure_coding_guide.meta/secure_coding_guide/secure_coding_soql_injection.htm ; blog, Write Simplified and Secure Apex with Spring '23 Updates — https://developer.salesforce.com/blogs/2023/05/write-simplified-and-secure-apex-with-spring-23-updates
