---
name: unlocked-package-development
description: "Use this skill when designing, creating, versioning, or installing unlocked packages: package directory configuration in sfdx-project.json, namespace management, package dependencies, version lifecycle (beta vs. released), ancestor versions, installation keys, and subscriber installation via sf CLI or Package Install UI. NOT for 2GP managed packages (ISV packaging with namespaces, push upgrades, or AppExchange listings), 1GP managed packages, change set deployments, or scratch org setup."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Scalability
triggers:
  - "how do I create an unlocked package and publish a new version with sf CLI"
  - "my package version create is failing with a dependency or coverage error"
  - "how do I install an unlocked package in a sandbox or production org"
  - "should I use a namespaced or namespace-less unlocked package for this project"
  - "how do I set up package dependencies between two unlocked packages in sfdx-project.json"
  - "I need to promote a package version from beta to released before deploying to production"
  - "what is the ancestor version field and do I need it for my package versioning strategy"
tags:
  - unlocked-packages
  - package-development
  - second-generation-packaging
  - sfdx
  - dev-hub
  - devops
inputs:
  - "Dev Hub org alias or username (Dev Hub must have Unlocked Packages and Second-Generation Packaging enabled)"
  - "Package name, namespace preference (namespaced or namespace-less), and target installation org edition"
  - "sfdx-project.json with packageDirectories already partially configured, if updating an existing project"
  - "List of external package dependencies (packageAliases with subscriber package version IDs — 04t...)"
  - "Code coverage requirement awareness (75% minimum to promote a version to Released)"
  - "Installation key preference (password-protected vs. no key)"
  - "Target subscriber orgs and whether they are sandbox or production"
outputs:
  - "Compliant sfdx-project.json with packageDirectories, packageAliases, and namespace configuration"
  - "sf CLI commands for package create, version create, version promote, and package install"
  - "Package version ID (04t...) and package ID (0Ho...) for deployment pipeline references"
  - "Diagnosis and remediation steps for version create failures, dependency conflicts, and install errors"
  - "Decision guidance on namespace strategy, ancestor versioning, and installation key usage"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Unlocked Package Development

This skill activates when you are designing or maintaining an unlocked package project: creating the package in a Dev Hub, defining package directories in `sfdx-project.json`, managing inter-package dependencies, creating and promoting package versions, and installing packages in subscriber orgs. It covers the full lifecycle from initial `sf package create` through subscriber installation — excluding 2GP managed packages (AppExchange ISV packaging) and 1GP managed packages.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Is Dev Hub enabled with Unlocked Packages and Second-Generation Packaging?** Both settings must be ON in Dev Hub Setup > Dev Hub. Without them, `sf package create` returns a permissions error. This is the most common blocker for teams new to unlocked packages.
- **Does this project need a namespace?** Namespace-less unlocked packages (the default) are simpler: no namespace registration, no namespace prefix on API names, and easier inter-package dependency management. Namespaced unlocked packages require a registered namespace linked to the Dev Hub. **The choice is permanent — a namespace-less package cannot be converted to a namespaced package after creation.**
- **What are the dependency chains?** All dependent packages must be installed in the target org before the dependent package version can be created or installed. Circular dependencies are not allowed. Map the dependency graph before creating any package.
- **Is code coverage at 75% or above across all Apex in the package directory?** Coverage is checked at version promotion time (`sf package version promote`). Low coverage blocks promotion but does not block beta version creation.
- **What is the target subscriber org type?** Unlocked packages can be installed in scratch orgs, sandboxes, and production orgs. Production installs require a Released version (not beta). Sandboxes accept both.

---

## Core Concepts

### 1. Package Identity: 0Ho vs. 04t IDs

Every unlocked package has two distinct ID types:

- **Package ID (`0Ho...`)** — Created once when you run `sf package create`. Identifies the package container in the Dev Hub. This ID goes into `sfdx-project.json` under `packageAliases`.
- **Package Version ID (`04t...`)** — Created each time you run `sf package version create`. Identifies a specific immutable snapshot of the package. This ID is what you install with `sf package install`.

