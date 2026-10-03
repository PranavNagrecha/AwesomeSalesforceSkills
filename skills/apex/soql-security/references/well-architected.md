# SOQL Security — Well-Architected Mapping

## Security

**Directly implements:**
- SOQL injection prevention protects against data exfiltration and manipulation via crafted queries
- FLS/CRUD enforcement ensures users can only access data their permission set allows — prevents privilege escalation through Apex code
- `WITH USER_MODE` and `stripInaccessible` are the Salesforce-native FLS enforcement mechanisms to design around; `WITH SECURITY_ENFORCED` is legacy at `apiVersion` 57.0–66.0 and removed at 67.0+, where user mode is the default for database operations

**Tag a finding as Security when:**
- `Database.query()` concatenates any variable that originates from user input, URL parameters, or deserialized JSON
- An `@AuraEnabled` or REST endpoint method queries or mutates records without FLS enforcement
- A `without sharing` class performs SOQL/DML on sensitive objects without documented justification

---

## Reliability

**How it connects:**
- Allowlist validation for dynamic SOQL prevents runtime failures from unexpected input shapes
- `WITH USER_MODE` throws `QueryException` on inaccessible fields — predictable failure mode vs. silent data exposure (as did `WITH SECURITY_ENFORCED` on the classes that still carry it)
- `stripInaccessible` on DML prevents "field not updatable" errors in production when a permission set changes

**Tag a finding as Reliability when:**
- Dynamic SOQL fails in production because a field was removed or renamed (no allowlist validation)
- A permission set change causes existing code to throw unexpected `QueryException` because FLS enforcement was added but not tested

---

## Operational Excellence

**How it connects:**
- `@SuppressWarnings('PMD.ApexCRUDViolation')` with justification comments makes intentional bypasses auditable during security reviews
- Allowlists documented inline make it clear which fields/objects are expected to be queried dynamically — reduces onboarding risk
- `stripInaccessible` `getRemovedFields()` call in logging path provides observability into FLS enforcement in production

**Tag a finding as Operational Excellence when:**
- A PMD suppression lacks justification comment — no way to audit in a security review
- A `without sharing` class is discovered during an org security review with no explanation of why system context was needed

## Official Sources Used

Fetched and read on 2026-10-03 (release 262, Summer '26, API 67.0) unless marked.

- Apex Developer Guide, Version 67.0: Apex Security and Sharing Model, Use the with sharing, without sharing, and inherited sharing Keywords (Omitted Sharing, Implementation in Apex Triggers), Set an Access Mode for Database Operations, Enforce Security with the stripInaccessible Method, Dynamic SOQL, SOQL Injection Defenses, Apex Versioned Behavior Changes (Version 67.0), Using the runAs Method. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Apex Reference Guide, Version 67.0: Security Class (`stripInaccessible` overloads and `enforceRootObjectCRUD`), String Class (`escapeSingleQuotes`). https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_reference_guide.pdf
- SOQL and SOSL Reference, Version 67.0: SOQL SELECT Syntax and WITH (recommendation of `WITH USER_MODE` over `WITH SECURITY_ENFORCED`; the system-mode default sentence that conflicts with the Apex guide). https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_soql_sosl.pdf
- Salesforce Well-Architected: Secure (Trusted), archived 2026-07-11. http://web.archive.org/web/20260711090005/https://architect.salesforce.com/docs/architect/well-architected/guide/secure.html
- Salesforce Well-Architected Overview, archived 2026-06-16. http://web.archive.org/web/20260616115029/https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Canonical version table in this repository: `agents/_shared/AGENT_CONTRACT.md` § Apex security idiom by API version.
