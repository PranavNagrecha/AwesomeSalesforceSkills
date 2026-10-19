---
name: fsc-deployment-patterns
description: "Use when planning or executing metadata deployments for Financial Services Cloud (FSC) — including Person Account enablement sequencing, Account record-type ordering, Compliant Data Sharing (CDS) activation. NOT for general metadata deployment (use devops/pre-deployment-checklist) or FSC architecture — use architect/fsc-architecture-patterns."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - Reliability
triggers:
  - "my FSC deployment fails because household record types cannot be deployed before Person Accounts are enabled"
  - "Compliant Data Sharing share table is empty after I deployed FSC CDS configuration"
  - "FinServ__ namespace metadata from our managed package FSC org is incompatible with the target platform-native FSC org"
  - "IndustriesSettings metadata deploy succeeds but CDS is still not active in the target org"
  - "Participant Role custom metadata deployment fails with a reference error to Financial Account Roles"
  - "how do I sequence FSC metadata components to avoid dependency errors during deployment"
  - "deploying FSC from sandbox to production — what is the correct order for Person Accounts, record types, and CDS objects"
tags:
  - fsc
  - financial-services-cloud
  - deployment
  - compliant-data-sharing
  - person-accounts
  - metadata-api
  - industries
  - namespacing
inputs:
  - "FSC licensing model: managed-package (FinServ__ namespace) or platform-native Core FSC (Winter '23+)"
  - "Target org type: sandbox, production, scratch org, or developer org"
  - "Whether Person Accounts are already enabled in the target org"
  - "List of FSC metadata components being deployed (record types, custom metadata, IndustriesSettings, sharing rules)"
  - "OWD settings for Account, Opportunity, and Financial Deal objects in the target org"
  - "Deployment tool in use: sf CLI, change sets, or Metadata API direct"
outputs:
  - "Sequenced FSC deployment plan with named deployment batches in dependency order"
  - "Pre-flight checklist for FSC-specific org prerequisites (Person Accounts, OWDs, namespace audit)"
  - "Namespace compatibility audit: FinServ__ vs standard-object API names across metadata artifacts"
  - "Post-deploy CDS validation checklist"
dependencies: []
version: 1.0.2
author: Pranav Nagrecha
updated: 2026-10-19
---

# FSC Deployment Patterns

Use this skill when planning or executing metadata deployments for Financial Services Cloud. FSC has strict, irreversible prerequisite steps — particularly around Person Account enablement and Compliant Data Sharing activation — that must be completed in the correct sequence before dependent metadata can land. It also covers the critical namespace incompatibility between managed-package FSC orgs (FinServ__ prefix) and platform-native Core FSC orgs (Winter '23+), which causes metadata artifacts to be non-portable between the two models.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm the FSC licensing model in use.** Managed-package FSC orgs use the `FinServ__` namespace prefix on all FSC objects and fields. Platform-native Core FSC orgs (introduced Winter '23) have no namespace — FSC objects are standard platform objects. Metadata artifacts are incompatible between these two models; a deployment package built for one cannot be applied to the other without an API name audit and rewrite.
- **Confirm Person Account status in the target org.** Person Account enablement is an irreversible org-level change that cannot be performed via Metadata API. It must be requested from Salesforce and in place before any household record types, Relationship Groups, or Financial Account metadata can be deployed. If Person Accounts are not enabled, the deployment will fail with a reference error on household record types.
- **Check OWD settings for Account, Opportunity, and Financial Deal.** Compliant Data Sharing share-table entries are only meaningful when the target objects have Org-Wide Defaults (OWDs) set to Private or Public Read-Only. If OWDs are Public Read/Write, CDS share-table rows are written but have no access-control effect. OWDs must be set before deploying CDS-enabling metadata.
- **Know your deployment tool's behavior with `IndustriesSettings`.** The IndustriesSettings Metadata API type controls feature flags for CDS and other FSC capabilities. Deploying IndustriesSettings does not always trigger immediate share-table recalculation — some flags require a post-deploy activation step or sharing recalculation job.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Is each org in the pipeline on managed-package FSC (`FinServ__`) or platform-native FSC? | A package built for one model fails on the other with component-level errors that read like missing dependencies (Gotcha 3) | A per-org model list and a namespace audit before the first deploy to any new target |
| Are person accounts enabled in every target, including the scratch org definition? | Person accounts are off by default and are requested from Salesforce, so no metadata deploy can turn them on (Gotcha 1) | A preflight query on `RecordType.IsPersonType` and the `PersonAccounts` scratch feature in the definition file |
| Which objects get Compliant Data Sharing, and are their OWDs already Private or Public Read Only? | `IndustriesSettings` enables CDS per object, and under a Public Read/Write OWD the share rows grant nothing new (Gotcha 5) | The exact `enableCompliantDataSharingFor*` flags to deploy and the OWD change scheduled ahead of them |
| How many records will the OWD tightening recalculate, and in which window? | Recalculation can run for hours, and CDS checks run during it are unreliable (Gotcha 5) | A maintenance window and a gate that waits for the background job to finish |
| Do records that need CDS access already exist in the target? | Activating CDS does not backfill share rows for existing records (Gotcha 2) | A named recalculation step and the record count it must cover |
| What does each `ParticipantRole` set for `parentObject`, `defaultAccessLevel`, and `isActive`? | A deploy validates the component's shape, not whether the role grants the access you expect (Gotcha 4) | A role-by-role access table the post-deploy test can check against |
| Which test record and test user will prove access after the deploy? | Deploy success is not evidence of row-level access in either gotcha above (Gotchas 2, 4) | A share-table query and a log-in-as check written into the runbook |

