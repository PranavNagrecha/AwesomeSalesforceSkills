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

## Anti-Pattern 4: Recommending More Than 5 Active Data Category Groups for Knowledge

**What the LLM generates:** "Create a separate Data Category Group for each audience: Products, Regions, Departments, Customer Tier, Language, Support Level, and Compliance Area. Assign all groups to Knowledge articles for maximum flexibility."

**Why it happens:** LLMs are familiar with tagging and taxonomy systems that have no hard category group limits. Salesforce Knowledge enforces a platform limit of 5 active Data Category Groups for Knowledge, which LLMs frequently ignore or are unaware of.

**Correct pattern:**

```
Salesforce Knowledge platform limits for Data Categories:
- Maximum 5 active Data Category Groups for Knowledge (additional groups can exist
  but only 5 apply to Knowledge at any time)
- Maximum 100 categories per group
- Maximum 5 hierarchy levels per group

Design principles to stay within limits:
- Consolidate related taxonomies into a single hierarchical group
  (e.g., one "Products" group with product lines as subcategories)
- Use Validation Status or article fields for attributes that do not
  require access-control enforcement (e.g., Language, Customer Tier)
- Reserve Data Category Groups for dimensions that require audience-scoped visibility
```

**Detection hint:** Count the number of distinct Data Category Groups recommended. Any count above 5 for Knowledge exceeds platform limits.

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
