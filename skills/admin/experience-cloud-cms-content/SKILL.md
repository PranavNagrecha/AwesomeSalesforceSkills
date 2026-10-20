---
name: experience-cloud-cms-content
description: "Use when setting up CMS workspaces, creating or publishing content types for Experience Cloud sites, managing content scheduling, or configuring audience targeting on content variants. Triggers: 'set up CMS workspace', 'publish content to Experience Cloud site', 'content scheduling community', 'audience targeting content', 'managed content vs unmanaged', 'custom content type metadata', 'CMS channel configuration'. NOT for moderating member-posted content — use admin/experience-cloud-moderation. NOT for Knowledge vs an external CMS or CMS Connect — use architect/knowledge-vs-external-cms."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - User Experience
  - Reliability
triggers:
  - "how do I set up a CMS workspace for my Experience Cloud site"
  - "publish content to a community or portal with scheduling and audience targeting"
  - "create a custom content type for CMS in Experience Cloud"
  - "content is not showing on my Experience Cloud site after publishing"
  - "how do I manage content versions and scheduling in Salesforce CMS"
tags:
  - experience-cloud-cms-content
  - cms-workspace
  - managed-content
  - content-types
  - audience-targeting
  - content-scheduling
  - digital-experiences
inputs:
  - "target Experience Cloud site type (LWR, Aura, or both)"
  - "content types needed (standard: news, image, document; or custom)"
  - "audience segments for targeting experience variations if personalization is required"
  - "content scheduling requirements (publish date, expiry date; UNVERIFIED 2026-10-20, Help-only)"
  - "whether content is managed (workspace and channels) or unmanaged (UNVERIFIED 2026-10-20: Help-only distinction)"
outputs:
  - "CMS workspace configuration with correct channel assignments"
  - "content type definitions for standard or custom types"
  - "publishing workflow guidance including audience targeting setup (scheduling is UNVERIFIED 2026-10-20, Help-only)"
  - "review checklist for CMS content readiness before go-live"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Experience Cloud CMS Content

Use this skill when setting up Salesforce CMS workspaces, defining content types, publishing managed content to Experience Cloud sites, or configuring content scheduling and audience targeting. This skill covers the native Salesforce CMS authoring surface accessed through the Digital Experiences app. It does not cover Salesforce Knowledge articles, CMS Connect to external headless CMS platforms, or Experience Builder page layout and theming.

Cites: `api_meta` and `object_reference` are the Winter '27 (264) guides; line numbers are those files'.

---

## Before Starting

Gather this context before working on anything in this domain:

- Which runtime is the target site: enhanced LWR, LWR or Aura? Enhanced custom content types (`ContentTypeBundle`, API 64.0 and later) are available for enhanced LWR site channels; to use them with Aura and non-enhanced LWR channels you use the enhanced CMS workspaces delivery resources (api_meta 264 L38391-38394, L38418-38419, L38649-38650). Classic custom types use `ManagedContentType` (API 47.0 and later, api_meta 264 L89078). UNVERIFIED (2026-10-20): which Experience Builder CMS components (Single Item, Collection, Content) each runtime uses is Help-only.
- Is the content managed (authored in a CMS workspace and delivered through channels) or unmanaged (authored directly in the site)? UNVERIFIED (2026-10-20): the managed/unmanaged distinction, that unmanaged content is site-local and non-reusable, and that managed content is portable, is Help-only; the corpus describes only managed content (`ManagedContent`, object_reference 264 L180276-180279).
- Is the Digital Experiences app enabled? `ManagedContent`, `ManagedContentChannel`, `ManagedContentSpace` and `ManagedContentVariant` are available when it is (object_reference 264 L180287, L180416, L180567, L180678), and `ManagedContentType` is available only if Salesforce CMS and digital experiences are enabled (api_meta 264 L89082). UNVERIFIED (2026-10-20): the Manage Experiences / Create and Set Up Experiences permission for CMS authoring (the corpus names it for keyword lists and moderation rules, api_meta 264 L84946, L92242) and "not in the classic Setup tree" are Help-only for CMS.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Is the site enhanced LWR, LWR or Aura? | The content type metadata (`ManagedContentType` or `ContentTypeBundle`) and the channel delivery path depend on it (Core Concept 2) | One runtime per site and the matching type metadata |
| Which channel type does the workspace deliver through? | `COMMUNITY`, `PublicUnauthenticated`, `ConnectedApp` and the others give different audiences access (Core Concept 3; gotchas.md Gotcha 2) | A named channel `Type` per site, checked in the Digital Experiences app |
| Are the standard types enough, or do we need fields beyond News, Image and Document? | Custom types need a metadata deployment and a detail page per type (gotchas.md Gotcha 1) | A node list: `nodeName`, `nodeLabel`, `nodeType`, exactly one `NAMEFIELD` |
| Which content must move from sandbox to production, and how? | Content records are not part of the type metadata deploy (gotchas.md Gotcha 3) | An export/import or API step in the release runbook |
| Which audiences exist in the site, and what do they target? | An audience targets experience variations, navigation link sets, reports or dashboards, not language variants (Core Concept 4; Gotcha 5) | An audience matrix with criteria and target types |
| What publish and unpublish times are needed, in which timezone? | Scheduling and its timezone are Help-only behaviours (gotchas.md Gotcha 4) | A tested schedule on a non-production item, with the timezone written down |
| Is any content authored directly in the site rather than in a workspace? | Site-local content is outside the workspace model and the refresh behaviour is unverified (gotchas.md Gotcha 5) | An inventory of unmanaged content and a re-entry plan |

