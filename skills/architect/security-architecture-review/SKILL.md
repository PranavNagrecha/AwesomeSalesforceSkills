---
name: security-architecture-review
description: "Use when conducting a dedicated security architecture review of a Salesforce org — assessing sharing model completeness, FLS/CRUD enforcement, Apex security patterns, exposed API surface, Connected App policies, and Shield readiness. Produces a structured findings report with severity ratings (Critical/High/Medium/Low) and a 20+ point review checklist. Triggers: security architecture review, org security posture, sharing model audit, FLS coverage review, Connected App security, Shield assessment, org security health deep-dive, HIPAA or PCI security controls Salesforce. NOT for implementing security fixes (use security/* skills). NOT for the Salesforce Security Health Check UI (use security-health-check skill). NOT for a full WAF review across all pillars (use well-architected-review)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
tags:
  - security
  - sharing-model
  - fls
  - apex-security
  - connected-apps
  - shield
triggers:
  - "review the security architecture of this org"
  - "audit the sharing model and OWD settings"
  - "check FLS and CRUD enforcement in Apex"
  - "assess Connected App OAuth scopes and session policies"
  - "does this org need Salesforce Shield?"
  - "security posture review before go-live"
  - "HIPAA or PCI compliance review for Salesforce"
  - "identify over-permissioned profiles and permission sets"
  - "check for SOQL injection risks in Apex"
  - "review community or Experience Cloud external sharing"
inputs:
  - Org type (production, sandbox, scratch) and Salesforce edition
  - Clouds and features in scope (Sales, Service, Experience Cloud, etc.)
  - Regulatory or compliance requirements (HIPAA, PCI-DSS, GDPR, FedRAMP, SOC 2)
  - Known security concerns or recent incidents
  - List of integration endpoints and Connected Apps (if available)
  - Whether Shield (Event Monitoring, Field Audit Trail, Platform Encryption) is licensed
outputs:
  - Security architecture review report with findings per domain area
  - Severity-rated findings table (Critical / High / Medium / Low)
  - 20+ point security checklist with pass/fail/not-applicable status
  - Shield needs assessment (criteria met, recommendation, justification)
  - Prioritized remediation backlog
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

Use this skill when you need a dedicated, deep-dive security architecture review of a Salesforce org. Where the `well-architected-review` skill surveys all three WAF pillars at breadth, this skill goes deep on the Trusted pillar — examining the sharing model, field-level security, Apex code security patterns, API exposure, Connected App configuration, and Shield licensing decisions. It produces a structured findings report with severity ratings and a comprehensive checklist, suitable for delivery to a security team, a compliance officer, or an architecture review board.

This skill does not cover implementation of fixes. Once findings are identified, route to `apex/apex-security-patterns`, `apex/soql-security`, or `security/` domain skills for remediation guidance.

---

## Before Starting

- **What is the scope?** Full org or a specific solution/integration? Scope determines which checklist sections are mandatory.
- **What are the regulatory requirements?** HIPAA, PCI-DSS, GDPR, FedRAMP, and SOC 2 each have specific control requirements that shape which findings are Critical vs Low.
- **Is Shield licensed?** Event Monitoring, Field Audit Trail, and Platform Encryption are add-ons. The review will assess whether they are needed even if not yet licensed.
- **Are there external users?** Experience Cloud sites change the OWD calculation — external OWD settings are independent of internal OWD and are frequently misconfigured.
- **What integrations exist?** REST/SOAP APIs, Connected Apps, and named credentials each have their own exposure surface.

---

## Review Domains

### Domain 1: Sharing Model Completeness

The sharing model defines who can see and modify which records. A misconfigured sharing model is one of the highest-impact security risks in a Salesforce org because it is difficult to audit retrospectively and often grows more permissive over time.

**Checklist items:**

1. **OWD settings per object** — Every custom object and every standard object holding sensitive data must have its OWD documented and justified. "Public Read/Write" on objects holding financial, health, or personal data is a Critical finding. "Public Read Only" on those same objects is High unless a specific business reason is documented.

