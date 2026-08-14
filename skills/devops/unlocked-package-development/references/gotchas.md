# Gotchas — Unlocked Package Development

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Namespace-Less Packages Cannot Be Converted to Namespaced

**What happens:** A team creates an unlocked package with `"namespace": ""` (the default). After several released versions, the team decides they want namespace isolation for API name safety. There is no migration path — the package must be deleted and recreated with a namespace. All subscriber orgs must uninstall the old package and reinstall the new namespaced version. This is a breaking change for every subscriber.

**When it occurs:** Any time a team makes the namespace decision without understanding it is permanent. Common in early-stage projects where the namespace requirement is discovered after go-live.

**How to avoid:** Make the namespace decision before running `sf package create`. If there is any chance the package will ever need a namespace (inter-org distribution, multiple teams, potential AppExchange, or need for API name uniqueness guarantees), either register a namespace and use it from the start, or document explicitly that the package is namespace-less by design and will never be namespaced. Do not defer the decision.

---

## Gotcha 2: Package Version Ancestry Is Linear — No Branching

**What happens:** The `ancestorId` field enforces that each package version has exactly one parent version. If a team tries to create version `3.0.0` from two different parent versions (e.g., one branch diverged from `2.0.0` and another from `2.5.0`), only one can be set as the ancestor. The version number space cannot model git-style branching — there is no merge concept in package version ancestry.

Teams that run parallel release branches (e.g., a hotfix branch and a feature branch) both needing their own package versions hit this constraint and discover that only one version lineage can be the official "trunk."

**When it occurs:** Multi-team projects with parallel feature development where each feature branch attempts to create independent package versions. Also occurs when a hotfix is needed on top of a released version while a major version is in development on a different branch.

**How to avoid:** Manage parallel development through scratch org isolation and source control branching, not through separate package version lineages. Create package versions only from the main branch. For hotfixes: complete the hotfix, merge to main, then create a version from main. The ancestor chain must always represent the linear release history, not the development branching strategy.

---

## Gotcha 3: Uninstalling an Unlocked Package Deletes Its Components from the Subscriber Org

**What happens:** Unlike Metadata API deployments or change sets (which leave metadata in place after deployment), unlocked package components are owned by the package. When a subscriber uninstalls an unlocked package, Salesforce removes all components that belong to that package from the org — custom objects, fields, classes, LWCs, flows, everything. Data in custom objects is also deleted if the `--no-prompt` flag is used and the package is uninstalled without a data preservation step.

This is by design (package ownership model), but it surprises teams coming from change-set-based deployments where undeploying was not a concept.

**When it occurs:** Any uninstall of an unlocked package from a subscriber org. Common scenario: a team decides to restructure packages (split one into two) and must uninstall the old combined package before installing the two new ones, inadvertently deleting org components and data.

**How to avoid:** Before any uninstall:
1. Export data from all custom objects owned by the package.
2. Verify no other installed packages or org metadata depend on components in the package being uninstalled (check via `sf package installed list` and dependency analysis).
3. Test the uninstall sequence in a sandbox that mirrors production before touching production.
4. If restructuring packages, plan a migration path that includes data backups and re-import steps.

---

## Gotcha 4: Beta Versions Are Permanently Blocked from Production Installs

**What happens:** A beta package version (`04t...` with status `Beta`) cannot be installed in a production org under any circumstances — no override flag exists. Teams that skip the promotion step in their pipeline because "it worked in sandbox" discover this at the production deployment step when `sf package install` returns a hard error.

**When it occurs:** Any pipeline that does not have an explicit `sf package version promote` step before production deployment. Also occurs when a hotfix is rushed and the promotion step is accidentally skipped.

**How to avoid:** Gate the production install step in CI/CD behind an explicit promotion check. One pattern: query the package version status via `sf package version report --json` and assert `"Status": "Released"` before allowing the pipeline to proceed. Make promotion a mandatory manual approval step in the pipeline, not an automated background operation.

