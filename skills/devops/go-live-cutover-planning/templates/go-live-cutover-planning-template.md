# Go Live Cutover Planning — Cutover Runbook Template

Use this template when building a go-live cutover plan for a Salesforce deployment.

## Scope

**Skill:** `go-live-cutover-planning`

**Project name:** (fill in)

**Go-live date:** (fill in — confirm this does not conflict with Salesforce seasonal release windows)

**Cutover window:** (start time) to (end time), timezone: (fill in)

**Deployment method:** change sets / Salesforce CLI / unlocked packages (circle one)

---

## Stakeholders

| Role | Name | Contact | Responsibilities |
|---|---|---|---|
| Deployment Lead | | | Owns runbook execution, makes rollback decisions |
| Business Sponsor | | | Go/no-go sign-off, post-go-live business confirmation |
| QA Lead | | | UAT sign-off, smoke test execution |
| Support Lead | | | Hypercare staffing, escalation routing |
| Release Manager | | | Code freeze enforcement, validation deploy execution |

---

## Code Freeze

**Freeze date:** (fill in — typically 3-7 days before go-live)

**Enforcement mechanism:**
- [ ] Branch protection enabled on main (no direct push)
- [ ] PR merge requires release manager approval
- [ ] Emergency hotfix process documented

**Thaw date:** (fill in — typically after hypercare ends or after go-live confirmation)

---

## Validation Deploy

**Scheduled date:** (fill in — 2-5 days before cutover)

**Command:**
```bash
sf project deploy start --target-org prod --dry-run --test-level RunLocalTests
```

**Validated deploy ID:** (fill in after execution)

**Expiration date:** (validation date + 10 calendar days)

**Test results:**
- Total tests: ___
- Passed: ___
- Failed: ___
- Coverage: ___%

---

## Go/No-Go Checklist

Complete this checklist at the go/no-go meeting. All items must be checked to proceed.

| # | Criterion | Status | Approver |
|---|---|---|---|
| 1 | Validation deploy passed against production with 75%+ coverage | | Release Manager |
| 2 | Zero Apex test failures in validation deploy | | Release Manager |
| 3 | UAT sign-off received from business sponsor | | Business Sponsor |
| 4 | Data migration dry-run completed successfully in Full sandbox | | Data Lead |
| 5 | Rollback plan reviewed and approved | | Deployment Lead |
| 6 | Hypercare team confirmed and on-call schedule published | | Support Lead |
| 7 | End-user communication sent (downtime notice, new feature guide) | | Business Sponsor |
| 8 | Cutover window does not conflict with Salesforce maintenance | | Release Manager |

**Decision:** GO / NO-GO

**Decision date/time:**

**Decision maker:**

---

## Cutover Runbook

### Pre-Cutover Steps

| # | Step | Owner | Est. Duration | Verify | Rollback Trigger | Rollback Action |
|---|---|---|---|---|---|---|
| 1 | Send cutover-start notification to stakeholders | Deployment Lead | 5 min | Notification confirmed received | N/A | N/A |
| 2 | Disable outbound integrations (deactivate Named Credentials) | Integration Lead | 10 min | Callouts return "Named Credential inactive" | N/A | Re-enable Named Credentials |
| 3 | Put org in maintenance mode (if applicable) | Deployment Lead | 5 min | Users see maintenance message | N/A | Remove maintenance page |

### Deployment Steps

| # | Step | Owner | Est. Duration | Verify | Rollback Trigger | Rollback Action |
|---|---|---|---|---|---|---|
| 4 | Execute quick deploy | Release Manager | 10-30 min | Deployment Status shows "Succeeded" | Deploy fails or partial success | Investigate error; redeploy previous version |
| 5 | Activate record-triggered Flows (verify version and trigger order) | Automation Lead | 15 min | Test record triggers correct Flow version | Flow throws unhandled fault | Deactivate Flow, revert to previous version |
| 6 | Run post-deploy Apex scripts (if any) | Dev Lead | 15 min | Scripts complete without exceptions | Script fails with governor limit | Revert script data changes manually |
| 7 | Execute data migration jobs (if applicable) | Data Lead | 30-120 min | Record counts match, spot-check 50 records | >1% error rate | Delete migrated records, investigate |

### Post-Cutover Steps

| # | Step | Owner | Est. Duration | Verify | Rollback Trigger | Rollback Action |
|---|---|---|---|---|---|---|
| 8 | Run smoke test checklist | QA Lead | 30-60 min | All smoke tests pass | >2 critical smoke tests fail | Initiate full rollback |
| 9 | Re-enable outbound integrations | Integration Lead | 10 min | Integration test callout succeeds | Integration returns auth errors | Re-authenticate Named Credentials |
| 10 | Business sponsor walkthrough of critical paths | Business Sponsor | 30 min | Sponsor confirms functionality | Sponsor identifies blocking issue | Evaluate severity; rollback if P1 |
| 11 | Remove maintenance mode | Deployment Lead | 5 min | Users can access org normally | N/A | N/A |
| 12 | Send go-live-complete notification | Deployment Lead | 5 min | Notification confirmed received | N/A | N/A |

### Scheduled Job Verification

| Job Name | Type | Expected Next Run | Post-Deploy Status | Action Required |
|---|---|---|---|---|
| | Apex Scheduled | | | |
| | Scheduled Flow | | | |
| | Batch Job | | | |

---

## Rollback Plan

**Full rollback decision authority:** Deployment Lead

**Full rollback trigger:** (define the condition that triggers a complete rollback — e.g., >5 critical smoke test failures, data corruption detected, system inaccessible to users)

**Full rollback steps:**
1. (fill in — typically: redeploy previous metadata version, deactivate new Flows, restore data from backup)
2.
3.

**Rollback time estimate:** (fill in)

**Items that cannot be rolled back:** (list destructive changes, data migrations without backups, etc.)

---

## Hypercare Plan

**Hypercare period:** (go-live date) through (go-live + 14 days)

**On-call schedule:**

| Week | Primary On-Call | Secondary On-Call | Hours |
|---|---|---|---|
| Week 1 | | | Business hours + extended |
| Week 2 | | | Business hours |

**Monitoring checklist (daily during hypercare):**
- [ ] Setup Audit Trail — review changes since go-live
- [ ] Apex Exception Emails — check for unhandled exceptions
- [ ] Login History — verify user adoption rates
- [ ] Flow error report — filter errors since go-live date
- [ ] Batch/scheduled job completion — verify via Apex Jobs page
- [ ] Integration callout logs — check Named Credential success rates

**Escalation matrix:**

| Severity | Response Time | Escalation Path |
|---|---|---|
| P1 — System down / data loss | 30 minutes | On-call engineer → Deployment Lead → Business Sponsor |
| P2 — Feature broken | 4 hours | On-call engineer → Dev Lead |
| P3 — Cosmetic / minor | Next business day | Logged in backlog |

**Transition to steady-state:** (define criteria for ending hypercare — e.g., no P1/P2 issues for 5 consecutive business days)

---

## Notes

Record any deviations from the standard runbook and the reason for each deviation.
