# LLM Anti-Patterns — OmniStudio Cache Strategies

Mistakes AI coding assistants reliably make when asked to configure or reason
about OmniStudio caching. Each entry names the wrong output, why the model
produces it, the corrected version, and a check that can be run mechanically.

OmniStudio is unusually bad terrain for language models: the majority of the
public writing about it describes the Vlocity managed package, so a model's
prior is anchored on names and behaviours that may not exist in the standard
runtime. Verify the runtime before accepting any OmniStudio symbol.

---

## Anti-Pattern 1: Cache Keys With Colons, Equals Signs, And Hyphens

**What the LLM generates:** the Redis idiom, because that is what "cache key"
means in almost all of its training data.

```apex
// DOES NOT RUN — throws Cache.InvalidParamException
String key = 'omni:catalog:v2:region=' + region + ':currency=' + currency;
Cache.Org.getPartition('local.OmniResponses').put(key, payload);
```

**Why it happens:** Colon-delimited hierarchical keys are the dominant
convention across Redis, Memcached, and every caching tutorial written for
those systems. The convention is so uniform that a model treats it as *the*
way to write a cache key rather than as one ecosystem's house style.
Salesforce Platform Cache is the outlier, and outliers lose to a strong prior.
The generated code is also syntactically perfect and semantically sensible,
so it reads as correct in review.

**Correct pattern:**

```apex
// Alphanumeric only. Max 50 characters. Version discriminator retained.
String key = 'omniCatalogV2'
           + region.replaceAll('[^a-zA-Z0-9]', '')
           + currency.replaceAll('[^a-zA-Z0-9]', '');
```

The rule, from the `Cache.Partition` class reference: a valid key must not be
null and must contain **alphanumeric characters only**; `put()` throws
`Cache.InvalidParamException` otherwise. Maximum key size is **50
characters**. The dots in the fully qualified form
`namespace.partition.key` are structural separators, not part of the key.

**Detection hint:** Mechanical. Regex every string literal or built value that
reaches a `Cache.*.put()` / `get()` / `contains()` call against
`^[a-zA-Z0-9]{1,50}$`. Any failure is a runtime exception waiting to happen,
and this check has no false positives — the constraint is absolute.

---

## Anti-Pattern 2: TTL Values Below The 5-Minute Floor

**What the LLM generates:** "Set Time to Live in Minutes to 2 for near-real-time
data," or an Apex `put(key, value, 60)` with a 60-*second* TTL.

**Why it happens:** The model is optimising the tradeoff it understands —
freshness versus hit ratio — and produces a number that is correct *as an
answer to that tradeoff*. It does not know the range is clamped, because the
clamp lives in a limits table rather than in the prose about caching strategy.
The answer is therefore well-reasoned and wrong, which is the hardest kind to
catch.

**Correct pattern:**

```text
Platform Cache TTL bounds (Apex Developer Guide, Platform Cache Limits):

  Session cache : min 300 s (5 min)   max 28,800 s  (8 hours)
  Org cache     : min 300 s (5 min)   max 172,800 s (48 hours)
                  default 86,400 s (24 hours)

OmniDataTransform.responseCacheTtlMinutes is expressed in MINUTES,
so its usable range is 5 .. 2880 (org) or 5 .. 480 (session).

If the freshness requirement is tighter than 5 minutes, the correct
design is NOT to cache. Write that conclusion down rather than
writing a smaller number into the field.
```

**Detection hint:** Any proposed TTL under 5 minutes, or over 48 hours, or a
session-cache TTL over 8 hours. Also flag any TTL expressed in seconds that is
being written into a field whose name ends in `Minutes` — the unit mismatch
between `responseCacheTtlMinutes` and Apex's seconds-based `put()` overload
produces 60×-off errors in both directions.

---

## Anti-Pattern 3: Inventing An OmniStudio Cache Property Name

**What the LLM generates:** confident, plausible, non-existent field names —
`cacheEnabled`, `isCacheable`, `cacheTTL`, `enableResponseCache`,
`cacheDurationMinutes` — usually inside a well-formed metadata snippet.

**Why it happens:** This is the highest-frequency OmniStudio failure and it
has a specific mechanism. OmniStudio's real names are irregular
(`responseCacheTtlMinutes`, `isMetadataCacheDisabled`,
`fieldLevelSecurityEnabled`, `synchronousProcessThreshold`), and irregular
vocabularies are exactly what autoregressive generation smooths out. The model
regularises toward the Salesforce-idiomatic shape it has seen ten thousand
times — `is<Thing>Enabled`, `<thing>Enabled` — and emits it with full
confidence because the *shape* is right even though the *token* is invented.
It is not hedging, because nothing in the generation feels uncertain.

