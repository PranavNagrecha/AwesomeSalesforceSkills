# LLM Anti-Patterns — IP Cacheable

Mistakes AI coding assistants reliably make when asked to cache an Integration
Procedure. Each entry names the wrong output, the mechanism that produces it,
the corrected version, and a check that runs mechanically.

OmniStudio is high-risk terrain for a language model: most public writing about
it describes the Vlocity managed package rather than the standard runtime, and
its metadata vocabulary is irregular enough that generation smooths it into
plausible non-existent names. Establish the runtime before accepting any
OmniStudio symbol.

---

## Anti-Pattern 1: Concluding A Designer Feature Is Absent Because The Metadata Type Omits It

This one is worth reading even if you never touch OmniStudio, because the
reasoning error generalises across the whole platform — and because an earlier
version of *this file* committed it, and taught it as fact.

**What the LLM generates:** two answers that look opposite and share one root.

*Fabrication.* Invented metadata for a setting the model assumes must exist:

```xml
<!-- WRONG — none of these fields exist on OmniIntegrationProcedure -->
<isCacheable>true</isCacheable>
<cacheEnabled>true</cacheEnabled>
<cacheTTL>3600</cacheTTL>
<responseCacheTtlMinutes>60</responseCacheTtlMinutes>
```

*Over-correction.* Having checked the metadata reference and found no TTL
field, the model announces that the **designer** has no procedure-level cache
setting at all — "configure IP cache duration on the Cache Block, not as a
top-level procedure property." That is wrong. The Integration Procedure's
configuration panel has a **Cache Configuration** section, and Trailhead
describes it verbatim: *"Use a cache to store frequently accessed, infrequently
updated Integration Procedure data. This saves round trips to the database and
improves performance."*

**Why it happens:** The fabrication is ordinary — "make this cacheable" maps
onto a boolean in nearly every framework the model has seen, and
`responseCacheTtlMinutes` is a real token borrowed across a type boundary from
`OmniDataTransform`.

The over-correction is subtler and more dangerous, because it *feels* like
rigour. The model checks an authoritative list, finds nothing, and treats the
absence as dispositive. But a metadata type enumerates what is **deployable as
metadata**, not what is **configurable in a designer**. Those two sets overlap;
they are not equal. The absence of a TTL field on `OmniIntegrationProcedure`
means the duration is not round-trippable through that type at API 67.0 — a
real, useful, narrow fact — and nothing whatsoever about the UI.

The failure mode compounds: the over-correction is stated with the confidence
earned by the verification step, so it survives review better than the
fabrication does.

**Correct pattern:**

```text
Two separate questions. Answer them from two separate sources.

1. Does the DESIGNER have this setting?
   Source: Trailhead unit / Salesforce Help for that designer.
   Answer here: YES. The IP configuration panel has a Cache
   Configuration section, alongside Chainable Configuration,
   Queueable Chainable Limits, and Test Configuration.

2. Is it deployable as a field on the METADATA TYPE?
   Source: Industries Common Resources Developer Guide, per API version.
   Answer here: PARTLY. At API 67.0 OmniIntegrationProcedure documents

       responseCacheType        "Response cache used for the integration
                                 procedure (session or Org)"
       isMetadataCacheDisabled  boolean, default false  (NEGATIVE name:
                                 false means metadata caching is ON)

   and NO TTL field. responseCacheTtlMinutes is real but belongs to
   OmniDataTransform.

Correct conclusion: the duration is set in the designer and is not
round-trippable through IP metadata at 67.0. Record it in the design
doc; verify it in the org.

Wrong conclusion: "there is no procedure-level cache setting."

Separately, the Cache Block element is a FINER-GRAINED alternative,
not the only mechanism:

    Cache Block        "Saves the output of the steps within it to a
                        session or org cache for quick retrieval"

    Procedure scope -> every step is a read, one audience, one
                       freshness contract.
    Block scope     -> some step must run per call, or parts of the
                       response have different audiences or TTLs.
```

