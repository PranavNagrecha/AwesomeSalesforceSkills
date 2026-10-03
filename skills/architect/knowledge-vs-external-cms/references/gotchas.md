# Gotchas -- Knowledge vs External CMS

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.
Each gotcha names its source. "Knowledge Guide (Classic)" is *Salesforce Knowledge Guide (Classic)*, Spring '26 (`salesforce_knowledge_implementation_guide.pdf`); "Knowledge Developer Guide" is the Summer '26 developer guide. Both are listed in `well-architected.md`. Where a fact comes only from the Classic guide and could differ in Lightning Knowledge, the gotcha says so. Claims no fetched source confirms carry an inline `UNVERIFIED (date):` marker.

## Gotcha 1: CMS Connect Does Not Feed the Agent Console

**What happens:** Teams assume CMS Connect makes external content available throughout Salesforce. The Metadata API Developer Guide (`CMSConnectSource`) defines a CMS Connect source as connection information for external CMSs "that feed content to Experience Builder sites", stored per network and treated in change sets as a dependent of `Network` and `Community`. The *Experience Cloud Developer Guide* (Chapter 7) describes it as a tool for embedding third-party CMS content in a site. Nothing in either guide connects it to the agent console or internal Lightning pages.

**When it occurs:** When architects design a hybrid strategy expecting agents to see CMS content alongside Knowledge articles in the console search results.

**How to avoid:** If agents need external CMS content, build a separate integration (MuleSoft, scheduled Apex, or middleware) that syncs a subset of CMS content into Knowledge records. Treat CMS Connect as a site-only bridge.

---

## Gotcha 2: Knowledge Translation Runs Through Queues and Export Files, With Limits

**What happens:** Teams coming from enterprise CMS platforms expect locale-based publishing and translation memory.

Correction (2026-10-03): earlier text said Knowledge has "no batch send-to-translator workflow". The Knowledge Guide (Classic) ("Export Articles for Translation", "Import Translated Articles") documents one: authors submit articles to per-language translation queues, an admin exports them for a vendor, and translated files are imported back. The same section caps it at 50 exports in 24 hours and 15 pending exports. Translations also cannot carry their own data categories; they inherit the primary article's ("Data Category Limits"). UNVERIFIED (2026-10-03): the absence of translation memory and locale-level scheduling is not stated in the guide either way.

**When it occurs:** When organizations with 10+ supported languages and frequent updates try to manage localization entirely within Knowledge.

**How to avoid:** Size the translation volume against the export limits before choosing Knowledge as the localization system of record. For heavy localization, keep the external CMS as the system of record and sync localized output into Knowledge if agents need it, or use CMS Connect for the portal. Note that `CMSConnectSource` supports language mappings (`cmsConnectLanguage`).

---

## Gotcha 3: Data Category Visibility Is Broader Than It Looks

**What happens:** An admin grants portal users visibility to one category, expecting them to see only that category's articles. Correction (2026-10-03): earlier text said granting a parent category does not cascade to children under Custom visibility. The Knowledge Guide (Classic) ("Visibility Setting Enforcement") says the opposite. Category group visibility "is broadly interpreted": making a category visible makes its whole direct family line visible, meaning its ancestors, immediate parent, children, and other descendants. Its example: with France visible, users see articles classified with Europe, France, and all French cities.

**When it occurs:** When internal-only articles are classified at a parent level (for example a continent or a product family) and a portal role is granted a child category under it.

**How to avoid:** Never classify internal-only content at an ancestor of any category that external users can see. Keep internal content in a separate category group, or control it with the channel settings instead. Test visibility per role, permission set, and profile before go-live.

---

## Gotcha 4: Knowledge Search Relevance Is Separate from Experience Cloud Search

**What happens:** Tuning applied to agent-side search does not carry over to the portal, and vice versa. UNVERIFIED (2026-10-03): the separation of the two search configurations is field experience; the fetched guides do not describe search tuning surfaces.

**When it occurs:** When teams optimize Knowledge search for agents and assume the customer portal will behave identically.

**How to avoid:** Treat agent-side and portal-side search as separate workstreams. Configure promoted search terms and article weights independently for each surface. Test search relevance with real queries in both channels.

---

## Gotcha 5: Knowledge Article File Attachments Count Against Storage

**What happens:** Files attached to Knowledge articles (images, PDFs, embedded documents) consume Salesforce file storage. UNVERIFIED (2026-10-03): the storage accounting for article attachments and embedded images is documented in Salesforce Help, not in the fetched guides.

