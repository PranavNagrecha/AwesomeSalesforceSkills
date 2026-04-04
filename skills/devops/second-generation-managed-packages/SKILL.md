---
name: second-generation-managed-packages
description: "2GP managed package development: creating managed packages with Dev Hub and Salesforce CLI, semantic versioning, patch versions, namespace linking, ISV AppExchange listing, and subscriber upgrade management. NOT for unlocked packages, unmanaged packages, or 1GP-only workflows."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - Reliability
triggers:
  - "I need to create a second-generation managed package for AppExchange distribution"
  - "How do I set up a Dev Hub org to build and version a 2GP managed package?"
  - "My package version won't promote — I'm getting a code coverage error"
  - "How do patch versions work in 2GP compared to 1GP patch orgs?"
  - "I want to share a namespace across multiple managed packages using @namespaceAccessible"
  - "How do I pin package dependency versions in sfdx-project.json?"
tags:
  - 2gp
  - managed-package
  - isv
  - appexchange
  - package-versioning
  - dev-hub
inputs:
  - Dev Hub org (Partner Business Org preferred) with Second-Generation Managed Packaging enabled
  - Namespace registered in a Developer Edition org and linked to the Dev Hub
  - Salesforce CLI installed and authenticated to the Dev Hub
  - sfdx-project.json with packageDirectories, namespace, and packageAliases configured
  - Apex test coverage at or above the required threshold (75% for production-ready versions)
outputs:
  - 2GP managed package and package version registered in the Dev Hub
  - Promoted (managed-released) package version installable by subscriber orgs
  - Patch version addressing bug fixes on a released minor version without a new minor release
  - Guidance on dependency declaration and upgrade path planning
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Second-Generation Managed Packages (2GP)

This skill activates when a practitioner needs to build, version, promote, or troubleshoot a second-generation managed package (2GP) for ISV distribution via AppExchange. It covers the full Dev Hub-centric workflow: namespace setup, package creation, version builds, patch releases, code coverage gating, and subscriber upgrade management.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Dev Hub org type**: All Salesforce ISV and OEM partners should designate their Partner Business Org (PBO) as their Dev Hub. Developer Edition orgs work but carry stricter daily scratch org and package version limits (six per day, three active scratch orgs maximum). A Dev Hub org cannot be disabled once enabled, and all packages are permanently associated with the Dev Hub org that created them.
- **Namespace linkage**: The namespace must be registered in a separate Developer Edition org, then linked to the Dev Hub via the Namespace Registries app. This association is permanent — namespaces cannot be transferred or reused.
- **"Enable Second-Generation Managed Packages" is a one-way switch**: Once enabled alongside "Enable Unlocked Packages and Second-Generation Managed Packages," it cannot be turned off. Enable only in the org intended for long-term production use.
- **Code coverage gate**: To promote a package version to the managed-released state, the `--code-coverage` flag must have been included during `sf package version create`, and Apex coverage must meet the platform threshold (75%). Failing to include this flag during version creation means the version can never be promoted.
- **Association is permanent**: A package is permanently associated with the Dev Hub org that created it. It cannot be transferred to another Dev Hub.

---

## Core Concepts

### Dev Hub as Control Plane

In 2GP, the Dev Hub org is the single control plane for all managed packages, scratch orgs, and namespaces. Unlike 1GP, which required a dedicated packaging org per package and per patch version, 2GP eliminates these separate orgs. All `sf package` commands target the Dev Hub (via `--target-dev-hub`). Scratch orgs are ephemeral development environments created from the Dev Hub and are used for active development and CI — they are not packaging orgs.

The source of truth is version control, not an org. Package metadata lives in the Salesforce DX project directory and is committed to a VCS. `sf package version create` reads source from that project structure to produce a versioned artifact registered in the Dev Hub.

### Semantic Versioning and Flexible Ancestors

2GP package versions follow a `major.minor.patch.build` numbering scheme, declared in `sfdx-project.json` under `versionNumber`. The `.NEXT` token increments the build number automatically on each version create run.

Unlike 1GP's strictly linear versioning, 2GP supports **flexible versioning**: if a managed-released version has not yet been distributed to any subscriber, it can be abandoned and a prior version selected as the ancestor for the next release. This is declared via `ancestorVersion` in `sfdx-project.json`. Once a version is installed by at least one subscriber, it is locked into the ancestor chain and cannot be abandoned.

