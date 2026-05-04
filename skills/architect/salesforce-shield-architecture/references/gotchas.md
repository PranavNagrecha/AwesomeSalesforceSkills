# Gotchas — Salesforce Shield Architecture

Non-obvious Shield behaviors that bite real Shield-enabled orgs.

---

## Gotcha 1: Three Shield licenses, separately purchased — none in standard editions

**What happens.** A design recommends Platform Encryption + Field
Audit Trail + Event Monitoring on an org that has only one or none of
the three licenses. Setup screens are missing; the recommendation
becomes a blocker on procurement.

**When it occurs.** Anyone treating "Salesforce Shield" as a single
SKU. It isn't — it's three separately-priced products bundled
marketing-wise.

**How to avoid.** Pre-flight: Setup → Company Information → Permission
Set Licenses. Three lines: `Platform Encryption`, `Event Monitoring`,
`Field Audit Trail`. Each must be present before recommending its
component. Document the per-component license cost up front.

---

## Gotcha 2: Probabilistic encryption blocks SOQL `WHERE =` and ORDER BY

**What happens.** Field encrypted probabilistically: SOQL queries that
filter on it (`WHERE EncryptedSSN__c = '123-45-6789'`) return nothing
even when the row exists. Reports filtering on the field also return
nothing.

**When it occurs.** Default scheme is probabilistic; team encrypts a
field assuming filterability survives encryption.

**How to avoid.** **Deterministic** encryption (case-sensitive or
case-insensitive) supports equality filter and sort. Decision criteria:
*if any business process needs to filter, sort, or group-by on the
field, it must be deterministic*. Probabilistic for fields that are
read-only-once (display, audit, archival).

You cannot change scheme on a populated field without re-encrypting
every row — a maintenance event for large objects.

---

## Gotcha 3: Formula, Roll-Up, and Unique-Indexed External ID fields cannot be encrypted

**What happens.** Setup rejects the field. Or worse — a metadata
deploy of a Encryption Policy listing a Formula field fails with an
error that doesn't immediately point at the field-type mismatch.

**When it occurs.** Encrypting a "computed" field (formula, roll-up
summary) thinking the encryption flows through the computation. It
doesn't — encryption breaks the computation.

**How to avoid.** Encrypt the **source** field instead. The formula /
roll-up evaluator reads decrypted plaintext at evaluation time; the
output isn't independently encrypted but the source is protected.

For unique-indexed External ID fields, the same rule applies — you
can't have a unique-index lookup AND encryption on the same field
because the index requires plaintext. If both are needed, encrypt a
*different* field that holds the same value, and use that one for
display while the unique-indexed plaintext stays as the lookup key.

---

## Gotcha 4: CCKM (Cache-Only Key Service) outage causes encryption operations to fail

**What happens.** Customer HSM (AWS CloudHSM, Azure Key Vault, on-prem
HSM appliance) goes offline. Salesforce's key cache eventually expires.
Encryption / decryption operations on Shield-protected fields fail —
new writes are rejected, reads of recently-cached data still work
until the cache TTL.

**When it occurs.** Any HSM availability incident. Power, network,
maintenance window without coordination.

**How to avoid.** Acknowledge it as the design's failure mode, not a
defect. Include in the runbook: "HSM outage = Salesforce write
availability degraded for Shield-encrypted fields until HSM restoration
or cache repopulation." Operate the HSM with the appropriate
availability target (99.95+ % for production-critical workloads).
Customers who can't accept this trade should use BYOK or
Salesforce-managed keys instead.

---

## Gotcha 5: Field Audit Trail retention is metadata XML, not a Setup checkbox

**What happens.** Architects assume "I'll just set the retention to 10
years in Setup" — there's no Setup UI for the per-object retention
policy. They look for the toggle, can't find it, escalate.

**When it occurs.** Anyone treating Field Audit Trail like a checkbox
feature.

**How to avoid.** The retention is set per object via the
`HistoryRetentionPolicy` element in the object's `.object-meta.xml`,
deployed via Metadata API or Tooling API. Example:

```xml
<HistoryRetentionPolicy>
    <archiveAfterMonths>18</archiveAfterMonths>
    <archiveRetentionYears>10</archiveRetentionYears>
</HistoryRetentionPolicy>
```

Maximum `archiveRetentionYears` is 10. The two values together describe
a two-tier retention: standard `<Object>History` for the first
`archiveAfterMonths`, then `FieldHistoryArchive` until
`archiveRetentionYears` total.

---

## Gotcha 6: Tenant-secret rotation re-encrypts every row of every encrypted field

**What happens.** The "rotate tenant secret" button looks instant. It
isn't — it triggers a background job that re-encrypts every row that
uses the rotated key derivation. For orgs with millions of encrypted
records, this is hours of background work and impacts throughput on
the affected objects.

**When it occurs.** Quarterly / annual rotation events on
heavy-encrypted-data orgs. Especially painful when rotation is forced
by an audit deadline rather than scheduled.

**How to avoid.** Plan rotation as a maintenance window. Inform users
that bulk operations on affected objects may run slower during
rotation. Coordinate with Salesforce account team for very large
orgs — they may recommend a rotation cadence that fits the org's
volume.

---

## Gotcha 7: Real-Time Event Monitoring is Pub/Sub-based; old streaming-API code is deprecated

**What happens.** A custom subscriber written against the
`/event/SessionHijackingEvent` CometD streaming channel stops
receiving events after a Salesforce release.

**When it occurs.** Subscribers written before Real-Time Event
Monitoring migrated to Pub/Sub API (the migration happened in stages
across Spring '23 → Summer '24).

**How to avoid.** Subscribe via Pub/Sub API (gRPC). The transaction
security framework consumes the same events natively if you don't
need a custom subscriber.

---

## Gotcha 8: Shield doesn't encrypt indexes — search index is a separate decision

**What happens.** Field encrypted at rest; admin assumes search now
hits ciphertext. The search index actually holds plaintext (or the
search wouldn't return matches). Search privileges are a different
control.

**When it occurs.** Threat-model assumption that "encrypted at rest"
means "ciphertext everywhere".

**How to avoid.** Document the encryption boundary: at-rest in the
database, ciphertext in disk-level dumps. Search index, in-memory
during query, decrypted in API responses. The threat model needs to
account for memory snapshots, search infrastructure access, and API
response interception — encryption-at-rest doesn't address all of
those.
