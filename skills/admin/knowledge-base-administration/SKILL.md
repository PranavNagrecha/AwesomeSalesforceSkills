---
name: knowledge-base-administration
description: "Use this skill when setting up, configuring, or managing Salesforce Lightning Knowledge — including enabling the feature, designing record types on Knowledge__kav, configuring Data Categories and Data Category Visibility for organization and access control, setting the four publishing channels, exposing articles on an Experience Cloud site or Help Center (Topics, guest access), setting up publishing workflows, and layering approval processes. Trigger keywords: Lightning Knowledge setup, Knowledge article record types, Data Category visibility, Knowledge publishing channels, publish Knowledge to Experience Cloud, Help Center Knowledge base, Knowledge publishing workflow, Knowledge__kav configuration. NOT for building, branding, or activating the Experience Cloud site itself (use admin/experience-cloud-site-setup), NOT for Einstein Article Recommendations surfacing (use agentforce/einstein-copilot-for-service), NOT for Knowledge search tuning or Apex programmatic article management."
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
  - "Publish Knowledge articles to an Experience Cloud site so customers can self-serve"
  - "Expose a public Knowledge base to guest users on a Help Center site"
tags:
  - knowledge
  - lightning-knowledge
  - data-categories
  - knowledge-base
  - publishing-workflow
  - record-types
  - experience-cloud
  - help-center
  - topics
  - guest-user
inputs:
  - "Confirmation that Lightning Knowledge is enabled (or the intent to enable it — irreversible decision)"
  - "List of article types or content categories needed (e.g., FAQ, How-To, Known Issue)"
  - "Audience segments requiring different article visibility (internal agents, partners, customers)"
  - "Publishing surfaces in scope (internal app only, authenticated Experience Cloud site, public/guest Knowledge base)"
  - "Approval or review process requirements before articles can be published"
outputs:
  - "Lightning Knowledge configuration plan with record type layout per audience"
  - "Data Category Group structure with role/profile/permission-set visibility assignments"
  - "Channel matrix mapping each record type to the Internal App / Customer / Partner / Public Knowledge Base channels"
  - "Experience Cloud exposure plan (Topics enablement, site-level Knowledge enablement, Experience Builder component placement, guest user access)"
  - "Publishing workflow decision: native statuses only vs. Validation Status picklist vs. full approval process"
  - "Review checklist confirming the Knowledge setup is production-ready"
dependencies: []
version: 1.1.1
author: Pranav Nagrecha
updated: 2026-07-08
---

# Knowledge Base Administration

This skill activates when an admin or architect needs to set up or manage Salesforce Lightning Knowledge — covering the one-time enablement decision, record type design on the `Knowledge__kav` object, Data Category configuration for dual-purpose organization and access control, channel selection and Experience Cloud exposure, and publishing workflow design using native statuses, Validation Status, and optional approval processes.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Lightning Knowledge enabled?** Navigate to Setup > Knowledge Settings. If the toggle is OFF, understand that enabling it is irreversible — once turned on, Classic Knowledge article types are permanently replaced by Lightning Knowledge record types on the single `Knowledge__kav` object. There is no undo path.
- **Most common wrong assumption:** Practitioners often assume Data Categories are purely organizational (like tags). In reality, they serve dual duty: content categorization AND access control. A user must have visibility to at least one category in every Data Category Group assigned to an article in order to see that article. Misconfigured visibility silently hides articles from users who expect to see them.
- **Which surfaces are in scope?** Publishing an article does not, by itself, put it in front of anyone outside the internal app. Establish up front whether the content must reach an authenticated Experience Cloud audience (customer or partner), an unauthenticated guest audience (public Knowledge base), or neither. Each surface adds a separate configuration axis — channel flags, Topics, Data Category Visibility, and (for guest) the site's Guest User profile.
- **Platform constraints:** The Knowledge Implementation Guide's Data Category Limits table gives the defaults: *"5 category groups, with 3 active at a time,"* 100 categories per group, 5 levels of hierarchy, and a maximum of 8 categories from one group assigned to a single article. The 3-active ceiling binds before the 5-group ceiling, because a category group is hidden from users until it is activated. Salesforce Support can raise the group and category limits on request.

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

