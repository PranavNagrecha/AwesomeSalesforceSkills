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
