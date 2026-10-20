# Gotchas — Experience Cloud CMS Content

Non-obvious Salesforce platform behaviors that cause real production problems in this domain. Cites are to the Winter '27 (264) `api_meta` and `object_reference` guides.

UNVERIFIED (2026-10-20): Gotchas 1 (no point-and-click type creation; silent failure), 2 (silent invisibility from a channel mismatch), 3 (the export/import and scripted routes), 4 (org-timezone scheduling) and 5 (sandbox refresh of unmanaged content) rest on Help-only or field-observed behaviour; each is marked again where it is asserted.

## Gotcha 1: Custom Content Types Are Metadata, and Each Needs a Detail Page

**What happens:** A team needs fields beyond the standard News, Image and Document types and cannot find where to define them. A custom type is a `ManagedContentType` (suffix `managedContentType`, folder `managedContentTypes`, API 47.0 and later; api_meta 264 L89072-89078), or for enhanced workspaces a `ContentTypeBundle` folder with a `schema.json` (API 64.0 and later; api_meta 264 L38404-38419). Each custom type also needs a CMS content page in the site as its detail page (api_meta 264 L89296-89299). UNVERIFIED (2026-10-20): that there is no Setup wizard or New Content Type button, and that an item of an undefined type fails silently or is missing from the Add Content menu, are not stated in the corpus.

**When it occurs:** Any time an org needs content fields beyond the fixed schemas of the standard types (object_reference 264 L180343-180362).

**How to avoid:** Author the node list with the guide's element names (`nodeName`, `nodeLabel`, `nodeType`; exactly one `NAMEFIELD` node with `isRequired` true; at most 15 nodes; api_meta 264 L89136-89161, L89221-89232), run `scripts/check_experience_cloud_cms_content.py --manifest-dir <dir>`, and deploy with `sf project deploy start`. The Tooling API as an alternative route is UNVERIFIED (2026-10-20): the Tooling API reference is not in the corpus.

---

## Gotcha 2: Channel Type Decides Who Can Read the Content

**What happens:** Published content reaches the wrong audience or none. A `ManagedContentChannel` has a `Type`: `COMMUNITY` (access follows the Experience Cloud site's settings), `CloudToCloud`, `ConnectedApp`, `PublicUnauthenticated` (no authentication; cacheable on public CDNs), `Record`, and `UserPermission` (reserved) (object_reference 264 L180507-180523). The names `ExperienceChannel` and `PublicChannel` that earlier versions of this skill used are not in the corpus. UNVERIFIED (2026-10-20): that a mismatch is silent, that the item still shows Published, and that the type cannot be edited in place are Help-only.

**When it occurs:** When a channel is created for headless delivery (`PublicUnauthenticated`) and reused for a site, or the reverse.

**How to avoid:** Query `ManagedContentChannel` and read `Type` (object_reference 264 L180412, L180507-180523); use `COMMUNITY` for Experience Cloud site delivery. After correcting a channel, confirm on a variant that `IsPublished` is true (L180707-180713).

---

## Gotcha 3: CMS Content Records Do Not Promote With the Type Metadata

**What happens:** A deployment from sandbox to production carries the custom type definitions but not the authored items. `ManagedContent` is the record for an item (object_reference 264 L180276-180279), so it is data, while `ManagedContentType` and `ContentTypeBundle` are metadata (api_meta 264 L89064, L38391).

**When it occurs:** Any time a team treats content items as metadata.

**How to avoid:** Deploy the type metadata first, then move content records as a separate runbook step. UNVERIFIED (2026-10-20): the Digital Experiences export/import tooling, and the Managed Content REST path `/services/data/vXX.0/connect/cms/content-items` that earlier versions of this skill gave, are not in the corpus; confirm the supported route in a sandbox before relying on either.

---

## Gotcha 4: Scheduling and Timezone Are Not in the Object Model

**What happens:** A publish or unpublish time lands on the wrong day. UNVERIFIED (2026-10-20): that CMS items carry per-item publish and unpublish schedules interpreted in the org timezone is Help-only. `ManagedContentVariant` has no schedule field (object_reference 264 L180683-180780); the only publish switches in the metadata are the flow actions `managedContentPublishVariant` and `managedContentUnpublishVariant` (api_meta 264 L71645-71650).

**When it occurs:** When the author's timezone differs from the org's, if the Help behaviour holds.

**How to avoid:** Test the schedule on a non-production item and write the timezone next to the time in the runbook; use a flow with the publish and unpublish actions only after deciding that native scheduling is not available.

---

## Gotcha 5: Unmanaged Content Is Outside the Workspace Model

**What happens:** Content authored directly in a site is not a `ManagedContent` record in a workspace, so it has no variants or channel. UNVERIFIED (2026-10-20): that it is overwritten on sandbox refresh, that it has no versioning, scheduling or targeting, and that managed content authored in sandbox and never promoted is also lost, are Help-only.

**When it occurs:** When a team skips the workspace to move faster.

**How to avoid:** Use managed content for anything that must be governed or reused (object_reference 264 L180277-180279), and keep an inventory of any site-local content with a re-entry plan.