**When it occurs:** When a content migration brings thousands of articles with embedded images from an external CMS into Knowledge.

**How to avoid:** Audit file storage before migrating rich-media content into Knowledge. Consider hosting images and documents in an external CDN or the CMS DAM and linking to them from Knowledge articles rather than attaching them directly.

---

## Gotcha 6: Data Category Limits Cap the Taxonomy You Can Mirror

**What happens:** The team maps a CMS taxonomy (12 facets, deep product trees) into data categories and runs out of room. The Knowledge Guide (Classic) ("Data Category Limits") allows 5 category groups with 3 active at a time, 100 categories per group (Salesforce Support can raise the defaults), 5 levels per hierarchy, and 8 categories from one group per article.

**When it occurs:** Hybrid designs that promise a "shared taxonomy" across Knowledge and the CMS without checking the Knowledge side's limits.

**How to avoid:** Use data categories only for visibility and the few facets agents filter on. Carry the rest of the CMS taxonomy in custom fields or record types on `Knowledge__kav`. Record which facets live where in the content routing rules.

---

## Gotcha 7: External Users Need the Right License to See Channel Articles

**What happens:** Articles are published to the Customer channel, but some site users cannot see them. The Knowledge Developer Guide ("Audience Channel") says that in a community, Customer-channel articles are available only to users with Customer Community or Customer Community Plus licenses, and Partner-channel articles only to users with Partner Community licenses.

**When it occurs:** Sites that mix license types, or that move users to a different external license for cost reasons.

**How to avoid:** List each external audience with its license type and the channel it should read. Confirm the license-channel pairing before promising self-service content to an audience. Use the Public Knowledge Base channel for anonymous visitors.

---

## Gotcha 8: Case Deflection Metrics Count Only Articles and Discussions, From Authenticated Users

**What happens:** A hybrid portal shows CMS Connect content next to the case form, and the business expects deflection reporting for it. The *Experience Cloud Developer Guide* ("Report on Deflections: The Deflection Signals Framework") records a deflection signal whose destination is an article or discussion ID, fired by the Case Deflection component in an Aura site, and reports only signals from authenticated users (custom report type on Community Case Deflection Metrics).

**When it occurs:** Deflection business cases built on external CMS content or on guest traffic.

**How to avoid:** Keep the content you need deflection metrics for in Knowledge. Measure guest-user and CMS-content deflection some other way (web analytics on the CMS) and label it as a different metric.

---

## Gotcha 9: Knowledge Articles Already Support Scheduled Publishing and Versions

**What happens:** The decision memo rejects Knowledge because "it can't schedule publication". The Knowledge Guide (Classic) says authors can publish directly or schedule publishing for a future date and time, and scheduled articles stay in the Draft Articles filter until then. UNVERIFIED (2026-10-03): this is documented in the Classic guide; confirm the same option in the Lightning Knowledge publish action before relying on it. The Knowledge Developer Guide ("Publishing Cycle", "KnowledgeArticleVersion") describes Draft, Online, and Archived statuses, with each new draft getting its own version number and ID.

Correction (2026-10-03): the SKILL.md gotcha list said Knowledge lacks scheduled publishing compared with CMS platforms. Scheduling exists. What Knowledge lacks, compared with branching CMS platforms, is parallel drafts of one article and variant testing (UNVERIFIED 2026-10-03: the guides describe one draft-to-online cycle per version but do not state the one-draft limit outright).

**When it occurs:** Platform comparisons written from memory of older Knowledge releases.

**How to avoid:** Compare against the current Knowledge capabilities: scheduled publication, per-version history (`KnowledgeArticleVersionHistory`), approval processes, and translation queues. Reserve the "CMS wins" argument for authoring experience, structured multi-channel delivery, DAM, and branching.

---

## Gotcha 10: Some Orgs Use Standard Sharing for Knowledge, Not Data Categories

**What happens:** A visibility design built entirely on data categories does nothing in an org that switched Lightning Knowledge to standard sharing, or a design built on sharing rules fails in an org still on data-category visibility. The Knowledge Guide (Classic), "Work with Data Categories", says standard Salesforce sharing for Lightning Knowledge has been available since Summer '20 and that switching to it changes how data categories and article access work.

**When it occurs:** Architects reuse a visibility design from another org, or an AI assistant states one model as universal.

**How to avoid:** Ask which access model the org's Knowledge uses before designing visibility. Record it in the decision record, and test article access per audience under that model.

