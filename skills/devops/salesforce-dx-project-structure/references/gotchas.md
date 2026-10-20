# Gotchas — Salesforce DX Project Structure

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: sourceApiVersion Higher Than Target Org

**What happens:** UNVERIFIED (2026-10-20): that deployment fails with `UNSUPPORTED_API_VERSION` and that the message hides the org's supported version; the corpus documents that code only as the SOAP API error for a retired API version (api_meta 264 L1314-1315). The documented behaviour is that `sourceApiVersion` "determines the fields retrieved for each metadata type" (sfdx_dev 264 L2430-2431), so a version older than a type's new field makes project commands error (L2432-2434).

**When it occurs:** After a Salesforce release, when the source version and the target org's version drift apart. UNVERIFIED (2026-10-20): the sandbox refresh-lag and instance-timing scenarios.

**How to avoid:** Check the org's version with `sf org display --target-org <alias>` (`Api Version` row, sfdx_dev 264 L3489) before changing the project config, and keep source and org versions aligned. UNVERIFIED (2026-10-20): "pin to the lowest common version" as a rule.

---

## Gotcha 2: Case-Sensitive Paths in CI but Not Locally

**What happens:** UNVERIFIED (2026-10-20): filesystem behaviour, not a corpus statement and the error texts are not in the corpus. The project works on macOS (case-insensitive filesystem) but can fail in Linux-based CI runners (case-sensitive) with a path-not-found error.

**When it occurs:** A developer creates a directory as `Force-App/` but references it as `force-app` in `sfdx-project.json`, or vice versa. macOS silently resolves both; Linux does not.

**How to avoid:** Enforce lowercase-only directory names as a team convention. Add a CI check that verifies all `packageDirectories[].path` values match actual directory names exactly (case-sensitive comparison).

---

## Gotcha 3: Namespace Scope Across Directories and Projects

**What happens:** `namespace` is a top-level key, "the global namespace that is used with a package" (sfdx_dev 264 L2326-2329), placed at top level in every corpus sample (L2314, L14681); the unlocked-package parameter table at L14826 mixes it with top-level keys such as `packageAliases` (L14831), so a per-directory namespace is UNVERIFIED (2026-10-20). "When you specify a package namespace, every component added to a package has the namespace prefixed to the component API name" (pkg2_dev 264 L946-948), and "a single managed 2GP package can't be associated with more than one namespace" (L953-954). UNVERIFIED (2026-10-20): that a project-level namespace is applied to components in unpackaged directories; the earlier text said so, and the corpus describes prefixing only for components added to a package.

**When it occurs:** Developing a managed package alongside an unpackaged extension in one repo.

**How to avoid:** "If you work with more than one namespace, we recommend that you set up one project for each namespace" (pkg2_dev 264 L955). UNVERIFIED (2026-10-20): the earlier advice that unpackaged profiles and permission sets "ignore namespace".

---

## Gotcha 4: Duplicate packageDirectory Paths (Handling Undocumented)

**What happens:** Two entries in `packageDirectories` point to the same `path`. UNVERIFIED (2026-10-20): that the CLI uses the first entry and silently skips the second with no error or warning; neither corpus describes duplicate-path handling.

**When it occurs:** During a project restructure when someone copies an entry to create a new package but forgets to update the `path`. Also happens in merge conflicts where both sides add a new entry with the same path.

**How to avoid:** Add a pre-commit hook or CI check that validates all `path` values are unique. The checker script in this skill package detects this issue.

---

## Gotcha 5: sfdcLoginUrl Affects Only Default Login

**What happens:** Setting `sfdcLoginUrl` to `https://test.salesforce.com` does not automatically route all CLI commands to sandbox. It is "the login URL that the org login commands use" and defaults to https://login.salesforce.com (sfdx_dev 264 L2420-2423); when it is unset, or you log in outside the project, you pass `--instance-url` (L2424-2425). Developers who switch between production and sandbox frequently get confused about which org they are authenticating to.

**When it occurs:** When a project targets sandboxes and the developer relies on the config rather than explicit flags.

**How to avoid:** Always use explicit `--instance-url` or `--target-org` flags in CI scripts. Set `sfdcLoginUrl` only as a convenience for interactive development, not as a reliable routing mechanism.

---

## Gotcha 6: Retrieving Metadata Into Wrong Package Directory

**What happens:** "Salesforce CLI uses the default package directory as the target directory when retrieving changes from the org to the local project" (sfdx_dev 264 L2365-2366). If you intended the metadata for a different package directory, it ends up in the default one and may be included in the wrong package version.

**When it occurs:** In multi-package projects when a developer retrieves without scoping the retrieve. UNVERIFIED (2026-10-20): the earlier text named a `--target-metadata-dir` flag; that flag is not in the corpus's retrieve examples.

**How to avoid:** Scope the retrieve to a package where one applies: `sf project retrieve start --package-name <PackageName>` (sfdx_dev 264 L2021, L13577). Review retrieved file paths before committing.

---

## Gotcha 7: Stale "Never Move Files" Advice and the Source Mobility Opt-Out (UNVERIFIED, 2026-10-20: not in either corpus)

**What happens:** UNVERIFIED (2026-10-20): grep of both corpora finds neither "source mobility" nor `SF_DISABLE_SOURCE_MOBILITY`; this gotcha rests on a blog and a CLI setup page outside the corpus, last checked 2026-08-13. Pre-Winter '26 guidance holds that moving a metadata file between package directories makes source tracking see the component as deleted and then recreated, so teams refuse to reorganize `packageDirectories` mid-project or reset tracking afterwards to clear the churn. The Winter '26 CLI release changed the default: "With source mobility you can move source files within your local Salesforce DX project without the source-tracking feature determining that you've deleted and then recreated a metadata component." Source mobility is enabled by default.

**When it occurs:** Splitting a single `force-app` into multi-package directories, or moving a component out of `unpackaged/` into a packaged directory. The old delete-plus-recreate churn now reappears only when source mobility has been switched off.

**How to avoid:** Do not treat `sf project reset tracking` as a restructuring ritual. Check two things before blaming source tracking for phantom deletes. First the CLI version — source mobility is a Salesforce CLI feature controlled by a CLI environment variable, not an org setting, so a pipeline pinned to an `sf` release older than Winter '26 still produces delete-plus-recreate churn whatever release the org is on. Second `SF_DISABLE_SOURCE_MOBILITY`, which defaults to `false`; setting it to `true` restores the old behaviour. Audit CI runner images and shell profiles for both, and pin the variable explicitly if a pipeline depends on one behaviour or the other. Note this covers moving files; it is not documented as covering renames, so plan renames separately.