**Detection hint:** Two checks, in this order.

1. Any metadata field name reaching an `OmniIntegrationProcedure` snippet gets
   regexed against the type's own field list in the Industries Common Resources
   Developer Guide for the target API version — and against the *right* type,
   since the most convincing wrong answers borrow a real field from a sibling.
   Absence there is proof the **field** does not exist.
2. Any sentence of the form "there is no *&lt;feature&gt;* in *&lt;designer&gt;*"
   whose only cited evidence is a metadata reference. Absence from a metadata
   type is not evidence about a UI. The claim needs a designer-facing source
   (Trailhead, Help, or a screenshot from the org) or it needs to be downgraded
   to "not deployable as metadata at API *&lt;n&gt;*."

---

## Anti-Pattern 2: Putting Side-Effecting Steps Inside The Cache Block

**What the LLM generates:** an IP where an audit write, a logging step, or a
Data Mapper Load sits inside the Cache Block alongside the reads — usually
because the model was asked to "add auditing" to an already-cached procedure
and appended the step to the existing structure.

**Why it happens:** The model reasons about the procedure as an ordered list of
steps, which is how it is presented in text. The Cache Block reads as a
grouping or organisational construct — like a folder — rather than as a control
structure that can skip its contents entirely. Nothing in the block's textual
representation signals "these steps may not execute." An LLM adding a step to a
list puts it where it logically belongs in the sequence, and inside the block
*is* where it logically belongs in the sequence.

**Correct pattern:**

```text
On a cache HIT, no step inside the block executes. That is the mechanism.

OUTSIDE the block, always:
    - DML of any kind (Data Mapper Load, Delete action)
    - audit and logging writes
    - correlation ids, timestamps, request ids
    - rate-limit and quota counters
    - consent capture
    - anything a regulator would ask you to produce per-transaction

INSIDE the block:
    - Data Mapper Extract / Transform
    - HTTP Action (GET only)
    - Remote Action that is a pure read
    - Decision Matrix / Expression Set evaluation over cached inputs

Review question: "must this be true on the ten-thousandth call as well
as the first?" If yes, it goes outside.
```

**Detection hint:** Statically checkable from the IP definition. Flag any Cache
Block containing a Data Mapper Load, a Delete action, a Chatter action, an
Email action, a DocuSign Envelope action, or an HTTP action with a non-GET
method. All are side-effecting; none belongs inside a cache boundary.

---

## Anti-Pattern 3: Redis-Style Cache Keys

**What the LLM generates:** the colon-delimited hierarchical key, because that
is what "cache key" means across the overwhelming majority of its training
data:

```apex
// DOES NOT RUN — Cache.InvalidParamException
String key = 'ip:Product_Catalog:v4:region=' + region + ':currency=' + currency;
```

**Why it happens:** Redis and Memcached conventions are so uniform across the
caching literature that a model treats colon-delimited keys as *the* way to
write a cache key rather than as one ecosystem's house style. Salesforce
Platform Cache is the outlier, and a strong uniform prior beats a rarely-stated
exception. The generated code is also syntactically flawless and semantically
sensible, so it survives review on plausibility.

There is an OmniStudio-specific aggravator: `omniProcessKey` has the form
`Type_SubType`, so the most natural prefix an assistant can reach for —
the procedure's own process key — contains an **underscore**, which is also
illegal.

**Correct pattern:**

```apex
// Alphanumeric only, <= 50 chars, fixed discriminator order,
// version discriminator preserved for prefix purging.
String prefix = 'productCatalogV4';                        // no underscore
String disc   = alnum(region) + alnum(currency);           // FIXED order
String key    = (prefix + disc).length() <= 50
              ? prefix + disc
              : prefix + String.valueOf(Math.abs(disc.hashCode()));
```

The rule, from the `Cache.Partition` class reference: a valid key must be
non-null and contain **alphanumeric characters only**; `put()` throws
`Cache.InvalidParamException` otherwise. **Maximum key size is 50 characters.**

