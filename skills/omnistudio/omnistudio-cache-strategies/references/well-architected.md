# Well-Architected Notes — OmniStudio Cache Strategies

## Relevant Pillars

- **Performant** — the reason anyone opens this skill. Caching an OmniStudio
  read path is usually the largest single latency win available without
  redesigning the data model, precisely because OmniStudio components are
  called from UI render paths where every millisecond is user-visible.
- **Resilient** — a cache is an accelerator that must be allowed to fail. The
  Platform Cache documentation states that cache "isn't persisted" and offers
  "no guarantee against data loss," which makes a hard dependency on a cache
  hit an availability defect, not a performance choice.
- **Secure** — the pillar teams forget here. Cached data is not encrypted, and
  a warm read does not re-evaluate the sharing and FLS checks that ran for the
  caller who populated the entry. Caching converts an access-control question
  into a key-design question.

## Architectural Tradeoffs

- **Org cache vs session cache:** org cache maximises reuse and gives 48 hours
  of headroom; session cache isolates per user but tops out at 8 hours and
  dies with the session. The choice is dictated by the payload's audience, not
  by the desired hit ratio. Choosing on hit ratio is how personalized data ends
  up in a shared partition.
- **TTL vs explicit invalidation:** a short TTL is safe and leaves value on the
  table; a long TTL needs a real invalidation design. Because the platform
  clamps TTL to a 5-minute floor, "just use a very short TTL" is not available
  as an escape hatch — below 5 minutes the honest answer is not to cache.
- **Response cache vs metadata cache:** they solve different problems and are
  configured independently (`responseCacheType` vs `isMetadataCacheDisabled`).
  Turning metadata caching off is a debugging move that costs cold-start
  performance; it is not a way to freshen responses.
- **Caching the payload vs caching the decision:** a 100 KB per-item ceiling
  pushes design toward caching resolved outcomes (a price, an eligibility
  verdict) rather than the records they were computed from. This is usually
  the better architecture anyway — it makes the cached unit meaningful and
  independently invalidatable.
- **Performance vs auditability in regulated paths:** any cached value is a
  value that was computed at an earlier time under an earlier permission
  state. Where a decision must be reproducible and attributable, cache the
  inputs' identity rather than the decision itself, or do not cache.

## Where This Skill Stops

Cache-key design, partition selection, and invalidation *for Integration
Procedures specifically* — including the Cache Block element — belong to
`omnistudio/integration-procedure-cacheable-patterns`. This skill owns the
cross-cutting layer taxonomy, the Data Mapper side, and org-level setup.

Symptom-first performance triage across the whole platform (Apex CPU, SOQL
selectivity, LDV, LWC render, Platform Cache) is routed by
`standards/decision-trees/performance-tuning.md`. Read that tree before
concluding that caching is the right lever — it frequently is not, and a cache
layered over an unselective query hides the defect rather than fixing it.

## Hygiene

- Every cached component records, in the design doc: which layer, which cache
  type, what TTL, what the invalidation lever is, and who may pull it.
- Cache keys go through one helper that enforces the alphanumeric and
  50-character constraints. Not enforced per call site.
- Partition allocation is verified as non-zero before any cache tuning work is
  scheduled, because zero allocation makes every downstream measurement
  meaningless and produces no error.
- Serialized payload size is measured, not estimated, against the 100 KB
  per-item ceiling.
- The runtime (standard vs managed package) is recorded at the top of any
  OmniStudio design document, because half the published guidance applies to
  only one of them.

## Official Sources Used

- **Platform Cache Limits — Apex Developer Guide** —
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_platform_cache_limits.htm
  — source for every number in this skill: maximum key size 50 characters;
  session cache TTL min 300 s / max 28,800 s; org cache TTL min 300 s / max
  172,800 s / default 86,400 s; maximum size of a single cached item 100 KB;
  minimum partition size 1 MB; maximum local cache per partition per request
  500 KB (session) and 1,000 KB (org). Verified 2026-08-14.
- **Platform Cache Considerations — Apex Developer Guide** —
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_platform_cache_limitations.htm
  — source for "Cache isn't persisted. There's no guarantee against data
  loss.", "Some or all cache is invalidated when you modify an Apex class in
  your org.", "Data in the cache isn't encrypted.", the 8-hour/48-hour storage
  statement, and the note on Salesforce Flow restrictions for session cache.
  Verified 2026-08-14.
- **Cache.Partition class — Apex Reference Guide** —
  https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_cache_Partition.htm
  — source for the `put(key, value)` contract: a valid key must be non-null
  and contain alphanumeric characters only, and `Cache.InvalidParamException`
  is thrown on validation failure. Verified 2026-08-14.
