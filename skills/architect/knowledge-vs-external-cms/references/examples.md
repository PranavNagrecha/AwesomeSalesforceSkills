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

**Why it works:** Every consumer is an agent in the console. Knowledge is the only content source that feeds Einstein recommendations and case deflection natively. Adding an external CMS would have created integration overhead with zero user-facing benefit.

---

## Example 2: E-Commerce Retailer -- Hybrid Split with CMS Connect

**Context:** An e-commerce retailer runs a Contentful-based content platform for product guides, how-to videos, and localized help content across 12 languages. They also have 500 service agents using Salesforce Service Cloud. Agents need troubleshooting articles; customers need rich self-service content on an Experience Cloud portal.

**Problem:** The team tried to migrate all Contentful content into Knowledge. The rich-text editor could not handle embedded video players, interactive size guides, or the 12-language translation pipeline. Authors reverted to editing in Contentful and manually copy-pasting into Knowledge, creating stale duplicates.

**Solution:**

Agent-facing troubleshooting articles stay in Knowledge (authored in Salesforce, surfaced via Einstein). Customer-facing product guides and localized help content remain in Contentful. CMS Connect renders Contentful content inside the Experience Cloud self-service portal. A shared tagging taxonomy (`product-line`, `issue-category`) enables coherent search results across both sources.

```text
Agent Console:
  └── Einstein Search → Knowledge articles only

Experience Cloud Portal:
  ├── Knowledge articles (public subset via data categories)
  └── Contentful content (via CMS Connect)
  └── Unified search (Salesforce search indexes both)

Authoring:
  - Agents/internal: Salesforce Knowledge
  - Customer/public: Contentful → CMS Connect → Experience Cloud
```

**Why it works:** Each system handles what it does best. Knowledge powers agent recommendations. Contentful powers rich customer content. CMS Connect eliminates the need for content migration while keeping the portal experience unified.

---

## Anti-Pattern: Syncing Everything Bidirectionally

**What practitioners do:** They build a bidirectional sync between Knowledge and the external CMS, attempting to keep every article identical in both systems. Edits in either system trigger an update in the other.

**What goes wrong:** Conflict resolution becomes a constant operational burden. Knowledge's linear versioning (draft > published > archived) clashes with CMS branching and scheduled publishing. Merge conflicts corrupt article content. The integration team spends more time debugging sync failures than the content team spends authoring.

**Correct approach:** Choose one system of record per content type. If the CMS is the source, push a read-only copy to Knowledge for agent consumption. If Knowledge is the source, expose it via Experience Cloud for customers. Never make both systems writable for the same content.
