---
name: knowledge-base-administration
description: "Use this skill when setting up, configuring, or managing Salesforce Lightning Knowledge — enabling the feature, designing record types on Knowledge__kav, configuring Data Categories for organization and visibility control, setting up publishing workflows, and layering approval processes. Trigger keywords: Lightning Knowledge setup, Knowledge article record types, Data Category visibility, Knowledge publishing workflow, Knowledge__kav configuration. NOT for converting Classic Article Types to Lightning — use admin/knowledge-classic-to-lightning. NOT for bulk-loading articles from an external help center — use data/knowledge-article-import. NOT for sizing the taxonomy itself (how many groups, how deep) — use architect/knowledge-taxonomy-design."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - Reliability
triggers:
  - "How do I set up Lightning Knowledge in a new Salesforce org?"
  - "Knowledge article record types are not showing the right fields to different user groups"
  - "How do Data Categories control who can see Knowledge articles, and how do I configure visibility by role?"
  - "we're having issues with lightning knowledge"
  - "agent published a knowledge article but nobody can find it"
  - "data category group deployed but does not show up when classifying an article"
  - "data category group not filtering articles"
  - "knowledge articles disappeared after we moved permissions off the profile"
  - "wildcard package.xml did not retrieve Knowledge__kav or its record types"
  - "knowledge SOQL returns nothing until I add PublishStatus to the where clause"
  - "user has read access to Knowledge__kav but sees zero articles"
  - "deploy a knowledge base from sandbox to production without losing data categories"
  - "how do I enable a second language for knowledge articles"
tags:
  - knowledge
  - lightning-knowledge
  - data-categories
  - knowledge-base
  - publishing-workflow
  - record-types
  - knowledge-settings
  - data-category-visibility
inputs:
  - "Confirmation that Lightning Knowledge is enabled (or the intent to enable it — irreversible decision)"
  - "List of article types or content categories needed (e.g., FAQ, How-To, Known Issue)"
  - "Audience segments requiring different article visibility (internal agents, partners, customers)"
  - "Approval or review process requirements before articles can be published"
outputs:
  - "Lightning Knowledge configuration plan with record type layout per audience"
  - "Data Category Group structure with role/profile/permission-set visibility assignments"
  - "Publishing workflow decision: native statuses only vs. Validation Status picklist vs. full approval process"
  - "Review checklist confirming the Knowledge setup is production-ready"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

# Knowledge Base Administration

This skill activates when an admin or architect needs to set up or manage Salesforce Lightning Knowledge — covering the one-time enablement decision, record type design on the `Knowledge__kav` object, Data Category configuration for dual-purpose organization and access control, and publishing workflow design using native statuses, Validation Status, and optional approval processes.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Lightning Knowledge enabled?** Navigate to Setup > Knowledge Settings. If the toggle is OFF, understand that enabling it is irreversible — once turned on, Classic Knowledge article types are permanently replaced by Lightning Knowledge record types on the single `Knowledge__kav` object. There is no undo path. <!-- UNVERIFIED (2026-09-04): irreversibility is not stated in the extracted Metadata API or Object Reference PDFs, where `enableLightningKnowledge` is documented as a plain boolean. The claim rests on Salesforce Help (Set Up Lightning Knowledge), which cannot be fetched from the authoring environment. Nothing here depends on it being wrong — plan the enablement as one-way — but do not quote "Salesforce documents this as irreversible" to a stakeholder without opening that Help article yourself. -->
- **Most common wrong assumption:** Practitioners often assume Data Categories are purely organizational (like tags). In reality, they serve dual duty: content categorization AND access control. A user must have visibility to at least one category in every Data Category Group assigned to an article in order to see that article. Misconfigured visibility silently hides articles from users who expect to see them.
- **Platform constraints:** The Metadata API guide caps a group at **100 categories and 5 hierarchy levels**. The org-level cap on how many groups can be *active* for Knowledge is 5, with 3 active by default. <!-- UNVERIFIED (2026-09-04): the 100-categories / 5-levels cap is stated in the Metadata API Developer Guide under DataCategoryGroup. The "5 groups, 3 active by default" org cap is not in the Metadata API PDF, the Object Reference, or the App Limits cheat sheet (which documents no Knowledge limits at all) — it is carried by architect/knowledge-taxonomy-design, which is the authority for taxonomy sizing. Verify against your org's Setup before designing a fourth group. -->
- **What is the knowledge object actually called?** `Knowledge__kav` is only the default. The Object Reference notes the prefix can be renamed in Object Manager, and the rename propagates to `Knowledge__DataCategorySelection`, to `ChannelLayout` field references, and to every metadata path and query. Read the real API name before writing any of them.

