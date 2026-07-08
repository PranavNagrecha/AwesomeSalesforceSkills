# Gotchas — Knowledge Base Administration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Lightning Knowledge Cannot Be Disabled After Enablement

**What happens:** Once an admin enables Lightning Knowledge in Setup > Knowledge Settings, the feature cannot be turned off. Classic Knowledge article types are permanently converted to record types on the `Knowledge__kav` object. The disable toggle is removed from the UI. All subsequent Knowledge configuration must be done in the Lightning Knowledge framework.

**When it occurs:** Any time an admin or developer enables Lightning Knowledge — including in sandbox orgs. Sandbox refreshes from a production org where Lightning Knowledge is enabled will have the feature enabled in the refreshed sandbox as well.

**How to avoid:** Treat Lightning Knowledge enablement as an architectural decision requiring stakeholder sign-off, not a configuration toggle. Design record types, page layouts, and Data Category Groups before enabling. Enable in a Developer sandbox first to validate the design, then promote the configuration through change management before enabling in production.

---

## Gotcha 2: Activating a Category Group Hides Classified Articles — Uncategorized Ones Stay Visible

**What happens:** The intuition most teams carry is backwards. Uncategorized articles are the ones that survive a restrictive visibility configuration. The Knowledge Implementation Guide states that when data category visibility is configured, "users with no data category visibility by role, permission set, or profile, only see uncategorized articles and questions unless you make the associated categories visible by default," and that revoking a group's visibility (setting it to *None*) leaves those users able to see "articles and questions that aren't classified with a category in that category group." Because a user "can see an article if they can see at least one category per category group on the article," it is *classification* that exposes an article to the visibility check.

Uncategorized articles do have a defect, but a milder one: per the same guide, "If an article has no categories, it displays only when you choose the No Filter option in the category drop-down menu." They are unbrowsable, not invisible.

**When it occurs:** When an admin activates a new Data Category Group and classifies existing articles against it. Every user without visibility to at least one category in that group loses those articles the moment the classification lands — no error, no warning. It also occurs on the flip side, when authors leave articles uncategorized and then cannot find them by browsing categories, and conclude (wrongly) that the articles are hidden.

**How to avoid:** Treat category-group activation as the risky operation. Category groups are hidden from users until activated, so finish defining categories *and* their visibility settings before flipping the switch, then re-test each audience segment. Separately, train authors to assign at least one category so their articles are browsable, and consider Validation Status or an Approval Process entry criterion that checks for category assignment before publish. Never explain a missing article with "it has no categories" until you have checked what the reader's visibility to the article's groups actually is.

---

## Gotcha 3: Publishing a New Version Immediately Archives the Current Published Version

**What happens:** When an author publishes a new version of an existing article, Salesforce instantly transitions the currently published version to Archived status. There is no "schedule for future publish" option and no grace period. The old published version is no longer visible to users the moment the new version is published.

**When it occurs:** Any time an author clicks "Publish" on a draft version of an article that already has a published version. Common during content refresh cycles when authors revise and publish articles without realizing the swap is instantaneous.

**How to avoid:** Review new article versions carefully before publishing, as there is no rollback to the previous published version (the archived version exists but must be explicitly restored, creating a new published version from it). Build the review step into the pre-publish workflow — either through Approval Processes or Validation Status checks that require sign-off before the Publish action is available. For critical articles, export the current published content before publishing a new version as a backup reference.

---

## Gotcha 4: The Parent Role Is a Ceiling on Child Data Category Visibility

**What happens:** Salesforce's wording is exact: "Child roles inherit their parent role's settings and are kept in sync with changes to the parent role. You can customize and reduce the child role's visibility, but you can't increase it to be greater than that of the parent role."

That single sentence carries two behaviors that get conflated. First, inheritance grants but never narrows — a child that should see fewer categories than its parent must be configured explicitly, because leaving it alone means it keeps the parent's full set and tracks the parent's future changes. Second, and more surprising, the parent is a hard ceiling — a child role cannot be granted a category its parent role lacks, no matter how the child's settings are edited.

**When it occurs:** The first behavior bites when organizations design role hierarchies for reporting rollup (broad visibility at the top) and then try to reuse the same hierarchy to restrict Knowledge visibility. The second bites when a specialist team sits low in the hierarchy under a generalist manager and needs a niche product category the manager's role has no reason to see.

**How to avoid:** Configure Data Category visibility explicitly at each role level rather than relying on inheritance. When a child role legitimately needs visibility its parent does not have, stop using the role hierarchy for that grant and assign the visibility by permission set instead — role, permission set, and profile definitions are combined with a logical OR, so the permission set adds the category without disturbing the role tree. The same lever is mandatory for guest users and high-volume portal users, who have no role at all.

---

## Gotcha 5: Approval Process on Knowledge__kav Requires "Manage Articles" to Submit — Not Just Article Ownership

**What happens:** Authors who own a draft article but lack the "Manage Articles" user permission cannot submit their own article for approval. The "Submit for Approval" button either does not appear or returns an insufficient privileges error. This breaks approval-gated publishing workflows silently — authors think the approval process is broken when in fact it is a permission gap.

