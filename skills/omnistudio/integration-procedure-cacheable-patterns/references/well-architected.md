# Well-Architected Notes — IP Cacheable Patterns

## Relevant Pillars

- **Performant** — an Integration Procedure sits on a UI render path, so its
  latency is directly user-visible. A Cache Block around the expensive read is
  usually the largest available win short of redesigning the data flow.
- **Scalable** — callout budgets, SOQL counts, and external-system load all
  drop roughly linearly with hit ratio. This is the pillar that justifies the
  work to a platform owner: caching a storefront catalog read is as much about
  the pricing service's capacity as about the shopper's wait.
- **Resilient** — Platform Cache documentation is explicit that cache "isn't
  persisted" and offers "no guarantee against data loss." Any design in which a
  miss changes the *result* rather than the *latency* has converted an
  accelerator into a dependency, which is a resilience defect.
- **Secure** — a warm read returns a payload computed during someone else's
  request. Org cache turns access control into key design, and key design is
  the part that gets reviewed least.

## Architectural Tradeoffs

- **Block scope vs procedure scope.** Both are available: the procedure's
  **Cache Configuration** section caches the whole response, and a **Cache
  Block** caches only the steps it encloses. Procedure scope is simpler and
  needs no boundary review, but it is correct only when nothing in the procedure
  had to run per call. Block scope lets you draw the boundary where the data's
  audience actually changes rather than at the procedure edge; the cost is that
  the boundary becomes a thing reviewers must understand, because a step in the
  wrong place is silently skipped on every hit. Wider blocks are simpler and
  more dangerous; narrower blocks are safer and give up hit ratio.
- **Org cache vs session cache.** Org maximises reuse and gives 48 hours of
  headroom; session isolates per user, dies with the session, and tops out at
  8 hours. Decide from the payload's audience, never from the desired hit
  ratio — choosing on hit ratio is precisely how personalized data reaches a
  shared partition.
- **Version-bump invalidation vs event-driven purge.** A schema-version
  discriminator in the key is atomic with the deploy, cannot half-fail, and
  needs no runtime infrastructure; it wastes capacity while orphans age out. An
  event-driven purge is precise and immediate but introduces a subscriber that
  can lag, fail, or be missed. Default to the version bump for shape changes
  and keep the purge for value emergencies.
- **Readable keys vs hashed keys.** A readable, prefixed key is purgeable by
  prefix and debuggable in a log. A hash is compact and collision-resistant but
  opaque and unpurgeable. Under a 50-character alphanumeric constraint you will
  often need both — a readable prefix plus a hashed discriminator tail.
- **Cache vs Chainable.** These read as alternatives and are not. Caching
  reduces repeat cost; Chainable reduces single-execution cost. Choosing one
  when the symptom calls for the other produces a design that passes warm-cache
  testing and fails on every cold call.
- **Hit ratio vs cold-start survivability.** A high steady-state hit ratio can
  conceal a source system that cannot serve the full call volume. Eviction is
  normal operation, so the honest capacity question is not "what is our hit
  ratio" but "what happens when it is briefly zero."

## Where This Skill Stops

The cross-cutting cache taxonomy (metadata cache vs response cache vs Platform
Cache), the Data Mapper caching surface, and org-level partition setup belong
to `omnistudio/omnistudio-cache-strategies`. This skill owns Cache Block
design, key construction, partition choice, and invalidation for Integration
Procedures specifically.

Symptom-first performance triage across the platform is routed by
`standards/decision-trees/performance-tuning.md`. Read it before concluding
caching is the right lever — a cache layered over an unselective query or a
chatty callout pattern hides the defect instead of fixing it.

## Hygiene

- The cache scope is chosen and recorded before anything else: procedure-level
  Cache Configuration only where no step must run per call, a Cache Block
  otherwise.
- Every Cache Block's contents are reviewed against one question: must this be
  true on the ten-thousandth call as well as the first? Side-effecting steps
  live outside.
- The IP's cache duration is recorded in the design doc, because it is not
  documented as a field on `OmniIntegrationProcedure` at API 67.0 and therefore
  does not travel in a retrieve or appear in a source diff.
- Cache keys are produced by a single helper that enforces alphanumeric-only,
  ≤ 50 characters, and a fixed discriminator order — with a unit test asserting
  that two differently-ordered input maps produce the same key.
- `getPartition()` is null-checked at every call site, and no user-visible
  error originates in the cache layer.
- Serialized payload size is measured in bytes against the 100 KB ceiling, not
  estimated from record count.
- The schema-version discriminator is bumped in the same commit as any change
  to the cached payload's shape.
- The runtime (standard vs managed package) is recorded before any OmniStudio
  behavioural claim is cited, because published guidance splits between them.

## Official Sources Used

