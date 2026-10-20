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
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Permission Set Deployment Ordering

Use this skill when deploying permission sets, permission set groups, or profiles and encountering cross-reference errors, permission loss, or deployment ordering failures. It covers the overwrite risk the Metadata API guide describes for permission sets (api_meta 264 L97416-97418), the different overlay behaviour of Profiles (L100265-100268), and the sequencing rules that prevent data loss in production deployments.

---

## Before Starting

Gather this context before working on anything in this domain:

- Know whether you are deploying permission sets, permission set groups, or both. PSGs require all constituent permission sets to already exist in the target org before the group can land. UNVERIFIED (2026-10-20): api_meta 264 L98043 only says the `permissionSets` field names "a permission set or permission sets included in the permission set group"; no passage in the 12 Winter '27 guides or the two 262 guides states an existence or ordering rule.
- Understand that from API version 40.0 a retrieve returns all of a permission set's metadata and "when you deploy a permission set, you must include all of its metadata to avoid accidentally overwriting the permission set's contents" (api_meta 264 L97416-97418). Treat the deployed XML as authoritative, not a merge. Whether the loss raises a warning is not stated: UNVERIFIED (2026-10-20): "silently removed, no warning" is the package's inference from L97418.
- Confirm whether your batch includes a ConnectedApp and a permission set or PSG that references it. The documented link runs from the app: ConnectedApp has a `permissionSetName` field naming the permission set (API 46.0+, api_meta 264 L37225-37226). A "cross-reference error when both land in the same transaction" is UNVERIFIED (2026-10-20): grep of both corpora finds no such statement.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Does each permission set in the package already exist in the target org? | Gotcha 1: the deployed XML must carry all of the set's metadata (api_meta 264 L97417-97418) | A retrieve-first list of existing sets, so nothing is built from scratch |
| Which org produced the XML, and does it hold fewer objects, fields or classes than the target? | Gotcha 1: a thinner permission set source overwrites grants in the target; Gotcha 3 (references/gotchas.md): a profile retrieve carries FLS only for objects in the same RetrieveRequest (api_meta 264 L100261-100263) | The source-vs-target diff to review before deploy |
| Are Profiles in the same package? | Gotcha 3: a Profile deploy overlays the target, so removing a permission from the XML does not remove it in the org (api_meta 264 L100265-100268) | A decision to set removals explicitly or manage them in permission sets |
| Does a ConnectedApp in the package name a package permission set in `permissionSetName`? | Gotcha 2 and Core Concepts: the documented link is ConnectedApp to PS (L37225) | Whether to split the batch as a precaution |
| Which PSGs are in scope, and do their constituent sets ship in the same release? | SKILL.md Gotcha 3 (PSG after PSets): ordered deploys must be submitted one at a time (api_meta 264 L4246-4249) | The ordered batch list |
| Does a PSG carry a muting permission set? | Gotcha 4 (references/gotchas.md): the group's `mutingPermissionSets` field names a set of the separate MutingPermissionSet type (api_meta 264 L92411, L98039-98041) | The muting set added to the retrieve and deploy list |
| Can the pipeline guarantee batch order, or are deploys queued? | Queued deploys are not necessarily run in submitted order (api_meta 264 L4246-4249) | Stage dependencies written into the pipeline |

A proper configuration adds an ordered, retrieve-first plan and a review of every permission about to be overwritten; just deploying the XML gives you neither.

---

## Core Concepts

### Include-All-Metadata Rule (API v40+)

Since API version 40.0, retrieving a permission set returns everything the Metadata API exposes for it, and the guide tells you to include all of that metadata on deploy "to avoid accidentally overwriting the permission set's contents" (api_meta 264 L97416-97418; at API 39.0 and earlier only app and system permissions travel, L97419-97421). If you retrieve a permission set, remove three field permissions from the XML, and deploy it, treat those three permissions as gone in the target: the deployed XML is authoritative. "Completely overwrites" and "no merge" are this package's reading of that sentence: UNVERIFIED (2026-10-20): the guide states the overwrite risk but no field-by-field delete semantics.

This behavior means: **always retrieve the current state from the target org before building a deployment package**. Never deploy a permission set constructed from scratch unless you have confirmed the target org has no existing configuration to preserve.

### Referenced Objects Must Exist First

Permission sets that grant access to custom objects, custom fields, Apex classes, or Visualforce pages need those components to be retrievable and deployable alongside them: the guide says "when retrieving object or field permissions, you must also retrieve the associated object" (api_meta 264 L2594-2596, package.xml retrieval guidance). UNVERIFIED (2026-10-20): that the object must already exist in the target before the permission set deploys, and that the Metadata API applies a "built-in ordering" that processes objects before permission sets, are not stated in either corpus.

In split deployments (object in one deploy, PS in another), ensure the first deploy completes successfully before starting the second. The guide's own rule: queued deployments "are not necessarily executed in the order in which they were submitted. To execute deployments in a particular order, submit them one at a time after the previous deployment has completed successfully" (api_meta 264 L4246-4249).

### PSG Constituent Ordering

Permission Set Groups (API 45.0+, api_meta 264 L98009) reference constituent Permission Sets through the `permissionSets` field and may carry a muting permission set through `mutingPermissionSets` (API 46.0+, L98039-98041); the individual permissions live in the referenced permission set, not in the group (L98056-98057). UNVERIFIED (2026-10-20): that each constituent must already exist, or precede the PSG inside one batch; the guide states no such rule.

