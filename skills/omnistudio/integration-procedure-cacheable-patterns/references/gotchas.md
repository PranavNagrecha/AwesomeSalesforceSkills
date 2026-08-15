# IP Cacheable — Gotchas

Behaviour that produces a silent no-op, a wrong answer, or a security finding
when caching an Integration Procedure. Numbers are from the Apex Developer
Guide's Platform Cache limits table; element and field names are from the
Integration Procedure Trailhead modules and the `OmniIntegrationProcedure`
metadata type at API 67.0.

---

## 1. Steps Inside A Cache Block Do Not Run On A Hit — Including The Ones You Needed

**What happens:** An audit write, a rate-limit increment, a permission check,
or a per-call timestamp placed inside a Cache Block executes once per cache
population and then not again for the whole TTL window.

**When it occurs:** Whenever a step is added to an existing IP and dropped into
the nearest block without asking whether it is a read. The Cache Block "saves
the output of the steps within it" — skipping those steps on a hit is the
mechanism, not a bug.

**Why it survives testing:** The first test run populates the cache and the
side effect fires. The tester sees the audit row, the counter increment, the
log line. Only at production call volumes does the ratio become visible, and
by then the gap is historical and unrecoverable.

**How to avoid:** Apply one question to every step in a Cache Block — "must
this be true on the ten-thousandth call as well as the first?" If yes, it goes
outside. In practice that always includes: DML of any kind, audit and logging
writes, correlation ids and timestamps, rate limiting, consent capture, and
anything a regulator would ask you to produce per-transaction.

---

## 2. Cache Keys Must Be Alphanumeric And ≤ 50 Characters

**What happens:** `Cache.InvalidParamException` at runtime, from a key that
passed review because it looked exactly like every cache key the reviewer has
ever seen.

**When it occurs:** Any Redis/Memcached-style key —
`ip:Product_Catalog:v4:region=NA`. Colons, equals signs, hyphens, **and
underscores** are all illegal inside the key segment. Underscores catch people
out specifically because `omniProcessKey` (`Type_SubType`) contains one, so
the natural move — use the process key as the prefix — produces an illegal key.

**The rule:** a valid key must be non-null and contain **alphanumeric
characters only**; `put(key, value)` throws `Cache.InvalidParamException`
otherwise. **Maximum key size is 50 characters.** The dots in the fully
qualified form `namespace.partition.key` are structural separators between
namespace, partition, and key — they do not license dots inside the key.

**How to avoid:** One helper, one convention, camelCase, no separators, applied
at every call site by construction rather than by discipline. Strip the
underscore when deriving a prefix from `omniProcessKey`.

---

## 3. Key Ordering Is Not Guaranteed By The Input Map

**What happens:** Hit ratio sits at half of what the input cardinality predicts,
and nobody can see why. Two callers requesting the same thing produce two
entries.

**When it occurs:** The key is built by iterating a `Map<String, Object>`. Apex
`Map` iteration order is not part of its contract, so `regionNAcurrencyUSD` and
`currencyUSDregionNA` both get written for logically identical requests.

**How to avoid:** Fix the discriminator order explicitly in the key helper — a
literal sequence of named inputs, not a loop over a map. Where the input set is
genuinely dynamic, sort the keys before concatenating. Then assert it: a unit
test that builds the key from two differently-ordered maps and asserts equality
costs three lines and catches the whole class.

---

## 4. `getPartition()` Returning Null Is Normal, Not Exceptional

**What happens:** A NullPointerException in production from a cache helper,
because a partition that existed in the sandbox does not exist — or has no
capacity — in the target org.

**When it occurs:** Partition allocation is org configuration, not deployable
metadata that travels with your package. A partition is also a finite
allocation with a **1 MB minimum**; capacity can be reduced or reallocated by
an admin at any time without a deploy.

**How to avoid:** Null-check `getPartition()` at every call site and fall
through to the live path. The stronger framing: no code path in a cached IP may
raise a user-visible error that originates in the cache layer. A cache miss, a
missing partition, and a full partition are all latency events. Building the
read path so this is structurally true — rather than remembering to
null-check — is what separates a cache from a dependency.

---

