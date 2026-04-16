---
name: managed-package-development
description: "Use when building or maintaining Salesforce first-generation managed packages (1GP) for ISV distribution — covers namespace registration, packaging org structure, PostInstall/UninstallHandler Apex interface, push upgrades, Flow version management, and subscriber org considerations. NOT for second-generation managed packages (2GP), unlocked packages, or AppExchange listing setup."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Security
triggers:
  - "How do I create a PostInstall script for a Salesforce 1GP managed package?"
  - "Can I delete a Flow from a released managed package in Salesforce 1GP?"
  - "Namespace registration for Salesforce managed package ISV distribution"
  - "Differences between packaging org and patch org for 1GP managed packages"
  - "1GP managed package push upgrade — how does it work and what are the limits?"
tags:
  - managed-package
  - 1GP
  - ISV
  - namespace
  - PostInstall
  - packaging-org
inputs:
  - "Package namespace and packaging org configuration"
  - "Components to include in the managed package (Apex classes, flows, custom objects)"
  - "PostInstall and UninstallHandler Apex class names (locked after initial upload)"
outputs:
  - "Packaging org setup guidance with namespace registration steps"
  - "PostInstall/UninstallHandler Apex interface implementation"
  - "Flow version management strategy for managed packages"
  - "Push upgrade plan with subscriber org compatibility analysis"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-16
---

# Managed Package Development

This skill activates when a practitioner needs to build or maintain a Salesforce first-generation managed package (1GP) for ISV AppExchange distribution. It covers the packaging org structure, namespace registration, the PostInstall Apex interface, the critical constraint that Flow versions in released packages cannot be deleted, and the differences between the packaging org and patch org model.

---

## Before Starting

Gather this context before working on anything in this domain:

- 1GP managed packages require a dedicated packaging org — a Developer Edition org where the package is authored and uploaded. This is a single org-per-package constraint (not per-namespace).
- The namespace is registered in a separate Developer Edition org and then linked to the packaging org Dev Hub. The namespace choice is permanent — it cannot be changed or reused after registration.
- Package upload (creating a new version) is done via Setup UI or Tooling API in the packaging org — not via `sf package version create` CLI, which is a 2GP command.
- Flows uploaded to a released or beta 1GP managed package **cannot be deleted** from the packaging org — only individual Flow versions can be removed, and only if a later version exists.
- The PostInstall/UninstallHandler Apex class name is locked after the first upload to a released managed package — the class body can change but the name cannot.

---

## Core Concepts

### Packaging Org and Namespace Structure

1GP managed packages use a dedicated packaging org model:

- **Namespace Dev Edition Org** — A Developer Edition org where the namespace identifier is registered (Setup > Company Profile > Namespace Prefix). This org becomes the namespace authority.
- **Packaging Org** — A separate Developer Edition org where all package components live. The packaging org is linked to the namespace by importing the registered namespace.
- **Patch Org** — For each released package version, a patch org can be created to develop patch releases (bug fixes only, no new features). One patch org per major.minor version.

There is no concept of "Dev Hub" or "scratch org" in 1GP — all development happens directly in the packaging org.

### PostInstall and UninstallHandler Interface

1GP managed packages can execute custom Apex logic when the package is installed, upgraded, or uninstalled in a subscriber org. This is implemented via the `InstallHandler` Apex interface:

```apex
global class MyPostInstall implements InstallHandler {
    global void onInstall(InstallContext context) {
        if (context.previousVersion() == null) {
            // Fresh install logic
        } else {
            // Upgrade logic — use context.previousVersion() to branch
        }
    }
}
```

The class implementing `InstallHandler` is registered in the Package Settings and its **API name is locked after the first upload to a released package**. Only the class body (logic) can be changed in subsequent versions.

For uninstall, implement `UninstallHandler`:
```apex
global class MyUninstall implements UninstallHandler {
    global void onUninstall(UninstallContext context) {
        // Cleanup logic
    }
}
```

### Flow Version Management in 1GP

Flows in a 1GP managed package have a critical constraint: once a Flow is uploaded to a released or beta package, **the Flow cannot be deleted from the packaging org**. You can:
- Deactivate a Flow version
- Remove individual older Flow versions (if a newer version exists)
- Create new Flow versions

But you cannot delete the Flow itself from the packaging org after it has been included in a released package. This creates a permanent registry of all Flows ever shipped in the package.

**Implication:** Be deliberate about which Flows are included in a managed package. Test Flows thoroughly before including them in a managed release.

---

## Common Patterns

### Pattern 1: PostInstall Script for Configuration Seeding

**When to use:** The package requires default Custom Metadata records, Permission Set assignments, or Named Credentials to be created in the subscriber org at install time.