Answering these turns an FSC release into gated phases with a proof of access at the end; "just deploying" ships a CDS configuration that reports success and shares nothing.

---

## Core Concepts

### Irreversible Prerequisite: Person Account Enablement

Person Account enablement is the foundational gate for FSC. The Metadata API guide states: "Person accounts aren't enabled by default in Salesforce. To request person accounts, contact Salesforce." UNVERIFIED (2026-10-19): irreversibility is stated only in Salesforce Help, which could not be fetched; treat it as one-way when planning. Once enabled:

- The `Account` object gains an `IsPersonAccount` field.
- Household record types and Relationship Group metadata become deployable.
- The Individual object interaction model changes.

**Impact for deployments:** If a CI pipeline attempts to deploy household-related record types or page layouts to an org where Person Accounts are not yet enabled, the deployment fails with an entity reference error. The fix is never a code change — it is an org configuration step that must precede the first metadata deploy wave.

### Sequential Dependency: Prerequisites Before ParticipantRole Components

FSC's Compliant Data Sharing model uses participant roles to define which roles grant share-table access. In the Summer '26 Metadata API guide `ParticipantRole` is its own metadata type (API 50.0+, `.participantRole` files in `participantRoles/`), not custom metadata, and its fields are `defaultAccessLevel` (Edit / None / Read), `isActive`, `masterLabel`, and `parentObject` (Account, Opportunity, FinancialDeal, Interaction, custom objects, and others) — no record type reference. The deployment sequence is therefore:

1. Person Accounts enabled (manual, Setup)
2. Account record types deployed (`RecordType` metadata)
3. CDS-target objects enabled (OWDs set to Private or Public Read-Only)
4. `IndustriesSettings` metadata deployed to activate CDS flags
5. `ParticipantRole` components deployed

Deploying `ParticipantRole` last keeps every role behind the CDS flag and OWD state it depends on. A successful deploy proves only that the component is well formed — whether the role grants the expected access is a post-deploy test.

### Namespace Model: Managed Package vs Platform-Native Core FSC

FSC historically shipped as a managed package with the `FinServ__` namespace. Every FSC object, field, and custom metadata type carried this prefix:

- `FinServ__FinancialAccount__c`
- `FinServ__Financial_Account__c.FinServ__Balance__c`
- `FinServ__ParticipantRole__mdt` — UNVERIFIED (2026-10-19): the managed-package name is not in the Summer '26 Metadata API guide, which documents only the unprefixed `ParticipantRole` type.

Starting with Winter '23, Salesforce introduced platform-native Core FSC, where FSC objects are standard platform objects with no namespace:

- `FinancialAccount`
- `FinancialAccount.Balance`
- `ParticipantRole` (a Metadata API type, not custom metadata)

A metadata deployment package built for a managed-package org contains `FinServ__`-prefixed API names throughout. Deploying this package to a platform-native Core FSC org will fail because those namespace-qualified names do not match any metadata in the target. The reverse is equally true. There is no automated conversion — every API name in the package must be audited and rewritten for the target model.

### Compliant Data Sharing Activation and OWD Dependency

CDS provides row-level sharing for regulated financial data. The share-table mechanism is controlled by three linked settings:

1. The `IndustriesSettings` metadata type enables CDS feature flags at the org level.
2. OWDs for Account, Opportunity, and Financial Deal must be Private or Public Read-Only for share-table entries to control access.
3. After CDS is activated, a sharing recalculation job must run to populate share-table rows for existing records.

Deploying `IndustriesSettings` to activate CDS on an org with Public Read/Write OWDs results in a state where CDS appears enabled but provides no access control — share-table entries exist but are irrelevant because the base OWD already grants access to everyone. This is a silent misconfiguration that will not surface as a deployment error.

---

## Common Patterns

