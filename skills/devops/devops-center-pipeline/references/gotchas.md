# Gotchas — DevOps Center Pipeline

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: The Error Is on the Request Record, Not in the Banner

**What happens:** A promotion fails or appears stalled. The DevOps Center UI shows a short status, and practitioners click around looking for the component-level error.

**When it occurs:** Any failed or interrupted asynchronous operation — commit, deploy, promote, rebase, back sync.

**How to avoid:** In Lifecycle Center every such operation creates a `DevopsRequestInfo` record with `OperationType`, `Status` (`NEW`, `IN_PROGRESS`, `FINALIZING`, `SUCCESS`, `ERROR`, `INTERRUPTED`, `CANCELLED`), `Message`, and `ErrorDetails`. The object reference says to query it when a promotion or commit appears stalled. Keep the query from SKILL.md Core Concepts in the team runbook. These objects belong to Lifecycle Center; on the managed package, check which edition is enabled first (gotcha 8).

---

## Gotcha 2: Out-of-Band Changes Leave Stage Branches Behind

**What happens:** Someone deploys a hotfix to the QA org with the CLI, or edits metadata directly in a stage org. The org now differs from the stage branch, and the next promotion either overwrites the fix or reports a conflict nobody can trace to a work item.

**When it occurs:** Any deploy or Setup edit to a pipeline org that does not go through a work item.

**How to avoid:** Treat every pipeline org as owned by DevOps Center (team practice). When an environment has fallen behind, use the operations DevOps Center records for this purpose — `BACK_SYNC` from the stage named in `BackSyncStageId`, or `REBASE` of the affected work item — instead of hand-editing branches.

---

## Gotcha 3: Source Tracking Applies to New and Refreshed Developer Sandboxes Only

**What happens:** The team enables source tracking for sandboxes, but the existing Developer sandbox still captures nothing; or someone tries to use a Developer Edition org as a development environment.

**When it occurs:** `SourceTrackingSettings.enableSourceTrackingSandboxes` turns tracking on automatically when Developer or Developer Pro sandboxes are created or refreshed, it is set in production (it is ignored in other orgs), and its default is false. Turning it back off does not stop an already-tracking sandbox until that sandbox is refreshed. Developer Edition orgs have no source tracking and can't be DevOps Center development environments.

**How to avoid:** Deploy the setting to production first (see `metadata-examples.md`), then create or refresh each development sandbox. Use scratch orgs or Developer/Developer Pro sandboxes only.

---

## Gotcha 4: Bundling Is a Stage Property

**What happens:** A release manager looks for a "create bundle" action on a set of work items, or flips bundling on a stage mid-release and finds work items already in that stage now move as a group.

**When it occurs:** `DevopsPipelineStage.IsBundled` (default false) indicates that work items in that stage are bundled together for promotion. It is a property of the stage, not of a selection of work items.

**How to avoid:** Decide the bundling stage at pipeline design time, record it in the stage map, and change it only between releases.

---

## Gotcha 5: The Provider Is GitHub or Bitbucket, Connected Through a Named Credential

**What happens:** A team on Bitbucket is told DevOps Center needs GitHub, or a pipeline breaks because the provider connection belonged to a person who left.

**When it occurs:** `SourceCodeRepoProvider.Provider` accepts `GITHUB` (default) and `BITBUCKET`, and its `NamedCredential` field names the credential DevOps Center uses to connect. GitLab and Azure Repos are not values of that picklist.

**How to avoid:** Confirm the provider before setup, and own the credential behind the Named Credential with a service account rather than an individual's login.

---

## Gotcha 6: Validate-Only Deployments Are Not Supported

**What happens:** A team expects a check-only deployment to production before release night, as they had with change sets or the CLI, and cannot find it in DevOps Center.

**When it occurs:** The `DevopsEnvDeployment` object has an `IsCheckDeploy` field, but the object reference states that "Validate-only deployment is not supported in the Lifecycle Center" (`object_reference.txt` 264 L97151; the Summer '26 text said "next-generation DevOps Center").

**How to avoid:** If the release process requires a production validation, run it outside DevOps Center (for example `sf project deploy validate` from the stage branch) and record the result in the release ticket; do not plan around a DevOps Center check-only step.

---

## Gotcha 7: The `Default` Test Level Runs No Tests in Sandboxes

**What happens:** QA and UAT promotions succeed, then the production promotion fails on Apex tests that were never run upstream.

**When it occurs:** `DevopsEnvDeployment.TestLevel` defaults to `Default`, which means no tests in sandboxes and all local tests in production.

**How to avoid:** Set an explicit test level for sandbox stages — `RunLocalTests`, or `RunSpecifiedTests` with the class list in `RunTests` — so test failures surface at QA rather than at production.

---

## Gotcha 8: Two DevOps Centers, Two Data Models

**What happens:** A practitioner queries `WorkItem` or `DevopsRequestInfo` in an org that runs the managed package and gets nothing, or follows managed-package instructions in a Lifecycle Center org.

**When it occurs:** The Dev Hub settings distinguish the managed package (`enableDevOpsCenterGA`, API 56.0+, "an older version of Lifecycle Center") from Lifecycle Center (`enableALMDevopsCorePref`, API 65.0+), which the Summer '26 guide called the "next-generation DevOps Center" (`api_meta.txt` 264 L117302–L117311). The `Devops*` and `WorkItem` standard objects are API 66.0–67.0. Moving projects from the package to Lifecycle Center (`enableDevopsCenterMigrationPref`, API 67.0) is a developer preview.

**How to avoid:** Read `settings/DevHub.settings-meta.xml` (or Setup) before troubleshooting, and do not plan a production migration on a developer-preview setting.
