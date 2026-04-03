# Official Salesforce Sources

This file defines the official Salesforce documentation set that skill authors must check before writing or materially revising a skill.

Use this file as the first stop for source selection. It is intentionally curated rather than exhaustive.

---

## Policy

- Official Salesforce documentation is the primary authority for platform behavior, limits, API usage, metadata semantics, and security guidance.
- Salesforce Architects content is the primary authority for architecture patterns, anti-patterns, and Well-Architected best practices.
- Local RAG material, project notes, and practitioner experience can refine the guidance, but they should not override official behavior claims unless the skill explicitly documents a gap or platform nuance.
- Do not bulk-copy official docs into skills. Validate the claim, then rewrite it in the repo's practitioner voice.
- When a skill makes a specific claim about API behavior, metadata behavior, security enforcement, or component/platform semantics, prefer an official source if one exists.

---

## Local Documentation (Search First — Always)

The following official Salesforce guides have been downloaded and stored as markdown in `knowledge/imports/`. **Always search these before hitting the web.** They are Tier 1 sources and are not blocked by any proxy.

```bash
python3 scripts/search_knowledge.py "<topic>"
```

| File | Covers |
|------|--------|
| `knowledge/imports/salesforce-apex-developer-guide.md` | Apex behavior, testing, transactions, async patterns, limits |
| `knowledge/imports/salesforce-bulk-api-guide.md` | Bulk API 2.0 and legacy Bulk API, ingest/query, job states, limits |
| `knowledge/imports/salesforce-change-data-capture.md` | CDC change events, Pub/Sub API, Apex trigger subscriptions |
| `knowledge/imports/salesforce-channel-revenue-management.md` | Channel Revenue Management, Rebate, Price Protection |
| `knowledge/imports/salesforce-metadata-api-guide.md` | Retrieve/deploy, CRUD-based API, REST deploy, result objects |
| `knowledge/imports/salesforce-analytics-rest-api.md` | CRM Analytics REST API, SAQL, dataflow scheduling |
| `knowledge/imports/salesforce-automotive-cloud.md` | Automotive Cloud standard objects |
| `knowledge/imports/salesforce-big-objects-guide.md` | Big Objects design, async SOQL, archival patterns |
| `knowledge/imports/salesforce-large-data-volumes-best-practices.md` | LDV design, indexing, query optimization, archival |
| `knowledge/imports/salesforce-soql-sosl-guide.md` | SOQL/SOSL syntax, bulk queries, limits |

If `search_knowledge.py` returns `has_coverage: true` on a topic — read that chunk before checking the web.

---

## How To Use This File

1. **Search local imports first** — `python3 scripts/search_knowledge.py "<topic>"`
2. Identify the skill domain and feature area.
3. Pick the smallest relevant official source set from the sections below.
4. Use product/reference docs for factual behavior and limits.
5. Use Architects / Well-Architected docs for best-practice and pattern guidance.
6. Record the official docs actually used in the skill's `references/well-architected.md` under `## Official Sources Used`.

Minimum expectation for a new or materially revised skill:
- 1 official Salesforce product/reference source
- 1 official Salesforce Architects / best-practice source when the topic is architecture- or pattern-driven

---

## Core Platform References

Use these when a skill needs baseline Salesforce platform facts.

- Object Reference
  Use for: sObject behavior, standard objects, field/object semantics, relationship model
  URL: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm

- REST API Developer Guide
  Use for: REST resources, request/response behavior, API capabilities, integration semantics
  URL: https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm

- Metadata API Developer Guide
  Use for: retrieve/deploy behavior, metadata coverage, deployment mechanics
  URL: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm

- Apex Developer Guide
  Use for: Apex behavior, testing, transactions, asynchronous patterns, implementation guidance
  URL: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm

- Apex Reference Guide
  Use for: Apex class and method signatures, built-in APIs, namespace details
  URL: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm

- Lightning Component Reference
  Use for: base Lightning components, attributes, events, supported usage
  URL: https://developer.salesforce.com/docs/platform/lightning-component-reference/guide

---

## Salesforce Architects Guidance

Use these for best practices, patterns, anti-patterns, and architecture tradeoffs.

- Salesforce Well-Architected Overview
  Use for: overall architecture quality model, trusted/easy/adaptable guidance, patterns and anti-patterns framing
  URL: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

- Integration Patterns
  Use for: system integration pattern selection, synchronous vs asynchronous tradeoffs, data/process/virtual integration design
  URL: https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html

---

## LWC and UI Development

Use these when building or reviewing `lwc/` skills or UI-heavy guidance.

- Best Practices for Development with Lightning Web Components
  Use for: LWC design guidelines, composition, DOM/event and coding best practices
  URL: https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html

- Data Guidelines
  Use for: Lightning Data Service vs wire adapters vs Apex decision-making, UI data access guidance
  URL: https://developer.salesforce.com/docs/platform/lwc/guide/data-guidelines.html

- Secure Apex Classes
  Use for: Apex security model for component-facing Apex, `with sharing`, CRUD/FLS enforcement patterns
  URL: https://developer.salesforce.com/docs/platform/lwc/guide/apex-security

---

## Domain Mapping

Use this as the default starting point when you are unsure which official docs to consult.

### Admin

- Start with Salesforce Well-Architected Overview for quality framing.
- Add the product guide most directly related to the feature if the skill makes platform-behavior claims.
- Add Integration Patterns when the topic touches APIs, outbound auth, middleware, or data sync.

### Apex

- Start with Apex Developer Guide and Apex Reference Guide.
- Add Secure Apex Classes when user-facing data access or component-facing Apex is involved.
- Add Salesforce Well-Architected Overview for quality framing.

### LWC

- Start with Lightning Component Reference, LWC Best Practices, and Data Guidelines.
- Add Secure Apex Classes if the component calls Apex.
- Add Salesforce Well-Architected Overview when architectural tradeoffs matter.

### Flow

- Start with Salesforce Well-Architected Overview.
- Add product documentation relevant to Flow behavior when the skill makes factual platform claims.
- Add Integration Patterns if the Flow uses callouts, platform events, or cross-system orchestration.

### Integration

- Start with REST API Developer Guide and Integration Patterns.
- Add Metadata API Developer Guide when the topic touches metadata movement or deployment semantics.
- Add Apex Developer Guide if the integration behavior depends on Apex implementation.

### Data / DevOps / Security

- Start with Salesforce Well-Architected Overview.
- Add the most specific official API or product guide for the behavior being described.
- Add Integration Patterns or Metadata API guidance when the topic includes promotion, deployment, or system interaction.

---

## Recording Sources In A Skill

Every new or materially revised skill should include an `## Official Sources Used` section in `references/well-architected.md`.

Format:

```markdown
## Official Sources Used

- Salesforce Well-Architected Overview — architecture quality framing
- Apex Developer Guide — transaction behavior and testing guidance
- Apex Reference Guide — language/API reference confirmation
```

Keep this concise. The point is to show which official docs informed the skill, not to restate the docs.