## 5. The IP Metadata Type Has A Cache Type But No TTL Field — Which Is Not The Same As Having No Setting

**What happens:** You go looking for the IP equivalent of a Data Mapper's
`responseCacheTtlMinutes` in the metadata reference and there isn't one. The
tempting next step — concluding the designer therefore has no procedure-level
cache configuration — is wrong, and is the mistake this gotcha exists to stop.

**When it occurs:** Porting a Data Mapper cache design onto an Integration
Procedure. The documented caching surface of `OmniIntegrationProcedure` at API
67.0 is exactly two fields:

- `responseCacheType` — "Response cache used for the integration procedure
  (session or Org)"
- `isMetadataCacheDisabled` — "Indicates whether metadata cache for the
  integration procedure is disabled. Default: false."

By contrast `OmniDataTransform` documents both `responseCacheType` **and**
`responseCacheTtlMinutes`.

**What that actually means:** the cache **duration is not round-trippable
through IP metadata** at API 67.0. It does not travel in a retrieve, it will
not show up in a source diff, and it cannot be asserted by a metadata-based
deployment check. That is a real constraint with real consequences for source
control — and it is the whole of the constraint.

The IP configuration panel does have a **Cache Configuration** section, sitting
alongside Chainable Configuration, Queueable Chainable Limits, and Test
Configuration. Trailhead's description, verbatim: *"Use a cache to store
frequently accessed, infrequently updated Integration Procedure data. This
saves round trips to the database and improves performance."*

**How to avoid:** Choose the scope on the shape of the procedure, not on what
the metadata type happens to expose. A procedure whose every step is a read,
with one audience and one freshness contract, can use procedure-level Cache
Configuration. A procedure with any per-call step — an audit write, a
correlation id, a mutation — needs a **Cache Block** with that step outside it.
Either way, record the TTL in the design doc rather than expecting to recover
it from a retrieve, and verify it in the org before a release.

And do not confuse the two metadata fields above: `isMetadataCacheDisabled`
governs the component *definition* and defaults to `false` (so metadata caching
is already **on**); flipping it to `true` disables caching and will not change
what a warm read returns.

---

## 6. Org Cache Is Addressed By A Key, And On A Guest Page The Caller Owns The Key

**What happens:** Two guests submitting the same form values receive the same
cached payload. The second one is reading the first one's data.

**When it occurs:** `responseCacheType` = `Org` on any IP reachable by an
unauthenticated or portal audience, keyed on values from the input map. The
reasoning that gets you there — "the input signature is unique enough to act as
a per-user key" — is wrong in a specific way: on a guest page the inputs are
attacker-controlled, so the key is attacker-controlled, so this is an
enumeration primitive rather than a collision to be waited for.

**Compounding fact:** Platform Cache considerations state plainly that **"data
in the cache isn't encrypted."** Shield Platform Encryption protects the field
in the record; it does not follow the value into a cache entry.

**How to avoid:** No org-segment cache on guest, portal, or PII Integration
Procedures. Use session cache with a **server-resolved** subject (`%UserId%`
from the session — never an input-map value called `userId`), or no cache. If
part of the payload genuinely is shared reference data, use the Cache Block's
block scoping to cache only that part.

---

## 7. Session Cache Dies With The Session, And Tops Out At 8 Hours

**What happens:** A session-scoped cache is treated as short-term storage and
loses its contents at logout, at session timeout, or when the browser session
ends.

**When it occurs:** By design. Session cache "expires when its specified
time-to-live value is reached or when the user session expires, whichever comes
first." Maximum TTL is **28,800 s (8 hours)**, against org cache's 172,800 s
(48 hours).

**How to avoid:** Do not use session cache for anything that must survive a
logout — that is a persistence requirement, not a caching one. See
`omnistudio/omniscript-session-state`. Note also the documented restriction on
accessing session cache from Salesforce Flow: if a Flow sits in your warming or
invalidation path, verify it can reach the partition before you design around
it.

---

## 8. TTL Below 5 Minutes Is Below The Platform Floor

**What happens:** A TTL of 1, 2, or 3 minutes is configured and does not behave
as written.

