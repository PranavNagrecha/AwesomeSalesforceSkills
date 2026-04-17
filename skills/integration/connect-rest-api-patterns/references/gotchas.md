# Gotchas — Connect REST API Patterns

## Gotcha 1: Missing community context

**What happens:** Post appears in wrong feed.

**When it occurs:** Forgot communityId.

**How to avoid:** Always pass explicit communityId.


---

## Gotcha 2: Sharing mismatch

**What happens:** Integration user can't post on behalf of another.

**When it occurs:** No 'Modify All' on FeedItem.

**How to avoid:** Use internal-only or run user override.


---

## Gotcha 3: Verbose payload bloat

**What happens:** Response 500kB.

**When it occurs:** Default include.

**How to avoid:** Request specific fields.

