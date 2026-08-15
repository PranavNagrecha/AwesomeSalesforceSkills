# Gotchas — OmniStudio Cache Strategies

Non-obvious behaviour that produces a wrong answer, a silent no-op, or a
security finding. Numbers are from the Apex Developer Guide's Platform Cache
limits table and the API 67.0 metadata reference unless marked otherwise.

---

## 1. TTLs Below 5 Minutes Are Below The Platform Floor

**What happens:** You set **Time to Live in Minutes** to `1`, `2`, or `3` on a
Data Mapper. The configuration saves. The behaviour does not match the number.

**When it occurs:** Whenever someone reasons "shorter TTL = safer" without
checking the range. It is the single most common cache misconfiguration
because the field accepts the value without complaint.

**The limits, verbatim from the Platform Cache limits table:**

| | Minimum TTL | Maximum TTL | Default TTL |
|---|---|---|---|
| Session cache | 300 s (5 min) | 28,800 s (8 h) | — |
| Org cache | 300 s (5 min) | 172,800 s (48 h) | 86,400 s (24 h) |

**How to avoid:** Treat 5 minutes as the floor and 48 hours (org) / 8 hours
(session) as the ceiling. If your freshness requirement is genuinely tighter
than 5 minutes, the correct answer is **not to cache**, not to write a small
number into the field.

---

## 2. Cache Keys Must Be Alphanumeric — Punctuation Throws

**What happens:** `Cache.InvalidParamException` at runtime, from a code path
that passed code review because the key "looked like a cache key."

**When it occurs:** Every time a key is built in the idiomatic style borrowed
from Redis or Memcached — `namespace:entity:v3:id=123`. Colons, equals signs,
dots inside the key segment, and hyphens are all illegal.

**The rule:** the `put(key, value)` method requires a key that is not null and
contains **alphanumeric characters only**, and throws
`Cache.InvalidParamException` when the key fails validation. Separately,
**maximum key size is 50 characters**.

**How to avoid:** Adopt a camelCase, separator-free key convention and enforce
it in one helper rather than at every call site. Keep a version discriminator
in the key (`pricingMatrixV3…`) — it is your cheapest invalidation lever and
it survives the alphanumeric constraint fine.

Note the one place punctuation is legal: the *fully qualified* key format is
`namespace.partition.key`, so the dots that separate namespace from partition
from key are structural. They are not part of the key segment, and they do not
license dots inside it.

---

## 3. Cached Data Is Not Encrypted, And Cache Does Not Re-Check Sharing

**What happens:** A payload that was correctly filtered by sharing and FLS on
the cold path is served from cache on the warm path without those checks
running again — because they ran against the *first* caller.

**When it occurs:** Any org-cache entry whose key is derived from
caller-supplied inputs rather than a server-resolved subject. Guest and
Experience Cloud contexts are the high-risk case: an unauthenticated visitor
controls every input, therefore controls the key, therefore can address
another visitor's entry.

**Compounding fact:** Platform Cache considerations state directly that
**"Data in the cache isn't encrypted."** Shield Platform Encryption protects
the field at rest in the record; it does not follow the value into a cache
entry. A payload you were required to encrypt in storage is sitting in
plaintext once cached.

**How to avoid:**

- Org cache only for payloads that are genuinely identical for every caller
  and contain no PII.
- Session cache, or no cache, for anything scoped to a person.
- If a cache is unavoidable on a personalized path, put a **server-resolved**
  subject in the key (from `UserInfo` / the session), never a value the caller
  supplied.
- Keep `fieldLevelSecurityEnabled` true on the Data Mapper. It governs the
  cold path — which is the path that decides what gets written into the cache
  and therefore what every subsequent warm read returns.

---

## 4. Scale Cache Is *Reported* To Execute A Cached Data Mapper Past Its Required Permission

**Provenance first, because this one is not Salesforce-documented.** Everything
in this entry traces to AppOmni's 2025 Salesforce Industry Cloud security
research, reported via CSO Online and Information Security Buzz. No
Salesforce-published source states the behaviour. Treat it as a reason to
design defensively, not as a platform fact to quote.

**What is reported to happen:** After a component's metadata is cached, it can
run for a user who would fail the **Required Permission** check on a cold
(uncached) execution — the permission check sits on the path that the cache is
designed to skip.

**When it occurs:** Guest-reachable portals where "Required Permission on
every component" was the only access control. Also nested execution: a parent
Integration Procedure invoking a child Data Mapper.