**Detection hint:** Regex every value reaching a `Cache.*.put()` / `get()` /
`contains()` against `^[a-zA-Z0-9]{1,50}$`. Zero false positives — the
constraint is absolute. Add a unit test that builds the key from two
differently-ordered input maps and asserts equality, which catches the ordering
defect in the same pass.

---

## Anti-Pattern 4: Org Cache Because The Input Signature "Looks Unique"

**What the LLM generates:** `responseCacheType` = `Org` on a guest-reachable or
personalized IP, justified by the richness of the input map.

**Why it happens:** The model is optimising the objective it can see — hit
ratio — and org cache maximises it. The security property that makes this wrong
is not a property of the cache at all; it is a property of the *key*. If the
caller supplies the inputs the key is derived from, the caller chooses which
entry to read. That requires reasoning through an indirection rather than
recalling a fact, and it is exactly the step that gets skipped when the
surface-level answer is fluent. "Unique inputs" also *sounds* like a security
argument, which is what lets it pass review.

**Correct pattern:**

```text
An input signature is not a tenant key.

Ask: is the subject SERVER-resolved or CALLER-supplied?

    %UserId% resolved from the session        -> a subject
    an input-map value named "userId"         -> a parameter an
                                                 attacker chooses

Org cache is correct ONLY when the payload is identical for every
caller AND contains no PII. Platform Cache considerations state:
"Data in the cache isn't encrypted."

Everything else: session cache with a server-resolved subject,
or no cache. If only part of the payload is shared reference data,
use the Cache Block's block scoping to cache only that part.
```

**Detection hint:** `responseCacheType` = `Org` on an IP that (a) accepts a
contact id, account id, context id, or token as an input, or (b) is reachable
by a guest user, or (c) is placed on an Experience Cloud page. Any one is
enough to require written justification.

---

## Anti-Pattern 5: TTL Presented As The Whole Invalidation Story

**What the LLM generates:** "Set a 1-hour TTL and the cache refreshes itself" —
with no version discriminator and no purge path.

**Why it happens:** TTL genuinely *is* a complete answer in the caching model
most training data describes, where a cache fronts a source that drifts on its
own schedule and no specific change has to be visible at a specific time.
Salesforce breaks that model: a deploy activates a new version at a moment a
human chose, and that human expects the change live. The model has no reason to
know that the deploy exists.

**Correct pattern:**

```text
TTL is a staleness BOUND, not an invalidation MECHANISM.

Payload SHAPE changed (fields added/renamed):
    bump a schema-version discriminator in the key prefix.
    Atomic with the deploy. Cannot half-fail. No runtime hook.
    Orphans age out on their own TTL.

Wrong VALUE shipped and must go now:
    explicit, permission-gated purge of the affected keys.
    An incident path, not a release step.

Do NOT rely on: "some or all cache is invalidated when you modify
an Apex class in your org." Real, documented, and it does not fire
for the metadata-only deploys that are most of OmniStudio's change
traffic.
```

**Detection hint:** A cache design naming a TTL but no version discriminator
and no purge path. The question that exposes it: "a wrong value ships at 09:00
— what makes the fix visible before the TTL expires?" If the answer is "wait,"
there is no invalidation design.

---

## Anti-Pattern 6: Failing Hard On A Cache Miss

**What the LLM generates:** defensive code that treats a null from the cache as
an error condition:

```apex
// WRONG — a miss is normal operation, not a fault
Cache.OrgPartition p = Cache.Org.getPartition('local.OmniResponses');
Object v = p.get(key);
if (v == null) {
    throw new CacheException('Cache miss for key ' + key);
}
```

**Why it happens:** "Check the return value and handle the failure" is correct
defensive practice almost everywhere else, and a null return does look like a
failure signal. The model applies a sound general habit to the one case where
null is the expected, routine outcome. Two nulls compound the error: `get()`
returning null (a miss) and `getPartition()` returning null (no such partition,
or none allocated) are different events, and the second is likewise normal
rather than exceptional.

