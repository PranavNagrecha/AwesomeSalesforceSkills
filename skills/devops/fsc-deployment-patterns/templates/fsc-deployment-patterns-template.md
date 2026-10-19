# FSC Deployment Patterns — Work Template

Use this template when planning or executing an FSC metadata deployment.

## Scope

**Skill:** `fsc-deployment-patterns`

**Request summary:** (fill in what the user asked for — e.g., "deploy FSC CDS configuration to production sandbox")

---

## Context Gathered

Answer these before proceeding:

- **FSC licensing model (source org):** [ ] Managed-package (FinServ__ namespace)  [ ] Platform-native Core FSC (no namespace)
- **FSC licensing model (target org):** [ ] Managed-package (FinServ__ namespace)  [ ] Platform-native Core FSC (no namespace)
- **Person Accounts enabled in target org:** [ ] Yes  [ ] No  [ ] Unknown — need to verify
- **OWD for Account in target org:** ___________________
- **OWD for Opportunity in target org:** ___________________
- **OWD for Financial Deal in target org:** ___________________
- **Metadata components being deployed:** (list them)
  - 
  - 
- **Deployment tool:** [ ] sf CLI  [ ] Change Sets  [ ] Metadata API direct  [ ] CI/CD pipeline (specify: _______)
- **Target environment:** [ ] Developer sandbox  [ ] UAT sandbox  [ ] Production  [ ] Scratch org

---

## Pre-Flight Checklist

Complete before any metadata deployment:

- [ ] **Namespace audit complete** — confirmed source and target orgs use the same FSC model (or rewrite performed)
- [ ] **Person Accounts verified** — query returned PersonAccount record type in target org
  ```bash
  sf data query \
    --query "SELECT Id, DeveloperName FROM RecordType WHERE SobjectType='Account' AND IsPersonType=true" \
    --target-org <alias>
  ```
  Result: ___________________

- [ ] **OWDs verified** — Account, Opportunity, Financial Deal are Private or Public Read-Only
- [ ] **OWD recalculation complete** — the OWD change shows complete on Setup > Background Jobs (or the completion email arrived)
- [ ] **FSC package version** — managed-package version confirmed (if managed-package model): ___________________

---

## Deployment Phase Plan

### Phase 1 — Structural Metadata (Record Types)

Components:
```
RecordType:Account.Household
RecordType:Account.Person_Account
# add others as needed
```

Validate first:
```bash
sf project deploy validate \
  --metadata "RecordType" \
  --target-org <alias> \
  --test-level RunSpecifiedTests --tests <test class>
```

Deploy:
```bash
sf project deploy start \
  --metadata "RecordType" \
  --target-org <alias>
```

Gate: [ ] Deploy succeeded  [ ] Record types confirmed in target org

---

### Phase 2 — Industries Settings (CDS Activation)

Components (`settings/Industries.settings`; one `enableCompliantDataSharingFor<Object>` boolean per CDS object, each false by default):
```xml
<IndustriesSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableCompliantDataSharingForAccount>true</enableCompliantDataSharingForAccount>
    <enableCompliantDataSharingForOpportunity>true</enableCompliantDataSharingForOpportunity>
</IndustriesSettings>
```

Deploy:
```bash
sf project deploy start \
  --metadata "Settings:Industries" \
  --target-org <alias>
```

Gate: [ ] Deploy succeeded  [ ] CDS flag confirmed active in Setup

---

### Phase 3 — ParticipantRole Components

`ParticipantRole` is a Metadata API type (API 50.0+), not custom metadata. One file per role in `participantRoles/<Name>.participantRole`:
```xml
<ParticipantRole xmlns="http://soap.sforce.com/2006/04/metadata">
    <defaultAccessLevel>Read</defaultAccessLevel>   <!-- required: Edit | None | Read -->
    <isActive>true</isActive>
    <masterLabel>Advisor</masterLabel>               <!-- required -->
    <parentObject>Account</parentObject>             <!-- required; must have its CDS flag set in Phase 2 -->
</ParticipantRole>
```

| Role (masterLabel) | parentObject | defaultAccessLevel | isActive | CDS flag for parentObject set? |
|---|---|---|---|---|
| | | | | [ ] |

Deploy:
```bash
sf project deploy start \
  --metadata "ParticipantRole" \
  --target-org <alias>
```

Gate: [ ] Deploy succeeded  [ ] Checker run clean: `python3 skills/devops/fsc-deployment-patterns/scripts/check_fsc_deployment_patterns.py --manifest-dir force-app/main/default`

---

### Phase 4 — CDS Post-Deploy Activation

Trigger sharing recalculation (managed-package FSC — UNVERIFIED (2026-10-19): this class is not in the Summer '26 Apex Reference; confirm it exists in the org first):
```apex
Database.executeBatch(
    new FinServ.FinancialAccountShareRecalcBatch(),
    200
);
```

Gate: [ ] Recalculation batch completed  [ ] Share-table rows confirmed

---

## Post-Deploy Validation

- [ ] OWD settings confirmed correct in target org
- [ ] Share-table query on the role's `parentObject` share object (for `Account`, `AccountShare`) returns a row for the test record and the expected user or group:
  ```sql
  SELECT Id, UserOrGroupId, RowCause
  FROM AccountShare
  WHERE AccountId = '<test_id>'
  ```
  Result: ___________________

- [ ] Each deployed `ParticipantRole` checked: `isActive` true, `defaultAccessLevel` as intended, `parentObject` has its CDS flag set
- [ ] Test user logged in and confirmed record visibility via CDS
- [ ] Pre-existing records confirmed visible (recalculation covered historical data)

---

## Approach Notes

Which pattern from SKILL.md applies? Why?

- [ ] Phased prerequisite-first deployment pattern
- [ ] Namespace audit and rewrite pattern
- [ ] CDS post-deploy validation pattern

---

## Deviations and Notes

Record any deviations from the standard pattern and why:

- 

---

## Rollback Plan

Note: Person Account enablement and OWD changes cannot be rolled back automatically.

- [ ] Pre-deployment org state snapshot taken (record counts, OWD settings, existing record types)
- [ ] Rollback procedure for metadata-only changes: `sf project deploy start --manifest destructiveChanges.xml`
- [ ] Rollback for OWD changes: documented manual steps with approver identified