**Correct pattern — the fields that actually exist, API 67.0:**

```text
OmniDataTransform (Data Mapper):
    responseCacheType          string   "org cache or session cache"
    responseCacheTtlMinutes    double   minutes the response stays cached
    fieldLevelSecurityEnabled  boolean  check user field-level access
    requiredPermission         string   custom permissions to execute
    synchronousProcessThreshold double  input records processed sync
    active / versionNumber / type (extract | transform | load)

OmniIntegrationProcedure:
    responseCacheType          string   "session or Org"
    isMetadataCacheDisabled    boolean  default false  (NOTE: negative name)
    requiredPermission         string
    isActive / versionNumber / uniqueName / omniProcessKey

    -- there is NO documented TTL field on OmniIntegrationProcedure.
       That means the IP's cache duration does not round-trip through
       metadata at 67.0. It does NOT mean the designer lacks a
       procedure-level cache setting -- the IP configuration panel has
       a Cache Configuration section. --

OmniScript:
    responseCacheType, isMetadataCacheDisabled, requiredPermission,
    isActive, versionNumber, propertySetConfig
```

**Detection hint:** Every OmniStudio metadata field name is enumerated in the
Industries Common Resources Developer Guide, per type, per API version. That
makes absence from the list *proof the field does not exist*, not merely
absence of evidence — the same property that makes the `ConnectApi` namespace
list authoritative. Check the name against the type's field list before
accepting it. A retrieve of the component from the org settles it in seconds.

**Where that inference stops.** A metadata type enumerates what is *deployable
as metadata*, not what is *configurable in a designer*. Absence of a field is
proof about the metadata surface and says nothing about the UI — a designer
setting that does not round-trip through metadata is a normal state of affairs,
not a contradiction. Over-reading the enumeration into "the feature does not
exist" is a distinct anti-pattern, and it is more convincing than a plain
fabrication because it arrives wearing the authority of the verification step.
See Anti-Pattern 1 in
`omnistudio/integration-procedure-cacheable-patterns/references/llm-anti-patterns.md`.

---

## Anti-Pattern 4: Answering With Managed-Package Behaviour For A Standard-Runtime Org

**What the LLM generates:** instructions referencing `vlocity_cmt`-prefixed
settings, the old activation/compilation/deployment cycle, or Vlocity-era
partition names, presented as current fact with no runtime caveat.

**Why it happens:** Volume. OmniStudio existed as the Vlocity managed package
for years before the standard runtime, so the overwhelming majority of blog
posts, Stack Exchange answers, course notes, and community documentation
describe the package. The standard runtime's corpus is thin by comparison and
much of it is recent. A model weighting by frequency will answer from the
package unless something forces it not to. Salesforce Help's own parallel
articles — distinguished only by a "(Managed Package)" suffix — make this
worse, because both variants are legitimate documentation and neither is
obviously stale.

**Correct pattern:**

```text
Establish the runtime BEFORE answering. OmniStudioSettings:

    enableStandardOmniStudioRuntime   API 65.0+  standard runtime on/off
    enableOaForCore                   64.0+  standard designer experience
                                      (namespaces: omnistudio, vlocity_cmt,
                                       vlocity_ins, vlocity_ps)
    enableOmniStudioMetadata          Metadata/Tooling API access —
                                      IRREVERSIBLE once enabled
    enableOmniStudioDrVersion         Data Mapper versioning (opt-in)

Then answer from the metadata reference for that runtime, not from prose.
If the runtime is unknown, say so and give the answer for both, labelled.
```

**Detection hint:** Any `vlocity_*` symbol, any reference to a separate
package installation, or any activation flow described as compile-and-deploy,
in an answer that did not first establish the runtime. Also flag the reverse
error: asserting a standard-runtime-only field to an org still on the package.

---

## Anti-Pattern 5: Org Cache For Anything The Caller Can Key

**What the LLM generates:** org cache as the default, because "org cache is
shared, and sharing is what caches are for" — including for personalized or
guest-reachable read paths.

**Why it happens:** Two reinforcing pressures. The model is optimising hit
ratio, and org cache maximises it. And the security property that makes org
cache wrong here is not a property of the *cache* at all — it is a property of
the *key*: if the caller supplies the inputs the key is derived from, the
caller chooses which entry to read. That is an indirection the model has to
reason through rather than recall, and it is exactly the kind of step that
gets skipped when the surface-level answer is fluent.

**Correct pattern:**

