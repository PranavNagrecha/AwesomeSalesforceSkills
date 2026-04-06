# LLM Anti-Patterns — Security Architecture Review

Common mistakes AI coding assistants make when generating or advising on Salesforce security architecture reviews.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating Profile-Level Security as Sufficient Without Checking Apex CRUD/FLS Enforcement

**What the LLM generates:** "Security is handled by profiles and permission sets — users can only see and edit fields they have access to" without noting that Apex code runs in system mode by default and bypasses both CRUD and FLS checks unless the developer explicitly enforces them.

**Why it happens:** LLMs conflate declarative security (profile/permission set FLS) with runtime Apex security. Training data from admin-focused content assumes the UI enforces FLS, which is true for standard UI but not for Apex, Visualforce, or LWC with imperative Apex.

**Correct pattern:**

```text
A security architecture review must check BOTH layers:

1. Declarative: profiles, permission sets, OWD, sharing rules, FLS settings
2. Programmatic: Apex classes must enforce CRUD/FLS explicitly

Apex enforcement methods:
- WITH USER_MODE in SOQL (Spring '23+): SELECT Id FROM Account WITH USER_MODE
- Schema.SObjectType.Account.isAccessible() for CRUD checks
- Security.stripInaccessible() to remove fields the user cannot access
- WITH SECURITY_ENFORCED in SOQL (older pattern, throws exception on violation)

Flag any Apex class that queries or DMLs user-facing data without one of
these enforcement mechanisms.
```

**Detection hint:** Search Apex code for SOQL queries without `WITH USER_MODE` or `WITH SECURITY_ENFORCED`, and DML operations without `stripInaccessible()`. Flag classes that handle user-facing data in system mode.

---

## Anti-Pattern 2: Ignoring Connected App OAuth Scope Over-Provisioning

**What the LLM generates:** Connected App configurations with `full` or `api` scope without evaluating whether the integration actually needs access to all objects and all API capabilities, or recommending `refresh_token offline_access` without mentioning the risk of long-lived tokens.

**Why it happens:** Most integration tutorials and training data use `full` scope for simplicity. LLMs reproduce this pattern without applying the principle of least privilege to OAuth scopes.

**Correct pattern:**

```text
Security review checklist for Connected Apps:

1. Scope: use the minimum required scope, not "full"
   - api: REST/SOAP API access (most common need)
   - chatter_api: only if Chatter integration is needed
   - custom_permissions: use custom permissions for fine-grained access
   - Avoid: full, web (unless specific UI delegation is required)

2. Token policies:
   - Set refresh token expiration (not "until revoked" for sensitive integrations)
   - Enable IP relaxation only when required, prefer "Enforce IP restrictions"
   - Set session policy to "Admin approved users are pre-authorized" for
     server-to-server flows

3. Callback URL: restrict to actual callback endpoints, not wildcards
```

**Detection hint:** Flag Connected App configurations with `scope=full` or `refresh_token` policies set to "until revoked" without justification. Search for `<oauthConfig>` metadata with overly broad scopes.

---

## Anti-Pattern 3: Recommending Public OWD to Solve Query Performance Without Assessing Data Sensitivity

**What the LLM generates:** "Set the OWD to Public Read/Write to avoid sharing rule recalculation overhead and improve SOQL query performance" without evaluating whether the data contains sensitive information that requires record-level access control.

**Why it happens:** Public OWD is simpler and eliminates sharing-related performance issues. LLMs optimize for performance without weighing the security implications of making all records visible to all users.

**Correct pattern:**

```text
OWD decision must balance security and performance:

Use Private OWD when:
- Records contain PII, financial data, or competitive information
- Users should only see records they own or are shared with
- Regulatory requirements mandate record-level access control
- Territory or team-based visibility is required

Use Public Read Only / Public Read-Write when:
- All internal users should see all records on this object
- The object contains non-sensitive reference data
- Performance concerns outweigh access control needs AND data is not sensitive

NEVER set OWD to Public solely for performance. Instead:
- Optimize sharing rules (remove redundant ones)
- Use skinny tables for query performance on large objects
- Defer sharing recalculation to off-peak hours
```

**Detection hint:** Flag OWD change recommendations that cite "performance" without a data sensitivity assessment. Look for "Public Read/Write" recommendations on objects containing PII fields.

