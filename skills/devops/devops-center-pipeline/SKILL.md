---
name: devops-center-pipeline
description: "Use when setting up, managing, or troubleshooting a Salesforce DevOps Center pipeline — including pipeline stages, work items, bundles, promotions, conflict resolution, and source control connectivity. Covers both the original managed package and next-generation DevOps Center. Trigger keywords: DevOps Center, next-generation DevOps Center, work item, pipeline stage, promote changes, bundle, DevOps Center Hub org, release management. NOT for CLI-based deployment workflows, SFDX commands, unlocked packages, or change sets — those have separate skills."
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
  - "enable next-generation DevOps Center in a brand new org"
  - "connect DevOps Center to Bitbucket instead of GitHub"
tags:
  - devops-center
  - next-generation-devops-center
  - pipeline
  - work-items
  - bundles
  - promotion
  - github
  - bitbucket
  - release-management
inputs:
  - "Which DevOps Center the org runs (original managed package, or next-generation)"
  - "Target org type (scratch org, Developer sandbox, Partial Copy sandbox, Full sandbox, production)"
  - "Number of pipeline stages required (dev, QA, UAT, staging, production)"
  - "Source control provider (GitHub, or Bitbucket on next-generation) plus organization and repository details"
  - "Connected App or source control OAuth credentials for DevOps Center auth"
  - "Team size and branching strategy preferences"
outputs:
  - "Determination of which DevOps Center the org runs, and the setup path that follows from it"
  - "Pipeline stage design with org-to-stage mapping"
  - "Work item and bundle promotion workflow guidance"
  - "Conflict resolution procedure for competing work items"
  - "Source control repository and branch strategy recommendations"
  - "Review checklist before first production promotion"
dependencies: []
version: 1.2.0
author: Pranav Nagrecha
updated: 2026-07-08
---

# DevOps Center Pipeline

