---
name: health-cloud-deployment-patterns
description: "Use when planning or executing a Health Cloud deployment to production or a full sandbox, including managed package installation sequencing, Permission Set License assignment, care plan template setup, HIPAA compliance controls, and post-deploy manual steps not captured in metadata. Triggers: 'how do I deploy Health Cloud', 'HealthCloudGA package install order', 'care plan template not working after deployment', 'Health Cloud HIPAA Shield Encryption setup', 'CarePlanProcessorCallback registration post-deploy'. NOT for Health Cloud data model design (use health-cloud-data-model), NOT for Apex extensions in Health Cloud (use health-cloud-apex-extensions), NOT for API usage patterns (use health-cloud-apis)."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "how do I deploy Health Cloud to a production org including package installation"
  - "HealthCloudGA managed package install fails or needs to be installed before other packages"
  - "care plan template is not working after deployment to production"
  - "how do I register CarePlanProcessorCallback after deploying Health Cloud"
  - "what HIPAA controls do I need to configure in Health Cloud before go-live"
  - "Health Cloud Shield Platform Encryption setup for clinical fields"
  - "Permission Set Licenses not assigned after Health Cloud managed package install"
tags:
  - health-cloud
  - managed-package
  - deployment
  - hipaa
  - care-plan
  - shield-encryption
  - devops
inputs:
  - "Target org type: production, full sandbox, or scratch org"
  - "List of custom metadata, flows, permission sets, and Apex classes to deploy on top of HealthCloudGA"
  - "HIPAA BAA status: signed or not yet signed"
  - "List of care plan templates and invocable action names to configure post-deploy"
  - "Shield Platform Encryption tenant secret availability and encryption policy decisions"
outputs:
  - "Ordered deployment runbook: managed package install sequence, metadata deploy steps, and manual post-deploy steps"
  - "HIPAA compliance checklist covering BAA, Shield Encryption, and debug log restrictions"
  - "CarePlanProcessorCallback registration checklist for Health Cloud Setup"
  - "Permission Set License assignment plan per user persona"
dependencies:
  - devops/permission-set-deployment-ordering
  - devops/go-live-cutover-planning
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# Health Cloud Deployment Patterns

Use this skill when planning or executing a Health Cloud deployment to production or a full sandbox. It covers the strict managed-package installation sequence required before metadata deployment, the manual post-deploy steps that are not captured in any deployable metadata artifact, HIPAA compliance controls that must be configured before PHI is stored, and the care plan template setup constraints enforced by the HealthCloudGA namespace.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the **HealthCloudGA managed package version** that must be installed and verify whether any dependent industry packages (e.g., Salesforce Industries Common Components) are also required and in what order.
- Determine whether a **signed HIPAA BAA** is in place before any PHI touches the target org. Salesforce requires a signed BAA before Health Cloud can be used with real patient data. Shield Platform Encryption configuration must follow immediately after.
- Understand that **care plan templates (`CarePlanTemplate__c`)** live in the HealthCloudGA namespace and are created only through invocable actions — direct DML is blocked by the platform. They cannot be captured in standard metadata deployments; they are set up as a post-deploy manual step or via Apex that calls the invocable action.
- Confirm that **CarePlanProcessorCallback** is a class you have authored in your org (or is provided by a package), and that it must be manually registered in Health Cloud Setup under Care Plan Settings after every deploy to a new org. This registration step produces no metadata artifact and is invisible to your CI/CD pipeline.

---

## Core Concepts

### Strict Managed Package Installation Order

Health Cloud deployments require the `HealthCloudGA` managed package to be installed before any dependent custom metadata, permission sets, or Apex classes are deployed. The platform enforces namespace resolution at deploy time: metadata that references `HealthCloudGA` namespace fields, objects, or classes will fail validation if the package is not present. Installing dependent packages (such as Omnistudio or Salesforce Industries Common Components) out of order causes the same namespace resolution failures.

