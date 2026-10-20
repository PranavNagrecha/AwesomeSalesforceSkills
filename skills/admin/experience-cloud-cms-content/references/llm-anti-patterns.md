# LLM Anti-Patterns — Experience Cloud CMS Content

Common mistakes AI coding assistants make when generating or advising on Experience Cloud CMS content setup and authoring.
These patterns help the consuming agent self-check its own output. Cites are to the Winter '27 (264) `api_meta` and `object_reference` guides.

UNVERIFIED (2026-10-20): Anti-Patterns 1, 3, 4, 5 and 6 restate Help-only behaviour (Knowledge versus CMS authoring surfaces, channel-assignment visibility, export/import, audience dropdowns, sandbox promotion); each is marked again inside.

## Anti-Pattern 1: Treating Knowledge Articles as CMS Content

**What the LLM generates:** Instructions that tell the user to create a Knowledge article to add content to their Experience Cloud site homepage, or that use Knowledge article creation steps when the user asked about CMS banners or news items.

**Why it happens:** Both Knowledge and CMS appear in Experience Cloud contexts, and LLM training data conflates them. Searches for "Salesforce CMS" or "Experience Cloud content" surface Knowledge article documentation because Knowledge is the more heavily documented content type.

**Correct pattern:**

```
CMS content (News, Image, Document, custom types) is a ManagedContent record in a CMS workspace
(object_reference 264 L180276-180279, L180343-180362) and is delivered through channels (L180406-180408).
Knowledge articles are a different object family. UNVERIFIED (2026-10-20): the Knowledge tab, data
categories, article types and the Knowledge component are Help-only here.
```

**Detection hint:** If the generated steps mention "Article Type", "Data Category", or the Knowledge tab when the user asked about CMS workspace content, this anti-pattern is present.

---

## Anti-Pattern 2: Advising Point-and-Click Creation of Custom Content Types

**What the LLM generates:** Instructions like "In Setup > Digital Experiences > Content Types, click New to create a custom content type and add your fields", or a ManagedContentType with invented element names such as `fieldType`, `label` and `name`.

**Why it happens:** LLMs generalize from other Salesforce declarative tools (custom objects, custom fields, custom metadata types) where point-and-click creation is available. They assume CMS custom types follow the same pattern.

**Correct pattern:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- excerpt: force-app/main/default/managedContentTypes/EventAnnouncement.managedContentType-meta.xml -->
<ManagedContentType xmlns="http://soap.sforce.com/2006/04/metadata">
    <developerName>EventAnnouncement</developerName>
    <masterLabel>Event Announcement</masterLabel>
    <managedContentNodeTypes>
        <nodeName>headline</nodeName>
        <nodeLabel>Headline</nodeLabel>
        <nodeType>NAMEFIELD</nodeType>
        <helpText>Event title</helpText>
        <isRequired>true</isRequired>
    </managedContentNodeTypes>
</ManagedContentType>
```

The element names are `nodeName`, `nodeLabel`, `nodeType` (api_meta 264 L89136-89161); one `NAMEFIELD` node with `isRequired` true is mandatory (L89221-89232). Deploy with: `sf project deploy start --source-dir force-app`

**Detection hint:** Any `<fieldType>`, `<label>` or `<name>` child inside `managedContentNodeTypes` is invented. UNVERIFIED (2026-10-20): that advice naming a Setup UI button or wizard is incorrect is Help-only; the corpus documents the metadata types and says nothing about an absent UI.

---

## Anti-Pattern 3: Recommending Content Publishing Without Channel Setup

**What the LLM generates:** Instructions to publish a CMS content item and then view it on the Experience Cloud site, skipping the step of creating and assigning a channel in the workspace.

**Why it happens:** The channel configuration step is an extra layer of indirection that LLMs skip when summarizing the workflow, especially if the model has seen tutorials that assume the channel already exists.

**Correct pattern:**

```
Before publishing content, verify:
1. A CMS workspace exists.
2. A channel whose Type is COMMUNITY delivers that workspace to the Experience Cloud site
   (object_reference 264 L180406-180408, L180515). ExperienceChannel is not a documented value.
