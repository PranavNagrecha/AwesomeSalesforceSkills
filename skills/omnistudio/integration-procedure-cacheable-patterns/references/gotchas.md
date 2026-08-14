# IP Cacheable — Gotchas

## 1. Platform Cache Size Is Finite

Org-wide partitions have an allocated size. A chatty IP can thrash the
partition and evict useful entries.

## 2. Session Cache Dies With The Session

Session partition data does not survive logout or browser close. Do not
rely on it for long-lived state.

## 3. Null Partition Returns

`Cache.Org.getPartition('X')` returns null if the partition is undefined.
Always handle the null case.

## 4. Cache Keys Are Case-Sensitive

`product` and `Product` are different keys. Use a canonical case in all
callers.

## 5. TTL Rounds Up

Platform cache TTL is in seconds but implementation granularity can
bucket. Don't depend on exact expiry.

## 6. Managed Package Namespaces

Partition names include the namespace. Cross-package cache sharing needs
thought.

## 7. Cached Serialized JSON Can Drift

If the serialization format changes, cached entries become
incompatible. Version the key prefix.

---

## 8. Org-Segment IP Cache Can Cross Users

**What happens:** Top-level IP cache keyed by input signature at **Org** scope returns another user's results to anyone who presents the same inputs — including a guest.

**When it occurs:** "Cacheable" ticked on a guest or PII IP because Preview was slow.

**How to avoid:** No Org-segment cache on guest, portal, or PII Integration Procedures. Session or User partition, or no cache. Include a server-side subject in the key if you must cache. Designer Preview `ignoreCache` defaults true — it will not catch this. See `omnistudio-performance` Gotcha 6.
