---
name: package-development-strategy
description: "Use this skill when deciding between Salesforce package development approaches — unmanaged, unlocked, 1GP managed, or 2GP managed — including namespace selection, ISV distribution requirements, upgrade path design, and AppExchange packaging strategy. Trigger keywords: should I use managed or unlocked package, Salesforce package type selection, 2GP vs 1GP managed package, namespace decision Salesforce, ISV AppExchange packaging, unlocked package strategy. NOT for individual package creation steps, scratch org setup, or day-to-day package version build commands."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-16
---

# Package Development Strategy

Use this skill when making the foundational decision about which Salesforce package type to use for a project — and specifically the namespace decision, which is permanent. Covers unmanaged, unlocked, 1GP managed, and 2GP managed package types across the spectrum of internal use to ISV AppExchange distribution.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is this for **internal use** (within one customer org), **multi-org internal distribution**, or **AppExchange ISV distribution**?
- Is **IP protection** (code obfuscation) required? Only managed packages provide IP protection.
- Is an **upgrade path** required? Unmanaged packages have no upgrade mechanism — each install is a one-time copy.
- Does the project require a **namespace**? Managed packages require a namespace. Unlocked packages can optionally use a namespace. The namespace decision is permanent and cannot be changed after it is linked to the Dev Hub.
- Is there an existing Dev Hub? Unlocked and 2GP packages require a Dev Hub. 1GP packages use a separate org-centric packaging model.

---

## Core Concepts

### The Four Package Types on the Control vs. Mutability Spectrum

| Package Type | Upgrade Path | IP Protection | AppExchange | Namespace Required | Source-Driven |
|---|---|---|---|---|---|
| Unmanaged | No | No | No | No | No |
| Unlocked | Yes | No | No | Optional | Yes |
| 1GP Managed | Yes | Yes | Yes | Yes | No (org-centric) |
| 2GP Managed | Yes | Yes | Yes | Yes | Yes |

**Unmanaged packages** are a one-time install with no upgrade path. Installed components can be freely modified by the subscriber org. Use only for code samples, templates, or when a subscriber org intentionally takes ownership of the code.

**Unlocked packages** support source-driven development, version-controlled releases, and org-to-org upgrades. They have no code obfuscation and cannot be listed on AppExchange as a protected managed application. Best for internal cross-team distribution or large org decomposition.

**1GP managed packages** provide IP protection (Apex classes are non-readable in subscriber orgs) and AppExchange distribution. They use an org-centric development model (not source-controlled via CLI). 1GP is the legacy managed package approach — Salesforce recommends 2GP for all new managed package development.

**2GP managed packages** are Salesforce's recommended approach for new ISV products. They provide IP protection, AppExchange distribution, CLI-based automation, and support multiple packages per namespace (unlike 1GP which is limited to one package per namespace). Development is source-driven via the Salesforce DX model.

### The Permanent Namespace Constraint

**Namespace choice is irreversible.** Specifically:
- A namespace linked to a Dev Hub for 2GP cannot be transferred, reused, or unlinked
- A namespace-less unlocked package cannot be retroactively namespaced after installation in subscriber orgs
- A managed package namespace cannot be renamed

This is the most consequential architectural decision in package strategy — it must be made correctly the first time. Before creating any managed package, verify that the namespace string is acceptable for long-term product branding and does not conflict with existing namespaces in the ecosystem.

### Unlocked Packages Cannot Be Listed on AppExchange as Protected Apps

A common misconception is that unlocked packages are suitable for AppExchange distribution. **Unlocked packages:**
- Have no code obfuscation — Apex classes are readable in subscriber orgs
- Cannot be listed on AppExchange as a protected managed product
- Are appropriate only for apps where the subscriber org is expected to view and modify the source

For any product requiring IP protection or AppExchange listing as a commercial product, only 2GP managed (preferred) or 1GP managed packages apply.

---

## Common Patterns

### Pattern: Unlocked Packages for Internal Org Decomposition

**When to use:** A large enterprise org has grown beyond manageability and needs to be decomposed into independently deployable packages for different teams (Sales Automation, Service, Shared Platform).

**How it works:**
1. Define package boundaries based on team ownership and functional domains.
2. Create a separate unlocked package per domain in the Dev Hub.
3. Define package dependencies (Service package depends on Shared Platform package).
4. Each team has independent release cycles with version pinning on dependencies.
5. CI/CD pipeline builds and installs each package in the correct dependency order.

