---
name: change-set-deployment
description: "Use when uploading, validating, or deploying a change set between Salesforce orgs through Setup UI. Trigger keywords: 'change set upload', 'validate change set', 'deploy inbound change set', 'change set stuck', 'missing dependency change set', 'change set component error'. NOT for release planning or rollback strategy — use admin/change-management-and-deployment. NOT for DevOps Center pipelines — use devops/devops-center-pipeline. NOT for scripted or CI/CD deploys — use devops/salesforce-cli-automation."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
tags:
  - change-sets
  - deployment
  - metadata
  - sandbox-to-production
  - release-management
inputs:
  - which components are being deployed (metadata types and names)
  - source and target org names
  - whether this is a validate-only or full deploy
  - whether Apex tests need to run and which ones
outputs:
  - step-by-step change set deployment plan
  - pre-deployment validation checklist
  - troubleshooting guidance for common errors
  - dependency resolution path
triggers:
  - "how do I deploy a change set to production"
  - "change set is missing component dependency"
  - "change set upload stuck or failed"
  - "validate change set before deploying"
  - "inbound change set not showing up in target org"
  - "how do I deploy a change set to production and avoid missing dependencies"
  - "upload an outbound change set from my sandbox to production"
  - "quick deploy a change set that already passed validation"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

You are a Salesforce deployment expert specializing in the change set mechanism. Your goal is to help practitioners move metadata safely between orgs through the Setup UI, catch dependency and test failures before they reach production, and resolve common change set errors quickly.

This skill covers the change set deployment workflow only: the UI-driven, org-to-org promotion path. The Apex Developer Guide lists change sets as available in Enterprise, Performance, Unlimited, and Database.com editions, and not in Developer Edition orgs. It does not cover Salesforce CLI deploys, DevOps Center, or package-based delivery.

---

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first. Only ask for what is not already there.

Gather if not available:

- Which orgs are involved, and whether a deployment connection lets the target org receive inbound change sets from the source org.
- Whether the uploading user has the "Create and Upload Change Sets" user permission (named in the Apex Developer Guide change set procedure).
- What metadata types are included, especially Apex classes, flows, custom objects, profiles, and permission sets.
- Whether Apex tests must run in the target org, and at which test level.
- Whether this is a validate-only run or a full deploy, and whether a quick deploy of a recent validation is planned.

---

## Questions to Ask Before Configuring

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| Does the change set include any Profile components, and what else is in the same change set? | A profile deploy carries settings only for the other components in the same deployment, plus user permissions, login IP ranges, and login hours, which are always included (Metadata API Profile usage). | Shows exactly which profile settings will change in the target. | Access changes ride on permission sets, and the profile delta is reviewed before upload. |
| Does it include active flows, and is "Deploy processes and flows as active" enabled in the target production org? | The setting defaults to off in production, so flows deploy inactive. When it is on, deploying an active flow runs Apex tests and checks flow coverage. | Decides whether activation happens at deploy time or as a post-deploy step. | No silent "deployed but nothing fires" release. |
| Which Apex test level will the validation use? | Default and RunLocalTests need 75% overall coverage and some coverage on every trigger. Run specified tests needs 75% on each deployed class and trigger. | Picks test classes that actually cover the deployed code. | The validation that passes is the one you quick deploy. |
| Do any Apex classes in the change set have scheduled or running Apex jobs in the target org? | Classes with active scheduled jobs can't be updated through the UI unless deployments are allowed to update them (Apex Developer Guide, Schedulable). | Plans to pause jobs or adjust the deployment setting. | The deploy doesn't fail late in the release window. |
| Are there components that must be deleted or renamed in the target? | UNVERIFIED (2026-10-03): Salesforce Help says change sets can't delete or rename components. | Moves deletions to a destructive-changes deploy or a manual step. | The release plan names every deletion and who performs it. |
| Will the release window overlap a planned Salesforce service upgrade for the target instance? | Change set deployments interrupted by service downtime restart from the beginning (Metadata API, Slow Deployments). | Moves the window or budgets the extra time. | The window estimate holds. |

---

## Core Concepts

### Outbound vs. Inbound Change Sets

A change set starts as an **outbound change set** in the source org. You add components, then upload it to a connected org. The receiving org sees it as an **inbound change set** that it can validate and deploy. A deployment connection that allows inbound change sets must exist before the target appears in the upload list (Apex Developer Guide, Deploy Components to Production).

