---
name: package-development-strategy
description: "Deciding between Salesforce package development approaches — unmanaged, unlocked, 1GP managed, 2GP managed — namespace selection, ISV distribution requirements, upgrade path design, AppExchange packaging strategy. Trigger keywords: should I use managed or unlocked package, Salesforce package type selection, 2GP vs 1GP managed package, namespace decision Salesforce, ISV AppExchange packaging, unlocked package strategy. NOT for creating and versioning an unlocked package — use devops/unlocked-package-development. NOT for 2GP build, patch and AppExchange steps — use devops/second-generation-managed-packages."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "should I use an unlocked package or a managed package for my Salesforce project"
  - "what is the difference between 1GP and 2GP managed packages in Salesforce"
  - "can I change my Salesforce package namespace after registering it"
  - "which Salesforce package type can be listed on AppExchange as an ISV product"
  - "how do I choose a package strategy for modularizing a large internal Salesforce org"
  - "is 2GP or 1GP managed package recommended for new ISV development on Salesforce"
  - "unlocked packages isn't working"
  - "we're having issues with unlocked packages"
  - "choose a package type and namespace before we start building"
  - "split our org metadata into unlocked packages"
tags:
  - packaging
  - unlocked-packages
  - managed-packages
  - isv
  - appexchange
  - namespace
  - 2gp
inputs:
  - "Distribution intent: internal use, AppExchange distribution, or ISV product"
  - "IP protection requirement: yes or no"
  - "Upgrade path requirement: yes (must support org upgrades) or no"
  - "Current Dev Hub and namespace availability"
outputs:
  - "Package type recommendation with rationale"
  - "Namespace decision guidance"
  - "AppExchange eligibility summary per package type"
  - "Upgrade path implications for the selected approach"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# Package Development Strategy

Use this skill when making the foundational decision about which Salesforce package type to use for a project, and especially the namespace decision, which can't be undone. It covers unmanaged, unlocked, 1GP managed, and 2GP managed package types, from internal use to ISV AppExchange distribution.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is this for **internal use** (within one customer org), **multi-org internal distribution**, or **AppExchange ISV distribution**?
- Is **IP protection** required? In a managed package, Apex class, trigger, and Visualforce component code is obfuscated in the installing org, except global method signatures (2GP Developer Guide). Unlocked package metadata can be modified in a production org.
- Is an **upgrade path** required? Unmanaged packages have no upgrade mechanism. UNVERIFIED (2026-10-03): the unmanaged package behavior is documented in Salesforce Help, not in the 262 packaging PDFs.
- Does the project need a **namespace**? Managed packages require one. Unlocked packages can be created with `--no-namespace`. A package's namespace can't be changed or added after the package is created.
- Is there a Dev Hub? Unlocked and managed 2GP packages are owned by a Dev Hub. A managed 1GP package is owned by its packaging org.

---

## Questions to Ask Before Configuring

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| Will this ever be listed on AppExchange or sold to other companies? | The Salesforce DX guide says AppExchange partners should use managed 2GP; unlocked packages are "the right package type for most use cases" only when you don't plan AppExchange distribution. | Rules package types in or out on day one. | No rebuild from unlocked to managed later, with new namespaced API names. |
| Do subscribers need to be blocked from reading or changing the code? | Managed package Apex is obfuscated except global signatures; unlocked package metadata can be changed directly in production. | Decides managed vs unlocked on a real requirement. | Governance matches the package type (who may edit packaged metadata in production). |
| Which namespace string, registered in which namespace org, linked to which Dev Hub? | After a namespace is associated with an org it can't be changed or reused, and after a package is created its namespace and Dev Hub can't be changed. | One deliberate, brand-stable namespace. | Package transfer stays possible later (a package with its own namespace can be transferred with that namespace). |
| Do the planned packages depend on each other or on unpackaged org metadata? | Org-dependent unlocked packages validate dependencies at install time, install only into orgs that contain the metadata, and can't depend on other packages. | A dependency graph that the chosen package variant supports. | Package versions install in a predictable order with explicit `dependencies`. |
| Who may delete package versions, and what pins a `04t` version? | Released unlocked versions can be deleted and deletion is permanent; installs of a deleted version fail. Released managed 2GP versions can't be deleted. | A retention rule per package type. | Pipelines never break because a pinned version vanished. |
| Is a patch path needed for managed 2GP? | Patch versioning must be enabled by Partner Support and is available only to packages that passed security review. | Starts the enablement early. | A hotfix path exists before the first customer escalation. |

