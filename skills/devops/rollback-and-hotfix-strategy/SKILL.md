---
name: rollback-and-hotfix-strategy
description: "Planning and executing metadata rollbacks and emergency hotfixes in Salesforce orgs. Use when a production deployment causes regression and needs to be reverted, or when an urgent fix must bypass the normal release pipeline. Covers pre-deploy archive bundles, quick deploy for hotfixes, non-rollbackable component handling, and hotfix branch isolation. NOT for routine CI/CD pipeline setup (use continuous-integration-testing). NOT for destructive changes authoring (use destructive-changes-deployment)."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "how do I roll back a failed Salesforce production deployment"
  - "emergency hotfix needs to go to production immediately"
  - "deployment broke production and I need to revert metadata"
  - "what components cannot be rolled back in Salesforce"
  - "quick deploy to push an urgent fix to production"
tags:
  - rollback
  - hotfix
  - deployment
  - metadata-api
  - quick-deploy
  - production-recovery
inputs:
  - Deployment history or package manifest of the failed deployment
  - Pre-deploy archive or source control reference of the previous known-good state
  - List of components changed in the failed deployment
  - Target org credentials or authenticated alias
outputs:
  - Rollback deployment package built from pre-deploy archive
  - Hotfix branch with minimal isolated change set
  - Quick deploy validation ID for fast-tracked production push
  - Post-rollback verification checklist confirming org stability
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Rollback And Hotfix Strategy

This skill activates when a production deployment has caused a regression and the practitioner needs to revert to the previous known-good state, or when an emergency fix must reach production outside the normal release cycle. Salesforce has no native one-click metadata rollback. Rollback means re-deploying the previous version of every changed component, and hotfix means isolating a minimal change and pushing it through a fast-tracked path.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether a pre-deploy archive (retrieve snapshot of production metadata taken before the failed deployment) exists. Without it, you must reconstruct the previous state from source control history.
- Identify every component that was changed or added in the failed deployment. The Metadata API deploy response and the original `package.xml` are the primary sources for this list.
- Determine which changed components are non-rollbackable: Record Types (once created, cannot be deleted via API), Picklist values (cannot be removed via Metadata API), and active Flow versions (cannot be deactivated or deleted via deployment). These require manual admin intervention in Setup.

---

## Core Concepts

### Pre-Deploy Archive Pattern

Because Salesforce provides no native rollback mechanism, teams must build their own safety net. The pre-deploy archive pattern works as follows: immediately before every production deployment, run `sf project retrieve start` with the same `package.xml` that will be deployed. This retrieves the current production state of every component that is about to change and stores it as a timestamped bundle (zip or folder). If the deployment causes a regression, this archive becomes the rollback package — you deploy it back to production to restore the previous state.

The archive must be stored outside the deployment pipeline artifacts directory to prevent accidental overwrite. Common storage targets include a dedicated Git branch, a CI artifact store, or a shared filesystem with retention policies.

### Quick Deploy for Hotfixes

The Metadata API supports a quick deploy workflow that skips Apex test execution for a deployment that has already passed validation. The flow is: first, run `sf project deploy validate` against production with `--test-level RunLocalTests`. This executes all tests and returns a validation ID. Within 10 days (the validation window), you can promote the validated package using `sf project deploy quick --job-id <validationId>` — this deploys immediately without re-running tests.

For hotfixes, this means you can validate the fix during business hours and then promote it during a low-traffic window in seconds rather than waiting for a full test run. The 10-day window is a hard platform limit; expired validations must be re-run.

### Non-Rollbackable Components

Several Salesforce metadata types cannot be fully rolled back through the Metadata API:

- **Record Types** — Once created and assigned to page layout assignments or used in data, they cannot be deleted via deployment. Rollback requires manual deactivation in Setup.
- **Picklist values** — Values added to a picklist field cannot be removed via Metadata API. Use the Replace Picklist Values feature in Setup or manual editing.
- **Active Flow versions** — An active Flow version cannot be deleted or deactivated via deployment. You must deactivate it manually in Setup before the previous version can be activated.
- **Custom metadata records** — While the type definition can be deployed, individual records (CustomMetadata) behave like data and may not revert cleanly.

A rollback plan must identify these components upfront and include manual remediation steps.

### Hotfix Branch Isolation

A hotfix branch should contain the absolute minimum change required to resolve the production issue. It branches from the production-matching tag or commit (not from a development branch that may contain unreleased work). The hotfix is merged back into both the production branch and the main development branch after deployment to prevent the fix from being overwritten by the next release.

---

## Common Patterns

### Pattern 1 — Full Rollback Using Pre-Deploy Archive

**When to use:** A production deployment caused widespread regression and the entire deployment needs to be reverted.

