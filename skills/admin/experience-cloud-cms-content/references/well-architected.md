# Well-Architected Notes — Experience Cloud CMS Content

## Relevant Pillars

- **Operational Excellence** — CMS workspaces enable content governance by separating content authoring from page development. Managed content with version history, approval roles, and scheduling reduces operational risk around content launches and allows rollback without a deployment.
- **User Experience** — Audience-targeted content variants ensure each user segment sees the most relevant content without site administrators maintaining separate pages per audience. Scheduling eliminates manual launch steps that introduce human error and missed windows.
- **Adaptability** — Managed content and custom content types defined via the Metadata API are portable across environments and promotable through a deployment pipeline. This keeps content governance aligned with standard DevOps practices rather than manual re-entry between orgs.
- **Security** — CMS workspace roles (Content Admin, Content Manager, Content Author) enforce least-privilege access to content creation and publishing. Content that is published but not assigned to a channel remains inaccessible to site visitors, providing a natural staging gate.

## Architectural Tradeoffs

**Managed vs. unmanaged content:** Managed content requires more upfront setup (workspace creation, channel configuration) but pays off for any content that will be reused, scheduled, targeted, or governed. Unmanaged content is faster to create but becomes a governance liability at scale — no centralized view, no scheduling, no audience targeting, no sandbox resilience.

**Standard vs. custom content types:** Standard types (News, Banner, Image) cover the majority of portal content needs and require no deployment. Custom types unlock structured authoring for complex content (product listings, event details, FAQs with structured fields), but they require a Metadata API deployment and developer involvement to define and maintain. Use custom types only when the standard schema is genuinely insufficient.

**CMS scheduling vs. Flow/Process Builder:** CMS native scheduling is sufficient for the vast majority of timed content launches and unpublishes. Avoid building Flow or Apex automation to swap CMS content on a schedule — it creates invisible dependencies and bypasses the content versioning and audit trail.

## Anti-Patterns

1. **Using unmanaged content for production-grade portal content** — Unmanaged content cannot be scheduled, targeted, versioned via the CMS workspace, or promoted between environments. At scale it creates a content inventory that is invisible to the CMS governance layer, making audits and updates manual and error-prone. Always use managed content for portal content that has any governance, scheduling, or reuse requirement.

2. **Manually managing content publishing through Flows or custom Apex** — Some teams build automation to swap or modify CMS content on a schedule using custom Apex or Flow. This bypasses native CMS scheduling, breaks the content version history, and creates hidden operational dependencies. Use native CMS scheduling and audience targeting for all timing and personalization needs within the CMS layer.

3. **Skipping channel setup and hardcoding content in Experience Builder** — Teams in a hurry skip the CMS workspace and channel configuration and hardcode content into Experience Builder page properties or static resources. This puts content under developer control, requires a deployment for every content change, and eliminates audience targeting and scheduling. The short-term speed gain creates long-term operational debt.

## Official Sources Used

- Salesforce CMS and Digital Experiences App — https://help.salesforce.com/s/articleView?id=sf.cms_home.htm
- CMS Content Types — https://help.salesforce.com/s/articleView?id=sf.cms_content_types.htm
- CMS Developer Guide (Managed Content REST API) — https://developer.salesforce.com/docs/atlas.en-us.cms_dev.meta/cms_dev/cms_dev_intro.htm
- Content Publication Schedules — https://help.salesforce.com/s/articleView?id=sf.cms_publish_schedule.htm
- Metadata API Developer Guide (ManagedContentType) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
