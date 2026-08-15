# IP Cacheable Patterns — Examples

Element names, action names, and metadata field names below are quoted from
the Omnistudio Integration Procedure Trailhead modules and the
`OmniIntegrationProcedure` metadata type (Industries Common Resources
Developer Guide, API 67.0). Platform Cache numbers are from the Apex
Developer Guide's Platform Cache limits table.

---

## Example 0: Two Caching Surfaces — Procedure Scope And Block Scope

**Context:** The most common structural misunderstanding about IP caching, in
both directions.

**Problem:** An Integration Procedure can be cached at two scopes, and people
routinely assume only one of them exists.

*The procedure-level surface* is the **Cache Configuration** section of the IP
configuration panel, alongside Chainable Configuration, Queueable Chainable
Limits, and Test Configuration. Trailhead: *"Use a cache to store frequently
accessed, infrequently updated Integration Procedure data. This saves round
trips to the database and improves performance."*

*The block-level surface* is the **Cache Block** element, which caches only the
steps inside it.

A note on the metadata, because it misleads in a specific way: the IP-level
metadata surface has `responseCacheType` — "Response cache used for the
integration procedure (session or Org)" — and **no documented TTL field** at
API 67.0. That means the duration does not round-trip through metadata. It does
**not** mean the designer has no procedure-level setting; it does. (Reading the
missing field as a missing feature is Anti-Pattern 1 in
`references/llm-anti-patterns.md`.)

**Solution — the four IP designer **Groups**, in the standard designer:**

| Group | What it does |
|---|---|
| **Cache Block** | "Saves the output of the steps within it to a session or org cache for quick retrieval" |
| **Conditional Block** | "Executes if a specified condition is true or treats the steps within it as a series of mutually exclusive alternatives" |
| **Loop Block** | "Iterates over the items in a data array, repeating the Actions within it for each item" |
| **Try-Catch Block** | "Lets you *try* running the steps inside the block and then *catch* the error if a step fails" |

Choosing block scope means **wrapping the expensive read steps in a Cache
Block**, so the unit of caching is the block's output rather than the whole
response. That buys two things the procedure-level setting cannot give you:

1. You can cache part of a procedure. The steps that resolve a rate table can
   sit in a Cache Block while the steps that resolve the caller's entitlement
   stay outside it, in the same procedure.
2. You can have more than one Cache Block, with different scopes, in one IP.

And it carries one obligation, which is the reason most IPs need it: anything
that must run per-call — an audit write, a permission evaluation, a mutation —
must live **outside** the block, or it will be skipped on a hit. That is the
failure mode that turns a caching change into a compliance incident, and at
procedure scope it applies to every step at once.

**Why it works:** Block-scoped caching lets you draw the cache boundary where
the data's audience actually changes, instead of at the procedure boundary
where it usually does not. Where the procedure boundary genuinely *is* the
audience boundary — every step a read, one freshness contract — procedure-level
Cache Configuration is the simpler design and there is no reason to reach for a
block.

---

## Example 1: Product Catalog — Cache The Expensive Read, Not The Procedure

**Context:** `GetProductCatalog` (Type `Product`, SubType `Catalog`) is called
on every storefront page load. It resolves a region-scoped catalog from a
custom object, enriches it from an external pricing service, and stamps the
response with a per-call correlation id for logging.

**Problem — the naive design:** cache the whole procedure. The correlation id
is now identical across thousands of requests, so the log line that was
supposed to make a slow request traceable instead points at whichever request
happened to populate the cache.

**Solution — draw the block boundary around the read only:**

```text
Integration Procedure: Product_Catalog
├── Set Values           setCorrelationId          [OUTSIDE the block]
│                        correlationId = %UUID%     — must be per-call
│
├── Cache Block          catalogRead                [org cache]
│   ├── Data Mapper Extract   getRegionCatalog
│   │                         input:  region, currency
│   └── HTTP Action           getListPrices
│                             Named Credential; GET only
│
├── Set Values           mergeResponse
│                        combines cached catalog + per-call correlationId
│
└── Response Action      returnCatalog
```

Metadata on the procedure itself:

```xml
<OmniIntegrationProcedure xmlns="http://soap.sforce.com/2006/04/metadata">
    <name>Product_Catalog</name>
    <type>Product</type>
    <subType>Catalog</subType>
    <language>en_US</language>
    <versionNumber>4</versionNumber>
    <uniqueName>Product_Catalog_en_US_4</uniqueName>
    <omniProcessKey>Product_Catalog</omniProcessKey>
    <isActive>true</isActive>
    <responseCacheType>Org</responseCacheType>
    <isMetadataCacheDisabled>false</isMetadataCacheDisabled>
    <requiredPermission>Storefront_Read</requiredPermission>
</OmniIntegrationProcedure>
```

Note the naming contract, which is not free-form: `uniqueName` is
"Type_SubType_Language_VersionNumber" and `omniProcessKey` is the
"Type_SubType" value. And per the IP designer documentation: **"There can be
only one Integration Procedure with the same Type and Sub Type active
simultaneously."** That single-active constraint is what makes the Type/SubType
pair a stable cache-key prefix — see Example 3.