Patch versions are created by specifying a non-zero patch number (e.g., `1.2.1`). A patch version branches off an existing major.minor and allows bug fixes to be released without incrementing the minor version. In 2GP, creating a patch version requires no separate patch org — it uses the same CLI command with the appropriate version number.

### Namespace Sharing and @namespaceAccessible

In 1GP, each managed package required a unique namespace, forcing ISVs to proliferate namespaces across their portfolio. 2GP allows multiple managed packages to share the same namespace. The `@namespaceAccessible` Apex annotation exposes public Apex classes and methods across packages within the same namespace, enabling modular ISV architectures without cross-namespace API surface exposure.

### Dependencies and sfdx-project.json

Inter-package dependencies are declared declaratively in `sfdx-project.json` under the `packageDirectories` entry using a `dependencies` array. Each dependency references a package alias (mapped to a version ID in `packageAliases`). This replaces the manual tracking and org-based dependency management required in 1GP. Dependencies can include other 2GP packages (managed or unlocked) or 1GP managed packages.

```json
{
  "packageDirectories": [
    {
      "path": "force-app",
      "package": "MyManagedApp",
      "versionName": "Spring Release",
      "versionNumber": "2.1.0.NEXT",
      "default": true,
      "dependencies": [
        {
          "package": "MySharedLibrary",
          "versionNumber": "1.3.0.LATEST"
        }
      ]
    }
  ],
  "namespace": "myns",
  "packageAliases": {
    "MyManagedApp": "0Ho...",
    "MySharedLibrary@1.3.0-1": "04t..."
  }
}
```

---

## Common Patterns

### Pattern 1: New 2GP Managed Package From Scratch

**When to use:** Starting a new ISV application with no existing 1GP package.

**How it works:**

1. Enable Dev Hub and Second-Generation Managed Packages in the PBO.
2. Register a namespace in a Developer Edition org. Link it to the Dev Hub via Namespace Registries > Link Namespace.
3. Authenticate the CLI to the Dev Hub: `sf org login web --alias devhub --set-default-dev-hub`.
4. Create the package: `sf package create --name "My App" --package-type Managed --path force-app --target-dev-hub devhub`.
   This registers the package in the Dev Hub and adds its 0Ho ID to `sfdx-project.json` under `packageAliases`.
5. Develop metadata in a scratch org: `sf org create scratch --definition-file config/project-scratch-def.json --target-dev-hub devhub --alias devorg`.
6. Push source and develop: `sf project deploy start --target-org devorg`.
7. When ready to version: `sf package version create --package "My App" --target-dev-hub devhub --code-coverage --wait 20`.
8. Test the beta version in a scratch org: `sf package install --package 04t... --target-org devorg`.
9. Promote to released: `sf package version promote --package 04t... --target-dev-hub devhub`.

**Why not the alternative:** 1GP requires a dedicated packaging org per package and cannot be automated end-to-end through the CLI. 2GP integrates into CI/CD pipelines and eliminates org credential management overhead.

### Pattern 2: Patch Version for a Released Minor

**When to use:** A bug is found in a shipped minor version (e.g., `2.1.0`) and must be fixed without releasing a new minor (`2.2.0`) that would require re-qualifying the AppExchange listing.

**How it works:**

1. Update `versionNumber` in `sfdx-project.json` to `2.1.1.NEXT` and set `ancestorVersion` to `2.1.0`.
2. Apply only the bug fix to the source.
3. Run: `sf package version create --package "My App" --target-dev-hub devhub --code-coverage --wait 20`.
4. Test in a scratch org, then promote: `sf package version promote --package 04t... --target-dev-hub devhub`.
5. Subscribers on `2.1.0` can upgrade to `2.1.1` directly.

**Why not the alternative:** Creating a new minor version (`2.2.0`) for a patch fix inflates the version history, may require AppExchange re-review, and forces subscribers onto a larger change than necessary.

### Pattern 3: CI/CD Pipeline Integration

**When to use:** Automating package version builds for every merge to the main branch in a release pipeline.

**How it works:**