---

## Core Concepts

### The Four Package Types on the Control vs. Mutability Spectrum

| Package Type | Upgrade Path | IP Protection | AppExchange | Namespace | Source-Driven |
|---|---|---|---|---|---|
| Unmanaged | No (UNVERIFIED (2026-10-03), Help only) | No | No | No | No |
| Unlocked | Yes | No | Not the intended channel | Optional (`--no-namespace`) | Yes |
| 1GP Managed | Yes | Yes | Yes | Yes, one package per namespace | No (packaging org is the source of truth) |
| 2GP Managed | Yes | Yes | Yes | Yes, many packages per namespace | Yes (version control is the source of truth) |

**Unmanaged packages** are a one-time install with no upgrade path. Installed components can be freely modified by the subscriber org. Use only for code samples, templates, or when a subscriber org intentionally takes ownership of the code.

**Unlocked packages** support source-driven development, versioned releases, and upgrades. "Metadata in unlocked packages can be modified in a production org" (Salesforce DX Developer Guide), so they suit internal business apps and large-org decomposition, not protected commercial products.

**1GP managed packages** provide IP protection and AppExchange distribution. The packaging org owns the package and holds its metadata. Some 1GP operations, such as package create and uninstall, can't be automated, and patches need patch orgs.

**2GP managed packages** are the Salesforce recommendation for ISVs listing on AppExchange. The Dev Hub owns the package, version control is the source of truth, every operation runs through Salesforce CLI, and multiple packages can share one namespace with `@namespaceAccessible` for public Apex.

### The Namespace Constraint

Namespace mistakes are hard to undo. The documented rules are:
- A namespace is created in a separate Developer Edition org (the namespace org) and linked to the Dev Hub through Namespace Registries. "After you associate a namespace with an org, you can't change it or reuse it."
- A namespace is assigned to a managed 2GP at creation and can't be changed. One 2GP package can't use more than one namespace.
- "After you create a package, you can't change or add a namespace, or change the Dev Hub the package is associated with." This applies to unlocked packages too.
- A managed 2GP package can still be transferred to another Dev Hub through a Salesforce Customer Support case. The namespace must be linked to both Dev Hubs first. Giving a sellable product its own namespace "enables you to transfer the namespace with the package."

### Unlocked Packages Are Not the AppExchange Vehicle

Unlocked packages expose modifiable metadata and are positioned for internal apps. For any product that needs IP protection or an AppExchange listing, use managed 2GP (preferred) or managed 1GP.

---

## Common Patterns

### Pattern: Unlocked Packages for Internal Org Decomposition

**When to use:** A large enterprise org needs to be split into independently deployable packages for different teams (Sales Automation, Service, Shared Platform).

**How it works:**
1. Define package boundaries based on team ownership and functional domains.
2. Create one unlocked package per domain in the Dev Hub (`sf package create --package-type Unlocked --path <dir> --name <name>`).
3. Declare package dependencies in `sfdx-project.json` (Service depends on Shared Platform).
4. Let each team release independently with pinned dependency versions (`2.1.0.RELEASED` or an explicit version).
5. Have CI/CD build and install each package in dependency order.
6. Use an org-dependent unlocked package only for metadata that can't yet be untangled from unpackaged org metadata.

**Why not one monolithic deployment:** monolithic deployments couple team releases, so a Service bug blocks a Sales release. Packages give each domain its own version history.

### Pattern: 2GP Managed Package for ISV AppExchange Product

**When to use:** Building a commercial Salesforce application for distribution on AppExchange.

**How it works:**
1. Create and register the namespace in a separate Developer Edition org.
2. Link the namespace org to the Dev Hub (App Launcher > Namespace Registries > Link Namespace).
3. Set the namespace in `sfdx-project.json` and create the package: `sf package create --name "Expense Manager" --path force-app --package-type Managed`.
4. Develop in scratch orgs and create versions with `sf package version create --package "Expense Manager" --code-coverage --installation-key-bypass --wait 30`.
5. Promote a version that meets 75% coverage with `sf package version promote --package <04t>`; beta versions install only in scratch orgs and sandboxes.
6. Submit for AppExchange security review and listing.

