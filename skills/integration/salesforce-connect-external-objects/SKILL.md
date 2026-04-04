---
name: salesforce-connect-external-objects
description: "Use when deciding whether Salesforce Connect and External Objects are the right fit for external data access, or when reviewing OData, cross-org, and custom adapter patterns, query limitations, and latency tradeoffs. Triggers: 'Salesforce Connect', 'External Objects', '__x', 'OData adapter', 'custom adapter'. NOT for ordinary ETL or replicated-data designs where the data should live inside Salesforce."
category: integration
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - Scalability
  - Reliability
tags:
  - salesforce-connect
  - external-objects
  - odata
  - custom-adapter
  - virtual-data
triggers:
  - "should I use Salesforce Connect or copy the data"
  - "external object query limitations in Salesforce"
  - "OData versus custom adapter for Salesforce Connect"
  - "cross org external object design"
  - "external objects performance and reporting limits"
inputs:
  - "source system type and whether the data must remain outside Salesforce"
  - "latency, availability, and write requirements"
  - "query shape, reporting needs, and relationship model"
outputs:
  - "virtual versus replicated data recommendation"
  - "review findings for adapter choice and platform-fit risks"
  - "Salesforce Connect pattern with operational guardrails"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

# Salesforce Connect External Objects

Use this skill when the architecture question is whether Salesforce should virtualize external data instead of copying it. Salesforce Connect is best when the source system stays authoritative and users need near-real-time access without a full replication pipeline. It is a poor fit when teams secretly need native Salesforce behavior on that data but do not want to admit they really need replication.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the source of truth staying outside Salesforce, and is that requirement real?
- Do users need read-only lookup-style access, or are they expecting reporting, automation, and low-latency interaction like a native object?
- Is the adapter choice OData, cross-org, or custom Apex because of source-system constraints?

---

## Core Concepts

### External Objects Are Virtual Data Surfaces

External Objects expose data that is stored outside Salesforce. That keeps storage and synchronization problems smaller, but it means performance and availability depend on the external system as well as on Salesforce.

### Adapter Choice Changes The Operating Model

OData adapters are the clean default when the source supports them. Cross-org patterns fit Salesforce-to-Salesforce virtualization. Custom adapters exist for sources that cannot expose a supported standard shape, but they increase implementation and support cost.

### Platform Feature Coverage Is Not The Same As Native Data

External Objects can participate in useful UI and query patterns, but they do not behave exactly like standard or custom objects in every part of the platform. If the use case needs native automation, reporting depth, or consistently low latency, replication may be the better answer.

### Query Shape And User Expectations Matter

Virtualized data is fine for lookup and reference views. It becomes painful when pages, related lists, or repeated queries assume local-database speed.

---

## Common Patterns

### Reference Data Lookup Pattern

**When to use:** Users need current ERP or legacy-system facts inside Salesforce without nightly copy jobs.

**How it works:** Expose the external entity as an External Object, keep queries narrow, and present the data where it supports decisions rather than where it drives heavy automation.

**Why not the alternative:** Full replication adds ETL cost and data-drift problems when users mainly need read access.

### Hybrid Pattern

**When to use:** Most data can stay external, but a hot subset or summary must behave like native Salesforce data.

**How it works:** Use Salesforce Connect for the broad virtual surface and replicate only the narrow subset that needs native workflows or reporting.

### Custom Adapter Escape Hatch

**When to use:** The source system cannot expose the right standard protocol but virtualization is still justified.

**How it works:** Build an adapter only after proving the source-of-truth and operational benefits outweigh the added complexity.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need current external data with minimal replication | Salesforce Connect | Virtual access fits the requirement |
| Need native automation, heavy reporting, and low-latency record behavior | Replicate into Salesforce | Users are really asking for local data behavior |
| Source exposes OData cleanly | OData adapter | Lowest-friction standard option |
| Source cannot expose a supported standard but virtualization is still justified | Custom adapter | Use only when the value outweighs added build and support cost |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Source-of-truth ownership is explicit and still belongs outside Salesforce.
- [ ] Adapter choice is justified by protocol and operational reality.
- [ ] Page and query design respect latency and external availability.
- [ ] Use cases that need native automation or deep reporting are challenged.
- [ ] Relationships and query limits are tested with realistic volumes.
- [ ] Reporting expectations are validated before the project promises native parity.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **External Objects are not native objects with someone else's storage** - feature expectations must be checked, not assumed.
2. **Latency belongs to the architecture** - slow external systems make Salesforce pages feel slow too.
3. **Reporting and aggregation expectations often exceed the fit** - virtualization does not equal native analytics behavior.
4. **Custom adapters are a power tool, not the default** - once chosen, you own more implementation and support surface.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Virtual-data decision | Recommendation for Salesforce Connect versus replication |
| External object review | Findings on adapter fit, performance expectations, and platform limitations |
| Hybrid architecture pattern | Guidance for when only a subset should be replicated |

---

## Related Skills

- `integration/graphql-api-patterns` - use when the real question is client-side query shaping rather than external-data virtualization.
- `data/roll-up-summary-alternatives` - use when the main gap is summary behavior over related data, not where that data is sourced.
- `integration/oauth-flows-and-connected-apps` - use when authentication to the external platform is the main blocker.
