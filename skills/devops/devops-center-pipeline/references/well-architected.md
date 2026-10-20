# Well-Architected Notes — DevOps Center Pipeline

## Relevant Pillars

- **Operational Excellence** — DevOps Center replaces ad-hoc change set processes with a tracked, auditable, source-controlled release pipeline. The stage chain enforces promotion order, and the work item model gives every change a named owner and history. Teams should define a branch protection policy, a bundling stage, and a test level per stage to realize these benefits.
- **Security** — The source control connection runs through a Named Credential named on the provider record. The credential behind it should be owned by a service account, not a personal account; if the individual's account is deactivated, the pipeline loses connectivity. Branch protection in the provider prevents direct pushes to stage branches.
- **Reliability** — The pipeline's reliability depends on the provider connection and on stage environments matching their branches. Out-of-band deploys break that match; back sync and rebase are the recovery operations, and failed operations are visible on `DevopsRequestInfo`.
- **Adaptability** — Adding a sandbox stage is a configuration change, not a code change. The Lifecycle Center data model also carries test suites, test providers, and quality gates per stage (`DevopsTestSuiteStage`, `DevopsQualityGate`, API 67.0), so evaluate those before concluding the team has outgrown DevOps Center.

## Architectural Tradeoffs

**DevOps Center vs. SFDX CLI + CI/CD:** DevOps Center is purpose-built for admin and low-code teams that want source control benefits without building a CI/CD platform. It trades flexibility for ease of use. SFDX CLI plus a CI service offers full scripting control and validate-only runs, but requires developer investment to set up and maintain. Choose DevOps Center when the team's primary skill is declarative configuration; choose CLI CI/CD when the team needs custom gates DevOps Center cannot express.

**Bundling strategy:** Bundling early (on QA) reduces conflict risk but holds back items that are ready to ship. Bundling late (on UAT or staging) lets simple items flow individually through QA and assembles the release where it is tested as a whole. Teams with heavy shared metadata (profiles, permission sets, shared flows) benefit from an earlier bundling stage.

**Provider choice:** The provider picklist offers GitHub and Bitbucket. Teams standardized on another Git host must either introduce one of these as the system of record for Salesforce metadata or use a CLI-based pipeline. Evaluate this at adoption time, not after setup.

## Anti-Patterns

1. **Using DevOps Center as a deployment shortcut alongside SFDX CLI** — Mixing CLI deployments into DevOps Center-managed orgs leaves stage branches describing a different org than the one deployed. Either commit to DevOps Center for all changes in those orgs, or use the CLI exclusively for them.

2. **Skipping branch protection rules after pipeline setup** — Stage branches are DevOps Center infrastructure. Leaving them unprotected in the provider allows deletion or force pushes that are time-consuming to recover from (team practice).

3. **Connecting DevOps Center through a personal account** — When the credential behind the provider's Named Credential belongs to one developer, the pipeline breaks when that person leaves or revokes access. Use a dedicated service account.

## Official Sources Used

Corpus: Summer '26 (API 67.0) PDFs; line numbers are `grep -n` positions in the `pdftotext -layout` text.

- Metadata API Developer Guide (`api_meta.txt`) L114168–114198 — DevHubSettings `enableALMDevopsCorePref` (next-generation, API 65.0), `enableDevOpsCenterGA` (managed package, "an older version", API 56.0), `enableDevopsCenterMigrationPref` (API 67.0, developer preview) (Before Starting, gotcha 8). Winter '27 (264) renames the product: the same fields at `api_meta.txt` 264 L117302–L117341 say "Lifecycle Center" and describe the package as "an older version of Lifecycle Center".
- Metadata API Developer Guide L127445–127491 — SourceTrackingSettings: Developer and Developer Pro sandboxes, `enableSourceTrackingSandboxes` default false, applies at create/refresh, production-only, sample XML (gotcha 3, metadata-examples.md).
- Apex Developer Guide (`salesforce_apex_developer_guide.txt`) L544–546 and L563–564 — source-tracked Developer/Developer Pro sandboxes work with DevOps Center; Developer Edition orgs can't be DevOps Center development environments (Before Starting).
- Object Reference (`object_reference.txt`) L8099–8150 and L8181–8183 — DevOps Center standard objects and their API versions (Devops*, `DevopsRequestInfo`) (Core Concepts).
- Object Reference L97329–97462 — `DevopsPipelineStage`: environment + branch, `IsBundled` (L97384, default false), `NextStageId` null for production (L97432) (gotcha 4, checker).
- Object Reference L316811–316826 — `WorkItem.Status` values from `NEW` to `CLOSED`, including `MERGE_CONFLICT` and `COMBINED` (Core Concepts "Work Items").
- Object Reference L96707–96719 — `DevopsEnvDeployment.TestLevel` values (`Default` = no tests in sandboxes) and "Validate-only deployment is not supported in the next-generation DevOps Center" (gotchas 6 and 7); 264 L97151 reads "...in the Lifecycle Center".
- Object Reference L98533–98690 — `DevopsRequestInfo` `ErrorDetails` (L98549), `OperationType` incl. `BACK_SYNC`, `REBASE`, `REBASE_AND_COMBINE` (L98597–98604), `Status` values (L98672), usage guidance for stalled operations (L98687–98690) (gotcha 1, troubleshooting SOQL).
- Object Reference L97844 and L97909 — `DevopsPipelnStgPromWkItem` tracks each work item's merge into the target stage branch; `MergeRemoteReference` holds the provider reference such as a pull request (Core Concepts "Conflicts").
- Object Reference L96456–96464 — `BackSyncStageId`, the stage changes are back-synced from (gotcha 2).
- Object Reference L272905–272992 and L273039, L273228 — `SourceCodeRepoProvider` (`GITHUB` default, `BITBUCKET`, `NamedCredential` field), repository default branch typically `main`, work item branch example `feature/WI-000001` (gotcha 5, examples).
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
