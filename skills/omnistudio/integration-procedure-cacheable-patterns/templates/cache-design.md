# IP Cache Design

## Runtime

- [ ] Standard runtime (`OmniStudioSettings.enableStandardOmniStudioRuntime` = true)
- [ ] Managed package
- Confirmed by: _(who checked, where)_

## IP

- Name / Type / SubType:
- `omniProcessKey` (Type_SubType):
- Current latency (p50 / p95):
- Calls / hour (peak):
- Source data volatility:
- **Serialized payload size (bytes, measured not estimated):** _(must be < 100 KB)_
  `System.debug(JSON.serialize(payload).length());`

## Cache Scope

Pick one. The test is whether ANY step must be true on the ten-thousandth call
as well as the first.

- [ ] **Procedure scope** — the **Cache Configuration** section of the IP
      configuration panel. Valid only when *no* step needs to run per call:
      every step a read, one audience, one freshness contract.
- [ ] **Block scope** — a **Cache Block** element around the read steps, with
      the per-call steps outside it. Required as soon as one step must run
      every time, or parts of the response have different audiences or TTLs.

Note for source control: the IP cache duration is **not** documented as a field
on `OmniIntegrationProcedure` at API 67.0 (`responseCacheType` is; a TTL field
is not). It will not appear in a retrieve or a source diff, so record the
agreed value here and verify it in the org before release.

- Duration set in the designer (value + who verified it, where):

## Cache Block Boundary

*(Skip if procedure scope was chosen above.)*

List every step and mark it in or out. A step goes OUTSIDE if it must be true
on the ten-thousandth call as well as the first.

| Step | Type | In block? | Why |
|---|---|---|---|
|  |  |  |  |

Mandatory outside-the-block audit:

- [ ] No Data Mapper Load / Delete action inside the block
- [ ] No non-GET HTTP action inside the block
- [ ] No audit or logging write inside the block
- [ ] No correlation id / timestamp generation inside the block
- [ ] No rate-limit or quota counter inside the block

## Cache Key

Constraints: **alphanumeric characters only**, **max 50 characters**.
`Cache.Partition.put()` throws `Cache.InvalidParamException` on an invalid key.

- Prefix (camelCased process key + schema version, no underscores):
- Discriminators, in **fixed** order:
- Inputs deliberately excluded (justify):
- Example key: _(count the characters)_
- Length of the longest realistic key: ____ / 50
- [ ] Built in a single helper, not per call site
- [ ] Unit test: two differently-ordered input maps produce the same key

## Partition

- [ ] Org (`responseCacheType` = `Org`) — justify: payload identical for every
      caller AND contains no PII
- [ ] Session (`responseCacheType` = `session`) — subject is server-resolved
      (`%UserId%`), not a caller-supplied input-map value
- [ ] No cache — freshness contract tighter than 5 minutes, or guest-reachable PII

Guest / portal exposure check:

- [ ] This IP is NOT reachable by a guest user, **or** it uses session cache /
      no cache
- [ ] Reviewed against "data in the cache isn't encrypted"

## TTL

- Value: ____ (org: 300–172,800 s / 5 min–48 h, default 86,400 s;
  session: 300–28,800 s / 5 min–8 h)
- [ ] Within platform bounds
- Freshness contract agreed with (data owner):
- Rationale:

## Invalidation

- [ ] Schema-version discriminator in the key prefix — bumped in the same
      commit as any change to the cached payload's **shape**
- [ ] Explicit purge path documented for value emergencies
- Purge owner / permission required:
- Answer this: *a wrong value ships at 09:00 — what makes the fix visible
  before the TTL expires?*

Not relied upon: "some or all cache is invalidated when you modify an Apex
class in your org" — it does not fire for metadata-only deploys.

## Fallback

- [ ] `getPartition()` null-checked at every call site
- [ ] A null from `get()` falls through to the live path
- [ ] No user-visible error can originate in the cache layer
- On live-fetch error: _(error surface / default)_

## Cold Path

- [ ] Cold-call governor-limit risk assessed separately from caching
- If at risk, lever chosen:
  - [ ] Chainable (sync bounds: 100 SOQL / 10,000 ms CPU / 6 MB heap / 150 DML)
  - [ ] Queueable Chainable (200 SOQL / 60,000 ms CPU / 12 MB heap)
  - [ ] Chain On Step (DML immediately before a callout)
- [ ] Source system can survive full cold-start load after a total eviction

## Monitoring

- Hit ratio target: ____%
- Alert on hit ratio below target
- Evictions trend tracked

## Sign-Off

- [ ] Block boundary excludes every side-effecting step
- [ ] Key is legal, bounded, deterministic, and prefix-purgeable
- [ ] Partition matches the payload's audience, not the desired hit ratio
- [ ] TTL inside platform bounds and agreed with the data owner
- [ ] Invalidation lever named with an owner
- [ ] Miss path never fails hard
- [ ] Verified in the target runtime context as two different users, comparing
      payloads — not by timing two designer preview runs
