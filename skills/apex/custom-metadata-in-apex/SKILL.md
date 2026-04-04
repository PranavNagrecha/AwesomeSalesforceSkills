---
name: custom-metadata-in-apex
description: "Use when Apex must read, interpret, or deploy Custom Metadata Type configuration, or when deciding between Custom Metadata Types, Custom Settings, and Custom Labels. Triggers: 'Custom Metadata Type', '__mdt', 'getInstance', 'Apex Metadata API', 'protected custom metadata'. NOT for setup-only administration with no Apex behavior, packaging, or deployment concern."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "how do I query custom metadata in Apex"
  - "custom metadata type versus custom settings"
  - "Apex Metadata API for custom metadata records"
  - "protected custom metadata in managed package"
  - "do tests see custom metadata records"
tags:
  - custom-metadata
  - __mdt
  - apex-metadata-api
  - configuration
  - packaging
inputs:
  - "the configuration use case and whether reads only or metadata updates are needed"
  - "packaging model such as unpackaged, unlocked, or managed package"
  - "test behavior, namespace, and visibility constraints"
outputs:
  - "configuration storage recommendation"
  - "review findings for read, test, and deployment risks"
  - "Apex pattern for reading or deploying custom metadata safely"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

# Custom Metadata In Apex

Use this skill when configuration belongs in metadata and Apex is either the consumer or the initiator of a metadata deployment path. The main goal is to keep behavior configurable without designing Custom Metadata Types as if they were ordinary row data.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the requirement read only configuration, subscriber-editable setup, or package-controlled behavior?
- Does Apex only need to read `__mdt` records, or must some setup flow eventually create or update metadata records?
- Are tests validating multiple configuration variants, packaging visibility, or namespace behavior?

---

## Core Concepts

### Custom Metadata Is App Configuration

Custom Metadata Types are for durable application configuration. In Apex, that usually means querying `__mdt` records or using generated accessors such as `getInstance()` and `getAll()` where that makes the intent clearer. Treat those records as part of the app contract instead of as business data.

### Read Paths And Write Paths Differ

Reading custom metadata in Apex is straightforward. Updating records is different. Do not design business logic around ordinary DML on `__mdt`. Metadata deployment is the real write boundary, and packaging visibility or subscriber-control rules determine what can actually be changed.

### Tests See Metadata Differently Than Data

Apex tests can see custom metadata records without `SeeAllData=true`. That is useful, but it also means tests can quietly rely on org metadata unless the dependency is explicit and deliberate.

### CMT, Settings, And Labels Solve Different Problems

Use Custom Metadata Types for deployable, versioned configuration. Use Custom Labels for translatable user-facing text. Use Custom Settings only when the org still depends on older hierarchy or runtime semantics that are a better fit than CMT.

---

## Common Patterns

### Configuration Reader Wrapper

**When to use:** Business logic needs stable access to config and should not scatter raw `__mdt` queries everywhere.

**How it works:** Create a small service that loads the relevant record, applies defaults, and exposes intent-level methods such as `isFeatureEnabled()` or `getEndpointKey()`.

**Why not the alternative:** Direct `__mdt` queries in many classes duplicate field knowledge and test assumptions.

### Strategy Table In Metadata

**When to use:** Routing, thresholds, or feature rules differ by region, channel, product, or environment.

**How it works:** Store rule dimensions and outputs in custom metadata, then have Apex resolve the best matching record and execute behavior from that result.

### Metadata Deployment Boundary

**When to use:** Admin tooling or packaged setup must create or update metadata records.

**How it works:** Keep deployment-oriented logic separate from transaction-level business services. Apex can initiate metadata deployment, but runtime services should not pretend that `insert` and `update` on `__mdt` are ordinary persistence.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Versioned config that should move through metadata deployment | Custom Metadata Type | Best fit for deployable app configuration |
| User-facing translatable text only | Custom Labels | Better than forcing text into metadata rows |
| Legacy per-user or hierarchy semantics | Evaluate hierarchy/custom settings carefully | CMT is not always a drop-in replacement |
| Runtime transaction wants to create config as row data | Redesign around metadata deployment or normal objects | `__mdt` is not standard business-data storage |

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

- [ ] Configuration stored in `__mdt` is truly setup, not transactional data.
- [ ] Apex reads are centralized behind a small config boundary where possible.
- [ ] Tests do not rely on accidental org metadata without stating it.
- [ ] No runtime design assumes ordinary DML on custom metadata.
- [ ] Packaging visibility and subscriber edit rules are understood.
- [ ] The choice between CMT, labels, settings, and ordinary data is deliberate.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Tests can see custom metadata without `SeeAllData=true`** - helpful, but easy to misuse if the dependency is never named.
2. **Write paths are metadata deployments, not normal DML** - code that treats `__mdt` like `__c` data eventually breaks.
3. **Protected and subscriber-controlled behavior matters in packages** - a design that works unpackaged can fail once namespace and visibility rules apply.
4. **Custom Labels are not structured configuration** - once rules need keys, thresholds, or multiple rows, labels are the wrong storage model.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Configuration decision | Recommendation for CMT vs labels vs settings vs ordinary data |
| Apex config review | Findings on read boundaries, test assumptions, and deployment risks |
| Metadata pattern scaffold | Reader service or metadata-deploy boundary example |

---

## Related Skills

- `admin/connected-apps-and-auth` - use when the real problem is integration credential governance, not where Apex stores config.
- `apex/test-class-standards` - use when metadata-dependent tests are part of a broader testing problem.
- `data/roll-up-summary-alternatives` - use when the actual gap is summary behavior over data relationships rather than configuration storage.
