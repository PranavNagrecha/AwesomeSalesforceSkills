---
name: omnistudio-cache-strategies
description: "Configure caching on DataRaptors and Integration Procedures for response-time gains. Triggers: OmniStudio cache, DataRaptor cache, IP cache TTL. NOT for IP-specific cacheable design — use omnistudio/integration-procedure-cacheable-patterns."
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
  - "why is my omnistudio cache not working"
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
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# OmniStudio Cache Strategies

Use this skill when deciding whether, where, and how to cache an OmniStudio
read path — and when diagnosing a cache that appears configured but is not
changing anything. It covers the three distinct caches that share the word
"cache" in OmniStudio, the Platform Cache limits every one of them inherits,
and the security consequences of serving a payload that was computed for
somebody else.

---

## Before Starting

- **Which runtime is this org on?** Standard runtime and the Vlocity managed
  package have separate documentation, separate settings, and in places
  separate behaviour. `OmniStudioSettings.enableStandardOmniStudioRuntime`
  (API 65.0+) and `enableOaForCore` (64.0+) answer the question. Most
  published OmniStudio writing describes the package; assume nothing until
  you have checked.
- **Is Platform Cache actually allocated?** A partition with no capacity
  produces no error and no speedup. Verify allocation in Setup before
  scheduling any tuning work.
- **What is the freshness contract in business terms?** Not "as fresh as
  possible" — a number, agreed with whoever owns the data. The platform's
  5-minute TTL floor means some answers rule caching out entirely.
- **Who can reach this component?** Internal only, authenticated portal, or
  guest. The answer changes the cache type and may forbid caching outright.

---

## The Three Caches

Naming the layer is the whole diagnostic. These are independent:

| Layer | Stores | Configured by | Symptom when misconfigured |
|---|---|---|---|
| **Component metadata cache** | the compiled component definition | `isMetadataCacheDisabled` (boolean, default `false` — so it is **on** by default) on `OmniIntegrationProcedure` and `OmniScript` | slow cold start after deploy |
| **Response cache** | the output payload | Data Mapper Options tab (**Platform Cache Type**, **Time to Live in Minutes**); IP **Cache Configuration** section (whole response) or **Cache Block** element (enclosed steps); `responseCacheType` in metadata, plus `responseCacheTtlMinutes` on the Data Mapper type only | warm reads no faster than cold |
| **Platform Cache** | the underlying key/value substrate | Setup → Platform Cache partition allocation | nothing is cached at all, silently |

`isMetadataCacheDisabled` is a negative. Default `false` means metadata
caching is already enabled; setting it `true` turns caching **off**. It is a
debugging lever, not a performance lever, and flipping it will not change what
a warm read returns.

---

## The Limits That Decide The Design

Every OmniStudio response cache sits on Platform Cache and inherits its
bounds. These are the numbers that most often invalidate a proposed design:

| Constraint | Value |
|---|---|
| TTL minimum (org and session) | 300 s / 5 minutes |
| TTL maximum — org cache | 172,800 s / 48 hours (default 86,400 s / 24 h) |
| TTL maximum — session cache | 28,800 s / 8 hours |
| Maximum cache key size | 50 characters |
| Cache key characters | **alphanumeric only** — `put()` throws `Cache.InvalidParamException` otherwise |
| Maximum size of a single cached item | 100 KB |
| Minimum partition size | 1 MB |
| Maximum local cache per partition, per request | 500 KB session / 1,000 KB org |

Three consequences worth internalising:

1. A freshness requirement tighter than 5 minutes is a decision **not to
   cache**, not a smaller number in the TTL field.
2. The Redis-style key `catalog:v2:region=NA` is illegal on this platform.
   Use camelCase with no separators.
3. Caching the whole aggregate response usually exceeds 100 KB. Cache the
   resolved decision instead.

---

## Security Consequences Of A Warm Read

A cache hit returns a payload computed during somebody else's request, under
that request's permission evaluation. Two documented facts and one reported
behaviour follow:

- **Documented.** **"Data in the cache isn't encrypted."** Shield Platform
  Encryption does not follow a value into a cache entry.
- **Documented.** Org cache is addressed by a key. If the key is derived from
  **caller-supplied** inputs rather than a **server-resolved** subject, the
  caller chooses which entry to read. On a guest-reachable page this is a
  cross-tenant read.
- **Reported, not documented.** Metadata caching is reported to let a component
  execute for a user who would fail its **Required Permission** check on a cold
  run, because that check sits on the path the cache skips. Treat this as a
  reason not to lean on Required Permission as your only authorization
  boundary — not as a Salesforce-documented behaviour you can cite. See
  `gotchas.md` §4 for the provenance.