In the CI job:
```bash
# Authenticate using JWT (no interactive login)
sf org login jwt \
  --client-id $SF_CONSUMER_KEY \
  --jwt-key-file server.key \
  --username $SF_DEV_HUB_USER \
  --set-default-dev-hub

# Create version with code coverage, write result ID to file
sf package version create \
  --package "My App" \
  --target-dev-hub $SF_DEV_HUB_USER \
  --code-coverage \
  --wait 30 \
  --json > version-result.json

# Optionally promote if on a release branch
PACKAGE_VERSION_ID=$(jq -r '.result.subscriberPackageVersionId' version-result.json)
sf package version promote --package $PACKAGE_VERSION_ID --target-dev-hub $SF_DEV_HUB_USER
```

**Why not the alternative:** Manually creating versions is error-prone and does not catch regressions early. Automated promotion gating on coverage failures prevents non-promotable versions from reaching subscribers.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New ISV app, no prior 1GP investment | Start with 2GP from day one | Avoids future migration cost; full CLI/API automation available |
| Bug fix on released version with active subscribers | Create a patch version (e.g., `2.1.1`) | Minimizes subscriber disruption; no minor version inflation |
| Multiple ISV modules sharing the same namespace | Use `@namespaceAccessible` Apex across 2GP packages | Allows modular architecture without cross-namespace surface leakage |
| Inter-package dependency | Declare in `sfdx-project.json` `dependencies` array | Declarative and VCS-traceable; eliminates manual org-based tracking |
| AppExchange submission | Promote version, then submit for security review from ISVforce partner portal | Promotion gates code coverage; security review gates listing readiness |
| Dev Hub org considerations | Use Partner Business Org (PBO) as Dev Hub | Avoids package loss on org expiry; higher scratch org and version limits |
| Migrating from 1GP | Use `sf package convert` + subscriber migration workflow | Converts 1GP metadata to 2GP version; subscriber migration preserves data |

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

- [ ] Dev Hub has "Enable Unlocked Packages and Second-Generation Managed Packages" turned on
- [ ] Namespace is registered in a Developer Edition org and linked to the Dev Hub Namespace Registry
- [ ] `sfdx-project.json` includes `namespace`, correct `packageDirectories`, and `packageAliases` with the 0Ho package ID
- [ ] `sf package version create` was run with `--code-coverage` flag (required for eventual promotion)
- [ ] Apex test coverage meets the 75% threshold across all classes in the package
- [ ] Package version has been tested in a scratch org before promotion
- [ ] `sf package version promote` issued with the correct 04t subscriber package version ID
- [ ] Dependencies are pinned to specific version IDs in `packageAliases`, not floating aliases
- [ ] AppExchange security review initiated from the ISVforce partner portal before public listing

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Omitting `--code-coverage` makes a version unpromotable** — If `sf package version create` is run without the `--code-coverage` flag, the resulting beta version can never be promoted to managed-released, even if coverage is 100%. The flag must be present at version creation time. A new version must be built with the flag to correct this.

2. **Dev Hub org association is permanent** — Once a package is created against a Dev Hub org, that association cannot be changed or transferred. If a Developer Edition org used as a Dev Hub expires due to inactivity, all packages associated with it become orphaned: installed packages cannot receive updates and new installs may fail. ISVs must use their Partner Business Org as the Dev Hub.

3. **Subscriber orgs cannot see Apex source** — Apex class, trigger, and Visualforce component source inside a managed 2GP package is obfuscated in subscriber orgs. Partners can view unobfuscated code only when logged in via the Subscriber Support Console. Attempting to reference or inspect source from a subscriber context fails silently — plan support and troubleshooting workflows around this constraint.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `sfdx-project.json` | Project configuration file containing package definitions, version numbers, namespace, and dependency aliases |
| Package (0Ho ID) | The managed package container registered in the Dev Hub, referenced by all package versions |
| Package version (04t ID) | A specific beta or promoted (managed-released) package version installable in subscriber orgs |
| Scratch org definition file | `config/project-scratch-def.json` defining features and settings required for development and testing |
| Patch version (04t ID) | A promoted patch release branching from an existing minor version for targeted bug fixes |

---

## Related Skills

- `unlocked-package-development` — For team-based, non-ISV modular deployments; unlocked packages do not support IP protection or AppExchange listing via the managed package route
- `change-set-deployment` — Legacy metadata deployment; relevant only when 2GP is not yet adopted or for metadata types not supported in 2GP
- `security-health-check` — Run before initiating AppExchange security review to catch common issues early
