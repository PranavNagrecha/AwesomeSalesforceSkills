# Examples — Experience Cloud Deployment Dev

## Example 1: Aura Site Retrieve Returns Empty — ExperienceBundleSettings Not Enabled

**Context:** A team is migrating a Customer Service Community (Aura runtime) from a Full sandbox to production for the first time. The site has been live in the sandbox for 18 months and contains 30+ custom pages.

**Problem:** Running the retrieve command returns a success message but the `experiences/` directory in the project is empty or only contains a top-level `.json` file with no page or component files. No error is shown.

```bash
# This command completes with exit 0 but returns nothing useful
sf project retrieve start \
  --metadata "ExperienceBundle:Customer_Service_Portal" \
  --target-org full-sandbox

# Result: experiences/Customer_Service_Portal.site/ directory is missing or empty
```

**Solution:**

First, check whether ExperienceBundleSettings is enabled by retrieving it:

```bash
sf project retrieve start \
  --metadata "Settings:ExperienceBundleSettings" \
  --target-org full-sandbox
```

Inspect the retrieved file at `force-app/main/default/settings/ExperienceBundleSettings.settings-meta.xml`. If it contains `<enableExperienceBundle>false</enableExperienceBundle>` (or the file does not exist), the feature is not enabled. Deploy the corrected settings to activate it:

```xml
<!-- force-app/main/default/settings/ExperienceBundleSettings.settings-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<ExperienceBundleSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableExperienceBundle>true</enableExperienceBundle>
</ExperienceBundleSettings>
```

```bash
sf project deploy start \
  --metadata "Settings:ExperienceBundleSettings" \
  --target-org full-sandbox

# Now retrieve the site bundle — it will return the full page structure
sf project retrieve start \
  --metadata "ExperienceBundle:Customer_Service_Portal" \
  --target-org full-sandbox
```

**Why it works:** ExperienceBundle retrieval is gated behind an org-level feature flag. The Metadata API silently returns empty results when the flag is off instead of returning an error. Enabling `ExperienceBundleSettings` first unlocks the retrieve for all Aura-based sites in that org.

---

## Example 2: Enhanced LWR Site Deployed — CMS Content Missing in Production

**Context:** A team uses the "Build Your Own LWR" template for a public-facing product catalog site. The site displays promotional content managed through the CMS Workspaces app (Digital Experiences CMS). They run a standard metadata deployment from UAT to production and the deployment succeeds.

**Problem:** After deployment, the site loads and navigation works correctly, but all content zones on product pages are empty. The deployment exited with code 0 and the deploy log shows no failures.

```bash
# This succeeds, but CMS content is not included
sf project deploy start \
  --metadata "DigitalExperienceBundle:Product_Catalog" \
  --metadata "Network:Product_Catalog" \
  --target-org production
# Exit code: 0
# Result: Site deploys but content zones are empty in production
```

**Solution:**

Recognize that CMS Managed Content records are not part of any metadata type and must be migrated separately. The two available options are:

**Option A — CMS Export/Import (manual, suitable for one-time migrations):**
1. In the source org: Setup > CMS Workspaces > select the workspace > Export Content Collection.
2. Download the export archive.
3. In the target org: Setup > CMS Workspaces > Import > upload the archive.
4. Verify channel assignments (the CMS workspace must be connected to the site's Experience Cloud channel in the target org).

**Option B — Managed Content REST API (scriptable, suitable for CI/CD):**
```bash
# List content items in source org
curl -H "Authorization: Bearer $SOURCE_ACCESS_TOKEN" \
  "$SOURCE_INSTANCE_URL/services/data/v62.0/connect/cms/contents?channelId=$SOURCE_CHANNEL_ID" \
  -o cms_contents.json

# Use the response to POST each content item to the target org
# (requires custom scripting per content type)
curl -X POST \
  -H "Authorization: Bearer $TARGET_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  "$TARGET_INSTANCE_URL/services/data/v62.0/connect/cms/contents" \
  --data @content_payload.json
```

**Why it works:** CMS Managed Content is stored as records in the org database, not as file-based metadata. The Metadata API has no mechanism to include record data in a deployment. Explicit export/import or REST API scripting is the only way to move this content between orgs.

---

## Example 3: Enhanced LWR Site Deploys but Renders Incorrectly — Wrong Metadata Type Used

**Context:** A developer attempts to retrieve a "Help Center" LWR site (enhanced LWR template) but uses `ExperienceBundle` instead of `DigitalExperienceBundle` in the package.xml, either through unfamiliarity with the runtime split or by copying an older pipeline configuration.

**Problem:** The retrieve completes but the directory structure is either empty or contains stale Aura-format data from a different site. When the bundle is deployed to another org, the site either fails to load or displays the wrong layout.

**Solution:**

Always verify the site runtime type before constructing the retrieve command:

1. Open Experience Builder for the target site.
2. Navigate to Settings > Advanced > Site Runtime.
3. If the value is "Enhanced LWR", use `DigitalExperienceBundle`:

```bash
# Correct for enhanced LWR sites
sf project retrieve start \
  --metadata "DigitalExperienceBundle:Help_Center" \
  --metadata "Network:Help_Center" \
  --target-org source-sandbox
```

The retrieved bundle will appear under `force-app/main/default/digitalExperiences/site/Help_Center/` with a `pages/` subdirectory and JSON route files — not the `views/` and `components/` layout used by Aura-based ExperienceBundle.

**Why it works:** The runtime split is fundamental to the metadata type design. DigitalExperienceBundle uses a different directory schema than ExperienceBundle. Using the correct type ensures the retrieved files match what Experience Builder expects to render in the target org.

---

## Anti-Pattern: Deploying the Site Bundle Without the Network Record

**What practitioners do:** Include only `ExperienceBundle:My_Site` or `DigitalExperienceBundle:My_Site` in the deployment manifest, omitting the `Network` metadata record because it seems like a separate concern.

**What goes wrong:** The site bundle deploys but has no associated Network record in the target org. The Experience Builder UI shows the site as existing but the site URL is unresolvable, the guest user profile is not linked, and login page configuration is absent. In orgs where the site was previously deployed, deploying only the bundle without the Network record can also reset guest profile assignments.

**Correct approach:** Always include both the site bundle and the corresponding Network record in the same deployment:

```xml
<!-- package.xml — always include both -->
<types>
  <members>My_Site</members>
  <name>Network</name>
</types>
<types>
  <members>My_Site</members>
  <name>ExperienceBundle</name>  <!-- or DigitalExperienceBundle for LWR -->
</types>
```