**How it works:**
1. Implement `InstallHandler` in a global Apex class
2. In `onInstall()`, check `context.previousVersion()` to distinguish fresh install from upgrade
3. For fresh install: insert default data records, assign permission sets to installing user
4. For upgrades: use version comparison to apply migration logic only for specific upgrade paths
5. Register the class name in Package Settings > Post Install Class before the first released upload

**Why not use Setup steps in subscriber org:** PostInstall scripts run automatically at install time, reducing subscriber configuration burden. For ISV packages, automated post-install configuration is a quality-of-life feature that reduces support requests.

### Pattern 2: Push Upgrade for Bug Fixes

**When to use:** A critical bug in a released package version needs to be fixed in all subscriber orgs without requiring subscribers to manually install the update.

**How it works:**
1. Create a new package version with the fix in the packaging org
2. Upload the version via Setup > Package Manager > Upload
3. Navigate to Package Details > Push Upgrades and schedule the push
4. Push upgrades are subject to subscriber org governor limits — the PostInstall script runs in the subscriber org and must stay within limits

**Why not wait for subscriber voluntary install:** Push upgrades ensure all subscribers receive critical security or data integrity fixes promptly. Voluntary upgrade adoption rates are often low.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New ISV managed package for AppExchange | 1GP packaging org with namespace | AppExchange requires managed package with IP protection |
| New internal modular package, no AppExchange | 2GP unlocked package | 2GP supports CLI-driven workflow and multi-package namespaces |
| Post-install configuration needed | InstallHandler Apex interface | Runs automatically at install/upgrade time in subscriber org |
| Bug fix across all subscribers | Push upgrade from Package Manager | Subscriber voluntary installs have low adoption rates |
| Flow in package needs to be deleted | Not possible after release upload | Can only deactivate/version — plan Flows before releasing |
| Package upload | Setup UI > Package Manager or Tooling API | 2GP CLI (`sf package version create`) does NOT work for 1GP |

---

## Recommended Workflow

1. **Register namespace** — In a dedicated Developer Edition org, register the namespace prefix (Setup > Company Profile > Namespace Prefix). Document the namespace — it is permanent.
2. **Configure packaging org** — Import the namespace into the packaging org by linking it in Setup > Package Manager. Create the package in the packaging org.
3. **Develop in packaging org** — Build all components (Apex, Flows, custom objects, layouts) directly in the packaging org. Test in the packaging org itself or a scratch org linked to it.
4. **Implement PostInstall/UninstallHandler** — Write the InstallHandler Apex class and register it in Package Settings before the first released upload. Confirm the class name — it cannot change after the first released upload.
5. **Test Flows before including in package** — Flows included in a released package cannot be deleted from the packaging org. Test all Flows thoroughly in a separate org before adding them to a managed release.
6. **Upload new package version** — Use Setup > Package Manager > Upload in the packaging org. Set the version number and release type (Beta or Released).
7. **Plan push upgrades** — For Released versions with bug fixes, schedule push upgrades via Package Details > Push Upgrades. Monitor upgrade status across subscriber orgs.

---

## Review Checklist

- [ ] Namespace registered in a dedicated Dev Edition org — name is permanent
- [ ] Packaging org configured with namespace linked
- [ ] PostInstall class name finalized before first released upload
- [ ] Flows tested thoroughly before inclusion in any managed release
- [ ] Package upload via Setup UI or Tooling API — not `sf package version create` CLI
- [ ] PostInstall script tested in sandbox with `Test.testInstall()` Apex testing method
- [ ] Push upgrade plan documented with subscriber org impact analysis

---

## Salesforce-Specific Gotchas

1. **PostInstall class name is locked after first released upload** — The API name of the class implementing InstallHandler is registered in Package Settings. After the first Released package version is uploaded with this class, the name cannot be changed — only the body. Plan the class name before the first release.
2. **Flows in released packages cannot be deleted from the packaging org** — Once a Flow is included in a Released or Beta managed package, it cannot be deleted from the packaging org. Only individual older versions can be removed (if a newer version exists). Be deliberate about which Flows are included in managed releases.
3. **`sf package version create` CLI is a 2GP command, not valid for 1GP** — First-generation managed packages are uploaded via Setup UI (Setup > Package Manager > Upload) or Tooling API. The `sf package version create` command in the Salesforce CLI only works with second-generation (2GP) packages.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Packaging org setup guide | Namespace registration steps and packaging org configuration |
| PostInstall class implementation | InstallHandler and UninstallHandler Apex with install/upgrade branching |
| Flow management policy | Which Flows are included in managed releases and version management strategy |
| Push upgrade plan | Version selection, subscriber org impact, and rollout schedule |

---

## Related Skills

- `devops/second-generation-managed-packages` — For 2GP managed packages with CLI-driven workflow
- `devops/package-development-strategy` — For selecting the right package type (1GP vs 2GP vs unlocked)
- `devops/cpq-deployment-patterns` — For deploying CPQ configuration alongside managed packages
