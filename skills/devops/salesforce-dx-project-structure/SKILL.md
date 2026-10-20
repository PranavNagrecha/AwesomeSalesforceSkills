---
name: salesforce-dx-project-structure
description: "Use this skill when setting up, configuring, or troubleshooting sfdx-project.json, organizing packageDirectories for mono-repo or multi-package projects, managing sourceApiVersion alignment, and structuring the standard source-format directory tree. NOT for scratch org definition files (use devops/scratch-org-management) or CLI command usage — use apex/sf-cli-and-sfdx-essentials."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
  - Scalability
triggers:
  - "how do I set up sfdx-project.json for a new Salesforce DX project"
  - "my deployment fails with UNSUPPORTED_API_VERSION and I need to fix sourceApiVersion"
  - "how should I organize packageDirectories for multiple unlocked packages in one repo"
  - "I want to structure a mono-repo with separate package directories for different teams"
  - "what is the correct force-app directory layout for source format metadata"
  - "sf project deploy fails because package directory path is wrong or missing"
tags:
  - sfdx-project-json
  - source-format
  - package-directories
  - source-api-version
  - mono-repo
  - dx-project
  - force-app
inputs:
  - "sfdx-project.json file (existing or to be created)"
  - "Number of packages or teams sharing the repo"
  - "Target sourceApiVersion for the project"
  - "Namespace (if managed package) or blank for unlocked"
  - "Package dependency graph if multi-package"
outputs:
  - "Compliant sfdx-project.json configuration"
  - "Recommended directory layout for the project"
  - "Diagnosis and remediation for project configuration errors"
  - "Multi-package dependency wiring in sfdx-project.json"
dependencies: []
version: 1.0.2
author: Pranav Nagrecha
updated: 2026-10-20
---

# Salesforce DX Project Structure