- **Store and Retrieve Values from the Org Cache — Apex Developer Guide** —
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_platform_cache_org_examples.htm
  — source for the fully qualified key format `namespace.partition.key`, the
  `local.` prefix equivalence, and `getPartition('myNs.myPartition')` usage.
  Verified 2026-08-14.
- **OmniDataTransform — Industries Common Resources Developer Guide (API 67.0)** —
  https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/meta_omnidatatransform.htm
  — source for `responseCacheTtlMinutes`, `responseCacheType`,
  `fieldLevelSecurityEnabled`, `requiredPermission`,
  `synchronousProcessThreshold`, `processSuperBulk`, `rollbackOnError`,
  `errorIgnored`, `active`, `versionNumber`, and the `type` values
  extract/transform/load. Verified 2026-08-14.
- **OmniIntegrationProcedure — Industries Common Resources Developer Guide (API 67.0)** —
  https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/meta_omniintegrationprocedure.htm
  — source for `responseCacheType` ("session or Org"),
  `isMetadataCacheDisabled` (default false), `requiredPermission`, `isActive`,
  and the absence of any documented TTL field on this type. Verified
  2026-08-14.
- **OmniScript — Industries Common Resources Developer Guide (API 67.0)** —
  https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/meta_omniscript.htm
  — confirms `responseCacheType` and `isMetadataCacheDisabled` also exist on
  OmniScript. Verified 2026-08-14.
- **OmniStudioSettings — Industries Common Resources Developer Guide (API 67.0)** —
  https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/meta_omnistudiosettings.htm
  — source for `enableStandardOmniStudioRuntime` (API 65.0+), `enableOaForCore`
  (API 63.0+), `enableOmniStudioMetadata` (irreversible once enabled), and
  `enableOmniStudioDrVersion`. Verified 2026-08-14.
- **DataRaptor Features for Data Integration — Trailhead** —
  https://trailhead.salesforce.com/content/learn/modules/omnistudio-dataraptors/explore-dataraptor-features
  — source for the exact Options-tab labels **Platform Cache Type** ("Session
  Cache for data related to users and their login sessions, or Org Cache for
  all other types of data") and **Time to Live in Minutes**, and for the
  field-level-access option. Verified 2026-08-14.
- **Configuring Integration Procedures for Efficiency — Trailhead** —
  https://trailhead.salesforce.com/content/learn/modules/omnistudio-integration-procedure-fundamentals/configure-your-integration-procedure
  — source for the fact that an Integration Procedure has a procedure-level
  **Cache Configuration** section in its configuration panel, alongside
  Chainable Configuration, Queueable Chainable Limits, and Test Configuration.
  Verbatim: **"Use a cache to store frequently accessed, infrequently updated
  Integration Procedure data. This saves round trips to the database and
  improves performance."** The page does not name the individual fields inside
  that section. Verified 2026-08-14.
- **What's New in Salesforce Omnistudio Standard Designers — Salesforce Developers blog** —
  https://developer.salesforce.com/blogs/2026/03/whats-new-in-salesforce-omnistudio-standard-designers
  — used only for the standard-runtime-vs-package framing (designers and
  runtime available without package installation; existing package customers
  must migrate). The post states **no** retirement or end-of-support dates, so
  this skill asserts none. Verified 2026-08-14.

### Sources deliberately not used

Salesforce Help articles on OmniStudio caching and security
(`os_cache_for_dataraptors_and_integration_procedures_*`,
`os_security_for_dataraptors_and_integration_procedures_*`,
`sf.os_configure_an_integration_procedure`) are the canonical prose for this
topic, and Help publishes a separate "(Managed Package)" variant of several of
them. `help.salesforce.com` renders no article text to a document fetcher, so
none of their content is quoted here. Every claim above is grounded in a
`developer.salesforce.com` or Trailhead source instead. Unverifiable claims
that appear in the wider community literature are marked inline with
`<!-- UNVERIFIED -->` in `SKILL.md`, `examples.md`, and `gotchas.md` rather
than being stated as fact.

Two marked items in particular, so they are easy to find:

- The **Required Permission bypass under metadata caching** (`SKILL.md`
  "Security Consequences Of A Warm Read", `gotchas.md` §4) is *reported*
  security research from AppOmni (2025), not a Salesforce-documented behaviour.
  Both the behaviour and the remediation setting names are unverified.
- The individual field labels inside an Integration Procedure's **Cache
  Configuration** section are unverified; only the section's existence and its
  Trailhead description are confirmed.
