# LLM Anti-Patterns -- Knowledge vs External CMS

Common mistakes AI coding assistants make when generating or advising on content platform decisions for Salesforce.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Knowledge Migration Without Checking Einstein Dependencies

**What the LLM generates:** "Migrate all content to the external CMS and retire Salesforce Knowledge to simplify the architecture."

**Why it happens:** LLMs optimize for architectural simplicity and assume a single system of record is always better. They do not check whether Einstein article recommendations, case deflection, or suggested articles on cases are active requirements.

**Correct pattern:**

```
Before recommending Knowledge retirement, verify:
1. Is Einstein article recommendation enabled on case pages?
2. Is case deflection configured in Experience Cloud?
3. Are agents trained to use Knowledge sidebar search in the console?
If any answer is yes, Knowledge must remain for those article types.
```

**Detection hint:** Look for "migrate all" or "retire Knowledge" without a preceding check for Einstein or case deflection usage.

---

## Anti-Pattern 2: Claiming CMS Connect Works in the Agent Console

**What the LLM generates:** "Use CMS Connect to surface external CMS content in both the Experience Cloud portal and the agent console for a unified experience."

**Why it happens:** LLMs generalize CMS Connect as a universal Salesforce-CMS bridge. Training data rarely emphasizes that CMS Connect is limited to Experience Cloud sites only.

**Correct pattern:**

```
CMS Connect renders external content in Experience Cloud sites only.
To surface external CMS content in the agent console, build a
separate integration (API callout, middleware sync, or MuleSoft flow)
that creates or updates Knowledge article records from CMS data.
```

**Detection hint:** Any mention of CMS Connect alongside "agent console," "Lightning app," or "service console" is incorrect.

---

## Anti-Pattern 3: Treating Knowledge and CMS Content as Interchangeable in Search

**What the LLM generates:** "Salesforce search will automatically index and rank content from both Knowledge and CMS Connect in a unified results list."

**Why it happens:** LLMs assume search unification is automatic. They conflate the fact that Experience Cloud search can surface both sources with the idea that relevance, ranking, and faceting work identically across them.

**Correct pattern:**

```
Experience Cloud search can return results from both Knowledge and
CMS Connect, but:
- Relevance algorithms differ between Knowledge and external content
- Promoted search terms only apply to Knowledge articles
- Faceted navigation must be configured separately for each source
- Agent-side Einstein Search only indexes Knowledge
Plan search tuning as a separate workstream for each channel.
```

**Detection hint:** Phrases like "unified search," "automatic indexing," or "seamless results" without caveats about per-source tuning.

---

## Anti-Pattern 4: Suggesting Bidirectional Sync as the Default Architecture

**What the LLM generates:** "Set up a bidirectional sync between Salesforce Knowledge and the CMS so edits in either system are reflected in both."

**Why it happens:** LLMs default to "keep everything in sync" as the safest-sounding recommendation. They underestimate the operational cost of conflict resolution between two systems with different versioning models.

**Correct pattern:**

```
Designate one system of record per content type:
- Agent-facing content: authored in Knowledge, consumed in console
- Customer-facing content: authored in CMS, consumed via portal
If agents need CMS content, push a READ-ONLY copy to Knowledge.
Never allow both systems to be writable for the same article.
```

**Detection hint:** "bidirectional sync," "two-way replication," or "edit in either system" for the same content type.

---

## Anti-Pattern 5: Ignoring Knowledge Data Categories in Visibility Design

**What the LLM generates:** "Use Salesforce profiles and permission sets to control which Knowledge articles are visible to different user groups."

**Why it happens:** LLMs default to the standard Salesforce access control model (profiles, permission sets, sharing rules) and do not account for Knowledge's unique data-category-based visibility system, which is the primary mechanism for controlling article access by audience.

**Correct pattern:**

```
Knowledge article visibility is controlled by data category visibility
settings on profiles and permission sets -- NOT by standard object
sharing rules or record-level access. Configure:
1. Data category groups mapped to content segments
2. Category visibility per profile (All, Custom, or None)
3. Role-based visibility for portal users via category group assignments
Standard sharing rules do not apply to Knowledge articles.
```

**Detection hint:** Recommendations mentioning "sharing rules," "org-wide defaults," or "record-level security" for Knowledge article access.

---

## Anti-Pattern 6: Overstating Knowledge Rich-Media Capabilities

**What the LLM generates:** "Salesforce Knowledge supports rich content including embedded videos, interactive widgets, and complex layouts comparable to modern CMS platforms."

**Why it happens:** LLMs see that Knowledge has a "rich text" field type and extrapolate that it supports the same content richness as dedicated CMS platforms. In reality, the Knowledge rich-text editor is limited compared to modern headless CMS structured content models.

**Correct pattern:**

```
Knowledge rich-text fields support basic HTML, inline images, and
simple formatting. They do NOT natively support:
- Embedded interactive components or widgets
- Structured content blocks (hero sections, accordions, tabs)
- Component-based layouts comparable to Contentful or AEM
- Native video hosting (videos require external embed URLs)
For content requiring rich media or structured layouts, use an
external CMS and deliver via CMS Connect or headless API.
```

**Detection hint:** Claims that Knowledge handles "rich media," "interactive content," or "complex layouts" without caveats about the editor's limitations.
