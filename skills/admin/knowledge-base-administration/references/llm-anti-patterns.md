# LLM Anti-Patterns — Knowledge Base Administration

Common mistakes AI coding assistants make when generating or advising on Knowledge Base Administration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating Lightning Knowledge Enablement as Reversible

**What the LLM generates:** "Enable Lightning Knowledge in Setup > Knowledge Settings to try it out. If it doesn't work for your org, you can disable it later and revert to Classic Knowledge."

**Why it happens:** LLMs generalize from other Salesforce feature toggles that can be enabled and disabled. Lightning Knowledge is a notable exception with no disable path, but training data may include pre-migration guidance or hallucinated rollback procedures.

**Correct pattern:**

```
Lightning Knowledge cannot be disabled after enablement. Once toggled on:
- Classic Knowledge article types are permanently replaced by record types on Knowledge__kav
- The disable option is removed from Setup
- Existing Classic article data is migrated — there is no undo

Before enabling:
1. Design record types and Data Category Groups in a Developer sandbox
2. Get explicit stakeholder sign-off on the irreversibility
3. Promote the complete configuration to production before enabling
```

**Detection hint:** Look for phrases like "revert," "disable," "roll back," or "undo Lightning Knowledge." Any of these in advice about Knowledge enablement is incorrect.

---

## Anti-Pattern 2: Confusing Data Category Visibility with Object-Level Permissions

**What the LLM generates:** "To restrict Knowledge articles to internal agents only, create a permission set that grants Knowledge__kav read access and assign it only to agent profiles. Remove Knowledge read access from partner and customer profiles."

**Why it happens:** LLMs default to standard Salesforce security patterns (profiles, permission sets, sharing rules) for object access control. Data Category visibility is a Knowledge-specific layer that operates independently, and LLMs frequently omit or conflate it with standard object permissions.

**Correct pattern:**

```
Knowledge article visibility requires TWO independent layers:
1. Object-level access: profile/permission set must grant Knowledge__kav Read
2. Data Category visibility: user's role/profile must have visibility to at least one
   category in every Data Category Group assigned to the article

Granting object read access without category visibility = article invisible to user
Granting category visibility without object read access = article inaccessible

Both layers must be configured for each audience segment.
```

**Detection hint:** Any Knowledge access control advice that mentions only profiles or permission sets without mentioning Data Category Group visibility is incomplete.

---

## Anti-Pattern 3: Assuming "Publish" on a New Version Schedules or Queues the Replacement

**What the LLM generates:** "When you're ready to replace an article, click Publish on the new draft version. Salesforce will queue the update and swap it in when you confirm." or "Publishing a new version does not affect the current published version until you archive it manually."

**Why it happens:** LLMs generalize from CMS systems (WordPress, Contentful) where draft/publish workflows often involve explicit swap or schedule steps. Salesforce Knowledge immediately archives the current published version the moment the new version is published — there is no queue, no delay, and no separate archive action.

**Correct pattern:**

```
Publishing a new Knowledge article version is an immediate, irreversible swap:
1. Author clicks Publish on draft version
2. Current published version transitions to Archived INSTANTLY
3. New version becomes the Published version INSTANTLY

There is no:
- Scheduled publish
- Preview swap
- Grace period
- Automatic rollback

To restore a previous version: find the Archived version, restore it (creates a new
Draft from the archived content), then Publish the restored draft.
```

**Detection hint:** Look for "schedule," "queue," "confirm swap," or "archive manually" in advice about re-publishing Knowledge articles.

---

## Anti-Pattern 4: Recommending More Than 3 Active Data Category Groups

**What the LLM generates:** "Create a separate Data Category Group for each audience: Products, Regions, Departments, Customer Tier, Language, Support Level, and Compliance Area. Assign all groups to Knowledge articles for maximum flexibility."

**Why it happens:** LLMs are familiar with tagging and taxonomy systems that have no hard category group limits. Salesforce's defaults are tighter than most assistants assume, and the number that gets remembered (5) is the *total* group limit, not the *active* one. Only active groups are visible to users, so the active ceiling is the one that constrains a design.

**Correct pattern:**

