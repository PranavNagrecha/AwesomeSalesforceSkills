---
name: multi-package-development
description: "Designing, orchestrating, and maintaining multi-package architectures in Salesforce DX: dependency DAG design, layered package decomposition, install ordering, cross-package API contracts, mono-repo vs. multi-repo layout, and CI/CD pipeline sequencing for projects with two or more unlocked or managed packages. NOT for single-package creation or versioning (see unlocked-package-development), 2GP managed-package ISV workflows (see second-generation-managed-packages), or change-set deployments."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Reliability
  - Operational Excellence
triggers:
  - "how do I split my Salesforce project into multiple packages and manage their dependencies"
  - "my package version create fails because a dependency package version is not found or mismatched"
  - "what order do I install packages in and how do I automate multi-package installs in CI/CD"
  - "should I use a mono-repo or separate repos for each package"
  - "how do I design a base/core package that other packages depend on without creating circular dependencies"
  - "I need to restructure sfdx-project.json for a layered multi-package project"
tags:
  - multi-package
  - package-dependencies
  - dependency-management
  - sfdx-project
  - package-architecture
  - devops
inputs:
  - "sfdx-project.json with multiple packageDirectories and packageAliases"
  - "Dev Hub org alias with Unlocked Packages and/or Second-Generation Packaging enabled"
  - "Current package dependency graph (which packages depend on which)"
  - "Source control layout — mono-repo or multi-repo"
  - "CI/CD pipeline platform in use (GitHub Actions, Bitbucket Pipelines, Azure DevOps, etc.)"
outputs:
  - "Validated dependency DAG with topological install order"
  - "Compliant sfdx-project.json with layered packageDirectories and dependency declarations"
  - "CI/CD pipeline stage sequence for building and installing packages in correct order"
  - "Decision guidance on mono-repo vs. multi-repo and package decomposition strategy"
  - "Diagnosis and remediation for dependency resolution failures, circular references, and install ordering errors"
dependencies:
  - unlocked-package-development
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Multi-Package Development

This skill activates when a Salesforce project spans two or more packages (unlocked or managed) and the practitioner needs to design, build, install, or maintain the cross-package dependency graph. It covers package decomposition strategy, dependency DAG design, topological install ordering, sfdx-project.json multi-directory configuration, mono-repo vs. multi-repo layout, and CI/CD pipeline sequencing. It does not cover single-package creation, versioning, or 2GP ISV workflows.

---

## Before Starting

Gather this context before working on anything in this domain:

- How many packages exist today, and what metadata does each contain? Review the `packageDirectories` array in `sfdx-project.json` and the `packageAliases` map.
- What is the current dependency graph? Each package directory's `dependencies` array declares subscriber package version IDs (04t...) it depends on. Circular dependencies are illegal and will cause version-create failures.
- Is the project in a mono-repo (all packages in one repository) or multi-repo (separate repos per package)? This drives CI/CD sequencing and source-of-truth decisions.
- Are packages unlocked, managed, or a mix? Managed packages introduce namespace isolation and @namespaceAccessible constraints that affect cross-package API surfaces.

---

## Core Concepts

### Dependency DAG (Directed Acyclic Graph)

Every multi-package project has a dependency graph. Salesforce enforces that this graph must be acyclic: if Package A depends on Package B, Package B cannot depend on Package A at any depth. The `sf package version create` command resolves dependencies at build time using the subscriber package version IDs listed in `sfdx-project.json`. If a dependency version does not exist or has not been promoted, the build fails.

The DAG determines:
- **Build order** — packages must be versioned from leaves (no dependencies) to root (depends on everything).
- **Install order** — packages must be installed in the same leaf-to-root order in every target org.
- **Upgrade order** — when updating packages, dependents must be upgraded after their dependencies.

### Layered Package Architecture

The standard decomposition pattern is a layered model:

1. **Base/Core layer** — shared objects, fields, and platform utilities with no outbound dependencies.
2. **Domain layer(s)** — business-logic packages (Sales, Service, etc.) that depend on Base.
3. **Experience/UI layer** — LWC, Aura, Flows, and page layouts that depend on Domain and Base.

Each layer depends only on layers below it. This prevents circular references and keeps the base package stable.

### sfdx-project.json Multi-Package Configuration