This skill activates when you need to create, configure, or troubleshoot the root project configuration file (`sfdx-project.json`) and directory layout for a Salesforce DX project. It covers packageDirectories configuration, sourceApiVersion management, multi-package mono-repo organization, namespace handling, and the standard source-format directory tree.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is this a new project or a restructure of an existing one? If existing, read the current `sfdx-project.json` first.
- How many packages or independent workstreams will share this repository? This determines single vs. multi-package directory layout.
- What API version does the target org support? `sf org display` prints an `Api Version` row (sfdx_dev 264 L3489). UNVERIFIED (2026-10-20): that deploying with a `sourceApiVersion` higher than the org supports fails with `UNSUPPORTED_API_VERSION`; the corpus documents `UNSUPPORTED_API_VERSION` only as the SOAP API error for a retired (too old) API version (api_meta 264 L1314-1315; versions 21.0-30.0 retired as of Summer '25, L1306).

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| How many package directories will the project have, and which one receives retrieved metadata? | Gotcha 2: with several entries one must be the default (sfdx_dev 264 L2363-2366) | A single named default directory |
| Which sourceApiVersion do the metadata files target, and which API versions do the target orgs run? | Gotcha 1: the version decides which fields are retrieved (L2430-2434) | A pinned version and the `Api Version` read from `sf org display` |
| Do any `path` values differ in case from the folders on disk? | Gotcha 3: Linux runners are case-sensitive | A CI check that compares paths exactly |
| Which namespace, if any, and how many managed packages share it? | Gotcha 4: one namespace per managed 2GP, one project per namespace recommended (pkg2_dev 264 L953-955) | A namespace decision per project |
| Could two entries ever point at the same directory? | Gotcha 5: duplicate-path handling is undocumented, so the checker reviews it | Unique paths enforced in review |
| Who increments the build segment of `versionNumber`? | Review Checklist: concrete BUILD vs `NEXT` (L14867-14873) | `NEXT` for auto-increment or a documented manual bump |
| Is deploy order between directories required? | Common Patterns: directories deploy in one transaction by default (L2584-2585) | Ordered `project deploy start --source-dir` runs |

A proper configuration adds one default directory, a pinned source version and an ordered deploy plan; just creating the file gives you none of them.

---

## Core Concepts

Understanding DX project structure requires clarity on four areas: the project configuration file, package directories, source format layout, and API version alignment.

### sfdx-project.json

The `sfdx-project.json` file "indicates that the directory is a Salesforce DX project" and tells the CLI where to put files when syncing with an org (sfdx_dev 264 L2299-2301). `packageDirectories` is the one required key (L2352). The documented optional keys are `name` (required for Salesforce Functions), `namespace`, `oauthLocalPort`, `packageAliases`, `plugins`, `replacements`, `sfdcLoginUrl`, `sourceApiVersion`, `sourceBehaviorOptions` (Beta) and the deprecated `pushPackageDirectoriesSequentially` (L2322-2463). UNVERIFIED (2026-10-20): `signupTargetLoginUrl` appears in neither corpus.

UNVERIFIED (2026-10-20): that the CLI resolves the project root by walking up the directory tree, and that a missing or malformed file makes every `sf` command fail; the guide ties the file to project commands, and some `sf` commands (for example `sf org display`) take no project.

### packageDirectories

The `packageDirectories` array defines which directories to target when syncing source to and from the org (sfdx_dev 264 L2353-2354). Each entry has a `path`, relative to the project, never absolute (L2358-2361). "You can have only one default path"; with one path it is assumed to be the default, and with several "you must indicate which one is the default" (L2363-2364). The CLI retrieves into the default directory and uses it for source conversions when no output directory is given (L2365-2368).

For packages, an entry can also carry `package`, `versionName`, `versionNumber` and `dependencies` (L14804, L14829, L14862-14867). `versionNumber` is "formatted as MAJOR.MINOR.PATCH.BUILD. For example, 1.2.1.8"; the keyword `NEXT` in the build slot (`1.2.1.NEXT`) increments it automatically, and `LATEST` sets a dependency (L14867-14879).

### Source Format Directory Layout

Inside each package directory, metadata follows the Salesforce source format tree. The standard structure is:

```
force-app/
  main/
    default/
      classes/
      triggers/
      lwc/
      aura/
      objects/
        Account/
          fields/
          listViews/
      flows/
      permissionsets/
      profiles/
      layouts/
      tabs/
      applications/
      staticresources/
```

Each metadata type has a defined folder name and file extension. Custom objects are decomposed by default into subfolders for business processes, compact layouts, fields, field sets, indexes, list views, record types, sharing reasons, validation rules and web links (sfdx_dev 264 L1647-1659, L2440); static resources must sit in `main/default/staticresources` (L1487). "Granular source tracking and conflict-free merging" is UNVERIFIED (2026-10-20): not stated in either corpus.

### sourceApiVersion

The `sourceApiVersion` is a string in the guide's examples (`"63.0"`, sfdx_dev 264 L2316) naming "the API version that the source is compatible with"; it "determines the fields retrieved for each metadata type during project deploy, project retrieve, or project convert" (L2429-2431). If the source is at an older version than a type's new field, project commands error because the components lack that field (L2432-2434). It is not the `org-api-version` CLI setting (L2435-2436). For package versions targeting a previous release, "any sourceApiVersion value below the current release is accepted" (L16101-16102). UNVERIFIED (2026-10-20): the `UNSUPPORTED_API_VERSION` failure when the version exceeds the org's, the claim that too low a version "silently excludes" newer types (the guide describes errors, not silence), and the "lowest-supported org" best practice.

---

## Common Patterns

### Single-Package Project

**When to use:** Small to medium projects with one team deploying from one directory.

**How it works:**

```json
{
  "packageDirectories": [
    {
      "path": "force-app",
      "default": true
    }
  ],
  "namespace": "",
  "sourceApiVersion": "62.0",
  "sfdcLoginUrl": "https://login.salesforce.com"
}
```

All metadata lives under `force-app/main/default/`. The `sf` CLI generates new components here automatically. This is the simplest and most common layout.

**Why not multi-package:** Adding unnecessary package boundaries creates build complexity, dependency management overhead, and longer CI times with no benefit for a single-team project.

### Multi-Package Mono-Repo

**When to use:** Large projects where multiple teams own separate packages, or where you need independent package versioning and deployment ordering.

**How it works:**

```json
{
  "packageDirectories": [
    {
      "path": "packages/core",
      "default": true,
      "package": "CoreDataModel",
      "versionName": "Spring 25",
      "versionNumber": "1.3.0.NEXT"
    },
    {
      "path": "packages/sales",
      "package": "SalesAutomation",
      "versionName": "Spring 25",
      "versionNumber": "2.1.0.NEXT",
      "dependencies": [
        {
          "package": "CoreDataModel",
          "versionNumber": "1.3.0.LATEST"
        }
      ]
    },
    {
      "path": "packages/service",
      "package": "ServiceExtensions",
      "versionName": "Spring 25",
      "versionNumber": "1.0.0.NEXT",
      "dependencies": [
        {
          "package": "CoreDataModel",
          "versionNumber": "1.3.0.LATEST"
        }
      ]
    }
  ],
  "namespace": "",
  "sourceApiVersion": "62.0"
}
```

Each team owns its directory. Dependencies flow upward (sales and service depend on core). The `dependencies` list is given "in the order of installation" (sfdx_dev 264 L14813-14814); UNVERIFIED (2026-10-20): that package version creation builds in dependency order automatically. The multi-directory layout is local only: on `project deploy start` "there's no association between its local package directory location and the package in the org" (L2485-2487), and by default all directories deploy in one transaction regardless of order (L2584-2585); for order, run several `project deploy start --source-dir` commands (L2593-2594).

**Why not a single directory:** With multiple teams, a flat directory causes merge conflicts, unclear ownership boundaries, and makes independent deployment impossible.

### Unpackaged Metadata Alongside Packages

**When to use:** When you have packaged components but also need org-specific configuration (profiles, permission sets, page layouts) that should not be packaged.

**How it works:**

```json
{
  "packageDirectories": [
    {
      "path": "packages/core",
      "default": true,
      "package": "CorePackage",
      "versionName": "v1",
      "versionNumber": "1.0.0.NEXT"
    },
    {
      "path": "unpackaged",
      "default": false
    }
  ],
  "namespace": "",
  "sourceApiVersion": "62.0"
}
```

The `unpackaged/` directory is a plain `{ "path": "unpackaged" }` entry like the guide's own sample (sfdx_dev 264 L2311) and holds metadata that deploys via `sf project deploy`. UNVERIFIED (2026-10-20): that it is never included in package version builds, and that it is the correct place for profiles and org-specific permission sets.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single team, no package versioning needed | Single `force-app` directory, no `package` key | Simplest setup; with one path the default is assumed (sfdx_dev 264 L2363-2364) |
| Multiple teams sharing one repo | Multi-package with explicit `dependencies` | Clear ownership; independent versioning; dependency-ordered builds |
| Managed package development | Single package dir with `namespace` set in `sfdx-project.json` | The 2GP package is associated with the namespace in that file (pkg2_dev 264 L992-993) |
| Mix of packaged and org-specific metadata | Separate `unpackaged/` directory entry without `package` key | Keeps org config out of package versions |
| API version mismatch errors on deploy | Lower `sourceApiVersion` to match oldest target org | UNVERIFIED (2026-10-20): a too-high version raising `UNSUPPORTED_API_VERSION`; the corpus gives that code for retired versions only (api_meta 264 L1314-1315); the guide ties `sourceApiVersion` to the fields retrieved (sfdx_dev 264 L2430-2434) |
| Need to support ISV with managed + extension packages | One project per namespace; several managed 2GP packages can share one namespace | A managed 2GP package cannot take more than one namespace, and one project per namespace is recommended (pkg2_dev 264 L953-955) |

---

## Recommended Workflow

Step-by-step instructions for setting up or restructuring a Salesforce DX project:

1. **Check for existing configuration** — Look for `sfdx-project.json` at the repo root. If it exists, read it and identify what needs to change. If it does not exist, run `sf project generate --name <project-name>` to scaffold.
2. **Determine package strategy** — Decide whether the project needs a single package directory, multiple packages, or a mix of packaged and unpackaged metadata. Base this on team count, deployment independence requirements, and ISV packaging needs.
3. **Configure packageDirectories** — Add entries for each directory. With more than one entry, mark exactly one `"default": true` (with one entry it is assumed, sfdx_dev 264 L2363-2364). For package development, add `package`, `versionName`, and `versionNumber` fields. Wire `dependencies` between packages in the correct order (base packages have no dependencies; downstream packages reference upstream versions).
4. **Set sourceApiVersion** — Set to the current API version of your lowest-supported production org (a team convention; the "lowest-supported org" rule is UNVERIFIED, 2026-10-20). Verify by running `sf org display --target-org <alias>` and reading the `Api Version` row (sfdx_dev 264 L3489).
5. **Create the directory tree** — Build out the source-format folder structure inside each package directory. Follow the standard layout: `<path>/main/default/<metadataType>/`. Run `sf project retrieve start` to pull existing metadata into the correct structure.
6. **Validate the configuration** — Run `sf project deploy start --dry-run --target-org <alias>` (the form api_meta 264 L4114 shows) to verify the project structure deploys cleanly. Check for path resolution errors, missing metadata types, and API version mismatches.
7. **Commit and verify** — Ensure `sfdx-project.json` is committed. Never commit `sfdxAuthUrl` values, `.sfdx/` local state, or sandbox credentials. Add `.sfdx/`, `.sf/`, and auth files to `.gitignore` (`sf project generate` creates a `.gitignore` for the standard template, sfdx_dev 264 L1410-1413; UNVERIFIED, 2026-10-20: its entries are not listed in the corpus).

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] `sfdx-project.json` exists at the repository root and is valid JSON
- [ ] `packageDirectories` array has at least one entry with a valid `path`
- [ ] With more than one packageDirectory, exactly one has `"default": true`
- [ ] `sourceApiVersion` is set and matches or is lower than the target org's API version (convention; the failure on a higher version is UNVERIFIED, 2026-10-20)
- [ ] All `path` values in packageDirectories point to directories that exist
- [ ] Package dependencies reference correct package names and valid version numbers
- [ ] `versionNumber` uses `MAJOR.MINOR.PATCH.BUILD`, with `NEXT` in the build slot for auto-increment (sfdx_dev 264 L14867-14873)
- [ ] `.gitignore` excludes `.sfdx/`, `.sf/`, and any auth credential files
- [ ] No `sfdxAuthUrl` or credential values are stored in `sfdx-project.json`

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **UNSUPPORTED_API_VERSION on deploy** — UNVERIFIED (2026-10-20): that a `sourceApiVersion` above the target org's version is rejected with this code, and the refresh-lag scenario; the corpus documents `UNSUPPORTED_API_VERSION` only as the SOAP API error for a retired (too old) API version (api_meta 264 L1314-1315; versions 21.0-30.0 retired as of Summer '25, L1306). What the guide does say: `sourceApiVersion` decides which fields are retrieved per type (sfdx_dev 264 L2430-2434).
2. **Missing default packageDirectory** — With more than one entry you must indicate the default (sfdx_dev 264 L2363-2364; the packaging table marks `default` required when there are several, L14795-14796); with one entry it is assumed. UNVERIFIED (2026-10-20): the "cryptic path resolution error" from `sf apex generate class`.
3. **Path case sensitivity across OS** — UNVERIFIED (2026-10-20): this is filesystem behaviour, not a corpus statement. A `path` of `Force-App` works on a case-insensitive macOS volume but can break on a case-sensitive Linux CI runner if the directory is `force-app`; check the `path` values against the folder names exactly.
4. **Namespace scope** — `namespace` is a top-level key, "the global namespace that is used with a package" (sfdx_dev 264 L2326-2327), and every corpus sample places it at top level (L2314, L14681). The unlocked-package parameter table lists `namespace` (L14826) beside top-level keys such as `packageAliases` (L14831), so it is not evidence of a per-directory namespace; UNVERIFIED (2026-10-20): any per-packageDirectory `namespace` key. For managed 2GP, "a single managed 2GP package can't be associated with more than one namespace" and with several namespaces "we recommend that you set up one project for each namespace" (pkg2_dev 264 L953-955). The earlier claim that multi-namespace work "requires separate repositories" is replaced by that recommendation.
5. **Duplicate path entries** — UNVERIFIED (2026-10-20): that the CLI uses the first of two entries with the same `path` and silently ignores the second; neither corpus describes duplicate-path handling. The checker flags duplicates as a review item.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `sfdx-project.json` | Root project configuration file with packageDirectories, sourceApiVersion, and optional package metadata |
| Directory layout | Source-format folder tree under each package directory path |
| `.gitignore` additions | Entries for `.sfdx/`, `.sf/`, and auth files to prevent credential leaks |

---

## Related Skills

- `sf-cli-and-sfdx-essentials` — For CLI command usage, authentication, and first-time project setup
- `scratch-org-management` — For scratch org definition files and Dev Hub configuration
- `unlocked-package-development` — For package version creation, installation, and promotion workflows
- `github-actions-for-salesforce` — For CI/CD pipeline configuration that deploys from a DX project
- `environment-strategy` — For org strategy decisions that influence project structure
