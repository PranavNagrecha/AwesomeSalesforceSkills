---
name: cross-cloud-deployment-patterns
description: "Use when sequencing a deployment that spans multiple Salesforce clouds — Sales Cloud, Service Cloud, and Experience Cloud — and encountering reference errors, cascading metadata failures, or DigitalExperienceBundle ordering problems. Triggers: 'ExperienceBundle deployment fails with no Network found', 'cross-cloud metadata dependency error', 'how do I deploy Experience Cloud with Sales Cloud together', 'DigitalExperienceBundle missing CustomSite reference', 'how to sequence multi-cloud deployment correctly'. NOT for single-cloud deployments (use pre-deployment-checklist), NOT for OmniStudio or Health Cloud deployment specifics (use health-cloud-deployment-patterns), NOT for package-based multi-cloud release strategy (use multi-package-development)."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "my ExperienceBundle deployment fails with 'no Network named X found'"
  - "how do I sequence a deployment that covers Sales Cloud, Service Cloud, and Experience Cloud at the same time"
  - "deployment fails with cascading reference errors when Experience Cloud metadata is included"
  - "DigitalExperienceBundle deploy fails even though all other metadata looks valid"
  - "what order do I deploy custom objects, Apex, and ExperienceBundle for a multi-cloud release"
  - "SiteDotCom blob causes deployment failure when included in ExperienceBundle package"
  - "target org API version mismatch causes Experience Cloud metadata to fail"
tags:
  - deployment
  - experience-cloud
  - metadata-api
  - multi-cloud
  - deployment-ordering
  - ExperienceBundle
  - DigitalExperienceBundle
inputs:
  - "List of metadata types included in the cross-cloud deployment"
  - "Source and target org API versions"
  - "Deployment tool in use (sf CLI, Metadata API, DevOps Center, change sets)"
  - "Error messages from the failed or blocked deployment"
  - "Whether ExperienceBundle or DigitalExperienceBundle is in scope"
outputs:
  - "Ordered deployment sequence that avoids cascading reference errors"
  - "Pre-flight checklist for cross-cloud metadata dependencies"
  - "List of metadata types that must be excluded from the Experience layer package"
  - "Decision table mapping deployment scenarios to correct packaging strategy"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# Cross-Cloud Deployment Patterns

This skill activates when a practitioner or agent must deploy metadata that spans multiple Salesforce clouds — typically Sales Cloud or Service Cloud combined with Experience Cloud — and must resolve dependency ordering to prevent cascading reference errors. It covers the mandatory foundation-first deployment sequence, ExperienceBundle and DigitalExperienceBundle exclusion rules, and API version compatibility constraints.

---

## Before Starting

Gather this context before working on anything in this domain:

- Identify every metadata type in the deployment package. Group them into three layers: (1) foundation objects and Apex, (2) Network and site infrastructure, (3) Experience layer (ExperienceBundle or DigitalExperienceBundle).
- Confirm source and target org API versions. Certain Experience Cloud metadata types are not backward-compatible. The target org must be on the same API version as or a newer API version than the source org.
- Check whether `SiteDotCom` is included in the package. If it is embedded inside an ExperienceBundle, it must be excluded from the deployment even when everything else in the package is valid. Including it causes deployment failure.
- Determine whether the deployment will go in a single transaction or must be split across multiple batches. Reference errors at the Experience layer almost always require a split sequence.

---

## Core Concepts

### Foundation-First Sequence

The Metadata API processes types in a documented internal order, but cross-cloud deployments introduce explicit ordering requirements that the engine cannot resolve automatically when dependencies span cloud domains.

The canonical sequence is:

1. **Foundation layer**: custom objects, custom fields, Apex classes, Apex triggers, Lightning components, permission sets, and profiles.
2. **Network infrastructure layer**: `Network` and `CustomSite` metadata types. These must exist in the target org before any Experience layer component can reference them.
3. **Experience layer**: `ExperienceBundle` or `DigitalExperienceBundle`. These types embed references to the Network record by name. If the Network does not exist in the target org when the ExperienceBundle lands, the deployment fails with the error `no Network named X found`.

