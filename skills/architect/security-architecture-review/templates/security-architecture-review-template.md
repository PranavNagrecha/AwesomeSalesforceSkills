# Salesforce Security Architecture Review

## Review Metadata

| Property | Value |
|----------|-------|
| **Org Name** | <fill in> |
| **Org ID** | <fill in> |
| **Review Date** | <fill in> |
| **Reviewer(s)** | <fill in> |
| **Review Scope** | <fill in: Full org / specific solution / pre-go-live / annual review> |
| **Salesforce Edition** | <fill in: Enterprise / Unlimited / Developer> |
| **Clouds in Scope** | <fill in: Sales Cloud, Service Cloud, Experience Cloud, etc.> |
| **Regulatory Requirements** | <fill in: HIPAA / PCI-DSS / GDPR / FedRAMP / SOC 2 / None> |
| **Shield Licensed?** | <fill in: Yes / No / Partial (list components)> |

---

## Executive Summary

<fill in: 3–5 sentence summary of the overall security posture. State the number of Critical, High, Medium, and Low findings. Indicate whether the org is suitable for production use, has conditional approval pending remediation of Critical/High findings, or requires significant work before go-live.>

---

## Summary Scorecard

| Domain | Score | Critical | High | Medium | Low |
|--------|-------|----------|------|--------|-----|
| Sharing Model | <fill in: Red / Amber / Green> | 0 | 0 | 0 | 0 |
| FLS / CRUD Enforcement | <fill in> | 0 | 0 | 0 | 0 |
| Apex Security Patterns | <fill in> | 0 | 0 | 0 | 0 |
| API Surface / Connected Apps | <fill in> | 0 | 0 | 0 | 0 |
| Shield Needs Assessment | <fill in> | 0 | 0 | 0 | 0 |
| **Total** | | **0** | **0** | **0** | **0** |

**Score key:** Green = no Critical or High findings | Amber = High findings present, no Critical | Red = Critical findings present

---

## Domain 1: Sharing Model

### Checklist

| # | Check | Status | Severity | Notes |
|---|-------|--------|----------|-------|
| 1 | OWD settings documented and justified for all objects holding sensitive data | <fill in: Pass / Fail / N/A> | <fill in> | <fill in> |
| 2 | No sensitive object has OWD "Public Read/Write" without documented justification | <fill in> | <fill in> | <fill in> |
| 3 | All sharing rules reviewed — no rule matches >50% of records without justification | <fill in> | <fill in> | <fill in> |
| 4 | All Apex classes have explicit sharing declarations (`with sharing`, `without sharing`, or `inherited sharing`) — record each class's `apiVersion`, since an absent keyword means *without sharing* at ≤66.0 and *with sharing* at 67.0+ | <fill in> | <fill in> | <fill in> |
| 5 | All `without sharing` classes have a documented reason | <fill in> | <fill in> | <fill in> |
| 6 | Experience Cloud external OWD reviewed for all objects accessible via the site | <fill in> | <fill in> | <fill in> |
| 7 | Manual shares reviewed — no unexplained accumulation of manual share records | <fill in> | <fill in> | <fill in> |

### Findings

| Finding | Severity | Recommendation |
|---------|----------|----------------|
| <fill in> | <fill in> | <fill in> |

---

## Domain 2: FLS and CRUD Enforcement

### Checklist

| # | Check | Status | Severity | Notes |
|---|-------|--------|----------|-------|
| 8 | All Apex querying sensitive fields uses `WITH USER_MODE` or `Security.stripInaccessible(...).getRecords()` — or is pinned at `apiVersion` 67.0+, where user mode is the default. `WITH SECURITY_ENFORCED` is a finding, not a pass: legacy at 57.0–66.0, non-compiling at 67.0+ | <fill in> | <fill in> | <fill in> |
| 9 | All DML in Apex uses `as user` / `AccessLevel.USER_MODE`, confirms CRUD before write, or runs at `apiVersion` 67.0+ where user mode is the default | <fill in> | <fill in> | <fill in> |
| 10 | All `@AuraEnabled` methods enforce FLS on fields returned to the LWC | <fill in> | <fill in> | <fill in> |
| 11 | Integration user profile/permission sets follow minimum necessary access | <fill in> | <fill in> | <fill in> |
| 12 | Visualforce pages displaying sensitive fields use explicit FLS checks | <fill in> | <fill in> | <fill in> |