A single `sfdx-project.json` can declare multiple packages via the `packageDirectories` array. Each entry specifies:
- `path` — the source directory for that package's metadata.
- `package` — the package alias (must match a key in `packageAliases`).
- `versionName` / `versionNumber` — human-readable version label and MAJOR.MINOR.PATCH.BUILD format.
- `dependencies` — array of `{ "package": "<alias>", "versionNumber": "X.Y.Z.LATEST" }` objects declaring upstream packages.
- `default` — at most one directory can be `true`; the CLI uses this when no `--path` is specified.

Only one entry should have `"default": true`. The `packageAliases` section maps human-readable names to subscriber package version IDs (04t...) or package IDs (0Ho...).

### Install Ordering and Idempotency

Packages must be installed in topological order. Installing a package before its dependencies are present in the target org produces `MISSING_DEPENDENCY` errors. In CI/CD, this means the pipeline must:
1. Compute the topological sort of the DAG.
2. Install (or upgrade) each package in that order.
3. Handle partial failures gracefully — a failed mid-chain install should not leave the org in an inconsistent state.

The `sf package install` command is idempotent for the same version: re-installing an already-installed version is a no-op.

---

## Common Patterns

### Pattern 1: Layered Mono-Repo with Shared sfdx-project.json

**When to use:** Teams that own all packages and want a single source of truth for the dependency graph.

**How it works:**

```
my-project/
  sfdx-project.json
  force-app-base/     # Base package source
  force-app-sales/    # Sales domain package source
  force-app-service/  # Service domain package source
  force-app-ui/       # Experience layer source
```

```json
{
  "packageDirectories": [
    {
      "path": "force-app-base",
      "default": true,
      "package": "MyOrg-Base",
      "versionName": "Spring 2025",
      "versionNumber": "1.2.0.NEXT",
      "dependencies": []
    },
    {
      "path": "force-app-sales",
      "package": "MyOrg-Sales",
      "versionName": "Spring 2025",
      "versionNumber": "1.1.0.NEXT",
      "dependencies": [
        { "package": "MyOrg-Base", "versionNumber": "1.2.0.LATEST" }
      ]
    },
    {
      "path": "force-app-ui",
      "package": "MyOrg-UI",
      "versionName": "Spring 2025",
      "versionNumber": "1.0.0.NEXT",
      "dependencies": [
        { "package": "MyOrg-Base", "versionNumber": "1.2.0.LATEST" },
        { "package": "MyOrg-Sales", "versionNumber": "1.1.0.LATEST" }
      ]
    }
  ],
  "packageAliases": {
    "MyOrg-Base": "0HoXXXXXXXXXXXXX",
    "MyOrg-Base@1.2.0-1": "04tXXXXXXXXXXXXX",
    "MyOrg-Sales": "0HoYYYYYYYYYYYYY",
    "MyOrg-Sales@1.1.0-1": "04tYYYYYYYYYYYYY",
    "MyOrg-UI": "0HoZZZZZZZZZZZZZ"
  }
}
```

**Why not the alternative:** Multi-repo setups require cross-repo version pinning and artifact passing between pipelines, adding significant coordination overhead. Mono-repo keeps the DAG visible in one file.

### Pattern 2: Multi-Repo with Pinned Dependencies

**When to use:** Separate teams own separate packages and release on independent cadences, or packages span different Dev Hubs (e.g., ISV + customer).

**How it works:**

Each repo has its own `sfdx-project.json` with a single `packageDirectories` entry. Dependencies reference promoted subscriber package version IDs (04t...) directly:

```json
{
  "packageDirectories": [
    {
      "path": "force-app",
      "default": true,
      "package": "TeamB-Service",
      "versionNumber": "2.0.0.NEXT",
      "dependencies": [
        { "package": "TeamA-Base@1.5.0-3", "versionNumber": "1.5.0.LATEST" }
      ]
    }
  ],
  "packageAliases": {
    "TeamA-Base@1.5.0-3": "04tAAAAAAAAAAAAAAA",
    "TeamB-Service": "0HoBBBBBBBBBBBBB"
  }
}
```

A CI/CD "orchestrator" pipeline (in the consuming repo or a dedicated ops repo) runs after upstream packages publish new versions, updating the pinned 04t IDs and triggering downstream builds.

**Why not the alternative:** In a mono-repo, independent release cadences create merge conflicts in the shared `sfdx-project.json` and force all teams to coordinate releases.

### Pattern 3: Unpackaged Metadata Alongside Packages

**When to use:** Some metadata (profiles, permission sets, org-wide settings) cannot be packaged or must be deployed org-specifically.

**How it works:**

Add an unpackaged directory to `sfdx-project.json` without a `package` key:

