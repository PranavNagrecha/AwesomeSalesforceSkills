---
name: knowledge-vs-external-cms
description: "Use when deciding between Salesforce Knowledge, an external CMS (Contentful, WordPress, AEM), or a hybrid content strategy. Triggers: 'should we use Salesforce Knowledge or a CMS', 'content federation across Salesforce and headless CMS', 'CMS Connect for Experience Cloud', 'agent-facing vs customer-facing content architecture'. NOT for CMS platform implementation, WordPress theme development, or AEM component authoring."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - User Experience
  - Operational Excellence
triggers:
  - "should we use Salesforce Knowledge or an external CMS for our support content"
  - "how do I federate content between Salesforce and a headless CMS like Contentful"
  - "what is the best content architecture for agent-facing and customer-facing articles"
  - "when does CMS Connect make sense vs building a custom integration"
tags:
  - knowledge-vs-external-cms
  - salesforce-knowledge
  - cms-connect
  - content-federation
  - headless-cms
  - experience-cloud
inputs:
  - "whether content is primarily agent-facing, customer-facing, or both"
  - "existing CMS investments and authoring team capabilities"
  - "Experience Cloud usage and self-service portal requirements"
  - "content volume, localization needs, and rich-media complexity"
outputs:
  - "content platform decision matrix with recommended architecture"
  - "hybrid content topology showing which content lives where and how it is federated"
  - "search strategy recommendation covering both agent console and public-facing channels"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Knowledge vs External CMS

Use this skill when an organization must decide where content lives: Salesforce Knowledge, an external CMS, or both. The highest-value move is usually to split content by consumer -- agent-facing articles stay in Knowledge for native case deflection and console integration, while customer-facing rich content lives in a purpose-built CMS -- and then federate where the audiences overlap.

---

## Before Starting

Gather this context before working on anything in this domain:

- Who consumes the content? Service agents via the console, customers via a portal, marketing audiences via a public site, or a mix?
- Does the organization already own a CMS with established authoring workflows, localization pipelines, or headless delivery APIs?
- Is Einstein article recommendation or case-deflection a requirement? These features depend on Knowledge being the content source.

---

## Core Concepts

The decision between Knowledge and an external CMS is not a feature comparison. It is a question of where each content type delivers the most value given the platform capabilities and the audience consuming it.

### Salesforce Knowledge Strengths

Salesforce Knowledge is a native object tightly coupled to the Service Cloud agent experience. Articles surface inside the console via Einstein Search and article recommendations. Data categories control visibility by audience segment. Knowledge supports approval workflows and article versioning (draft, published, archived lifecycle). Case deflection works out of the box in Experience Cloud when Knowledge is the source. The limitation is authoring: the rich-text editor is basic compared to modern CMS platforms, rich media support is constrained, and localization workflows are minimal beyond basic multi-language article translation.

### External CMS Strengths

Platforms like Contentful, WordPress, and AEM offer structured content modeling, sophisticated authoring experiences, advanced localization with translation management, headless API delivery for omnichannel publishing, and mature rich-media pipelines (video, interactive components, DAM integration). They are purpose-built for content teams who publish at volume across web, mobile, and other channels. The tradeoff is that external CMS content does not natively participate in Salesforce case deflection, agent recommendations, or data-category-based visibility.

### CMS Connect and Content Federation

CMS Connect is the Salesforce-provided bridge that brings external CMS content into Experience Cloud sites. It supports connections to headless CMS APIs, allowing external articles to render inside Salesforce-hosted portals without migrating content. This enables a hybrid model where the CMS is the system of record for customer-facing content, but that content still appears in the Salesforce portal. CMS Connect does not feed content into the agent console or Einstein recommendations -- that path still requires Knowledge.

### Search Strategy Across Boundaries

When content spans two systems, search becomes the integration challenge. Agent-side search uses Einstein Search over Knowledge. Customer-side search in Experience Cloud can combine Knowledge articles with CMS Connect content, but relevance tuning and faceted navigation require deliberate configuration. Organizations that skip search planning end up with fragmented results where customers see partial content from each source.

---

## Common Patterns

### Pattern 1: Knowledge-Only for Agent-Centric Orgs

**When to use:** The primary content consumers are service agents. Customer self-service is minimal or not yet launched. Content volume is under 5,000 articles with limited rich-media needs.

**How it works:** All content lives in Salesforce Knowledge. Data categories segment visibility (internal-only vs. public). Einstein article recommendations surface relevant articles during case work. Experience Cloud exposes public articles for basic self-service.

**Why not the alternative:** Adding an external CMS for agent-facing content creates a sync problem with no benefit. Agents need articles in the console, and Knowledge is the only source that feeds Einstein recommendations natively.

### Pattern 2: Hybrid Split by Audience

**When to use:** The organization serves both agents and customers, but customer-facing content requires richer authoring, localization, or multimedia than Knowledge supports. A CMS is already in place or justified by content volume.

**How it works:** Agent-facing troubleshooting articles and internal procedures stay in Knowledge. Customer-facing help center content, product documentation, and marketing-adjacent guides live in the external CMS. CMS Connect renders CMS content inside the Experience Cloud portal. A shared taxonomy or tagging scheme bridges the two systems so search results are coherent.

**Why not the alternative:** Migrating all content to the CMS loses case deflection and Einstein recommendations. Migrating all content to Knowledge forces content teams into a basic editor and drops localization maturity.