<!-- UNVERIFIED: the Required Permission bypass in the third bullet is not
stated in any Salesforce-published doc I could read. It traces to AppOmni's
2025 Salesforce Industry Cloud security research, reported via CSO Online and
Information Security Buzz. The behaviour itself, its scope (standard runtime vs
managed package), and the remediation settings are all unconfirmed against
Salesforce. Do not present it to a customer as documented platform behaviour;
reproduce it in a sandbox first. -->

The defensive posture the third bullet implies is sound regardless of whether
the specific bypass reproduces in your org: an access check that runs only on a
cold path is not an authorization boundary. Gate on the object and field
permissions of the running user and on the sharing model, which are evaluated
per call.

Keep `fieldLevelSecurityEnabled` true on Data Mappers. It governs the cold
path, and the cold path decides what every subsequent warm read returns.

---

## Recommended Workflow

1. Establish the runtime (standard vs managed package) and confirm Platform
   Cache partition allocation is non-zero. Stop here if it is zero — nothing
   downstream is measurable until it is fixed.
2. Measure the read path cold, as a user from the target audience. Record p50
   and p95 and the serialized payload size in bytes.
3. Classify the payload: identical for everyone, or scoped to a person. This
   choice — not the desired hit ratio — sets `responseCacheType` to `org` or
   `session`. Anything guest-reachable or containing PII defaults to no cache.
4. Set a TTL inside the platform range (5 min – 48 h org, 5 min – 8 h session)
   that matches the agreed freshness contract. If the contract is tighter than
   5 minutes, record the decision not to cache and stop.
5. Design invalidation before shipping: a version discriminator inside the
   cache key for routine releases, plus a documented purge path for incidents.
   A TTL alone is a staleness bound, not an invalidation mechanism.
6. Verify in the runtime context, as two different users, comparing payloads
   and not only elapsed time. Designer preview timings do not demonstrate the
   response cache.
7. Instrument hit ratio and cold-start load. Plan capacity for the cold-start
   spike that follows an eviction — cache "isn't persisted" and an Apex deploy
   may clear it.

---

## Review Checklist

- [ ] Runtime recorded (standard vs managed package) before any doc was cited
- [ ] Partition allocation verified non-zero in Setup
- [ ] TTL within 5 min – 48 h (org) or 5 min – 8 h (session)
- [ ] `responseCacheType` matches the payload's audience, not its latency
- [ ] No org cache on a guest-reachable, portal, or PII component
- [ ] Cache keys are alphanumeric only and ≤ 50 characters, enforced in one helper
- [ ] Serialized payload measured against the 100 KB per-item ceiling
- [ ] Version discriminator in the key, plus a documented purge path
- [ ] `fieldLevelSecurityEnabled` true on cached Data Mappers
- [ ] No cache on a Data Mapper whose `type` is `Load`
- [ ] Read path treats a miss as a latency event, never an error

---

## Worked Examples (see `references/examples.md`)

- *Naming the layer* — the three caches, and which one your symptom belongs to
- *Reference-data Data Mapper* — the full Options-tab and metadata configuration
- *The cache that silently did nothing* — partition allocation
- *Cache key characters* — the `Cache.InvalidParamException` reproduction
- *Org vs session from the payload* — deciding on audience, not latency
- *Invalidation on deploy* — the case nobody configures

## Common Gotchas (see `references/gotchas.md`)

- TTLs below 5 minutes are below the platform floor and do not mean what they say
- Keys with `:` or `=` throw `Cache.InvalidParamException`
- Cached data is unencrypted and warm reads do not re-check sharing
- `isMetadataCacheDisabled` is a negative that defaults to `false`
- The IP metadata type documents a cache *type* but no TTL field — which means
  the duration does not round-trip through metadata, not that the setting
  is missing from the designer
- Standard runtime and managed package have parallel, differently-behaving docs

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Redis-style punctuated cache keys
- TTL values below the 5-minute floor
- Inventing property names (`cacheEnabled`, `isCacheable`, `cacheTTL`)
- Answering with managed-package behaviour for a standard-runtime org
- Org cache for anything the caller can key
- Treating TTL as the invalidation design

---

## Related

- **omnistudio/integration-procedure-cacheable-patterns** — owns cache-key
  design, partition selection, the Cache Block element, and invalidation for
  Integration Procedures specifically.
- **omnistudio/omniscript-session-state** — when the requirement is durability
  across a logout rather than latency, session cache is the wrong store.
- **omnistudio/omnistudio-security** — Required Permission, guest exposure, and
  the security settings referenced in `gotchas.md` §4.
- **standards/decision-trees/performance-tuning.md** — read before concluding
  that caching is the right lever. A cache layered over an unselective query
  hides the defect rather than fixing it.

## Official Sources Used

See `references/well-architected.md` for the full source list with the
specific claim each source grounds.
