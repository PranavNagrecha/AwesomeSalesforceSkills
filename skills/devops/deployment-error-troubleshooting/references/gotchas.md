# Gotchas — Deployment Error Troubleshooting

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Sandbox Partial Deploys Are Silent and Persistent

**What happens:** A deployment to a sandbox fails on 2 of 15 components. The practitioner sees "Deploy failed" and assumes nothing was applied. In reality, 13 components were successfully deployed and remain in the org. The sandbox now has metadata at a version that does not match any branch in version control. Subsequent deploys may behave unpredictably because the org state is a hybrid of the old and new versions.

**When it occurs:** Every sandbox deployment where `rollbackOnError` is not explicitly set to `true` — which is the default for all non-production orgs. This is especially dangerous when deploying Apex triggers alongside their dependent classes: the trigger may deploy but the class it calls may not, causing runtime errors for users.

**How to avoid:** Always use `--test-level RunLocalTests` for sandbox deployments that include Apex. Alternatively, use the Metadata API `deploy()` call directly and set `rollbackOnError=true`. After any failed sandbox deploy, run `sf project deploy report --json` to identify exactly which components landed.

---

## Gotcha 2: Compile All Classes Does Not Fix All Dependency Errors

**What happens:** A practitioner encounters "Dependent class is invalid" errors and navigates to Setup > Apex Classes > Compile All Classes. The compilation succeeds for all classes, but the next deployment attempt still fails with the same error. This occurs because Salesforce caches compilation state at the deployment layer differently from the Setup UI compilation.

**When it occurs:** When the dependent class compiles successfully on its own but fails during transitive recompilation in the deployment context — usually because the deployment introduces a method signature change that the dependent class cannot resolve at deploy time, even though the class was previously compiled against the old signature.

**How to avoid:** Include the dependent class in the deployment package. If the dependent class is not owned by your team, coordinate with the owning team to deploy a compatible version first. Manual Compile All in Setup is a useful diagnostic step but not a reliable fix for deployment-time compilation errors.

---

## Gotcha 3: RunSpecifiedTests Coverage Is Per-Class, Not Per-Org

**What happens:** A team switches from `RunLocalTests` to `RunSpecifiedTests` for faster production deploys. Deployments that previously passed now fail with coverage warnings on specific classes that were below 75% individually but were hidden by the org-wide aggregate being above 75%.

**When it occurs:** Any production deployment using `RunSpecifiedTests` where the specified test classes do not collectively provide 75% coverage for every Apex class in the deployment package. The per-class evaluation is the key behavioral difference from `RunLocalTests` and `RunAllTestsInOrg`.

**How to avoid:** Before switching to `RunSpecifiedTests`, run a coverage analysis with `sf apex run test --code-coverage --result-format json` and check the per-class coverage for every class in the deployment package. Ensure every class meets 75% individually from the tests you plan to specify.

---

## Gotcha 4: Quick Deploy Invalidation Is Not Communicated

**What happens:** A validation succeeds and the team schedules a Quick Deploy for the weekend maintenance window. Before the window, a developer adds one more class to the package "while we're at it." The Quick Deploy is attempted with the modified package and fails silently or triggers a full test run instead of the expected instant deployment.

**When it occurs:** Any modification to the deployment package after a successful validation invalidates the Quick Deploy eligibility. The package hash must match exactly. Adding, removing, or modifying any component — even a whitespace change in a class — creates a new package that requires a fresh validation.

**How to avoid:** Treat the validated package as frozen. If any change is needed, run a new validation and wait for it to complete before scheduling the Quick Deploy. CI pipelines should enforce this by hashing the deployment package and comparing it to the validation package hash.

---

## Gotcha 5: API Version in sfdx-project.json vs. Individual Meta Files

**What happens:** A practitioner sets `sourceApiVersion` to `61.0` in `sfdx-project.json` but individual `-meta.xml` files still reference `62.0` from when they were retrieved from a preview sandbox. The deployment fails with `UNSUPPORTED_API_VERSION` even though `sfdx-project.json` looks correct. The `sourceApiVersion` in `sfdx-project.json` controls which API version the CLI uses for the deployment request, but individual component metadata files declare their own API version in the `<apiVersion>` element. When these disagree, the component-level version wins for schema validation.

**When it occurs:** After retrieving metadata from a sandbox on a newer release, or when team members work on sandboxes at different release levels and commit their retrieved metadata without normalizing the API version.

**How to avoid:** Standardize the API version across all `-meta.xml` files in the project. Use a pre-commit hook or CI check that scans for API version mismatches. After retrieving from any org, normalize the version before committing.

---

## Gotcha 6: A User-Permission Field Removed From the Org Schema Breaks Profile and PermissionSet Deploys, and Lowering the API Version Does Not Help

**What happens:** A Profile or PermissionSet in version control carries the **Waive Multi-Factor Authentication for Exempt Users** user permission. As MFA enforcement rolls out, the API field backing that permission "is removed from the PermissionSet and Profile object schema, unless you have reached out to Salesforce Support for an extension." Metadata that still names it now references a field the target schema no longer has. Salesforce publishes the packaged-code consequence verbatim: "When removed, referencing this field by API name will cause compilation errors that block package installs or upgrades." The MFA article prints no error string for the unpackaged case, but this failure shape has its own documented error: a Profile deploy naming a user permission the org does not have fails with `Error: Unknown user permission: <Name>`. Triage on that string plus the permission named in `componentFailures`.

**When it occurs:** On calendar enforcement dates, not on a release upgrade — sandboxes from July 10, 2026 (the schedule table dates that row `Sandboxes [Preview]`, and says non-preview sandbox timing differs) and production from July 20, 2026 (Release Group `R0`), staggered by Release Group, with the group the article labels "All others not listed" on September 3, 2026. This is the trap for anyone reaching for Gotcha 5's remedy: the removal is a change to the org's object schema, so lowering `sourceApiVersion` or the `<apiVersion>` in a `-meta.xml` file does not restore the field. Unlike Apex behavior changes, it is not pinned by the component's API version.

**How to avoid:** Before your org's Release Group date, scan the project's `profiles/` and `permissionsets/` directories for the waiver permission and delete only the single `<userPermissions>` element whose `<name>` is that permission — not every `<userPermissions>` element in the file, which would strip every user permission the Profile or PermissionSet grants. Confirm the exact token against your own org first — retrieve a Profile or PermissionSet and read the identifier the platform actually emits. Do not copy the API field name out of an article or from memory: the Salesforce Help page prints it in two different casings (`...ForUILogins` and `...ForUiLogins`) in the same document, so neither spelling is safe to hard-code into a manifest or a cleanup script. If a genuine exemption is required — automated test users are the case Salesforce names — it has to be approved by Salesforce Support; assigning the permission no longer grants it.
