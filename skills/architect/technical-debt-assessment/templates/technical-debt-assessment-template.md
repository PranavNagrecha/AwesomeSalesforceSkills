# Technical Debt Assessment Report

**Org Name:** (Org nickname or Salesforce instance name)
**Assessment Date:** (YYYY-MM-DD)
**Conducted By:** (Name / Team)
**Assessment Scope:** (Full org audit | Targeted — specify area | Pre-release health check)
**Assessment Mode:** (Mode 1: Full | Mode 2: Targeted | Mode 3: Pre-release)

---

## 1. Org Profile

| Field | Value |
|---|---|
| Org Age | (Years in production) |
| Org Edition | (Enterprise / Unlimited / Developer / Scratch) |
| Approximate Custom Object Count | |
| Approximate Apex Class Count | |
| Approximate Active Flow Count | |
| Last Audit Date | (YYYY-MM-DD or "Never") |
| Managed Packages Installed | (List names, or "None") |
| Team Composition | (e.g., 3 admins, 2 developers, 1 architect) |
| Known Pain Points | (Free text — what brought this assessment about) |

---

## 2. Automation Audit Summary

### 2a. Automation Inventory by Type

| Automation Type | Active Count | Inactive Count | Draft/Archived Count | Notes |
|---|---|---|---|---|
| Record-Triggered Flows | | | | |
| Screen Flows | | | | |
| Scheduled Flows | | | | |
| Autolaunched Flows (other) | | | | |
| Process Builder Flows | | | | Active PBs are a migration finding |
| Workflow Rules | | | | Active WRs are a migration finding |
| Apex Triggers | | | | |

**Total Flow Version Count:** (Retrieved from Setup or Tooling API: `SELECT count() FROM FlowVersion`)
**Flow Version Limit:** 2,000
**Buffer Remaining:** (2,000 minus total)

If buffer is below 200: add High finding to section 8.

### 2b. Automation Overlap Risk Matrix

For each object with multiple active automation types, complete this table:

| Object | Automation Type 1 | Automation Type 2 | Shared Trigger Event? | Shared Field Write? | Overlap Severity |
|---|---|---|---|---|---|
| (e.g. Case) | Record-Triggered Flow | Apex Trigger | (Yes/No) | (Yes/No) | (Critical/High/Medium/Low/None) |
| | | | | | |
| | | | | | |

**Overlap findings count:** (Total entries with Severity above None)

---

## 3. Dead Code Summary

### 3a. Apex Coverage Overview

| Coverage Band | Class Count | Class Names |
|---|---|---|
| 0% coverage | | (List class names) |
| 1–74% coverage (below deployment minimum) | | |
| 75–84% coverage (passing but marginal) | | |
| 85%+ coverage (healthy) | | |

**Overall Org Coverage:** (%)
**Deployment minimum:** 75%

### 3b. Unreferenced Apex Classes

Classes identified as having no inbound references from other Apex, Flows, LWC wire calls, or scheduled jobs:

| Class Name | Last Modified | Coverage % | Recommended Action |
|---|---|---|---|
| | | | Delete / Verify / Keep |
| | | | |

### 3c. Test Classes with No Assertions (Coverage Theater)

| Class Name | Test Method Count | Assert Count | Recommended Action |
|---|---|---|---|
| | | 0 | Add assertions or delete |
| | | | |

---

## 4. Deprecated Features Inventory

| Feature | Status in This Org | Count Active | Migration Required? | Priority |
|---|---|---|---|---|
| Process Builder Flows | (Active / None) | | Yes — migrate to Flow | |
| Workflow Rules | (Active / None) | | Yes — migrate to Flow | |
| Aura Components (org-owned) | (Present / None) | | Recommended — migrate to LWC | |
| API Versions below v50.0 in Flows | (Present / None) | | Yes — upgrade API version | |
| API Versions below v50.0 in integrations | (Present / None) | | Yes — upgrade callout versions | |

### Deprecated Feature Notes

(Free text — any context on why deprecated features remain, who owns migration, known blockers)

---

## 5. Complexity Hotspots

### 5a. High-Complexity Apex

| Class Name | Estimated Cyclomatic Complexity | Lines of Code | Key Methods |
|---|---|---|---|
| | (> 20 = flag) | | |
| | | | |

