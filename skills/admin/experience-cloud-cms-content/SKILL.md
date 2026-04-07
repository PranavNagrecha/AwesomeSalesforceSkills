---
name: experience-cloud-cms-content
description: "Use when setting up CMS workspaces, creating or publishing content types for Experience Cloud sites, managing content scheduling, or configuring audience targeting on content variants. Triggers: 'set up CMS workspace', 'publish content to Experience Cloud site', 'content scheduling community', 'audience targeting content', 'managed content vs unmanaged', 'custom content type metadata', 'CMS channel configuration'. NOT for Salesforce Knowledge articles, CMS Connect to external CMS platforms, or Experience Builder layout/theming work."
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
  - "content types needed (standard: news, banner, image; or custom)"
  - "audience segments for targeting if variants are required"
  - "content scheduling requirements (publish date, expiry date)"
  - "whether content is managed (shared via channels) or unmanaged (site-local)"
outputs:
  - "CMS workspace configuration with correct channel assignments"
  - "content type definitions for standard or custom types"
  - "publishing workflow guidance including scheduling and audience variant setup"
  - "review checklist for CMS content readiness before go-live"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Experience Cloud CMS Content

Use this skill when setting up Salesforce CMS workspaces, defining content types, publishing managed content to Experience Cloud sites, or configuring content scheduling and audience targeting. This skill covers the native Salesforce CMS authoring surface accessed through the Digital Experiences app. It does not cover Salesforce Knowledge articles, CMS Connect to external headless CMS platforms, or Experience Builder page layout and theming.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the target site LWR (Lightning Web Runtime) or Aura-based? LWR sites require the CMS content component; Aura sites use the CMS Single Item or Collection components. Channel type must match the site type.
- Is the content managed (shared across multiple sites via a CMS channel) or unmanaged (authored directly within a single site)? Managed content is portable; unmanaged content is tied to one site and cannot be reused.
- Does the org have the Digital Experiences app enabled? CMS workspaces live in the Digital Experiences app, not in the classic Setup tree. Admins need the Manage Experiences or Create and Set Up Experiences permission.

---

## Core Concepts

### CMS Workspaces

A CMS workspace is the organizational container for all CMS content in an org. Workspaces are created through the Digital Experiences app (App Launcher > Digital Experiences). Each workspace holds content items, manages contributor access, and is linked to one or more channels. A single org can have multiple workspaces to separate content by brand, language, or business unit. Workspace membership controls who can create, edit, approve, and publish content; workspace roles include Content Admin, Content Manager, and Content Author.

### Content Types

Salesforce CMS ships with three standard content types: News (text-rich articles with a title, body, summary, and banner image), Banners (promotional image content with a title, body text, and image), and Images (standalone image assets with alt text). Custom content types extend these with org-specific fields and are defined through the Metadata API using the `ManagedContentType` metadata type or through the Tooling API. Custom types are not configurable through point-and-click Setup; they require a metadata deployment. Each content item is versioned: draft, published, and archived are the available lifecycle states.

### CMS Channels

A CMS channel connects a workspace to a delivery endpoint — either an Experience Cloud site or a public API endpoint for headless delivery. Channels have a type: `ExperienceChannel` for Experience Cloud sites or `PublicChannel` for headless API delivery. The channel type must match the site's runtime. Content is not visible to site visitors until it is published and assigned to the correct channel. A single workspace can serve multiple channels; content can be shared across channels without duplication.

### Content Scheduling and Audience Targeting

Content items support publish scheduling: a scheduled publish date queues a draft for automatic publication, and a scheduled unpublish date automatically archives a live item. Scheduling is set per content item, not at the workspace level. Audience targeting applies to content variants — a single content item can have multiple variants, each targeted to a named audience defined in Experience Cloud. Variant-level targeting means different users see different versions of the same content item based on audience membership. Audiences are defined in the Experience Cloud site's audience configuration and then referenced on the content variant.

### Managed vs. Unmanaged Content

Managed content lives in a CMS workspace and is published to sites through channels. It is versioned, reusable across multiple sites, and portable across sandboxes via metadata deployment. Unmanaged content is authored directly within an Experience Builder site and is not accessible from the CMS workspace. Unmanaged content cannot be shared across sites, is not promoted through a channel, and does not participate in CMS versioning or scheduling. New implementations should default to managed content for any content intended to be reused or governed.

---

## Common Patterns

### Pattern 1: Standard Content Types for a Portal Homepage

**When to use:** A portal needs a rotating banner, a news feed, and featured images managed by a content team without developer involvement.

**How it works:** Create a CMS workspace in Digital Experiences. Add the portal site as a channel of type `ExperienceChannel`. Create Banner content items for the rotating hero area and News items for the feed. In Experience Builder, drop the CMS Single Item component onto the page and bind it to the Banner content. Drop the CMS Collection component for the news feed and configure the collection filter. Content authors update CMS items without touching the page layout.

**Why not the alternative:** Hardcoding content in Experience Builder page properties or static resources ties content updates to a developer deploy. CMS-backed components let content authors publish independently of the page structure.

### Pattern 2: Scheduled Seasonal Content with Audience Targeting

**When to use:** A seasonal promotion should appear for loyalty-tier customers starting on a specific date and expire automatically, while non-members see a default banner.