- **OmniIntegrationProcedure — Industries Common Resources Developer Guide (API 67.0)** —
  https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/meta_omniintegrationprocedure.htm
  — source for `responseCacheType` ("Response cache used for the integration
  procedure (session or Org)"), `isMetadataCacheDisabled` (default `false`),
  `requiredPermission`, `isActive`, `versionNumber`, `uniqueName`
  ("Type_SubType_Language_VersionNumber"), `omniProcessKey` ("Type_SubType"),
  and the **absence** of any documented TTL field on this metadata type — which
  this skill reads as "the cache duration is not round-trippable through IP
  metadata at 67.0," *not* as evidence about what the designer offers. Verified
  2026-08-14.
- **OmniDataTransform — Industries Common Resources Developer Guide (API 67.0)** —
  https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/meta_omnidatatransform.htm
  — used for the contrast that `responseCacheTtlMinutes` is documented on the
  Data Mapper type and not on the Integration Procedure type. Verified
  2026-08-14.
- **Master Integration Procedure Designer Elements — Trailhead** —
  https://trailhead.salesforce.com/content/learn/modules/omnistudio-integration-procedure-fundamentals/explore-integration-procedure-designer-elements
  — source for the four designer **Groups** and their verbatim descriptions
  (Cache Block: "Saves the output of the steps within it to a session or org
  cache for quick retrieval"; Conditional Block; Loop Block; Try-Catch Block),
  and for the standard action list used in the worked examples: Assert,
  Chatter, Decision Matrix, Delete, DocuSign Envelope, Email, Expression Set,
  HTTP, Integration Procedure, List, Remote, Response, Set Values, plus the
  Data Mapper extract/load/transform actions. Verified 2026-08-14.
- **Configuring Integration Procedures for Efficiency — Trailhead** —
  https://trailhead.salesforce.com/content/learn/modules/omnistudio-integration-procedure-fundamentals/configure-your-integration-procedure
  — source for the Procedure Configuration panel sections (Chainable
  Configuration, Queueable Chainable Limits, **Cache Configuration**, Test
  Configuration) and for the constraint "There can be only one Integration
  Procedure with the same Type and Sub Type active simultaneously." Load-bearing
  for this skill's central claim that procedure-level caching exists: the page's
  Cache Configuration section reads, verbatim, **"Use a cache to store
  frequently accessed, infrequently updated Integration Procedure data. This
  saves round trips to the database and improves performance."** The page does
  **not** name the individual fields inside that section. Re-fetched and
  re-verified 2026-08-14.
- **Optimizing Integration Procedure Performance — Trailhead** —
  https://trailhead.salesforce.com/content/learn/modules/advanced-features-of-omnistudio-integration-procedures/manage-long-running-integration-procedures
  — source for Chainable / Queueable Chainable / Chain On Step semantics ("if
  an Integration Procedure step exceeds the configured limits, the interim
  results are saved and the step continues in a new transaction") and for the
  threshold values, which correspond to the underlying Apex governor limits:
  100 SOQL / 10,000 ms CPU / 6 MB heap / 150 DML synchronous, and 200 SOQL /
  60,000 ms CPU / 12 MB heap for the queueable variant. Verified 2026-08-14.
- **Platform Cache Limits — Apex Developer Guide** —
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_platform_cache_limits.htm
  — source for maximum key size 50 characters; TTL minimum 300 s and maxima
  28,800 s (session) / 172,800 s (org, default 86,400 s); maximum size of a
  single cached item 100 KB; minimum partition size 1 MB; maximum local cache
  per partition per request 500 KB (session) / 1,000 KB (org). Verified
  2026-08-14.
- **Platform Cache Considerations — Apex Developer Guide** —
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_platform_cache_limitations.htm
  — source for "Cache isn't persisted. There's no guarantee against data
  loss.", "Some or all cache is invalidated when you modify an Apex class in
  your org.", "Data in the cache isn't encrypted.", "Cache misses can happen.
  We recommend constructing your code to consider a case where previously
  cached items aren't found.", and the session-cache/Flow restriction.
  Verified 2026-08-14.
- **Cache.Partition class — Apex Reference Guide** —
  https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_cache_Partition.htm
  — source for the `put(key, value)` key contract: non-null, alphanumeric
  characters only, `Cache.InvalidParamException` on validation failure.
  Verified 2026-08-14.
- **Store and Retrieve Values from the Org Cache — Apex Developer Guide** —
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_platform_cache_org_examples.htm
  — source for the fully qualified key format `namespace.partition.key`, the
  `local.` prefix, and `getPartition('myNs.myPartition')`. Verified 2026-08-14.
- **Salesforce Well-Architected — Performant** —
  https://architect.salesforce.com/docs/architect/well-architected/performant/performant
  — framing for the Performant and Scalable pillar notes above.

### Sources deliberately not used

The Salesforce Help articles on OmniStudio caching
(`os_cache_for_dataraptors_and_integration_procedures_*`, including the
separate "(Managed Package)" variants) and `sf.os_configure_an_integration_procedure`
are the canonical prose for this topic. `help.salesforce.com` renders no article
text to a document fetcher, so nothing from them is quoted. That is why the
individual field labels inside the IP's Cache Configuration section —
reportedly **Platform Cache Type** and **Time to Live in Minutes** — are marked
`<!-- UNVERIFIED -->` in `SKILL.md` rather than asserted. The section's
existence and its description come from Trailhead and are not in doubt; only
the labels are. Community claims about designer preview cache flags,
`ConnectApi` cache-clearing methods, and named Vlocity-era cache partitions
appear in the wider literature but could not be verified against a
Salesforce-published source; where they are mentioned in this package they are
marked inline with `<!-- UNVERIFIED -->` rather than stated as fact.
