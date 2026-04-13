---
name: experience-cloud-deployment-admin
description: "Use this skill when deploying an Experience Cloud site (formerly Community) between Salesforce orgs or sandboxes — including metadata ordering, ExperienceBundle enablement, post-deployment publishing, and change-set or SFDX-based migration. NOT for: LWC component development within Experience Builder, CMS content migration via Managed Content REST API, or Aura/LWC code authoring."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Security
triggers:
  - "My Experience Cloud site is missing after deployment to production"
  - "ExperienceBundle deployment fails even though the metadata looks correct"
  - "How do I deploy a Community or Experience Cloud site with a change set"
  - "The deployed site is unpublished and I cannot see it live after deployment"
  - "Enable Experience Bundle Metadata API checkbox must be checked before deploying"
  - "Network or CustomSite metadata missing from my deployment package"
tags:
  - experience-cloud
  - deployment
  - experiencebundle
  - metadata-api
  - change-set
  - digital-experiences
  - network-metadata
inputs:
  - "Source and target org types (sandbox, production, scratch org)"
  - "Deployment mechanism in use: change set, Salesforce CLI (sf/sfdx), or Metadata API"
  - "Site name and template type (LWR, Aura, Salesforce Tabs + Visualforce)"
  - "Whether Enable Experience Bundle Metadata API is checked in both orgs"
  - "Full list of metadata components the site depends on (Apex, profiles, permission sets, custom objects)"
outputs:
  - "Ordered deployment plan with required metadata types and sequencing"
  - "Pre-deployment checklist for Experience Bundle enablement in source and target"
  - "Post-deployment publishing instructions (UI path and Connect REST API alternative)"
  - "Review checklist confirming site is live and permissioned correctly"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# Experience Cloud Deployment Admin

This skill activates when a practitioner needs to deploy an Experience Cloud site from one Salesforce org to another using change sets, the Salesforce CLI, or the Metadata API. It enforces the strict metadata ordering rules required by ExperienceBundle and guides the admin through the manual publish step that must follow every deployment.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm that **Enable Experience Bundle Metadata API** is checked in Setup > Digital Experiences > Settings in both the source org and the target org. Without this flag, ExperienceBundle metadata cannot be retrieved or deployed.
- Identify the full dependency chain: Apex classes used by the site, custom objects, profiles, permission sets, and any connected apps must be deployed before the site metadata.
- The most common wrong assumption is that deploying ExperienceBundle alone is sufficient. The Network, CustomSite, and all Apex/class dependencies must already exist in the target org before the ExperienceBundle deploy step.
- A successful deployment does not automatically publish the site. The deployed site remains in Draft status until an admin triggers Publish in Experience Builder or calls the Connect REST API.

---

## Core Concepts

### ExperienceBundle Metadata Type

ExperienceBundle is the primary metadata type representing an Experience Cloud site built in Experience Builder (LWR or Aura-based). It stores page layouts, themes, component configurations, and navigation menus as JSON and XML files. It does not store the classic SiteDotCom blob — including the SiteDotCom component in the same deployment package as ExperienceBundle causes the entire deployment to fail, even if all other metadata is valid.

ExperienceBundle is only available for retrieval and deployment when the **Enable Experience Bundle Metadata API** checkbox is active in both the source and the target org. This setting does not transfer automatically during provisioning.

### Network and CustomSite — Required Predecessors

The `Network` metadata type represents the configuration record for the Experience Cloud site (domain, status, authentication settings). The `CustomSite` metadata type represents the underlying site record that controls URL mappings and guest user access. Both must already exist in the target org before ExperienceBundle can be deployed successfully. Deploying ExperienceBundle into a target org that has no matching Network record will fail with a cryptic metadata error rather than a clear dependency message.

### Deployment Ordering Rule

The required metadata deployment order for an Experience Cloud site is:

1. Apex classes, Apex triggers, and Lightning components that the site references
2. Custom objects, custom fields, and record types that site pages surface
3. Profiles and permission sets (including the site Guest User Profile)
4. `Network` and `CustomSite` metadata
5. `ExperienceBundle`

Violating this sequence — for example, deploying ExperienceBundle and Network in the same change set in the wrong order — causes deployment failures that are difficult to diagnose because the Salesforce error messages reference the ExperienceBundle rather than the missing dependency.

### Draft Status After Deployment

Every successfully deployed ExperienceBundle lands in **Draft** (unpublished) status regardless of the status it had in the source org. The site is not accessible to end users until a workspace admin explicitly triggers Publish in Experience Builder (Preview > Publish) or programmatically publishes it via the Connect REST API (`POST /connect/communities/{communityId}/publish`). This is a platform-enforced safety gate, not a bug.

---

## Common Patterns

### Pattern: Staged Change Set Deployment

**When to use:** An admin-managed org with no SFDX or CLI tooling, deploying a new or updated Experience Cloud site from sandbox to production using change sets.

**How it works:**
1. Outbound change set in the source org includes: all Apex classes/triggers, custom objects/fields, profiles, `Network`, `CustomSite`, and `ExperienceBundle` for the site.
2. Upload and then deploy the change set containing Apex and data model components first — validate and deploy without ExperienceBundle.
3. Deploy a second change set containing `Network`, `CustomSite`, and `ExperienceBundle` in sequence.
4. After deployment completes, log in to the target org, open Experience Builder for the site, and click Publish.

**Why not a single change set:** Change sets deploy all components simultaneously and do not guarantee a dependency-aware ordering within the set. When ExperienceBundle and Network land together, ExperienceBundle may attempt to resolve references before Network is committed, causing the deploy to fail.

### Pattern: SFDX CLI Sequenced Deploy