A proper configuration names the runtime, channel type, type metadata and audience targets up front; "just doing it" publishes into whatever channel exists and finds the gaps on the live site.

---

## Core Concepts

### 1. CMS Workspaces

`ManagedContentSpace` represents the complete instance of a Salesforce CMS workspace that stores managed content; users and groups with designated permissions can access and manage the content in it (object_reference 264 L180558-180559). An enhanced workspace has an `ApiName` of 40 characters or fewer, starting with a letter, with only underscores and alphanumerics, no spaces, no trailing underscore and no two consecutive underscores (L180577-180583), and a `DefaultLanguage` (L180585-180590).

UNVERIFIED (2026-10-20): that workspaces are created from App Launcher > Digital Experiences, that one org can hold several workspaces split by brand, language or business unit, and the workspace roles Content Admin, Content Manager and Content Author are Help-only; no corpus line names those roles.

### 2. Content Types

The standard content types are News, Image and Document: `ContentTypeFullyQualifiedName` is `news`, `cms_image` and `cms_document` in a CMS workspace, and `sfdc_cms__news`, `sfdc_cms__image` and `sfdc_cms__document` in an enhanced CMS workspace (object_reference 264 L180343-180362). There is no standard Banner type. A custom type's fully qualified name is its developer name (L180363-180365).

A custom content type is a `ManagedContentType` (suffix `managedContentType`, folder `managedContentTypes`, API 47.0 and later; api_meta 264 L89072-89078): "displayed as forms with defined fields" (L89064-89065). Each field is a `managedContentNodeTypes` entry with `nodeName`, `nodeLabel` and `nodeType` required (L89136-89161); there is a maximum of 15 node types per content type (L89160), and one and only one node must be `NAMEFIELD`, which requires `isRequired` true (L89221-89232). For enhanced workspaces the type is a `ContentTypeBundle` (API 64.0 and later), a folder per type with a `schema.json` (api_meta 264 L38404-38419). For each custom type there must also be a CMS content page in the site that serves as the detail page for that type (api_meta 264 L89296-89299, L38646-38648).

A managed content variant carries a publication status of Draft, Published or Revised (object_reference 264 L180762-180765).

UNVERIFIED (2026-10-20): that custom types cannot be created from a Setup or Digital Experiences wizard, that the Tooling API can define them, and that a type must be deployed before its items can be authored are Help-only or unstated; the corpus documents the metadata types and says nothing about an absent UI. UNVERIFIED (2026-10-20): the earlier text listed an "archived" lifecycle state; the corpus lists Draft, Published and Revised.

### 3. CMS Channels