**Why it works:** The cached unit is exactly the part of the response that is
identical for every caller in a region. Per-call concerns stay per-call.

---

## Example 2: The Same Procedure, Made Wrong By One Step Placement

**Context:** Same procedure, six months later. Someone adds an audit
requirement: log every catalog access with the accessing user.

**The wrong version:**

```text
├── Cache Block          catalogRead
│   ├── Data Mapper Extract   getRegionCatalog
│   ├── HTTP Action           getListPrices
│   └── Data Mapper Load      writeAccessAudit     ← INSIDE the block
```

**What goes wrong:** On a cache hit, none of the block's steps execute — that
is the entire point of the block. The audit row is written exactly once per
cache population and never again for the whole TTL window. The system passes
its own smoke test (audit rows exist) and fails its actual requirement (audit
rows are not complete). Nothing errors.

There is a second defect stacked on the first: a **Data Mapper Load** is a DML
step. Mutations do not belong inside a cache block at all, independently of
the audit requirement.

**The right version:**

```text
├── Cache Block          catalogRead
│   ├── Data Mapper Extract   getRegionCatalog
│   └── HTTP Action           getListPrices
│
├── Data Mapper Load     writeAccessAudit          ← OUTSIDE, runs every call
└── Response Action      returnCatalog
```

**Why it works:** The rule generalises — everything with a per-call
side effect or a per-call correctness requirement lives outside the block:
audit writes, permission evaluation, mutations, correlation ids, timestamps,
rate-limit counters. A useful review question is "what must be true on the
ten-thousandth call that was true on the first?" Anything on that list is
outside the block.

---

## Example 3: Cache Key Design Under The Real Constraints

**Context:** You need a purgeable, collision-free key for an IP-backed read.

**Problem — what an assistant will produce:**

```apex
// WRONG on two counts
String key = 'ip:Product_Catalog:v4:region=' + region + ':currency=' + currency;
```

1. Platform Cache keys must contain **alphanumeric characters only**;
   `put()` throws `Cache.InvalidParamException` otherwise. `:`, `=`, and `_`
   are all illegal inside the key segment.
2. **Maximum key size is 50 characters.** The string literals above account for
   39 characters (`'ip:Product_Catalog:v4:region='` is 29, `':currency='` is
   10) before a single `region` or `currency` value is appended — leaving 11
   characters for both values combined.

**Solution — a convention that survives both constraints and stays purgeable:**

```apex
/**
 * Key shape:  <procKey><schemaVer><discriminators>
 *   procKey        camelCased omniProcessKey (Type_SubType, underscore stripped)
 *   schemaVer      'V' + integer, bumped when the cached payload's SHAPE changes
 *   discriminators sanitized input values, in a FIXED order
 *
 * The leading procKey+schemaVer is a stable, purgeable prefix. Keep it short:
 * every character it consumes is a character the discriminators cannot use.
 */
private static String cacheKey(String region, String currency) {
    String prefix = 'productCatalogV4';                 // 16 chars
    String disc   = alnum(region) + alnum(currency);    // 34 chars remaining
    String key    = prefix + disc;
    return key.length() <= 50
         ? key
         : prefix + String.valueOf(Math.abs(disc.hashCode()));
}

private static String alnum(String s) {
    return s == null ? 'null' : s.replaceAll('[^a-zA-Z0-9]', '');
}
```

**Ordering matters more than it looks.** Two callers passing the same values in
a different order must produce the same key, or your hit ratio silently halves.
Fix the order in the helper; never derive it from a map's iteration order.

**What goes in the key:** every input that changes the result, plus the schema
version. **What stays out:** correlation ids, timestamps, request ids, and —
for an org-cache entry — anything identifying the caller. If caller identity
genuinely belongs in the key, that is the signal that the entry belongs in
session cache instead.

**Why it works:** The key is legal, bounded, deterministic, and prefix-purgeable.
The hash fallback preserves correctness when discriminators run long, at the
cost of readability for those specific entries only.

---

## Example 4: Per-User Entitlements — Session Cache With A Server-Resolved Subject

**Context:** `GetUserEntitlements` resolves what the running user may see. It
is called several times per page.

**Problem:** Org cache is tempting — the entitlement computation is expensive
and the hit ratio would be excellent. It is also a cross-user data leak,
because the entry is addressed by a key and the key would have to encode the
user.

**Solution:**

```text
Integration Procedure: Entitlement_ForUser
├── Set Values           resolveSubject
│                        userId = %UserId%       ← SERVER-resolved, not an input
│
├── Cache Block          entitlementRead          [session cache]
│   ├── Data Mapper Extract   getGrants
│   └── Remote Action         EntitlementResolver.resolve
│
└── Response Action      returnEntitlements
```

```xml
<responseCacheType>session</responseCacheType>
```

Two properties of session cache shape this design:

