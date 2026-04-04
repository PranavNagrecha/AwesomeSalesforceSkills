---
name: permission-set-deployment-ordering
description: "Use when deploying permission sets, permission set groups, or profiles and encountering cross-reference errors, silent permission loss, or ordering failures. Triggers: 'permission set deployment fails', 'cross-reference id error during deploy', 'permissions disappear after deployment', 'permission set group deployment error'. NOT for permission set design or architecture decisions (use permission-set-architecture), NOT for creating permission sets from scratch (use admin/permission-set-architecture)."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "my deployment fails with a cross-reference id error on a permission set"
  - "permissions are getting wiped out after I deploy a permission set"
  - "my permission set group deployment fails because constituent sets are not found"
  - "how do I safely deploy permission sets without losing existing permissions"
  - "ConnectedApp permission in permission set causes cross-reference error in same batch"
tags:
  - permission-sets
  - deployment
  - metadata-api
  - permission-set-groups
  - deployment-ordering
inputs:
  - "List of permission sets and permission set groups being deployed"
  - "Target org environment (sandbox, production, scratch org)"
  - "Deployment tool (sf CLI, change sets, Metadata API direct)"
  - "Any cross-reference error messages from the failed deployment"
outputs:
  - "Ordered deployment sequence to avoid cross-reference errors"
  - "Permission set validation checklist before deployment"
  - "Guidance on handling ConnectedApp permission conflicts"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Permission Set Deployment Ordering

Use this skill when deploying permission sets, permission set groups, or profiles and encountering cross-reference errors, silent permission wipeouts, or deployment ordering failures. It covers the full-replace behavior of the Metadata API for permission sets and the correct sequencing rules that prevent data loss in production deployments.

---

## Before Starting

Gather this context before working on anything in this domain:

- Know whether you are deploying permission sets, permission set groups, or both. PSGs require all constituent permission sets to already exist in the target org before the group can land.
- Understand that the Metadata API performs a **full-replace** on permission sets (API v40+), not a merge. Any permission not in the deployed XML is silently removed from the target org.
- Confirm whether your batch includes a ConnectedApp and a permission set or PSG referencing that ConnectedApp — this combination triggers a known cross-reference error when both land in the same deploy transaction.

---

## Core Concepts

### Full-Replace Semantics (API v40+)

Since API version 40.0, deploying a PermissionSet metadata type completely overwrites the existing record in the target org. If you retrieve a permission set, remove three field permissions from the XML, and deploy it — those three permissions are gone in the target. There is no merge; the deployed XML is authoritative.

This behavior means: **always retrieve the current state from the target org before building a deployment package**. Never deploy a permission set constructed from scratch unless you have confirmed the target org has no existing configuration to preserve.

### Referenced Objects Must Exist First

Permission sets that grant access to custom objects, custom fields, Apex classes, or Visualforce pages require those components to already exist in the target org before the permission set deploys. If the deploy batch includes both the custom object and the permission set that grants access to it, order matters: the object must land before the permission set.

In a Metadata API deployment, objects are processed before permission sets by default because the deployment engine uses a built-in ordering. However, in split deployments (object in one deploy, PS in another), ensure the first deploy completes successfully before starting the second.

### PSG Constituent Ordering

Permission Set Groups require each constituent Permission Set to already exist in the target org (or be deployed in the same batch before the PSG is evaluated). If a PSG references `PS_A` and `PS_B`, both must be present before `PSG_1` is processed.

**Safe pattern**: deploy constituent PSets first (separate deploy or earlier in the batch), then deploy the PSG in a subsequent deploy. Do not rely on implicit ordering within a single batch unless you have verified the Metadata API processes them in the correct order.

### ConnectedApp Cross-Reference Bug

A known platform bug causes a cross-reference error when a ConnectedApp and a permission set or PSG that references that ConnectedApp are both included in the same deployment batch. The workaround is to deploy the ConnectedApp in a separate deploy from the permission set that grants access to it.

---

## Common Patterns

### Retrieve-Then-Deploy Pattern

**When to use:** Any time you need to update a permission set without inadvertently removing existing permissions.

**How it works:**
1. Retrieve the current permission set from the target org: `sf project retrieve start --metadata "PermissionSet:My_PS"`
2. Make only the needed changes in the local XML.
3. Deploy the modified file: `sf project deploy start --metadata "PermissionSet:My_PS"`

**Why not construct from scratch:** A constructed-from-scratch XML only contains the permissions you explicitly added. All permissions already granted in the target org that are not in your XML will be silently removed on deploy.

