---
name: integration-procedure-cacheable-patterns
description: "Use when designing Integration Procedures (IPs) with platform cache to cut latency and callout load. Covers Cache Block boundary, cache key design, per-user vs org-wide partitions, invalidation on data changes, and safe fallback on cache miss. NOT for general IP authoring or LWC client-side caching — use omnistudio/integration-procedures."
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
  - "omnistudio cache block"
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
runtime_orphan: true
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# Integration Procedure Cacheable Patterns

Integration Procedures orchestrate Data Mappers, Apex, and external callouts,
and they sit on UI render paths where their latency is directly user-visible.
Many of them return mostly-static data that is re-fetched on every page load.
Caching cuts that cost by orders of magnitude — but only if the cache scope,
key, partition, and invalidation are designed together. This skill
covers those four decisions and the failure modes each one produces when it is
made by reflex.

---

## Two Caching Surfaces, Not One

An Integration Procedure has **two** places to configure response caching, and
picking between them is the structural decision that reorganises everything
else.

**Procedure scope — the Cache Configuration section** of the Integration
Procedure's configuration panel, sitting alongside Chainable Configuration,
Queueable Chainable Limits, and Test Configuration. Trailhead describes it
verbatim as: *"Use a cache to store frequently accessed, infrequently updated
Integration Procedure data. This saves round trips to the database and improves
performance."* It caches the procedure's response as one unit.

**Block scope — the Cache Block element**, one of the four designer Groups:
*"Saves the output of the steps within it to a session or org cache for quick
retrieval."* It caches only the enclosed steps' output, so the boundary can sit
anywhere inside the procedure.

| Reach for | When |
|---|---|
| **Cache Configuration** (procedure) | Every step is a read, the whole response has one audience, and one freshness contract covers all of it. |
| **Cache Block** (element) | Some steps must run on every call — an audit write, a correlation id, a mutation, a personalized resolution — or different parts of the response have different audiences or TTLs. |

Most non-trivial IPs end up on the block, because "every step is a read" is a
stronger condition than it sounds. But the procedure-level setting is real, and
for a genuinely read-only procedure it is the simpler answer.

The four designer Groups, for orientation:

| Group | Behaviour |
|---|---|
| **Cache Block** | "Saves the output of the steps within it to a session or org cache for quick retrieval" |
| **Conditional Block** | "Executes if a specified condition is true or treats the steps within it as a series of mutually exclusive alternatives" |
| **Loop Block** | "Iterates over the items in a data array, repeating the Actions within it for each item" |
| **Try-Catch Block** | "Lets you *try* running the steps inside the block and then *catch* the error if a step fails" |

### What The Metadata Type Carries — And What That Does Not Prove

The documented caching surface of `OmniIntegrationProcedure` at API 67.0 is two
fields:

| Field | Meaning |
|---|---|
| `responseCacheType` | "Response cache used for the integration procedure (session or Org)" |
| `isMetadataCacheDisabled` | boolean, default `false` — a **negative** name, so metadata caching is already **on** |

There is **no TTL field on this type.** `responseCacheTtlMinutes` is real, but
it is documented on `OmniDataTransform` — the Data Mapper type — not here.
Transplanting it into IP metadata is the most common wrong answer in this
domain.

Read that as a statement about the *metadata surface*, not about the designer.
It means the cache duration is not round-trippable through this metadata type
at API 67.0: record it in the design doc and confirm it in the org rather than
diffing it out of source control. It is **not** evidence that the designer
lacks a procedure-level cache setting — the Cache Configuration section above
is exactly that setting. A metadata type not surfacing a field is a gap in the
metadata type.

<!-- UNVERIFIED: the individual field labels inside the IP's Cache
Configuration section — reportedly **Platform Cache Type** and **Time to Live
in Minutes**, mirroring the Data Mapper Options tab — come from Salesforce Help
("Configure an Omnistudio Integration Procedure",
id `sf.os_configure_an_integration_procedure`). help.salesforce.com renders no
article text to a document fetcher, so the exact labels on the IP panel are
unconfirmed here. The section's existence and its description ARE confirmed,
verbatim, from the Trailhead unit cited in `references/well-architected.md`.
Check the panel in the org before quoting either label to a customer. -->

Three consequences follow from the block being available as a unit of caching:

1. You can cache part of a procedure — a shared reference lookup inside the
   block, a personalized resolution outside it.
