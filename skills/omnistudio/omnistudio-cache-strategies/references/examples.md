# Examples — OmniStudio Cache Strategies

Every configuration name below is quoted from the metadata reference for the
**standard runtime** (`OmniDataTransform`, `OmniIntegrationProcedure`,
`OmniScript` — Industries Common Resources Developer Guide, API 67.0) or from
the Platform Cache section of the Apex Developer Guide. Where a name comes
from the managed package instead, it is labelled inline.

---

## Example 0: Know Which Of The Three Caches You Are Talking About

**Context:** Almost every "OmniStudio cache" conversation goes wrong in the
first sentence because three unrelated caches share the word.

**Problem:** A team enabled "cache" on a Data Mapper, saw no latency change,
and concluded caching was broken. They had been measuring the *metadata*
cache path while configuring the *response* cache.

**Solution — name the layer before you touch anything:**

| Layer | What it stores | Where you configure it | Metadata field |
|---|---|---|---|
| **Component metadata cache** | The compiled definition of the IP / OmniScript itself, so the runtime does not re-read the definition per call | Per component | `isMetadataCacheDisabled` on `OmniIntegrationProcedure` and `OmniScript` (default `false`, i.e. metadata caching is **on**) |
| **Response cache** | The *output payload* of a Data Mapper, or of the steps inside an IP Cache Block | Data Mapper **Options** tab; IP **Cache Block** element | `responseCacheType` (`session` or `Org`) on `OmniIntegrationProcedure`, `OmniScript`, `OmniDataTransform`; `responseCacheTtlMinutes` on `OmniDataTransform` |
| **Platform Cache** | The underlying org-wide key/value store both of the above sit on | Setup → Platform Cache (partition allocation) | n/a — see `Cache.Org` / `Cache.Session` in Apex |

Only the middle row changes what a user waits for on a warm read. The top
row changes cold-start cost. The bottom row is the substrate: if it has no
capacity, the middle row cannot function.

**Why it works:** Once the layer is named, the diagnostic question becomes
answerable. "Response times did not improve" is a response-cache question.
"The first call after deploy is slow" is a metadata-cache question. "Nothing
is being cached at all" is usually a partition-allocation question.

---

## Example 1: Reference-Data Data Mapper — The Full Configuration

**Context:** A `GetCountryStateCodes` Data Mapper Extract feeds three
OmniScripts and two FlexCards. The underlying custom metadata changes maybe
twice a year. It is called on every script load.

**Problem:** The team set "Time to Live in Minutes" to `2` because "shorter is
safer." Two minutes is below the Platform Cache floor.

**Solution:**

Data Mapper **Options** tab (labels quoted from the Omnistudio Data Mappers
Trailhead module):

| Option | Value | Why |
|---|---|---|
| **Platform Cache Type** | `Org Cache` | The result is identical for every user. No user identity is in the payload. |
| **Time to Live in Minutes** | `60` | Above the 5-minute Platform Cache minimum, well under the 48-hour org-cache maximum. Reference data tolerates an hour. |

Corresponding metadata (`OmniDataTransform`):

```xml
<OmniDataTransform xmlns="http://soap.sforce.com/2006/04/metadata">
    <name>GetCountryStateCodes</name>
    <type>Extract</type>
    <active>true</active>
    <versionNumber>3.0</versionNumber>
    <responseCacheType>org</responseCacheType>
    <responseCacheTtlMinutes>60</responseCacheTtlMinutes>
    <fieldLevelSecurityEnabled>true</fieldLevelSecurityEnabled>
</OmniDataTransform>
```

**The TTL floor that broke the original config:** Platform Cache enforces a
minimum TTL of **300 seconds (5 minutes)** for both org cache and session
cache. `responseCacheTtlMinutes` is expressed in minutes, so any value below
`5` is below the platform floor. Do not author a TTL of 1, 2, or 3 minutes and
expect it to mean what it says.

The maxima matter at the other end: **48 hours (172,800 s)** for org cache,
**8 hours (28,800 s)** for session cache. A "one week" TTL is not expressible.

**Why it works:** The TTL is inside the range the platform can actually
honour, the cache type matches the data's audience, and FLS stays enforced on
the cold path.