**When it occurs:** The reasoning "shorter TTL is safer" produces a number
outside the platform's range. Platform Cache enforces a **minimum TTL of 300
seconds (5 minutes)** for both org and session cache. Maxima are 48 hours (org,
default 24 hours) and 8 hours (session).

**How to avoid:** If the freshness contract is tighter than 5 minutes, the
correct output is a written decision **not to cache** — not a smaller number.
Record it, so the next person does not re-litigate it.

---

## 9. A Cached Payload Over 100 KB Silently Does Not Persist

**What happens:** The put appears to succeed. The next read is a miss. Hit ratio
sits near zero with no error anywhere.

**When it occurs:** **Maximum size of a single cached item** for `put()` methods
is **100 KB**. IP responses that aggregate a Data Mapper Extract with an HTTP
enrichment cross that line easily — a few hundred records with a dozen fields
each will do it, and field width matters more than record count.

There is a second ceiling that catches the composite case: **maximum local
cache size for a partition, per request** is 500 KB (session) / 1,000 KB (org).
A transaction that reads many legal entries can still exhaust it.

**How to avoid:** Cache the resolved decision, not the raw aggregate — and
measure the serialized payload in bytes rather than estimating from record
count. `JSON.serialize(payload).length()` in an anonymous block settles it.

---

## 10. Cache Is Not Persisted, And An Apex Deploy May Clear It

**What happens:** Hit ratio drops to zero at an unpredictable moment, then
recovers over the following minutes. No OmniStudio configuration changed.

**When it occurs:** Two documented behaviours outside your control. **"Cache
isn't persisted. There's no guarantee against data loss."** — eviction under
memory pressure is normal operation. And **"some or all cache is invalidated
when you modify an Apex class in your org."** — any deploy touching Apex,
including one unrelated to this path, may clear entries.

**How to avoid:** Capacity-plan for the **cold-start load that follows a full
eviction**, not for the steady-state hit ratio you measured once. If the source
system behind the IP cannot survive every caller missing simultaneously, the
cache is load-bearing and the real fix is upstream. Also: do not build a
release process on the Apex-deploy invalidation — it does not fire for the
metadata-only deploys that are most of OmniStudio's change traffic.

---

## 11. Caching Does Not Fix A Cold-Path Governor Limit

**What happens:** An IP that breaches SOQL, CPU, heap, or DML limits is
"fixed" by adding a Cache Block. It passes in testing, where the cache is warm,
and fails in production on every cold call.

**When it occurs:** Conflating two orthogonal levers. Caching reduces *repeat*
cost; **Chainable** reduces *single-execution* cost by splitting one
transaction into several — "if an Integration Procedure step exceeds the
configured limits, the interim results are saved and the step continues in a
new transaction."

The chainable thresholds are bounded by the underlying Apex governor limits:
synchronous — 100 SOQL queries, 10,000 ms CPU, 6 MB heap, 150 DML statements;
Queueable Chainable — 200 SOQL queries, 60,000 ms CPU, 12 MB heap.

**How to avoid:** Diagnose from the symptom. Slow *warm* calls → Cache Block.
Cold call breaching a limit → Chainable. A DML step immediately preceding an
HTTP callout → **Chain On Step**, which forces the next step into its own
transaction. Long-running work that can be asynchronous → Queueable Chainable.
They compose; they do not substitute.

---

## 12. Only One IP Per Type/SubType Can Be Active — Which Is Why Your Key Prefix Is Stable

**What happens:** Activating a new version deactivates the previously active
one, and any cache prefix derived from Type/SubType now points at entries
produced by different code.

**When it occurs:** By design: **"There can be only one Integration Procedure
with the same Type and Sub Type active simultaneously."** The identity fields
encode this — `omniProcessKey` is the "Type_SubType" value and `uniqueName` is
"Type_SubType_Language_VersionNumber".

**How to avoid:** Use Type/SubType as the stable, purgeable *prefix* and carry
your own schema-version discriminator after it — bumped when the cached
payload's **shape** changes, which is not the same event as an IP version
increment. Most version bumps do not change the payload shape; the ones that do
must invalidate, and only you know which is which. Deriving the discriminator
from `versionNumber` automatically evicts the entire cache on every release,
which is correctness-safe and performance-expensive.