A CMS channel is a managed content publishing endpoint that delivers published content from workspaces to an audience (`ManagedContentChannel`, object_reference 264 L180406-180408). Its `Type` is the connection type, which determines which audience can access the content: `COMMUNITY` (access follows the Experience Cloud site's settings), `CloudToCloud`, `ConnectedApp`, `PublicUnauthenticated` (no authentication; cacheable on public CDNs), `Record`, and `UserPermission` (reserved for future use) (L180507-180523). Only public channels can have an assigned domain (L180434). The channel's `Domain` is a `mydomain.cdn.salesforce-experience.com` value (L180435-180436).

The channel type names `ExperienceChannel` and `PublicChannel` that this skill used earlier do not appear in the corpus; use `COMMUNITY` for Experience Cloud site delivery and `PublicUnauthenticated` for headless public delivery.

UNVERIFIED (2026-10-20): that the channel type "must match the site's runtime", that mismatched content is silently invisible, that one workspace serves several channels without duplication, and that the channel type cannot be edited in place are Help-only.

### 4. Variants, Scheduling and Audience Targeting

A `ManagedContentVariant` is a variant of a managed content item: for example, translating News content into Spanish, Japanese and French creates a variant per language (object_reference 264 L180665-180670), and it has a `Language` field (L180716-180721). Variants are language variants, not audience variants.

Audiences are a separate metadata type: `Audience` "represents the audience in an Experience Builder site", used for targeting in a site (api_meta 264 L26225-26227), with a `container` (the site, L26256), `criteria` of type GeoLocation, Domain, Profile, FieldBased, Permission, Default or Audience (L26322-26330) and an `isDefaultAudience` flag (L26276-26280). An audience's `targets` have a `targetType` of ExperienceVariation, NavigationLinkSet, Report or Dashboard (L26447-26452); a content item or content variant is not a listed target type. Deploying an audience with experience variation targets requires ExperienceBundle in the package (L26426). Personalization by audience "varies what the user can see in the browser but doesn't secure data in any way" (L26595-26596).

UNVERIFIED (2026-10-20): per-item publish and unpublish schedules, that scheduling uses the org timezone, and any audience selection on a CMS content variant are Help-only; `ManagedContentVariant` has no schedule or audience field (object_reference 264 L180683-180780), and the CMS flow actions publish, unpublish, lock, mark ready for publication, or assign for review a variant (`managedContentPublishVariant`, `managedContentUnpublishVariant`, `managedContentVariantSetLockStatus`, `managedContentVariantSetReadyStatus`, `managedContentRoleStepInteractive`; api_meta 264 L71641-71656); none of them is a schedule.

### 5. Managed vs. Unmanaged Content

Managed content is the `ManagedContent` record (a consistent identifier so that variants can be created over time; object_reference 264 L180277-180279) in a workspace, delivered through channels. UNVERIFIED (2026-10-20): the unmanaged-content half of this distinction (authored directly in an Experience Builder site, site-local, no versioning or scheduling, lost on sandbox refresh) and the default-to-managed advice are Help-only.

---

## Common Patterns

### Pattern 1: Standard Content Types for a Portal Homepage

**When to use:** A portal needs a hero image area and a news feed managed by a content team without developer involvement.

**How it works:** Create a CMS workspace. Make sure a channel of `Type` `COMMUNITY` delivers it to the portal site. Create Image items for the hero area and News items for the feed (the standard types are News, Image and Document). In Experience Builder, bind CMS components on the page to the items and the collection. UNVERIFIED (2026-10-20): the CMS component names and the binding steps are Help-only. Content authors update CMS items without touching the page layout.

**Why not the alternative:** Hardcoding content in Experience Builder page properties or static resources ties content updates to a developer deploy.

### Pattern 2: Audience-Targeted Experience Variation

**When to use:** One section of a site should differ for loyalty-tier customers, with everyone else seeing a default.

**How it works:** Define the audiences as `Audience` metadata with the site as `container`, one default audience, and FieldBased, Profile or Permission criteria (api_meta 264 L26225-26330). Add `PersonalizationTargetInfo` targets of `targetType` `ExperienceVariation` that pair each audience with a variation (L26434-26456), and include ExperienceBundle in the deployment (L26426). Treat the result as personalization, not security (L26595-26596). Language versions of the content itself are `ManagedContentVariant` records (object_reference 264 L180665-180670). UNVERIFIED (2026-10-20): timed switching on given dates is Help-only.

**Why not the alternative:** Manually swapping page components needs deployment windows and developer access.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Content will be reused across multiple sites | Managed content in a CMS workspace, delivered through channels | Channels deliver published content from workspaces to an audience (object_reference 264 L180407-180408) |
| Content is site-specific and not shared | Managed content still; unmanaged is UNVERIFIED (2026-10-20) | The unmanaged model is Help-only |
| Custom fields are needed beyond News/Image/Document | `ManagedContentType` (or `ContentTypeBundle` for enhanced workspaces) deployed as metadata | Standard types are fixed (object_reference 264 L180343-180362); custom types are metadata (api_meta 264 L89064, L38391) |
| Content should publish automatically on a future date | Per-item schedule, UNVERIFIED (2026-10-20) | Help-only; not in the object model |
| Different user segments should see different content | `Audience` + `ExperienceVariation` target | Audiences target experience variations, not CMS variants (api_meta 264 L26447-26452) |
| Content needs to move from sandbox to production | Deploy type metadata; move content records separately | Content records are `ManagedContent` data, not type metadata (object_reference 264 L180276-180279). UNVERIFIED (2026-10-20): the export/import tooling is Help-only |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify Digital Experiences and CMS prerequisites** -- Confirm the Digital Experiences app is enabled (object_reference 264 L180287). Identify the site runtime (enhanced LWR, LWR or Aura) because it decides the type metadata and the delivery path (Before Starting).
2. **Create or verify the CMS workspace and channel** -- Query `ManagedContentSpace` and `ManagedContentChannel` (both support `query()`, object_reference 264 L180563, L180412) and confirm the channel `Type` is `COMMUNITY` for site delivery.
3. **Define content types** -- Decide whether News, Image and Document are enough. If custom fields are needed, author `ManagedContentType` (or `ContentTypeBundle` for enhanced workspaces) and run `python3 scripts/check_experience_cloud_cms_content.py --manifest-dir <metadata dir>` before deploying it.
4. **Author and stage content items** -- Create items in the workspace; use variants for languages. Keep items Draft until ready (status Draft, Published or Revised, object_reference 264 L180762-180765).
5. **Publish content to the channel** -- Publish and confirm `IsPublished` is true on the variant (object_reference 264 L180707-180713).
6. **Wire content and audiences** -- In Experience Builder, bind CMS components to the published items; deploy `Audience` metadata with targets for any audience-specific variation (Pattern 2). UNVERIFIED (2026-10-20): component names and preview modes are Help-only.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] A CMS workspace exists and a channel of `Type` `COMMUNITY` delivers it to the target site
- [ ] Custom content types are deployed (`ManagedContentType` or `ContentTypeBundle`), each has exactly one `NAMEFIELD` node, and each has a detail page in the site
- [ ] Items are published: `ManagedContentVariantStatus` is Published and `IsPublished` is true, not just Draft
- [ ] Audience-specific experience variations are targeted by `Audience` metadata deployed with ExperienceBundle
- [ ] Any scheduled publish or unpublish dates were tested on a non-production item (UNVERIFIED 2026-10-20: scheduling is Help-only)
- [ ] Experience Builder components are bound to managed content items, not hardcoded text or static resources
- [ ] Rendering is verified in a preview for each audience (UNVERIFIED 2026-10-20: the preview modes are Help-only)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Custom content types are metadata.** `ManagedContentType` is authored as XML and `ContentTypeBundle` as a `schema.json` folder, then deployed. Each custom type also needs a content page in the site. UNVERIFIED (2026-10-20): that there is no point-and-click alternative, and that items of an undefined type fail silently, are not stated in the corpus.
2. **Channel `Type` decides who can read the content.** `COMMUNITY` follows the site's access settings; `PublicUnauthenticated` needs no authentication (object_reference 264 L180512-180523). A channel of the wrong type delivers to the wrong audience. UNVERIFIED (2026-10-20): that a mismatch is silent and shows Published status with no content is Help-only.
3. **Content records do not travel with the type metadata.** Type definitions deploy; `ManagedContent` records are data (object_reference 264 L180276-180279). UNVERIFIED (2026-10-20): the export/import tooling and the scripted route are Help-only.
4. **Unmanaged content and sandbox refresh.** UNVERIFIED (2026-10-20): that unmanaged content is lost when a sandbox is refreshed is Help-only.
5. **Audiences must exist before they can be targeted.** An `Audience` belongs to a site container (api_meta 264 L26256) and the target pairs an audience with a variation (L26438-26456). UNVERIFIED (2026-10-20): that a CMS authoring dropdown stays empty until audiences exist is Help-only.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| CMS workspace configuration | Workspace name, channel `Type` and site delivery documented for handoff |
| Content type inventory | Standard and custom types in use, with the node list for each custom type |
| Content publishing checklist | Per-item checklist confirming channel, status and published flag |
| Audience targeting matrix | Table mapping audiences to criteria and to their `ExperienceVariation` (or other) targets |

---

## Related Skills

- `architect/knowledge-vs-external-cms` -- Use when the broader question is whether to use Salesforce CMS, Salesforce Knowledge, or an external CMS platform for a given content strategy
- `admin/experience-cloud-site-setup` -- Use when the Experience Cloud site itself needs to be created, configured, or connected to a CMS workspace for the first time
