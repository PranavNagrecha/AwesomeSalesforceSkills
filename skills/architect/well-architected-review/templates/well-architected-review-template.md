# Salesforce Well-Architected Framework Review

**Org / Solution:** [Org name or solution name]
**Review Date:** [YYYY-MM-DD]
**Review Type:** [ ] Full Org Review  [ ] Solution Design Review  [ ] Pre-Delivery Sign-off
**Reviewer(s):** [Name(s)]
**Stakeholder(s):** [Name(s) and role(s)]
**Next Review Due:** [YYYY-MM-DD or quarter]

---

## Executive Summary

[2–4 sentences summarising the overall WAF posture. Include the overall health (e.g., "The org is in a broadly Amber state, with one Red finding in the Trusted pillar requiring immediate attention and several Amber findings in the Easy and Adaptable pillars scheduled for remediation over the next two quarters.")]

**Overall Posture:** [ ] Red — Critical gaps present  [ ] Amber — Improvement needed  [ ] Green — Well-architected

---

## Org Profile

| Attribute | Value |
|-----------|-------|
| Salesforce Edition | [Enterprise / Unlimited / Developer / etc.] |
| Licensed Clouds | [Sales Cloud, Service Cloud, etc.] |
| Active Users | [Count] |
| Org Age | [Years since go-live] |
| Custom Objects | [Count] |
| Active Flows | [Count] |
| Apex Classes | [Count] |
| External Integrations | [Count and names] |
| Shield Enabled | [Yes / No / Partial] |
| MFA Enforced | [Yes / No / Partial] |
| Source Control | [Yes / No / Tool name] |
| Last Sandbox Refresh | [Date or "Unknown"] |
| Known Pain Points | [Brief list from pre-review questionnaire] |

---

## Summary Scorecard

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| Trusted | [Red / Amber / Green] | [One-line summary of the most significant finding] |
| Easy | [Red / Amber / Green] | [One-line summary of the most significant finding] |
| Adaptable | [Red / Amber / Green] | [One-line summary of the most significant finding] |

**Scoring guide:** Red = critical gap requiring immediate action. Amber = improvement needed, schedule within the quarter. Green = good practice, maintain and document.

---

## Trusted Pillar Review

The Trusted pillar covers security model integrity, compliance readiness, and authentication strength.

### Security Model

| Area | Finding | Severity | Recommendation |
|------|---------|----------|----------------|
| Sharing Model — OWDs | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |
| Sharing Rules | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |
| Role Hierarchy | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |
| Apex FLS Enforcement | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |
| `without sharing` Usage | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |

### Authentication and Identity

| Area | Finding | Severity | Recommendation |
|------|---------|----------|----------------|
| MFA Enforcement | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |
| SSO Configuration | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |
| Trusted IP Ranges | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |
| Integration User Credentials | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |

### Compliance and Data Classification

| Area | Finding | Severity | Recommendation |
|------|---------|----------|----------------|
| Data Classification Inventory | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |
| Regulated Data (GDPR/HIPAA/PCI) | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |
| Shield Assessment | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |
| Sandbox Data Masking | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |

**Trusted Pillar Score:** [Red / Amber / Green]

---

## Easy Pillar Review

The Easy pillar covers user experience quality, adoption signals, and process simplicity.

### User Experience

| Area | Finding | Severity | Recommendation |
|------|---------|----------|----------------|
| Lightning Page Performance | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |
| Page Layout Complexity | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |
| Mobile Readiness | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |
| Accessibility | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |
| Error Message Clarity | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |

### Adoption Signals

| Area | Finding | Severity | Recommendation |
|------|---------|----------|----------------|
| Field Usage Rates | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |
| Object Record Counts vs Licence Count | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |
| Report and Dashboard Activity | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |
| Abandoned Custom Objects | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |

### Process Simplicity

| Area | Finding | Severity | Recommendation |
|------|---------|----------|----------------|
| Manual Steps That Could Be Automated | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |
| Automation Overlap (Flows vs Apex vs Process Builder) | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |
| Approval Process Clarity | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |

**Easy Pillar Score:** [Red / Amber / Green]

---

## Adaptable Pillar Review

The Adaptable pillar covers scalability headroom, technical debt, and deployment pipeline maturity.

### Scalability and Governor Limits

| Area | Finding | Severity | Recommendation |
|------|---------|----------|----------------|
| Daily API Limit Headroom | [Finding — include % used at peak] | [Red/Amber/Green] | [Recommendation] |
| SOQL Row Limit in Peak Transactions | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |
| Heap Size in Batch Jobs | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |
| LDV Patterns on High-Volume Objects | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |
| Bulkification of Apex and Flows | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |

### Technical Debt

| Area | Finding | Severity | Recommendation |
|------|---------|----------|----------------|
| Apex Test Coverage (%) | [Finding — include actual % ] | [Red/Amber/Green] | [Recommendation] |
| Test Class Assertion Quality | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |
| Hardcoded IDs | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |
| API Version Currency | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |
| Configuration vs Code Ratio | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |
| Architecture Decision Documentation | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |

### Deployment Pipeline

| Area | Finding | Severity | Recommendation |
|------|---------|----------|----------------|
| Source Control | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |
| CI/CD Pipeline | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |
| Sandbox Refresh Cadence | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |
| Scratch Org Definition | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |
| Deployment Runbook | [Finding or "No issues found"] | [Red/Amber/Green] | [Recommendation] |

**Adaptable Pillar Score:** [Red / Amber / Green]

---

## Prioritized Recommendations

List all Red and Amber findings consolidated into a prioritized backlog. Green findings do not need to appear here unless they are dependencies for other items.

| Priority | Recommendation | Pillar | Effort | Owner | Target Date |
|----------|---------------|--------|--------|-------|-------------|
| 1 | [Most critical recommendation] | [Trusted/Easy/Adaptable] | [S/M/L/XL] | [Named role or person] | [YYYY-MM-DD] |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Effort guide:** S = hours to days. M = one sprint. L = one quarter. XL = multi-quarter program.

---

## Accepted Risks and Deferrals

Items that cannot be remediated before go-live (for Mode 3 reviews) or within the current planning cycle, accepted with documentation.

| Item | Reason for Deferral | Accepted By | Target Remediation Date |
|------|-------------------|-------------|------------------------|
| [Finding] | [Reason] | [Named individual and role] | [Date] |

---

## Sign-off

| Role | Name | Decision | Date |
|------|------|----------|------|
| Reviewer | [Name] | Approved / Conditional / Withheld | [Date] |
| Delivery Lead / Architect | [Name] | Acknowledged | [Date] |
| Stakeholder Sponsor | [Name] | Acknowledged | [Date] |

**Sign-off notes:** [Any conditions attached to approval, or reason for withholding]

**Next Review Date:** [YYYY-MM-DD]
**Next Review Owner:** [Named individual responsible for scheduling the next review]

---

*Generated using the Salesforce Well-Architected Review skill — `skills/architect/well-architected-review`*
*Official reference: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html*