**Safe pattern**: deploy constituent PSets first in a separate deploy, wait for it to succeed, then deploy the PSG, which is the one-at-a-time ordering the guide prescribes (api_meta 264 L4246-4249). Do not rely on implicit ordering within a single batch.

### ConnectedApp Cross-Reference Bug

UNVERIFIED (2026-10-20): a "known platform bug" that raises a cross-reference error when a ConnectedApp and a permission set or PSG that references it share a batch. Neither corpus describes it; treat the isolation pattern below as a precaution, not a documented requirement. What the guide does document: ConnectedApp carries `permissionSetName` (API 46.0+, api_meta 264 L37225-37226, sample at L38057) and `profileName` (L37255-37257), both requiring `isAdminApproved` true on the OAuth config (L37239-37240); a PermissionSet's `applicationVisibilities` is described for "standard and custom apps" (L97467-97471), with no mention of connected apps. Note also: connected app creation is restricted as of Spring '26 (L37161-37163), so an existing app's metadata is what you will usually deploy.

---

## Common Patterns

### Retrieve-Then-Deploy Pattern

**When to use:** Any time you need to update a permission set without inadvertently removing existing permissions.

**How it works:**
1. Retrieve the current permission set from the target org: `sf project retrieve start --metadata "PermissionSet:My_PS"`
2. Make only the needed changes in the local XML.
3. Deploy the modified file: `sf project deploy start --metadata "PermissionSet:My_PS"`

**Why not construct from scratch:** A constructed-from-scratch XML only contains the permissions you explicitly added. All permissions already granted in the target org that are not in your XML are at risk of being lost on deploy (api_meta 264 L97417-97418).

### Sequential Batch Deployment Pattern

**When to use:** Deploying permission set groups whose constituent sets may not already exist in the target.

**How it works:**
1. Deploy 1: `PermissionSet:PS_A`, `PermissionSet:PS_B` — confirms both land and pass tests.
2. Deploy 2: `PermissionSetGroup:PSG_1` — PSG references PS_A and PS_B, which now exist.

**Why not a single batch:** The guide gives no ordering specification for components inside one batch, and says ordered deploys must be submitted one at a time after the previous one succeeds (api_meta 264 L4246-4249). The sequential pattern is explicit and repeatable.

### ConnectedApp Isolation Pattern

**When to use:** Deploying a ConnectedApp and a PermissionSet or PSG that references it.

**How it works:**
1. Deploy 1: `ConnectedApp:My_App`
2. Deploy 2: `PermissionSet:My_PS` (which grants access to My_App)

**Why not together:** UNVERIFIED (2026-10-20): the claim that same-batch resolution order causes a platform error is not in either corpus; separation is a precaution that costs one extra deploy.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Updating an existing permission set | Retrieve from target first, edit XML, deploy | Prevents permission loss |
| Deploying new PSG to org that doesn't have constituent PSets | Two-step: PSets first, then PSG | Ordered deploys go one at a time (api_meta 264 L4246-4249); "PSG validation requires constituent PSets" is UNVERIFIED (2026-10-20) |
| Deploying ConnectedApp + PS that references it | Two separate deploys | Precaution; the "known platform bug" is UNVERIFIED (2026-10-20) |
| Deploying permission set to scratch org (fresh) | Single deploy fine | No existing permissions to preserve |
| CI pipeline deploys entire org metadata | Ensure object metadata deploys before PS in same batch | Retrieve the objects with their permissions (api_meta 264 L2594-2596, package.xml retrieval guidance); "must exist for PS to validate" is UNVERIFIED (2026-10-20) |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner deploying permission sets:

1. **Identify all permission sets and PSGs in the deployment package.** List their dependencies: which custom objects, fields, Apex classes, or ConnectedApps they reference.
2. **Retrieve the current state from the target org** for any permission set that already exists there. Use `sf project retrieve start --metadata "PermissionSet:<name>"` to get the authoritative current XML.
3. **Merge your changes** into the retrieved XML rather than replacing it. Only modify the specific permissions you intend to add, remove, or change.
4. **Check for ConnectedApp references.** If any PS or PSG in the batch references a ConnectedApp also in the batch, split into two sequential deploys: ConnectedApp first, then the PS/PSG.
5. **Sequence the deployment batches.** Deploy constituent PSets before PSGs. Deploy custom objects/fields before the PSets that reference them.
6. **Validate deploy first** (`sf project deploy validate --manifest manifest/package.xml --target-org <alias> --test-level RunLocalTests`, sfdx_dev 264 L14359-14360; `sf project deploy start --dry-run` is the other documented form, api_meta 264 L4114) before running the actual deploy in production. Review any cross-reference errors in the validation output and resolve them.
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

1. **Permission wipeout on full-replace** — The guide says to include all of a permission set's metadata when you deploy, "to avoid accidentally overwriting the permission set's contents" (api_meta 264 L97417-97418). Permissions missing from your XML are at risk; "silently, with no warning or error" is UNVERIFIED (2026-10-20). Always retrieve from the target first and diff before deploying.
2. **ConnectedApp cross-reference error in same batch** — UNVERIFIED (2026-10-20): the CANNOT_INSERT_UPDATE_ACTIVATE_ENTITY or cross-reference error for a ConnectedApp and a PermissionSet or PSG in one batch is in neither corpus. The precaution is a sequential deploy: ConnectedApp first, permission set second.
3. **PSG validation failure when PSets are missing** — UNVERIFIED (2026-10-20): the "validation error referencing the missing set" is in neither corpus. Deploy PSets before PSGs that reference them, one deploy at a time (api_meta 264 L4246-4249).

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