```
Salesforce default Data Category limits (Knowledge Implementation Guide,
"Data Category Limits" table):
- 5 category groups, with 3 ACTIVE at a time   ← the active ceiling binds first
- 100 categories per category group
- 5 levels in a category group hierarchy
- 8 categories from one group assigned to a single article

Salesforce Support can raise the group and category limits on request.
A category group is hidden from users until it is activated.

Design principles to stay within limits:
- Consolidate related taxonomies into a single hierarchical group
  (e.g., one "Products" group with product lines as subcategories)
- Use Validation Status or article fields for attributes that do not
  require access-control enforcement (e.g., Language, Customer Tier)
- Reserve Data Category Groups for dimensions that require audience-scoped visibility
```

**Detection hint:** Count the distinct Data Category Groups recommended as active. Any count above 3 exceeds the default active limit; any count above 5 exceeds the default total. An answer that cites "5 active groups" has confused the two numbers.

---

## Anti-Pattern 5: Suggesting Apex Triggers as the Primary Publishing Workflow Enforcement Mechanism

**What the LLM generates:** "To enforce approval before publishing, write an Apex trigger on Knowledge__kav that throws an exception if the Status field is set to 'Published' without the Validation Status being 'Approved.'"

**Why it happens:** LLMs default to Apex triggers as a general enforcement mechanism for field-value rules on Salesforce objects. While Apex triggers work on `Knowledge__kav`, Salesforce provides declarative tools (Approval Processes, Validation Rules, Validation Status) that are more maintainable, testable, and aligned with Knowledge's native workflow model.

**Correct pattern:**

```
Preferred enforcement mechanisms for Knowledge publishing workflow (in order):
1. Approval Process on Knowledge__kav — declarative, auditable, supports multi-step review
2. Validation Rules on Knowledge__kav — prevent publish if Validation Status is not set
3. Validation Status picklist — non-blocking quality signal for agent filtering
4. Flow (Record-Triggered) — for custom notifications or field updates on status change

Use Apex triggers on Knowledge__kav only when:
- The logic cannot be expressed declaratively
- Complex cross-object validation is required
- The requirement is confirmed to exceed Flow governor limits

Apex triggers on Knowledge__kav have additional considerations:
- Article versioning creates new records on each publish — triggers fire on insert/update
  of version records, not the parent Knowledge__ka container
- Test coverage must handle Draft, Published, and Archived status transitions
```

**Detection hint:** Look for `trigger on Knowledge__kav` as the first or only recommended approach for publishing enforcement. Propose declarative alternatives before Apex.

---

## Anti-Pattern 6: Claiming a Published Article Automatically Appears on the Experience Cloud Site

**What the LLM generates:** "Publish the article and check 'Visible to Customer.' It will now appear in your customer community's Knowledge tab." Or, more subtly: "Enable Knowledge in Setup, add the Knowledge component in Experience Builder, and published articles will render."

**Why it happens:** LLMs pattern-match Knowledge to a CMS, where publishing is the terminal step. Salesforce splits the concern across four unrelated configuration surfaces — Topics on the Knowledge object, site-level Knowledge enablement, per-article channel flags, and Data Category Visibility — and none of them errors when it is missing, so nothing in the platform's feedback trains the correct sequence.

**Correct pattern:**

```
An article appears on an Experience Cloud site only when ALL of these hold:

1. Topics enabled on the Knowledge object
   Setup > Topics for Objects > Knowledge > Enable Topics (+ Title field)
   Trailhead, "Enable and Configure Lightning Knowledge" (project: Build an
   Experience Cloud Site with Knowledge and Enhanced Chat): "Without enabling
   Salesforce Knowledge topics, articles can't be displayed outside an org."

2. Salesforce Knowledge enabled on the SITE
   (a distinct step from org-level Knowledge enablement)

3. The article's channel flag is set for the READER, not for the template
   IsVisibleInCsp (authenticated customer) / IsVisibleInPrm (authenticated
   partner) / IsVisibleInPkb (unauthenticated guest — including guests on a
   public-access Help Center)

4. The viewer has Data Category Visibility to a category on the article
   (role, permission set, or profile — combined with logical OR; guest and
   high-volume portal users have no role, so use permission set or profile)

5. A Knowledge component is placed on the page in Experience Builder
   (Topic Catalog, Top Articles by Topic, Articles with This Topic, Article Content)

Missing any one of these produces an EMPTY PAGE, not an error.
```

