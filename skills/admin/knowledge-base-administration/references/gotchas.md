# Gotchas — Knowledge Base Administration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Lightning Knowledge Cannot Be Disabled After Enablement

**What happens:** Once an admin enables Lightning Knowledge in Setup > Knowledge Settings, the feature cannot be turned off. Classic Knowledge article types are permanently converted to record types on the `Knowledge__kav` object. The disable toggle is removed from the UI. All subsequent Knowledge configuration must be done in the Lightning Knowledge framework. <!-- UNVERIFIED (2026-09-04): irreversibility is not stated in the extracted Metadata API or Object Reference PDFs, where `enableLightningKnowledge` is documented as a plain boolean. The claim rests on Salesforce Help (Set Up Lightning Knowledge), which cannot be fetched from the authoring environment. Nothing here depends on it being wrong — plan the enablement as one-way — but do not quote "Salesforce documents this as irreversible" to a stakeholder without opening that Help article yourself. -->

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

---

## Gotcha 6: Deploying a Data Category Group Deletes Every Category the XML Does Not Mention

**What happens:** Metadata API treats a `DataCategoryGroup` file as the complete definition of the group, not a patch. On deploy it "deletes any category that is not defined in the XML file", and records associated with a deleted category are silently re-associated with that category's **parent**. Object associations under `objectUsage` are handled the same way — one omitted `<object>KnowledgeArticleVersion</object>` unassigns the entire group from articles. Repositioning is just as lossy in a different direction: the guide's own worked example shows a sandbox where records classified under `FR` end up under `EU`, while the same deploy leaves them under `EMEA` in production, because Metadata API replays the end state and has "no concept of the order of the changes made to the sandbox".

**When it occurs:** Any sandbox-to-production deploy of a category group that already exists in the target, and any partial retrieve where someone hand-trimmed the XML. It is invisible in a `--dry-run` diff because the file itself looks smaller, not wrong.

**How to avoid:** The Metadata API guide gives an unusually blunt instruction here: Salesforce "recommends that you manually create data categories and record associations in an organization from Setup… rather than deploying changes from a sandbox to a production organization." Treat the `DataCategoryGroup` XML as the authoring and review artefact — commit it, diff it, get it approved — then make structural category changes in production through Setup. If you do deploy, retrieve the target org's current group first and diff it against yours category by category, and never deploy a group file that was assembled by hand.

---

## Gotcha 7: A Data Category Group With No `objectUsage` Deploys Clean and Classifies Nothing

**What happens:** `objectUsage` is an optional field on `DataCategoryGroup`. A group with a complete, well-formed category tree and `active` set to `true` deploys successfully with no `objectUsage` element and then does not appear when an author classifies an article, because it was never associated with `KnowledgeArticleVersion`. Only two values are valid — `KnowledgeArticleVersion` for articles and `Question` for questions, the latter limited to one group.

**When it occurs:** Most often when the group XML was written from the taxonomy design rather than retrieved from an org where someone had already ticked the assignment in Setup, and whenever a later deploy of the same group omits the element (gotcha 6 then permanently strips the assignment that was there).

**How to avoid:** Make `objectUsage/object` a required line in your review of any category group destined for Knowledge — `scripts/check_knowledge_base_administration.py` WARNs on a group without one. Confirm after deploy in **Setup → Data Categories → Data Category Group Assignments** rather than trusting the deploy result, which reports success either way.

---

## Gotcha 8: Category Visibility Cannot Be Moved to a Permission Set

**What happens:** `categoryGroupVisibilities` is documented in the Metadata API as `ProfileCategoryGroupVisibility` — a field on `Profile`, available in API version 41.0 and later. The `PermissionSet` field list has no equivalent element. A profile-to-permission-set migration that moves object CRUD, field permissions, record type visibility and user permissions onto permission sets and then points every user at a minimal-access profile removes their data category visibility with it, and every article that carries a category from an affected group disappears for them.

**When it occurs:** During "profile decomposition" projects, and whenever a new profile is cloned from Minimum Access and given its permissions entirely through permission sets. The symptom presents as a Knowledge outage rather than a permissions bug, because object access and the Articles tab still work — searches just return nothing.