---

## Questions to Ask Before Configuring

Ask these before touching Knowledge Settings. Each one maps to a documented behaviour that is expensive to reverse, and an assistant that skips them produces a knowledge base that deploys cleanly and shows nobody any articles.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Is Lightning Knowledge already on, and if not, who signs off on turning it on?" | `enableKnowledge` plus `enableLightningKnowledge` is the fork between one `Knowledge__kav` object and per-type Classic `__kav` objects; the Classic path needs `admin/knowledge-classic-to-lightning` instead of this skill | A named approver, and the sandbox the design was proved in |
| "Which audiences read articles, and does any of them sit outside the role hierarchy?" | Category visibility is granted per role, and per profile via `categoryGroupVisibilities`; guest and community users need the profile route | The audience × category matrix that becomes the `Profile` XML |
| "Which classification axes are genuinely independent — and how many groups is that?" | Each axis is a `DataCategoryGroup`, capped at 100 categories and 5 levels, and the org caps how many can be active | A group list sized against `architect/knowledge-taxonomy-design`, before any XML exists |
| "Do articles need more than one language?" | `defaultLanguage` and the `languages` block are set once in the settings file, and each language carries its own default assignee and reviewer | The language list with a *queue* per language rather than a named user |
| "Does anything need to block publication, or only signal quality?" | Native `PublishStatus` has no gate; `ValidationStatus` signals without blocking; an approval process blocks and needs "Manage Articles" to submit | The chosen workflow and who holds the submit permission |
| "Who gets the Knowledge User feature licence, and how many are there?" | The Object Reference is explicit that internal Knowledge users need it *in addition to* the View Articles permission — it is a checkbox on the User record, not a permission set | A licence count checked against what the org owns, before go-live |
| "Will this configuration be deployed from a sandbox, or built in production?" | Deploying a `DataCategoryGroup` permanently deletes any category the XML omits and re-parents its articles; Salesforce's own guidance is to make category changes in Setup | An explicit decision, with the deploy path restricted to settings, record types, and profiles |

What a proper configuration adds over just enabling Knowledge: articles are findable by the audience they were written for on the day they are published, the taxonomy can be changed later without silently re-parenting articles, and the publish workflow is a reviewed gate rather than an author's one-click habit.

---

## Core Concepts

### Lightning Knowledge and the Knowledge__kav Object

Lightning Knowledge consolidates all article content onto a single standard Salesforce object: `Knowledge__kav` (the Knowledge Article Version object). Unlike Classic Knowledge, which used separate custom objects for each article type, Lightning Knowledge uses standard record types on `Knowledge__kav` to differentiate content types (e.g., FAQ, How-To, Known Issue). This means page layouts, field sets, and Lightning record pages are configured per record type — the same tooling used for any other Salesforce object.

Enabling Lightning Knowledge is a one-way migration. The Setup toggle activates the feature and converts existing Classic article types into record types. There is no disable path and no rollback. Once enabled, Classic Knowledge Setup options disappear and the `Knowledge__kav` object is the permanent storage layer.

Each Knowledge Article has a parent `Knowledge__ka` (Knowledge Article) record that acts as the container, while `Knowledge__kav` records represent individual versions. Published articles always have exactly one published version. Archiving a published article creates a new Archived version rather than modifying the Published version in place.

