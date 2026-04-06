# Well-Architected Notes — Secure Coding Review Checklist

## Relevant Pillars

- **Security** — This is the primary pillar. Every check in this skill directly enforces the principle that custom code must respect platform security controls: CRUD/FLS, sharing rules, input validation, and output encoding. The Salesforce Well-Architected Security pillar requires that solutions "protect the confidentiality, integrity, and availability of data" and that developers leverage platform-native security mechanisms rather than building custom authorization logic.

- **Trusted** — The Salesforce Trusted pillar emphasizes that solutions must maintain user trust through transparent, secure data handling. Failing a security review erodes trust with both Salesforce and end customers. Code that silently bypasses FLS or sharing rules violates the Trusted principle even if the data exposure is unintentional — users expect their permission model to be enforced everywhere.

- **Reliability** — Security defects cause production failures: unhandled `FlsException` from `WITH USER_MODE`, SOQL injection that returns unexpected result sets, or XSS payloads that break page rendering. Secure coding practices overlap with reliability because they force explicit error handling, input validation, and defensive programming patterns that also prevent non-security runtime failures.

- **Operational Excellence** — Maintaining security review readiness is an ongoing operational concern. AppExchange partners face periodic re-reviews, and every code change risks introducing new vulnerabilities. Embedding security checks into CI/CD (Salesforce Code Analyzer in deployment pipelines) transforms security from a one-time gate to a continuous quality signal.

## Architectural Tradeoffs

The primary tradeoff is between strict enforcement and graceful degradation. `WITH USER_MODE` is the strictest approach — it throws exceptions when access is denied, ensuring no data leaks but requiring careful error handling to avoid crashing the user experience. `Security.stripInaccessible()` offers graceful degradation — it silently removes inaccessible fields, which is friendlier for the user but can cause confusing behavior if a component relies on a field that gets stripped. Architects must decide per-use-case: for data display, graceful degradation via `stripInaccessible()` is usually better; for data mutation, strict enforcement via `WITH USER_MODE` or explicit `isCreateable()`/`isUpdateable()` checks is safer because silent field removal during DML can cause data loss.

A secondary tradeoff is performance vs. security granularity. The older describe-check pattern (`isAccessible()` per field) requires Schema describe calls that consume CPU time and governor limits. `WITH USER_MODE` delegates enforcement to the query engine with negligible overhead, making it both more secure and more performant.

## Anti-Patterns

1. **Security-through-obscurity via UI-only restriction** — Restricting component visibility via page layouts or app assignments without enforcing access in the Apex layer. Any authenticated user can call `@AuraEnabled` methods directly, so UI-level restrictions provide no real security. The correct approach is to enforce permissions inside the Apex method and treat UI visibility as a convenience, not a control.

2. **One-time security audit with no CI integration** — Running Salesforce Code Analyzer manually before submission, fixing the findings, then never scanning again. New code changes introduce new vulnerabilities, and AppExchange partners face periodic re-reviews. The correct approach is to integrate Code Analyzer into the CI/CD pipeline so every pull request is scanned automatically.

3. **Blanket `without sharing` with post-hoc filtering** — Declaring a class `without sharing` to query all records, then filtering in Apex based on the user's role or profile. This is fragile, bypasses platform sharing optimizations, and is a guaranteed security review failure. The correct approach is to use `with sharing` and let the platform enforce sharing rules at the database level.

## Official Sources Used

- ISVforce Guide — Security Review: https://developer.salesforce.com/docs/atlas.en-us.packagingGuide.meta/packagingGuide/security_review_prepare.htm
- Apex Developer Guide — Security and Sharing: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_security_sharing_chapter.htm
- Salesforce Well-Architected — Security: https://architect.salesforce.com/well-architected/trusted/security
- Shield Platform Encryption Implementation Guide — https://help.salesforce.com/s/articleView?id=sf.security_pe_overview.htm&type=5
- Secure Apex Classes — https://developer.salesforce.com/docs/platform/lwc/guide/apex-security
- Salesforce Security Guide — https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5