The package ID never changes. Version IDs are created per version and are immutable after creation. When referencing a package in a dependency list or install command, always use the `04t...` subscriber package version ID, not the `0Ho...` package ID.

### 2. sfdx-project.json — The Package Manifest

All package configuration lives in `sfdx-project.json`. The `packageDirectories` array defines which directories contain package source, and `packageAliases` maps human-readable names to Salesforce-assigned IDs.

**Minimal valid package project:**

```json
{
  "packageDirectories": [
    {
      "path": "force-app",
      "default": true,
      "package": "MyUnlockedPackage",
      "versionName": "Spring 2025",
      "versionNumber": "1.0.0.NEXT",
      "dependencies": []
    }
  ],
  "namespace": "",
  "sfdcLoginUrl": "https://login.salesforce.com",
  "sourceApiVersion": "63.0",
  "packageAliases": {
    "MyUnlockedPackage": "0Ho..."
  }
}
```

Key fields in `packageDirectories`:

| Field | Required | Notes |
|---|---|---|
| `path` | Yes | Relative path to the package source directory |
| `package` | Yes | Human-readable package name; must match a key in `packageAliases` |
| `versionNumber` | Yes | Semantic version in `major.minor.patch.build` format; use `NEXT` for auto-increment |
| `versionName` | No | Display name for this version |
| `dependencies` | No | Array of `{ "package": "<alias>", "versionNumber": "..." }` objects |
| `ancestorId` | No | Package version ID (`04t...`) of the version this version descends from |
| `definitionFile` | No | Path to scratch org definition file used during version creation |

### 3. Package Version Lifecycle: Beta vs. Released

Every version created with `sf package version create` starts as **beta**. Beta versions:
- Can be installed in scratch orgs and sandboxes
- Cannot be installed in production orgs
- Are mutable in the sense that new builds can use the same version number with `NEXT` auto-increment

**Promotion to Released** (`sf package version promote`) is a one-way, irreversible operation that:
- Enables installation in production orgs
- Requires Apex code coverage >= 75% across all classes in the package directory
- Locks the version — it cannot be modified after promotion

Released versions can be installed in any org type. Plan promotion as a deliberate gate before production deployments.

### 4. Package Dependencies

If Package B depends on Package A, the dependency must be declared in Package B's `packageDirectories` entry and Package A must already be installed in the org where Package B is being created or tested.

Dependencies are specified by alias and minimum version number in `sfdx-project.json`:

```json
"dependencies": [
  {
    "package": "SharedComponents",
    "versionNumber": "2.3.0.LATEST"
  }
]
```

The alias (`SharedComponents`) must resolve to a subscriber package version ID (`04t...`) in `packageAliases`. Use `LATEST` in the version number to resolve to the latest released version of a dependency, or pin to an exact version for reproducible builds.

**During `sf package version create`**, Salesforce validates that all declared dependencies are installed in the scratch org or build org used for version creation. Missing dependencies cause a `PACKAGE2_VERSION_CREATE_DEPENDENCY_UNRESOLVED` error.

### 5. Namespace Configuration

The `namespace` field in `sfdx-project.json` is set once per project:

- **Empty string (`""`)** — Namespace-less package. No prefix on any API name. Components can have the same API names as components in other packages (potential conflict risk in subscriber orgs). Simpler development workflow; recommended for internal enterprise packages.
- **Registered namespace string (e.g., `"acme"`)** — All components get the `acme__` prefix. Namespace must be registered and linked to the Dev Hub org via Setup. Required if you plan to distribute the package publicly or need namespace isolation.

The namespace declaration in `sfdx-project.json` must match the namespace registered in the Dev Hub. A mismatch causes package creation to fail.

---

## Common Patterns

### Mode 1 — Create a Package and Publish a First Version