---

## Anti-Pattern 4: Missing Guest User Security in Experience Cloud Reviews

**What the LLM generates:** Security reviews of Experience Cloud (Community) sites that only check authenticated user permissions without auditing guest user profile access, guest user sharing rules, and public API access through the guest user context.

**Why it happens:** Guest user security is a Salesforce-specific attack surface that was the subject of multiple critical security advisories. General web security training data does not cover the Salesforce guest user model, and LLMs treat it as a standard unauthenticated user pattern.

**Correct pattern:**

```text
Experience Cloud security review MUST include guest user audit:

1. Guest User Profile: verify every object permission, FLS setting, and
   Apex class access on the guest user profile. Remove ALL unnecessary access.
2. Guest User Sharing Rules: check for sharing rules that expose records
   to the guest user. Disable "Secure guest user record access" setting review.
3. Public API access: verify that /services/data API endpoints are not
   accessible to unauthenticated users via the site.
4. Aura/LWC component exposure: check that components marked
   "Available for All Users" do not expose sensitive data or actions.
5. Apex controllers: verify that @AuraEnabled methods called by guest-facing
   components enforce CRUD/FLS and do not return sensitive records.

Salesforce critical update "Require Permission to View Record Names in
Lookup Fields" must be enabled for guest user contexts.
```

**Detection hint:** Flag Experience Cloud security reviews that do not include a dedicated "Guest User" section. Search for `@AuraEnabled` methods accessible to guest profiles without explicit CRUD/FLS checks.

---

## Anti-Pattern 5: Claiming Shield Platform Encryption Protects Against All Data Exposure

**What the LLM generates:** "Enable Shield Platform Encryption to protect sensitive data" as a comprehensive security recommendation, without noting that encryption at rest does not protect against authorized users viewing data through the UI, API, or reports.

**Why it happens:** LLMs conflate encryption-at-rest with access control. Shield Platform Encryption protects against database-level exposure (e.g., stolen backups, unauthorized infrastructure access) but does not restrict which authenticated users can see decrypted field values.

**Correct pattern:**

```text
Shield Platform Encryption scope:
- Protects: data at rest in the Salesforce database and backups
- Does NOT protect: data viewed by authorized users through UI, API, or reports
- Does NOT replace: FLS, CRUD checks, sharing rules, or data masking

A complete data protection strategy requires:
1. Shield Platform Encryption for at-rest protection (compliance mandate)
2. FLS and CRUD to restrict which users see which fields
3. Sharing rules to restrict which users see which records
4. Data Mask for non-production environments
5. Field-level masking (custom or AppExchange) for UI display of SSN, etc.
```

**Detection hint:** Flag Shield encryption recommendations that position it as a comprehensive data protection solution without mentioning FLS, sharing, and UI-level masking as complementary controls.

---

## Anti-Pattern 6: Skipping SOQL Injection Review in Dynamic Query Patterns

**What the LLM generates:** Security review checklists that focus on XSS and CSRF but omit SOQL injection, or that mention SOQL injection only for dynamic SOQL without also checking dynamic SOSL and dynamic DML.

**Why it happens:** SOQL injection is Salesforce-specific and less represented in general web security training data. LLMs apply generic web security checklists (XSS, CSRF, SQL injection) without adapting to Salesforce-specific injection vectors.

**Correct pattern:**

```text
Salesforce injection review checklist:
1. Dynamic SOQL: any string concatenation in Database.query() or
   Database.queryWithBinds() — use bind variables, not concatenation
2. Dynamic SOSL: Search.query() with user-supplied search terms —
   use String.escapeSingleQuotes() at minimum
3. Visualforce expressions: {!mergeField} in component attributes can
   enable XSS if the field contains user-controlled HTML
4. Lightning: verify that user input passed to Apex is sanitized
   before use in dynamic queries
5. SOQL injection in Flow: formula-based dynamic conditions in
   Get Records elements (rare but possible)

Use Salesforce Code Analyzer (sfdx scanner) to detect dynamic query
patterns that lack proper escaping.
```

**Detection hint:** Search for `Database.query(`, `Database.queryWithBinds(`, and `Search.query(` calls that use string concatenation with variables that could contain user input. Flag any that do not use bind variables or `escapeSingleQuotes()`.