- Session cache TTL maxes out at **8 hours (28,800 s)**, and an entry "expires
  when its specified time-to-live value is reached **or when the user session
  expires, whichever comes first**." Entitlements that must survive a logout
  are not a caching problem.
- Session cache is scoped to the session, so the subject does not need to be
  in the key for isolation. Put it there anyway if the same session can act on
  behalf of more than one subject.

**The distinction that actually matters:** `%UserId%` is resolved by the
platform from the session. An input map value named `userId` is supplied by
the caller. The first is a subject; the second is a parameter an attacker
chooses. Never key a cache on the second.

**Why it works:** The isolation boundary is the session, enforced by the
platform, rather than a key convention enforced by code review.

---

## Example 5: Cache Block And Chainable Are Solving Different Problems

**Context:** A long IP is both slow *and* close to governor limits. Someone
proposes caching to fix both.

**Problem:** Caching reduces *repeat* cost. Chainable reduces *single-execution*
cost by splitting one transaction into several. A first, cold call gets no
benefit from a cache at all — and the cold call is precisely the one that hits
the governor limit.

**Solution — pick by symptom:**

| Symptom | Lever |
|---|---|
| Second and subsequent calls are slow | Cache Block |
| The *first* call breaches SOQL / CPU / heap / DML limits | Chainable |
| A DML step precedes an HTTP callout | **Chain On Step** — forces the next step into its own transaction |
| Work is long-running and can be asynchronous | Queueable Chainable |

The chainable thresholds are bounded by the underlying Apex governor limits:

| | Chainable (synchronous) | Queueable Chainable (async) |
|---|---|---|
| SOQL queries | 100 | 200 |
| CPU time | 10,000 ms | 60,000 ms |
| Heap | 6 MB | 12 MB |
| DML statements | 150 | — |

When a step exceeds the configured limits, "the interim results are saved and
the step continues in a new transaction."

**They compose, in one order only:** put the Cache Block around the expensive
read so warm calls skip it entirely, *and* set chainable thresholds so the cold
call survives. Caching first without chainable leaves the cold path broken;
chainable first without caching leaves every call paying full price.

**Why it works:** The two mechanisms are orthogonal, and conflating them
produces a design that fixes the symptom you can see (slow warm calls) while
leaving the one that pages you at 3am (cold-call limit breach) untouched.

---

## Example 6: Invalidation That Is Atomic With The Deploy

**Context:** The catalog payload's shape changes — a field is added and two are
renamed. Cached entries written by the old version are now structurally wrong,
not merely stale.

**Problem:** A TTL does not help. For up to 48 hours, warm reads return a
payload the consuming FlexCard cannot parse. Worse, this is a *correctness*
failure that a TTL-based mental model does not predict, because "stale data"
sounds survivable and "unparseable data" is not.

**Solution — bump the schema version in the key prefix as part of the change:**

```apex
- String prefix = 'productCatalogV4';
+ String prefix = 'productCatalogV5';
```

Properties that make this the right default mechanism:

- **Atomic with the deploy.** The new code cannot read old entries; there is no
  window where mixed shapes are both live.
- **Cannot half-fail.** Unlike an event-driven purge, there is no subscriber to
  miss, no retry to exhaust, no partial completion.
- **Self-cleaning.** Orphaned entries age out on their own TTL — up to 48 hours
  of wasted capacity, which is why partitions want headroom.
- **Needs no runtime infrastructure.** No platform event, no invocable Apex, no
  operational runbook.

Keep an explicit purge path as well, but scope it to incidents: a wrong *value*
shipped and must be evicted before its TTL expires. Version-bumping is for
shape changes; purging is for value emergencies. Using the second where the
first belongs is how routine releases acquire an operational step.

One thing you may not build on: Platform Cache considerations state "some or
all cache is invalidated when you modify an Apex class in your org." True, but
it does not fire for the metadata-only deploys that are most of OmniStudio's
change traffic. Treat it as an occasional free purge, never as the design.

**Why it works:** The invalidation is a source-code change reviewed alongside
the change that necessitated it, which is the only place it cannot be
forgotten.

---

## Anti-Pattern: Org Cache On A Guest-Reachable IP Because The Inputs "Look Unique"

**What practitioners do:** Set `responseCacheType` to `Org` on an IP exposed to
an Experience Cloud guest audience, reasoning that the input map is rich enough
to be effectively a per-user key.

**What goes wrong:** An input signature is not a tenant key. Two guests who
enter the same form values collide on one entry, and the second receives the
first's payload. On a guest page every input is attacker-controlled, so this is
not a coincidence to be waited for — it is an enumeration primitive. Add the
documented fact that **"data in the cache isn't encrypted"** and a PII payload
is sitting in plaintext in a shared partition, addressable by anyone who can
guess the inputs.

**Correct approach:** No org-segment cache on guest, portal, or PII Integration
Procedures. Session cache, keyed on a server-resolved subject, or no cache. If
the read genuinely must be shared across callers, cache only the part of the
payload that contains no personal data — which is what the Cache Block's
block-scoping makes possible: wrap the shared reference lookup, leave the
personalized resolution outside it.