**Why not one monolithic deployment:** Monolithic deployments create release coupling between teams — a Service bug blocks a Sales release. Package decomposition enables independent deployment.

### Pattern: 2GP Managed Package for ISV AppExchange Product

**When to use:** Building a commercial Salesforce application for distribution on AppExchange.

**How it works:**
1. Register a namespace in a dedicated Namespace Registry org.
2. Link the namespace to the Dev Hub.
3. Create the 2GP managed package via CLI: `sf package create --name "MyApp" --package-type Managed`.
4. Develop components in a scratch org, package them, and create a version: `sf package version create`.
5. Promote the version to Released before submitting to AppExchange security review.
6. Submit for AppExchange listing and security review.

**Why not 1GP:** 1GP requires org-centric development without Salesforce DX tooling, has no source control integration, and limits you to one package per namespace. Salesforce officially recommends 2GP for all new ISV development.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Internal enterprise org decomposition | Unlocked packages | Source-driven, versioned, no IP protection needed |
| ISV commercial AppExchange product | 2GP managed package | IP protection, multi-package per namespace, DX tooling |
| Legacy ISV product on 1GP | Evaluate 2GP migration | 1GP is legacy; 2GP is recommended for new development |
| Code sample or starter template | Unmanaged package | No upgrade needed; subscriber takes ownership |
| AppExchange listing required, ISV product | 2GP or 1GP managed only | Unlocked packages cannot be AppExchange ISV listings |
| Need to namespace an existing unlocked package | Start over — not retroactively possible | Namespace cannot be added after subscriber installs |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Classify the distribution intent** — Internal only, multi-org internal, or AppExchange commercial distribution? AppExchange distribution requires a managed package.
2. **Assess IP protection requirement** — If IP protection (code obfuscation) is required, only managed packages (2GP preferred) apply. Eliminate unlocked from consideration.
3. **Decide on namespace** — If proceeding with managed package: select the namespace string carefully. It is permanent. Verify it is not already registered and is acceptable as a long-term product brand identifier.
4. **Check Dev Hub availability** — Unlocked and 2GP packages require a Dev Hub. Confirm Dev Hub is enabled and the namespace (for managed) is linked.
5. **Select package type** — Apply the decision matrix above. For most new projects: unlocked (internal) or 2GP managed (ISV/AppExchange).
6. **Document the decision** — Record the package type, namespace, distribution intent, and upgrade path approach. This is a foundational architectural decision.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Distribution intent documented (internal / multi-org / AppExchange)
- [ ] IP protection requirement assessed — if yes, only managed packages
- [ ] Namespace selected and its permanence acknowledged
- [ ] Dev Hub confirmed available and namespace linked (for managed/unlocked)
- [ ] Unlocked package NOT selected for AppExchange ISV distribution
- [ ] For 2GP: CLI tooling (sf package create, sf package version create) confirmed
- [ ] Package type decision documented with rationale

---

## Salesforce-Specific Gotchas

1. **Unlocked packages provide no IP protection** — Recommending unlocked packages for ISV products or AppExchange commercial listings is incorrect. Unlocked packages have no code obfuscation and cannot be listed as a protected commercial product on AppExchange.

2. **Namespace choice is permanent and cannot be transferred** — A namespace linked to a Dev Hub is bound to that Dev Hub permanently. Teams that discover they chose the wrong namespace after linking cannot undo the decision. The namespace must be abandoned and a new one selected.

3. **1GP is org-centric and not DX-compatible** — 1GP managed packages require development in the packaging org and do not support Salesforce DX source-format development. Teams expecting to use Git + CLI workflows with 1GP will face significant friction. 2GP should be used for all new managed package development.

4. **Installing a namespace-less unlocked package in a subscriber org locks out future namespacing** — Once an unlocked package without a namespace is installed in a subscriber org, adding a namespace to that package later is not possible without breaking the existing installation. The subscriber org would need to uninstall and reinstall a new namespaced package.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Package type decision record | Selected package type, namespace, rationale, and distribution intent |
| Namespace selection documentation | Chosen namespace, verification that it is available, permanence acknowledgment |
| Dependency graph | Package dependency diagram for multi-package architectures |
| AppExchange eligibility assessment | Documents whether the selected package type supports AppExchange listing |

---

## Related Skills

- `devops/scratch-org-management` — Use for scratch org configuration and shape management used in 2GP package development
- `devops/ci-cd-pipeline-architecture` — Use for CI/CD pipeline design around package version creation and installation
- `devops/salesforce-dx-project-structure` — Use for SFDX project structure and source format layout for package development