**How to avoid:** The defensive posture is correct whether or not the reported
bypass reproduces in your org, which is why it is worth acting on anyway: do
not treat Required Permission as an authorization boundary that holds after the
cache warms. Gate access at the surface that is actually evaluated per call —
the object and field permissions of the running user, and the sharing model —
and keep `fieldLevelSecurityEnabled` on. If you need to know whether the bypass
is live for you, reproduce it in a sandbox; do not assert it to a customer.

<!-- UNVERIFIED: the behaviour above AND the OmniStudio custom-setting names
for its remediation are both unconfirmed against Salesforce. The setting names —
`TurnOffScaleCache` (set to `true` to disable scale cache) and
`CheckCachedMetadataRecordSecurity` — come from AppOmni's 2025 Salesforce
Industry Cloud research as reported by CSO Online and Information Security
Buzz, not from a Salesforce-published doc I could read. The same research
reports that enabling `CheckCachedMetadataRecordSecurity` was NOT sufficient
for Data Mappers and that only disabling scale cache enforced the check. The
corresponding Salesforce Help articles ("Security for Omnistudio Data Mappers
and Integration Procedures", "Omnistudio Data Mapper and Integration Procedure
Security Settings") exist but render no article text to a fetcher, so I could
not verify the setting names, their exact spelling, or whether they apply to
the standard runtime, the managed package, or both. Verify in Setup before
quoting either name to a customer. -->

---

## 5. `isMetadataCacheDisabled` Defaults To `false` — Metadata Caching Is Already On

**What happens:** Someone "enables caching" on an Integration Procedure by
looking for a metadata-cache switch, finds `isMetadataCacheDisabled`, and
reasons about it backwards.

**When it occurs:** Reading the metadata reference without noticing the field
is a *negative*. On both `OmniIntegrationProcedure` and `OmniScript`:

> **isMetadataCacheDisabled** (boolean) — "Indicates whether metadata cache
> for the integration procedure is disabled. Default: false."

Default `false` means metadata caching is **on** out of the box. Setting it to
`true` turns caching **off**, which is a debugging and staleness-remediation
move, not a performance move.

**How to avoid:** Read negatively-named booleans twice. And keep the two
concerns separate: `isMetadataCacheDisabled` governs the component
*definition*; `responseCacheType` governs the component *output*. Flipping the
first will not change what a warm read returns.

---

## 6. The IP Metadata Type Documents A Cache Type But No TTL

**What happens:** You try to set a response-cache TTL on an Integration
Procedure *in metadata* the way you set one on a Data Mapper, and there is no
field.

**When it occurs:** Porting a Data Mapper cache design onto an IP. The two
metadata types genuinely differ:

| Field | `OmniDataTransform` | `OmniIntegrationProcedure` |
|---|---|---|
| `responseCacheType` | yes (org / session) | yes (session or Org) |
| `responseCacheTtlMinutes` | **yes** | **not documented** |
| `isMetadataCacheDisabled` | not documented | yes |

**The trap inside the trap:** this is a fact about the *metadata surface*, and
it is easy to over-read into a claim about the *designer*. It is not one. The
Integration Procedure configuration panel has a **Cache Configuration**
section — Trailhead: *"Use a cache to store frequently accessed, infrequently
updated Integration Procedure data. This saves round trips to the database and
improves performance."* — sitting alongside Chainable Configuration, Queueable
Chainable Limits, and Test Configuration. What the missing field actually means
is that the IP's cache duration **does not round-trip through metadata** at API
67.0: it will not appear in a retrieve, a source diff, or a metadata-based
deployment check.

**How to avoid:** Set and verify the IP cache duration in the designer, and
record it in the design doc, because source control will not carry it. Then
pick the scope on the shape of the procedure: procedure-level Cache
Configuration when every step is a read with one audience and one freshness
contract; a **Cache Block** when any step must run per call or parts of the
response have different audiences. See
`omnistudio/integration-procedure-cacheable-patterns`, which owns that design in
this library.

---

## 7. A Cached Item Over 100 KB Does Not Fit

**What happens:** A large aggregate response — a full catalog, a wide record
set — is written to cache and is simply not there on the next read. No
exception on the read; a miss looks identical to an expiry.

**When it occurs:** The Platform Cache limit is **100 KB maximum size of a
single cached item** for `put()` methods. OmniStudio aggregate responses cross
that line easily; a few hundred records with a dozen fields each will do it.

There is a second, easier-to-miss ceiling: **maximum local cache size for a
partition, per request** is 500 KB (session) / 1,000 KB (org). A single
transaction that reads many cached entries can exhaust the per-request local
cache even when each individual entry is legal.

**How to avoid:** Cache the *expensive small thing* (a resolved rate, a
permission decision, a lookup table's compact form), not the *large convenient
thing* (the whole response payload). If the payload is inherently large,
project it down before caching, and measure the serialized size rather than
guessing from record count.

---

## 8. Cache Is Not Persisted, And An Apex Deploy May Wipe It

**What happens:** Hit ratio drops to zero at an unpredictable moment, then
recovers. Nothing in the OmniStudio configuration changed.

**When it occurs:** Two documented behaviours, both outside your control:

- **"Cache isn't persisted. There's no guarantee against data loss."** Eviction
  under memory pressure is normal operation, not a fault.
- **"Some or all cache is invalidated when you modify an Apex class in your
  org."** Any deploy that touches Apex — including one unrelated to the cached
  path — can clear entries.

**How to avoid:** Build every read path so a miss is a latency event, never a
correctness or availability event. Concretely: no code path may throw because
a `get()` returned null, and no user-visible error may originate in the cache
layer. Also, do not size capacity planning on a steady-state hit ratio you
observed once — plan for the cold-start load that follows an eviction, because
that is the load the system must survive.

---

## 9. Session Cache Dies With The Session, Not With Its TTL

**What happens:** An 8-hour session-cache TTL evaporates at logout, at session
timeout, or when the browser session ends.

**When it occurs:** By design — session cache "expires when its specified
time-to-live value is reached or when the user session expires, whichever
comes first."

**How to avoid:** Never use session cache as a store for anything that must
survive a logout. That is a persistence requirement, not a caching one — see
`omnistudio/omniscript-session-state` for the durable options. There is also a
platform restriction on accessing session cache from Salesforce Flow; if a
Flow is in your invalidation or warming path, verify it can reach the
partition before designing around it.

---

## 10. "Standard Runtime" And "Managed Package" Are Different Products In The Docs

**What happens:** You follow a caching article to the letter and the UI does
not match, because you are reading the other runtime's documentation.

**When it occurs:** Constantly, and it is under-signposted. Salesforce Help
publishes parallel articles distinguished only by a "(Managed Package)"
suffix and a different URL id prefix — for example, a "Cache for Omnistudio
Data Mappers" article and a separate "Cache for Omnistudio Data Mappers
(Managed Package)" article. Search results mix them freely.

**How to tell which runtime you are on:** `OmniStudioSettings` carries
`enableStandardOmniStudioRuntime` — "Indicates whether to enable the standard
Omnistudio runtime environment," available in API version 65.0 and later.
`enableOaForCore` enables "Omnistudio core builder functionality and the
standard Omnistudio designer experience," available in API 63.0 and later,
with namespace constraints covering `omnistudio`, `vlocity_cmt`,
`vlocity_ins`, and `vlocity_ps`.

**How to avoid:** Check the settings before citing any behavioural claim, and
prefer the metadata reference over prose articles — `OmniDataTransform`,
`OmniIntegrationProcedure`, and `OmniScript` in the Industries Common
Resources Developer Guide are versioned to the API release, so a field that is
documented there at API 67.0 exists in the standard surface at Summer '26.

One related setting deserves a standing warning: **`enableOmniStudioMetadata`
is irreversible once enabled.** It turns on Metadata and Tooling API access
for OmniStudio components. Enable it deliberately, in a sandbox first.

---

## 11. Data Mapper Versioning Is A Setting, Not A Default

**What happens:** A team assumes Data Mappers version like OmniScripts do, and
designs a cache-invalidation-on-version-bump strategy around a version number
that is not being incremented.

**When it occurs:** `OmniStudioSettings.enableOmniStudioDrVersion` —
"Indicates whether to turn on Omnistudio Data Mapper version functionality
within Omnistudio" — is a separate opt-in. `OmniDataTransform.versionNumber`
exists as a field regardless, but whether the platform manages it as a
versioning lifecycle depends on the setting.

**How to avoid:** Confirm the setting before making version-based invalidation
load-bearing. If it is off, put the version discriminator in your own cache
key convention (`…V3…`) where you control the increment, rather than deriving
it from component metadata you are not actually versioning.
