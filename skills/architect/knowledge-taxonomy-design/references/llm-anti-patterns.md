# LLM Anti-Patterns — Knowledge Taxonomy Design

Common mistakes AI coding assistants make when generating or advising on Knowledge Taxonomy Design.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending More Than 3 Active Data Category Groups Without Noting the Default Limit

**What the LLM generates:** A taxonomy design that specifies 4 or 5 active Data Category Groups (e.g., Products, Topics, Audience, Region, Language) without mentioning that Salesforce orgs are limited to 3 active groups by default and that exceeding this requires a support case.

**Why it happens:** LLMs trained on Salesforce documentation learn that the *maximum* is 5 groups and the *maximum* hierarchy is 5 levels, but underweight the distinction between the absolute maximum and the default activation limit. The distinction between "exists in the system" and "active and visible to users" is a subtle platform nuance that LLMs conflate.

**Correct pattern:**

```text
Default active limit: 3 Data Category Groups
Absolute maximum: 5 (requires Salesforce support case to enable beyond 3 active)

Design guidance:
- Start with ≤3 active groups
- If 4–5 are genuinely required, open a support case BEFORE finalising the design
- Document the limit clearly in the architecture decision record
```

**Detection hint:** Any recommendation listing 4+ Data Category Groups as "active" without a note about the default limit or a support case requirement is likely wrong.

---

## Anti-Pattern 2: Treating Validation Status as Per-Article-Type Configurable

**What the LLM generates:** Advice like "configure Validation Status separately for each article type" or "enable Validation Status only for your How-To articles, not for your Known Issue articles." Instructions that suggest per-article-type picklist customisation for Validation Status.

**Why it happens:** LLMs generalise from Salesforce's per-object picklist customisation model. Most Salesforce picklists can be scoped to record types or object types. LLMs apply this general rule to Validation Status without accounting for the fact that Validation Status is a single org-wide binary setting, not a per-article-type configuration.

**Correct pattern:**

```text
Validation Status is org-wide:
- Enable/disable applies to ALL Knowledge article types simultaneously
- Picklist values are shared across all article types
- Cannot scope to a specific article type or record type

Design implication:
- Design the picklist values to work across all article types in the org
- If different article types need different quality workflows, use a custom field
  (e.g., Expert__c picklist) per article type, not Validation Status customisation
```

**Detection hint:** Any suggestion to "configure Validation Status for a specific article type" or "enable it only for X article type" is incorrect.

---

## Anti-Pattern 3: Advising Deep Hierarchies for Better Organisation

**What the LLM generates:** Category hierarchy designs with 4–5 levels, reasoning that deeper classification improves findability and organisation, often using analogies to file system folder structures or library classification systems.

**Why it happens:** LLMs trained on general information architecture and taxonomy design content associate depth with precision. File system and library analogies dominate training data and reinforce the "more specific = better" mental model. Salesforce-specific search behaviour — where SOSL relevance scoring is affected by category depth — is underrepresented in training data relative to generic IA guidance.

**Correct pattern:**

```text
Target: 2–3 hierarchy levels per group for most orgs

Apply Level 3 only when:
- Parent category has >200 articles
- Sub-classification reduces agent search time measurably
- A dedicated Knowledge admin can maintain re-categorisation over time

Avoid Level 4–5:
- Increases authorship burden (agents must navigate deep trees)
- Weakens SOSL category-match relevance scoring
- Creates brittle structure — product line changes require deep restructuring
```

**Detection hint:** Any taxonomy design proposing 4+ levels without a specific corpus-size justification is likely over-engineered.

---

## Anti-Pattern 4: Suggesting SOQL to Query Search Activity Gaps Data

**What the LLM generates:** SOQL queries attempting to read Search Activity Gaps data, such as `SELECT SearchTerm, ClickCount FROM KnowledgeSearchActivity` or references to a `SearchActivityGap` object, implying the data is accessible via standard API queries.

**Why it happens:** LLMs generalise from Salesforce's pattern of exposing analytics data through standard objects (e.g., `LoginHistory`, `ContentDocumentView`). They assume Search Activity Gaps follows the same pattern. The actual dashboard is a UI-only report with no corresponding queryable standard object, which is an exception to the general platform pattern.

**Correct pattern:**

```text
Search Activity Gaps is a UI-only dashboard:
- Location: Knowledge tab → Search Activity Gaps
- Retention: 90-day rolling window
- Export: manual CSV download from the dashboard UI only
- API access: none (no REST endpoint, no SOQL object, no Connect API resource)

For programmatic trend tracking:
- Scheduled manual export to a shared spreadsheet or BI tool
- Build custom instrumentation: log article creation events (Knowledge article trigger)
  alongside manual gap exports to correlate gap closure with article creation activity
```

**Detection hint:** Any SOQL query targeting a "KnowledgeSearchActivity", "SearchActivityGap", or similar object should be flagged as a hallucinated API.

---

## Anti-Pattern 5: Conflating Article Publication Status with Data Category Visibility

**What the LLM generates:** Guidance that setting an article to Published status makes it visible to all agents and portal users, or that visibility is controlled solely by Publication Status and article type sharing settings. Failure to mention Data Category visibility rules as a separate, independent access control layer.

**Why it happens:** LLMs learn that Published = visible from general Salesforce Knowledge documentation. The interplay between Publication Status, Data Category Group Assignments, and profile-level Data Category Visibility is a three-layer access control model that requires explicit documentation to understand. LLMs trained on incomplete documentation snippets collapse these layers into a simpler "published = visible" mental model.

**Correct pattern:**

```text
Knowledge article visibility requires ALL of the following to be true:
1. Article Publication Status = Published (or Archived for legacy access)
2. User's profile has Data Category Visibility configured for the article's category
3. Article is assigned to a Data Category that the user's profile can see
4. Article type sharing settings allow the user's profile to read that article type

Testing protocol:
- Always test article visibility as a non-System Administrator test user
- Test with a user on each affected profile after any Data Category Group changes
- Do not rely on System Administrator visibility as a proxy for agent/portal visibility
```

**Detection hint:** Any visibility troubleshooting advice that does not mention Data Category visibility as a distinct access control layer is incomplete.

---

## Anti-Pattern 6: Assuming KCS Solve Loop Requires No Permission Changes

**What the LLM generates:** KCS Solve Loop implementation guidance that has agents creating and publishing articles during case work but fails to address the Salesforce permission model — specifically that the "Manage Articles" permission (required to create, edit, and publish Knowledge articles) is typically restricted to Knowledge authors, not the full agent population.

**Why it happens:** LLMs describe the KCS workflow process accurately but miss the operational detail that the default Salesforce Knowledge permission model restricts publication rights. The mismatch between the KCS ideal (all agents author) and the Salesforce default (only Knowledge authors publish) is a real-world implementation blocker that is underrepresented in process documentation versus the KCS methodology documentation.

**Correct pattern:**

```text
KCS Solve Loop permission requirements:
- Agents need "Manage Articles" permission to create, edit, and publish articles
- By default, this permission is NOT included in standard agent profiles
- Grant "Manage Articles" to agent profiles or via permission set before Solve Loop launch

Also required:
- "Create" and "Edit" on Knowledge object (standard FLS)
- Data Category visibility for the categories agents will assign to new articles
- Consider whether agents should publish directly or submit for review:
  - Direct publish: grant full "Manage Articles" (Solve Loop — publish immediately)
  - Submit for review: use an Approval Process or Flow instead of direct publish permission
```

**Detection hint:** KCS Solve Loop guidance that does not mention permission model changes or profile updates is incomplete and will fail at implementation time.