Deploying these three layers in a single transaction is possible only when the Metadata API's internal ordering guarantees that Network and CustomSite are fully committed before ExperienceBundle is evaluated. In practice, the safest approach is to split the deployment into two or three ordered transactions.

### ExperienceBundle vs DigitalExperienceBundle

Salesforce introduced `DigitalExperienceBundle` in API version 54.0 as the successor to `ExperienceBundle` for Experience Builder sites. The two types are not interchangeable across API versions:

- `ExperienceBundle` is available from API v45.0 and covers earlier Experience Cloud sites.
- `DigitalExperienceBundle` is required for sites built with the newer Digital Experiences framework (API v54.0+).

When the source org is on API v54.0+ and the target org is on an older version, `DigitalExperienceBundle` metadata is not recognized in the target and the deployment fails. Always confirm both org API versions before attempting a cross-cloud deploy that includes Experience Cloud sites.

### SiteDotCom Blob Exclusion Rule

`SiteDotCom` is a binary blob that Salesforce auto-generates when you retrieve certain Experience Cloud site metadata. It is not deployable as part of a standard Metadata API deployment package. Including it — even unintentionally — causes a deployment failure that can be mistaken for an unrelated error. The fix is to explicitly exclude the `SiteDotCom` type from `package.xml` and from any `.forceignore` or `.gitignore` files that might accidentally allow it to be staged.

### API Version Compatibility Constraint

The target org cannot be on an older API version than the source org when Experience Cloud metadata is in scope. Unlike most metadata types that degrade gracefully, Experience Cloud metadata types may reference internal references, page layout formats, or component capabilities that do not exist in older API versions. Deploying across a version boundary in this direction fails silently on some components and loudly on others.

---

## Common Patterns

### Split Deployment Pattern (Recommended)

**When to use:** Any cross-cloud deployment that includes ExperienceBundle, DigitalExperienceBundle, or CustomSite alongside foundational metadata like custom objects, Apex, or permission sets.

**How it works:**

1. Build a `foundation-package.xml` that includes: `CustomObject`, `ApexClass`, `ApexTrigger`, `LightningComponentBundle`, `PermissionSet`, `Profile`.
2. Deploy the foundation package and wait for it to complete successfully.
3. Build a `network-package.xml` that includes: `Network`, `CustomSite`.
4. Deploy the network package and wait for it to complete successfully.
5. Build an `experience-package.xml` that includes: `ExperienceBundle` or `DigitalExperienceBundle`. Explicitly exclude `SiteDotCom`.
6. Deploy the experience package.

**Why not a single package:** A single-transaction deploy of all three layers risks the Experience layer being evaluated by the Metadata API before the Network record is fully committed, which produces the `no Network named X found` error regardless of whether the XML is otherwise valid.

### Single-Transaction Pattern (Low-Risk Releases)

**When to use:** Small releases where only ExperienceBundle page layout changes or content updates are included and the foundation layer already exists and is stable in the target org.

**How it works:** Deploy only the Experience layer changes in a single package. The Network and CustomSite records already exist in the target org, so no cross-layer dependency needs to be resolved.