### Data Categories: Dual-Purpose Organization and Access Control

Data Categories are hierarchical category groups that admins attach to Knowledge articles. Their dual role is critical:

1. **Organization**: Categories allow agents and customers to browse or filter articles by topic. A support team might use a "Products" category group with subcategories for each product line.
2. **Access Control**: Salesforce evaluates category visibility before showing articles to any user. Visibility is granted through Role Hierarchy, Profiles, or Permission Sets. If a user has no visibility into any category in a group that is assigned to an article, that article is invisible to them — regardless of object-level permissions.

The visibility model is additive: users inherit visibility from their role hierarchy. An admin must explicitly deny visibility to restrict access downward. Default visibility for unauthenticated guest users must be set separately via the Guest User Category Visibility settings.

Unclassified articles (articles with no category assigned from a group) are visible only to users with "View All Data" or explicit "Manage Categories" permissions — a common cause of articles disappearing immediately after creation.

### Publishing Workflow: Statuses, Validation Status, and Approval Processes

Every Knowledge article version moves through three native platform statuses:

- **Draft**: Article is being authored or edited. Not visible to end users.
- **Published**: Article is live. Exactly one published version can exist per article at any time. Publishing a new version automatically archives the previous published version.
- **Archived**: Article is retired from public view but preserved for history and potential restoration.

On top of native statuses, admins can enable a **Validation Status** picklist on `Knowledge__kav`. This is an admin-customizable picklist (values like "Validated", "Not Validated", "In Review") that signals content quality. Validation Status is separate from publish status — an article can be Published but flagged as "Not Validated." Agents can filter article searches by Validation Status to surface only quality-assured content.

For organizations requiring formal review before publishing, Salesforce supports standard **Approval Processes** on `Knowledge__kav`. An approval process can require sign-off from a subject-matter expert before a Draft article can transition to Published. Approval processes on Knowledge articles use the same Process Builder/Flow-backed approval framework as other objects, with the constraint that only the record owner or users with "Manage Articles" permission can submit articles for approval.

### Channels and Languages: The Two Switches Outside the Category Model

Data category visibility decides *which* articles a user may see. Two other switches decide *where* an article can appear at all, and neither is a category:

| Switch | Where it lives | What it controls |
|---|---|---|
| `IsVisibleInApp` | Field on the article version | Article appears on the Articles tab |
| `IsVisibleInCsp` | Field on the article version | Article appears in the Customer Portal |
| `IsVisibleInPrm` | Field on the article version | Article appears in the partner portal |
| `IsVisibleInPkb` | Field on the article version | Article appears in the public knowledge base |
| `ChannelLayout` | `channelLayouts/` metadata | Which article fields get shared inline into Email, Chat, Messaging, and Social publishers, optionally per record type |

All four `IsVisibleIn*` fields are marked Required in the Object Reference and default on create, so a bulk-loaded article has channel flags whether the loader set them or not. An internal-only record type is not protected by its layout — it is protected by leaving `IsVisibleInPkb` and `IsVisibleInCsp` false and by field permissions on the internal fields.

Languages are set once, in the settings file: a required `defaultLanguage` plus a `languages` block where each entry carries `name`, `active`, and a default assignee and reviewer that may be a `User` or a `Queue`. On the article side, `Language`, `IsMasterLanguage`, and `IsOutOfDate` carry the translation state, and every article query should filter on `Language` as well as `PublishStatus`.

---

## Common Patterns

### Pattern: Record Type per Content Audience

**When to use:** When different teams produce different content types that need distinct field sets and layouts. For example, a support team authoring detailed technical Known Issue articles needs different fields than a marketing team writing FAQ articles for customers.

**How it works:**
1. Enable Lightning Knowledge in Setup > Knowledge Settings.
2. Navigate to Setup > Object Manager > Knowledge > Record Types.
3. Create a record type for each content type (e.g., "FAQ", "How-To", "Known Issue", "Release Note").
4. Assign page layouts per record type — hide internal-only fields (e.g., "Root Cause") from the customer-facing layout.
5. Assign record types to profiles so authors only see record types relevant to their role.

