# Examples -- Knowledge vs External CMS

## Example 1: Financial Services Firm -- Knowledge-Only for Agent Support

**Context:** A financial services company with 200 service agents handles regulatory inquiries. All content is internal procedure documentation and compliance FAQs. There is no public-facing self-service portal. Content volume is roughly 2,000 articles with no localization needs.

**Problem:** The team initially planned to purchase a headless CMS for "future flexibility." This would have introduced a second authoring system, an integration layer, and ongoing sync logic -- all for content that only agents consume through the Salesforce console.

**Solution:**

All content stays in Salesforce Knowledge. Data categories separate compliance articles from general support procedures. Einstein article recommendations surface relevant articles when agents open cases. The approval workflow routes compliance-sensitive articles through legal review before publication.

```text
Data Categories:
  Compliance
    ├── Regulatory-FAQ
    ├── Internal-Procedures
    └── Audit-Responses
  General-Support
    ├── Account-Inquiries
    └── Transaction-Issues

Article Types:
  - FAQ__kav (customer-safe subset, exposed to internal portal)
  - Procedure__kav (internal-only, agent console visibility)
```

> Note (2026-10-03): `FAQ__kav` and `Procedure__kav` are Salesforce Classic article types. In Lightning Knowledge the Knowledge Developer Guide uses one object, `Knowledge__kav`, with record types (for example FAQ and Procedure) for article structure. Also, data category visibility is broadly interpreted (a visible category exposes its ancestors and descendants), so keep internal-only procedures out of any branch that a portal role can see.

**Why it works:** Every consumer is an agent in the console. Knowledge is the only content source that feeds Einstein recommendations and case deflection natively. Adding an external CMS would have created integration overhead with zero user-facing benefit.

---

## Example 2: E-Commerce Retailer -- Hybrid Split with CMS Connect

**Context:** An e-commerce retailer runs a Contentful-based content platform for product guides, how-to videos, and localized help content across 12 languages. They also have 500 service agents using Salesforce Service Cloud. Agents need troubleshooting articles; customers need rich self-service content on an Experience Cloud portal.

**Problem:** The team tried to migrate all Contentful content into Knowledge. The rich-text editor could not handle embedded video players, interactive size guides, or the 12-language translation pipeline. Authors reverted to editing in Contentful and manually copy-pasting into Knowledge, creating stale duplicates.

**Solution:**

Agent-facing troubleshooting articles stay in Knowledge (authored in Salesforce, surfaced via Einstein). Customer-facing product guides and localized help content remain in Contentful. CMS Connect renders Contentful content inside the Experience Cloud self-service portal (Contentful is not one of the named `CMSConnectSource` types, so it connects as type `Other`). A shared tagging taxonomy (`product-line`, `issue-category`) enables coherent search results across both sources.

```text
Agent Console:
  └── Einstein Search → Knowledge articles only

Experience Cloud Portal:
  ├── Knowledge articles (public subset via data categories)
  └── Contentful content (via CMS Connect)
  └── Unified search (Salesforce search indexes both; UNVERIFIED 2026-10-03, site search coverage of CMS Connect content not confirmed)

Authoring:
  - Agents/internal: Salesforce Knowledge
  - Customer/public: Contentful → CMS Connect → Experience Cloud
```

**Why it works:** Each system handles what it does best. Knowledge powers agent recommendations. Contentful powers rich customer content. CMS Connect eliminates the need for content migration while keeping the portal experience unified.

---

## Anti-Pattern: Syncing Everything Bidirectionally

**What practitioners do:** They build a bidirectional sync between Knowledge and the external CMS, attempting to keep every article identical in both systems. Edits in either system trigger an update in the other.

**What goes wrong:** Conflict resolution becomes a constant operational burden. Knowledge's linear versioning (draft > published > archived) clashes with CMS branching. (Knowledge does support scheduled publication, so scheduling is not the conflict.) Merge conflicts corrupt article content. The integration team spends more time debugging sync failures than the content team spends authoring.

**Correct approach:** Choose one system of record per content type. If the CMS is the source, push a read-only copy to Knowledge for agent consumption. If Knowledge is the source, expose it via Experience Cloud for customers. Never make both systems writable for the same content.

---

## Example 3: Decision Record for Telecom Support Content Across Three Audiences

**Context:** A telecom operator (Service Cloud Enterprise Edition) has 900 agents, an authenticated customer portal on Experience Cloud (Customer Community Plus licenses), a partner portal for resellers (Partner Community licenses), and a public marketing site on Adobe Experience Manager (AEM). Support content exists in 14 languages; about 600 articles change each month. Leadership wants deflection reporting and agent article recommendations.

**Decision record (machine-readable form):**

```yaml
adr: CNT-002
title: Knowledge for service content, AEM for public product content, CMS Connect for the customer portal
status: accepted
date: 2026-10-03
licences:
  knowledge: additional cost in Enterprise Edition (included with Service Cloud in Unlimited and Essentials)
  customer_portal: Customer Community Plus -> can read Customer-channel articles
  partner_portal: Partner Community -> can read Partner-channel articles
content_routing:
  - type: troubleshooting and how-to fixes
    system_of_record: Salesforce Knowledge (Knowledge__kav, record types Troubleshooting and How_To)
    surfaces: [agent console, customer portal, partner portal]
    reason: case deflection signals record only article or discussion IDs from authenticated users
  - type: internal procedures and scripts
    system_of_record: Salesforce Knowledge, Internal App channel only
    surfaces: [agent console]
  - type: product pages, plan comparisons, launch content
    system_of_record: AEM
    surfaces: [public site, customer portal via CMS Connect]
    reason: rich media, marketing workflow, AEM personalization (CMSConnectSource personalization is AEM-only)
data_categories:   # limits: 5 groups (3 active), 100 categories/group, 5 levels, 8 per group per article
  active_groups:
    - Products   (2 levels, 38 categories)
    - Audience   (Internal / Customer / Reseller)   # separate group keeps internal content off portal branches
    - Region     (3 levels, 61 categories)
  not_in_categories: [device model, firmware version, plan code]   # custom fields on Knowledge__kav
translation:
  monthly_changed_articles: 600
  languages: 14
  path: Knowledge translation queues per language -> Export Articles for Translation -> vendor -> Import Translated Articles
  limit_check: 50 exports per 24 hours, 15 pending; batching by language keeps this to ~14 exports per weekly cycle
cms_connect:
  source: CMSConnectSource type AEM, connectionType Authenticated (named credential AEM_Delivery)
  per_site: customer portal only (CMS Connect feeds Experience Builder sites, not the console)
consequences:
  - agents never see AEM product pages in the console; a link field on Knowledge__kav points to the public URL
  - deflection reports cover Knowledge articles for logged-in customers only; guest and AEM traffic measured in web analytics
  - a reviewer checks each new category placement against the Audience group before publish
```

**Why it works:** content lands where the platform features that matter for it exist (deflection and recommendations in Knowledge, rich media and personalization in AEM). The taxonomy fits the data category limits by moving technical facets to fields. Visibility leaks are prevented structurally, because internal content sits in its own category group. The translation path is sized against the documented export limits instead of being discovered in production.