```text
Decide from the payload, in this order:

1. Does the response differ by who is asking?          -> not org cache
2. Is the subject SERVER-resolved (UserInfo, ownership,
   sharing) or CALLER-supplied (a form field, a URL
   parameter, an input map value)?                     -> caller-supplied
                                                          means the caller
                                                          picks the key
3. Does it contain PII? Platform Cache documentation:
   "Data in the cache isn't encrypted."                -> not a shared
                                                          partition

Org cache is correct only for payloads identical for every caller
AND free of PII. Everything else is session cache or no cache.
```

**Detection hint:** `responseCacheType` = `Org` on any component that (a) takes
a contact id, account id, context id, or session token as an input, or (b) is
reachable by a guest user, or (c) is placed on an Experience Cloud page. Any
one of the three is enough to require justification.

---

## Anti-Pattern 6: Treating TTL As The Invalidation Design

**What the LLM generates:** "Set a 1-hour TTL and the cache will refresh
itself" — TTL presented as a complete answer to staleness.

**Why it happens:** TTL genuinely *is* a complete answer in the simple caching
model most training data describes, where the cache fronts a source of truth
that changes on its own schedule and nobody needs a specific change to be
visible at a specific time. Salesforce breaks that model: a deploy activates a
new component version at a moment a human chose, and that human expects the
change to be live.

**Correct pattern:**

```text
TTL is a staleness BOUND. It is not an invalidation MECHANISM.

Routine releases : bump a version discriminator inside the cache key.
                   Atomic with the deploy, no runtime hook, cannot
                   half-fail, old entries age out on their own TTL.

Incidents        : an explicit, permission-gated purge of the affected
                   keys. Exercised rarely; document who may run it.

Do NOT rely on: "some or all cache is invalidated when you modify an
Apex class in your org." It is real, it is documented, and it does not
fire for the metadata-only deploys that are most of OmniStudio's
change traffic.
```

**Detection hint:** A cache design that names a TTL but no version
discriminator and no purge path. Ask the question that exposes it: "a wrong
value ships to production at 09:00 — what makes the fix visible before the
TTL expires?" If the answer is "wait," there is no invalidation design.

---

## Anti-Pattern 7: Caching The Large Convenient Thing

**What the LLM generates:** cache the whole aggregate response — the full
catalog, the complete record set — because that is the call that was slow.

**Why it happens:** The model correctly identifies the expensive operation and
then applies the obvious remedy to the whole of it. Sizing is invisible at
generation time: nothing in the prompt says how big the payload is, so the
100 KB ceiling never enters the reasoning.

**Correct pattern:**

```text
Platform Cache size ceilings:

  Maximum size of a single cached item (put)   : 100 KB
  Max local cache per partition, per request   : 500 KB   (session)
                                                 1,000 KB (org)
  Minimum partition size                       : 1 MB

Cache the expensive SMALL thing:
  - a resolved rate or price, not the rate table's full response
  - a permission or eligibility decision, not the records it was
    derived from
  - a compact projection, not the wide payload

An oversized put does not raise an error on the subsequent read. It
produces a miss that is indistinguishable from an expiry, which is why
this bug survives testing.
```

**Detection hint:** Any cached value whose serialized size was never measured.
Serialize the representative payload and check its length before shipping the
cache; record-count intuition is unreliable because field width dominates.

---

## Anti-Pattern 8: Caching A Write Path

**What the LLM generates:** enabling cache on a Data Mapper Load, or wrapping
a DML or mutating HTTP step in a cache, on the reasoning that cache makes
things faster and this thing is slow.

**Why it happens:** Over-generalisation of "cache = performance." The model
applies it uniformly across step types because the OmniStudio configuration
surface presents cache as a per-component option without distinguishing read
from write semantics — nothing at the point of configuration says "reads
only."

**Correct pattern:**

```text
Cache reads. Never cache a mutation.

OmniDataTransform.type distinguishes them explicitly:
    extract   (SOQL)      -> cacheable
    transform             -> cacheable (pure function of its input)
    load      (DML)       -> NOT cacheable

The correct lever for a slow Load is elsewhere entirely:
    synchronousProcessThreshold  - input records processed synchronously;
                                   above this it uses a batch job
    processSuperBulk             - spread upsert across multiple Apex
                                   batch jobs
    rollbackOnError              - do not commit partial work on error

Duplicate-write protection is an idempotency-key problem on the write
path, not a cache-entry problem.
```

**Detection hint:** `responseCacheType` or `responseCacheTtlMinutes` set on an
`OmniDataTransform` whose `type` is `Load`. Also flag a Cache Block in an
Integration Procedure that encloses any DML or non-GET HTTP action.
