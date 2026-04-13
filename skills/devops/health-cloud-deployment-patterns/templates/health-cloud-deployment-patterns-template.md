# Health Cloud Deployment Patterns — Deployment Runbook Template

Use this template when planning or executing any Health Cloud deployment to production or a full sandbox. Fill every section before the deployment window opens.

---

## Deployment Overview

**Target org:** __________________________________ (production / full sandbox / partial sandbox)

**Deployment type:** __________________________________ (initial install / metadata update / sandbox refresh reconfiguration)

**Scheduled deployment window:** __________________________________ (date and time with timezone)

**Deployer:** __________________________________ (name and role)

**Approver:** __________________________________ (name and role)

---

## Phase 0: Pre-Deployment Gates

Complete these before any deployment activity begins.

### HIPAA Compliance Gate (required for production with PHI)

- [ ] Signed HIPAA BAA with Salesforce confirmed — BAA document reference: __________________
- [ ] Shield Platform Encryption is already configured (for updates) OR will be configured before PHI import (for initial deploys)
- [ ] Debug log access policy reviewed — production debug logging is restricted to prevent PHI exposure

### Version Compatibility Gate

- [ ] HealthCloudGA package version to install: __________________ (04t subscriber version ID)
- [ ] Salesforce Industries Common Components version (if required): __________________
- [ ] Additional feature package versions (if required): __________________
- [ ] All package versions tested in a lower sandbox at this version: [ ] Yes / [ ] N/A

---

## Phase 1: Managed Package Installation

Execute in strict order. Do not proceed to Phase 2 until all packages are verified as installed.

### Step 1.1: Install Salesforce Industries Common Components (if required)

- [ ] N/A — not required for this org
- [ ] Command run:
  ```
  sf package install --package <04t_version_id> --target-org <alias> --wait 10
  ```
- [ ] Verified in Setup > Installed Packages: [ ] Yes

### Step 1.2: Install HealthCloudGA Managed Package

- [ ] Command run:
  ```
  sf package install --package <04t_version_id> --target-org <alias> --wait 20
  ```
- [ ] Verified in Setup > Installed Packages: [ ] Yes
- [ ] Installed version matches target: __________________ vs expected: __________________

### Step 1.3: Install Additional Feature Packages (if required)

Feature packages to install (list all):

| Package Name | Version ID | Installed? |
|---|---|---|
|  |  | [ ] |
|  |  | [ ] |

---

## Phase 2: Permission Set License Assignment

PSLs must be assigned before deploying permission sets that reference Health Cloud features.

- [ ] Health Cloud PSL assigned to: __________________
  - Method: [ ] Setup UI (manually) / [ ] Data Loader / [ ] sf CLI
- [ ] PSL assignment verified by querying: `SELECT Id FROM UserPackageLicense WHERE PackageLicense.NamespacePrefix = 'HealthCloudGA'`
- [ ] Count of users with PSL: __________________ (expected: __________________)

---

## Phase 3: Org-Specific Metadata Deployment

### Step 3.1: Validate Deploy

```bash
sf project deploy validate \
  --target-org <alias> \
  --manifest manifest/package.xml \
  --test-level RunLocalTests
```

- [ ] Validation run completed
- [ ] Test pass count: __________________ / __________________
- [ ] All validation errors resolved

### Step 3.2: Deploy Metadata

```bash
sf project deploy start \
  --target-org <alias> \
  --manifest manifest/package.xml \
  --test-level RunLocalTests
```

- [ ] Deploy completed successfully
- [ ] Deployed components:
  - Custom Objects: __________________
  - Apex Classes: __________________
  - Flows: __________________
  - Permission Sets: __________________
  - Custom Metadata: __________________

---

## Phase 4: Post-Deploy Manual Steps

These steps CANNOT be automated via sf project deploy. Each is mandatory.

### Step 4.1: Register CarePlanProcessorCallback

- [ ] Navigate to: Setup > Health Cloud Setup > Care Plan Settings
- [ ] CarePlan Processor Callback class selected: __________________
- [ ] Saved and confirmed
- [ ] Verification query run: `SELECT Id, HealthCloudGA__ClassName__c FROM HealthCloudGA__CarePlanProcessorSetting__mdt`
  - Result: __________________

### Step 4.2: Shield Platform Encryption Configuration (initial deploy only)

- [ ] N/A — encryption already configured from prior deployment
- [ ] Tenant secret generated and activated in: Setup > Platform Encryption > Tenant Secrets
- [ ] Encryption policies applied to fields:

| Object | Field | Policy | Active? |
|---|---|---|---|
| HealthCloudGA__EhrPatientMedication__c | (medication fields) | AES256 | [ ] |
| HealthCloudGA__PatientHealthCondition__c | (condition fields) | AES256 | [ ] |
| Contact | (PHI fields: SSN, DOB) | AES256 | [ ] |
| (add rows as needed) | | | |

- [ ] Encryption verified: sample record field value returned as encrypted in debug log

### Step 4.3: Create or Restore Care Plan Templates

Templates to create or verify in target org:

| Template Name | Created via UI? | Verified in Wizard? |
|---|---|---|
|  | [ ] | [ ] |
|  | [ ] | [ ] |

- [ ] All templates appear in Care Plan wizard
- [ ] Template entries and goals display correctly

---

## Phase 5: Post-Deploy Smoke Tests

- [ ] Health Cloud app opens without errors for a test user with PSL + permission set
- [ ] Care Plan wizard opens and displays available templates
- [ ] Creating a new care plan with a template completes without errors
- [ ] CarePlanProcessorCallback fires correctly on care plan save (verify via debug log with non-PHI test case)
- [ ] Encrypted field values confirmed encrypted: field contents not readable in plaintext via API or export

---

## Rollback Plan

| Scenario | Rollback Action |
|---|---|
| Managed package install fails | Contact Salesforce Support — managed package uninstall may require support assistance |
| Metadata deploy fails | Re-deploy prior commit; run `sf project deploy start` with the previous package.xml |
| CarePlanProcessorCallback registration broken | Re-navigate to Setup and re-register; check for Apex class compilation errors |
| Shield Encryption causes data access issues | Review encryption policy; consult Shield Platform Encryption troubleshooting guide |

---

## Sign-Off

| Step | Completed by | Timestamp |
|---|---|---|
| Package installation verified | | |
| PSL assignment verified | | |
| Metadata deployment verified | | |
| CarePlanProcessorCallback registered | | |
| Shield Encryption policies active | | |
| Care plan templates verified | | |
| Smoke tests passed | | |
| Deployment approved for production use | | |