**Correct pattern:**

```apex
// Cache is an accelerator. A miss is a latency event.
Cache.OrgPartition p = Cache.Org.getPartition('local.OmniResponses');
Object v = (p == null) ? null : p.get(key);
if (v == null) {
    v = fetchLive();                       // errors here MAY surface
    if (p != null) { p.put(key, v, 3600); } // best-effort write
}
return v;
```

Three documented reasons a miss is routine: **"Cache isn't persisted. There's
no guarantee against data loss."**; **"some or all cache is invalidated when
you modify an Apex class in your org."**; and **"cache misses can happen. We
recommend constructing your code to consider a case where previously cached
items aren't found."** Partition allocation is also org configuration, not
deployable metadata — a partition present in the sandbox may be absent in
production.

**Detection hint:** Any `throw` whose trigger is a null from `get()` or
`getPartition()`. Any user-visible error message whose origin is the cache
layer. Any code path where a cache failure changes the *result* rather than the
*latency*.

---

## Anti-Pattern 7: Caching To Fix A Governor-Limit Breach

**What the LLM generates:** asked to fix an IP hitting SOQL or CPU limits, it
adds a Cache Block and declares the problem solved.

**Why it happens:** Both "slow" and "over the limit" present as performance
problems, and caching is the canonical performance remedy. The distinction the
model misses is *which execution* each lever helps. Caching helps the second
call onward; a governor limit is breached on the first. Warm-cache testing then
confirms the fix, because the test run is not the run that fails.

**Correct pattern:**

```text
Diagnose from the symptom:

  Warm calls slow                          -> Cache Block
  COLD call breaches SOQL/CPU/heap/DML     -> Chainable
  DML step immediately before an HTTP call -> Chain On Step
                                              (next step in its own
                                               transaction)
  Long-running, can be async               -> Queueable Chainable

Chainable thresholds are bounded by the underlying Apex limits:

  Chainable (sync)     : 100 SOQL, 10,000 ms CPU, 6 MB heap, 150 DML
  Queueable Chainable  : 200 SOQL, 60,000 ms CPU, 12 MB heap

"If an Integration Procedure step exceeds the configured limits, the
interim results are saved and the step continues in a new transaction."

They COMPOSE. Cache Block so warm calls skip the work; chainable so
the cold call survives. Neither substitutes for the other.
```

**Detection hint:** Any caching recommendation whose stated justification is a
governor-limit exception (`System.LimitException`, "Too many SOQL queries",
"Apex CPU time limit exceeded") rather than a latency measurement. Also flag
any performance test whose runs all execute against a warm cache.

---

## Anti-Pattern 8: Caching An Aggregate Response Without Sizing It

**What the LLM generates:** wrap the entire IP response — Data Mapper Extract
plus HTTP enrichment plus transformation — in one Cache Block, because that is
the whole of the expensive work.

**Why it happens:** The model correctly identifies the expensive operation and
applies the remedy to all of it. Payload size is invisible at generation time:
nothing in the prompt states how many records or how wide, so the 100 KB
ceiling never enters the reasoning. The failure is also invisible at runtime —
an oversized `put()` produces a subsequent miss, indistinguishable from an
expiry, with no error on either side.

**Correct pattern:**

```text
Platform Cache size ceilings:

  Maximum size of a single cached item (put) : 100 KB
  Max local cache per partition, per request : 500 KB   (session)
                                               1,000 KB (org)
  Minimum partition size                     : 1 MB

Cache the resolved DECISION, not the raw aggregate:
  - the resolved price, not the full rate-table response
  - the eligibility verdict, not the records it came from
  - a projected subset, not the wide payload

Measure, don't estimate:
  System.debug(JSON.serialize(payload).length());
Field width dominates record count.
```

**Detection hint:** Any Cache Block whose enclosed steps produce a
record-collection response, where no serialized size measurement exists. Ask
for the byte count; if nobody has it, the design is unverified.
