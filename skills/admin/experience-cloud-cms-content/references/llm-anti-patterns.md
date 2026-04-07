# LLM Anti-Patterns — Experience Cloud CMS Content

Common mistakes AI coding assistants make when generating or advising on Experience Cloud CMS content setup and authoring.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating Knowledge Articles as CMS Content

**What the LLM generates:** Instructions that tell the user to create a Knowledge article to add content to their Experience Cloud site homepage, or that use Knowledge article creation steps when the user asked about CMS banners or news items.

**Why it happens:** Both Knowledge and CMS appear in Experience Cloud contexts, and LLM training data conflates them. Searches for "Salesforce CMS" or "Experience Cloud content" surface Knowledge article documentation because Knowledge is the more heavily documented content type.

**Correct pattern:**

```
CMS content (News, Banner, Image, custom types) is authored in Digital Experiences > Workspaces.
Knowledge articles are authored in the Knowledge tab and use a separate data category / article type system.
CMS content is published to sites through channels.
Knowledge articles are surfaced in sites through the Knowledge component or via search.
These are entirely separate systems with separate authoring UIs, separate metadata types, and separate publishing workflows.
```

**Detection hint:** If the generated steps mention "Article Type", "Data Category", or the Knowledge tab when the user asked about CMS workspace content, this anti-pattern is present.

---

## Anti-Pattern 2: Advising Point-and-Click Creation of Custom Content Types

**What the LLM generates:** Instructions like "In Setup > Digital Experiences > Content Types, click New to create a custom content type and add your fields."

**Why it happens:** LLMs generalize from other Salesforce declarative tools (custom objects, custom fields, custom metadata types) where point-and-click creation is available. They assume CMS custom types follow the same pattern.

**Correct pattern:**

```xml
<!-- ManagedContentType metadata — deploy via SFDX or Metadata API -->
<!-- File: force-app/main/default/managedContentTypes/EventAnnouncement.managedContentType-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<ManagedContentType xmlns="http://soap.sforce.com/2006/04/metadata">
    <developerName>EventAnnouncement</developerName>
    <masterLabel>Event Announcement</masterLabel>
    <managedContentNodeTypes>
        <fieldType>TEXT</fieldType>
        <helpText>Event title</helpText>
        <isRequired>true</isRequired>
        <label>Title</label>
        <name>title</name>
    </managedContentNodeTypes>
</ManagedContentType>
```

Deploy with: `sf project deploy start --source-dir force-app`

**Detection hint:** Any advice mentioning a Setup UI button or wizard for creating CMS content types is incorrect. Custom content types require a metadata deployment.

---

## Anti-Pattern 3: Recommending Content Publishing Without Channel Setup

**What the LLM generates:** Instructions to publish a CMS content item and then view it on the Experience Cloud site, skipping the step of creating and assigning a channel in the workspace.

**Why it happens:** The channel configuration step is an extra layer of indirection that LLMs skip when summarizing the workflow, especially if the model has seen tutorials that assume the channel already exists.

**Correct pattern:**

```
Before publishing content, verify:
1. A CMS workspace exists.
2. The target Experience Cloud site is added as a channel of type ExperienceChannel in that workspace.
3. The content item is published AND the channel appears under the item's Channel Assignments.

Content published without a channel assignment is not delivered to any site,
even if the item shows Published status.
```

**Detection hint:** If the workflow jumps from "publish the content item" to "the content appears on your site" without mentioning channel assignment, this anti-pattern is present.

---

## Anti-Pattern 4: Suggesting Metadata Deploy to Promote CMS Content Items Between Orgs

**What the LLM generates:** Instructions to add CMS content items to a SFDX source package, run `sf project deploy start`, and have the content appear in the target org.

**Why it happens:** LLMs know that Salesforce uses metadata deployment for most configuration promotion. They incorrectly generalize this to CMS content records, which are data, not metadata.

**Correct pattern:**

```
CMS content items are data records, not metadata files.
They are NOT included in sf project retrieve/deploy or Metadata API Retrieve/Deploy.

To move content between orgs:
1. Use Digital Experiences > Workspace > Export to export the workspace content as a ZIP.
2. In the target org, use Digital Experiences > Workspace > Import to import the ZIP.
3. Custom content type definitions (ManagedContentType XML) DO deploy via metadata — deploy those first.

Alternatively, use the Managed Content REST API to script content migration:
GET /services/data/vXX.0/connect/cms/content-items
POST /services/data/vXX.0/connect/cms/content-items
```

**Detection hint:** Any advice that includes CMS content items (banners, news articles) in a SFDX package manifest or metadata deploy command is incorrect.

---

## Anti-Pattern 5: Configuring Audience Targeting Before Audiences Exist in the Site

**What the LLM generates:** Instructions to create a content variant and select an audience from the dropdown during content authoring, without first confirming that audiences are defined in the Experience Cloud site settings.

**Why it happens:** LLMs present the end state (variant with audience selected) without surfacing the prerequisite that audiences must exist in the site before they appear in the CMS content authoring UI.

**Correct pattern:**

```
Audiences are defined per Experience Cloud site, not in the CMS workspace.

Prerequisite order:
1. Open the Experience Cloud site in Experience Builder.
2. Navigate to site Settings > Audience > New Audience.
3. Define the audience criteria (profile, record type, custom criteria).
4. Save and publish the audience.
5. Return to the CMS workspace and create the content variant.
   The audience now appears in the Target Audience dropdown.

If the Target Audience dropdown is empty when creating a variant,
it means no audiences have been defined for that site.
```

**Detection hint:** If the workflow for audience-targeted content variants does not include a step to define audiences in Experience Builder site settings before authoring the variant, this anti-pattern is likely present.

---

## Anti-Pattern 6: Assuming Sandbox-Published Content Automatically Appears in Production

**What the LLM generates:** Advice that treats CMS content published in a sandbox as automatically available in production, or that suggests no additional steps are needed to make sandbox-authored content live in production after a metadata deploy.

**Why it happens:** Developers familiar with metadata-driven configuration assume that publishing or configuring something in sandbox makes it promotable via a standard deploy pipeline. CMS content items do not follow this model.

**Correct pattern:**

```
CMS content items published in a sandbox stay in that sandbox.
A metadata deploy (sf project deploy) will NOT move content items to production.

To promote content to production:
1. In the sandbox workspace, use Export to download the content package.
2. In the production workspace, use Import to load the content package.
3. After import, review and publish each content item in production explicitly.
4. Confirm channel assignments are correct in the production workspace.
```

**Detection hint:** If a content promotion workflow mentions only `sf project deploy` without an explicit CMS Export/Import step, this anti-pattern is present.
