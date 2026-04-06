---
name: salesforce-dx-project-structure
description: "Use this skill when setting up, configuring, or troubleshooting sfdx-project.json, organizing packageDirectories for mono-repo or multi-package projects, managing sourceApiVersion alignment, and structuring the force-app directory tree for source-driven development. NOT for scratch org definition files (use scratch-org-management), CLI command usage (use sf-cli-and-sfdx-essentials), or CI/CD pipeline configuration (use github-actions-for-salesforce or bitbucket-pipelines-for-salesforce)."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Salesforce DX Project Structure

This skill activates when you need to create, configure, or troubleshoot the root project configuration file (`sfdx-project.json`) and directory layout for a Salesforce DX project. It covers packageDirectories configuration, sourceApiVersion management, multi-package mono-repo organization, namespace handling, and the standard source-format directory tree.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is this a new project or a restructure of an existing one? If existing, read the current `sfdx-project.json` first.
- How many packages or independent workstreams will share this repository? This determines single vs. multi-package directory layout.
- What API version does the target org support? Deploying with a `sourceApiVersion` higher than the org supports causes `UNSUPPORTED_API_VERSION` failures.

---

## Core Concepts

Understanding DX project structure requires clarity on four areas: the project configuration file, package directories, source format layout, and API version alignment.

### sfdx-project.json

The `sfdx-project.json` file is the root configuration file for every Salesforce DX project. It lives at the repository root and is required for all `sf` CLI operations. The file must contain at minimum a `packageDirectories` array with at least one entry. Other top-level keys include `sourceApiVersion`, `namespace`, `sfdcLoginUrl`, `signupTargetLoginUrl`, and `plugins`.

The CLI resolves the project root by walking up the directory tree until it finds this file. If the file is missing or malformed, every `sf` command fails immediately.

### packageDirectories

The `packageDirectories` array defines which folders contain deployable metadata. Each entry requires a `path` (relative to the project root). Exactly one entry must have `"default": true` — this is where `sf` CLI commands place newly created metadata by default.

For unlocked or managed packages, each entry can also include `package` (the package name), `versionName`, `versionNumber` (format: `MAJOR.MINOR.PATCH.NEXT`), and `dependencies` (array of package references with minimum version constraints).

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

Each metadata type has a defined folder name and file extension. Objects decompose into subfolders for fields, list views, record types, and other child components. This decomposed structure enables granular source tracking and conflict-free merging.

### sourceApiVersion

The `sourceApiVersion` is a string (e.g., `"62.0"`) that tells the CLI which metadata API version to use for deploys and retrieves. If this version is higher than the org's API version, the deployment fails with `UNSUPPORTED_API_VERSION`. If it is too low, newer metadata types are silently excluded from retrieves. Best practice: set it to the current API version of your lowest-supported org.

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

Each team owns its directory. Dependencies flow upward (sales and service depend on core). Package version creation builds in dependency order automatically.

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

The `unpackaged/` directory holds metadata that deploys via `sf project deploy` but is never included in package version builds. This is the correct place for profiles, org-specific permission sets, and post-install configuration.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single team, no package versioning needed | Single `force-app` directory, no `package` key | Simplest setup; avoids package build overhead |
| Multiple teams sharing one repo | Multi-package with explicit `dependencies` | Clear ownership; independent versioning; dependency-ordered builds |
| Managed package development | Single package dir with `namespace` set at project level | Namespace applies to all metadata in the project |
| Mix of packaged and org-specific metadata | Separate `unpackaged/` directory entry without `package` key | Keeps org config out of package versions |
| API version mismatch errors on deploy | Lower `sourceApiVersion` to match oldest target org | Prevents `UNSUPPORTED_API_VERSION` rejections |
| Need to support ISV with managed + extension packages | Multi-package with namespace on managed, blank on extensions | Each package can have its own lifecycle |

---

## Recommended Workflow

Step-by-step instructions for setting up or restructuring a Salesforce DX project:

1. **Check for existing configuration** — Look for `sfdx-project.json` at the repo root. If it exists, read it and identify what needs to change. If it does not exist, run `sf project generate --name <project-name>` to scaffold.
2. **Determine package strategy** — Decide whether the project needs a single package directory, multiple packages, or a mix of packaged and unpackaged metadata. Base this on team count, deployment independence requirements, and ISV packaging needs.
3. **Configure packageDirectories** — Add entries for each directory. Ensure exactly one has `"default": true`. For package development, add `package`, `versionName`, and `versionNumber` fields. Wire `dependencies` between packages in the correct order (base packages have no dependencies; downstream packages reference upstream versions).
4. **Set sourceApiVersion** — Set to the current API version of your lowest-supported production org. Verify by running `sf org display --target-org <alias>` and checking the API version in the output.
5. **Create the directory tree** — Build out the source-format folder structure inside each package directory. Follow the standard layout: `<path>/main/default/<metadataType>/`. Run `sf project retrieve start` to pull existing metadata into the correct structure.
6. **Validate the configuration** — Run `sf project deploy start --dry-run --target-org <alias>` to verify the project structure deploys cleanly. Check for path resolution errors, missing metadata types, and API version mismatches.
7. **Commit and verify** — Ensure `sfdx-project.json` is committed. Never commit `sfdxAuthUrl` values, `.sfdx/` local state, or sandbox credentials. Add `.sfdx/`, `.sf/`, and auth files to `.gitignore`.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] `sfdx-project.json` exists at the repository root and is valid JSON
- [ ] `packageDirectories` array has at least one entry with a valid `path`
- [ ] Exactly one packageDirectory has `"default": true`
- [ ] `sourceApiVersion` is set and matches or is lower than the target org's API version
- [ ] All `path` values in packageDirectories point to directories that exist
- [ ] Package dependencies reference correct package names and valid version numbers
- [ ] `versionNumber` uses the format `MAJOR.MINOR.PATCH.NEXT` (not `MAJOR.MINOR.PATCH.BUILD`)
- [ ] `.gitignore` excludes `.sfdx/`, `.sf/`, and any auth credential files
- [ ] No `sfdxAuthUrl` or credential values are stored in `sfdx-project.json`

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **UNSUPPORTED_API_VERSION on deploy** — If `sourceApiVersion` in `sfdx-project.json` is higher than the target org's current API version, the deploy is rejected outright. This commonly happens when a developer updates the version after a Salesforce release but the target sandbox has not been refreshed to the new release yet.
2. **Missing default packageDirectory** — If no entry has `"default": true`, the CLI cannot resolve where to place newly generated metadata. Commands like `sf apex generate class` fail with a cryptic path resolution error rather than a clear "no default directory" message.
3. **Path case sensitivity across OS** — macOS is case-insensitive by default but Linux CI runners are case-sensitive. A `path` of `Force-App` works locally but breaks in CI if the actual directory is `force-app`. This causes intermittent "package directory not found" failures that only appear in pipelines.
4. **Namespace is project-wide, not per-directory** — The `namespace` key applies to the entire project. You cannot assign different namespaces to different packageDirectories within the same `sfdx-project.json`. Multi-namespace development requires separate repositories.
5. **Duplicate path entries silently ignored** — If two packageDirectories point to the same `path`, the CLI uses the first entry and silently ignores the second. This can mask configuration errors where a developer intended separate packages but used the same path.

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
