# Gotchas — Experience Cloud CMS Content

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Custom Content Types Have No Declarative Setup UI

**What happens:** Admins who try to define a custom CMS content type through the Digital Experiences app or Setup UI find no option to do so. The platform provides no New Content Type button or wizard. Attempts to create content items of a custom type before the type is deployed result in the type not appearing in the Add Content dropdown.

**When it occurs:** Any time an org needs content fields beyond the fixed schemas of News, Banner, and Image. This affects nearly every production CMS implementation that goes beyond simple announcements.

**How to avoid:** Author the `ManagedContentType` metadata XML and deploy it via SFDX (`sf project deploy start`) or via the Metadata API Retrieve/Deploy cycle before any content authoring work begins. The custom type appears in the workspace Add Content menu only after a successful deployment. Use the Tooling API as an alternative if a programmatic approach is preferred over a file-based deploy.

---

## Gotcha 2: Channel Type Must Match the Site Runtime

**What happens:** Content published to a workspace does not appear on the target Experience Cloud site. No error is surfaced in the UI. The content item shows Published status and the channel appears to be configured correctly, but site visitors (and Experience Builder preview) show no content.

**When it occurs:** When the CMS channel is configured with the wrong type — typically `PublicChannel` (intended for headless API delivery) instead of `ExperienceChannel` (required for Experience Cloud site delivery). This most often happens when a channel is copied or configured by someone following headless CMS documentation instead of Experience Cloud documentation.

**How to avoid:** In Digital Experiences > Workspace > Channels, confirm each channel's type. For Experience Cloud sites, the type must be `ExperienceChannel`. Delete and recreate the channel if the type is wrong — there is no in-place edit for channel type. After correcting the channel, republish content items to refresh the channel assignment.

---

## Gotcha 3: CMS Content Data Does Not Promote Between Environments via Metadata Deploy

**What happens:** A developer deploys a SFDX project from sandbox to production and the CMS content items are absent in production. The custom content type metadata deploys correctly, but the authored content (the Banner text, images, and News articles) is not included.

**When it occurs:** Any time a team treats CMS content items as if they are metadata. Content items are data records in the Salesforce database, not metadata files in a source package. `sf project deploy` only moves custom type definitions and related configuration, not content records.

**How to avoid:** Use the CMS Export/Import tooling available in the Digital Experiences app to move content items between environments. Export the workspace content from the source org, import into the target org after the metadata deploy. For CI/CD pipelines, document this as a separate manual step or automate using the Managed Content REST API (`/services/data/vXX.0/connect/cms/content-items`).

---

## Gotcha 4: Scheduling Uses Org Timezone, Not User Timezone

**What happens:** A content item scheduled to publish at midnight on a specific date goes live at the wrong time from the content author's perspective, or worse, at the wrong calendar date in some regions.

**When it occurs:** When the content author is in a different timezone than the org's configured timezone. The scheduling panel in Digital Experiences accepts a datetime value and interprets it in the org's timezone. An author in UTC-8 who sets a publish time of "December 1, 00:00" will see the content go live at a time that may be December 1 in one timezone but still November 30 in their local time.

**How to avoid:** Confirm the org's timezone in Setup > Company Information before setting any content schedules. Document the schedule using the org's timezone explicitly in content item naming or description fields. For critical launches, verify the scheduled time in the content item's detail view and convert to all relevant stakeholder timezones before confirming.

---

## Gotcha 5: Unmanaged Content Is Overwritten on Sandbox Refresh

**What happens:** After a full or partial sandbox refresh, all unmanaged content previously authored within Experience Builder sites is gone. The content was not preserved in the refresh because it is stored as site-local data in the sandbox, not in a metadata package or the production org's content records.

**When it occurs:** Any time a sandbox is refreshed from production, and the sandbox was used for CMS content authoring with unmanaged content. Also affects managed content that was authored in sandbox and never promoted to production.

**How to avoid:** Use managed CMS content (workspace + channel) for any content that must survive sandbox lifecycle events. Before refreshing a sandbox, export managed content from the workspace. After refresh, re-import. For unmanaged content, document it externally (screenshots, content spreadsheets) before refreshing. Treat sandbox content authoring as ephemeral unless it is managed and exported.