**How it works:**
1. Locate the pre-deploy archive bundle that was captured before the failed deployment.
2. Build a `package.xml` from the archive contents (or reuse the original deployment manifest).
3. Deploy the archive to production: `sf project deploy start --manifest package.xml --source-dir <archive-path> --target-org production`.
4. For any components that were newly added (not updates), create a `destructiveChangesPost.xml` to remove them.
5. Handle non-rollbackable components manually in Setup.

**Why not the alternative:** Rolling forward (fixing the bug instead of reverting) is sometimes faster, but when the regression is broad or the root cause is unclear, a full rollback restores stability immediately while the team investigates.

### Pattern 2 — Quick Deploy Hotfix

**When to use:** A targeted fix is ready and must reach production with minimal downtime. The change is small and well-understood.

**How it works:**
1. Create a hotfix branch from the production tag.
2. Make the minimal change (single Apex class fix, LWC patch, configuration update).
3. Validate against production: `sf project deploy validate --manifest package.xml --test-level RunLocalTests --target-org production`.
4. Capture the validation job ID from the output.
5. Promote during the deployment window: `sf project deploy quick --job-id <validationId> --target-org production`.
6. Merge the hotfix branch back into main/develop.

**Why not the alternative:** A normal deployment re-runs all local tests, which can take 30-90 minutes in large orgs. Quick deploy skips this because tests already passed during validation, reducing the deployment window to seconds.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Broad regression, root cause unclear | Full rollback from pre-deploy archive | Restores stability immediately; investigate later |
| Single component is broken, fix is obvious | Quick deploy hotfix | Minimal change, fast promotion, low risk |
| Regression involves Record Types or Picklist values | Partial rollback + manual Setup intervention | These components cannot be reverted via API |
| No pre-deploy archive exists | Reconstruct from source control history | Git diff between current and previous release tag identifies changed files |
| Hotfix validation expired (>10 days) | Re-run validation before quick deploy | Platform enforces 10-day window; no override |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Assess severity** — Determine whether the production issue requires a full rollback (broad regression, unknown root cause) or a targeted hotfix (isolated defect, known fix). Check whether affected components include non-rollbackable types.
2. **Locate the previous known-good state** — Find the pre-deploy archive bundle, or identify the last known-good Git commit/tag corresponding to production. If neither exists, retrieve the current production state and diff against source control.
3. **Build the rollback or hotfix package** — For rollback: use the pre-deploy archive as the deployment source. For hotfix: create a branch from the production tag and make the minimal change. Include destructive changes manifests if new components were added in the failed deployment.
4. **Validate before deploying** — Run `sf project deploy validate` with `--test-level RunLocalTests` against production. Capture the validation job ID. Review test results for any new failures introduced by the rollback/hotfix itself.
5. **Deploy to production** — Use `sf project deploy quick --job-id <id>` for validated packages, or `sf project deploy start` for immediate deployment. Execute during a low-traffic window when possible.
6. **Handle non-rollbackable components** — Manually deactivate Record Types, remove Picklist values, and deactivate Flow versions in Setup as needed. Document each manual step.
7. **Verify and merge** — Confirm the regression is resolved in production. Merge the hotfix branch back into main/develop. Update release notes with the rollback/hotfix record.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Pre-deploy archive exists or previous state has been reconstructed from source control
- [ ] All changed components from the failed deployment are accounted for in the rollback package
- [ ] Non-rollbackable components (Record Types, Picklist values, active Flows) have manual remediation steps documented
- [ ] Destructive changes manifest included for any newly-added components that must be removed
- [ ] Validation passed against production with RunLocalTests
- [ ] Quick deploy job ID captured and promotion executed within the 10-day window
- [ ] Hotfix branch merged back into main/develop to prevent regression in next release

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **No native rollback** — Salesforce does not offer a one-click undo for metadata deployments. Every rollback is a forward deployment of the previous version. Teams that skip the pre-deploy archive step have no fast recovery path.
2. **Quick deploy validation window is 10 days** — A validated deployment that is not promoted within 10 days expires silently. The `sf project deploy quick` command will fail with a non-obvious error. Re-validation is required.
3. **Newly added components require destructive changes** — If the failed deployment added new components (not just updated existing ones), simply re-deploying the old versions of changed components will not remove the new additions. A companion `destructiveChangesPost.xml` is required.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Pre-deploy archive bundle | Retrieved snapshot of production metadata before deployment; serves as rollback source |
| Rollback `package.xml` | Manifest listing every component to be reverted to its previous version |
| `destructiveChangesPost.xml` | Manifest for removing newly-added components that did not exist before the failed deployment |
| Hotfix branch | Minimal Git branch from the production tag containing only the emergency fix |
| Validation job ID | Identifier from `sf project deploy validate` used for quick deploy promotion |

---

## Related Skills

- `destructive-changes-deployment` — use for authoring destructive changes manifests when rolling back includes removing newly-added components
- `continuous-integration-testing` — use for setting up the CI pipeline that validates deployments before production
- `release-management` — use for the broader release process including release trains, tagging, and promotion gates
