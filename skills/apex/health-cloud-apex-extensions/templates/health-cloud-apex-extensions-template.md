# Health Cloud Apex Extensions — Work Template

Use this template when implementing Health Cloud Apex extension points: CarePlanProcessorCallback, care plan invocable actions, Industries Common Components referral actions, or HIPAA logging governance for clinical Apex classes.

## Scope

**Skill:** `health-cloud-apex-extensions`

**Request summary:** (fill in what the user asked for — e.g., "Implement a care plan activation callback that creates a coordinator task" or "Refactor referral creation to use ICC invocable actions")

---

## Context Gathered

Answer these before writing any code:

- **HealthCloudGA package version installed:** (e.g., 252.0.x — check Setup > Installed Packages)
- **Care plan model in use:** [ ] Integrated Care Management (ICM) [ ] Legacy CarePlanTemplate__c model
- **Extension point needed:** [ ] CarePlanProcessorCallback [ ] Care Plan invocable action [ ] ICC referral action [ ] Other: ___
- **Existing code to review for anti-patterns:** (list Apex class names that currently handle care plan or referral logic)
- **Debug logging status in production:** [ ] Disabled (compliant) [ ] Enabled on specific users [ ] Unknown — must verify
- **AuthorizationFormConsent configured:** [ ] Yes [ ] No [ ] Unknown

---

## Approach

Which pattern from SKILL.md applies?

- [ ] **CarePlanProcessorCallback** — implementing a lifecycle hook (activation, creation, closure)
- [ ] **Care Plan Invocable Action** — creating or modifying care plan data from Apex
- [ ] **ICC Referral Action** — submitting or updating referrals from Apex
- [ ] **HIPAA Logging Audit** — reviewing and gating System.debug() calls in clinical classes

**Reason this pattern applies:** (fill in)

---

## Implementation Plan

### Apex Class(es) to Create or Modify

| Class Name | Interface / Base | Purpose |
|---|---|---|
| (e.g., CarePlanActivationCallback) | HealthCloudGA.CarePlanProcessorCallback | (describe what it does) |
| (e.g., CarePlanActivationHandler) | n/a (@future or Queueable) | (async delegate for heavy logic) |

### Invocable Actions to Call

| Action API Name | Purpose | Called From |
|---|---|---|
| (e.g., HealthCloudGA.CreateCarePlan) | Create care plan from template | (Apex class or Flow name) |
| (e.g., industries_referral_mgmt.CreateReferral) | Submit referral through ICC | (Apex class or Flow name) |

### Setup Registration Required

- [ ] Register callback class in Health Cloud Setup > Care Plan Settings > Custom Apex Callback
  - Class name to register: ___
  - Sandbox validation step: ___

---

## Debug Logging Governance

- [ ] All `System.debug()` calls in clinical Apex classes reviewed
- [ ] Any calls that reference clinical object fields (`EhrPatientMedication`, `PatientHealthCondition`, `ClinicalEncounterCode`, `AuthorizationFormConsent`) removed or gated
- [ ] Debug gate Custom Metadata record exists: `DebugSettings__mdt.ApexDebug.IsEnabled__c = false` in production
- [ ] Production debug log purge policy confirmed: logs purged within ___ hours after use

---

## Checklist

Work through these before marking the task complete:

- [ ] HealthCloudGA package version confirmed; interface method signatures verified against installed package
- [ ] Callback class declared `global` (not `public`) and registered in Health Cloud Setup
- [ ] No direct DML on `CarePlan`, `CarePlanGoal`, `CarePlanProblem`, `CarePlanTemplate__c`, or `ReferralRequest__c`
- [ ] All care plan operations route through `CreateCarePlan` / `AddCarePlanGoal` invocable actions
- [ ] All referral operations route through ICC invocable actions
- [ ] Invocable action results checked for `isSuccess() == false` with explicit error handling
- [ ] `System.debug()` calls gated by `DebugSettings__mdt` flag — no PHI in debug output
- [ ] Heavy callback logic delegated to `@future` or Queueable to avoid governor limit conflicts
- [ ] Unit tests cover callback methods and action calls; test class does not use direct DML on clinical objects
- [ ] Deployment runbook includes Health Cloud Setup registration step

---

## Notes

(Record any deviations from the standard pattern, version-specific behavior, or decisions made during implementation.)