2. **Sharing rules coverage** — Are sharing rules granting access beyond the role hierarchy? Review each sharing rule: criteria-based rules can grant overly broad access if the criteria are poorly designed. Role-and-subordinates sharing rules grow in scope as the role hierarchy expands.

3. **With sharing / without sharing Apex** — Every Apex class that performs DML or queries should have an explicit sharing declaration. Classes using `without sharing` should be documented with a reason. Classes using `inherited sharing` should be traced to their caller chain to confirm the caller enforces sharing.

4. **Community / Experience Cloud external OWD** — External OWD settings are separate from internal OWD. An object set to "Private" internally can be "Public Read Only" externally if the external OWD was not set explicitly. Review all objects accessible in Experience Cloud sites against their external OWD.

5. **Manual sharing and Share objects** — Review whether manual shares (`AccountShare`, `OpportunityShare`, etc.) are present at scale. Manual shares are invisible in standard UI reports and can accumulate over years without review.

6. **Role hierarchy depth and scope** — An overly flat hierarchy grants broad data visibility to senior roles. Review whether roles at the top of the hierarchy genuinely need visibility to all subordinate records or whether territory management or criteria-based sharing would be more appropriate.

---

### Domain 2: Field-Level Security and CRUD Enforcement

Field-Level Security (FLS) controls which fields individual users can read and write. CRUD controls whether they can create, read, update, or delete records of a given object. Violations allow authenticated users to read or modify data they should not access, even if the sharing model is correct.

**Checklist items:**