The full project file and command sequence are in [references/metadata-examples.md](references/metadata-examples.md).

**Why not 1GP:** 1GP keeps metadata in a packaging org, allows one package per namespace, uses linear versioning, and needs patch orgs. Salesforce recommends managed 2GP for ISVs listing on AppExchange.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Internal enterprise org decomposition | Unlocked packages | Source-driven, versioned, no IP protection needed |
| ISV commercial AppExchange product | Managed 2GP | IP protection, many packages per namespace, CLI-first |
| Legacy ISV product on 1GP | Evaluate 2GP migration | The 2GP guide says adopting 2GP for new packages avoids a future migration |
| Code sample or starter template | Unmanaged package | No upgrade needed; subscriber takes ownership |
| AppExchange listing required | Managed 2GP or 1GP only | Unlocked packages are positioned for internal apps |
| Need a namespace on an existing namespace-less unlocked package | Create a new package with the namespace | A package's namespace can't be added after creation |
| Metadata can't yet be separated from unpackaged org metadata | Org-dependent unlocked package, as a stepping stone | Validation moves to install time; no dependencies on other packages |

---

## Recommended Workflow

1. **Classify the distribution intent** (internal, multi-org internal, AppExchange) and record it in the decision record template.
2. **Assess IP protection and production-edit governance**: obfuscated managed code vs modifiable unlocked metadata.
3. **Decide the namespace**: pick a brand-stable string, register it in a dedicated namespace org, and link it to the Dev Hub that will own the packages. One namespace per sellable product keeps a transfer path open.
4. **Draft `sfdx-project.json`** with `packageDirectories`, `namespace`, `versionNumber` ending in `NEXT`, and pinned `dependencies`, then run `python3 skills/devops/package-development-strategy/scripts/check_package_development_strategy.py --project-dir .` to catch namespace, keyword, and dependency mistakes.
5. **Set the version retention and deletion policy**: who holds Delete Second-Generation Packages, and which `04t` IDs pipelines pin.
6. **Document the decision**: package type, namespace, distribution intent, dependency graph, and upgrade path.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Distribution intent documented (internal / multi-org / AppExchange)
- [ ] IP protection requirement assessed; if yes, only managed packages
- [ ] Namespace selected, registered in a namespace org, linked to the owning Dev Hub
- [ ] Unlocked package NOT selected for AppExchange ISV distribution
- [ ] `sfdx-project.json` passes the skill checker (namespace, `NEXT`, dependency keywords)
- [ ] Version deletion policy and Delete Second-Generation Packages assignment documented
- [ ] Package type decision documented with rationale

---

## Salesforce-Specific Gotchas

Full write-ups with sources are in [references/gotchas.md](references/gotchas.md).

| Gotcha | One-line summary |
|---|---|
| Namespace association | After a namespace is associated with an org it can't be changed or reused. |
| Package namespace | A package's namespace and Dev Hub can't be changed after creation. |
| Unlocked vs AppExchange | Unlocked metadata is editable in production; AppExchange products use managed 2GP. |
| Beta versions | Every version is beta until promoted; betas install only in scratch orgs and sandboxes and can't be upgraded. |
| Deletion rules | Released unlocked versions are deletable (permanent); released managed 2GP versions are not. |
| Org-dependent packages | Install only where the dependent metadata exists, and can't depend on other packages. |
| Skip validation | Versions built with `--skip-validation` can't be promoted. |
| InstalledPackage | Metadata installs cover managed 1GP only and must deploy alone. |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Package type decision record | Selected package type, namespace, rationale, and distribution intent |
| Namespace selection documentation | Chosen namespace, namespace org, linked Dev Hub, permanence acknowledgment |
| Dependency graph | Package dependency diagram for multi-package architectures |
| AppExchange eligibility assessment | Whether the selected package type supports AppExchange listing |

---

## Related Skills

- `devops/scratch-org-management`: scratch org configuration and shape management used in 2GP package development
- `architect/ci-cd-pipeline-architecture`: CI/CD pipeline design around package version creation and installation
- `devops/salesforce-dx-project-structure`: SFDX project structure and source format layout for package development