The canonical install sequence is:
1. Salesforce Industries Common Components (if required by your org)
2. HealthCloudGA managed package
3. Any additional Health Cloud feature packages (e.g., Provider Search, Intelligent Appointment Management) in the order documented in the Health Cloud Administration guide
4. Your org-specific metadata (flows, permission sets, custom objects, Apex classes)

There is no automated way to enforce this order in a standard `sf project deploy` run. It must be scripted or documented as a pre-deploy checklist step.

### Permission Set Licenses Are Assigned Post-Install

After the HealthCloudGA package installs, Health Cloud Permission Set Licenses (PSLs) are available in the org but are not automatically assigned to users. PSL assignment must occur before end-user permission sets that reference Health Cloud features can be assigned. Deploying a permission set that grants Health Cloud object access to a user who has no PSL results in a deployment success but a runtime access failure — the user simply cannot open Health Cloud records.

PSL assignment is done through Setup > Users > Permission Set License Assignments and cannot be captured in metadata. It must be documented as an explicit post-deploy step in every deployment runbook.

### Care Plan Templates Cannot Be Deployed as Metadata

`CarePlanTemplate__c` and its child records (`CarePlanTemplateEntry__c`, `CarePlanTemplateGoal__c`) are `HealthCloudGA` namespace objects. While they can be queried via SOQL and inserted via the API in theory, the platform enforces that care plan templates must be created through the Health Cloud Care Plan Template invocable action (`HealthCloud.CreateCarePlanTemplate`). Direct DML attempts either fail silently or produce incomplete records. This means care plan templates are **not captured in sfdx source format or change sets** and must be recreated or migrated using invocable actions or the Health Cloud Setup UI in each new org.

### CarePlanProcessorCallback Is a Post-Deploy Manual Registration

`CarePlanProcessorCallback` is a class that implements the `HealthCloud.CarePlanProcessorCallbackInterface` interface. After deploying this class to a new org (or after any reinstall of HealthCloudGA), the class must be manually registered in **Setup > Health Cloud Setup > Care Plan Settings > CarePlan Processor Callback**. This registration writes to a Custom Metadata Type record, but that record is in the HealthCloudGA namespace and is not retrievable as part of your org's metadata via `sf project retrieve`. If you restore an org from backup or deploy to a fresh sandbox, this step must be repeated.

### HIPAA Controls Are Configuration, Not Metadata

HIPAA-relevant controls in Health Cloud are primarily org configuration decisions, not metadata artifacts:
- **Signed BAA** with Salesforce must precede any PHI storage.
- **Shield Platform Encryption** must be enabled and tenant secrets generated; encryption policies for clinical fields (e.g., fields on `EhrPatientMedication__c`, `PatientHealthCondition__c`, `CarePlanActivity__c`) must be set in the Encryption Policy UI.
- **Debug log restrictions**: enabling debug logs on a production Health Cloud org risks capturing PHI in log output. Log levels must be gated and logs purged after debugging. This is an operational control, not a metadata setting.
- **Audit trail and event log**: Field Audit Trail or Event Monitoring should be configured for access to clinical records.

---

## Common Patterns

### Sequential Package-Then-Metadata Deployment

**When to use:** Every Health Cloud deployment to production or a new full sandbox.

**How it works:**
1. Install Salesforce Industries Common Components package (if required) via Setup > Installed Packages or `sf package install`.
2. Install HealthCloudGA managed package at the correct version.
3. Install any additional Health Cloud feature packages.
4. Assign Health Cloud Permission Set Licenses to appropriate users or groups.
5. Run `sf project deploy start` for org-specific metadata (custom objects, flows, Apex, permission sets).
6. Perform post-deploy manual steps: register CarePlanProcessorCallback in Care Plan Settings, configure Shield Encryption policies, create care plan templates via invocable actions or UI.