**Why not the alternative:** Using a single record type with all fields visible causes layout clutter and risks exposing internal fields (root cause analysis, workaround notes) to customer-facing surfaces. Record types enforce the separation cleanly without custom Apex.

### Pattern: Data Category Groups for Layered Visibility

**When to use:** When the org serves multiple audiences (internal agents, partners, customers via Experience Cloud) who should see overlapping but distinct article sets.

**How it works:**
1. Create Data Category Groups in Setup > Data Category Groups, and assign each to `KnowledgeArticleVersion` — the group's `objectUsage` element. Size the group count against `architect/knowledge-taxonomy-design` before building.
2. Design the hierarchy to reflect your content taxonomy (e.g., "Products > Product A > Feature X").
3. In Setup > Roles, assign category visibility per role: "Include subcategories" to inherit the tree downward, or "Exclude" to explicitly block.
4. Test visibility by logging in as a representative user from each role before go-live.
5. For guest/unauthenticated users, set the default category visibility under Knowledge Settings > Guest User Category Access.

**Why not the alternative:** Using only object-level sharing or permission sets for article access bypasses the Data Category visibility check — articles remain invisible even if the user has object read access unless category visibility is also configured.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single article type, small team, no approval needed | One record type + native Draft/Published/Archived statuses | Lowest overhead; sufficient for simple use cases |
| Multiple content types with different field requirements | Separate record type per content type with distinct page layouts | Record types are the standard mechanism for layout differentiation on a single object |
| Content quality signal needed without blocking publish | Enable Validation Status picklist; train authors to mark status | Non-blocking; lets agents filter by quality without stopping publication |
| Regulated content requiring sign-off before publishing | Approval Process on Knowledge__kav + Validation Status | Approval processes enforce the gate; Validation Status surfaces the approval outcome |
| Multiple audiences with different article visibility needs | Data Category Groups with role-based visibility assignments | The only platform-native mechanism for audience-scoped article visibility |
| Migrating from Classic Knowledge | Plan record types before enabling Lightning Knowledge; enablement is irreversible | Post-enablement reconfiguration is possible but article type recategorization requires bulk data updates |

---

## Recommended Workflow