**How to avoid:** Keep category visibility on the profile as a deliberate exception and document it as such in the permission architecture, so the next person does not "finish the migration". Assign visibility through the role hierarchy where the role model allows it, since that mechanism is independent of the profile-versus-permission-set question. Before and after any profile change, retrieve the profile and diff the `categoryGroupVisibilities` blocks specifically — `admin/permission-sets-vs-profiles` and the `/migrate-profile-to-permset` agent both assume everything moves off the profile, and this does not.

---

## Gotcha 9: A Wildcard `package.xml` Retrieves No Part of the Knowledge Base

**What happens:** Three of the five metadata types a Knowledge setup needs refuse the wildcard, each for a different documented reason, and all three fail silently rather than erroring. `*` on `CustomObject` "doesn't match standard objects" — and `Knowledge__kav` is a standard object, so a wildcard manifest returns no knowledge object, no fields, and no record types. `RecordType` does not support `*` at all. `Settings` accepts `*` only in the sense of retrieving every setting; an individual feature setting such as `Knowledge` must be named as a member. The deploy that follows looks like a success and ships a knowledge base with no article types.

**When it occurs:** Any org-comparison, backup, or "retrieve everything" pipeline built on wildcards, and any hand-written manifest copied from a custom-object example.

**How to avoid:** Name `Knowledge` under `Settings`, `Knowledge__kav` under `CustomObject`, and each record type as `Knowledge__kav.<Name>` under `RecordType`. The manifest in `references/metadata-examples.md` is the shape to copy. After retrieve, confirm the files are physically on disk — `objects/Knowledge__kav/recordTypes/` present and non-empty — before treating the retrieve as a baseline.

---

## Gotcha 10: Article SOQL Requires a `PublishStatus` Filter and Rejects Bind Variables

**What happens:** Two independent constraints apply to querying articles that apply to no other object. First, the Object Reference states that "article queries and searches in SOQL or SOSL require that you specify either the `PublishStatus` or the `Id` field in the `WHERE` clause" — omit both and the query fails rather than returning everything. Second, `KnowledgeArticleVersion` objects reject bind variables in Apex SOQL: `WHERE PublishStatus = :PUBLISH_STATUS_ONLINE` in a static query is a **compilation error**, and the documented workaround is to build the same string and run it through `Database.query()`, which does bind. The status values are also not the ones the UI shows — the picklist is `Draft`, `Online`, `Archived`, so filtering on `'Published'` matches nothing.

**When it occurs:** In every Apex utility, batch job, or test that touches articles, and in the reporting and reconciliation queries written during a Knowledge migration. The bind-variable rule bites at compile time so it is caught early; the missing-filter and `'Published'` rules produce empty result sets that read as "no data yet".

**How to avoid:** Standardise on `WHERE PublishStatus = 'Online' AND Language = '<code>'` as the baseline article query, add `IsLatestVersion = false` when hunting archived versions (the guide requires that pairing for `Archived`), and route any status that comes from a variable through `Database.query()`. Remember the permission side too: only users with "View Draft Articles" see `Draft` rows and only "View Archived Articles" sees `Archived`, so an integration user's query can legitimately return fewer rows than an admin's.

---

## Gotcha 11: `Knowledge__kav` Is Only the Default Name, and Renaming It Breaks Every Hard-Coded Path

**What happens:** The Object Reference notes that the `Knowledge` prefix "can be modified by changing the Object Name for the `Knowledge__kav` object in Object Manager". The rename propagates: `Knowledge__DataCategorySelection` takes the new prefix too, `ChannelLayout` field references change from `Knowledge.FieldName` to `<NewName>.FieldName`, and every `package.xml` member, metadata directory path, SOQL `FROM` clause, and Apex type name follows. Nothing warns you, because the org where the rename happened works perfectly — it is the shared skill, script, template, or managed package written against `Knowledge__kav` that breaks.

**When it occurs:** In orgs where the knowledge base was branded during setup ("Article", "HelpArticle", a product name), and in any org that inherited such a rename through a sandbox refresh. It surfaces the first time a deploy, a checker script, or an AI-generated snippet from a generic example is run against that org.

**How to avoid:** Read the object's actual API name from Object Manager (or `describeSObjects`) before writing any path or query, and record it at the top of the Knowledge runbook alongside the record type list. When authoring reusable scripts, take the object name as a parameter that defaults to `Knowledge__kav` rather than hard-coding it — that is exactly why the checker in this package reports the directory it looked in when it finds nothing, instead of reporting "no record types".
