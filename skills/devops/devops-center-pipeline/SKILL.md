---
name: devops-center-pipeline
description: "Use when setting up, managing, or troubleshooting a Salesforce DevOps Center pipeline — including pipeline stages, work items, bundles, promotions, conflict resolution, and GitHub connectivity. Trigger keywords: DevOps Center, work item, pipeline stage, promote changes, bundle, release management. NOT for CLI-based deployment workflows, SFDX commands, unlocked packages, or change sets — those have separate skills."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Security
  - Reliability
triggers:
  - "how do I set up a DevOps Center pipeline with multiple sandbox stages"
  - "work item is stuck and won't promote to the next stage in DevOps Center"
  - "how do I resolve a merge conflict when promoting a bundle in DevOps Center"
  - "DevOps Center promotion failed and I cannot find the error message"
  - "should I bundle my work items before promoting to QA"
  - "two work items are modifying the same metadata component and conflicting"
  - "DevOps Center versus SFDX CLI deployment which should I use for my admin team"
tags:
  - devops-center
  - pipeline
  - work-items
  - bundles
  - promotion
  - github
  - release-management
inputs:
  - "Target org type (scratch org, Developer sandbox, Partial Copy sandbox, Full sandbox, production)"
  - "Number of pipeline stages required (dev, QA, UAT, staging, production)"
  - "GitHub organization and repository details"
  - "Connected App or GitHub OAuth credentials for DevOps Center auth"
  - "Team size and branching strategy preferences"
outputs:
  - "Pipeline stage design with org-to-stage mapping"
  - "Work item and bundle promotion workflow guidance"
  - "Conflict resolution procedure for competing work items"
  - "GitHub repository and branch strategy recommendations"
  - "Review checklist before first production promotion"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# DevOps Center Pipeline

This skill activates when a practitioner needs to set up, operate, or troubleshoot a Salesforce DevOps Center pipeline — the point-and-click release management tool built natively in Salesforce. It covers pipeline design, work item lifecycle, bundle promotion, GitHub integration, and conflict resolution. It does NOT cover SFDX CLI deployments, unlocked packages, or change sets.

---

## Before Starting

Gather this context before working on anything in this domain:

- **DevOps Center is enabled in the org** — it is a managed package installed via AppExchange and must be enabled in Setup before any pipeline work. Confirm the package is installed and the user has the DevOps Center Admin or DevOps Center User permission set.
- **GitHub repository exists and is accessible** — DevOps Center uses GitHub as its source control back-end. A repository (public or private) must exist before pipeline stages can be created. The org connects via a GitHub OAuth app or a Connected App with Named Credentials.
- **Source tracking is available for every pipeline org** — DevOps Center requires source tracking. This limits eligible org types to Developer sandboxes, scratch orgs, and (since Summer '22) Partial Copy and Full sandboxes with source tracking enabled. Regular sandboxes without source tracking are not supported.
- **The common wrong assumption** — practitioners often assume DevOps Center is a wrapper around `sf deploy`. It is not. DevOps Center uses the Metadata API under the hood and manages its own branch-per-work-item model in GitHub. You cannot mix SFDX CLI deployments into the same pipeline and expect them to stay in sync.
- **Pipeline stage limits** — a single pipeline supports up to 15 stages. Each stage maps to exactly one Salesforce org and one branch in the repository.

---

## Core Concepts

### Work Items

A Work Item is DevOps Center's unit of work — analogous to a user story or task. When a Work Item is started, DevOps Center automatically creates a feature branch in the connected GitHub repository. All metadata changes tracked in that org are associated with the Work Item's branch. Work Items move through pipeline stages one at a time and carry their changes forward. Each Work Item has a status: In Progress, Ready to Promote, Promoted, or Merged.

Key constraints:
- One Work Item maps to one feature branch.
- A Work Item can only be in one stage at a time.
- Metadata changes made outside DevOps Center (e.g., via Setup UI changes tracked by source tracking) are still captured and attributed to the active Work Item in that org.

### Pipeline Stages

A pipeline stage represents one environment in the release path. Each stage is associated with:
- A Salesforce org (scratch org, Developer sandbox, Partial Copy, Full sandbox, or production)
- A Git branch in the connected repository

The typical stage sequence is: Development → QA → UAT → Staging → Production. Stages are ordered and promotions flow in one direction only — you promote forward, never backward. If a regression is found in UAT, you fix it in a new Work Item starting from Development.

DevOps Center creates and manages these branches automatically. The production stage's branch is typically `main`. Intermediate stage branches are created and managed by DevOps Center; practitioners should not rename or delete them manually.

### Bundles and Promotion

Before changes are promoted from one stage to the next, they must be packaged into a Bundle. A Bundle is a snapshot of one or more Work Items selected for joint promotion. Bundling serves two purposes:

1. It groups related Work Items that share metadata components, reducing the risk of conflicts between separate feature branches.
2. It creates an auditable promotion unit — a single deployment from one stage to the next that can be tracked, approved, and rolled back as a group.

**Individual vs. bundled promotion:** A single Work Item can be promoted individually, or multiple Work Items can be combined into one Bundle before promotion. Combining Work Items merges their feature branches before the promotion, which surfaces and resolves merge conflicts in GitHub before the deployment runs.

### Conflict Detection and Resolution

When two Work Items modify the same metadata component in different feature branches, DevOps Center detects the conflict when a promotion or bundle merge is attempted. Conflicts appear in the DevOps Center UI and must be resolved in GitHub — DevOps Center itself does not provide an in-app merge editor.

Resolution path:
1. DevOps Center flags the conflict during the bundle/promotion step.
2. The practitioner opens the pull request in GitHub and resolves the conflict there.
3. Once the PR is merged in GitHub, the promotion can proceed in DevOps Center.

---

## Common Patterns

### Mode 1: Simple Linear Pipeline (Admin Team)

**When to use:** A small admin team with a single Dev sandbox and a production org. Minimal parallel work. Moving from change sets to a source-tracked workflow.

**How it works:**
1. Install DevOps Center from AppExchange and assign the DevOps Center Admin permission set to the admin.
2. Connect to GitHub via the Setup wizard (OAuth). DevOps Center creates a new repository or connects to an existing one.
3. Create a pipeline with two stages: Development (mapped to the Developer sandbox) and Production (mapped to production).
4. Create a Work Item for each change. Start the Work Item — DevOps Center creates the feature branch.
5. Make metadata changes in the Development org. DevOps Center tracks them via source tracking.
6. Mark the Work Item as Ready to Promote.
7. Promote the Work Item directly to Production (no bundle needed for single items).
8. DevOps Center opens a pull request in GitHub, runs the deployment, and merges the PR when successful.

**Why not change sets:** Change sets have no version history, no rollback capability, and no conflict detection. DevOps Center provides all three while remaining fully point-and-click.

### Mode 2: Multi-Stage Pipeline with Bundled Promotions (Mid-Size Team)

**When to use:** A team running parallel sprints with multiple developers working in separate Work Items that share overlapping metadata components (e.g., shared page layouts, permission sets, or flows).

**How it works:**
1. Set up a pipeline with stages: Dev → QA → UAT → Production, each mapped to a different sandbox.
2. Each developer creates and works on their own Work Items.
3. At the end of the sprint, a release manager creates a Bundle in the QA stage containing all Work Items ready for QA.
4. DevOps Center merges all feature branches into the QA stage branch. Any conflicts appear as GitHub pull request conflicts to resolve before the promotion proceeds.
5. The Bundle is promoted through QA → UAT → Production as a unit.
6. Each promotion creates a GitHub pull request. DevOps Center merges it and deploys the metadata to the target stage org.

**Why bundling matters:** Without bundling, two Work Items modifying the same Apex class will conflict when promoted separately. Bundling forces conflict resolution before deployment, not during it.

### Mode 3: Combining Work Items to Manage Dependencies

**When to use:** Two Work Items have metadata dependencies — e.g., a new custom object (Work Item A) and a new flow that references it (Work Item B). Promoting B before A would cause a deployment error.

**How it works:**
1. In the DevOps Center pipeline view, select both Work Items.
2. Use the Combine Work Items action. DevOps Center merges Work Item B's branch into Work Item A's branch.
3. The combined Work Item now carries both sets of changes and can be promoted as one unit, eliminating the dependency ordering problem.
4. The original Work Item B is closed; its changes live in the combined item.

**Why not promote in order:** Manual ordering works once, but as parallel work increases, maintaining promotion order by hand becomes error-prone and blocks unrelated work items that happen to share a component.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single developer, two orgs, no parallel work | Individual Work Item promotion, no bundles | Bundles add overhead with no benefit when there is no parallelism |
| Multiple developers, shared metadata components | Bundle all Work Items before QA promotion | Forces conflict resolution before deployment; audit trail per release |
| Work Items have a metadata dependency | Combine Work Items before promoting | Ensures dependent components travel together; avoids deployment failures |
| Conflict detected during promotion | Resolve in GitHub PR, then retry promotion | DevOps Center delegates conflict resolution to GitHub; UI flags the state |
| Scratch orgs needed instead of sandboxes | Supported but requires Dev Hub and scratch org definitions; map each stage to a scratch org | Scratch orgs are short-lived; ensure the stage org is refreshed before promoting |
| Team also uses SFDX CLI deployments alongside DevOps Center | Separate the workflows completely — do not mix | CLI deployments to the same org will diverge the DevOps Center source tracking state |
| Need rollback after a bad production promotion | Create a new Work Item that reverts the change, promote through all stages | DevOps Center has no native rollback button; revert via a new forward promotion |

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

Run through these before marking work in this area complete:

- [ ] DevOps Center managed package is installed and the correct permission sets are assigned (DevOps Center Admin, DevOps Center User)
- [ ] GitHub repository is connected and DevOps Center can read/write branches and pull requests
- [ ] Each pipeline stage maps to an org with source tracking enabled (Developer sandbox, scratch org, Partial Copy, or Full sandbox)
- [ ] Pipeline stage branch names in GitHub have not been manually renamed or deleted
- [ ] All Work Items intended for the current release are either bundled together or combined where metadata dependencies exist
- [ ] All conflict-flagged pull requests in GitHub are resolved before attempting promotion
- [ ] Production promotion is gated by a manual approval step (if the team requires change management sign-off)
- [ ] No SFDX CLI deployments or Metadata API direct deploys are targeting the same orgs managed by DevOps Center

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Source-tracking drift from out-of-band changes** — If a developer makes changes directly in a DevOps Center-managed org using Setup UI actions that DevOps Center is not tracking (e.g., activating a flow, modifying a profile setting), source tracking will capture the change but it may be attributed to the wrong Work Item or become untracked. Always ensure changes are associated with an active Work Item before editing in the org.

2. **Stage branch deletion breaks the pipeline** — Pipeline stage branches in GitHub (e.g., `stage/qa`, `stage/uat`) are managed by DevOps Center. If a developer deletes or force-pushes to these branches outside DevOps Center, the pipeline enters an inconsistent state that requires manual recovery. Protect these branches in GitHub with branch protection rules.

3. **DevOps Center is NOT the SFDX Metadata API deploy path** — Practitioners accustomed to `sf project deploy start` expect a command-line deploy log. DevOps Center deploys via the Metadata API internally but surfaces only a simplified status in its UI. Detailed deployment errors appear in the Deployment Status page in Salesforce Setup, not in DevOps Center itself — this is a common source of confusion when debugging failed promotions.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Pipeline stage design | Mapping of pipeline stages to orgs, branch names, and promotion sequence |
| Work Item workflow guide | Step-by-step for creating, progressing, and promoting Work Items |
| Bundle strategy | Decision on individual vs. bundled promotion with rationale |
| Conflict resolution runbook | Steps for resolving GitHub PR conflicts flagged by DevOps Center |
| Pre-production promotion checklist | Verification steps before pushing a Bundle to production |

---

## Related Skills

- `devops/change-set-deployment` — Legacy change set workflow; use when migrating a team from change sets to DevOps Center or when DevOps Center is not available
- `devops/scratch-org-management` — Managing scratch org definitions and Dev Hub; needed when pipeline stages use scratch orgs instead of sandboxes
- `devops/cicd-pipeline-setup` — Full CI/CD automation with GitHub Actions or other CI tools; use when the team needs automated test runs, approval gates, or deployment automation beyond what DevOps Center provides natively
- `admin/sandbox-strategy` — Sandbox type selection, refresh scheduling, and data masking; use alongside this skill when planning the org topology for pipeline stages
- `admin/change-management-and-deployment` — Release planning, approval gates, and rollback planning at the process level
