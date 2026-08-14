# LLM Anti-Patterns — IP Cacheable

## Anti-Pattern 1: Cache Everything Org-Wide

**What the LLM generates:** put every IP result in org-wide partition.

**Why it happens:** "cache = shared."

**Correct pattern:** user-scoped data in Session; only truly shared data
in Org-wide.

## Anti-Pattern 2: Hash-Only Keys

**What the LLM generates:** `MD5(JSON.stringify(input))`.

**Why it happens:** uniqueness.

**Correct pattern:** readable, versioned keys so you can purge by prefix
during invalidation.

## Anti-Pattern 3: No Invalidation

**What the LLM generates:** TTL 3600s and done.

**Why it happens:** TTL feels like a complete story.

**Correct pattern:** event-driven invalidation or versioned keys; TTL is
a safety net, not the primary mechanism.

## Anti-Pattern 4: Fail Hard On Cache Miss

**What the LLM generates:** throw if `get()` returns null.

**Why it happens:** defensive coding.

**Correct pattern:** cache is an accelerator; fall through to live
fetch; only bubble errors from the live path.

## Anti-Pattern 5: Cache PII In Shared Partition

**What the LLM generates:** cache a personalized response globally.

**Why it happens:** missed scope.

**Correct pattern:** audit every cached field for user-specificity
before picking the partition.

---

## Anti-Pattern 6: Org Cache on a Guest IP Because the Inputs "Look Unique"

**What the LLM generates:** Org-segment cache keyed by the IP input map. Guest A and guest B with the same form fields share a payload.

**Why it happens:** Input signature feels like a tenant key.

**Correct pattern:** No Org-segment cache on guest, portal, or PII Integration Procedures. Put a server-resolved subject in the key if you must cache. Designer Preview will not catch this (`ignoreCache` defaults true).

**Detection hint:** Procedure Configuration cache type Org plus an IP reachable via `GenericInvoke2NoCont` as guest.

---

## Anti-Pattern 7: Proving Cache in Designer Preview

**What the LLM generates:** Two Preview runs, elapsed-ms compared, "cache works."

**Why it happens:** Preview is where authors live.

**Correct pattern:** Preview `ignoreCache` defaults true, so the run never saves. Set it false, assert `vlcCacheResult` / `vlcCacheKey`, and clear with `ConnectApi.OmniDesignerConnect.ClearIntegrationProcedureCache`. Failed IPs are not cached — an intermittent fault looks like a permanent miss.
