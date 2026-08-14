# LLM Anti-Patterns — OmniStudio Cache Strategies

## Anti-Pattern 1: Cache With No Bust Strategy

**What the LLM generates:** DataRaptor or IP cache enabled, TTL copied from another component, no deploy-time key bump.

**Why it happens:** Cache is treated as a checkbox, not an operational contract.

**Correct pattern:** Version the cache key on deploy. Document who busts it. Preview `ignoreCache` defaults true — designer timing does not prove the cache.

**Detection hint:** Cache on, no key prefix, no `TurnOffScaleCache` decision for guest DMs.

---

## Anti-Pattern 2: Global Cache for User-Specific Data

**What the LLM generates:** Org-segment platform cache on a guest or portal IP "because Preview was slow."

**Why it happens:** Org cache is the default that looks fastest.

**Correct pattern:** Session or User partition for anything keyed by a person. Org cache only for truly shared, non-PII reference data. Same inputs from two guests must not share a PII payload.

**Detection hint:** `Cache Type = Org` on an IP that takes ContextId, contactId, or a session token.

---

## Anti-Pattern 3: Absurdly Long TTLs

**What the LLM generates:** 24-hour TTL on eligibility or notice-list data.

**Why it happens:** Copy-paste from a product catalog example.

**Correct pattern:** TTL per freshness contract. Fetch-once / store-in-transaction-object is a different store — it still needs purge.

---

## Anti-Pattern 4: Trusting Required Permission After Scale Cache Warms

**What the LLM generates:** "Required Permission on every Data Mapper, so guests are safe."

**Why it happens:** The property looks like an authorization gate.

**Correct pattern:** Scale Cache can execute a cached DM regardless of Required Permission. `TurnOffScaleCache` on guest-reachable DMs. `CheckCachedMetadataRecordSecurity` on IPs. Nested parent IPs skip child permission entirely.

**Detection hint:** Guest Omni + Scale Cache on + Required Permission as the only control.

---

## Anti-Pattern 5: Caching Writes

**What the LLM generates:** Cache a DataRaptor Load response so "the next save is faster."

**Why it happens:** Cache = faster, applied to every step type.

**Correct pattern:** Cache reads. Loads and HTTP mutations are not cache entries. Idempotency keys belong on the write path, not in platform cache.
