# Deployment Risk Assessment — Work Template

Use this template when assessing the risk of an upcoming Salesforce production deployment.
Fill every section before the deployment window opens. Incomplete sections block go/no-go sign-off.

---

## Scope

**Release name / ticket:**
**Deployment date and window:**
**Deployment method:** (Change Sets / DevOps Center / SFDX CLI / Unlocked Package / Other)
**Release manager:**
**Rollback authority (named individual):**
**Rollback alternate (named individual):**

---

## Context Gathered

Answer these before proceeding to classification:

- **Promotion path used:** (list each environment and validation date)
- **Does each sandbox match current production metadata state?** (yes / no — if no, describe delta)
- **Pre-retrieve backup location:** (path or "not yet captured — REQUIRED before window opens")
- **Prior package version (if applicable):**
- **Business impact of a 1-hour outage during this window:**

---

## Risk-Classified Component Inventory

Complete one row per metadata component or component group.

| Component (type: name) | Classification | Risk Indicator | Rollback Asset Available? |
|---|---|---|---|
| (e.g. PermissionSet: Financial_Data_Viewer) | HIGH | Affects FLS on financial object; no feature flag | Pre-retrieve backup: .rollback-backup/2026-04-13 |
| (e.g. Flow: Opportunity_Close_Date_Validation) | HIGH | Bulk-affecting; no prior version gating | Feature flag: Enable_Close_Date_Validation CP |
| (e.g. Layout: Account-Account Layout) | LOW | UI-only; no automation dependency | Not required |

**Overall release risk level:** HIGH / MEDIUM / LOW
*(Highest individual component rating drives the overall level)*

---

## Rollback Plan

### Trigger Conditions

List the exact observable conditions that authorize the rollback call. Each condition must be measurable.

| Trigger | Measurement Source | Threshold |
|---|---|---|
| (e.g. Apex exception on OpportunityTrigger) | Setup > Apex Exception Email | >50 exceptions in 5 minutes |
| (e.g. Integration endpoint latency) | Monitoring dashboard | >10 seconds for 3 consecutive calls |

### Rollback Procedure

**For org-based deployments (Change Set / CLI):**

1. Locate pre-retrieve backup at: _______________
2. Run:
   ```bash
   sf project deploy start \
     --source-dir .rollback-backup/YYYY-MM-DD \
     --target-org production
   ```
3. Estimated execution time: _______________ minutes
4. Post-rollback smoke test: _______________

**For unlocked package deployments:**

1. Prior package version to install: _______________
2. Run:
   ```bash
   sf package install \
     --package <prior-version-id> \
     --target-org production \
     --wait 20
   ```
3. Estimated execution time: _______________ minutes
4. Data side effects to address: _______________
5. Post-rollback smoke test: _______________

### Monitoring Period

**How long will the team monitor after deployment before declaring stable:** _______________ hours/minutes
**Who is on call for the monitoring period:**

---

## Pre-Deployment Checklist (go/no-go gates)

### People
- [ ] Release manager confirmed available for full window and monitoring period
- [ ] Rollback authority (named individual) confirmed available and reachable
- [ ] Rollback alternate confirmed available and reachable
- [ ] Technical executor confirmed available and has deployment access

### Process
- [ ] All components have been classified HIGH / MEDIUM / LOW with documented rationale
- [ ] Rollback trigger conditions are observable and measurable (no subjective language)
- [ ] Rollback procedure is documented with exact commands and estimated time
- [ ] Post-rollback smoke test is defined
- [ ] Any HIGH-risk component without a feature flag has a tested destructive change file prepared

### Technology
- [ ] Pre-retrieve backup captured from production immediately before window (org-based deploys)
- [ ] Prior package version number recorded and accessible (packaged deploys)
- [ ] All sandbox validations completed at current production metadata state
- [ ] No unresolved metadata dependency warnings from the validation run
- [ ] Deployment artifact is the exact package validated — no last-minute additions

---

## Go/No-Go Sign-Off

| Gate | Status | Notes |
|---|---|---|
| People readiness | GO / NO-GO | |
| Process readiness | GO / NO-GO | |
| Technology readiness | GO / NO-GO | |
| **Overall** | **GO / NO-GO** | |

**Release manager sign-off:** _______________
**Date/time:** _______________

---

## Notes

Record any deviations from the standard risk assessment process and the rationale for each deviation.
