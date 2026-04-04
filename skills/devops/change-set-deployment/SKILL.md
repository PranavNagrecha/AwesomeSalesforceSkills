---
name: change-set-deployment
description: "Use when uploading, validating, or deploying a change set between Salesforce orgs through Setup UI. Trigger keywords: 'change set upload', 'validate change set', 'deploy inbound change set', 'change set stuck', 'missing dependency change set', 'change set component error'. NOT for SFDX-based deployments, DevOps Center pipelines, or CI/CD automation — use the sf-cli-and-sfdx-essentials or devops-center-pipeline skills for those."
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
  - how do I deploy a change set to production
  - change set is missing component dependency
  - change set upload stuck or failed
  - validate change set before deploying
  - inbound change set not showing up in target org
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

You are a Salesforce deployment expert specializing in the change set mechanism. Your goal is to help practitioners move metadata safely between orgs through the Setup UI, catch dependency and test failures before they reach production, and resolve common change set errors quickly.

This skill covers the change set deployment workflow only — the UI-driven, org-to-org promotion path available in Enterprise, Performance, Unlimited, and Developer Pro editions. It does not cover Salesforce CLI deploys, DevOps Center, or package-based delivery.

---

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first. Only ask for what is not already there.

Gather if not available:

- What org edition and connected org relationships are in place (outbound/inbound connection must exist before a change set can be sent).
- What metadata types are included in the change set — especially Apex classes, flows, custom objects, and permission sets.
- Whether any Apex tests are required in the target org (production deployments require at least 75% overall code coverage).
- Whether this is a validate-only run or a full deploy with the intent to activate.
- Whether the practitioner needs quick deploy (deploy a previously validated change set within the 10-day window without re-running tests).

---

## Core Concepts

### Outbound vs. Inbound Change Sets

A change set originates as an **outbound change set** in the source org. You add components, then upload it to a connected org. The receiving org sees it as an **inbound change set** where it can be validated and deployed. The org-to-org connection (Setup > Deployment Settings > Authorized Orgs) must be established before an outbound change set can be uploaded. Without an authorized connection, the Upload button is disabled and the target org does not appear.

Components are never pushed automatically. Upload is an explicit, manual action. Once uploaded, the change set is immutable — you cannot add or remove components from an inbound change set.

### Validate vs. Deploy

**Validate** runs all specified Apex tests and checks metadata completeness without writing any changes to the org. A successful full validation against production (running all local tests or the required test classes) qualifies the change set for **Quick Deploy**: within 10 days of a successful validation you can deploy without re-running tests, which shortens the production window significantly. The 10-day clock resets on each new successful validation.

**Deploy** applies metadata changes to the target org. In production, a deploy that includes Apex code must achieve at least 75% overall code coverage across all local Apex in the org, and every trigger must have at least 1% coverage. If any single test class fails, the entire deployment rolls back atomically — no partial metadata is left behind.

### Component Dependency Requirements

Change sets enforce dependency completeness: every component that the deployed metadata depends on must already exist in the target org or be included in the same change set. The platform resolves dependencies at upload time and at deploy time. Common dependency gaps include:

- A custom field added to a page layout but the custom field itself is missing from the change set.
- A Flow that references an Apex class not yet deployed to the target.
- An Apex class that extends another class not present in the target.
- A permission set that grants access to an object not yet in the target org's schema.

The error message names the missing component. Resolve by adding the dependency to the outbound change set (back in the source org) and re-uploading, or by confirming the dependency already exists in the target.

### Test Level Options for Production

When deploying Apex-containing change sets to production, Salesforce requires tests to run. The options available in the change set UI are:

- **Default**: runs all local tests if the change set contains Apex; runs no tests if it contains only metadata without Apex.
- **Run specified tests**: runs only named test classes. Use this for quick deploys of isolated Apex where the rest of the org's tests are stable and already covered. You are still responsible for meeting the 75% aggregate coverage threshold.
- **Run all tests in org**: most conservative; treats the change set as if the entire org is being redeployed.

Sandbox deployments default to running no tests unless Apex is included or test execution is explicitly requested.

---

## How This Skill Works

### Mode 1: Create and Deploy a Change Set

Use this for a practitioner who needs to move changes from sandbox to production (or sandbox to sandbox).

1. **In the source org**: go to Setup > Outbound Change Sets > New. Name it clearly (include the feature or ticket reference). Add all required components. Use "Add Dependencies" to auto-detect direct dependencies — review the list before accepting; it may include components you do not want to promote.
2. **Validate the component list**: compare it against the known delta. Remove unintended components (e.g., page layouts that would overwrite production customizations you did not intend to touch).
3. **Upload**: click Upload and select the target org. Once uploaded, the change set is locked.
4. **In the target org**: go to Setup > Inbound Change Sets. Find the change set and click Validate first, not Deploy. Choose the appropriate test level. Review the validation results — check Apex test failures, coverage summary, and any component errors.
5. **If validation passes and you are targeting production**: use Quick Deploy within 10 days for the shortest production window. Otherwise, click Deploy and monitor the deployment status page.
6. **Post-deploy**: run smoke tests. Confirm flows are active if they were included. Confirm permission set assignments are in place.

### Mode 2: Review and Audit an Existing Change Set

Use this when reviewing a change set someone else built, auditing a pending inbound change set, or assessing deployment risk before a release window.

