# Well-Architected Notes — Deployment Error Troubleshooting

## Relevant Pillars

- **Reliability** — Deployment failures are the primary risk to release reliability. Atomic rollback behavior (production default) protects against partial deployments, but sandbox defaults leave orgs vulnerable to inconsistent metadata states. A reliable deployment practice treats sandbox deploys with the same rigor as production: checkOnly validation first, atomic rollback enabled, and full package re-deployment after any failure.
- **Operational Excellence** — Systematic error diagnosis reduces mean time to recovery for failed deployments. Operational excellence requires that deployment errors are classified, resolved by root cause, and documented in a runbook rather than resolved ad hoc. Teams should maintain a catalog of previously-encountered deployment errors and their resolutions to accelerate future troubleshooting.

## Architectural Tradeoffs

**RunSpecifiedTests speed vs. RunLocalTests safety:** `RunSpecifiedTests` is faster because it runs only named tests, but its per-class 75% coverage requirement is stricter per component. `RunLocalTests` runs all non-managed tests (slower) but uses org-wide aggregate coverage (more forgiving per class). The tradeoff is deployment speed vs. coverage granularity. Teams with strong per-class test coverage benefit from `RunSpecifiedTests`; teams with uneven coverage across the codebase should use `RunLocalTests` until coverage gaps are closed.

**checkOnly validation vs. direct deploy:** CheckOnly (dry-run) deployments add a round trip but prevent partial deploys and qualify the package for Quick Deploy. Direct deploys are faster but risk leaving an org in a broken state on failure, especially in sandboxes. Production deployments should always validate first; sandbox deploys can skip validation for low-risk declarative-only changes but should validate whenever Apex is involved.

**Fixing the target org vs. fixing the source project:** Dependency compilation errors can be fixed in either location. Fixing the target org (manual compilation or patching) is faster but creates org drift — the fix is not captured in version control. Fixing the source project and including the dependent class in the deployment is slower but keeps all changes tracked. The Well-Architected approach is to always fix in the source project unless the broken class is a managed package component that cannot be modified.

## Anti-Patterns

1. **Guessing at the root cause without reading componentFailures** — Practitioners who do not examine the `DeployMessage` details waste deployment cycles on incorrect fixes. The componentFailures array contains the exact component name, type, and error text needed to diagnose the issue. Skipping this step violates operational excellence by turning a diagnostic process into trial and error.

2. **Deploying only failed components after a partial sandbox deploy** — After a partial failure, re-deploying only the components that failed leaves the successfully-deployed components at an indeterminate version. If source was modified between the first and second deploy, the org ends up with a mix of versions from different commits. Always re-deploy the full package to ensure version consistency.

3. **Lowering the test level to bypass coverage failures** — When a deployment fails coverage checks, switching from `RunSpecifiedTests` to `NoTestRun` (where allowed) or from `RunLocalTests` to a lower level masks the coverage gap. The gap persists and will surface in production where test levels cannot be lowered below the minimum. Fix the coverage, do not work around it.

## Official Sources Used

- Metadata API Developer Guide — DeployResult and DeployMessage: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_deploy_result.htm
- Salesforce Help — Troubleshoot Deployment Failures: https://help.salesforce.com/s/articleView?id=sf.code_deploy_troubleshoot.htm
- Salesforce Help — Dependent Class Is Invalid: https://help.salesforce.com/s/articleView?id=000382702
- Salesforce CLI Troubleshooting Guide: https://developer.salesforce.com/docs/atlas.en-us.sfdx_setup.meta/sfdx_setup/sfdx_setup_troubleshoot.htm
- Metadata API Developer Guide — deploy() Options: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_deploy.htm
