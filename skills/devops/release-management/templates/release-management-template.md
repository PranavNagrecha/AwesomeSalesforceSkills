# Release Management — Release Plan Template

Use this template to document a Salesforce release before deployment.

## Release Identification

**Release Name / Version:** (e.g., `v2026.04-R1` or `Winter '26 Feature Release`)
**Target Deployment Date:**
**Target Org:**
**Deployment Model:** [ ] Org-based (SFDX deploy) [ ] Unlocked Package [ ] 2GP Managed Package

---

## Scope

| Component | Type | Change Summary | Owner |
|---|---|---|---|
| (e.g., AccountTrigger) | ApexClass | Added null check for BillingState | (developer name) |

---

## Pre-Deployment Checklist

- [ ] All components listed in scope table
- [ ] Pre-release backup manifest (`pre-release-backup.xml`) retrieved and stored in `backups/YYYY-MM-DD/`
- [ ] Validation deploy passed against production (deploy ID: `_____________`, valid through: `_____________`)
- [ ] All Apex test failures from validation resolved
- [ ] UAT sign-off obtained from product owner
- [ ] Zero open Severity-1 defects
- [ ] Salesforce upgrade weekend checked at trust.salesforce.com — no overlap with deployment date

---

## Go / No-Go Criteria

| Criterion | Status |
|---|---|
| All Apex tests pass (≥75% org-wide or per-class coverage) | [ ] Pass / [ ] Fail |
| Validation deploy succeeded within last 10 days | [ ] Pass / [ ] Fail |
| UAT complete with product owner sign-off | [ ] Pass / [ ] Fail |
| Zero open Sev-1 defects | [ ] Pass / [ ] Fail |
| Pre-release backup stored | [ ] Pass / [ ] Fail |

**Go / No-Go Decision:** [ ] GO [ ] NO-GO

---

## Rollback Trigger Definition

Rollback will be initiated if any of the following occurs within 2 hours of deployment:
- [ ] Apex test failure in production post-deploy
- [ ] ___Sev-1 defects raised by users
- [ ] ____________________________________________ (org-specific trigger)

**Rollback procedure:**
1. `sf project deploy start --manifest backups/YYYY-MM-DD/pre-release-backup.xml --test-level RunSpecifiedTests --tests <affected test classes>`
2. Confirm rollback succeeded — run smoke tests
3. Notify stakeholders of rollback

---

## Post-Deployment Smoke Tests

| Test | Expected Result | Actual Result | Status |
|---|---|---|---|
| (e.g., Create new Account) | Account creates without error | | [ ] Pass / [ ] Fail |
| (e.g., Trigger business rule) | Expected automation fires | | [ ] Pass / [ ] Fail |

---

## Sign-Off

| Role | Name | Date | Signature |
|---|---|---|---|
| Developer / Release Lead | | | |
| Product Owner / BA | | | |
| QA / UAT Lead | | | |