**How it works:** Define two audiences in Experience Cloud: `LoyaltyTierMembers` and `AllVisitors`. Create a Banner content item with two variants: the seasonal variant targeted to `LoyaltyTierMembers` with a scheduled publish and unpublish date, and the default variant targeted to `AllVisitors` with no schedule. Publish the content item. The platform automatically switches variant visibility on the scheduled dates without any further admin action.

**Why not the alternative:** Manually swapping page components on a schedule requires deployment windows and developer access. CMS scheduling + variants handles this entirely within the content layer.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Content will be reused across multiple sites | Managed content via CMS workspace + channels | Single source of truth; changes propagate to all channels |
| Content is site-specific and not shared | Unmanaged content in Experience Builder | Lower overhead; no workspace or channel setup required |
| Custom fields are needed beyond News/Banner/Image | Custom content type via Metadata API deployment | Standard types have fixed schemas; custom types add org-specific fields |
| Content should publish automatically on a future date | Per-item schedule on the content variant | Scheduling is built into the content item; no Flow or automation needed |
| Different user segments should see different content | Audience-targeted content variants | Define audiences in Experience Cloud and reference on each variant |
| Content needs to be promoted from sandbox to production | Managed content via metadata deployment | Managed content and custom type definitions are promotable via SFDX/CLI |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify Digital Experiences and CMS prerequisites** -- Confirm the Digital Experiences app is enabled. Check that the admin has Manage Experiences permission. Identify the target site's runtime (LWR or Aura) because this determines the correct channel type and Experience Builder CMS components to use.
2. **Create or verify the CMS workspace** -- In Digital Experiences, open Workspaces and create a new workspace (or confirm one exists for this content domain). Add the target Experience Cloud site as a channel. Confirm the channel type matches the site runtime.
3. **Define content types** -- Identify whether standard types (News, Banner, Image) are sufficient. If custom fields are needed, author the `ManagedContentType` metadata and deploy via SFDX or Metadata API before attempting to create content items of that type.
4. **Author and stage content items** -- Create content items in the workspace. Set variant targeting if audience-specific content is required. Set publish and unpublish schedules on variants if timed delivery is needed. Save as draft until ready.
5. **Publish content to the channel** -- Publish each content item (or use bulk publish from the workspace view). Confirm the item status changes to Published and the channel is listed under the item's channel assignments.
6. **Wire content to Experience Builder components** -- In Experience Builder, add CMS Single Item or CMS Collection components to the target page. Bind them to the published content items or collections. Preview in the correct audience context to verify variant targeting renders correctly.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] CMS workspace exists and the target Experience Cloud site is added as a channel with the correct channel type
- [ ] Custom content types have been deployed via Metadata API before content items of that type are created
- [ ] All content items are in Published status and assigned to the correct channel (not just saved as draft)
- [ ] Audience-targeted variants reference defined audiences from the site's audience configuration
- [ ] Scheduled publish/unpublish dates are set in the org's local timezone and confirmed in the content item's schedule panel
- [ ] Experience Builder components are bound to managed content items (not hardcoded text or static resources)
- [ ] Content rendering is verified in Experience Builder preview under the target audience context

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Custom content types require a Metadata/Tooling API deployment — there is no declarative UI** -- The `ManagedContentType` metadata type must be authored as XML and deployed via SFDX, Metadata API, or the Tooling API. Admins expecting a Setup wizard or a New Content Type button in Digital Experiences will not find one. Attempting to create content items of an undefined type fails silently in some org versions.
2. **Channel type mismatch causes content to be invisible** -- A channel configured as `PublicChannel` will not deliver content to an LWR or Aura Experience Cloud site. The channel type must be `ExperienceChannel` for site delivery. Mis-configured channels produce no error — content simply does not appear. Verify channel type in Digital Experiences > Workspace > Channels.
3. **Publishing to a sandbox does not replicate to production** -- Managed content items are not promoted automatically between environments. CMS content must be exported from the source org and imported into the target, or re-authored. Custom content type metadata is promotable via deployment, but content item data is not metadata — it requires CMS export/import tooling or manual re-entry.
4. **Unmanaged content is lost in sandbox refreshes** -- Unmanaged content authored directly in an Experience Builder site is stored as site-local data. A full sandbox refresh overwrites it. Organizations that use unmanaged content for non-trivial content must document a re-entry process after each refresh.
5. **Audience targeting requires audiences to exist before content is created** -- Audiences are defined in the Experience Cloud site settings, not in the CMS workspace. If a content author tries to target a variant to an audience that has not been created yet, the audience selection dropdown is empty and there is no inline creation path. Audiences must be set up in the site configuration first.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| CMS workspace configuration | Workspace name, contributor roles, and channel assignments documented for handoff |
| Content type inventory | List of standard and custom content types in use with field definitions for custom types |
| Content publishing checklist | Per-item checklist confirming channel assignment, variant targeting, scheduling, and published status |
| Audience targeting matrix | Table mapping content variants to audience definitions and scheduled dates |

---

## Related Skills

- knowledge-vs-external-cms — Use when the broader question is whether to use Salesforce CMS, Salesforce Knowledge, or an external CMS platform for a given content strategy
- experience-cloud-site-setup — Use when the Experience Cloud site itself needs to be created, configured, or connected to a CMS workspace for the first time