---

## Example 2: The Cache That Silently Did Nothing — Partition Allocation

**Context:** Cache configured correctly on six Data Mappers. Zero measurable
change in p95. No errors in the debug log.

**Problem:** Platform Cache partitions have an explicit capacity allocation,
and **the minimum partition size is 1 MB**. A partition with no allocated
capacity has nowhere to put entries. The OmniStudio configuration is valid;
the substrate is empty.

**Solution — verify allocation before you tune anything:**

1. Setup → **Platform Cache**. Confirm the org has purchased/trial capacity
   and that the partition backing OmniStudio responses has a non-zero
   allocation.
2. Confirm allocation is split deliberately between Org Cache and Session
   Cache — they are separate allocations within a partition, not one pool.
3. Re-run the read path twice and compare. A warm second read that is
   indistinguishable from the first is still a miss.

<!-- UNVERIFIED: multiple third-party sources (Apex Hours, Packt "Optimizing
Salesforce Industries Solutions on the Vlocity OmniStudio Platform") state the
OmniStudio partitions are named `VlocityAPIResponse` (response data) and
`VlocityMetadata` (component metadata) and that both default to zero
allocation. I could not confirm the partition names or the zero default
against any Salesforce-published doc — the relevant Salesforce Help article
("Cache for Omnistudio Data Mappers and Integration Procedures") renders no
article text to a fetcher. The `Vlocity*` prefix strongly suggests these are
managed-package partition names; I could not determine the standard-runtime
equivalents. Treat the names as a starting point for a Setup lookup, not as
a fact to quote. -->

**Why it works:** It separates "configured" from "operative." Everything
downstream — TTL tuning, key design, hit-ratio monitoring — is meaningless
while allocation is zero, and none of it produces an error that would tell
you so.

---

## Example 3: Cache Key Characters — The Failure Models Reproduce Most Often

**Context:** A developer writes an Apex helper to warm and purge the cache
that an OmniStudio read path depends on.

**Problem — the version an assistant will hand you:**

```apex
// WRONG — throws Cache.InvalidParamException at runtime
String key = 'ip:PricingMatrix:v3:sku=' + sku + ':region=' + region;
Cache.Org.getPartition('local.OmniResponses').put(key, payload);
```

Two independent defects:

1. **Platform Cache keys must contain alphanumeric characters only.** The
   `put(key, value)` method throws `Cache.InvalidParamException` when the key
   fails validation. `:` and `=` are not alphanumeric.
2. **Maximum key size is 50 characters.** The string literals above account for
   32 characters (`'ip:PricingMatrix:v3:sku='` is 24, `':region='` is 8) before
   a single `sku` or `region` value is concatenated in — leaving 18 characters
   for both values combined. A five-character SKU and a two-character region
   fit; realistic values do not.

**Solution:**

```apex
// RIGHT — alphanumeric only, length-bounded, still purgeable by prefix
// Convention: <ipname><schemaVersion><discriminators>, camelCase, no separators.
String key = 'pricingMatrixV3'
           + sku.replaceAll('[^a-zA-Z0-9]', '')
           + region.replaceAll('[^a-zA-Z0-9]', '');
if (key.length() > 50) {
    // Truncating loses uniqueness. Hash the tail instead, then re-check.
    key = key.substring(0, 34) + String.valueOf(Math.abs(key.hashCode()));
}
Cache.OrgPartition part = Cache.Org.getPartition('local.OmniResponses');
if (part != null) {
    part.put(key, payload, 3600);   // TTL seconds, 300 min / 172800 max
}
```

Notes on the fixed version:

- `local.` resolves to the namespace of the org the code is running in, and
  is equivalent to naming that namespace explicitly. Use it so the helper
  survives being packaged.
- The fully qualified key format is `namespace.partition.key`. Omit the
  `namespace.partition.` prefix only when you intend the default partition.
- `getPartition()` is null-checked because a missing partition is a normal
  runtime state, not an exceptional one.

**Why it works:** The key is legal, bounded, and still carries a readable
version discriminator (`V3`) you can bump to invalidate an entire schema
generation without enumerating keys.

---

## Example 4: Choosing Org Cache vs Session Cache From The Payload, Not The Latency

**Context:** Two Data Mappers on the same Experience Cloud page.

| Data Mapper | Payload | Correct `responseCacheType` |
|---|---|---|
| `GetProductCatalog` | Same rows for every visitor. No identity in the response. | `org` |
| `GetMyOpenApplications` | Filtered to the running user's contact. | `session` — or no cache at all |

**Problem:** The second one is the trap. Org cache is keyed by the inputs the
component sends. If two users produce the same input signature — trivially
common on a guest-accessible page where the input is a form field rather than
a server-resolved identity — they collide on one entry, and the second user
is served the first user's payload.

**Solution:** Decide from the payload's audience, in this order:

1. Does the response vary by who is asking? → not org cache.
2. Is the response derived from a *server-resolved* subject (`UserInfo`,
   record ownership, sharing) rather than a caller-supplied parameter? If the
   subject is caller-supplied, an attacker chooses the key.
3. Does it contain PII? → do not put it in a shared partition. Platform Cache
   documentation states plainly: **"Data in the cache isn't encrypted."**

Session cache carries two extra properties worth designing around:

- It "expires when its specified time-to-live value is reached **or when the
  user session expires, whichever comes first**." You cannot rely on it
  outliving a logout.
- Its maximum TTL is 8 hours, half a working week shorter than org cache's 48.

**Why it works:** The decision is made on a property of the data (whose is
it?) rather than a property of the symptom (it felt slow), which is the only
version that stays correct when the page later moves to a guest context.

---

## Example 5: Invalidation On Deploy — The Case Nobody Configures

**Context:** A bug fix ships. The corrected Data Mapper is deployed and
activated. Users still see the old values for the rest of the TTL window.

**Problem:** A TTL is a staleness *bound*, not an invalidation *mechanism*.
Activating a new component version does not, by itself, evict entries written
by the old one.

**Solution — two mechanisms, used together:**

1. **A schema-version discriminator inside the key.** Bump it as part of the
   change. Old entries become unreachable immediately and age out on their own
   TTL. This is the only invalidation that is atomic with the deploy, needs no
   runtime hook, and cannot half-fail.
2. **An explicit purge for the emergency case.** Keep a documented,
   permission-gated way to clear the affected keys — used for incidents, not
   for routine releases.

One free invalidation you should know about but must not depend on: the
Platform Cache considerations state that **"some or all cache is invalidated
when you modify an Apex class in your org."** So a deploy that touches Apex
may clear cache as a side effect. A deploy that only touches OmniStudio
metadata has no such guarantee. Do not build a release process on the side
effect — it does not apply to the metadata-only deploys that are most of
OmniStudio's change traffic.

**Why it works:** The routine path (version bump) requires no operational
readiness, and the incident path (explicit purge) is exercised rarely enough
that its cost is acceptable.

---

## Anti-Pattern: Proving The Cache Works By Timing The Designer Preview

**What practitioners do:** Run the component twice in the designer's preview
panel, watch the second run come back faster, and record "caching verified."

**What goes wrong:** The preview harness is an authoring tool. It runs with
the author's permissions, in the author's session, and its cache behaviour is
not the runtime's. A latency difference between two preview runs is consistent
with warm JIT, a warm metadata cache, a warm connection, and browser-side
effects — none of which is the response cache you configured.

More importantly, preview cannot reproduce the two failure modes that matter:
a cross-user collision (there is only one user) and an unallocated partition
(which produces no error, just no speedup).

<!-- UNVERIFIED: existing corpus text in this repo asserts that the designer
Preview sets an `ignoreCache` flag defaulting to true, so a preview run never
writes a cache entry. I could not confirm the flag name or its default in any
Salesforce-published doc. The conclusion above — that preview timings do not
demonstrate the response cache — holds regardless of whether that specific
flag exists, so the guidance does not depend on it. -->

**Correct approach:** Verify in the runtime context you are shipping to.
Exercise the read path as two *different* users (at minimum: one internal, one
in the target external audience), on the target page, and compare payloads
rather than only elapsed time. A cache that is working correctly returns the
same payload to the same audience quickly; a cache that is working *wrongly*
returns the same payload to two audiences that should have received
different ones, and only a payload comparison catches that.