1. **Establish the object name and current state** — read the knowledge object's real API name in Object Manager (`Knowledge__kav` is only the default), and retrieve `Settings:Knowledge` to see whether `enableKnowledge` and `enableLightningKnowledge` are already true. A Classic org routes to `admin/knowledge-classic-to-lightning` before anything here applies.
2. **Answer the seven questions above and size the taxonomy** — the audience × category matrix and the group count come from `architect/knowledge-taxonomy-design`; do not write `DataCategoryGroup` XML before that number is agreed, because the group is expensive to split later.
3. **Write the five artefacts together** — settings, category groups, record types and fields, the profile blocks that carry `categoryGroupVisibilities`, and the author permission set. `references/metadata-examples.md` has the deployable shape of each plus the manifest that names the three types a wildcard will not retrieve.
4. **Check before deploying** — run `python3 scripts/check_knowledge_base_administration.py --manifest-dir force-app/main/default`. It catches the four silent failures: an inactive group, a group with no `objectUsage`, a Classic settings file (`enableKnowledge` true with `enableLightningKnowledge` false), and a profile granting visibility to a category group that is not in the package.
5. **Deploy settings, record types, and profiles — but make category structure changes in Setup** — the Metadata API guide states plainly that deploying category changes between orgs "permanently removes categories and record categorizations that are not specified in your XML file" and recommends Setup instead (`references/gotchas.md` #6).
6. **Prove visibility per audience, not per config screen** — publish one article per record type and per language, classify it, then query it as a representative user of each audience with `WHERE PublishStatus = 'Online' AND Language = '<code>'` and confirm the rows in `Knowledge__DataCategorySelection`. Both queries are in `references/metadata-examples.md` §7.
7. **Record the runbook** — object API name, record type list, group and category developer names (which the guide says cannot be changed later), which profiles hold category visibility, and who holds "Manage Articles". `templates/knowledge-base-administration-template.md` is the shape.

---

## Review Checklist

Run through these before marking Knowledge setup work complete:

- [ ] Lightning Knowledge enablement decision documented and acknowledged as irreversible
- [ ] Record types created with appropriate page layouts per content type
- [ ] Record types assigned to correct author profiles
- [ ] Data Category Groups created, `active` true, and each assigned to `KnowledgeArticleVersion` (Setup → Data Category Group Assignments)
- [ ] Group count within the org's active limit, sized per `architect/knowledge-taxonomy-design`
- [ ] Category visibility assigned per audience on **roles and profiles** — permission sets carry no `categoryGroupVisibilities`; guest user defaults set if applicable
- [ ] Knowledge User feature licence granted to every internal author and agent, in addition to the View Articles permission
- [ ] Unclassified article visibility tested — confirm articles without categories behave as expected
- [ ] Publishing workflow configured (native statuses, Validation Status, and/or Approval Process)
- [ ] At least one test article created, published, and verified visible to each intended audience
- [ ] Archived version behavior verified (previous published version archived on re-publish)
- [ ] Verification queries run: `Knowledge__kav` filtered on `PublishStatus` + `Language`, and `Knowledge__DataCategorySelection` for the classifications
- [ ] `scripts/check_knowledge_base_administration.py --manifest-dir <dir>` run clean against the retrieved metadata

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Lightning Knowledge enablement is irreversible** — Once you enable Lightning Knowledge in Setup, there is no disable toggle. Classic Knowledge article types are permanently converted to record types on `Knowledge__kav`. Do not enable in production without a complete design review and stakeholder sign-off.
2. **Unclassified articles are invisible by default** — If an article has no Data Category assigned from any active Knowledge Category Group, it is only visible to users with "View All Data" or "Manage Articles" permission. New authors who forget to assign categories inadvertently publish invisible articles, leading to "I can't find the article I just published" support requests.
3. **Publishing a new version archives the previous one immediately** — Clicking Publish transitions the currently published version to Archived at once, and there is no in-place undo. The documented recovery is `KbManagement.PublishingService.restoreOldVersion(articleId, versionNumber)`, which builds a *new draft* from an archived version rather than reinstating it. Note that scheduling does exist programmatically even though the Setup button is immediate: `scheduleForPublication` and `archiveOnlineArticle` both accept a date, and dates are GMT.
4. **Data Category visibility is additive from role hierarchy, not subtractive** — Administrators cannot use role hierarchy to restrict visibility downward using inheritance alone. A child role inherits parent role visibility. If you need a child role to see fewer categories than the parent, you must explicitly configure that child role's visibility separately, not rely on inheritance.
5. **Approval Processes on Knowledge__kav require "Manage Articles" to submit** — Only the article owner or a user with the "Manage Articles" permission can submit a Knowledge article for approval. If authors lack this permission, they cannot trigger the approval workflow, breaking the publishing gate. Assign "Manage Articles" to author profiles intentionally.
6. **A `DataCategoryGroup` deploy is a replace, not a merge** — every category absent from the XML is deleted and its articles are re-parented; every `objectUsage` entry absent from the XML is unassigned. Salesforce's own guidance is to make category structure changes in Setup rather than deploy them between orgs.
7. **`categoryGroupVisibilities` exists on `Profile` only** — the Metadata API `PermissionSet` type has no equivalent, so a profile-to-permission-set migration silently strips article visibility while leaving object access intact.
8. **A wildcard manifest retrieves none of it** — `*` on `CustomObject` does not match standard objects (and `Knowledge__kav` is standard), `RecordType` does not accept `*` at all, and `Settings` needs the member named `Knowledge`.
9. **Article SOQL has two rules of its own** — `PublishStatus` or `Id` must appear in the `WHERE` clause, and bind variables are a compile error against article objects (use `Database.query`). The status value is `Online`, not "Published".

Full treatment, with the guide passages each rests on, is in `references/gotchas.md`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Knowledge Setup Decision Document | Records the Lightning Knowledge enablement decision, confirming it is irreversible and that stakeholders have approved |
| Record Type Taxonomy | Table of record types, associated layouts, and profile assignments |
| Data Category Group Map | Hierarchy diagram of category groups with role/profile visibility matrix per audience |
| Publishing Workflow Decision | Documents choice of native statuses / Validation Status / Approval Process and the rationale |
| Admin Runbook | Operational procedures for ongoing Knowledge management (creating article types, updating categories, managing approvals) |
| `settings/Knowledge.settings-meta.xml` | Feature enablement, default language, active languages with assignee/reviewer queues, Validation Status switch |
| `datacategorygroups/<Name>.datacategorygroup-meta.xml` | The taxonomy tree with `active` and `objectUsage` on `KnowledgeArticleVersion` |
| `objects/Knowledge__kav/` record types and fields | Article types and their custom fields, dot-qualified as `Knowledge__kav.<Field>__c` |
| `profiles/<Name>.profile-meta.xml` | The `categoryGroupVisibilities` blocks — the only place article visibility can be deployed |
| Verification query output | `Knowledge__kav` rows by `PublishStatus` + `Language`, and the matching `Knowledge__DataCategorySelection` rows |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing deployable `KnowledgeSettings`, `DataCategoryGroup`, `Knowledge__kav` record type and field, `Profile` / `PermissionSet` XML, the package.xml, the retrieve/deploy commands, the verification SOQL, and the `KbManagement.PublishingService` snippet |
| `references/gotchas.md` | Eleven platform behaviours behind most Knowledge incidents — silent category deletion on deploy, missing `objectUsage`, visibility stranded on the profile, wildcard manifests that retrieve nothing, and the article-SOQL rules |
| `references/examples.md` | Worked multi-audience visibility design, the approval-process layering, and the permission-sets-alone anti-pattern |
| `references/well-architected.md` | Pillar mapping, the native-status vs Validation Status vs approval tradeoff, and the source list behind every claim in this package |
| `references/llm-anti-patterns.md` | Self-checking generated output — the ways an assistant gets Lightning Knowledge wrong |
| `templates/knowledge-base-administration-template.md` | Capturing the design before building it: context, record type matrix, category matrix, workflow choice, and the build checklist |
| `scripts/check_knowledge_base_administration.py` | Linting a retrieved metadata directory before deploy (`--manifest-dir`) |

---

## Related Skills

- `architect/knowledge-taxonomy-design` — Owns taxonomy *sizing and shape* (how many groups, how deep, which axes). Read it before writing any `DataCategoryGroup` XML; this skill owns the deployable metadata that results
- `admin/knowledge-classic-to-lightning` — Use instead of this skill when the org is still on Knowledge in Salesforce Classic with per-type `__kav` objects that must become record types
- `data/knowledge-article-import` — Use when articles arrive in bulk from an external help centre; imported articles land in Draft and need an explicit publish before any visibility design takes effect
- `admin/record-types-and-page-layouts` — Use for the record type and layout mechanics themselves, including why a record type is not an access control
- `architect/knowledge-vs-external-cms` — Use when deciding whether to use Salesforce Knowledge or an external CMS for content management
- `agentforce/einstein-copilot-for-service` — Knowledge article quality directly bounds Einstein Service Replies grounding quality; review both skills when deploying AI-assisted service
- `admin/delegated-administration` — Use alongside this skill when Knowledge article management responsibilities are delegated to non-admin users

Taxonomy *design or audit* for a whole org is the job of the `/design-knowledge-taxonomy` run-time agent (`agents/knowledge-article-taxonomy-agent/AGENT.md`), which cites this skill for the admin setup and deployable shapes.
