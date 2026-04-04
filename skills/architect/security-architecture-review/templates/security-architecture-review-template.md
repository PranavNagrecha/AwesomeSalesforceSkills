# Salesforce Security Architecture Review

## Review Metadata

| Property | Value |
|----------|-------|
| **Org Name** | TODO |
| **Org ID** | TODO |
| **Review Date** | TODO |
| **Reviewer(s)** | TODO |
| **Review Scope** | TODO: Full org / specific solution / pre-go-live / annual review |
| **Salesforce Edition** | TODO: Enterprise / Unlimited / Developer |
| **Clouds in Scope** | TODO: Sales Cloud, Service Cloud, Experience Cloud, etc. |
| **Regulatory Requirements** | TODO: HIPAA / PCI-DSS / GDPR / FedRAMP / SOC 2 / None |
| **Shield Licensed?** | TODO: Yes / No / Partial (list components) |

---

## Executive Summary

TODO: 3–5 sentence summary of the overall security posture. State the number of Critical, High, Medium, and Low findings. Indicate whether the org is suitable for production use, has conditional approval pending remediation of Critical/High findings, or requires significant work before go-live.

---

## Summary Scorecard

| Domain | Score | Critical | High | Medium | Low |
|--------|-------|----------|------|--------|-----|
| Sharing Model | TODO: Red / Amber / Green | 0 | 0 | 0 | 0 |
| FLS / CRUD Enforcement | TODO | 0 | 0 | 0 | 0 |
| Apex Security Patterns | TODO | 0 | 0 | 0 | 0 |
| API Surface / Connected Apps | TODO | 0 | 0 | 0 | 0 |
| Shield Needs Assessment | TODO | 0 | 0 | 0 | 0 |
| **Total** | | **0** | **0** | **0** | **0** |

**Score key:** Green = no Critical or High findings | Amber = High findings present, no Critical | Red = Critical findings present

---

## Domain 1: Sharing Model

### Checklist

| # | Check | Status | Severity | Notes |
|---|-------|--------|----------|-------|
| 1 | OWD settings documented and justified for all objects holding sensitive data | TODO: Pass / Fail / N/A | TODO | TODO |
| 2 | No sensitive object has OWD "Public Read/Write" without documented justification | TODO | TODO | TODO |
| 3 | All sharing rules reviewed — no rule matches >50% of records without justification | TODO | TODO | TODO |
| 4 | All Apex classes have explicit sharing declarations (`with sharing`, `without sharing`, or `inherited sharing`) | TODO | TODO | TODO |
| 5 | All `without sharing` classes have a documented reason | TODO | TODO | TODO |
| 6 | Experience Cloud external OWD reviewed for all objects accessible via the site | TODO | TODO | TODO |
| 7 | Manual shares reviewed — no unexplained accumulation of manual share records | TODO | TODO | TODO |

### Findings

| Finding | Severity | Recommendation |
|---------|----------|----------------|
| TODO | TODO | TODO |

---

## Domain 2: FLS and CRUD Enforcement

### Checklist

| # | Check | Status | Severity | Notes |
|---|-------|--------|----------|-------|
| 8 | All Apex querying sensitive fields uses `WITH USER_MODE`, `WITH SECURITY_ENFORCED`, or `stripInaccessible` | TODO | TODO | TODO |
| 9 | All DML in Apex uses `WITH USER_MODE` or confirms CRUD before write | TODO | TODO | TODO |
| 10 | All `@AuraEnabled` methods enforce FLS on fields returned to the LWC | TODO | TODO | TODO |
| 11 | Integration user profile/permission sets follow minimum necessary access | TODO | TODO | TODO |
| 12 | Visualforce pages displaying sensitive fields use explicit FLS checks | TODO | TODO | TODO |

### Findings

| Finding | Severity | Recommendation |
|---------|----------|----------------|
| TODO | TODO | TODO |

---

## Domain 3: Apex Security Patterns

### Checklist

| # | Check | Status | Severity | Notes |
|---|-------|--------|----------|-------|
| 13 | No dynamic SOQL using string concatenation with user-controlled input | TODO | TODO | TODO |
| 14 | No dynamic SOSL using string concatenation with user-controlled input | TODO | TODO | TODO |
| 15 | All Visualforce output of user-controlled strings is HTML-encoded | TODO | TODO | TODO |
| 16 | No hardcoded credentials, tokens, or secrets in Apex, Custom Labels, or accessible Custom Metadata | TODO | TODO | TODO |
| 17 | Async Apex (batch, future, queueable, scheduled) sharing declarations reviewed and justified | TODO | TODO | TODO |

### Findings

| Finding | Severity | Recommendation |
|---------|----------|----------------|
| TODO | TODO | TODO |

---

## Domain 4: API Surface and Connected Apps

### Checklist

| # | Check | Status | Severity | Notes |
|---|-------|--------|----------|-------|
| 18 | All Connected Apps with "Relax IP restrictions" have a documented justification | TODO | TODO | TODO |
| 19 | No Connected App has `full` or `api` scope when a narrower scope is sufficient | TODO | TODO | TODO |
| 20 | No Connected App has a never-expiring refresh token without compensating controls | TODO | TODO | TODO |
| 21 | All Connected Apps unused for 90+ days have been reviewed for deactivation | TODO | TODO | TODO |
| 22 | Named Credential certificates have documented expiry dates and renewal process | TODO | TODO | TODO |

### Findings

| Finding | Severity | Recommendation |
|---------|----------|----------------|
| TODO | TODO | TODO |

---

## Domain 5: Shield Needs Assessment

### Assessment Table

| Criterion | Applicable? | Shield Component |
|-----------|-------------|-----------------|
| Org holds HIPAA-regulated PHI | TODO: Yes / No | Event Monitoring, Field Audit Trail, Platform Encryption |
| Org holds PCI-DSS cardholder data | TODO | Event Monitoring, Field Audit Trail, Platform Encryption |
| Org subject to FedRAMP | TODO | All three components |
| SOC 2 Type II audit scope | TODO | Event Monitoring, Field Audit Trail recommended |
| 500+ users with data export access | TODO | Event Monitoring recommended |
| Fields store SSN, passport, or financial account numbers | TODO | Platform Encryption, Field Audit Trail recommended |
| Org has experienced a data breach | TODO | All three components required |

### Shield Recommendation

TODO: State whether Shield licensing is Required, Recommended, or Not currently required. Specify which components and the primary justification. If not currently required, state the conditions under which a reassessment would be needed.

---

## Prioritized Remediation Backlog

| Priority | Finding | Domain | Severity | Owner | Target Date |
|----------|---------|--------|----------|-------|------------|
| 1 | TODO | TODO | Critical | TODO | TODO |
| 2 | TODO | TODO | Critical | TODO | TODO |
| 3 | TODO | TODO | High | TODO | TODO |
| 4 | TODO | TODO | High | TODO | TODO |
| 5 | TODO | TODO | Medium | TODO | TODO |

---

## Accepted Risks

Document any findings that cannot be remediated before go-live (or within the standard SLA) and have been formally accepted by a named owner.

| Finding | Severity | Reason for Acceptance | Risk Owner | Review Date |
|---------|----------|-----------------------|------------|-------------|
| TODO | TODO | TODO | TODO | TODO |

---

## Next Review

Recommended next security architecture review date: TODO

Recommended trigger conditions for an unscheduled review:
- Any regulatory requirement change (new HIPAA BAA, PCI scoping change, etc.)
- Addition of Experience Cloud site or external user community
- Significant new integration or Connected App
- Security incident or unauthorized data access event
- Org headcount increase above 100 new users