**When to use:** Greenfield package project, or setting up an existing repo to use unlocked packages for the first time.

```bash
# Step 1: Create the package in Dev Hub (run once per package)
sf package create \
  --name "MyUnlockedPackage" \
  --package-type Unlocked \
  --path force-app \
  --target-dev-hub MyDevHub

# This outputs a Package ID (0Ho...) — copy it into sfdx-project.json packageAliases

# Step 2: Create a scratch org for development
sf org create scratch \
  --definition-file config/project-scratch-def.json \
  --alias pkg-dev --duration-days 7 \
  --target-dev-hub MyDevHub

# Step 3: Push source to scratch org (iterative development)
sf project deploy start --target-org pkg-dev

# Step 4: Create a beta package version
sf package version create \
  --package MyUnlockedPackage \
  --installation-key-bypass \
  --wait 10 \
  --target-dev-hub MyDevHub

# This outputs a Package Version ID (04t...) — copy into packageAliases as a versioned alias

# Step 5: Install beta version in a sandbox for QA
sf package install \
  --package 04t... \
  --target-org QASandbox \
  --wait 10

# Step 6: Promote to Released before production install
sf package version promote \
  --package 04t... \
  --target-dev-hub MyDevHub
```

### Mode 2 — Review and Audit Package Version Coverage and Status

**When to use:** Pre-promotion gate check, CI pipeline validation, or troubleshooting a version that is failing to promote due to coverage or dependency issues.

```bash
# List all versions of a package
sf package version list \
  --package MyUnlockedPackage \
  --target-dev-hub MyDevHub \
  --verbose

# Get detailed info about a specific version
sf package version report \
  --package 04t... \
  --target-dev-hub MyDevHub

# Check code coverage for a version
sf package version report \
  --package 04t... \
  --target-dev-hub MyDevHub \
  --json | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['result']['CodeCoverage'])"

# List all packages registered to the Dev Hub
sf package list --target-dev-hub MyDevHub
```

Coverage is reported per class in the version report output. Classes below 75% are listed individually, helping identify exactly which Apex needs more tests before promotion is possible.

### Mode 3 — Troubleshoot Installation and Dependency Failures

**When to use:** `sf package install` fails, or version create reports unresolved dependencies.

**Common install error: `PACKAGE_UNAVAILABLE`**

The package version does not exist in the target org's region, or the version ID is a beta being installed into production. Verify the version is Released before installing to production.

**Common error: `DUPLICATE_COMPONENT`**

A component with the same API name already exists in the target org (from a deployment or another package). Unlocked packages do not automatically take ownership of pre-existing components. Resolution options:
1. Remove the conflicting component from the org before installing.
2. Restructure the package to avoid the conflicting component name.

**Common error: dependency not installed**

```bash
# Check what packages are installed in the target org
sf package installed list --target-org TargetOrg

# Install missing dependency first
sf package install --package 04t_DEPENDENCY_VERSION_ID --target-org TargetOrg --wait 10

# Then retry the main package install
sf package install --package 04t_MAIN_PACKAGE_ID --target-org TargetOrg --wait 10
```

**Common error during version create: `PACKAGE2_VERSION_CREATE_DEPENDENCY_UNRESOLVED`**