### Pattern 3: CMS as Source of Truth with Knowledge Sync

**When to use:** A mature CMS is the organization's canonical content platform and the team refuses to author in two places, but agents still need articles in the console.

**How it works:** Content is authored and managed in the external CMS. A scheduled integration (MuleSoft, middleware, or custom Apex) pushes a subset of articles into Knowledge as read-only records so that agents and Einstein can consume them. The CMS remains the authoring system; Knowledge is a distribution endpoint.

**Why not the alternative:** This adds integration complexity and latency. It only makes sense when the CMS authoring investment is too large to duplicate and agent-side consumption is a hard requirement.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Agents are the primary audience; self-service is basic | Knowledge-only | Native console integration, Einstein recommendations, case deflection with no integration overhead |
| Customer portal needs rich content; CMS already exists | Hybrid split with CMS Connect | Each system handles its strength; CMS Connect bridges content into Experience Cloud |
| Content team refuses dual authoring; agents still need articles | CMS as source with Knowledge sync | Preserves single authoring workflow while enabling agent-side features via integration |
| Localization across 10+ languages with regional variants | External CMS for localized content | Knowledge translation is basic; CMS platforms offer robust translation management |
| Einstein article recommendations are a hard requirement | Knowledge must be the source for those articles | Einstein Search and recommendations only index Knowledge articles |
| Public SEO-driven content with structured metadata | External CMS with headless delivery | CMS platforms offer better SEO tooling, structured data, and CDN delivery |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Inventory content consumers** -- List every audience (agents, customers, partners, public visitors) and the channels they use (console, portal, public site, mobile app). Map each audience to their primary content needs.
2. **Assess existing CMS investment** -- Determine whether the organization already operates a CMS, what content lives there, how mature the authoring and localization workflows are, and whether there is organizational willingness to adopt a second authoring tool.
3. **Map feature requirements to platforms** -- For each content type, check whether it requires Einstein article recommendations, case deflection, data-category visibility, rich media, localization, or headless delivery. Use the decision table above to assign each content type to Knowledge or the external CMS.
4. **Design the federation layer** -- If hybrid, define how content crosses system boundaries. Decide whether CMS Connect, a middleware integration, or both are needed. Specify the shared taxonomy or tagging convention that enables coherent cross-system search.
5. **Plan the search strategy** -- Define how agent-side search (Einstein Search) and customer-side search (Experience Cloud search, external search) will index and rank content from both sources. Test that results do not fragment across systems.
6. **Validate with a content pilot** -- Stand up a small set of articles in the chosen architecture. Verify that agents see recommendations, customers find content in self-service, and the authoring team can publish without friction.
7. **Document the content routing rules** -- Record which content types go where, who owns each system, and the escalation path when content does not fit cleanly into either platform.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every content type is explicitly assigned to Knowledge, the external CMS, or both with a clear rationale
- [ ] Einstein article recommendation and case deflection requirements are mapped to Knowledge as the source
- [ ] CMS Connect configuration is validated if external content must appear in Experience Cloud
- [ ] Search strategy covers both agent-side and customer-side channels without fragmented results
- [ ] Localization requirements are satisfied by the chosen platform (Knowledge translation vs. CMS translation management)
- [ ] Content authoring team has confirmed the workflow is acceptable -- no shadow authoring in unapproved tools
- [ ] Data category or taxonomy alignment between systems is documented

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Einstein recommendations only index Knowledge** -- If articles live in an external CMS and are not synced into Knowledge, Einstein article recommendations and suggested articles on cases will not surface them. There is no workaround short of syncing content into Knowledge records.
2. **CMS Connect content is read-only in Experience Cloud** -- CMS Connect renders external content but does not support inline editing, commenting, or case attachment from within Salesforce. Users cannot interact with CMS Connect content the way they interact with Knowledge articles.
3. **Knowledge article versioning is linear, not branching** -- Unlike modern CMS platforms that support content branches, scheduled publishing, and variant testing, Knowledge articles follow a single draft-to-published-to-archived lifecycle. Teams accustomed to CMS branching workflows will find this restrictive.
4. **Data categories have a depth limit of 5 levels** -- Organizations that map complex content taxonomies into Knowledge data categories hit the 5-level nesting limit. Deep hierarchies must be flattened or supplemented with custom fields.
5. **CMS Connect requires Experience Cloud** -- CMS Connect is only available in Experience Cloud sites. It cannot bring external CMS content into the agent console, internal Lightning pages, or other Salesforce surfaces.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Content platform decision matrix | Table mapping each content type to its target platform with rationale and feature requirements |
| Hybrid content topology diagram | Architecture diagram showing content flow between CMS, Knowledge, Experience Cloud, and agent console |
| Search strategy document | Specification for how search indexes, ranks, and presents content from both sources |
| Content routing rules | Operational guide defining which content goes where and who owns each system |

---

## Related Skills

- service-cloud-architecture -- Use when the broader service architecture (not just content) needs design, including routing, entitlements, and agent workspace layout
- multi-channel-service-architecture -- Use when the content decision is part of a larger omnichannel service strategy spanning chat, voice, email, and self-service

---

## Official Sources Used

- Salesforce Knowledge Overview -- https://help.salesforce.com/s/articleView?id=sf.knowledge_whatis.htm
- CMS Connect for Experience Cloud -- https://help.salesforce.com/s/articleView?id=sf.cms_connect.htm