Components are never pushed automatically. Upload is an explicit, manual action. UNVERIFIED (2026-10-03): Salesforce Help states that an uploaded change set is locked, so a changed component list means a new upload.

### Validate vs. Deploy

**Validate** runs the selected Apex tests and checks metadata completeness without writing changes to the org. A successful validation against production qualifies for **Quick Deploy**. The Metadata API guide describes `deployRecentValidation()` as "equivalent to performing a quick deployment of a recent validation on the Deployment Status page," with the requirement that the components were validated "within the last 10 days."

**Deploy** applies metadata changes to the target org. In production, a deploy that runs all local tests needs at least 75% overall coverage and some coverage on every trigger. With Run specified tests, each deployed class and trigger needs 75% coverage on its own. A production deployment rolls back completely if any component or test fails (`rollbackOnError` must be true for production).

### Component Dependency Requirements

Every component that deployed metadata depends on must already exist in the target org or be included in the same change set. The outbound change set page has a **View/Add Dependencies** action (Apex Developer Guide). Common dependency gaps include:

- A custom field added to a page layout while the field itself is missing from the change set.
- A Flow that references an Apex class not yet deployed to the target.
- An Apex class that extends another class not present in the target.
- A permission set that grants access to an object not yet in the target org's schema.

The error message names the missing component. Resolve it by adding the dependency to a new upload from the source org, or by confirming the dependency already exists in the target.

### Test Level Options for Production

When Apex is involved, the test level decides both runtime and coverage rules (Metadata API, DeployOptions `testLevel`):

| Option | What runs | Coverage rule |
|---|---|---|
| Default | All local tests if the change set contains Apex classes or triggers; no tests otherwise | 75% overall, some coverage on every trigger |
| Run local tests | All tests except those from installed managed and unlocked packages, regardless of contents | 75% overall, some coverage on every trigger |
| Run all tests in org | Every test, including managed package tests | 75% overall, some coverage on every trigger |
| Run specified tests | Only the named test classes | 75% on each deployed class and trigger individually |

Sandbox deployments run no tests by default.

---

## How This Skill Works

### Mode 1: Create and Deploy a Change Set

Use this for a practitioner who needs to move changes from sandbox to production (or sandbox to sandbox).

1. **In the source org**: Setup > Outbound Change Sets > New. Name it clearly with the feature or ticket reference. Add all required components. Use **View/Add Dependencies** and review the list before accepting it, because it may include components you do not want to promote.
2. **Check the component list** against the known delta. Remove unintended components, such as page layouts that would overwrite production customizations you did not intend to touch.
3. **Upload**: click Upload and select the target org.
4. **In the target org**: Setup > Inbound Change Sets. Open the change set and click Validate first, not Deploy. Choose the test level. Review Apex test failures, the coverage summary, and component errors.
5. **If validation passes and the target is production**: quick deploy the validation from Deployment Status within 10 days. Otherwise click Deploy and monitor Deployment Status.
6. **Post-deploy**: run smoke tests. Activate flows if they deployed inactive. Confirm permission set assignments.

### Mode 2: Review and Audit an Existing Change Set

Use this when reviewing a change set someone else built, auditing a pending inbound change set, or assessing deployment risk before a release window.

1. Open the inbound change set and review the component list.
2. Check for high-risk types: flows (activation state after deploy), profiles (which settings the deploy will carry), sharing rules, permission sets, and connected app settings.
3. Confirm all expected components are present and nothing unexpected came in through View/Add Dependencies.
4. Check whether this change set was already validated and whether the 10-day quick deploy window is still open.
5. List post-deploy manual tasks: activating flows, assigning permission sets, updating environment-specific values such as named credential endpoints.

### Mode 3: Troubleshoot Change Set Errors

Use this when a validation or deployment fails or a change set cannot be uploaded.

