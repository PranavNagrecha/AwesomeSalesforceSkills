---
name: devops-center-pipeline
description: "Use when setting up, managing, or troubleshooting a Salesforce DevOps Center pipeline — including pipeline stages, work items, bundles, promotions, conflict resolution, and GitHub connectivity. Trigger keywords: DevOps Center, work item, pipeline stage, promote changes, bundle. NOT for CLI-based deployment or SFDX commands — use devops/salesforce-cli-automation. NOT for change sets — use devops/change-set-deployment. NOT for unlocked packages — use devops/unlocked-package-development."
category: devops
salesforce-version: "Summer '26+"
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
  - "query why a DevOps Center promotion or back sync is stuck"
  - "migrate from the DevOps Center managed package to the next-generation DevOps Center"
  - "enable Lifecycle Center in Dev Hub settings"
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
version: 1.1.1
author: Pranav Nagrecha
updated: 2026-10-19
---

# DevOps Center Pipeline

This skill activates when a practitioner needs to set up, operate, or troubleshoot a Salesforce DevOps Center pipeline — the point-and-click release management tool built natively in Salesforce. It covers pipeline design, work item lifecycle, bundle promotion, source control connectivity, and conflict resolution. It does NOT cover SFDX CLI deployments, unlocked packages, or change sets.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Which DevOps Center the org runs.** There are two, and the newer one has been renamed. The Winter '27 guides call it **Lifecycle Center**: `DevHubSettings.enableALMDevopsCorePref` (API 65.0+) "Indicates whether the Lifecycle Center is enabled", giving "the AI-powered, Lifecycle Center for change and release management" (`api_meta.txt` 264 L117302–L117305). The Summer '26 guides called the same product the "next-generation DevOps Center" (262 L114168–L114171); the setting name did not change. The DevOps Center managed package is `enableDevOpsCenterGA` (API 56.0+), which the guide now describes as "an older version of Lifecycle Center" (264 L117307–L117311). Lifecycle Center stores its pipeline, stages, work items, and requests as standard objects (`DevopsPipeline`, `DevopsPipelineStage`, `WorkItem`, `DevopsRequestInfo`, API 66.0–67.0), whose Object Reference pages also say "Lifecycle Center" now. Migration from the package (`enableDevopsCenterMigrationPref`, API 67.0) is still a developer preview (264 L117334–L117341). Everything below about objects and field values is the Lifecycle Center data model; this skill still says "DevOps Center" for the tool in general.
- **Development environments have source tracking.** Developer and Developer Pro sandboxes with source tracking, and scratch orgs, are the supported development environments; Developer Edition orgs have no source tracking and can't be used as development environments in DevOps Center.
- **A source control repository exists.** The Lifecycle Center provider record (`SourceCodeRepoProvider`) supports `GITHUB` (default) and `BITBUCKET`, and names the Named Credential DevOps Center uses to connect.
- **Who administers the pipeline and who only works items.** Decide the two groups before setup and assign DevOps Center access from what Setup lists for the edition in use; do not copy permission set names from older guides.
- **The common wrong assumption** — practitioners often assume DevOps Center is a wrapper around `sf project deploy start`. It records its own work items, branches, promotions, and deployments, so out-of-band deploys to the same orgs leave its records and branches out of step with the org.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Is the org on the DevOps Center managed package or Lifecycle Center (formerly "next-generation DevOps Center")? | The two are enabled by different Dev Hub settings and only Lifecycle Center exposes the `Devops*` / `WorkItem` objects this skill queries (gotcha 8). | The right troubleshooting path and data model from the first step. |
| Which org is each developer's development environment, and does it have source tracking? | Only source-tracked Developer/Developer Pro sandboxes and scratch orgs qualify; enabling the setting affects sandboxes created or refreshed afterwards (gotcha 3). | A development-environment list that will actually capture changes. |
| Which source control provider and account own the repository? | The provider is GitHub or Bitbucket and the connection runs through a Named Credential; a personal account breaks the pipeline when that person leaves (gotcha 5). | A service-owned provider connection and a named repository. |
| Which stage should start bundling work items together? | Bundling is a per-stage flag (`IsBundled`); deciding late reshuffles promotions already in flight (gotcha 4). | One agreed bundling stage and a release cadence for it. |
| Which test level must each stage's deployment run? | The default test level runs no tests in sandboxes and all local tests in production, so QA promotions can pass untested (gotcha 7). | An explicit `TestLevel` per stage and the test list for `RunSpecifiedTests`. |
| Does anyone deploy to pipeline orgs outside DevOps Center (CLI, change sets, Setup edits in stage orgs)? | Out-of-band changes leave stage branches behind the org; DevOps Center's back sync and rebase operations exist to bring environments back in step (gotcha 2). | A rule that every change to a pipeline org enters as a work item, with back sync as the documented recovery. |
| Who reads failed operations, and where? | Promotion and commit failures are recorded on `DevopsRequestInfo` with `Status = ERROR` and `ErrorDetails`; nobody looking there means stalled promotions sit unnoticed (gotcha 1). | A named owner and the query in Recommended Workflow step 5. |