**Role-based visibility is capped by the parent role, not merely additive.** The Knowledge Implementation Guide is precise: *"Child roles inherit their parent role's settings and are kept in sync with changes to the parent role. You can customize and reduce the child role's visibility, but you can't increase it to be greater than that of the parent role."* A parent sets a ceiling. A child can be narrowed below it, never widened above it. Users with no role at all — guest users and high-volume portal users — cannot receive role-based visibility, so their visibility must come from a permission set or profile.

**Uncategorized articles are not hidden — this is the most commonly inverted fact in the domain.** Per the same guide, once data category visibility is configured, "users with no data category visibility by role, permission set, or profile, only see uncategorized articles and questions unless you make the associated categories visible by default." Revoking a group's visibility (setting it to *None*) leaves those users able to see "articles and questions that aren't classified with a category in that category group." What uncategorized articles suffer is unbrowsability, not invisibility: *"If an article has no categories, it displays only when you choose the No Filter option in the category drop-down menu."* The real disappearing-article mechanism runs the other way — activate a category group, classify articles against it, and every user without visibility to one of its categories loses those articles. (There is no "Manage Categories" permission; the system permission is **Manage Data Categories**.)

**Default visibility** — what a user sees when no role, permission set, or profile grants them anything — is a separate org-wide fallback, documented by Salesforce Help as *Modify Default Data Category Visibility* (Setup, Quick Find: **Default Data Category Visibility**). It is not a guest-specific screen, and it does not substitute for assigning visibility to the Guest User profile.

**How visibility is actually configured.** Salesforce Help documents three Data Category Visibility settings — *All Categories*, *None*, and *Custom* — and each can be set on a role, a permission set, or a profile. When visibility is defined in more than one place for the same user, Salesforce combines the definitions with a logical OR to produce that user's effective visibility rule. This matters for Experience Cloud: external users sit in portal roles that are frequently generic, so permission-set-based visibility is often the practical lever for customer and partner audiences rather than role-based visibility.

### Publishing Channels: Where an Article Actually Appears

Publishing an article version sets it live; it does not decide *who sees it*. That is the job of the channel flags carried on each `Knowledge__kav` (KnowledgeArticleVersion) record. Four standard boolean fields map one-to-one onto four audience surfaces:

| Channel | `Knowledge__kav` field | Audience |
|---|---|---|
| Internal App | `IsVisibleInApp` | Internal Salesforce users (agents, authors) |
| Customer | `IsVisibleInCsp` | Authenticated customer users on an Experience Cloud site |
| Partner | `IsVisibleInPrm` | Authenticated partner users on an Experience Cloud site |
| Public Knowledge Base | `IsVisibleInPkb` | Unauthenticated guest users of a public site |

Only three of the four flags are writable. The `Knowledge__kav` object reference lists `IsVisibleInCsp`, `IsVisibleInPrm`, and `IsVisibleInPkb` with Properties *Create, Defaulted on create, Filter, Group, Sort, Update*, while `IsVisibleInApp` carries only *Defaulted on create, Filter, Group, Sort* — it is neither createable nor updateable through the API. Treat the internal-app channel as a given and the three external flags as the design surface.

Channels are a *publishing* control, orthogonal to Data Category Visibility (an *access* control). An article can be flagged Customer and still be invisible to a customer whose Data Category Visibility excludes every category on that article — and vice versa. Treat the channel matrix as a deliberate design artifact per record type, not as a checkbox authors tick from memory.

Authors and managers cannot set the external channels without the right permissions. Salesforce's Lightning Knowledge access guidance provisions a Knowledge manager permission set with full object CRUD on Knowledge plus View All Records / Modify All Records, the app permissions **Manage Articles**, **Manage Knowledge Article Import/Export**, **Manage Salesforce Knowledge**, **Publish Articles**, and **Share internal Knowledge articles externally**, and the system permission **Manage Data Categories**. (View Archived Articles and View Draft Articles are enabled automatically.) Separately, Salesforce Help's public-Knowledge guidance calls out checking the **Knowledge User** checkbox on the user record before that user can author or manage articles at all.