---

## Gotcha 5: Code Coverage Is Measured in the Version Creation Org, Not in the Subscriber Org

**What happens:** Code coverage for an unlocked package version is calculated during `sf package version create` by running the package's tests in the scratch org (or build org) used for version creation. If that scratch org has a different configuration than the target subscriber org (missing custom settings, different feature flags, different test data), the coverage numbers can diverge significantly.

A version that achieves 76% coverage in the version creation org may have different coverage in a subscriber org where tests run differently. Promotion requires only that the version-creation-time coverage passes — there is no re-evaluation at install time.

**When it occurs:** When the scratch org definition file used for version creation does not mirror the subscriber org environment. Common in teams that use a minimal scratch org for speed and discover that production-equivalent tests fail or have lower coverage in a more fully configured environment.

**How to avoid:** Use `--code-coverage` flag when creating versions and review the per-class coverage breakdown via `sf package version report`. Ensure the scratch org definition file used for version creation (`definitionFile` in `sfdx-project.json`) includes the same features and settings as the target subscriber org. Run the full test suite in a sandbox that mirrors production as a secondary validation step before promoting.

---

## Gotcha 6: `packageAliases` Must Be Kept in Sync Manually — There Is No Auto-Sync

**What happens:** When `sf package create` or `sf package version create` creates new IDs, it updates `sfdx-project.json` automatically if the command is run locally. However, in CI environments that do not commit the updated `sfdx-project.json` back to source control, the new `04t...` version IDs accumulate only in CI outputs and are never captured in the file. Developers checking out the repo later have stale or missing version aliases, causing dependency resolution failures.

**When it occurs:** CI pipelines that treat `sfdx-project.json` as read-only or do not include a commit step after version creation. Common in teams that copy-paste version IDs from CI logs manually.

**How to avoid:** Include a step in the CI pipeline that commits the updated `sfdx-project.json` (with new aliases written by the CLI) back to the repository or to a release branch. Alternatively, use the `--json` output of `sf package version create` to capture the version ID and store it as a pipeline artifact or environment variable for downstream steps, and treat `sfdx-project.json` as the authoritative store to be updated and committed.

---

## Gotcha 7: Promotion Is Spend-Once Per Version Number, and `version delete` Is Not an Undo

**What happens:** The Salesforce DX Developer Guide states it flatly: "You can promote and release only once for each package version number, and you can't undo this change." Once `sf package version promote --package "Expense Manager@1.3.0-7"` returns `Successfully promoted the package version, ID: 04t... to released.`, that build number is spent. A defect found an hour later cannot be fixed by rebuilding `1.3.0-7` and re-promoting it — the number is burned and you must ship `1.3.0-8`.

Teams then reach for `sf package version delete` as an "un-promote." It is not one. For unlocked packages a released version *can* be deleted (unlike 2GP managed packages, where only beta versions are deletable) — but deletion is permanent, every later attempt to install that `04t...` fails, and any package that names it as a dependency breaks. Deleting does not return the version to beta and does not undo the release.

Promotion is additionally gated by a permission most orgs never provision deliberately: the **Promote a package version to released** user permission, which must be enabled in the **Dev Hub** org for the user (or CI integration user) running the command. Salesforce's guidance is to create a permission set containing this permission and assign it only to the users who should be able to release.

**When it occurs:** Pipelines that promote automatically on every green `main` build. Also hotfixes promoted ahead of QA sign-off, and first-time setups where the CI integration user fails the promote step because nobody assigned the permission.

**How to avoid:** Treat promotion as a release event, not a build step — manual approval gate, run after sandbox validation. Enforce it at the platform layer too: put **Promote a package version to released** in a `Release_Manager` permission set assigned only to release managers in the Dev Hub, so an automation account cannot promote by accident. When a promoted version is bad, roll forward to a new build number; never plan a rollback that depends on deleting or demoting the released version.
