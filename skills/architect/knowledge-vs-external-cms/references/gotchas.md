# Gotchas -- Knowledge vs External CMS

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: CMS Connect Does Not Feed the Agent Console

**What happens:** Teams assume CMS Connect makes external content available throughout Salesforce. In reality, CMS Connect only renders external CMS content inside Experience Cloud sites. Agent console, internal Lightning app pages, and other Salesforce surfaces cannot consume CMS Connect content.

**When it occurs:** When architects design a hybrid strategy expecting agents to see CMS content alongside Knowledge articles in the console search results.

**How to avoid:** If agents need external CMS content, build a separate integration (MuleSoft, scheduled Apex, or middleware) that syncs a subset of CMS content into Knowledge records. CMS Connect is a portal-only bridge.

---

## Gotcha 2: Knowledge Translation Is Per-Article, Not Per-Locale Pipeline

**What happens:** Teams coming from enterprise CMS platforms expect a centralized translation management workflow with locale-based publishing, translation memory, and reviewer assignment per language. Knowledge translation works at the individual article level -- you create a translated version of each article manually or via API. There is no built-in translation memory, no batch send-to-translator workflow, and no locale-level scheduling.

**When it occurs:** When organizations with 10+ supported languages try to manage localization entirely within Knowledge and discover the per-article workflow does not scale.

**How to avoid:** For heavy localization needs (10+ languages, frequent content updates), keep the external CMS as the localization system of record. Sync the localized output into Knowledge if agent-side consumption is required, or use CMS Connect for the customer portal.

---

## Gotcha 3: Data Category Visibility Overrides Do Not Cascade as Expected

**What happens:** Data category visibility settings control which articles appear to which user groups. However, the visibility inheritance behavior between parent and child categories is not always intuitive. Granting access to a parent category does not automatically grant access to all descendants when using "Custom" visibility -- you must explicitly configure each level.

**When it occurs:** When administrators set up a deep category hierarchy and assume child-category articles will be visible to users who have access to the parent.

**How to avoid:** Test data category visibility for every user profile and permission set combination before go-live. Use the "All Categories" visibility setting only for internal agents, and configure explicit category mappings for portal users.

---

## Gotcha 4: Knowledge Search Relevance Is Separate from Experience Cloud Search

**What happens:** The search algorithm and relevance tuning in the agent console (Einstein Search for Knowledge) is a different system from the search in Experience Cloud portals. Tuning that improves agent-side results does not carry over to the portal, and vice versa.

**When it occurs:** When teams optimize Knowledge search for agents and assume the customer portal will behave identically.

**How to avoid:** Treat agent-side and portal-side search as separate workstreams. Configure promoted search terms and article weights independently for each surface. Test search relevance with real queries in both channels.

---

## Gotcha 5: Knowledge Article File Attachments Count Against Storage

**What happens:** Files attached to Knowledge articles (images, PDFs, embedded documents) consume Salesforce file storage. Organizations that embed many images or attach PDFs to articles can hit file storage limits unexpectedly, especially in orgs that are already storage-constrained.

**When it occurs:** When a content migration brings thousands of articles with embedded images from an external CMS into Knowledge.

**How to avoid:** Audit file storage before migrating rich-media content into Knowledge. Consider hosting images and documents in an external CDN or the CMS DAM and linking to them from Knowledge articles rather than attaching them directly.
