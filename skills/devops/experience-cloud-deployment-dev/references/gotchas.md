# Gotchas — Experience Cloud Deployment Dev

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: ExperienceBundle Retrieve Succeeds With Exit 0 but Returns Zero Components

**What happens:** Running `sf project retrieve start --metadata "ExperienceBundle:My_Site"` completes without errors and reports a successful retrieve, but the `experiences/` directory in the project is completely empty or only contains a stub JSON file.

**When it occurs:** When `ExperienceBundleSettings` has not been enabled in the source org. The ExperienceBundle metadata type is gated behind an org-level feature flag. Salesforce does not return an error when the flag is off — it simply returns no components.

**How to avoid:** Always retrieve and verify `Settings:ExperienceBundleSettings` before attempting a site bundle retrieve. If the settings file contains `<enableExperienceBundle>false</enableExperienceBundle>`, deploy the corrected settings first. Add a pre-retrieve check to CI pipelines that validates ExperienceBundleSettings is enabled before attempting the site bundle retrieve.

---

## Gotcha 2: CMS Managed Content Deployment Exits 0 With No Content in Target Org

**What happens:** A metadata deployment including ExperienceBundle or DigitalExperienceBundle completes with exit code 0 and no deployment errors. The site loads in the target org and navigation works, but all content zones powered by CMS Managed Content are empty.

**When it occurs:** When the site uses content created in a CMS Workspace (Digital Experiences CMS). This content is stored as Managed Content records — data, not metadata — and is silently excluded from both ExperienceBundle and DigitalExperienceBundle. The Metadata API does not warn about this exclusion.

**How to avoid:** Before starting any Experience Cloud deployment, inventory whether the site uses CMS Workspace content (check the site in Experience Builder for CMS content zones or content blocks). If it does, plan a parallel CMS content migration using either the CMS Workspaces export/import UI or the Managed Content REST API (`/connect/cms/contents`). Document this as a mandatory step in the release runbook. Never assume a successful deployment means all site content is present in the target org.

---

## Gotcha 3: Deployed Site Activates in Inactive State Even When Source Site Was Active

**What happens:** After deploying a Network record and its associated site bundle, the site exists in the target org but is in an inactive (offline) state. Users who visit the site URL see a generic "site offline" page or an HTTP error. The deployment completed with no errors.

**When it occurs:** The site active/inactive status is often environment-specific and the `Network` metadata may deploy the site in the state it had when the metadata was last retrieved (which may have been inactive in a sandbox at the time of retrieve). Additionally, some org configurations enforce manual activation as a security gate.

**How to avoid:** After every Experience Cloud deployment, explicitly activate the site using Experience Builder (Preview > Publish, or the Activate button under All Sites) or via the CLI:
```bash
sf community publish --name "My Site Name" --target-org target-org
```
Add site activation as a mandatory final step in the post-deployment runbook, not as an afterthought.

---

## Gotcha 4: Domain Config, SSO, and CDN Bindings Are Never Captured in Metadata

**What happens:** Custom domain URLs, CDN configuration (e.g., Akamai or Cloudflare origins set through Site.com or Experience Cloud settings), and SSO authentication provider bindings are not included in ExperienceBundle, DigitalExperienceBundle, or the Network metadata type. Deploying the complete site bundle to a new org leaves these settings unconfigured, even though the site content and page structure are correctly deployed.

**When it occurs:** Any time the source site uses a custom domain (not the default `*.site.salesforce.com` or `*.force.com` URL), Salesforce Identity or a third-party SSO provider for login, or a CDN-backed URL. This affects all Experience Cloud deployment scenarios, not just first-time deployments.

**How to avoid:** Create a post-deployment runbook section specifically for these manual steps:
1. **Custom domain** — Configure in Setup > My Domain, then assign to the site under Site Details.
2. **SSO** — Configure the Authentication Provider and assign it to the site's Login & Registration settings.
3. **CDN** — Re-register the CDN origin in Setup > Sites and Domains (if using Enhanced Domains) or in the CDN provider's configuration pointing at the target org's site URL.

Do not assume these settings transfer with the site bundle — they never do.

---

## Gotcha 5: DigitalExperienceBundle Not Supported in All Scratch Org Configurations

**What happens:** Attempting to deploy DigitalExperienceBundle components into a freshly created scratch org either fails with a cryptic metadata error or deploys without errors but results in an incomplete or non-functional site structure.

**When it occurs:** When using scratch orgs for end-to-end LWR site development. DigitalExperienceBundle scratch org support has known gaps as of Spring '25 — specifically around scratch org definition files that do not include the correct `features` and `settings` entries for enhanced digital experiences.

**How to avoid:** Scratch orgs for Experience Cloud development are best suited for developing individual LWC components and Apex classes used on the site, not for full site deployment testing. Use a sandbox as the primary integration environment for DigitalExperienceBundle deployments. If scratch orgs must be used, consult the current Salesforce DX Developer Guide for the latest scratch org definition requirements for Experience Cloud features and test thoroughly against the specific API version.

---

## Gotcha 6: ContentTypeBundle Is a Separate Metadata Type Not Included in Site Bundles

**What happens:** Custom content types created for use in the CMS (via Content Type Builder or manually as ContentTypeBundle metadata) are not included when retrieving ExperienceBundle or DigitalExperienceBundle. Deploying the site bundle to an org that lacks the content types causes content zone rendering failures.

**When it occurs:** When the site uses custom CMS content types (not the Salesforce-standard News or Document types) for structured content in content zones or content blocks.

**How to avoid:** Always include `ContentTypeBundle` components in the deployment alongside the site bundle:
```xml
<types>
  <members>*</members>
  <name>ContentTypeBundle</name>
</types>
```
Retrieve and deploy ContentTypeBundle before or alongside the site bundle and CMS content migration.