2. You can have several blocks with different scopes in one IP.
3. **Anything with a per-call requirement must live outside the block.** On a
   hit, no step inside it executes. That is the mechanism, and it is how a
   caching change becomes a missing-audit-trail incident. The identical hazard
   applies at procedure scope, only wider: a cached response means the *whole*
   procedure was skipped, so a procedure-level cache is only correct when
   nothing in it needed to run.

---

## The Four Decisions

### 1. Scope, then boundary

Apply one question to every step: *must this be true on the ten-thousandth
call as well as the first?* If **no step** answers yes, the procedure is a pure
read and procedure-level Cache Configuration is the simpler design. If any step
answers yes, you need a Cache Block, and that step goes outside it.

| Outside the block, always | Inside the block |
|---|---|
| DML (Data Mapper Load, Delete) | Data Mapper Extract / Transform |
| Audit and logging writes | HTTP Action — GET only |
| Correlation ids, timestamps | Remote Action that is a pure read |
| Rate-limit and quota counters | Decision Matrix / Expression Set evaluation |
| Consent capture | |

### 2. Key

Platform Cache keys must contain **alphanumeric characters only** — `put()`
throws `Cache.InvalidParamException` otherwise — and the **maximum key size is
50 characters**. Colons, equals signs, hyphens, and underscores are all
illegal inside the key segment, which catches people out because
`omniProcessKey` has the form `Type_SubType`.

```text
Shape:  <procKeyCamelCased><schemaVersion><discriminators, FIXED order>
Legal:  productCatalogV4NAUSD
Illegal: ip:Product_Catalog:v4:region=NA:currency=USD
```

Include every input that changes the result, plus a schema version you
control. Exclude correlation ids, timestamps, and — for org cache — anything
identifying the caller. Fix the discriminator order explicitly; deriving it
from `Map` iteration order silently halves the hit ratio.

### 3. Partition

Decide from the payload's audience, never from the desired hit ratio.

| | Org cache | Session cache |
|---|---|---|
| Scope | all callers | one user session |
| TTL range | 300 s – 172,800 s (48 h), default 86,400 s | 300 s – 28,800 s (8 h) |
| Ends when | TTL | TTL **or session end, whichever first** |
| Use for | catalogs, reference data, no PII | entitlements, personalized results |

The question that decides it: is the subject **server-resolved** (`%UserId%`
from the session) or **caller-supplied** (an input-map value)? If the caller
supplies the inputs the key is built from, the caller chooses which entry to
read. On a guest page that is an enumeration primitive, not a coincidence. And
Platform Cache documentation states plainly: **"Data in the cache isn't
encrypted."**

### 4. Invalidation

A TTL is a staleness *bound*, not an invalidation *mechanism*.

- **Payload shape changed** → bump the schema-version discriminator in the key
  prefix. Atomic with the deploy, cannot half-fail, needs no runtime hook,
  orphans age out on their own TTL. This is the default.
- **Wrong value shipped and must go now** → an explicit, permission-gated
  purge. An incident path, not a release step.
- **Do not build on** "some or all cache is invalidated when you modify an
  Apex class in your org." Real and documented, but it does not fire for the
  metadata-only deploys that are most of OmniStudio's change traffic.

---

## Cache Is Not Chainable

These read as alternatives and are orthogonal. Caching reduces *repeat* cost;
Chainable reduces *single-execution* cost. A cold call gets nothing from a
cache — and the cold call is the one that breaches the limit.

| Symptom | Lever |
|---|---|
| Warm calls slow | Cache Block |
| **Cold** call breaches SOQL / CPU / heap / DML | Chainable |
| DML step immediately before an HTTP callout | **Chain On Step** |
| Long-running, can be asynchronous | Queueable Chainable |

Chainable thresholds are bounded by the underlying Apex governor limits:
synchronous 100 SOQL / 10,000 ms CPU / 6 MB heap / 150 DML; Queueable
Chainable 200 SOQL / 60,000 ms CPU / 12 MB heap. When a step exceeds the
configured limits, "the interim results are saved and the step continues in a
new transaction." Use both: the block so warm calls skip the work, chainable
so the cold call survives.

---

## Recommended Workflow

1. Measure first. Log IP latency (p50, p95), call volume, and the **serialized
   payload size in bytes**. Cacheability is a decision, not a reflex, and the
   100 KB per-item ceiling rules some payloads out before design starts.