### Surfacing Knowledge on an Experience Cloud Site

Getting an article onto a site is a four-part configuration, and skipping any part produces an empty page rather than an error:

1. **Enable Topics on the Knowledge object.** Setup > Topics for Objects > Knowledge > Enable Topics, then select at least one field (Title) to be scanned. Salesforce's Trailhead project *Build an Experience Cloud Site with Knowledge and Enhanced Chat* (unit: *Enable and Configure Lightning Knowledge*) states the prerequisite directly: *"Without enabling Salesforce Knowledge topics, articles can't be displayed outside an org."*
2. **Enable Knowledge on the site.** Salesforce Help documents a distinct site-level step — *Enable Salesforce Knowledge in Your Experience Cloud Site*. Org-level Knowledge enablement does not imply site-level enablement.
3. **Flag the articles for the audience that will actually read them.** Set the channel that matches the reader: `IsVisibleInCsp` (*Visible to Customer*) for authenticated customer users, `IsVisibleInPrm` for authenticated partner users, `IsVisibleInPkb` for unauthenticated guests. Then assign Topics to the articles — manually in Experience Workspaces > Content Management > Topics > Article Management, or with Automatic Topic Assignment. Navigational Topics build the site's browse structure; Featured Topics highlight a curated subset on the home page.
4. **Place the components.** In Experience Builder, drop the Knowledge components that render the content — Topic Catalog, Top Articles by Topic, Trending Articles by Topic, Articles with This Topic, Article Content. Without a component bound to the topic or article, correctly flagged and correctly categorized articles still render nowhere.

Salesforce also ships a purpose-built template for this exact job. The **Help Center** template is described as a public-access, self-service site that exposes the articles you make available from your knowledge base, and as a public-facing portal where guest users search that knowledge base — as distinct from the general-purpose community templates, which require you to assemble the same Knowledge surface by hand. Prefer Help Center when self-service article browsing is the primary use case.

Note what "public-access" implies for the channel decision: a visitor who arrives without logging in is a guest, and guests are evaluated against the **Public Knowledge Base** channel (`IsVisibleInPkb`), not the Customer channel. `IsVisibleInCsp` governs authenticated customer users. Choosing the Help Center template does not change which flag a given reader is evaluated against — a Help Center serving both guests and logged-in customers needs both flags set.

For an unauthenticated public Knowledge base, two additional gates apply, both independent of the internal Knowledge User setup: the site's **Guest User profile** must be granted Knowledge object access (directly on the profile or via a permission set), and only articles carrying the **Public Knowledge Base** designation are eligible for guest visibility. Because guest users have no role, their Data Category Visibility must also be set on that profile or permission set. Knowledge Settings' *Share Article via URL* settings determine which site hosts the shared article URLs.

### Publishing Workflow: Statuses, Validation Status, and Approval Processes

Every Knowledge article version moves through three native platform statuses. The UI labels and the API values do not match: the `Knowledge__kav` object reference defines `PublishStatus` as a restricted picklist with the values `Draft`, `Online` ("articles published in Salesforce Knowledge"), and `Archived`. SOQL and SOSL filters therefore use `PublishStatus = 'Online'`, never `'Published'`, and the object reference requires that every article query specify either `PublishStatus` or `Id` in the `WHERE` clause.

- **Draft** (`PublishStatus = 'Draft'`): Article is being authored or edited. Not visible to end users.
- **Published** (`PublishStatus = 'Online'`): Article is live. Exactly one published version can exist per article at any time. Publishing a new version automatically archives the previous published version. The object reference notes that a user "must have the 'Manage Articles' permission enabled to use Online."
- **Archived** (`PublishStatus = 'Archived'`): Article is retired from public view but preserved for history and potential restoration. When querying archived articles, also filter `IsLatestVersion = false`.