```json
{
  "path": "force-app-unpackaged",
  "default": false
}
```

This directory is deployed via `sf project deploy start` after all packages are installed. It is not version-controlled by the packaging system.

**Why not the alternative:** Forcing unpackageable metadata into a package causes version-create failures or installs metadata that should vary per org (e.g., org-specific profiles).

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single team, shared release cadence, < 5 packages | Mono-repo with layered directories | One sfdx-project.json is the single source of truth; simpler CI/CD |
| Multiple teams with independent release schedules | Multi-repo with pinned 04t IDs | Avoids cross-team merge conflicts and forced coordinated releases |
| Some metadata is org-specific (profiles, settings) | Unpackaged directory deployed after packages | Keeps packages portable; org-specific config stays outside packages |
| Shared custom objects used by multiple domain packages | Extract into a Base/Core package at the bottom of the DAG | Prevents duplication; all domain packages reference one source of truth |
| Package A and Package B need to reference each other's objects | Refactor shared objects into a new Base package both depend on | Circular dependencies are illegal; extract the shared surface into a lower layer |
| ISV managed package + customer customization packages | Multi-repo; customer packages depend on the managed package's 04t ID | ISV and customer have separate Dev Hubs and release cycles |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on multi-package architecture:

1. **Map the current state** — Parse `sfdx-project.json` and list all `packageDirectories`, their `dependencies`, and the `packageAliases` map. Draw the dependency DAG.
2. **Validate the DAG** — Confirm the graph is acyclic. Check that every dependency alias in `dependencies` arrays has a matching entry in `packageAliases` with a valid 04t or 0Ho ID.
3. **Compute topological order** — Determine the build and install order. Packages with no dependencies build first; packages that depend on them build next.
4. **Apply layered decomposition** — If restructuring, group metadata into Base (shared objects/fields), Domain (business logic), and Experience (UI) layers. Move metadata between `packageDirectories` paths accordingly.
5. **Configure sfdx-project.json** — Update `packageDirectories`, `dependencies`, and `packageAliases` to reflect the desired DAG. Ensure exactly one directory has `"default": true`.
6. **Build and test in order** — Run `sf package version create` for each package in topological order. Fix dependency resolution errors before proceeding to the next package.
7. **Set up CI/CD sequencing** — Configure the pipeline to build and install packages in topological order, passing 04t IDs from upstream stages to downstream stages.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Dependency DAG is acyclic — no circular references between packages
- [ ] Every dependency alias in `dependencies` arrays resolves to a valid entry in `packageAliases`
- [ ] Exactly one `packageDirectories` entry has `"default": true`
- [ ] No metadata file appears in more than one package directory (no source duplication)
- [ ] Unpackageable metadata (profiles, org settings) is in a separate unpackaged directory, not in a package
- [ ] CI/CD pipeline builds and installs packages in topological order
- [ ] Each package's Apex tests pass independently (no cross-package test dependencies)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Dependency version pinning with LATEST vs. explicit build** — Using `"versionNumber": "1.2.0.LATEST"` in a dependency resolves to the latest build of that major.minor.patch at version-create time. If an upstream team creates a new build, your next version create silently picks it up. Pin to an explicit build number in production pipelines to avoid surprise regressions.
2. **Package install order is not validated by the CLI** — `sf package install` does not check whether dependencies are already installed before attempting installation. It simply fails with a `MISSING_DEPENDENCY` error. Your pipeline must enforce topological order.
3. **Removing a component from a package requires deprecation** — Once a component (field, object, class) is in a released package version, removing it from source and creating a new version causes an error. You must deprecate the component first or use `--skip-ancestor-check` (which breaks upgrade paths).

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Dependency DAG diagram | Visual or textual representation of which packages depend on which, including install order |
| sfdx-project.json | Updated project configuration with correct packageDirectories, dependencies, and aliases |
| CI/CD pipeline config | Stage definitions showing topological build and install order |
| Package decomposition plan | Document mapping metadata types to target packages with rationale |

---

## Related Skills

- unlocked-package-development — Single unlocked package creation, versioning, and installation; use alongside this skill when building individual packages within the multi-package graph
- second-generation-managed-packages — 2GP managed package ISV workflows; relevant when the multi-package architecture includes managed packages
- scratch-org-management — Scratch org configuration for multi-package development; scratch org definitions must include dependent package features
- github-actions-for-salesforce — CI/CD pipeline implementation; use when sequencing multi-package builds in GitHub Actions