7. **FLS enforcement in Apex** — Apex running in system context bypasses FLS by default. Review all Apex classes that read or write sensitive fields. Enforcement mechanisms: `WITH SECURITY_ENFORCED` in SOQL, `WITH USER_MODE` on DML statements (available in API 56.0+, Summer '22), or `Security.stripInaccessible()` before DML.

8. **CRUD enforcement in Apex** — Before performing DML, Apex should verify the current user has create/read/update/delete permission on the object. Use `Schema.sObjectType.describe().isAccessible()` or rely on `WITH USER_MODE` DML.

9. **AuraEnabled and LWC wire methods** — `@AuraEnabled` methods and wire adapters backed by Apex run in system context if the class uses `with sharing` without FLS checks. Review all `@AuraEnabled` methods for FLS enforcement on fields returned to the UI.

10. **Integration user FLS** — Integration users (named credentials, connected app users) often have broad profiles because they "need access to everything." Review the integration user's profile and permission sets against the minimum necessary access principle. A CRUD-level over-permission on an integration user is a High finding.

11. **Visualforce and field references** — Visualforce pages that reference fields via `{!record.Field__c}` will render even if the running user has no FLS read permission on that field — Visualforce does not enforce FLS automatically. Any VF page displaying sensitive fields must use `$ObjectType.describe()` checks or be replaced with an LWC that enforces FLS server-side.

---

### Domain 3: Apex Security Patterns

Insecure Apex code can bypass the sharing model, enable data exfiltration, or allow privilege escalation. Review focuses on injection, encoding, and system-context risks.

**Checklist items:**

12. **SOQL injection** — Dynamic SOQL built by string concatenation with user-supplied input is a Critical finding. Check all classes that use `Database.query()` with string variables that originate from user input, URL parameters, or external system payloads. Remediation: use bind variables or `String.escapeSingleQuotes()`.

13. **SOSL injection** — Same pattern as SOQL but for `Search.query()`. Less common but equally severe.

14. **Encoding in Visualforce** — All output rendered in Visualforce should use `{!HTMLENCODE(value)}` or equivalent. Unencoded output of user-controlled strings enables stored XSS.

15. **Hardcoded credentials and sensitive strings** — Passwords, tokens, client secrets, and encryption keys must not be stored in Apex code, Custom Labels, or Custom Metadata that is accessible to all users. Use Named Credentials for endpoint authentication and Protected Custom Metadata for secrets.

16. **System-context callouts** — Apex making callouts in system context (batch jobs, future methods, platform events) should be reviewed to confirm they do not relay data the calling user could not access directly.

---

### Domain 4: API Surface and Connected Apps

Every Connected App is an OAuth entry point. Misconfigured Connected Apps allow credential theft, session hijacking, and unauthorized data export.

**Checklist items:**

17. **IP relaxation on Connected Apps** — Connected Apps with "Relax IP restrictions" allow access from any IP address without MFA step-up. This is a High finding for any app not explicitly approved for IP-unrestricted access. Review each Connected App's IP policy.

18. **OAuth scope breadth** — Connected Apps with `full` or `api` scope have unrestricted access to all objects the authorized user can access. Review whether each app's scope can be narrowed. A Connected App used only for reading Account data should not hold `full` scope.

19. **Session policy and token lifetime** — Review session security level and token validity settings per Connected App. Refresh tokens that never expire combined with IP relaxation are a Critical finding for apps holding sensitive data.

20. **Unused or dormant Connected Apps** — Connected Apps that have not been used in 90+ days should be reviewed for deactivation. Each dormant app is a latent attack surface.

21. **Named Credential certificate management** — Named Credentials using JWT or certificate-based auth should have documented certificate expiry dates and a renewal process. Expired certificates cause integration failures; unrotated credentials are a security risk.

---

### Domain 5: Shield Needs Assessment

Salesforce Shield comprises three capabilities: Event Monitoring, Field Audit Trail, and Platform Encryption. This domain assesses whether the org's data profile and compliance obligations require Shield.

**Assessment criteria:**

| Criterion | Event Monitoring | Field Audit Trail | Platform Encryption |
|-----------|-----------------|------------------|---------------------|
| Org holds HIPAA-regulated PHI | Required | Required | Required |
| Org holds PCI-DSS cardholder data | Required | Required | Required |
| Org subject to FedRAMP | Required | Required | Required |
| SOC 2 Type II audit scope | Recommended | Recommended | Recommended |
| Org has 500+ users with data export access | Recommended | Not required | Not required |
| Fields store SSN, passport, or financial account numbers | Not required | Recommended | Required |
| Org has experienced a data breach | Required | Required | Recommended |

If two or more "Required" criteria are met, a Shield licensing conversation is a Critical finding. If only "Recommended" criteria are met, it is a Medium finding with a recommendation to evaluate Shield.

---

## Severity Rating Definitions

| Severity | Definition | Expected Response |
|----------|-----------|------------------|
| Critical | Exploitable risk with high likelihood or high impact on regulated data | Remediate before go-live or within 72 hours in production |
| High | Significant risk or compliance gap not yet exploited | Remediate within the current sprint or within 2 weeks |
| Medium | Risk present but requires additional conditions to exploit | Schedule remediation within the quarter |
| Low | Best-practice deviation with minimal exploitability | Address in next maintenance cycle |

---

## Review Sequence

1. Gather inputs (see frontmatter inputs section above).
2. Complete the 21-point checklist across all five domains.
3. Rate each finding (Critical / High / Medium / Low / N/A).
4. Complete the Shield Needs Assessment table.
5. Produce the findings report: findings table, Shield recommendation, and prioritized remediation backlog.
6. Route Critical and High findings to appropriate `security/` or `apex/` skills for remediation.

---

## Related Skills

- `architect/well-architected-review` — full WAF review across all three pillars; use as the entry point before this skill for a new org assessment
- `apex/apex-security-patterns` — with/without/inherited sharing patterns, stripInaccessible, FLS enforcement in Apex
- `apex/soql-security` — SOQL injection prevention, bind variables, dynamic SOQL review
- `security/connected-app-security` — Connected App OAuth configuration, IP restrictions, scope management (if that skill exists)

---

## Official Sources Used

- Salesforce Well-Architected: Trusted — https://architect.salesforce.com/docs/architect/well-architected/guide/trusted.html
- Salesforce Well-Architected Framework Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Secure Apex Classes (Apex Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_perms_enforcing.htm
- Apex Security and Sharing — https://developer.salesforce.com/docs/platform/lwc/guide/apex-security
- Salesforce Sharing Model — https://help.salesforce.com/s/articleView?id=sf.sharing_model.htm
- Connected App Overview — https://help.salesforce.com/s/articleView?id=sf.connected_app_overview.htm
- Salesforce Shield Overview — https://help.salesforce.com/s/articleView?id=sf.security_shield.htm

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