**When it occurs:** When admins build Approval Processes on `Knowledge__kav` but assign the "Manage Articles" permission only to senior agents or admins, leaving junior authors without the permission needed to trigger the approval gate themselves.

**How to avoid:** Audit the profile/permission set for Knowledge authors and confirm "Manage Articles" is enabled. This permission also grants the ability to publish, archive, and delete articles directly — if those actions should be restricted to approvers, pair the Approval Process with criteria-based restrictions or a separate Validation Status workflow that signals readiness without granting direct publish access.

---

## Gotcha 6: Articles Cannot Display Outside the Org Until Topics Are Enabled on the Knowledge Object

**What happens:** An article is Published, assigned to a Data Category the audience can see, flagged for the Customer channel, and the Experience Cloud site is live — and the article still does not appear anywhere on the site. Salesforce's Trailhead project *Build an Experience Cloud Site with Knowledge and Enhanced Chat* (unit: *Enable and Configure Lightning Knowledge*) states the prerequisite directly: "Without enabling Salesforce Knowledge topics, articles can't be displayed outside an org." Until Setup > Topics for Objects > Knowledge has Enable Topics turned on (with at least the Title field selected), no article renders on any site.

**When it occurs:** Every first-time Knowledge-on-Experience-Cloud rollout, because org-level Knowledge enablement and article publishing both succeed without ever prompting for Topics. It also occurs after a sandbox-to-production deployment where the Topics-for-Objects setting was never captured in the change set, leaving production with a fully configured site and zero visible articles.

**How to avoid:** Enable Topics on the Knowledge object as the first step of any Experience Cloud exposure work, before touching channel flags, permission sets, or Experience Builder. When a "channel flag is set but articles do not appear" ticket arrives, check Topics before debugging anything else — it is the single most common root cause and the failure mode is silent. Nothing logs, nothing errors, the page just renders empty.

---

## Gotcha 7: Guest Knowledge Access Is Three Independent Gates and Failing Any One Yields an Empty Page

**What happens:** An admin grants the site's Guest User profile Read on the Knowledge object, expecting public articles to appear. Nothing renders. Unauthenticated Knowledge access requires three separate, unrelated configurations: (1) the article carries the Public Knowledge Base designation, (2) the site's Guest User profile has Knowledge object access — granted directly on the profile or via a permission set assigned to the guest user, and (3) guest Data Category Visibility is explicitly configured on that profile or permission set. Salesforce Help's *View Knowledge Base Articles on a Lightning Platform Site* (Knowledge Article 000382935) is explicit that "only articles marked as Public Knowledge Base will be available to guest users," and separately that the Guest User associated with the site must be granted access.

Gate (3) has its own trap: guest users have no role, so role-based Data Category Visibility can never reach them. The Knowledge Implementation Guide says the same thing about high-volume portal users — "Because high-volume portal users don't have roles, you must designate visibility settings by permission set or profile before these users can view categorized articles and questions."

**When it occurs:** When teams reason about guest access using the standard sharing mental model — object permission plus sharing rule — and never discover the channel flag or the category visibility layer. It also occurs when authors publish new public content but forget the Public Knowledge Base channel, so a public knowledge base slowly goes stale without anyone noticing new articles are missing.

**How to avoid:** Treat the three gates as a checklist, not a chain of inference, and verify by loading an article URL in a logged-out private browser window. An authenticated Experience Builder preview runs as the admin and will happily render articles a real guest cannot see. Also configure Knowledge Settings > Share Article via URL to designate which site hosts the public article URLs, otherwise the URLs agents share from a case will not resolve for the recipient.

---

## Gotcha 8: Choosing the Help Center Template Does Not Make the Customer Channel Reach Guests

**What happens:** Salesforce Help describes the Help Center template as a public-access, self-service site that exposes the articles you make available from your knowledge base, and as a public-facing portal where guest users search that knowledge base. Teams read "customers," reach for the Customer channel, set `IsVisibleInCsp = true`, and ship a public site whose article pages are empty for every visitor who has not logged in.

The channel flags are defined by reader, not by template. The `Knowledge__kav` object reference is unambiguous: `IsVisibleInCsp` indicates "whether the article is visible in the Customer Portal" (authenticated customer users), while `IsVisibleInPkb` indicates "whether the article is visible in the public knowledge base" (guests). The Classic article-import channel keywords make the same split — `csp` for Customer, `sites` for Public Knowledge Base.

**When it occurs:** On the first Help Center rollout, where the site name and template description both say "customers" and nothing in the UI warns that an unauthenticated visitor is evaluated as a guest. It also occurs on mixed sites that serve both logged-in customers and anonymous visitors, where only one of the two flags gets set and half the audience silently sees nothing.

**How to avoid:** Decide the channel from the reader, not the template. Unauthenticated visitor → `IsVisibleInPkb`. Authenticated customer user → `IsVisibleInCsp`. A Help Center serving both needs both flags on the articles both audiences should read. Verify each audience separately: a logged-out private browser window for the guest path, a real portal login for the authenticated path.
