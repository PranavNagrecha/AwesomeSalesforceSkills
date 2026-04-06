# Gotchas — Knowledge Base Administration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Lightning Knowledge Cannot Be Disabled After Enablement

**What happens:** Once an admin enables Lightning Knowledge in Setup > Knowledge Settings, the feature cannot be turned off. Classic Knowledge article types are permanently converted to record types on the `Knowledge__kav` object. The disable toggle is removed from the UI. All subsequent Knowledge configuration must be done in the Lightning Knowledge framework.

**When it occurs:** Any time an admin or developer enables Lightning Knowledge — including in sandbox orgs. Sandbox refreshes from a production org where Lightning Knowledge is enabled will have the feature enabled in the refreshed sandbox as well.

**How to avoid:** Treat Lightning Knowledge enablement as an architectural decision requiring stakeholder sign-off, not a configuration toggle. Design record types, page layouts, and Data Category Groups before enabling. Enable in a Developer sandbox first to validate the design, then promote the configuration through change management before enabling in production.

---

## Gotcha 2: Unclassified Articles Are Invisible to Standard Users

**What happens:** If a Knowledge article version has no Data Category assigned from any active Knowledge Data Category Group, it is only visible to users with the "View All Data" or "Manage Articles" permission. Standard agents and customers cannot see the article in search results or direct URL navigation. Authors receive no warning — the article appears published but is effectively invisible to the audience.

**When it occurs:** Occurs whenever a new article is created and the author forgets (or does not know) to assign at least one category. Also occurs when an admin activates a new Data Category Group without immediately assigning categories to existing articles — those articles lose visibility for users who lack "View All Data."

**How to avoid:** Train all Knowledge authors to assign at least one category before publishing. Add a Validation Status check (e.g., "requires category assignment") to the pre-publication review process. Consider using a Flow or Approval Process entry criteria that checks for category assignment before allowing publish. Audit existing articles for unclassified status when activating new category groups.

---

## Gotcha 3: Publishing a New Version Immediately Archives the Current Published Version

**What happens:** When an author publishes a new version of an existing article, Salesforce instantly transitions the currently published version to Archived status. There is no "schedule for future publish" option and no grace period. The old published version is no longer visible to users the moment the new version is published.

**When it occurs:** Any time an author clicks "Publish" on a draft version of an article that already has a published version. Common during content refresh cycles when authors revise and publish articles without realizing the swap is instantaneous.

**How to avoid:** Review new article versions carefully before publishing, as there is no rollback to the previous published version (the archived version exists but must be explicitly restored, creating a new published version from it). Build the review step into the pre-publish workflow — either through Approval Processes or Validation Status checks that require sign-off before the Publish action is available. For critical articles, export the current published content before publishing a new version as a backup reference.

---

## Gotcha 4: Data Category Visibility Is Additive — You Cannot Restrict Child Roles Below Parent Visibility via Inheritance

**What happens:** Salesforce role hierarchy for Data Category visibility is additive-only. A user inherits all category visibility from roles above them in the hierarchy. If a parent role has visibility to "All Products" category, every child role in that hierarchy also has visibility to "All Products" — even if the intent was for child roles to see only a subset.

**When it occurs:** When organizations design role hierarchies for reporting (broad visibility at top) and then try to use the same hierarchy to restrict Knowledge visibility. A regional manager role above a front-line agent role will cause the agent to inherit all visibility the manager has.

**How to avoid:** Explicitly configure Data Category visibility at each role level rather than relying on inheritance. For roles that should have restricted visibility compared to their parent, open that role's category visibility settings and explicitly assign only the categories that role should see. Do not assume inheritance will restrict — inheritance only grants.

---

## Gotcha 5: Approval Process on Knowledge__kav Requires "Manage Articles" to Submit — Not Just Article Ownership

**What happens:** Authors who own a draft article but lack the "Manage Articles" user permission cannot submit their own article for approval. The "Submit for Approval" button either does not appear or returns an insufficient privileges error. This breaks approval-gated publishing workflows silently — authors think the approval process is broken when in fact it is a permission gap.

**When it occurs:** When admins build Approval Processes on `Knowledge__kav` but assign the "Manage Articles" permission only to senior agents or admins, leaving junior authors without the permission needed to trigger the approval gate themselves.

**How to avoid:** Audit the profile/permission set for Knowledge authors and confirm "Manage Articles" is enabled. This permission also grants the ability to publish, archive, and delete articles directly — if those actions should be restricted to approvers, pair the Approval Process with criteria-based restrictions or a separate Validation Status workflow that signals readiness without granting direct publish access.
