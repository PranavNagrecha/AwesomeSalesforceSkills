# LLM Anti-Patterns — Experience Cloud Deployment Dev

Common mistakes AI coding assistants make when generating or advising on Experience Cloud deployment scripting.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using ExperienceBundle for Enhanced LWR Sites

**What the LLM generates:** A retrieve command that uses `--metadata "ExperienceBundle:My_LWR_Site"` for a site that runs on the enhanced LWR runtime (Build Your Own LWR, Microsites, Help Center).

**Why it happens:** LLMs are trained on documentation and community posts that predate the DigitalExperienceBundle type (GA Spring '23). ExperienceBundle is more frequently mentioned across all Experience Cloud documentation and is the type LLMs default to regardless of the site runtime.

**Correct pattern:**

```bash
# First identify the runtime — enhanced LWR sites use DigitalExperienceBundle
sf project retrieve start \
  --metadata "DigitalExperienceBundle:My_LWR_Site" \
  --metadata "Network:My_LWR_Site" \
  --target-org source-sandbox

# Retrieved files appear under:
# force-app/main/default/digitalExperiences/site/My_LWR_Site/
```

**Detection hint:** Look for `ExperienceBundle` in any command or package.xml targeting an enhanced LWR, Microsites, Help Center, or "Build Your Own LWR" site. Any such combination is likely wrong.

---

## Anti-Pattern 2: Omitting ExperienceBundleSettings From the Retrieve/Deploy Plan

**What the LLM generates:** A retrieve command or package.xml that includes `ExperienceBundle:My_Site` and `Network:My_Site` but does not include `Settings:ExperienceBundleSettings`. The assistant presents this as a complete deployment plan.

**Why it happens:** LLMs often skip prerequisite setup steps when generating deployment plans, focusing on the primary metadata types. The ExperienceBundleSettings dependency is a non-obvious feature flag that is rarely emphasized in deployment tutorials.

**Correct pattern:**

```xml
<!-- package.xml — always include ExperienceBundleSettings for Aura sites -->
<types>
  <members>ExperienceBundleSettings</members>
  <name>Settings</name>
</types>
<types>
  <members>My_Site</members>
  <name>Network</name>
</types>
<types>
  <members>My_Site</members>
  <name>ExperienceBundle</name>
</types>
```

**Detection hint:** Any ExperienceBundle deployment plan that does not mention `ExperienceBundleSettings` is incomplete for Aura sites. Look for its absence in package.xml entries and CLI command sequences.

---

## Anti-Pattern 3: Claiming CMS Managed Content Is Included in the Site Bundle Deployment

**What the LLM generates:** A statement such as "deploying ExperienceBundle will migrate your site including its content" or a deployment plan that does not mention CMS content migration as a separate step, implying that all site content is captured in the metadata deploy.

**Why it happens:** LLMs conflate "site deployment" with "complete content migration." CMS Managed Content is a record-data concept, not a metadata concept, and LLMs trained on general Salesforce documentation frequently miss this distinction.

**Correct pattern:**

```
CMS Managed Content is NOT included in ExperienceBundle or DigitalExperienceBundle.
A metadata deployment of an Experience Cloud site will succeed (exit 0) even when
CMS content is absent. Always plan a parallel CMS content migration using:

Option A: Setup > CMS Workspaces > Export/Import (manual)
Option B: Managed Content REST API (/services/data/vXX.0/connect/cms/contents)

Document CMS content migration as a required step in the release runbook.
```

**Detection hint:** Any deployment plan for an Experience Cloud site that does not include CMS content migration as a separate, explicit step should be flagged for review.

---

## Anti-Pattern 4: Assuming Deployment Completion Means the Site Is Active and Accessible

**What the LLM generates:** Post-deployment instructions that skip site activation, or a statement that the site will be "live" immediately after running the deploy command.

**Why it happens:** LLMs generalize from typical metadata deployment behavior where a deployed component is immediately active. Experience Cloud sites have a separate active/inactive toggle that is not reliably managed by metadata deployment and defaults to inactive in many configurations.

**Correct pattern:**

```bash
# After deploying the site bundle, explicitly publish/activate the site
sf community publish --name "My Site Name" --target-org target-org

# OR manually activate in Experience Builder:
# All Sites > My Site > Activate (or Publish)

# Then verify the site is accessible
curl -o /dev/null -s -w "%{http_code}" "https://my-site-url.my.site.salesforce.com"
# Expected: 200
```

**Detection hint:** Post-deployment instructions that do not include a site activation step or a smoke test of the site URL are incomplete.

---

## Anti-Pattern 5: Treating Domain Config, SSO, and CDN as Deployable Metadata

**What the LLM generates:** A package.xml or deployment command that implies custom domain settings, SSO authentication provider bindings, or CDN configuration will be migrated as part of the Experience Cloud deployment.

**Why it happens:** LLMs sometimes hallucinate that authentication-related settings (like `AuthProvider` or `SamlSsoConfig`) are sufficient to configure SSO for a site when in reality the site-to-SSO binding must be manually set in Experience Builder's Login & Registration settings. Similarly, LLMs may not surface the fact that CDN configuration is entirely outside metadata.

**Correct pattern:**

```
The following settings are NEVER captured in ExperienceBundle or DigitalExperienceBundle
and must be manually configured after every deployment to a new org:

1. Custom domain URL binding (Setup > My Domain > Assign to Site)
2. SSO provider assignment (Experience Builder > Administration > Login & Registration)
3. CDN origin configuration (varies by CDN provider; not in any Salesforce metadata type)
4. Guest user profile field-level security (must be re-verified in target org)

Add these as mandatory manual steps in the post-deployment runbook with named owners.
```

**Detection hint:** Any deployment plan claiming to migrate SSO configuration, custom domain bindings, or CDN settings via metadata should be flagged. These configuration items require post-deployment manual steps in every Experience Cloud migration.

---

## Anti-Pattern 6: Recommending Scratch Orgs as the Primary Environment for Full LWR Site Deployment

**What the LLM generates:** Instructions to create a scratch org with a communities-enabled definition file and deploy a DigitalExperienceBundle there for full end-to-end site testing.

**Why it happens:** LLMs are trained on Salesforce DX best practices that recommend scratch orgs as the primary development environment. This advice is appropriate for Apex and LWC development but is not reliable for full DigitalExperienceBundle deployments due to known scratch org support gaps in Spring '25.

**Correct pattern:**

```
For enhanced LWR site (DigitalExperienceBundle) deployments:
- Use a Developer or Developer Pro sandbox as the primary integration environment.
- Reserve scratch orgs for individual LWC component and Apex development.
- Do not rely on scratch orgs for full DigitalExperienceBundle deployment testing.

Check the Salesforce DX Developer Guide for the latest scratch org feature support
status for Digital Experiences before using scratch orgs for site-level testing.
```

**Detection hint:** Any workflow that deploys a full DigitalExperienceBundle to a scratch org for end-to-end testing should be reviewed against the current scratch org feature support documentation.
