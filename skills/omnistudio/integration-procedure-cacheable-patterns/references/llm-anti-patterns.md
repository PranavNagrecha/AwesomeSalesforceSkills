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
