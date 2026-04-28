---
name: integration-procedure-cacheable-patterns
description: "Use when designing Integration Procedures (IPs) with platform cache to cut latency and callout load. Covers cache key design, TTL selection, per-user vs org-wide partitions, invalidation on data changes, and safe fallback on cache miss/stale. Does NOT cover general IP authoring (see omnistudio-error-handling-patterns) or LWC client-side caching."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Scalability
  - Reliability
triggers:
  - "integration procedure cache"
  - "ip cacheable action"
  - "omnistudio platform cache"
  - "cache key design integration procedure"
  - "invalidate ip cache record change"
tags:
  - omnistudio
  - integration-procedure
  - cache
  - performance
  - platform-cache
inputs:
  - IP whose result repeats across calls
  - Data volatility of the source
  - Audience scope (per-user, per-org, per-tenant)
outputs:
  - Cache key + TTL design
  - Partition selection (org-wide vs session)
  - Invalidation plan
  - Fallback behavior when cache is unavailable
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Integration Procedure Cacheable Patterns

## Purpose

Integration Procedures are the workhorse for orchestrating DataRaptors
and external callouts in OmniStudio. Many IPs return mostly-static data —
product catalogs, entitlement matrices, rate tables — that is re-fetched
on every UI load. Platform Cache inside an IP cuts latency and callout
volume by orders of magnitude, but only if the cache key, TTL, partition,
and invalidation are designed together. Teams either skip caching (slow)
or cache too aggressively (stale data, cross-user leakage). This skill
codifies the decisions.

## Recommended Workflow

1. **Measure.** Log IP latency and call volume. Cacheability is a
   decision, not a reflex — some IPs shouldn't be cached.
2. **Design cache key.** Include every input that changes the result AND
   nothing that doesn't. Stable ordering matters.
3. **Pick partition.** Org-wide for shared data (catalogs, metadata),
   Session for per-user data (entitlements when scoped to the user).
4. **Choose TTL.** Align TTL to source-data SLA. Default 5-15 minutes for
   quick wins; longer needs explicit invalidation.
5. **Design invalidation.** Record-triggered flow or Apex trigger on the
   source object purges cache keys when data changes.
6. **Plan fallback.** Cache unavailable (partition full, platform error)
   must not break the IP. Fall through to live fetch.
7. **Monitor cache hit ratio.** < 40% suggests wrong key or wrong TTL.

## Cache Key Design

- Include: inputs that change the result, the API version, and the
  feature flag set that governs behavior.
- Exclude: request ids, timestamps, user-identity if the result is
  org-wide.
- Keep keys short but unambiguous; platform cache has key-length limits.

Example key: `ip:PricingMatrix:v3:sku=ABC123:region=NA:tier=GOLD`

## Partition Selection

| Partition | Scope | Use For |
|---|---|---|
| Org-wide | All users | Catalogs, reference data |
| Session | Per user | Entitlements, personalized results |

Do NOT put user-specific data in the org-wide partition. Data leaks.

## TTL Guidance

- Reference data that rarely changes: 30–60 min with explicit
  invalidation.
- User entitlements: 5–10 min.
- Pricing: 5–15 min.
- Anything regulated / audit-bound: keep short and verify invalidation
  works.

## Invalidation Patterns

- **Event-driven:** record-triggered flow publishes a Platform Event;
  invocable Apex clears the matching cache key.
- **Versioned keys:** bump a version field in the key prefix when the
  schema changes; old keys age out naturally.
- **Namespace purge:** clear an entire prefix during deploys for safety.

## Fallback

- `getPartition()` may return null if the partition is missing or full.
- Code the IP to treat cache as an accelerator, not a dependency.
- Never let a cache miss produce an error surfaced to the user.

## Anti-Patterns (see references/llm-anti-patterns.md)

- Cache results of callouts that return per-user PII into org-wide.
- Hash the entire input blob as a key (breaks invalidation).
- TTL 24h with no invalidation plan.
- Assume cache always succeeds.

## Official Sources Used

- OmniStudio Integration Procedures — https://help.salesforce.com/s/articleView?id=sf.os_design_integration_procedures.htm
- Platform Cache — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_cache_namespace_overview.htm
- OmniStudio Caching — https://help.salesforce.com/s/articleView?id=sf.os_use_platform_cache_to_improve_integration_procedure_performance.htm
- Salesforce Well-Architected Performant — https://architect.salesforce.com/docs/architect/well-architected/performant/performant