Tool used for complexity measurement: (PMD / CodeScan / Manual review)

### 5b. Oversized Flows

| Flow API Name | Element Count | Subflow Depth | Recommended Action |
|---|---|---|---|
| | (> 50 = flag) | (> 3 levels = flag) | Decompose / Refactor / Accept |
| | | | |

### 5c. Trigger Handler Anti-Patterns

| Trigger File | Has Direct DML? | Has Direct SOQL? | Recommended Action |
|---|---|---|---|
| | (Yes/No) | (Yes/No) | Refactor to handler pattern |
| | | | |

### 5d. Data Model Issues

| Object | Issue Type | Field/Rule Name | Severity | Recommended Action |
|---|---|---|---|---|
| | Formula references deleted field | | Medium | Rebuild formula |
| | Validation rule always-true | | Medium | Remove or rewrite |
| | Validation rule always-false | | High | Investigate — rule never fires |
| | Duplicate objects same purpose | | High | Consolidate |

---

## 6. Security Configuration Indicators

These are indicators only — not full security findings. For a full security review, use `security-architecture-review`.

| Indicator | Details | Severity | Recommended Action |
|---|---|---|---|
| Profiles with View All Data outside Sys Admin | (List profiles) | High | Review and restrict |
| Profiles with Modify All Data outside Sys Admin | (List profiles) | High | Review and restrict |
| Permission sets with 0 assigned users | (List PS names) | Low | Delete or document |
| Apex classes running without sharing (undocumented) | (List class names) | High | Document justification or add with sharing |
| Validation rules with hardcoded user/profile IDs | (List rule names) | Medium | Replace with dynamic lookup or CMDT |

---

## 7. Integration Debt

| Indicator | Location | Severity | Recommended Action |
|---|---|---|---|
| Hardcoded endpoint URL | (Apex class or Custom Setting name) | High | Move to Named Credential |
| API version below v50.0 | (Integration name) | High | Upgrade to current API version |
| Hardcoded credentials in Apex | (Class name and line) | Critical | Move to Named Credential with OAuth |
| Named Credential using password auth instead of OAuth | (NC name) | Medium | Migrate to OAuth 2.0 auth provider |
| Unused Named Credentials | (NC name) | Low | Remove to reduce attack surface |

---

## 8. Prioritized Remediation Backlog

All findings from sections 2–7, consolidated and sorted by Severity then Effort.

| # | Area | Finding | Location | Severity | Effort | Owner |
|---|---|---|---|---|---|---|
| 1 | | | | Critical | | |
| 2 | | | | Critical | | |
| 3 | | | | High | | |
| 4 | | | | High | | |
| 5 | | | | High | | |
| 6 | | | | Medium | | |
| 7 | | | | Medium | | |
| 8 | | | | Low | | |

**Effort key:** XS = < 1 hour | S = 1–4 hours | M = 1–3 days | L = 1 week | XL = multi-sprint

**Owner key:** Admin | Developer | Architect | Release Manager | Vendor (managed package)

---

## 9. Summary Score

| Category | Finding Count | Critical | High | Medium | Low |
|---|---|---|---|---|---|
| Automation | | | | | |
| Dead Code | | | | | |
| Deprecated Features | | | | | |
| Complexity | | | | | |
| Security Config | | | | | |
| Integration | | | | | |
| **Total** | | | | | |

**Overall Debt Assessment:** (Healthy / Moderate / High / Critical)

**Recommended Next Step:**
(One paragraph summarizing the top 3 actions the team should take before any other work continues, and why.)

---

## 10. Notes and Exclusions

**Managed Package Debt (Informational Only — cannot be modified by org team):**

| Package Name | Namespace | Debt Type | Recommendation |
|---|---|---|---|
| | | (e.g., Active PB flow in package) | Contact vendor / Uninstall if unused |

**Known Exclusions:**
(Any areas explicitly out of scope for this assessment, and why)

**Assessment Methodology:**
- Static metadata scan using: `scripts/check_technical_debt.py`
- Manual Setup review for: (list areas)
- Tooling API queries for: (list queries run)
- Apex coverage report run: (Yes / No — date if yes)