### Sequential Batch Deployment Pattern

**When to use:** Deploying permission set groups whose constituent sets may not already exist in the target.

**How it works:**
1. Deploy 1: `PermissionSet:PS_A`, `PermissionSet:PS_B` — confirms both land and pass tests.
2. Deploy 2: `PermissionSetGroup:PSG_1` — PSG references PS_A and PS_B, which now exist.

**Why not a single batch:** While the Metadata API often processes PSets before PSGs in a single batch, this is not guaranteed and there is no documented specification. The sequential pattern is explicit and repeatable.

### ConnectedApp Isolation Pattern

**When to use:** Deploying a ConnectedApp and a PermissionSet or PSG that references it.

**How it works:**
1. Deploy 1: `ConnectedApp:My_App`
2. Deploy 2: `PermissionSet:My_PS` (which grants access to My_App)

**Why not together:** The cross-reference resolution order in the same batch causes a platform error even though both components are present. Separation into sequential deploys resolves it.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Updating an existing permission set | Retrieve from target first, edit XML, deploy | Prevents silent permission wipeout |
| Deploying new PSG to org that doesn't have constituent PSets | Two-step: PSets first, then PSG | PSG validation requires constituent PSets to exist |
| Deploying ConnectedApp + PS that references it | Two separate deploys | Known platform bug — same batch causes cross-reference error |
| Deploying permission set to scratch org (fresh) | Single deploy fine | No existing permissions to preserve |
| CI pipeline deploys entire org metadata | Ensure object metadata deploys before PS in same batch | Referenced objects must exist for PS to validate |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner deploying permission sets:

1. **Identify all permission sets and PSGs in the deployment package.** List their dependencies: which custom objects, fields, Apex classes, or ConnectedApps they reference.
2. **Retrieve the current state from the target org** for any permission set that already exists there. Use `sf project retrieve start --metadata "PermissionSet:<name>"` to get the authoritative current XML.
3. **Merge your changes** into the retrieved XML rather than replacing it. Only modify the specific permissions you intend to add, remove, or change.
4. **Check for ConnectedApp references.** If any PS or PSG in the batch references a ConnectedApp also in the batch, split into two sequential deploys: ConnectedApp first, then the PS/PSG.
5. **Sequence the deployment batches.** Deploy constituent PSets before PSGs. Deploy custom objects/fields before the PSets that reference them.
6. **Validate deploy first** (`sf project deploy validate`) before running the actual deploy in production. Review any cross-reference errors in the validation output and resolve them.
7. **Confirm post-deploy** that key permission grants are still intact in the target org. Use `sf project retrieve start` to pull the deployed PS and diff against expectations.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Retrieved current state of all existing permission sets from the target org before building deploy package
- [ ] Verified no ConnectedApp and permission set referencing it are in the same deploy batch
- [ ] Confirmed all constituent PSets deploy before any PSG that references them
- [ ] Confirmed all referenced custom objects, fields, and Apex classes exist in target before PS deploys
- [ ] Ran `sf project deploy validate` and resolved all errors before actual deploy
- [ ] Post-deploy verification: retrieved deployed PS and confirmed expected permissions are present

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Silent permission wipeout on full-replace** — Deploying a PermissionSet that is missing permissions which exist in the target org silently removes those permissions. There is no warning or error. Always retrieve from the target first and perform a diff before deploying.
2. **ConnectedApp cross-reference error in same batch** — Including a ConnectedApp and a PermissionSet or PSG referencing it in the same deployment batch causes a CANNOT_INSERT_UPDATE_ACTIVATE_ENTITY or cross-reference error. The fix is always a sequential deploy: ConnectedApp first, permission set second.
3. **PSG validation failure when PSets are missing** — A Permission Set Group deployed to an org where one of its constituent PSets does not yet exist will fail with a validation error referencing the missing set. PSets must be deployed before PSGs that reference them.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Ordered deployment plan | A numbered list of deployment batches in sequence, each listing the metadata types included |
| Pre-deploy PS diff | Side-by-side comparison of current target org PS vs the PS about to be deployed, highlighting permissions that will be removed |

---

## Related Skills

- permission-set-architecture — when to design PSets vs PSGs vs Profiles for user access strategy
- change-set-deployment — for change-set-based deployment workflows where metadata ordering is also relevant
- deployment-error-troubleshooting — for diagnosing the specific error messages that arise from PS deployment failures