Declare dependencies in `sfdx-project.json` and ensure they are installed in the scratch org used for version creation. The scratch org definition file (`definitionFile` in the package directory) can reference a snapshot of installed packages.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Internal enterprise app, single team | Namespace-less unlocked package | Simpler API names, no namespace registration overhead |
| Sharing package across teams or orgs | Namespace-less with installation key | Key restricts install to authorized teams without full namespace setup |
| ISV or AppExchange distribution | Use 2GP managed package (outside this skill's scope) | Managed packages support push upgrades, namespace locking, and subscriber org protection |
| Multiple interdependent packages | Map dependency order first; create and version in dependency order | Installing out of order causes DEPENDENCY_UNRESOLVED errors at both version create and install time |
| CI pipeline version creation | Pin dependency versions to `LATEST` or an exact `04t...` | Avoids non-deterministic resolution failures when upstream packages change |
| Production deployment | Promote version before pipeline reaches prod | Beta versions are blocked from production installs by the platform |
| Need to roll back an installed package | Uninstall and reinstall prior version | Unlocked package components can be deleted on uninstall; verify subscriber org impact before rolling back |
| Code coverage blocking promotion | Run `sf apex run test` in the version creation org and address failing or uncovered classes | Coverage must reach 75% across all Apex in the package directory, not org-wide |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] `sf package create` was run once and the `0Ho...` package ID is saved in `packageAliases` in `sfdx-project.json`
- [ ] All package directories have `package`, `versionNumber`, and `path` fields set correctly
- [ ] All inter-package dependencies are declared in `dependencies` arrays and resolve to valid `04t...` IDs in `packageAliases`
- [ ] Namespace decision is locked in and matches Dev Hub configuration (cannot change after package creation)
- [ ] Code coverage >= 75% for all Apex classes in the package directory before attempting promotion
- [ ] Version promoted to Released (`sf package version promote`) before any production org install
- [ ] Installation key decision is documented — if using a key, it is stored in secrets management, not in `sfdx-project.json` plaintext
- [ ] `sf package installed list` confirms all dependencies are present in every target subscriber org before attempting install
- [ ] Ancestor version (`ancestorId`) is set if the versioning strategy requires a linear promotion history

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Namespace-less packages are permanent** — Once a package is created without a namespace (empty `namespace` field), it cannot be converted to a namespaced package. If the team later wants namespace isolation, a new package must be created and all subscribers must reinstall.

2. **Package version ancestry must be linear — branching version numbers is not supported** — The `ancestorId` field enforces a single linear version chain. You cannot create version 2.0 branching from both 1.0 and 1.5. If your team runs parallel feature branches that need separate package versions, you must manage this through scratch org isolation, not separate version lineages.

3. **Deleting an unlocked package uninstalls and destroys its components in subscriber orgs** — Unlike change sets or Metadata API deployments, unlocked package components are owned by the package. Uninstalling an unlocked package removes its components from the subscriber org (unless `--no-prompt` is used and the org has dependent components, in which case it fails). Subscribers must be warned before an uninstall.

4. **Beta versions cannot be installed in production — not even with overrides** — The platform enforces this at install time. There is no flag or permission that bypasses it. Teams that run `sf package install` in a CI deploy step targeting production must always promote first.

5. **Code coverage is evaluated at version create time using the scratch org, not the subscriber org** — Coverage is measured against the Apex in the package directory during `sf package version create`. If your scratch org definition file does not load the same test data or settings as production, coverage numbers may differ. A version can pass promotion threshold in scratch org but the same tests may have different coverage behavior in a real org.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `sfdx-project.json` | Package manifest with `packageDirectories`, `packageAliases`, `namespace`, and dependency configuration |
| Package ID (`0Ho...`) | Permanent identifier for the package container in Dev Hub; stored in `packageAliases` |
| Package Version ID (`04t...`) | Immutable snapshot ID for a specific build; used in `sf package install` and CI pipeline references |
| `sf package version list` output | Audit view of all versions: version numbers, status (beta/released), created date, code coverage |
| Install command | `sf package install --package 04t... --target-org <org> --wait 10` with optional `--installation-key` |

---

## Related Skills

- `scratch-org-management` — Managing scratch org definitions and allocation limits; needed as the build environment for package version creation
- `sf-cli-and-sfdx-essentials` — First-time SF CLI setup, Dev Hub enablement, and basic source push/pull; prerequisite to this skill
- `change-set-deployment` — Alternative metadata deployment mechanism; use this skill when unlocked packages are not appropriate (e.g., sandboxes without Dev Hub access)
- `cicd-pipeline-setup` — Full CI/CD pipeline configuration including package version create and promote steps as pipeline gates