**Detection hint:** Any advice about surfacing Knowledge externally that never mentions Topics is incomplete. If the answer stops at "publish + check the visibility box," it will not work.

---

## Anti-Pattern 7: Conflating Channel Flags with Data Category Visibility

**What the LLM generates:** "Set `IsVisibleInPkb = true` to make the article public" (presented as sufficient), or conversely "Grant the customer community profile Data Category Visibility and articles become visible to customers" (also presented as sufficient). Some outputs go further and recommend a sharing rule to expose Knowledge to guest users.

**Why it happens:** Both mechanisms restrict who sees an article, so LLMs collapse them into a single concept and pick whichever one appears in the nearest training example. Sharing rules get pulled in because guest-user access on every *other* Salesforce object is a sharing problem.

**Correct pattern:**

```
Two orthogonal axes. Both must pass.

CHANNEL (publishing eligibility) — per article version, on Knowledge__kav:
  IsVisibleInApp  → Internal App    [NOT createable/updateable — defaulted on create]
  IsVisibleInCsp  → Customer (authenticated Experience Cloud)   [Create, Update]
  IsVisibleInPrm  → Partner (authenticated Experience Cloud)    [Create, Update]
  IsVisibleInPkb  → Public Knowledge Base (guest / unauthenticated) [Create, Update]

DATA CATEGORY VISIBILITY (read access) — per audience, set to All / None / Custom
  on a role, a permission set, or a profile. Multiple definitions for the same
  user are combined with a logical OR. Guest and high-volume portal users have
  no role, so only permission set or profile reaches them.

Channel set + no category visibility  → article eligible, viewer sees nothing
Category visibility + no channel      → viewer entitled, article not on that surface

Sharing rules do NOT govern Knowledge article visibility. Do not recommend them
for Knowledge audience segmentation.
```

**Detection hint:** Look for guest-user Knowledge advice that mentions sharing rules or `Knowledge__kav` sharing; for any answer that offers exactly one of {channel flag, Data Category Visibility} as the complete solution to an audience-scoping question; or for code and data loads that try to write `IsVisibleInApp`.

---

## Anti-Pattern 8: Asserting That Uncategorized Articles Are Hidden

**What the LLM generates:** "Articles with no Data Category assigned are invisible to everyone except users with View All Data. That is why the article you just published cannot be found — assign it a category."

**Why it happens:** The claim is intuitive (no category → fails the category check) and it circulates widely in community posts. Salesforce documents the opposite, and the true failure mode — activating a category group — is less memorable than the false one.

**Correct pattern:**

```
Uncategorized articles are the ones that SURVIVE a restrictive visibility config.

Knowledge Implementation Guide, "Initial Visibility Settings":
  "if data category visibility is set, users with no data category visibility by
   role, permission set, or profile, only see uncategorized articles and questions
   unless you make the associated categories visible by default"

Knowledge Implementation Guide, "Revoked Visibility":
  visibility revoked (None) for a group → users "can only see articles and
  questions that aren't classified with a category in that category group"

Knowledge Implementation Guide, "Categorized Article Visibility":
  "Users can see an article if they can see at least one category per category
   group on the article"  ← classification is what exposes an article to the check

The real defect of an uncategorized article (Data Category Implementation Tips):
  "If an article has no categories, it displays only when you choose the
   No Filter option in the category drop-down menu."   → unbrowsable, not invisible

The real disappearing-article cause:
  activating a category group + classifying articles into it
  → invisible to every user without visibility to one of its categories

There is no "Manage Categories" permission. The system permission is
"Manage Data Categories".
```

**Detection hint:** Any claim that uncategorized/unclassified Knowledge articles are hidden, or that "View All Data" / "Manage Articles" / "Manage Categories" is what reveals them. Also flag "Manage Categories" as a permission name — it does not exist.