2. Pick the scope, then draw the boundary. Walk every step and ask whether it
   must run on every call. No such step anywhere → procedure-level Cache
   Configuration. Any such step → a Cache Block with that step outside it. This
   is the decision with the worst failure mode, so make it before the ones that
   feel more technical.
3. Pick the partition from the payload's audience. Org cache only for payloads
   identical for every caller and free of PII; session cache with a
   server-resolved subject for anything personal; no cache for guest-reachable
   PII.
4. Build the key in one helper: alphanumeric only, ≤ 50 characters, fixed
   discriminator order, schema-version prefix retained for purging. Unit-test
   that two differently-ordered input maps produce the same key.
5. Choose a TTL inside the platform range — 5 min to 48 h (org), 5 min to 8 h
   (session). If the freshness contract is tighter than 5 minutes, record the
   decision **not** to cache and stop.
6. Design invalidation before shipping: version bump for shape changes, purge
   path for value emergencies. Answer the question "a wrong value ships at
   09:00 — what makes the fix visible before the TTL expires?"
7. Make the miss path structurally safe. Null-check `getPartition()`, treat a
   null `get()` as routine, and confirm no user-visible error can originate in
   the cache layer. Then capacity-plan for the cold-start load after a full
   eviction, not for the steady-state hit ratio.

---

## Review Checklist

- [ ] Cache scope chosen deliberately — procedure-level Cache Configuration
      only if no step needs to run per call; otherwise a Cache Block
- [ ] No DML, audit write, counter, or timestamp inside a Cache Block
- [ ] No non-GET HTTP action inside a Cache Block
- [ ] Key is alphanumeric only and ≤ 50 characters, built in one helper
- [ ] Discriminator order fixed and unit-tested against map-ordering
- [ ] Schema-version discriminator present in the key prefix
- [ ] `responseCacheType` matches the payload's audience
- [ ] No org cache on a guest-reachable, portal, or PII procedure
- [ ] TTL within 5 min – 48 h (org) or 5 min – 8 h (session)
- [ ] Serialized payload measured against the 100 KB ceiling
- [ ] `getPartition()` null-checked; a miss is a latency event, never an error
- [ ] Cold-path governor-limit risk addressed by Chainable, not by the cache
- [ ] Invalidation lever named, with an owner for the purge path

---

## Worked Examples (see `references/examples.md`)

- *Two caching surfaces* — procedure-level Cache Configuration vs the Cache
  Block, and what block scoping buys you
- *Product catalog* — drawing the boundary around the read only
- *One step in the wrong place* — how caching deletes an audit trail
- *Key design under the real constraints* — the 50-char alphanumeric version
- *Per-user entitlements* — session cache with a server-resolved subject
- *Cache Block and Chainable* — orthogonal levers, and how they compose
- *Invalidation atomic with the deploy* — the version-discriminator pattern

## Common Gotchas (see `references/gotchas.md`)

- Steps inside a Cache Block do not run on a hit — including the ones you needed
- Underscores are illegal in keys, and `omniProcessKey` contains one
- `Map` iteration order silently halves the hit ratio
- `getPartition()` returning null is normal, not exceptional
- The IP metadata type has a cache *type* but no TTL field — a metadata gap,
  not a missing designer feature
- Only one IP per Type/SubType can be active, which is why the prefix is stable

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Concluding a designer feature is absent because the metadata type omits it
- Side-effecting steps inside the Cache Block
- Redis-style punctuated cache keys
- Org cache because the input signature "looks unique"
- TTL presented as the whole invalidation story
- Failing hard on a cache miss
- Caching to fix a governor-limit breach

---

## Related

- **omnistudio/omnistudio-cache-strategies** — owns the cross-cutting cache
  taxonomy (metadata vs response vs Platform Cache), the Data Mapper caching
  surface, and org-level partition setup.
- **omnistudio/omnistudio-performance** — when the answer is that the IP should
  not be doing this work at all.
- **omnistudio/omnistudio-security** — Required Permission, guest exposure, and
  the cached-metadata security settings.
- **standards/decision-trees/performance-tuning.md** — read before concluding
  caching is the right lever. A cache over an unselective query hides the
  defect rather than fixing it.

## Official Sources Used

See `references/well-architected.md` for the full source list with the
specific claim each source grounds.