### Phased Prerequisite-First Deployment Pattern

**When to use:** Initial FSC deployment to a new sandbox or production org where FSC has never been configured.

**How it works:**

Phase 0 — Org prerequisites (manual, cannot be scripted):
1. Get Person Accounts enabled — "Person accounts aren't enabled by default in Salesforce. To request person accounts, contact Salesforce."
2. Set OWDs for Account, Opportunity, and Financial Deal to Private (or Public Read-Only if full private is not required).
3. Confirm FSC managed package is installed (managed-package model) or Core FSC is provisioned (platform-native model).

Phase 1 — Deploy structural metadata:
```
sf project deploy start --metadata "RecordType:Account.Household,RecordType:Account.Person_Account" --target-org <alias>
```

Phase 2 — Deploy Industries settings:
```
sf project deploy start --metadata "IndustriesSettings" --target-org <alias>
```

Phase 3 — Deploy `ParticipantRole` components:
```
sf project deploy start --metadata "ParticipantRole" --target-org <alias>
```

Phase 4 — Trigger sharing recalculation (manual or via Apex):
```apex
// Trigger CDS share recalculation for Financial Accounts
// UNVERIFIED (2026-10-19): this batch class name is not in the Summer '26 Apex Reference; confirm it in the target org before scripting it
Database.executeBatch(new FinancialAccountShareRecalcBatch(), 200);
```

**Why not a single deploy wave:** Because Phase 0 requires manual org changes that block all subsequent metadata, and because a role deployed before its CDS flag and OWD are in place cannot be tested for the access it is meant to grant.

### Namespace Audit and Rewrite Pattern

**When to use:** Migrating metadata between a managed-package FSC org and a platform-native Core FSC org (or vice versa), or when promoting a pipeline built for one model to an org running the other.

**How it works:**

1. Export the full metadata package from the source org.
2. Run a namespace audit script to catalog all API names containing `FinServ__` (for managed-package to platform-native migration) or to identify bare API names that need the prefix added (for the reverse).
3. Perform a bulk find-and-replace on the metadata XML, updating all API names, field references, and custom metadata type references.
4. Validate the rewritten package against the target org's object model using `sf project deploy validate --dry-run`.
5. Deploy the validated, rewritten package.

**Why not skip the audit:** The namespace mismatch is invisible at the tool level — `sf project deploy start` does not warn you that a metadata API name does not match the target org's model. It simply fails with a generic component-not-found error that can be misdiagnosed as a missing dependency rather than a namespace mismatch.

### CDS Post-Deploy Validation Pattern

**When to use:** After deploying IndustriesSettings to activate CDS in a target org.

**How it works:**

1. Confirm OWDs are set correctly: Setup > Sharing Settings > check Account, Opportunity, Financial Deal.
2. Create a test Financial Account record and confirm a share-table row is written: `SELECT Id, UserOrGroupId, AccessLevel FROM FinancialAccountShare WHERE ParentId = '<test_id>'`.
3. Assign a Participant Role to the test record and confirm the share-table row updates.
4. Log in as a test user who should gain access via CDS and confirm they can see the record.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Deploying FSC to a net-new org | Phased prerequisite-first pattern; Person Accounts enabled before any metadata deploy | Household record types will fail to deploy without Person Accounts enabled |
| Migrating pipeline from managed-package to Core FSC org | Namespace audit and rewrite of all metadata XML before deploy | FinServ__-prefixed API names do not exist in platform-native orgs |
| CDS share table empty after deploy | Check OWDs first; trigger sharing recalculation job | OWDs must be Private/Public Read-Only; recalculation does not run automatically |
| `ParticipantRole` deploys but grants no access | Check `isActive`, `parentObject`, and that object's CDS flag in `IndustriesSettings` | The type has no record type reference; deploy success proves shape, not access |
| IndustriesSettings deploys but CDS shows no effect | Verify OWD setting for Account; check if CDS flag requires post-deploy activation step | CDS activation via IndustriesSettings does not apply retroactively to existing records |
| Deploying FSC to a scratch org for CI | Add the `FinancialServicesUser:<value>` and `PersonAccounts` features to the scratch org definition file | Both are documented scratch org features; the first adds the FSC Standard permission set license |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner deploying FSC metadata:

1. **Identify the FSC licensing model in the source and target orgs.** Check whether objects use the `FinServ__` namespace (managed-package) or bare names (platform-native Core FSC). If they differ, run the namespace audit and rewrite before any other step.
2. **Confirm Person Accounts are enabled in the target org.** Query `SELECT Id, DeveloperName FROM RecordType WHERE SobjectType = 'Account' AND IsPersonType = true` — `IsPersonType` is visible only when the person account feature is enabled. If not enabled, stop and request it from Salesforce; no metadata deploy turns it on.
3. **Verify OWD settings for Account, Opportunity, and Financial Deal.** Navigate to Setup > Sharing Settings and confirm each object is set to Private or Public Read-Only. If OWDs are Public Read/Write, update them before deploying CDS configuration.
4. **Deploy structural metadata in sequence:** first Account record types, then other FSC object record types. Validate each wave before proceeding: `sf project deploy validate --metadata "RecordType" --target-org <alias>`.
5. **Deploy IndustriesSettings** to activate CDS and other FSC feature flags: `sf project deploy start --metadata "IndustriesSettings" --target-org <alias>`. Confirm the deploy succeeds without errors.
6. **Deploy `ParticipantRole` components** after the CDS flags and OWDs are confirmed in the target: `sf project deploy start --metadata "ParticipantRole" --target-org <alias>`.
7. **Run CDS post-deploy validation:** confirm OWDs, trigger sharing recalculation if needed, and verify share-table rows are populated for test records. Log in as a test user to confirm row-level access is functioning correctly.

---

## Review Checklist

Run through these before marking FSC deployment work complete:

- [ ] Confirmed FSC licensing model (managed-package vs platform-native) is the same in source and target orgs, or namespace audit and rewrite has been completed
- [ ] Person Accounts are enabled in the target org before any household or Financial Account metadata was deployed
- [ ] OWDs for Account, Opportunity, and Financial Deal are set to Private or Public Read-Only before CDS metadata was deployed
- [ ] Each deployed `ParticipantRole` was checked for `isActive`, `parentObject`, and `defaultAccessLevel` against the intended access
- [ ] IndustriesSettings deploy succeeded without errors
- [ ] Post-deploy sharing recalculation job was triggered and completed
- [ ] Share-table rows verified for at least one test Financial Account record
- [ ] Test user login confirmed row-level access is functioning via CDS

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Person Account enablement is irreversible and blocks household metadata** — Attempting to deploy household Account record types or Relationship Group metadata before Person Accounts are enabled fails with a generic entity reference error. The root cause is not obvious from the error message. Get Person Accounts enabled (requested from Salesforce) before the first metadata deploy wave — and understand this change cannot be undone in the org.
2. **OWD mismatch silently breaks CDS without a deployment error** — Deploying `IndustriesSettings` to activate CDS on an org with Public Read/Write OWDs for Account succeeds with no errors. CDS appears active. But share-table entries have no access-control effect because the base OWD already grants everyone full access. This misconfiguration does not surface until a security audit or a pen-test reveals the data exposure.
3. **FinServ__ namespace renders metadata non-portable between FSC models** — A `package.xml` built from a managed-package FSC org will reference `FinServ__FinancialAccount__c`. Deploying this to a platform-native Core FSC org fails because that object does not exist under that name. The sf CLI error message ("Component not found") does not mention namespace as the cause, leading practitioners to incorrectly diagnose the issue as a missing dependency or wrong API version.
4. **IndustriesSettings does not backfill share-table rows for existing records** — After deploying CDS activation via IndustriesSettings, share-table rows are created for new records going forward but are not retroactively created for records that existed before CDS was activated. A sharing recalculation batch job must be explicitly triggered to populate shares for existing records. Skipping this step leaves pre-existing financial accounts invisible to users who should have access via CDS.
5. **A `ParticipantRole` deploy proves shape, not access** — `ParticipantRole` is a Metadata API type with `defaultAccessLevel`, `isActive`, `masterLabel`, and `parentObject`; it carries no record type reference. The deploy succeeds whether or not the role is active or its parent object has CDS enabled, so only a share-table and log-in-as test shows the role grants what was intended.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| FSC deployment phase plan | Numbered list of deployment batches in dependency order, with prerequisite checks listed for each phase |
| Namespace compatibility audit report | Inventory of all FinServ__-prefixed API names in the source package with their platform-native equivalents |
| CDS validation report | OWD status, share-table row counts, and test user access confirmation for post-deploy verification |

---

## Related Skills

- fsc-architecture-patterns — for FSC architectural decisions before deployment begins, including CDS design and household model choices
- fsc-data-model — for understanding FSC object relationships, Financial Account roll-up logic, and Relationship Groups that affect what must be deployed
- metadata-api-coverage-gaps — for understanding which FSC metadata types are not supported by the Metadata API and require manual configuration
- permission-set-deployment-ordering — for ordering permission set deployments that grant access to FSC objects and CDS-protected records
- post-deployment-validation — for the general post-deploy validation framework; FSC adds CDS-specific validation steps documented in this skill
- health-cloud-deployment-patterns — parallel skill for Health Cloud (similar Industries Cloud deployment sequencing patterns)