On top of native statuses, admins can enable a **Validation Status** picklist on `Knowledge__kav`. This is an admin-customizable picklist (values like "Validated", "Not Validated", "In Review") that signals content quality. Validation Status is separate from publish status — an article can be Published but flagged as "Not Validated." Agents can filter article searches by Validation Status to surface only quality-assured content.

For organizations requiring formal review before publishing, Salesforce supports standard **Approval Processes** on `Knowledge__kav`. An approval process can require sign-off from a subject-matter expert before a Draft article can transition to Published. Approval processes on Knowledge articles use the same Process Builder/Flow-backed approval framework as other objects, with the constraint that only the record owner or users with "Manage Articles" permission can submit articles for approval.

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
1. Create Data Category Groups from Setup > Data Category Setup. Defaults allow 5 groups with 3 active at a time; a group is hidden from users until it is activated, so activate only after its categories and visibility are finalized.
2. Design the hierarchy to reflect your content taxonomy (e.g., "Products > Product A > Feature X"). Making a category visible exposes its whole direct family line — ancestors, parent, children, and other descendants — but not siblings.
3. In Setup > Roles, assign category visibility per role (All Categories / None / Custom). A child role inherits the parent's settings and stays in sync with them; you can customize and reduce a child role's visibility, but you cannot raise it above the parent's.
4. Test visibility by logging in as a representative user from each role before go-live.
5. Guest users and high-volume portal users have no role, so assign their Data Category Visibility on the Guest User profile or a permission set assigned to it. The org-wide fallback for users with no visibility from any source is configured separately under *Default Data Category Visibility*.

**Why not the alternative:** Using only object-level sharing or permission sets for article access bypasses the Data Category visibility check — articles classified into an active group remain invisible even if the user has object read access unless category visibility is also configured.

### Pattern: Self-Service Knowledge Base on a Help Center Site

**When to use:** When the goal is case deflection — letting customers find answers themselves instead of opening a case — and article browsing is the site's primary purpose rather than one feature among many.

**How it works:**
1. Provision a Knowledge manager permission set (object CRUD on Knowledge, Manage Articles, Publish Articles, Share internal Knowledge articles externally, Manage Data Categories) and confirm the Knowledge User checkbox on each author's user record.
2. Enable Topics on the Knowledge object in Setup > Topics for Objects and select the Title field.
3. Create the site from the **Help Center** template rather than a general community template — Knowledge search, article pages, and topic navigation are pre-wired.
4. Enable Salesforce Knowledge on the site itself, a distinct step from org-level enablement.
5. Set the channel that matches who reads the article. Help Center is a public-access site, so unauthenticated visitors require the Public Knowledge Base channel (`IsVisibleInPkb`); add the Customer channel (`IsVisibleInCsp`) only if authenticated customer users also read the site. Then assign Data Category Visibility (All / None / Custom) to that audience — by permission set or profile for guest and high-volume portal users, who have no role — and assign Topics in Experience Workspaces > Content Management > Topics.
6. Configure Navigational Topics for the browse tree and Featured Topics for the home page, then verify the Experience Builder pages carry the Knowledge components.

**Why not the alternative:** Building the same surface on a general template means hand-assembling article pages, topic routing, and search — and it is easy to end up with the channel flag set but Topics never enabled, at which point articles are simply absent from the site with no error anywhere.

### Pattern: Public (Unauthenticated) Knowledge Base

**When to use:** When articles must be readable without login — indexed by search engines, linkable from support emails, reachable before a customer has a portal account.

**How it works:**
1. Set the Public Knowledge Base channel on the articles that are cleared for public release. Treat this as a content-governance decision, not an author convenience.
2. Grant the site's Guest User profile access to the Knowledge object, directly on the profile or through a permission set assigned to the guest user.
3. Configure guest Data Category Visibility explicitly on the Guest User profile or on a permission set assigned to it. Guest users have no role, so role-based visibility never reaches them, and the org-wide *Default Data Category Visibility* fallback is not a substitute for an explicit assignment.
4. Configure Knowledge Settings > Share Article via URL to designate which site hosts the public article URLs.
5. Verify by loading an article URL in a private browser window with no session.

