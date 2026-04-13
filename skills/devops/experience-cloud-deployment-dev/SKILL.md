---
name: experience-cloud-deployment-dev
description: "Use this skill when scripting or automating the deployment of Experience Cloud sites between Salesforce orgs using the Metadata API, Salesforce CLI, or CI/CD pipelines. Covers ExperienceBundle (Aura-based sites), DigitalExperienceBundle (enhanced LWR sites), the ExperienceBundleSettings prerequisite, CMS content exclusion gaps, and required post-deployment manual steps for domain configuration, SSO, and CDN bindings. NOT for general Experience Cloud site building in Experience Builder, OmniStudio-based sites, CMS content authoring, or Salesforce Sites (Force.com Sites) deployments."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "how do I deploy an Experience Cloud site from sandbox to production using sf CLI"
  - "my ExperienceBundle retrieve returns empty metadata even though the site exists in the org"
  - "deploying an LWR Experience Cloud site fails or the site structure is wrong after deploy"
  - "CMS content is missing after deploying an Experience Cloud site with Metadata API"
  - "which metadata type do I use to deploy an Aura community versus an enhanced LWR site"
  - "post-deployment steps required after deploying an Experience Cloud site — domain, SSO, CDN not configured"
tags:
  - experience-cloud
  - experiencebundle
  - digitalexperiencebundle
  - lwr
  - aura
  - communities
  - metadata-api
  - deployment
  - devops
  - cms-content
inputs:
  - "Site runtime type (Aura-based community or enhanced LWR site) — determines which metadata type to use"
  - "Source org (sandbox or scratch org) and target org (production or UAT sandbox) details"
  - "Whether the site uses CMS managed content from a CMS workspace"
  - "Domain configuration requirements: custom domain, CDN, or SSO settings"
  - "API version in use (ExperienceBundle requires v46+; DigitalExperienceBundle requires v58+)"
outputs:
  - "Correct metadata type selection (ExperienceBundle vs. DigitalExperienceBundle) with rationale"
  - "Retrieve and deploy CLI commands with correct flags and package.xml entries"
  - "CMS content migration plan documenting what cannot be deployed via CLI and how to handle it"
  - "Post-deployment manual step runbook covering domain config, SSO bindings, and CDN URL configuration"
  - "ExperienceBundleSettings activation instructions for orgs where ExperienceBundle is not yet enabled"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# Experience Cloud Deployment Dev

This skill activates when a practitioner needs to script or automate the migration of an Experience Cloud site between Salesforce orgs using the Metadata API or Salesforce CLI. It guides selection of the correct metadata type for the site's runtime (Aura vs. enhanced LWR), diagnoses silent retrieval failures caused by missing ExperienceBundleSettings, handles the CMS content exclusion gap, and documents the post-deployment manual steps that no metadata type captures.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Site runtime type** — Determine whether the site is Aura-based (uses the original Communities runtime) or enhanced LWR (Lightning Web Runtime, available from Summer '22). This is the single most important prerequisite: the wrong metadata type retrieves nothing silently or deploys to the wrong structure.
- **ExperienceBundleSettings status** — For Aura-based sites, ExperienceBundle retrieval only works if the `ExperienceBundleSettings` metadata type is enabled in the org. Attempting to retrieve without it returns an empty result with no error.
- **CMS workspace content** — Identify whether the site displays content managed through a CMS workspace (Managed Content / Digital Experiences CMS). This content is excluded from both ExperienceBundle and DigitalExperienceBundle and cannot be promoted via `sf project deploy`. A deploy will exit 0 but the content will not appear in the target org.
- **Post-deployment configuration gaps** — Domain URL bindings, custom domain certificates, SSO provider configuration, and CDN URL bindings are not captured by any Experience Cloud metadata type. Plan for manual post-deployment steps in every migration.

---

## Core Concepts

### ExperienceBundle vs. DigitalExperienceBundle — The Runtime Split

Salesforce maintains two separate metadata types for Experience Cloud sites, split by the site's underlying runtime:

- **ExperienceBundle** (API v46+) — used for Aura-based sites (Classic, Customer Service, Partner Central templates, and similar). Must be explicitly enabled by deploying `ExperienceBundleSettings` with `enableExperienceBundle` set to `true` before any retrieve/deploy of site bundles will work.
- **DigitalExperienceBundle** (API v58+, generally available Spring '23) — used for enhanced LWR sites (Build Your Own LWR, Microsites, Help Center, and other LWR-native templates). Has a different directory structure: site-level JSON, a `pages/` tree, and a `routes/` tree instead of the Aura-oriented `views/` and `components/` layout.

Using the wrong type is the most common mistake: deploying an enhanced LWR site's files into an ExperienceBundle structure produces a deployment that completes with no errors but renders incorrectly or not at all.

### ExperienceBundleSettings Prerequisite

ExperienceBundle retrieval is gated behind an org-level feature flag. The metadata type `ExperienceBundleSettings` (a singleton Settings metadata) must exist in the project and be deployed first to enable the bundle-based retrieve/deploy workflow. Without it, `sf project retrieve start --metadata ExperienceBundle` completes successfully but returns zero components. This behavior is documented in the Salesforce Metadata API Developer Guide and is one of the most frequently misdiagnosed silent failures in Experience Cloud deployments.

To enable it, include in `package.xml`:
```xml
<types>
  <members>ExperienceBundleSettings</members>
  <name>Settings</name>
</types>
```
And ensure the retrieved `ExperienceBundleSettings.settings` file has `<enableExperienceBundle>true</enableExperienceBundle>`.

### CMS Managed Content Is Not Deployable via Metadata API

Content created in a CMS workspace (Digital Experiences CMS, accessible from the CMS Workspaces app) is stored as Managed Content records, not as metadata. Neither ExperienceBundle nor DigitalExperienceBundle includes this content. A deployment that omits CMS content will exit with code 0 (success) but the content will not appear in the target org — no warning is issued.

The two supported options for CMS content migration are:
1. **CMS export/import** — Export a content collection from the source org (Setup > CMS Workspaces > Export) and import it in the target org. Manual and error-prone for large volumes.
2. **Managed Content REST API** — The `connect/cms/contents` REST API can be used to script content creation in the target org, but it requires custom scripting outside the standard CLI deployment flow.

### Network Metadata and Deployment Ordering

The `Network` metadata type represents the community/site record configuration (active status, guest profile, login page, etc.). It is a separate metadata type from ExperienceBundle. Deploying ExperienceBundle without the corresponding `Network` record in the target org will create an orphaned site bundle. The correct deployment order is: (1) ExperienceBundleSettings, (2) Network, (3) ExperienceBundle or DigitalExperienceBundle.

---

## Common Patterns

### Pattern 1: Deploy an Aura-Based Experience Cloud Site

**When to use:** Migrating a site built on the Aura runtime (Customer Service, Partner Central, Salesforce Tabs + Visualforce, or similar legacy templates) from sandbox to production.

**How it works:**
1. Verify `ExperienceBundleSettings` is enabled in the target org or include it in the deployment.
2. Construct a `package.xml` that includes `Settings:ExperienceBundleSettings`, `Network:<SiteName>`, and `ExperienceBundle:<SiteName>`.
3. Retrieve from the source org:
   ```bash
   sf project retrieve start \
     --metadata "Settings:ExperienceBundleSettings" \
     --metadata "Network:My_Site" \
     --metadata "ExperienceBundle:My_Site" \
     --target-org source-sandbox
   ```
4. Review the retrieved bundle under `force-app/main/default/experiences/My_Site.site/`.
5. Deploy to the target org with the same component set.
6. Execute post-deployment manual steps (domain, SSO, CDN).

**Why not the alternative:** Retrieving only `ExperienceBundle` without `ExperienceBundleSettings` returns empty results. Deploying without the `Network` record creates an orphaned bundle with no associated site configuration.

### Pattern 2: Deploy an Enhanced LWR Site

**When to use:** Migrating a site built on the LWR runtime (Build Your Own LWR, Microsites, Help Center, or any template marked "Enhanced" in Experience Builder) from sandbox to production.

**How it works:**
1. Confirm the site is LWR-enhanced (check in Experience Builder: Settings > Advanced > Site Runtime shows "Enhanced LWR").
2. Construct a `package.xml` with `DigitalExperienceBundle:<SiteName>` and `Network:<SiteName>`.
3. Retrieve from the source org:
   ```bash
   sf project retrieve start \
     --metadata "DigitalExperienceBundle:My_LWR_Site" \
     --metadata "Network:My_LWR_Site" \
     --target-org source-sandbox
   ```
4. Review the retrieved bundle under `force-app/main/default/digitalExperiences/site/My_LWR_Site/`.
5. Deploy to the target org. Activate the site manually in Experience Builder if it deploys in inactive state.
6. Execute post-deployment manual steps.

**Why not the alternative:** Using `ExperienceBundle` for an LWR site produces an empty retrieve. The underlying file structure differs — DigitalExperienceBundle uses a `pages/` and `routes/` layout that ExperienceBundle does not support.

### Pattern 3: CI/CD Pipeline for Experience Cloud Sites

**When to use:** Setting up a repeatable automated pipeline that deploys Experience Cloud site changes alongside Apex, LWC, and other metadata.

**How it works:**
1. In `sfdx-project.json`, set `sourceApiVersion` to 58.0 or higher to support DigitalExperienceBundle.
2. Add a pre-deploy step that checks ExperienceBundleSettings is enabled in the target org (for Aura sites).
3. Deploy in the correct order: shared metadata first, then ExperienceBundleSettings, then Network, then the site bundle.
4. Add a post-deploy step script that calls the Managed Content REST API to sync CMS content if the site uses a CMS workspace.
5. Run a smoke-test step that fetches the site's public URL and checks for a non-5xx response.

**Why not the alternative:** A single-step `sf project deploy start --manifest package.xml` for all metadata does not guarantee the correct deployment order and may fail if ExperienceBundleSettings is not already active in the target org.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Site is Aura-based (Customer Service, Partner Central, etc.) | Use ExperienceBundle + ExperienceBundleSettings | DigitalExperienceBundle does not support Aura runtime sites |
| Site is enhanced LWR (Build Your Own LWR, Microsites, Help Center) | Use DigitalExperienceBundle | ExperienceBundle retrieves nothing for LWR sites |
| Unsure of runtime type | Check Experience Builder > Settings > Advanced > Site Runtime | Avoids silent failures from wrong metadata type |
| Site uses CMS workspace content | Plan CMS export/import or Managed Content REST API script in addition to metadata deploy | CMS content is not included in either metadata type |
| Post-deploy site is inactive | Manually activate in Experience Builder or use `sf community publish` CLI command | Site status is not reliably deployed by metadata |
| Scratch org development | Use DigitalExperienceBundle only; ExperienceBundle has known scratch org support gaps | Avoid inconsistent behavior in scratch orgs with Aura sites |
| Target org missing custom domain or CDN config | Document as post-deployment manual step in release runbook | Domain/CDN config is not captured in any metadata type |

---

## Recommended Workflow

Step-by-step instructions for deploying an Experience Cloud site:

1. **Identify the site runtime** — In Experience Builder for the source site, navigate to Settings > Advanced and note the Site Runtime value. "Aura" means use ExperienceBundle; "Enhanced LWR" means use DigitalExperienceBundle. This step cannot be skipped.
2. **Verify ExperienceBundleSettings (Aura sites only)** — Attempt a test retrieve of `Settings:ExperienceBundleSettings`. If the retrieve returns empty, the feature is not yet enabled. Deploy the settings metadata to activate it in the source and target orgs before proceeding.
3. **Build the component list and deploy order** — Construct the full component list: ExperienceBundleSettings (Aura only), shared LWC/Apex dependencies, Network record, and the site bundle. Document the required deployment order.
4. **Retrieve from source** — Run `sf project retrieve start` with the correct metadata type. Inspect the retrieved file structure to confirm the bundle directory is non-empty before proceeding.
5. **Assess CMS content** — Determine whether the site uses CMS workspace content. If yes, create a parallel CMS migration plan using export/import or the Managed Content REST API. Document this as a separate runbook step.
6. **Deploy to target** — Execute the deployment in the correct order. Monitor for partial success states — Experience Cloud deployments can return 0 exit codes even when post-activation steps are required.
7. **Execute post-deployment manual steps** — Configure domain bindings, CDN URLs, SSO providers, and guest user profile settings in the target org. Verify the site is active and publicly accessible. Document completed steps in the release runbook.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Site runtime type (Aura vs. enhanced LWR) confirmed and correct metadata type selected
- [ ] ExperienceBundleSettings enabled in both source and target orgs (Aura sites only)
- [ ] Retrieve from source org returns non-empty bundle directory
- [ ] Network metadata record included alongside the site bundle in the deployment
- [ ] CMS managed content migration plan documented separately (if applicable)
- [ ] Deployment order enforced: shared dependencies > ExperienceBundleSettings > Network > site bundle
- [ ] Post-deployment manual steps completed and documented: domain config, SSO, CDN, site activation

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Wrong metadata type returns empty results with no error** — Attempting to retrieve an enhanced LWR site using `ExperienceBundle` (or vice versa) completes successfully with exit code 0 but returns zero components. There is no warning. The practitioner must know to check the retrieved directory for non-empty content before proceeding.
2. **CMS deploy succeeds but content is invisible** — A deployment that excludes CMS workspace content completes with exit 0 and no warnings. The site loads but content zones are empty in the target org. This is the most common Experience Cloud deployment gap reported by practitioners.
3. **ExperienceBundleSettings must be deployed before ExperienceBundle can be retrieved** — This is a sequencing constraint that is not obvious from the metadata type names. Many teams discover it after spending hours debugging empty retrieve results. The setting must be active in the org, not just in the project files.
4. **Site activates in a deactivated state after deployment** — The `Network` metadata record may deploy the site in an inactive state even if it was active in the source org. The active/inactive toggle is often environment-specific and not reliably migrated. Manual activation in Experience Builder (or `sf community publish`) is required after every deployment.
5. **DigitalExperienceBundle has limited scratch org support** — Creating a scratch org with `DigitalExperienceBundle` components pre-loaded is not fully supported as of Spring '25. Scratch orgs are typically used for component development, not full LWR site deployment. Running `sf project deploy start` with DigitalExperienceBundle into a fresh scratch org can fail silently or produce an incomplete site structure.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Metadata type selection rationale | Written record of whether ExperienceBundle or DigitalExperienceBundle is correct for this site and why |
| package.xml with deployment order | Component manifest including ExperienceBundleSettings, Network, and the correct site bundle type |
| CMS content migration plan | Documented approach for migrating CMS workspace content outside the standard metadata deploy |
| Post-deployment runbook | Step-by-step checklist for domain config, SSO, CDN, and site activation with responsible owners |
| Smoke test script | Shell or Node script that fetches the site's public URL and validates a 200 response after deployment |

---

## Related Skills

- devops/metadata-api-coverage-gaps — Use when the Experience Cloud metadata type is behaving inconsistently or when CMS content gaps need to be documented in a formal coverage gap table
- devops/post-deployment-validation — Use for validating the deployed site and running post-deploy smoke tests after Experience Cloud deployment
- devops/pre-deployment-checklist — Use for the pre-deploy gate checks before any Experience Cloud site migration
- devops/cross-cloud-deployment-patterns — Use when the Experience Cloud site is part of a larger multi-cloud deployment that includes Sales Cloud, Service Cloud, or other metadata
- devops/scratch-org-management — Use when the Experience Cloud development workflow involves scratch org setup and known scratch org support gaps for LWR sites