3. The content variant is published (IsPublished true, L180707-180713).

UNVERIFIED (2026-10-20): that content published without a channel assignment is not delivered, and
that the Channel Assignments panel shows it, are Help-only.
```

**Detection hint:** If the workflow jumps from "publish the content item" to "the content appears on your site" without mentioning channel assignment, this anti-pattern is present.

---

## Anti-Pattern 4: Suggesting Metadata Deploy to Promote CMS Content Items Between Orgs

**What the LLM generates:** Instructions to add CMS content items to a SFDX source package, run `sf project deploy start`, and have the content appear in the target org.

**Why it happens:** LLMs know that Salesforce uses metadata deployment for most configuration promotion. They incorrectly generalize this to CMS content records, which are data, not metadata.

**Correct pattern:**

```
CMS content items are data records, not metadata files.
They are NOT part of the type metadata that sf project deploy carries (UNVERIFIED 2026-10-20: the exclusion is
Help-only; the corpus shows only that ManagedContent is a record).

To move content between orgs:
1. Deploy the custom content type definitions first (ManagedContentType XML, api_meta 264 L89072-89078;
   ContentTypeBundle for enhanced workspaces, L38404-38419).
2. Move the content records as a separate step; they are ManagedContent data, not type metadata
   (object_reference 264 L180276-180279).

UNVERIFIED (2026-10-20): the Workspace Export/Import screens and the REST paths
/services/data/vXX.0/connect/cms/content-items given by earlier versions of this skill are not in
the corpus. Do not recommend either without confirming it in a sandbox.
```

**Detection hint:** Any advice that includes CMS content items (news articles, images) in a SFDX package manifest or metadata deploy command is incorrect.

---

## Anti-Pattern 5: Configuring Audience Targeting Before Audiences Exist in the Site

**What the LLM generates:** Instructions to create a content variant and select an audience from the dropdown during content authoring, as if a CMS variant were audience-specific.

**Why it happens:** LLMs merge two features. A `ManagedContentVariant` is a language variant (object_reference 264 L180665-180670); an `Audience` targets experience variations, navigation link sets, reports or dashboards (api_meta 264 L26447-26452).

**Correct pattern:**

```
Audiences are defined per Experience Cloud site (Audience.container is the site, api_meta 264 L26256),
not in the CMS workspace.

Prerequisite order:
1. Define the Audience: criteria of type GeoLocation, Domain, Profile, FieldBased, Permission,
   Default or Audience (api_meta 264 L26322-26330), and a default audience (L26276-26280).
2. Add targets of targetType ExperienceVariation to the audience (L26447-26456) and deploy
   ExperienceBundle with it (L26426).
3. Treat the result as personalization, not security (L26595-26596).

UNVERIFIED (2026-10-20): the site Settings > Audience path, and an empty Target Audience dropdown
in CMS authoring, are Help-only.
```

**Detection hint:** If the output attaches an audience to a CMS content variant, it conflates language variants with audience targets.

---

## Anti-Pattern 6: Assuming Sandbox-Published Content Automatically Appears in Production

**What the LLM generates:** Advice that treats CMS content published in a sandbox as automatically available in production, or that suggests no additional steps are needed to make sandbox-authored content live in production after a metadata deploy.

**Why it happens:** Developers familiar with metadata-driven configuration assume that publishing or configuring something in sandbox makes it promotable via a standard deploy pipeline. CMS content items do not follow this model.

**Correct pattern:**

```
CMS content items are ManagedContent records (object_reference 264 L180276-180279); a metadata
deploy of type definitions does not create them in production.

To promote content to production:
1. Deploy the custom type metadata first.
2. Move the content records as a separate, rehearsed step.
3. After the move, confirm each variant's status and IsPublished (L180707-180713, L180762-180765)
   and the channel Type (L180507-180523) in production.

UNVERIFIED (2026-10-20): that sandbox-published content "stays in that sandbox" and the Export/Import
tooling are Help-only.
```

**Detection hint:** If a content promotion workflow mentions only `sf project deploy` without an explicit CMS Export/Import step, this anti-pattern is present.