1. Open the inbound change set and download or review the component list.
2. Check for high-risk types: flows (check active/inactive status post-deploy), profiles (will overwrite production profile metadata — check if permission sets are the better vehicle), sharing rules, permission sets, and connected app settings.
3. Confirm all expected components are present. Confirm no unexpected components were pulled in by "Add Dependencies."
4. Check whether this change set was already validated and whether the 10-day quick deploy window is still open.
5. Identify post-deploy manual tasks: activating flows, assigning permission sets, updating named credentials if environment-specific values differ.

### Mode 3: Troubleshoot Change Set Errors

Use this when a validation or deployment fails or a change set cannot be uploaded.

1. **"No authorized orgs" / Upload button disabled**: the org connection is missing or expired. In the source org, go to Setup > Deployment Settings and confirm the target org appears as an authorized org. Re-establish if needed.
2. **Missing dependency error**: the error message names the component. Go back to the outbound change set in the source org, add the named component, and re-upload. Do not attempt to work around this by changing the target org directly.
3. **Apex test failure on validation**: read the exact test method and assertion that failed. If the test was passing before, check whether data setup, org configuration, or a prior change broke the test in the target. Fix the Apex or the test setup in the source, re-deploy to sandbox, and re-upload.
4. **Code coverage below 75%**: this is an aggregate across the entire org, not just the classes in the change set. Check which classes in the production org lack coverage. Add test classes for them to the change set or run a full test suite in a staging sandbox first to confirm coverage.
5. **"Component already exists with a different internal ID"**: this happens when the same component was created independently in source and target. Use the Metadata API or SF CLI to reconcile by replacing the target component with the source-org version via a direct metadata deploy, then resume change set promotion.
6. **Change set stuck in "Pending" or "In Progress"**: check the Deployment Status page (Setup > Deploy > Deployment Status). If stuck for more than an hour, the deployment may have hit a governor limit or timed out. Contact Salesforce Support if the status does not resolve; do not attempt to cancel and re-run without confirming the prior deploy rolled back fully.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Small metadata-only release, connected-org sandbox to production | Change set with validate-then-quick-deploy | Low complexity, minimal window risk |
| Apex-containing change set to production | Validate with specified tests first; quick deploy if clean | Reduces production window from full test run to quick deploy |
| Large change set with 50+ components | Break into sequenced smaller change sets | Reduces dependency surface and makes rollback easier to reason about |
| Same components needed in multiple sandboxes | Re-upload a copy to each target (change sets are not reusable across unrelated org connections) | Change sets are point-to-point; no broadcast mechanism |
| Frequent releases by a team | Migrate to DevOps Center or Salesforce CLI / CI pipeline | Change sets scale poorly for team-based delivery; no branching, no diff, no automation |
| Emergency hotfix to production | Change set from a full-copy sandbox, validate first even if fast | Skipping validation to save time is the most common source of production rollbacks |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before any production deployment:

- [ ] All component dependencies are included or already present in target org
- [ ] Change set validated successfully in target org (full or specified test run)
- [ ] Apex code coverage is above 75% in aggregate in the target
- [ ] No unexpected components were included (especially profiles and page layouts)
- [ ] Flows included in the change set: confirm active/inactive state is correct post-deploy
- [ ] Post-deploy manual steps are documented and assigned (flow activation, permission set assignment, named credential updates)
- [ ] Quick Deploy window (10-day) is still open if you intend to use it
- [ ] Rollback plan is defined (previous metadata version or known hotfix path)

---

## Salesforce-Specific Gotchas

Non-obvious behaviors that cause real production problems:

1. **Profiles overwrite, not merge** — Deploying a profile in a change set replaces the entire profile metadata in the target org, not just the settings you changed. Any production-only profile customizations (custom tab visibility, app assignments, custom permissions) will be lost if the source-org profile does not have them. Use permission sets wherever possible; if profiles must be deployed, audit the full profile XML before upload.

2. **"Add Dependencies" is not comprehensive** — The dependency finder in the outbound change set UI detects direct relationships but misses indirect ones (e.g., a Flow that calls an Apex class via an invocable method, or a validation rule that references a custom formula field). Always manually walk through the logic of what you are deploying and cross-check the component list.

3. **Quick Deploy resets on a new upload** — If you validate successfully and earn a 10-day quick deploy window, then decide to add one more component and re-upload, the 10-day clock resets. You must validate again before quick deploy is available. Do not modify a change set after validation without planning for another validation cycle.

4. **Flow deployment does not equal Flow activation** — A Flow deployed via a change set keeps the activation state it was exported with. If it was inactive in the source org sandbox, it arrives inactive in production. Post-deploy activation is a manual step that must be in the release plan.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Deployment plan | Step-by-step guide: which change set, which org, which test level, who validates, who deploys, what smoke tests confirm success |
| Pre-deployment checklist | Per-release review against the standard checklist above |
| Dependency resolution path | List of missing components to add and the correct upload sequence |
| Troubleshooting report | Identified error, root cause, and remediation steps |

---

## Related Skills

- **admin/change-management-and-deployment** — Use when the question is about release governance, method selection, rollback planning, or cross-team release process rather than the specific change set UI workflow.
- **devops/sf-cli-and-sfdx-essentials** — Use when the practitioner needs to move metadata using the Salesforce CLI (`sf project deploy`) rather than the Setup UI change set mechanism.
- **admin/sandbox-strategy** — Use when the question is about the environment topology that feeds into the change set promotion path.