A proper pipeline setup adds a written stage map, a bundling decision, and a test level per stage before the first work item exists, where "just clicking through the wizard" produces a pipeline whose QA stage runs no tests and whose failures nobody can find.

---

## Core Concepts

### Work Items

A work item is a logical unit of work — a user story, task, or bug — that tracks metadata and configuration-data changes until the work is complete and part of the release pipeline. Each work item has its own branch in the repository (the object reference's example branch name is `feature/WI-000001`). In the Lifecycle Center data model, `WorkItem.Status` moves through `NEW`, `IN_PROGRESS`, `IN_REVIEW` (changes committed and a pull request created for review), `READY_TO_PROMOTE`, `PROMOTED`, and finally `CLOSED` when the work is promoted through the entire pipeline. Two exception states matter for troubleshooting: `MERGE_CONFLICT` (conflicts must be resolved before promotion) and `COMBINED` (merged into another work item to resolve conflicts or dependencies). `NEVERED` marks an inactive item that won't be promoted.

### Pipeline Stages

A `DevopsPipelineStage` connects a pipeline, an environment (`DevopsEnvironment`, currently always a Salesforce org), and the source control branch used for that stage. Stages are linked through `NextStageId`; the production stage has a null `NextStageId`. Promotions move work forward along that chain — a regression found in UAT is fixed by a new work item that starts in development, not by promoting backwards. The repository's default branch (typically `main` in GitHub) holds the changes you plan to release.

### Bundling and Promotion

A stage promotion (`DevopsPipelnStgProm`) moves one or more work items to the next stage, and `DevopsPipelnStgPromWkItem` records the merge of each work item into the target stage branch, including the pull request reference. Bundling is configured per stage: `DevopsPipelineStage.IsBundled` (default false) indicates that work items in that stage are bundled together for promotion. The design decision is therefore *which stage bundles*, not "create a bundle object".

### Conflicts, Combine, Rebase, and Back Sync

When two work items change the same component, the later one reaches `MERGE_CONFLICT`. The recovery operations DevOps Center records on `DevopsRequestInfo.OperationType` are `REBASE`, `REBASE_AND_COMBINE`, and `BACK_SYNC`; combining leaves the absorbed work item in `COMBINED`. A back sync brings changes from a pipeline stage (`BackSyncStageId`) back into a development environment so developers stop building on stale metadata. The merge itself is recorded per work item on `DevopsPipelnStgPromWkItem`, whose `MergeRemoteReference` holds the provider's pull request reference.

### Deployments and Test Levels

Each deployment to a stage environment is a `DevopsEnvDeployment` record with a `TestLevel` (`Default` — no tests in sandboxes, all local tests in production; `NoTestRun`; `RunLocalTests`; `RunAllTestsInOrg`; `RunSpecifiedTests` with the class list in `RunTests`) and an `IsFullDeploy` flag (deploy everything in the branch instead of just the changes). Validate-only deployment is not supported in the Lifecycle Center.

```soql
SELECT Name, OperationType, Status, Message, ErrorDetails, RequestCompletionDate
FROM DevopsRequestInfo
WHERE Status IN ('ERROR', 'INTERRUPTED')
ORDER BY CreatedDate DESC
LIMIT 20
```

---

## Common Patterns

### Mode 1: Simple Linear Pipeline (Admin Team)

**When to use:** A small admin team with one source-tracked Developer sandbox and production. Minimal parallel work. Moving from change sets to a source-tracked workflow.

**How it works:**
1. Turn on source tracking for sandboxes in production (`SourceTrackingSettings.enableSourceTrackingSandboxes`) and refresh or create the Developer sandbox afterwards.
2. Enable DevOps Center, connect the source control provider through its Named Credential, and create or connect the repository.
3. Create a pipeline with two stages: Development and Production (production's `NextStageId` is empty).
4. Create a work item per change; it gets its own branch.
5. Make the change in the development environment, commit it to the work item, and move it to `READY_TO_PROMOTE`.
6. Promote it; check the resulting `DevopsRequestInfo` record if the promotion does not reach `SUCCESS`.

**Why not change sets:** Change sets have no version history and no conflict detection; DevOps Center records every change against a work item and a branch while staying point-and-click.

### Mode 2: Multi-Stage Pipeline with a Bundling Stage (Mid-Size Team)

**When to use:** A team running parallel sprints whose work items share components (page layouts, permission sets, flows).

**How it works:**
1. Stages Dev → QA → UAT → Production, each a different environment.
2. Developers promote individual work items into QA as they finish.
3. Set `IsBundled` on the stage where the release is assembled (commonly UAT), so items there promote onward together.
4. Set an explicit test level for every stage deployment; do not rely on `Default` for QA and UAT.
5. After each promotion into a shared stage, back sync development environments that build on it.

**Why bundling matters:** Without a bundling stage, two items that touch the same flow promote separately and the second one hits `MERGE_CONFLICT` at whichever stage it reaches last.

### Mode 3: Combining Work Items to Manage Dependencies

**When to use:** Work item B depends on work item A (a flow that references A's new field), so promoting B alone fails.

**How it works:** Combine the items (recorded as `REBASE_AND_COMBINE`); the absorbed item moves to `COMBINED` and its changes travel with the surviving item. Confirm both are on the same release schedule first — the combined item promotes as one unit.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single developer, two orgs, no parallel work | Individual work item promotion, no bundling stage | Bundling adds overhead with no benefit when there is no parallelism |
| Multiple developers, shared metadata components | Set `IsBundled` on the release-assembly stage | Work items in that stage promote together; one deployment per release |
| Work items have a metadata dependency | Combine them before promoting | The dependent components travel in one item |
| Promotion stuck or failed | Query `DevopsRequestInfo` for `ERROR` / `INTERRUPTED`, read `ErrorDetails` | The request record is the documented place to troubleshoot stalled operations |
| Development environment is behind the stage it builds on | Back sync from that stage | `BackSyncStageId` names the stage changes flow back from |
| Team also uses SFDX CLI deployments alongside DevOps Center | Separate the orgs completely — do not mix (team practice) | CLI deploys leave stage branches and work item records describing a different org |
| Need rollback after a bad production promotion | Create a new work item that reverts the change and promote it through all stages (team practice) | Keeps the branch history and the org in step |

---

## Recommended Workflow

1. Identify the DevOps Center edition from `settings/DevHub.settings-meta.xml` (`enableDevOpsCenterGA` vs `enableALMDevopsCorePref`) and confirm source tracking for development sandboxes from `settings/SourceTracking.settings-meta.xml`.
2. Fill in `templates/devops-center-pipeline-template.md`: stage map (environment, branch, next stage), bundling stage, and test level per stage; answer every row of the Questions table above.
3. Export the stages with `sf data query -o <devops-center-org-alias> -q "SELECT Id, Name, DevopsPipelineId, NextStageId, IsBundled, DevOpsEnvironmentId FROM DevopsPipelineStage" --json > devops/stages.json` and run `python3 skills/devops/devops-center-pipeline/scripts/check_devops_center_pipeline.py --manifest-dir .` over the project; fix every ERROR (no production stage, a cycle in `NextStageId`).
4. Run a first work item end to end through every stage before onboarding the team; record the `DevopsEnvDeployment` test level that actually ran.
5. For any stuck promotion, run the `DevopsRequestInfo` query in Core Concepts and act on `ErrorDetails`; for `MERGE_CONFLICT`, rebase or combine, then back sync affected development environments.
6. Re-run the checker and the Review Checklist before the first production promotion.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] The DevOps Center edition (managed package or Lifecycle Center) is recorded, and only one is in active use for the project
- [ ] The source control provider (GitHub or Bitbucket) is connected through a service-owned Named Credential
- [ ] Every development environment is a source-tracked Developer/Developer Pro sandbox or a scratch org
- [ ] Exactly one stage has an empty `NextStageId` (production) and the `NextStageId` chain has no cycle
- [ ] The bundling stage is decided and `IsBundled` is set only where intended
- [ ] Every stage deployment has an explicit test level; QA/UAT do not rely on `Default`
- [ ] Stage branches are protected in the provider against deletion and force pushes (team practice)
- [ ] No SFDX CLI deployments or direct Metadata API deploys target orgs managed by the pipeline
- [ ] A named owner monitors `DevopsRequestInfo` records in `ERROR` or `INTERRUPTED`

---

## Salesforce-Specific Gotchas

Full list in `references/gotchas.md`. The three that cost the most time:

1. **Failures live on the request record** — `DevopsRequestInfo.ErrorDetails` holds the error for a failed promotion, commit, or back sync.
2. **`Default` test level skips tests in sandboxes** — a QA stage on `Default` promotes without running Apex tests.
3. **Validate-only deployments are not supported** in Lifecycle Center (`object_reference.txt` 264 L97151) — plan check-only runs outside it.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Pipeline stage design | Mapping of pipeline stages to environments, branches, next stage, bundling flag, and test level |
| Work item workflow guide | Status path from `NEW` to `CLOSED`, including `MERGE_CONFLICT` and `COMBINED` handling |
| Bundling decision | Which stage bundles and why |
| Troubleshooting query | `DevopsRequestInfo` query and the owner who runs it |
| Pre-production promotion checklist | Verification steps before promoting to production |

---

## Reference Files

| File | Use it for |
|---|---|
| `references/examples.md` | Change-set-to-DevOps Center migration, a bundling-stage sprint, and the CLI-mixing anti-pattern |
| `references/gotchas.md` | Eight platform behaviours with avoidance steps |
| `references/llm-anti-patterns.md` | Answers AI assistants get wrong about DevOps Center |
| `references/well-architected.md` | Pillar framing and the corpus lines behind each claim |
| `references/metadata-examples.md` | Dev Hub and source tracking settings XML, stage export JSON, and troubleshooting SOQL |

---

## Related Skills

- `devops/change-set-deployment` — Legacy change set workflow; use when migrating a team from change sets to DevOps Center or when DevOps Center is not available
- `devops/scratch-org-management` — Managing scratch org definitions and Dev Hub; needed when development environments are scratch orgs
- `devops/github-actions-for-salesforce` — Full CI/CD automation with GitHub Actions; use when the team needs automation beyond what DevOps Center provides natively
- `devops/bitbucket-pipelines-for-salesforce` — The same for teams whose repository lives in Bitbucket
- `admin/sandbox-strategy` — Sandbox type selection, refresh scheduling, and data masking; use alongside this skill when planning the org topology for pipeline stages
- `admin/change-management-and-deployment` — Release planning, approval gates, and rollback planning at the process level