### Findings

| Finding | Severity | Recommendation |
|---------|----------|----------------|
| <fill in> | <fill in> | <fill in> |

---

## Domain 3: Apex Security Patterns

### Checklist

| # | Check | Status | Severity | Notes |
|---|-------|--------|----------|-------|
| 13 | No dynamic SOQL using string concatenation with user-controlled input | <fill in> | <fill in> | <fill in> |
| 14 | No dynamic SOSL using string concatenation with user-controlled input | <fill in> | <fill in> | <fill in> |
| 15 | All Visualforce output of user-controlled strings is HTML-encoded | <fill in> | <fill in> | <fill in> |
| 16 | No hardcoded credentials, tokens, or secrets in Apex, Custom Labels, or accessible Custom Metadata | <fill in> | <fill in> | <fill in> |
| 17 | Async Apex (batch, future, queueable, scheduled) sharing declarations reviewed and justified | <fill in> | <fill in> | <fill in> |

### Findings

| Finding | Severity | Recommendation |
|---------|----------|----------------|
| <fill in> | <fill in> | <fill in> |

---

## Domain 4: API Surface and Connected Apps

### Checklist

| # | Check | Status | Severity | Notes |
|---|-------|--------|----------|-------|
| 18 | All Connected Apps with "Relax IP restrictions" have a documented justification | <fill in> | <fill in> | <fill in> |
| 19 | No Connected App has `full` or `api` scope when a narrower scope is sufficient | <fill in> | <fill in> | <fill in> |
| 20 | No Connected App has a never-expiring refresh token without compensating controls | <fill in> | <fill in> | <fill in> |
| 21 | All Connected Apps unused for 90+ days have been reviewed for deactivation | <fill in> | <fill in> | <fill in> |
| 22 | Named Credential certificates have documented expiry dates and renewal process | <fill in> | <fill in> | <fill in> |

### Findings

| Finding | Severity | Recommendation |
|---------|----------|----------------|
| <fill in> | <fill in> | <fill in> |

---

## Domain 5: Shield Needs Assessment

### Assessment Table

| Criterion | Applicable? | Shield Component |
|-----------|-------------|-----------------|
| Org holds HIPAA-regulated PHI | <fill in: Yes / No> | Event Monitoring, Field Audit Trail, Platform Encryption |
| Org holds PCI-DSS cardholder data | <fill in> | Event Monitoring, Field Audit Trail, Platform Encryption |
| Org subject to FedRAMP | <fill in> | All three components |
| SOC 2 Type II audit scope | <fill in> | Event Monitoring, Field Audit Trail recommended |
| 500+ users with data export access | <fill in> | Event Monitoring recommended |
| Fields store SSN, passport, or financial account numbers | <fill in> | Platform Encryption, Field Audit Trail recommended |
| Org has experienced a data breach | <fill in> | All three components required |

### Shield Recommendation

<fill in: State whether Shield licensing is Required, Recommended, or Not currently required. Specify which components and the primary justification. If not currently required, state the conditions under which a reassessment would be needed.>

---

## Prioritized Remediation Backlog

| Priority | Finding | Domain | Severity | Owner | Target Date |
|----------|---------|--------|----------|-------|------------|
| 1 | <fill in> | <fill in> | Critical | <fill in> | <fill in> |
| 2 | <fill in> | <fill in> | Critical | <fill in> | <fill in> |
| 3 | <fill in> | <fill in> | High | <fill in> | <fill in> |
| 4 | <fill in> | <fill in> | High | <fill in> | <fill in> |
| 5 | <fill in> | <fill in> | Medium | <fill in> | <fill in> |

---

## Accepted Risks

Document any findings that cannot be remediated before go-live (or within the standard SLA) and have been formally accepted by a named owner.

| Finding | Severity | Reason for Acceptance | Risk Owner | Review Date |
|---------|----------|-----------------------|------------|-------------|
| <fill in> | <fill in> | <fill in> | <fill in> | <fill in> |

---

## Next Review

Recommended next security architecture review date: <fill in>

Recommended trigger conditions for an unscheduled review:
- Any regulatory requirement change (new HIPAA BAA, PCI scoping change, etc.)
- Addition of Experience Cloud site or external user community
- Significant new integration or Connected App
- Security incident or unauthorized data access event
- Org headcount increase above 100 new users
