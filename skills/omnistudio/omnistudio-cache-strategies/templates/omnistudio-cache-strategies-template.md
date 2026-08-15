# OmniStudio Cache Strategy — Work Template

## 0. Runtime and substrate (do this first — everything else is meaningless until it passes)

- Runtime: [ ] Standard (`OmniStudioSettings.enableStandardOmniStudioRuntime` = true)
             [ ] Managed package
  - Confirmed by / where:
- Platform Cache allocation in Setup → Platform Cache:
  - Org Cache allocated: ______ MB   (minimum partition size is 1 MB)
  - Session Cache allocated: ______ MB
- [ ] **Allocation is non-zero.** A partition with no capacity produces no
      error and no speedup, and every measurement below is meaningless.

> Salesforce Help publishes parallel articles distinguished only by a
> "(Managed Package)" suffix. Record the runtime before citing any article.

## 1. Which cache layer is this about?

- [ ] **Component metadata cache** — the compiled component definition.
      `isMetadataCacheDisabled` (default `false`, i.e. caching is already ON).
      Symptom it fixes: slow cold start after deploy.
- [ ] **Response cache** — the output payload. Data Mapper **Options** tab; or,
      on an Integration Procedure, either the **Cache Configuration** section of
      the procedure's configuration panel (whole response) or a **Cache Block**
      element (enclosed steps only).
      Symptom it fixes: warm reads no faster than cold.
- [ ] **Platform Cache** — the substrate. Setup → Platform Cache.
      Symptom it fixes: nothing is cached at all, silently.

Naming the layer is the whole diagnostic. Do not proceed until one box is
ticked.

## 2. Component

- Name / type: [ ] Data Mapper (`OmniDataTransform`)  [ ] Integration Procedure
  [ ] OmniScript
- `type` (Data Mapper only): [ ] Extract  [ ] Transform  [ ] Load
  - **A `Load` is a mutation. Do not cache it.** The levers for a slow Load are
    `synchronousProcessThreshold`, `processSuperBulk`, and `rollbackOnError`.
- Reachable by: [ ] internal only  [ ] authenticated portal  [ ] **guest**
- Contains PII: [ ] yes  [ ] no

## 3. Measurement (before)

- p50 / p95 latency, cold, as a target-audience user:
- Calls per hour at peak:
- **Serialized payload size in bytes** (measured, not estimated):
  `System.debug(JSON.serialize(payload).length());`
  - [ ] Under the **100 KB** single-item ceiling

## 4. Cache type — decided from the payload's audience, not its latency

- [ ] `org` — the payload is identical for **every** caller AND contains no PII
- [ ] `session` — scoped to a person; subject is **server-resolved**
      (`%UserId%` from the session), not a caller-supplied input value
- [ ] **No cache** — guest-reachable PII, or a freshness contract tighter than
      5 minutes

Guest check:

- [ ] This component is not guest-reachable, **or** it is not using org cache
- [ ] Reviewed against the documented fact that "data in the cache isn't
      encrypted" — Shield encryption does not follow a value into a cache entry

## 5. TTL

- Value: ______
- Field: [ ] `responseCacheTtlMinutes` (Data Mapper — **minutes**)
         [ ] IP Cache Configuration section (procedure scope)
         [ ] Cache Block configuration (block scope)
- [ ] Within platform bounds:

| | Minimum | Maximum | Default |
|---|---|---|---|
| Session cache | 300 s / 5 min | 28,800 s / 8 h | — |
| Org cache | 300 s / 5 min | 172,800 s / 48 h | 86,400 s / 24 h |

- Freshness contract agreed with (data owner, name + date):
- [ ] If the contract is tighter than 5 minutes, the recorded decision is
      **not to cache** — not a smaller number in the field

> `responseCacheTtlMinutes` is in minutes; Apex `put(key, value, ttl)` is in
> seconds. A 60× error in either direction is the commonest unit bug here.
>
> An IP's cache duration is not documented as a field on
> `OmniIntegrationProcedure` at API 67.0, so it does not travel in a retrieve
> or show up in a source diff. Record the agreed value in this document and
> verify it in the org.

## 6. Cache keys (if any Apex touches the cache directly)

Constraints: **alphanumeric characters only**, **max 50 characters**.
`put()` throws `Cache.InvalidParamException` on an invalid key.

- Key convention (camelCase, no separators — note `omniProcessKey` contains an
  underscore that must be stripped):
- Version discriminator:
- Longest realistic key length: ______ / 50
- [ ] Built in one helper, not per call site
- [ ] `getPartition()` null-checked at every call site

## 7. Invalidation

- [ ] Version discriminator in the key, bumped in the same commit as any change
      to the cached payload's **shape**
- [ ] Explicit purge path documented for value emergencies
- Purge owner / permission required:
- Answer this: *a wrong value ships at 09:00 — what makes the fix visible
  before the TTL expires?*

Not relied upon: "some or all cache is invalidated when you modify an Apex class
in your org." Real, documented, and it does not fire for metadata-only deploys —
which are most of OmniStudio's change traffic.

## 8. Security posture

- [ ] `fieldLevelSecurityEnabled` = true on cached Data Mappers (it governs the
      **cold** path, which decides what every warm read returns)
- [ ] Required Permission is **not** the only access control — metadata caching
      can execute a cached component for a user who would fail it on a cold run
- [ ] No PII in a shared partition

## 9. Verification (not the designer preview)

- [ ] Exercised in the **target runtime context**, on the target page
- [ ] As **two different users**, at minimum one internal and one from the
      target external audience
- [ ] **Payloads compared**, not only elapsed time — a cache working *wrongly*
      returns the same payload to two audiences that should have received
      different ones, and only a payload comparison catches that

## 10. Monitoring

- Hit ratio target: ______%
- [ ] Alert when hit ratio drops below target
- [ ] Cold-start load after a full eviction is survivable by the source system
      (cache "isn't persisted"; an Apex deploy may clear it)

## Sign-off

- [ ] Runtime recorded; partition allocation non-zero
- [ ] Correct layer identified
- [ ] Cache type matches the payload's audience
- [ ] TTL inside platform bounds and agreed with the data owner
- [ ] Payload under 100 KB, measured
- [ ] Keys alphanumeric and ≤ 50 chars
- [ ] Invalidation lever named with an owner
- [ ] No cache on a `Load`, and no cache on guest-reachable PII
- [ ] Verified as two users with payload comparison
