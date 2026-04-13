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
    --query "SELECT Id, DeveloperName FROM RecordType WHERE SObjectType='Account' AND DeveloperName='PersonAccount'" \
    --target-org <alias>
  ```
  Result: ___________________

- [ ] **OWDs verified** — Account, Opportunity, Financial Deal are Private or Public Read-Only
- [ ] **OWD recalculation complete** — no active SharingRecalculation background jobs in target org
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

Components:
```
IndustriesSettings
```

Deploy:
```bash
sf project deploy start \
  --metadata "IndustriesSettings" \
  --target-org <alias>
```

Gate: [ ] Deploy succeeded  [ ] CDS flag confirmed active in Setup

---

### Phase 3 — Participant Role Custom Metadata

Components:
```
ParticipantRole
# list specific records if applicable
```

Deploy:
```bash
sf project deploy start \
  --metadata "ParticipantRole" \
  --target-org <alias>
```

Gate: [ ] Deploy succeeded

---

### Phase 4 — CDS Post-Deploy Activation

Trigger sharing recalculation (managed-package FSC):
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
- [ ] Share-table query returns rows for test Financial Account:
  ```sql
  SELECT Id, UserOrGroupId, RowCause, FinancialAccountAccessLevel
  FROM FinancialAccountShare
  WHERE ParentId = '<test_id>' AND RowCause = 'ParticipantRole'
  ```
  Result: ___________________

- [ ] Participant Role record type references validated against target org record types
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