**Why not a single deploy:** There is no way to combine managed package installation with a `sf project deploy` command. They are separate operations. Any metadata that references the HealthCloudGA namespace must be deployed after the package exists in the target org.

### Care Plan Template Migration via Invocable Actions

**When to use:** When care plan templates must be reproduced in a new sandbox or production org from an existing org.

**How it works:**
1. Query existing templates in the source org: `SELECT Id, Name, HealthCloudGA__Description__c FROM HealthCloudGA__CarePlanTemplate__c`.
2. For each template, call the `HealthCloud.CreateCarePlanTemplate` invocable action in the target org, passing name, description, and entry/goal details.
3. Verify template creation in the target org via the Health Cloud Care Plan Templates list view.

**Why not direct insert:** Direct DML on `CarePlanTemplate__c` bypasses the platform's template validation logic and either fails or produces malformed templates that do not function correctly in the Care Plan wizard.

### HIPAA Pre-Go-Live Configuration Pattern

**When to use:** Before Health Cloud goes live with real patient data.

**How it works:**
1. Confirm signed BAA with Salesforce Account team.
2. Enable Shield Platform Encryption; generate and activate a tenant secret.
3. Define encryption policies for all clinical fields that may contain PHI (patient demographics, medication data, care plan notes).
4. Restrict debug log access: remove Modify All Data or View All Data from debug log profiles; set a post-debug log purge procedure.
5. Enable Field Audit Trail or Event Monitoring for access logging to clinical records.
6. Review all integration users and connected apps for PHI exposure risk.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Deploying Health Cloud to a brand-new production org | Sequential: packages first, metadata second, then manual post-deploy steps | Package namespace must exist before metadata references are validated |
| Refreshing a full sandbox from production | Reinstall packages in the sandbox at matching version, reassign PSLs, re-register CarePlanProcessorCallback | Sandbox refresh wipes installed packages and configuration registrations |
| Migrating care plan templates between orgs | Export via SOQL, recreate via invocable actions in target | Direct DML is blocked or produces malformed templates |
| Setting up Shield Encryption for clinical fields | Enable encryption after package install, before any PHI is imported | Encryption must be configured before PHI data is written, not after |
| Using scratch orgs for Health Cloud development | Limited support; scratch orgs require Health Cloud features to be declared in `project-scratch-def.json` and packages installed via `sf package install` | Scratch org definition does not automatically provision HealthCloudGA namespace |
| Change set vs unlocked package for org-specific customizations | Unlocked package for Apex/LWC; change set for one-off config | Unlocked packages support version pinning and dependency declaration; change sets have no dependency management |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner deploying Health Cloud:

1. **Verify the signed BAA and compliance posture.** Confirm that Salesforce has cosigned the HIPAA BAA for this org before any PHI or test PHI is planned for import. If BAA is not signed, halt and escalate.
2. **Install managed packages in order.** Install Salesforce Industries Common Components (if required), then HealthCloudGA at the target version, then any feature packages. Use `sf package install --package <04t...> --target-org <alias>` or Setup UI. Verify installed packages list before proceeding.
3. **Assign Permission Set Licenses.** In Setup > Users > Permission Set License Assignments, assign the Health Cloud PSL to all users or permission set groups that will use Health Cloud features. Document the assignment in the deployment runbook.
4. **Deploy org-specific metadata.** Run `sf project deploy start --target-org <alias>` for custom objects, flows, Apex classes, permission sets, and custom metadata. Validate first with `sf project deploy validate`. Resolve any namespace resolution errors before proceeding.
5. **Register CarePlanProcessorCallback.** Navigate to Setup > Health Cloud Setup > Care Plan Settings. In the CarePlan Processor Callback field, select and save the callback class. Confirm the class name matches what was deployed. Document this step in the runbook as a required post-deploy action.
6. **Configure Shield Platform Encryption.** Generate and activate a tenant secret. Define encryption policies for all clinical fields identified in the HIPAA field inventory. Test that encrypted fields are readable by authorized users and blocked from unauthorized profiles.
7. **Create care plan templates.** Use the Health Cloud Care Plan Templates UI or invoke `HealthCloud.CreateCarePlanTemplate` to recreate templates in the target org. Verify that templates appear in the Care Plan wizard and that entries and goals are correct.

