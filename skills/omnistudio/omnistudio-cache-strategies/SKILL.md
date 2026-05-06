---
name: omnistudio-cache-strategies
description: "Configure caching on DataRaptors and Integration Procedures to cut response times, with cache-bust and freshness guarantees. NOT for platform-level org cache."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
triggers:
  - "dataraptor cache"
  - "integration procedure cache"
  - "omnistudio cache ttl"
  - "cache bust omniscript"
tags:
  - omnistudio
  - cache
  - performance
inputs:
  - "current response times per IP/DR"
  - "data freshness requirements"
outputs:
  - "cache config + bust strategy + monitoring"
dependencies: []
runtime_orphan: true
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# OmniStudio Cache Strategies

OmniStudio supports caching per-record on DataRaptors (cache duration in minutes) and Integration Procedures (cache-enabled flag with TTL). Used correctly, cache cuts 50–90% of repeated calls; used wrong it serves stale data. This skill walks through identifying read-heavy paths, choosing a TTL aligned to business freshness tolerance, implementing a deterministic cache-bust on mutation, and monitoring hit ratio so the cache's contribution is observable.

## Adoption Signals

Read-heavy IPs/DRs where source data changes infrequently (product catalog, reference data).

- Tune the Integration Procedure cache for any IP whose response shape is stable for hours and whose source touch is expensive.
- DataRaptor cache when transform output (label translation, code-table lookup) is identical across users.

## Recommended Workflow

1. Identify read-heavy IP/DR with stable data.
2. Enable cache; set TTL based on business tolerance for staleness (e.g., 5 min for catalog, 60 min for reference data).
3. Implement bust strategy: a mutation path publishes a Platform Event; subscriber clears cache via Apex `CacheMgmt`.
4. Monitor hit ratio via custom logging on IP/DR invocation.
5. Stress test: simulate peak load, confirm cache absorbs expected fraction.

## Key Considerations

- Per-user cache partitions avoid leaking one user's data to another.
- Cache doesn't respect sharing — ensure cached key includes user context if sharing-sensitive.
- TTL < 1 min likely not worth it.
- Cache failure falls through to live call — a bug here is 'slow', not 'wrong'.

## Worked Examples (see `references/examples.md`)

- *Product catalog IP* — Hundreds of shoppers
- *Bust on update* — Admin edits reference data

## Common Gotchas (see `references/gotchas.md`)

- **Sharing leak** — User A sees User B's filtered list.
- **Stale after bug fix** — Patched data still missing.
- **Over-long TTL** — Business data stale.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Cache with no bust strategy
- Global cache for user-specific data
- Absurdly long TTLs

## Official Sources Used

- OmniStudio Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer.meta/omnistudio_developer/
- OmniStudio for Salesforce — https://help.salesforce.com/s/articleView?id=sf.os_omnistudio_for_salesforce_overview.htm
- OmniScript to LWC OSS — https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer.meta/omnistudio_developer/os_migrate_from_vf_to_lwc.htm