**Why not always:** If foundation components are also changing in the same release, this pattern breaks. Foundation changes must land first.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Full multi-cloud release with new objects, Apex, and new Experience site | Three-batch split: foundation → network → experience | Guarantees cross-layer dependencies resolve in order |
| Only Experience layer content updates, foundation stable | Single experience-layer batch | Network already exists; no ordering risk |
| Source org on API v54+, target org on older version | Block deployment until target is upgraded | DigitalExperienceBundle is not backward-compatible |
| SiteDotCom appears in retrieved metadata | Exclude via package.xml and .forceignore before packaging | Including it causes deployment failure |
| Network metadata and ExperienceBundle must go together | Deploy Network first, then ExperienceBundle in sequence | ExperienceBundle references Network by name |
| Permission sets grant access to objects in the same release | Include permission sets in the foundation batch, not experience batch | Object must exist before permission grants can resolve |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Audit the full component list.** Enumerate every metadata type in the release. Group each type into foundation, network, or experience layer. Flag any `SiteDotCom` entries for exclusion.
2. **Check API version alignment.** Confirm source org API version equals or is less than the target org API version. If the target is behind, escalate to the platform admin before proceeding.
3. **Build the foundation package.** Assemble a `package.xml` containing all custom objects, Apex classes, Apex triggers, Lightning components, permission sets, and profiles. Exclude Network, CustomSite, ExperienceBundle, DigitalExperienceBundle, and SiteDotCom.
4. **Deploy foundation and validate.** Run `sf project deploy start --manifest foundation-package.xml --target-org <alias>`. Confirm full success before advancing. Do not proceed if any component fails.
5. **Deploy the network layer.** Assemble and deploy a package containing Network and CustomSite. Verify the Network record is queryable in the target org after deployment (`sf data query --query "SELECT Id, Name FROM Network" --target-org <alias>`).
6. **Deploy the experience layer.** Assemble and deploy a package containing ExperienceBundle or DigitalExperienceBundle. Confirm SiteDotCom is absent from the manifest. Monitor the deploy for `no Network named X found` errors — if they appear, the network layer did not fully resolve before the experience layer was submitted.
7. **Run post-deployment validation.** Verify site availability, navigate to community pages, confirm permission sets grant the expected access, and run automated smoke tests against the target org.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All metadata components classified into foundation, network, or experience layer
- [ ] SiteDotCom excluded from every deployment package
- [ ] Target org API version confirmed equal to or newer than source org API version
- [ ] Foundation layer deployed and validated before network layer starts
- [ ] Network layer deployed and validated before experience layer starts
- [ ] ExperienceBundle or DigitalExperienceBundle deployed without SiteDotCom
- [ ] Post-deployment site availability and permission checks passed

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **`no Network named X found` appears even when Network is in the same package** — The Metadata API can evaluate ExperienceBundle before Network is committed within a single transaction. This error is not a missing-component error; it is an ordering error. The fix is to split Network into a prior deployment batch.
2. **SiteDotCom is silently included in retrievals** — When you run `sf project retrieve start` and include ExperienceBundle in the manifest, Salesforce may return SiteDotCom as part of the result set. It does not appear as an error during retrieval but causes a deployment failure if included in the deploy manifest. Audit retrieved metadata before packaging.
3. **DigitalExperienceBundle is version-locked** — Unlike most metadata types that degrade gracefully across API version differences, DigitalExperienceBundle does not deploy to a target org on a lower API version. The deployment fails without a clear actionable error message pointing to the version mismatch.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `foundation-package.xml` | Manifest for the first deployment batch: custom objects, Apex, components, permission sets, profiles |
| `network-package.xml` | Manifest for the second batch: Network and CustomSite metadata only |
| `experience-package.xml` | Manifest for the third batch: ExperienceBundle or DigitalExperienceBundle, SiteDotCom excluded |
| Cross-cloud deployment checklist | Pre-flight verification list for API version alignment, SiteDotCom exclusion, and layer sequencing |

---

## Related Skills

- `pre-deployment-checklist` — use for pre-flight validation across any Salesforce deployment before executing the sequence
- `permission-set-deployment-ordering` — use when permission sets in the foundation batch require precise ordering to avoid cross-reference errors
- `experience-cloud-deployment-dev` — use for Experience Cloud-specific developer configuration and LWR or Aura component deployment details
- `experience-cloud-deployment-admin` — use for admin-level Experience Cloud setup, Network settings, and guest user access configuration
- `post-deployment-validation` — use after the experience layer is deployed to verify site availability and access
- `metadata-api-coverage-gaps` — use when unexpected metadata types are missing from the deployment or not behaving as documented