**Why not the alternative:** Adding guest users to a sharing rule or a permission set that grants Knowledge read is not sufficient on its own — an article missing the Public Knowledge Base channel will never render to a guest, and a guest with no Data Category Visibility sees nothing regardless of object access.

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
| Customers need self-service article browsing as the site's primary job | Help Center template + Topics on Knowledge + Public Knowledge Base channel (add the Customer channel if authenticated customers also read it) | Help Center is documented as a public-access self-service site; unauthenticated readers are guests and are evaluated against `IsVisibleInPkb`, not `IsVisibleInCsp` |
| Knowledge is one feature inside an existing customer or partner site | Enable Knowledge on the existing site, set the Customer/Partner channel, add Knowledge components in Experience Builder | Avoids a second site and a second membership model for a secondary use case |
| Articles must be readable without login | Public Knowledge Base channel + Guest User profile Knowledge access + explicit guest Data Category Visibility | All three gates are independent; missing any one produces a silently empty page |
| External users share a generic portal role, or have no role at all | Assign Data Category Visibility via permission set or profile rather than role | Guest and high-volume portal users have no role; role, permission set, and profile visibility are combined with a logical OR, so permission sets give per-audience precision when roles are coarse or absent |
| A child role must see fewer categories than its parent | Configure that child role's visibility explicitly (reduce it); never expect inheritance to narrow it | Child roles inherit and stay in sync with the parent; you can reduce a child's visibility but cannot raise it above the parent's |
| Articles are flagged for a channel but do not appear on the site | Verify Topics are enabled on the Knowledge object before debugging anything else | Trailhead's Knowledge-on-Experience-Cloud project states articles can't be displayed outside an org without Knowledge topics enabled |

---

## Recommended Workflow

Step-by-step instructions for an admin or agent working on Knowledge setup:

1. **Confirm readiness for irreversible enablement**: Verify that all stakeholders understand Lightning Knowledge cannot be disabled once enabled. Document the decision. Confirm whether Classic Knowledge is in use and whether a migration plan exists for existing articles.
2. **Design record types before enabling**: Map out the content types needed (e.g., FAQ, How-To, Known Issue). Determine which fields belong on each layout. Plan profile-to-record-type assignments. This design is much harder to change after articles are created at scale.
3. **Enable Lightning Knowledge and configure record types**: Toggle Lightning Knowledge in Setup > Knowledge Settings. Create record types in Object Manager > Knowledge > Record Types. Build page layouts per record type. Assign record types to author profiles.
4. **Design and activate Data Category Groups**: Create category groups in Setup > Data Category Setup, staying within the default 5 groups / 3 active. Build the hierarchy, then activate — an inactive group is hidden from users. Assign Data Category Visibility (All Categories / None / Custom) on roles, permission sets, or profiles — remembering that Salesforce ORs these definitions together for each user, that a child role can be reduced below its parent but never raised above it, and that guest and high-volume portal users have no role and must be covered by permission set or profile. Test visibility by logging in as a test user from each audience segment.
5. **Set publishing channels and configure the publishing workflow**: Build the channel matrix per record type across Customer (`IsVisibleInCsp`), Partner (`IsVisibleInPrm`), and Public Knowledge Base (`IsVisibleInPkb`) — the three writable flags; `IsVisibleInApp` is defaulted on create and not settable through the API. Match the flag to the reader: guests need `IsVisibleInPkb` even on a Help Center site. Decide whether native statuses are sufficient, or whether Validation Status and/or Approval Processes are needed. Enable Validation Status under Knowledge Settings if required. Build Approval Processes in Setup > Approval Processes targeting the Knowledge__kav object if formal sign-off is needed. If any article must reach an Experience Cloud site, also complete the exposure chain in order:
   - Provision the Knowledge manager permission set (object CRUD, Manage Articles, Publish Articles, Share internal Knowledge articles externally, Manage Data Categories) and confirm the Knowledge User checkbox on each author.
   - Enable Topics on the Knowledge object (Setup > Topics for Objects > Knowledge), selecting the Title field — articles cannot display outside the org without this.
   - Enable Salesforce Knowledge on the site itself, separately from org-level enablement.
   - Assign Topics to articles (Content Management > Topics > Article Management or Automatic Topic Assignment), configure Navigational and Featured Topics, and place the Knowledge components in Experience Builder.
   - For public access, grant the site's Guest User profile Knowledge object access and set guest Data Category Visibility explicitly on that profile or a permission set assigned to it.
