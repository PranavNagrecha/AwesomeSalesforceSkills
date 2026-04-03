# SOQL Security — Well-Architected Mapping

## Security

**Directly implements:**
- SOQL injection prevention protects against data exfiltration and manipulation via crafted queries
- FLS/CRUD enforcement ensures users can only access data their permission set allows — prevents privilege escalation through Apex code
- `WITH USER_MODE` / `WITH SECURITY_ENFORCED` / `stripInaccessible` are the three Salesforce-native FLS enforcement mechanisms

**Tag a finding as Security when:**
- `Database.query()` concatenates any variable that originates from user input, URL parameters, or deserialized JSON
- An `@AuraEnabled` or REST endpoint method queries or mutates records without FLS enforcement
- A `without sharing` class performs SOQL/DML on sensitive objects without documented justification

---

## Reliability

**How it connects:**
- Allowlist validation for dynamic SOQL prevents runtime failures from unexpected input shapes
- `WITH SECURITY_ENFORCED` throws `QueryException` on inaccessible fields — predictable failure mode vs. silent data exposure
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

- Salesforce Well-Architected Overview — security and audit framing for data-access design
- Apex Developer Guide — secure query and transaction behavior guidance
- Apex Reference Guide — query, security API, and language reference confirmation
- Secure Apex Classes — component-facing sharing and CRUD/FLS enforcement patterns
