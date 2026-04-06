# Pre-Deployment Checklist -- Work Template

Use this template when preparing a Salesforce metadata deployment for production.

## Scope

**Skill:** `pre-deployment-checklist`

**Release name / ticket:** (fill in)

**Target org:** (fill in production org alias or username)

**Deployment tool:** SF CLI / Change Sets / DevOps Center / Metadata API (circle one)

**Scheduled deployment window:** (fill in date, time, timezone)

## Context Gathered

- **Metadata types in release:** (list: Apex classes, LWC, Flows, permission sets, etc.)
- **Component count:** (number)
- **Apex test level:** RunLocalTests / RunSpecifiedTests / RunAllTestsInOrg
- **Destructive changes included:** Yes / No
- **Target instance:** (e.g., NA45, CS99 -- check trust.salesforce.com)

## Pre-Deployment Gates

### 1. Component Inventory
- [ ] All metadata components listed in manifest match the source control diff
- [ ] No unintended components included (especially profiles, page layouts)
- [ ] Destructive changes (if any) are in a separate manifest with correct ordering

### 2. Dependency Completeness
- [ ] MetadataComponentDependency queried via Tooling API for all components
- [ ] All transitive dependencies present in target org or included in package
- [ ] No references to renamed/deleted fields, objects, or classes

### 3. Pre-Release Backup
- [ ] Current production state retrieved for all components being deployed
- [ ] Backup stored in: `backups/____________/`
- [ ] Backup tested: can be redeployed without errors (optional but recommended)

### 4. Validation Deploy
- [ ] Validation deploy executed against production (`checkOnly: true`)
- [ ] Validated deploy request ID: `________________________`
- [ ] Validation timestamp: `____________` (quick-deploy valid until: `____________`)
- [ ] All Apex tests passed
- [ ] Code coverage: ____% (aggregate) -- meets 75% threshold

### 5. Environment Safety
- [ ] trust.salesforce.com checked -- no maintenance for target instance
- [ ] No other deploys or validations in progress (Deployment Status page checked)
- [ ] No batch Apex jobs scheduled during the deployment window
- [ ] Deployment scheduled outside peak business hours

### 6. Post-Deploy Plan
- [ ] Post-deploy manual steps documented:
  - [ ] Flow activations needed: (list)
  - [ ] Permission set assignments needed: (list)
  - [ ] Named credential updates needed: (list)
  - [ ] Data fixes or scripts needed: (list)
- [ ] Smoke test plan defined
- [ ] Rollback plan defined (backup package path: `backups/____________/`)
- [ ] Communication plan: stakeholders notified of deployment window

## Go / No-Go Decision

| Gate | Status |
|---|---|
| Component inventory complete | Pass / Fail |
| Dependencies verified | Pass / Fail |
| Backup retrieved | Pass / Fail |
| Validation deploy passed | Pass / Fail |
| Environment safe | Pass / Fail |
| Post-deploy plan ready | Pass / Fail |

**Decision:** GO / NO-GO

**Decided by:** (name)

**Decision timestamp:** (date and time)

## Notes

Record any deviations from the standard checklist and why.