**When to use:** Source-tracked project using Salesforce CLI (`sf` or `sfdx`) with a manifest (`package.xml`) targeting a sandbox or scratch org.

**How it works:**
1. Split the manifest into two: `package-deps.xml` (Apex, objects, profiles, Network, CustomSite) and `package-site.xml` (ExperienceBundle only).
2. Run: `sf project deploy start --manifest package-deps.xml --target-org <alias>` and wait for success.
3. Run: `sf project deploy start --manifest package-site.xml --target-org <alias>`.
4. Publish via Connect REST API or Experience Builder UI.

**Why not the alternative:** Deploying a single merged `package.xml` containing both Network and ExperienceBundle risks the same ordering failure as unordered change sets.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| First-time site deploy; Network does not exist in target | Deploy Network + CustomSite before ExperienceBundle | ExperienceBundle requires an existing Network record in target |
| Site already exists in target, updating component configs only | Deploy ExperienceBundle alone after verifying Network is present | Reduces deployment surface and risk |
| Site uses Apex controllers or custom LWC | Deploy Apex/LWC first in a separate step before deploying Network and ExperienceBundle | Avoids reference resolution failures in ExperienceBundle |
| Need automated publish after CLI deploy | Use Connect REST API `POST /connect/communities/{communityId}/publish` | Removes manual step from the release pipeline |
| SiteDotCom blob present in retrieval output | Remove SiteDotCom from the deployment package before deploying | Including SiteDotCom with ExperienceBundle causes deploy failure |
| Enable Experience Bundle Metadata API not active in target | Enable in Setup > Digital Experiences > Settings before deploying | ExperienceBundle cannot be deployed without this flag |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify Experience Bundle Metadata API is enabled** in both source and target orgs. Navigate to Setup > Digital Experiences > Settings and confirm the checkbox. Without this, retrieval and deployment of ExperienceBundle will fail silently or with misleading errors.
2. **Retrieve the full site metadata** from the source org including `Network`, `CustomSite`, and `ExperienceBundle`. Review the retrieved package and remove any `SiteDotCom` component — it must not be included in the deployment package.
3. **Identify and stage all Apex, LWC, and data model dependencies** the site references (Apex classes, triggers, custom objects, custom fields, record types, profiles, permission sets). Deploy these to the target org first and confirm success before proceeding.
4. **Deploy Network and CustomSite** to the target org. Confirm that the Network record now exists in the target (visible in Setup > All Sites).
5. **Deploy ExperienceBundle** in a separate deployment step after Network and CustomSite are confirmed present. Monitor deployment status and address any component-level errors before retrying.
6. **Publish the site** in the target org. Either open Experience Builder > Publish, or call `POST /connect/communities/{communityId}/publish` via the Connect REST API. Confirm the site status changes to Active and the URL is reachable.
7. **Validate guest user access and profile permissions** in the target org. The Guest User Profile for the site does not automatically inherit permission changes from the source — verify Apex class access, object CRUD permissions, and field-level security match the source configuration.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Enable Experience Bundle Metadata API is active in the target org
- [ ] SiteDotCom component is absent from the deployment package
- [ ] All Apex classes and LWC dependencies are deployed and accessible in the target before ExperienceBundle deploy
- [ ] Network and CustomSite records exist in the target org before ExperienceBundle is deployed
- [ ] Deployment completed without errors (checked in Setup > Deployment Status)
- [ ] Site is Published (Active) and reachable at its expected URL in the target org
- [ ] Guest User Profile permissions reviewed and confirmed correct in the target org

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **SiteDotCom blob breaks ExperienceBundle deployment** — When retrieving an Experience Cloud site, Salesforce includes a `SiteDotCom` component in the retrieved package. If this component is included when deploying ExperienceBundle, the entire deployment fails, often with a misleading error. Always strip SiteDotCom from the deployment manifest before deploying.
2. **Deployment does not publish the site** — A successful ExperienceBundle deployment leaves the site in Draft status. End users cannot access it until an admin publishes it. Teams frequently discover this only after release to production when users report the site is inaccessible.
3. **Enable Experience Bundle Metadata API must be set in both orgs independently** — This setting is org-specific and does not replicate via sandbox refresh or org copy. Every new sandbox or scratch org requires this checkbox to be enabled before ExperienceBundle can be retrieved or deployed.
4. **Network record name must match exactly** — The `Network` metadata component is keyed by the site name. If the site was renamed in the source org, the target org must also have a Network record with the exact same name, or the ExperienceBundle deploy will fail to find its parent Network.
5. **Guest User Profile changes require a separate profile deployment** — Changes made to the site's Guest User Profile (Apex class access, object permissions) are not included in ExperienceBundle. They must be retrieved and deployed separately as a `Profile` metadata component, otherwise the target site may behave differently from the source.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Ordered deployment plan | A sequenced list of change sets or CLI commands covering Apex/LWC deps → Network/CustomSite → ExperienceBundle |
| Pre-deployment checklist | Verification steps for Experience Bundle Metadata API flag, SiteDotCom removal, and dependency readiness |
| Post-deployment publishing runbook | Step-by-step instructions for publishing the site via UI or Connect REST API |
| Guest User Profile review notes | Summary of permissions that must be manually validated in the target org after deployment |

---

## Related Skills

- **devops/change-set-deployment** — Use for the general change set deployment workflow when the Experience Cloud site is one component among many in a broader release.
- **devops/pre-deployment-checklist** — Use to build the full org-level pre-deployment checklist; this skill provides the Experience Cloud-specific items to add.
- **devops/deployment-monitoring** — Use to monitor deployment status and interpret deployment errors after initiating the ExperienceBundle deploy step.
- **lwc/experience-cloud-lwc-components** — Use when the site references custom LWC components that must be authored or updated before deployment.