This skill activates when a practitioner needs to set up, operate, or troubleshoot a Salesforce DevOps Center pipeline — the point-and-click release management tool built natively in Salesforce. It covers pipeline design, work item lifecycle, bundle promotion, GitHub integration, and conflict resolution. It does NOT cover SFDX CLI deployments, unlocked packages, or change sets.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Establish which DevOps Center the org runs, before quoting any setup step** — there are two products with the same name. The original DevOps Center is a managed package installed via AppExchange and enabled in Setup. Next-generation DevOps Center, offered starting April 2026, is a native platform capability: it "doesn't require any package downloads and installs," and once you turn it on in the DevOps Center Hub org you can start using it immediately. Setup instructions, permission sets, and source control options all diverge between the two. Check Setup > Installed Packages first.
- **DevOps Center is enabled in the org** — on the managed-package path, confirm the package is installed and the user holds the permission sets the task requires. Salesforce ships five: **DevOps Center** (the base set, for every user), **DevOps Center Manager** (set up projects, environments, and users), **DevOps Center Release Manager** (perform promotions through the pipeline), `sf_devops_InitializeEnvironments` (manage connections to work environments), and `sf_devops_NamedCredentials` (authenticate to environments). There is no "DevOps Center Admin" or "DevOps Center User" permission set — those names do not exist. On the next-generation path, confirm DevOps Center is enabled in the Hub org, the user exists as a user *in that Hub org*, and a DevOps Center permission set is assigned. **New downloads and installations of the managed package are no longer supported as of April 2026** — orgs that installed it earlier keep working and reach it from the App Launcher, but a greenfield setup today is next-generation.
- **A source control repository exists and is accessible** — DevOps Center keeps source control as the single source of truth. The managed package supports GitHub only (github.com or GitHub Enterprise Server) and connects via a GitHub OAuth app or a Connected App with Named Credentials. Next-generation DevOps Center requires a source control provider account on **GitHub or Bitbucket**. Salesforce's documentation names no other provider — GitLab and Azure Repos are not documented as supported, so do not plan a pipeline around them.
- **Source tracking is available for every pipeline org** — DevOps Center requires source tracking. This limits eligible org types to Developer sandboxes, scratch orgs, and (since Summer '22) Partial Copy and Full sandboxes with source tracking enabled. Regular sandboxes without source tracking are not supported. Next-generation DevOps Center loosens this at the *development* end: DX Inspector can manually add and commit changes from non-source-tracked development environments, which matters for complex data configuration where source tracking isn't enabled.
- **The common wrong assumption** — practitioners often assume DevOps Center is a wrapper around `sf deploy`. It is not. DevOps Center uses the Metadata API under the hood and manages its own branch-per-work-item model in the source control repository. You cannot mix SFDX CLI deployments into the same pipeline and expect them to stay in sync.
- **Pipeline stage count is not capped** — Salesforce states plainly that "Your pipeline can contain any number of pipeline stages." Each stage maps to exactly one Salesforce org and one branch in the repository. The docs recommend at least one test stage between development and production; a robust pipeline typically has two or three. Do not quote a numeric stage ceiling — no Salesforce Help page states one.

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

On next-generation DevOps Center this path gains a first step, not a replacement. Salesforce ships DevOps Center MCP tools that run against the Salesforce DX Model Context Protocol (MCP) Server to give "AI-based recommendations for work item management, conflict resolution, and deployment failure resolution." Read the recommendation, verify it against the metadata, then land the merge in the provider repository — the recommendation does not merge for you, and an unverified AI-proposed resolution to a conflicting Flow or profile is exactly the change that reaches production unnoticed.

---

## Next-Generation DevOps Center

Starting April 2026, Salesforce offers next-generation DevOps Center in addition to the managed package. It keeps the click-based model this skill describes — projects, pipelines, work items, bundles, promotions — and changes how you obtain it, where source can live, how changes are tested, and how conflicts and failures get triaged.

Salesforce Help states the availability as: "Available in: Lightning Experience in **Professional** (API access required), **Enterprise**, **Performance**, **Unlimited**, and **Developer** Editions." It is **not available in Government Cloud Plus** and **not available in the EU Operating Zone**. Carry the Professional API-access qualifier and both exclusions whenever you quote the edition list — a Professional-edition org without API access cannot run it.

### What Differs From the Managed Package

| Concern | Managed package (original) | Next-generation |
|---|---|---|
| How you get it | Install from AppExchange; **new downloads and installations are no longer supported as of April 2026** | Turn it on in the DevOps Center Hub org — no package download or install |
| Source control provider | GitHub only | GitHub or Bitbucket (no other provider is documented as supported) |
| Setup entry point | Setup wizard in the org | Enable DevOps Center, then add team members as users in the Hub org before any project exists |
| Automated testing and quality gates | Not provided — tests run as part of the Metadata API deploy, with no configurable gate | **DevOps Center Testing**: test suites run automatically on review creation (Left-Shift Testing) and before every promotion (Testing Before Promotion), plus On-Demand Testing. Quality gate rules enforce pass thresholds, severity limits, and essential test requirements |
| Data alongside metadata | Metadata only | **Data Commit and Deployment** via DX Inspector — track, commit, and review metadata *and data* changes |
| Non-source-tracked dev environments | Not usable | DX Inspector can manually add and commit changes from them |
| Conflict and failure triage | Resolve in the provider pull request | AI-based recommendations via the Salesforce DX MCP Server and DevOps Center MCP tools, then resolve in the provider |
| UI | Original DevOps Center UI | Rebuilt as an extensible UI on Salesforce Lightning Design System 2 (SLDS 2) |

These two rows are the most decision-relevant deltas. A team that rejected the managed package because it could not gate a promotion on test results should re-evaluate — next-generation ships exactly that gate.

### The Hub Org

Next-generation setup introduces the **DevOps Center Hub org** as a first-class concept. Adding team members as users in the Hub org, and assigning them DevOps Center permission sets, is a discrete step that happens *before* creating a project or building a pipeline. Practitioners coming from the managed package expect permissions to be an afterthought inside the org they already work in; here the Hub org is the place the team collaborates, and a user who is not in it cannot be assigned a Work Item.

### Setup Order

Salesforce documents next-generation setup as an ordered sequence. Follow it in order — steps 3 and 4 are the ones teams skip:

1. Enable DevOps Center.
2. Switch from the DevOps Center managed package to next-generation DevOps Center (only when migrating an existing install).
3. Add team members as users in the DevOps Center Hub org.
4. Assign DevOps Center permission sets.
5. Source control setup — connect the GitHub or Bitbucket account that becomes the single source of truth.
6. Exclude metadata with the `.forceignore` file.
7. Create a DevOps Center project.
8. Build the pipeline.
9. Create and assign work items.
10. Integrate the Agentforce Vibes IDE with DevOps Center (optional; requires an MCP-enabled IDE or MCP client).

### DX Inspector

DX Inspector surfaces change tracking directly inside a sandbox, scratch org, or Developer Edition org and connects that environment to a next-generation DevOps Center project. Two consequences matter for pipeline design:

- Work items and tracked changes are managed without leaving the development org.
- Changes from **non-source-tracked** development environments can be added and committed manually. This relaxes the hard constraint that every development environment must have source tracking — but it does not relax the constraint on pipeline *stage* orgs, and manual commits carry no source-tracking safety net. Use it for the environments where source tracking genuinely isn't available, not as a general workflow.

`.forceignore` is what keeps DX Inspector and DevOps Center from pushing or pulling files that have no business in the repository — IDE configuration, local test data, environment-specific profiles. Configure it before the first commit, not after the first noisy diff.

### DevOps Center Testing and Quality Gates

Next-generation DevOps Center ships automated test execution and configurable quality gates. This is the single biggest correction to the folk wisdom that "DevOps Center can't gate a promotion."

Salesforce documents two automatic phases plus a manual one:

- **Left-Shift Testing** — "Triggered when a developer creates a review in DX Inspector, catching issues early in the pipeline."
- **Testing Before Promotion** — "Triggered before a work item advances to the next stage, so that only validated changes reach Integration, Staging, and Production."
- **On-Demand Testing** — "lets you manually verify whether tests are passing before attempting promotion again."

A **quality gate rule** is a checkpoint that makes sure only work items meeting your quality criteria move to the next pipeline stage. A rule evaluates three kinds of condition, and failing any one of them fails the gate and blocks the promotion:

| Criterion | Fails when |
|---|---|
| Severity level threshold | Any test with a severity equal to or higher than the threshold fails |
| Test pass percentage | The overall test pass rate is below the set percentage |
| Essential test failures | Any test marked as essential fails |

Configure test providers, assign test suites, and set up gates from the Tests tab in the pipeline view. Note that testing setup is *not* one of the ten ordered setup steps above — it is configured after the pipeline exists.

---

## Common Patterns

### Mode 1: Simple Linear Pipeline (Admin Team)

**When to use:** A small admin team with a single Dev sandbox and a production org. Minimal parallel work. Moving from change sets to a source-tracked workflow.

**How it works:**
1. Get DevOps Center into the org. On the managed package (installed before April 2026), it is already there — assign the **DevOps Center** base permission set to the admin, plus **DevOps Center Manager** (to set up the project, environments, and users) and **DevOps Center Release Manager** (to run promotions). On a greenfield org, enable next-generation DevOps Center in the Hub org, add the admin as a user in that Hub org, then assign a DevOps Center permission set. There is nothing to install from AppExchange.
2. Connect source control. Managed package: GitHub OAuth via the Setup wizard, which creates a new repository or connects to an existing one. Next-generation: complete Source Control Setup against the GitHub or Bitbucket account.
3. Create a pipeline with two stages: Development (mapped to the Developer sandbox) and Production (mapped to production).
4. Create a Work Item for each change. Start the Work Item — DevOps Center creates the feature branch.
5. Make metadata changes in the Development org. DevOps Center tracks them via source tracking.
6. Mark the Work Item as Ready to Promote.
7. Promote the Work Item directly to Production (no bundle needed for single items).
8. DevOps Center opens a pull request in the connected repository, runs the deployment, and merges the PR when successful.

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

### Mode 4: Moving an Existing Managed-Package Pipeline to Next-Generation

**When to use:** The org installed the DevOps Center managed package before April 2026, the pipeline is in daily use, and the team wants the next-generation feature set (Bitbucket support, automated testing and quality gates, data commit and deployment, MCP-assisted triage, DX Inspector, SLDS 2 UI).

**How it works:**
1. Confirm the pipeline is quiet. Do not attempt this mid-release with Work Items sitting between stages.
2. Enable DevOps Center in the Hub org.
3. Run the documented "Switch from DevOps Center Managed Package to Next Generation DevOps Center" step. This is a supported, documented transition — do not hand-migrate branches, re-point stage orgs, or rewrite repository history to simulate it.
4. Add team members as users in the Hub org and assign DevOps Center permission sets. Managed-package permission set assignments do not carry over as Hub org membership.
5. Re-verify source control connectivity and `.forceignore` before the first promotion on the new experience.

**Why not just keep the package:** Existing installations continue to work, so there is no forced deadline. But the package is a closed road — no new installs means new orgs in the same estate cannot join a managed-package pattern, and every future capability lands on the next-generation side. Migrate on a planned quiet window, not under release pressure.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Standing up DevOps Center in an org today | Enable next-generation DevOps Center; do not plan an AppExchange install | New downloads and installations of the managed package are no longer supported as of April 2026 |
| Org already runs the managed package and the pipeline is healthy | Keep operating it; schedule the switch for a quiet window | Existing installations continue to work and remain reachable from the App Launcher; there is no forced cutover |
| Team's source control is Bitbucket | Next-generation DevOps Center | The managed package is GitHub-only; next-generation accepts a GitHub or Bitbucket provider account |
| Team's source control is GitLab or Azure DevOps | Neither — use SFDX CLI + CI/CD | Salesforce documents GitHub and Bitbucket only; no other provider is documented as supported |
| Team needs a promotion blocked on test results | Next-generation DevOps Center with a quality gate rule | Quality gate rules enforce pass thresholds, severity limits, and essential test requirements before a work item advances |
| A development environment has no source tracking | Next-generation DevOps Center with DX Inspector | DX Inspector can manually add and commit changes from non-source-tracked development environments |
| Merge conflict or deployment failure on next-generation | Read the DevOps Center MCP recommendation first, verify it, then resolve in the provider | MCP tools cover work item management, conflict resolution, and deployment failure resolution — they advise, they do not merge |
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

- [ ] Which DevOps Center the org runs is established (managed package vs. next-generation), and every setup instruction given matches that product
- [ ] DevOps Center is available: the managed package is installed with the correct permission sets assigned (DevOps Center for every user; DevOps Center Manager for whoever configures projects, environments, and users; DevOps Center Release Manager for whoever promotes), or next-generation is enabled and the team exists as users in the DevOps Center Hub org with permission sets assigned
- [ ] No guidance in the deliverable tells the team to install the DevOps Center managed package from AppExchange
- [ ] Source control repository (GitHub, or Bitbucket on next-generation) is connected and DevOps Center can read/write branches and pull requests
- [ ] On next-generation: `.forceignore` excludes IDE configuration, local test data, and environment-specific profiles before the first commit
- [ ] Each pipeline stage maps to an org with source tracking enabled (Developer sandbox, scratch org, Partial Copy, or Full sandbox)
- [ ] Pipeline stage branch names in the connected repository have not been manually renamed or deleted
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

4. **Every "install it from AppExchange" instruction written before April 2026 is now a dead end** — Salesforce closed new downloads and installations of the DevOps Center managed package. Blogs, Trailhead notes, internal runbooks, and this skill's own pre-1.1 guidance all opened with an install step that a greenfield org can no longer perform. When an org has no DevOps Center in Setup > Installed Packages, that is not a broken install to fix — it is the signal to enable next-generation DevOps Center instead.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| DevOps Center mode determination | Which product the org runs (managed package vs. next-generation) and the setup path that follows |
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