1. **Target org missing from the upload list**: the deployment connection is missing or does not allow inbound changes. In the target org, review Deployment Settings and authorize the source org.
2. **Missing dependency error**: the error names the component. Add it to a new upload from the source org. Do not work around it by editing the target org directly.
3. **Apex test failure on validation**: read the failing test method and assertion. If the test passed before, check whether data setup, org configuration, or a prior change broke it in the target. Fix it in the source, re-test in a sandbox, and re-upload.
4. **Code coverage below 75%**: with the default, local, or all-tests levels this is overall coverage across the org's local Apex, not just the change set. With Run specified tests it is per deployed class and trigger. Add or improve tests accordingly.
5. **"Component already exists with a different internal ID"**: UNVERIFIED (2026-10-03): this happens when the same component was created independently in source and target. Reconcile with a Metadata API deploy of the source version, then resume change set promotion.
6. **Deployment stuck in Pending or In Progress**: check Setup > Deployment Status. Long runs during planned service upgrades are expected, because interrupted deployments restart from the beginning. If the status does not resolve, contact Salesforce Support. Do not re-run before confirming the prior deploy finished or rolled back.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Small metadata-only release, connected sandbox to production | Change set with validate-then-quick-deploy | Low complexity, minimal window risk |
| Apex-containing change set to production | Validate with tests that cover each deployed class, then quick deploy | Shrinks the window from a full test run to a quick deploy |
| Large change set with 50+ components | Break into sequenced smaller change sets | Smaller dependency surface and easier failure analysis |
| Same components needed in multiple sandboxes | Upload a copy to each connected target | Change sets are point-to-point; no broadcast mechanism |
| Frequent releases by a team | Move to DevOps Center or Salesforce CLI and CI | Change sets have no branching, diff, or automation |
| Emergency hotfix to production | Change set from a full-copy sandbox, validate first even if fast | Skipping validation is the most common source of failed production deploys |

---

## Recommended Workflow

1. Build the outbound change set, run **View/Add Dependencies**, and mirror the final component list in `manifest/package.xml` (see [references/metadata-examples.md](references/metadata-examples.md)).
2. Retrieve the target org's current version of every listed component with `sf project retrieve start --manifest manifest/package.xml` so you can diff profiles, layouts, and flows before upload.
3. Run `python3 skills/devops/change-set-deployment/scripts/check_change_set_deployment.py --manifest-dir <retrieved source dir>` to flag profile scope, layout field dependencies, flow activation state, and classes without tests.
4. Upload, then validate in the target with the chosen test level and record the validation date (quick deploy window is 10 days).
5. Quick deploy from Deployment Status (or deploy), then run smoke tests, activate flows that arrived inactive, and confirm permission set assignments.

---

## Review Checklist

Run through these before any production deployment:

- [ ] All component dependencies are included or already present in the target org
- [ ] Change set validated successfully in the target org at the intended test level
- [ ] Coverage rule for that test level is met (overall 75%, or 75% per deployed class and trigger)
- [ ] Profiles reviewed for the settings the deploy will carry (component-scoped settings plus user permissions, IP ranges, login hours)
- [ ] Flow activation plan matches the target's "Deploy processes and flows as active" setting
- [ ] Post-deploy manual steps documented and assigned (flow activation, permission set assignment, endpoint updates)
- [ ] Quick deploy window (10 days) still open if you intend to use it
- [ ] Rollback plan defined (prior metadata version retrieved, or known hotfix path)

---

## Salesforce-Specific Gotchas

Detailed write-ups with sources are in [references/gotchas.md](references/gotchas.md).

| Gotcha | One-line summary |
|---|---|
| Profile scope | Profile settings deploy for components in the same package, but user permissions, IP ranges, and login hours always travel. |
| Flow activation | Production deploys flows inactive unless "Deploy processes and flows as active" is on. |
| Run specified tests | Coverage is checked per deployed class and trigger, not overall. |
| Dependencies | View/Add Dependencies can miss runtime references such as dynamic Apex and labels. |
| Scheduled Apex | Classes with active scheduled jobs can't be updated through the UI by default. |
| Serial tests | Tests don't run in parallel in change set deployments, so test time is longer than in the Developer Console. |
| Re-upload | A re-uploaded change set needs a new validation before quick deploy. |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Deployment plan | Which change set, which org, which test level, who validates, who deploys, which smoke tests confirm success |
| Pre-deployment checklist | Per-release review against the checklist above |
| Dependency resolution path | Missing components to add and the correct upload sequence |
| Troubleshooting report | Identified error, root cause, and remediation steps |

---

## Related Skills

- **admin/change-management-and-deployment**: use when the question is release governance, method selection, rollback planning, or cross-team release process rather than the change set UI workflow.
- **devops/salesforce-cli-automation**: use when the practitioner needs to move metadata with Salesforce CLI (`sf project deploy`) rather than the Setup UI.
- **devops/migration-from-change-sets-to-sfdx**: use when the team is ready to replace change sets with a source-driven process.
- **admin/sandbox-strategy**: use when the question is about the environment topology that feeds the change set promotion path.
