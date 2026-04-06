# Gotchas — Salesforce DX Project Structure

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: sourceApiVersion Higher Than Target Org

**What happens:** Deployment fails with `UNSUPPORTED_API_VERSION`. The error message references the API version but does not tell you what version the org actually supports.

**When it occurs:** After a Salesforce release, a developer updates `sourceApiVersion` to the latest (e.g., `"63.0"`), but the target sandbox has not been refreshed and still runs the previous release. Also happens when deploying to orgs on different Salesforce instances that receive releases at different times.

**How to avoid:** Set `sourceApiVersion` to the API version of your lowest-supported target org. Check the org's version with `sf org display --target-org <alias>` before updating the project config. In multi-org environments, pin to the version supported by all target orgs.

---

## Gotcha 2: Case-Sensitive Paths in CI but Not Locally

**What happens:** The project works on macOS (case-insensitive filesystem) but fails in Linux-based CI runners (case-sensitive). Errors like "package directory not found" or "source path does not exist" appear only in pipelines.

**When it occurs:** A developer creates a directory as `Force-App/` but references it as `force-app` in `sfdx-project.json`, or vice versa. macOS silently resolves both; Linux does not.

**How to avoid:** Enforce lowercase-only directory names as a team convention. Add a CI check that verifies all `packageDirectories[].path` values match actual directory names exactly (case-sensitive comparison).

---

## Gotcha 3: Namespace Is Project-Wide, Not Per-Package

**What happens:** A developer adds a `namespace` key expecting it to apply only to one packageDirectory. Instead, the namespace applies to every component in the entire project. Components in other directories unexpectedly get prefixed.

**When it occurs:** When trying to develop a managed package alongside an unpackaged extension in the same repo.

**How to avoid:** Understand that `namespace` is a top-level project setting, not per-directory. If you need components without a namespace, either use a second `sfdx-project.json` in a separate repo or ensure unpackaged directories only contain metadata types that ignore namespace (like profiles and permission sets).

---

## Gotcha 4: Duplicate packageDirectory Paths Are Silently Ignored

**What happens:** Two entries in `packageDirectories` point to the same `path`. The CLI uses the first entry and silently skips the second. No error, no warning.

**When it occurs:** During a project restructure when someone copies an entry to create a new package but forgets to update the `path`. Also happens in merge conflicts where both sides add a new entry with the same path.

**How to avoid:** Add a pre-commit hook or CI check that validates all `path` values are unique. The checker script in this skill package detects this issue.

---

## Gotcha 5: sfdcLoginUrl Affects Only Default Login

**What happens:** Setting `sfdcLoginUrl` to `https://test.salesforce.com` does not automatically route all CLI commands to sandbox. It only affects the default login URL used by `sf org login web` when no `--instance-url` flag is provided. Developers who switch between production and sandbox frequently get confused about which org they are authenticating to.

**When it occurs:** When a project targets sandboxes and the developer relies on the config rather than explicit flags.

**How to avoid:** Always use explicit `--instance-url` or `--target-org` flags in CI scripts. Set `sfdcLoginUrl` only as a convenience for interactive development, not as a reliable routing mechanism.

---

## Gotcha 6: Retrieving Metadata Into Wrong Package Directory

**What happens:** Running `sf project retrieve start` without specifying a target directory places retrieved metadata into the `default` packageDirectory. If you intended the metadata for a different package directory, it ends up in the wrong place and may be included in the wrong package version.

**When it occurs:** In multi-package projects when a developer forgets the `--target-metadata-dir` flag or does not specify the package.

**How to avoid:** In multi-package projects, always specify which package to target: `sf project retrieve start --package-name <PackageName>`. Review retrieved file paths before committing.
