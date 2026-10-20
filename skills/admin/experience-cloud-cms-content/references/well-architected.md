# Well-Architected Notes — Experience Cloud CMS Content

## Relevant Pillars

- **Operational Excellence** — CMS workspaces enable content governance by separating content authoring from page development. Managed content carries variants with a Draft, Published or Revised status (object_reference 264 L180762-180765), which reduces operational risk around content launches. UNVERIFIED (2026-10-20): approval roles, native scheduling and rollback without a deployment are Help-only.
- **User Experience** — Audiences target experience variations so each segment can see a relevant version of a page section without separate pages per audience (api_meta 264 L26447-26452). UNVERIFIED (2026-10-20): that scheduling removes manual launch steps is Help-only.
- **Adaptability** — Custom content types defined via the Metadata API (`ManagedContentType`, api_meta 264 L89072-89078; `ContentTypeBundle`, L38404-38419) are promotable through a deployment pipeline. UNVERIFIED (2026-10-20): that managed content itself is portable between environments is Help-only; content items are records (object_reference 264 L180276-180279).
- **Security** — Workspace users and groups with designated permissions manage the content (object_reference 264 L180558-180559); the channel `Type` controls which audience can read it (L180512-180523). Audience targeting is personalization and does not secure data (api_meta 264 L26595-26596). UNVERIFIED (2026-10-20): the workspace roles Content Admin, Content Manager and Content Author, and the "unassigned content is inaccessible" staging gate, are Help-only.

## Architectural Tradeoffs

**Managed vs. unmanaged content:** Managed content requires more upfront setup (workspace creation, channel configuration) but pays off for any content that will be reused or governed. UNVERIFIED (2026-10-20): that unmanaged content has no centralized view, scheduling, targeting or sandbox resilience is Help-only.

**Standard vs. custom content types:** Standard types (News, Image, Document; object_reference 264 L180343-180362) cover simple content needs and require no deployment. Custom types unlock structured authoring for complex content (product listings, event details, FAQs with structured fields), but they require a Metadata API deployment and developer involvement to define and maintain. Use custom types only when the standard schema is genuinely insufficient.

**CMS scheduling vs. Flow:** UNVERIFIED (2026-10-20): native CMS scheduling is Help-only. The metadata does provide flow actions that publish or unpublish a content variant (`managedContentPublishVariant`, `managedContentUnpublishVariant`, api_meta 264 L71645-71650); decide deliberately between native scheduling and those actions, and document the dependency either way.

## Anti-Patterns

1. **Using unmanaged content for production-grade portal content** — UNVERIFIED (2026-10-20): that unmanaged content cannot be scheduled, targeted, versioned or promoted is Help-only. A managed item is a `ManagedContent` record that supports variants over time (object_reference 264 L180277-180279); use it for portal content with any governance or reuse requirement.

2. **Hand-built automation that swaps CMS content without recording the dependency** — Custom Apex or Flow that changes published content creates hidden operational dependencies. UNVERIFIED (2026-10-20): that it bypasses native scheduling and breaks version history is Help-only. Prefer the documented publish and unpublish variant flow actions (api_meta 264 L71645-71650) and record where they run.

3. **Skipping channel setup and hardcoding content in Experience Builder** — Teams in a hurry skip the CMS workspace and channel configuration and hardcode content into Experience Builder page properties or static resources. This puts content under developer control and requires a deployment for every content change. The short-term speed gain creates long-term operational debt.

## Official Sources Used

- ManagedContentType fields, node types and limits — api_meta 264 L89063-89292 (the 15-node maximum L89160, the single NAMEFIELD L89221-89232, the sample L89243-89292)
- ContentTypeBundle for enhanced custom content types (API 64.0 and later) — api_meta 264 L38391-38419
- Standard content types and fully qualified names — object_reference 264 L180343-180365; ManagedContent L180276-180279
- ManagedContentChannel `Type` values — object_reference 264 L180507-180523; ManagedContentVariant (language variants, status) L180665-180670, L180762-180765
- Audience, criteria and ExperienceVariation targets — api_meta 264 L26225-26283, L26322-26330, L26426, L26447-26452, L26595-26596
- Salesforce CMS and Digital Experiences App — https://help.salesforce.com/s/articleView?id=sf.cms_home.htm
- CMS Content Types — https://help.salesforce.com/s/articleView?id=sf.cms_content_types.htm
- CMS Developer Guide (Managed Content REST API) — https://developer.salesforce.com/docs/atlas.en-us.cms_dev.meta/cms_dev/cms_dev_intro.htm
- Content Publication Schedules — https://help.salesforce.com/s/articleView?id=sf.cms_publish_schedule.htm — UNVERIFIED (2026-10-20): Help page, not fetchable; it is the only source for per-item scheduling
- Metadata API Developer Guide (ManagedContentType) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