6. **Pilot and validate**: Have representative authors create articles of each record type, assign to categories and topics, submit through the publishing workflow. Confirm visibility for each audience segment, including a logged-out browser check for any public Knowledge base. Check that archived versions are preserved correctly.
7. **Document operational procedures**: Record the record type taxonomy, Data Category structure, channel matrix, and publishing workflow in an internal admin runbook. Knowledge administration decisions compound over time — undocumented decisions lead to inconsistent setups.

---

## Review Checklist

Run through these before marking Knowledge setup work complete:

- [ ] Lightning Knowledge enablement decision documented and acknowledged as irreversible
- [ ] Record types created with appropriate page layouts per content type
- [ ] Record types assigned to correct author profiles
- [ ] Data Category Groups created and activated within the default limits (5 groups, 3 active at a time)
- [ ] Role/profile/permission-set visibility assigned for each audience; guest and high-volume portal users covered by profile or permission set, not role
- [ ] No child role expected to see categories its parent role cannot see
- [ ] Uncategorized article behavior understood — such articles stay visible but surface only under the No Filter category option; activating a new group is what hides classified articles
- [ ] Publishing workflow configured (native statuses, Validation Status, and/or Approval Process)
- [ ] Channel matrix defined per record type across the three writable flags (Customer / Partner / Public Knowledge Base); guest-facing articles carry `IsVisibleInPkb`
- [ ] Knowledge manager permission set includes "Share internal Knowledge articles externally" if content leaves the org
- [ ] Topics enabled on the Knowledge object (Setup > Topics for Objects) if articles surface outside the org
- [ ] Salesforce Knowledge enabled on the Experience Cloud site itself, not just at org level
- [ ] Topics assigned to articles; Navigational and Featured Topics configured
- [ ] Knowledge components placed on the relevant Experience Builder pages
- [ ] Guest User profile granted Knowledge object access and explicit Data Category Visibility on the profile or an assigned permission set (public Knowledge base only)
- [ ] Public article URL loaded in a logged-out browser session (public Knowledge base only)
- [ ] At least one test article created, published, and verified visible to each intended audience
- [ ] Archived version behavior verified (previous published version archived on re-publish)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Lightning Knowledge enablement is irreversible** — Once you enable Lightning Knowledge in Setup, there is no disable toggle. Classic Knowledge article types are permanently converted to record types on `Knowledge__kav`. Do not enable in production without a complete design review and stakeholder sign-off.
2. **Activating a category group hides *classified* articles; uncategorized ones stay visible** — The folk belief runs backwards. Salesforce documents that users with no data category visibility "only see uncategorized articles and questions," and that revoking a group (visibility = None) still lets them see "articles and questions that aren't classified with a category in that category group." What actually breaks is activation: switch on a new Data Category Group, classify existing articles against it, and every user without visibility to one of its categories loses those articles instantly. Uncategorized articles have a milder, separate trap — they display "only when you choose the No Filter option in the category drop-down menu," so they are unbrowsable rather than invisible.
3. **Publishing a new version archives the previous one immediately** — There is no "schedule replacement" option. When you click Publish on a new version, the currently published version transitions to Archived instantly. If the new version has errors, you must immediately restore or publish a corrected version — there is no rollback to the previous published state.
4. **Role-based category visibility is capped by the parent role, not additive without limit** — Salesforce's wording is exact: "Child roles inherit their parent role's settings and are kept in sync with changes to the parent role. You can customize and reduce the child role's visibility, but you can't increase it to be greater than that of the parent role." Two consequences. Inheritance never narrows a child on its own, so a child that should see less must be configured explicitly. And a child can never see *more* than its parent, so a front-line role needing a category its manager's role lacks cannot get it from the role hierarchy at all — grant it by permission set.
5. **Approval Processes on Knowledge__kav require "Manage Articles" to submit** — Only the article owner or a user with the "Manage Articles" permission can submit a Knowledge article for approval. If authors lack this permission, they cannot trigger the approval workflow, breaking the publishing gate. Assign "Manage Articles" to author profiles intentionally.
6. **Articles cannot leave the org until Topics are enabled on the Knowledge object** — Salesforce's Trailhead project *Build an Experience Cloud Site with Knowledge and Enhanced Chat* states it plainly: "Without enabling Salesforce Knowledge topics, articles can't be displayed outside an org." A correctly published, correctly categorized, Customer-flagged article on a live Experience Cloud site renders nowhere if Setup > Topics for Objects > Knowledge has Topics disabled. No error surfaces anywhere; the page is simply empty.
7. **Guest Knowledge access is three independent gates, not one** — Exposing articles to unauthenticated users requires the Public Knowledge Base channel on the article, Knowledge object access on the site's Guest User profile, and explicit guest Data Category Visibility on that profile or an assigned permission set. These are separate from the internal Knowledge User setup and from each other. Granting object access alone to the guest profile produces a public page with zero articles.
8. **A Help Center does not make the Customer channel reach guests** — The template is public-access, which means most of its readers are unauthenticated. `IsVisibleInCsp` addresses authenticated customer users; guests are matched against `IsVisibleInPkb`. Teams that pick Help Center for "customers" and then flag articles *Visible to Customer* ship a public site whose article pages are empty for everyone who has not logged in.
9. **`IsVisibleInApp` cannot be set through the API** — The object reference gives it Properties *Defaulted on create, Filter, Group, Sort* — no Create, no Update — while the three external channel flags are createable and updateable. Data loads and Apex that try to write the internal-app channel alongside the external ones will fail on that field.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Knowledge Setup Decision Document | Records the Lightning Knowledge enablement decision, confirming it is irreversible and that stakeholders have approved |
| Record Type Taxonomy | Table of record types, associated layouts, and profile assignments |
| Data Category Group Map | Hierarchy diagram of category groups with role/profile/permission-set visibility matrix per audience |
| Channel Matrix | Table mapping each record type to the Internal App / Customer / Partner / Public Knowledge Base channels, with the governance owner for each external channel |
| Experience Cloud Exposure Plan | Topics enablement, site-level Knowledge enablement, Topic assignment strategy, Experience Builder component placement, and guest user access (if public) |
| Publishing Workflow Decision | Documents choice of native statuses / Validation Status / Approval Process and the rationale |
| Admin Runbook | Operational procedures for ongoing Knowledge management (creating article types, updating categories, managing approvals) |

---

## Related Skills

- `architect/knowledge-vs-external-cms` — Use when deciding whether to use Salesforce Knowledge or an external CMS for content management
- `architect/knowledge-taxonomy-design` — Use when designing the Data Category and Topic taxonomy itself rather than configuring the platform
- `admin/experience-cloud-site-setup` — Use to build, brand, and activate the Experience Cloud site that this skill exposes Knowledge on
- `admin/experience-cloud-guest-access` — Use when designing the guest user profile and public access settings for an unauthenticated Knowledge base
- `admin/knowledge-classic-to-lightning` — Use when migrating an existing Classic Knowledge deployment rather than standing up a new one
- `agentforce/einstein-copilot-for-service` — Knowledge article quality directly bounds Einstein Service Replies grounding quality; review both skills when deploying AI-assisted service. Also the home for Einstein Article Recommendations
- `admin/delegated-administration` — Use alongside this skill when Knowledge article management responsibilities are delegated to non-admin users