---

## Review Checklist

Run through these before marking a Health Cloud deployment complete:

- [ ] Signed HIPAA BAA confirmed with Salesforce Account team before any PHI is stored
- [ ] HealthCloudGA managed package installed at correct version; verified in Installed Packages list
- [ ] Health Cloud Permission Set Licenses assigned to all relevant users or groups
- [ ] Org-specific metadata deployed and validated; all tests passing
- [ ] CarePlanProcessorCallback class registered in Setup > Health Cloud Setup > Care Plan Settings
- [ ] Shield Platform Encryption enabled; tenant secret active; encryption policies applied to all clinical fields
- [ ] Care plan templates created or verified in target org via invocable actions or UI
- [ ] Debug log access restricted; post-debug log purge procedure documented
- [ ] Integration users and connected apps reviewed for PHI exposure risk

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **CarePlanProcessorCallback registration is invisible to CI/CD** — Registering the callback class in Care Plan Settings writes to a Custom Metadata Type in the HealthCloudGA namespace, which is not retrievable via `sf project retrieve`. Every deployment to a new org or sandbox refresh requires manual re-registration. CI/CD pipelines that assume a full org restore cannot detect this gap.
2. **Care plan templates fail silently on direct DML** — Attempting to insert `HealthCloudGA__CarePlanTemplate__c` records via direct DML either fails with a generic error or produces records that appear valid in SOQL but are non-functional in the Care Plan wizard. Only the `HealthCloud.CreateCarePlanTemplate` invocable action produces correctly formed templates.
3. **PSL assignment required before permission set assignment works at runtime** — A user without a Health Cloud PSL can receive a Health Cloud permission set without error, but will receive "insufficient privileges" errors at runtime when accessing Health Cloud features. This silent failure makes troubleshooting confusing. Always confirm PSL assignment before testing permission set access.
4. **Sandbox refresh wipes HealthCloudGA package and configuration** — A full sandbox refresh from production does not preserve the installed HealthCloudGA package, PSL assignments, or the CarePlanProcessorCallback registration. The post-deploy manual steps must be repeated in full after every sandbox refresh. Partial sandbox refreshes (source sandbox) may preserve packages but still lose configuration registrations.
5. **Shield Encryption must precede PHI import** — If Shield Platform Encryption policies are configured after PHI data is already present in the org, existing data is not retroactively encrypted. The encryption policy applies only to new writes. Retroactive encryption requires a data re-import or Salesforce support involvement. Always configure encryption before importing any PHI.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Ordered deployment runbook | Step-by-step checklist covering package installs, metadata deploys, PSL assignments, and manual post-deploy steps |
| HIPAA compliance checklist | Pre-go-live checklist covering BAA, Shield Encryption, debug log restrictions, and audit logging |
| Care plan template inventory | List of templates to recreate in the target org, with entry and goal details for invocable action calls |
| Post-deploy validation report | Confirmation that CarePlanProcessorCallback is registered, encryption policies are active, and care plan templates are functional |

---

## Related Skills

- devops/permission-set-deployment-ordering — for the detailed rules governing Health Cloud permission set and PSL ordering during deployment
- devops/go-live-cutover-planning — for the broader go-live runbook that wraps this Health Cloud deployment checklist
- data/health-cloud-data-model — for understanding which objects and fields are in the HealthCloudGA namespace and must be treated as managed-package components
- apex/health-cloud-apex-extensions — for Apex-level patterns including CarePlanProcessorCallback implementation and invocable action usage
- devops/deployment-monitoring — for post-deploy health monitoring of Health Cloud orgs
