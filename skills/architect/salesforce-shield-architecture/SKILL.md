---
name: salesforce-shield-architecture
description: "Salesforce Shield as an architectural choice — Platform Encryption + Event Monitoring + Field Audit Trail as three SEPARATELY-LICENSED components, none of which ship in any standard edition. Covers BYOK vs Cache-Only Key Service (CCKM) tradeoffs, probabilistic vs deterministic encryption schemes, the field-type encryption blocklist (Formula, Roll-Up Summary, indexed External ID), Field Audit Trail's 10-year retention model, and why every Shield design starts with a license confirmation. NOT for individual feature setup steps (see security/platform-encryption, security/event-monitoring, security/field-audit-trail), NOT for compliance certification mapping (HIPAA / FedRAMP / PCI specifics)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "salesforce shield license required which components"
  - "platform encryption probabilistic vs deterministic decision"
  - "byok cache-only key service cckm comparison"
  - "field audit trail retention 10 year configuration"
  - "shield platform encryption field types blocklist formula rollup"
  - "salesforce shield architecture compliance design"
tags:
  - shield
  - platform-encryption
  - event-monitoring
  - field-audit-trail
  - byok
  - cache-only-keys
  - compliance-architecture
inputs:
  - "Compliance driver (HIPAA, FedRAMP, PCI, internal policy) and which Shield components address it"
  - "Existing Salesforce edition and which Shield licenses are already provisioned"
  - "Field-level inventory of what must be encrypted vs filtered/sorted"
  - "Key-management posture (Salesforce-managed, BYOK upload, Cache-Only HSM)"
  - "Audit retention requirement in years"
outputs:
  - "Shield component selection (Platform Encryption / Event Monitoring / Field Audit Trail) with the matching license per component"
  - "Encryption scheme decision per field (probabilistic vs deterministic) tied to filter/sort requirements"
  - "Key management mode decision (Salesforce-managed / BYOK / Cache-Only) tied to compliance posture"
  - "Field Audit Trail retention policy XML for each archived object"
  - "License-confirmation pre-flight checklist that runs before any Shield Setup work"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-04
---

# Salesforce Shield Architecture

Shield is the wrong size of question to answer with "go to Setup → enable
encryption". It's three separately-priced add-on products — Platform
Encryption, Event Monitoring, Field Audit Trail — sold per-org, none
included in any standard edition. The architectural decision is *which
components, with what posture, against which fields*, and that has to
happen before anyone clicks anything in Setup.

This skill is the architectural decision layer. The setup mechanics for
each component live in their own skills:
`security/platform-encryption`, `security/event-monitoring`,
`security/field-audit-trail`. Compliance certification mapping
(specifically what HIPAA / FedRAMP-High / PCI require from Shield) lives
in a separate skill — Shield is *part* of the answer to those, not the
whole answer.

---

## Before Starting

- **Confirm every Shield license you're about to assume.** Setup → Company
  Information → Permission Set Licenses. Three distinct lines: Platform
  Encryption, Event Monitoring, Field Audit Trail. The most common
  Shield-architecture failure is recommending a feature against an org
  that doesn't have the license — a 3-month procurement cycle becomes
  visible in the design review, not afterwards.
- **Inventory the fields.** For each candidate-encryption field: data
  type (some types can't be encrypted at all), whether filter / sort /
  group-by is required, whether full-text search is required, and
  whether external IDs depend on it.
- **Decide the key-management posture before picking components.** A
  Cache-Only Key Service design has implications for every Shield
  component (single point of unavailability) — choosing it after
  picking components forces rework.
- **Decide retention up-front.** Field Audit Trail retention is set per
  object in metadata XML, with a maximum of 10 years. Plan storage
  cost and the 18-month-tier vs longer-tier transition.

---

## Core Concepts

### Shield's three components, each with its own license

| Component | What it does | License (separately purchased) |
|---|---|---|
| **Shield Platform Encryption** | At-rest encryption of selected fields, files, search indexes. Uses Salesforce-managed or customer-supplied keys. | `Platform Encryption` PSL |
| **Event Monitoring** | Hourly / real-time event log files (Login, API, Apex, Visualforce, etc.) and Real-Time Event Monitoring streams via Pub/Sub. Backs Transaction Security Policies for in-flight blocking. | `Event Monitoring` PSL |
| **Field Audit Trail** | Per-object configurable history retention up to 10 years; stores history rows in `FieldHistoryArchive` (queryable). Replaces the 18-month default `FieldHistory` retention. | `Field Audit Trail` PSL |

Standard Salesforce ships with **classic encryption** (a different
product — single-key, weaker, fewer field types) and **18-month field
history retention** in `<Object>History` (no separate license). Shield
upgrades both, plus adds Event Monitoring.

### Platform Encryption: probabilistic vs deterministic

The most consequential per-field decision under Shield Platform
Encryption. Salesforce supports two schemes:

| Scheme | Same plaintext → same ciphertext? | Filter / sort / group-by? | Strength |
|---|---|---|---|
| **Probabilistic** (default) | No (random IV per encryption) | Equality filter NO; sort NO | Stronger — ciphertext analysis cannot infer plaintext distribution |
| **Deterministic — case-sensitive** | Yes | Equality filter YES; sort YES (lexicographic on ciphertext) | Weaker — ciphertext frequency analysis is possible |
| **Deterministic — case-insensitive** | Yes (after case-fold) | Equality filter YES (case-insensitive); sort YES | Same as case-sensitive plus case-fold |

Deterministic is the only path if SOQL needs to filter or sort on the
encrypted field. Probabilistic is the right default for everything else.
You cannot change scheme on a populated field without re-encrypting
every row.

### Field types you cannot encrypt

The blocklist matters because authors often promise encryption of
fields that physically cannot be encrypted:

- **Formula** fields — encryption would break the formula evaluation engine.
- **Roll-Up Summary** fields — same reason; aggregation requires plaintext.
- **External ID fields with `Unique` checked AND backed by a unique index** — the unique index requires plaintext for collision detection.
- **Auto-Number** fields — generated server-side, value is the index.
- A handful of standard fields (`Id`, `IsDeleted`, `RecordTypeId`, etc.) — system fields.

If a field on the encryption candidate list is one of these, the
architectural answer is to encrypt the *underlying* field that the
formula / roll-up reads from, not the derived field.

### BYOK vs Cache-Only Key Service (CCKM)

The two customer-supplied-key models have very different operational
shapes:

| Mode | Key resides where? | Key fetch path | Outage impact |
|---|---|---|---|
| **Salesforce-managed** | Salesforce key infrastructure | Internal | Salesforce's standard reliability |
| **BYOK (tenant-secret upload)** | Salesforce, after upload from customer | Customer uploads key material; Salesforce derives data-encryption keys from it | Customer can rotate / destroy. Loss of key = loss of data |
| **Cache-Only Key Service (CCKM)** | Customer HSM (e.g. AWS CloudHSM, Azure Key Vault, on-prem) | Salesforce fetches just-in-time, holds in cache only | **Strongest posture; KMS outage causes encryption operations to FAIL** until cache or KMS is restored |

CCKM is the right answer for high-compliance shops (regulator-audited
key custody). BYOK is the right middle ground for "we want to control
rotation but don't want to operate an HSM for Salesforce traffic".
Salesforce-managed is fine for orgs whose compliance posture doesn't
require customer custody.

### Field Audit Trail retention

Not a single dial — set *per object* in metadata XML:

```xml
<HistoryRetentionPolicy>
    <archiveAfterMonths>18</archiveAfterMonths>
    <archiveRetentionYears>10</archiveRetentionYears>
    <description>HIPAA-archived patient records</description>
</HistoryRetentionPolicy>
```

`archiveAfterMonths` controls when records move from the standard
`<Object>History` table (queryable in reports) to `FieldHistoryArchive`
(queryable via SOQL only). `archiveRetentionYears` controls deletion
from the archive — capped at 10 years.

---

## Decision Guidance

| Situation | Approach | Reason |
|---|---|---|
| User asks "how do I turn on encryption?" before licensing is confirmed | **Stop.** Confirm `Platform Encryption` PSL first. | Telling them to go to Setup against a non-Shield org wastes a sprint. |
| Field needs SOQL `WHERE` equality filter AND must be encrypted | **Deterministic case-sensitive** (or case-insensitive if business requires) | Probabilistic blocks the filter |
| Field is a Formula / Roll-Up / Unique-Indexed-External-ID | **Encrypt the source field instead** | The derived field cannot be encrypted; encrypting the source flows the property through |
| HIPAA / FedRAMP / regulator-audited key custody | **CCKM** (Cache-Only Key Service) with customer HSM | Highest posture; KMS outage = encryption ops fail (acceptable trade) |
| Compliance requires customer-controlled rotation but no HSM operations | **BYOK** (tenant-secret upload) | Customer rotates / destroys; Salesforce holds the derived key |
| Internal policy, no specific regulator | **Salesforce-managed** keys | Lowest operational cost, still encrypted-at-rest |
| Audit retention needed > 18 months | **Field Audit Trail** with `HistoryRetentionPolicy` per object | Standard 18-month `History` retention is hard-capped |
| Real-time blocking of suspicious sessions / API calls | **Event Monitoring + Transaction Security Policies** | TSP is the only policy-driven block-in-flight mechanism |
| Need event log files but no real-time blocking | Event Monitoring **without** TSP — log-only mode | Cheaper to operate; many orgs don't need real-time |
| Asked for "everything Shield does" without a compliance driver | **Push back.** Shield is paid; per-component justification matters | Buying all three components without a driver is a budget smell |

---

## Recommended Workflow

1. **Pre-flight: license confirmation.** Permission Set Licenses page. Three lines, three independent purchases. If any is missing, the conversation pauses for procurement.
2. **Compliance driver inventory.** What forces Shield to be in scope (regulator, contract, internal control)? Map each requirement to the *minimum* Shield component that addresses it.
3. **Field inventory + scheme decision.** For Platform Encryption: list every candidate field with its filter / sort / search requirement; pick probabilistic vs deterministic per field. Identify any encryption-blocked field types and reroute to source fields.
4. **Key-management posture.** Salesforce-managed / BYOK / CCKM. Document the outage tradeoff for CCKM.
5. **Audit retention design.** For Field Audit Trail: per-object `HistoryRetentionPolicy` XML, with `archiveAfterMonths` and `archiveRetentionYears` decided per object.
6. **Event Monitoring scope.** Log-files-only vs Log-files + Real-Time Event Monitoring + Transaction Security Policies. Document which event types are subscribed and why.
7. **Cost projection.** Component licenses + key-management infrastructure (HSM if CCKM) + storage growth from Field Audit Trail archive.

---

## Review Checklist

- [ ] Three Shield licenses confirmed in Setup (or marked "not in scope" with rationale).
- [ ] Per-field encryption scheme matches filter / sort requirements.
- [ ] No field on the encryption list is a Formula / Roll-Up / unique-indexed External ID; if it was, the source field is encrypted instead.
- [ ] Key-management posture named (Salesforce-managed / BYOK / CCKM) with one-sentence rationale.
- [ ] CCKM design documents the HSM outage failure mode.
- [ ] Field Audit Trail retention XML present for every audited object; `archiveRetentionYears` ≤ 10.
- [ ] Event Monitoring scope explicit (which event types, log-only vs real-time).
- [ ] Total cost projection includes component licenses + HSM (if CCKM) + storage growth.

---

## Salesforce-Specific Gotchas

1. **Three Shield components, three separate licenses.** None included in any standard edition. Verify each PSL before any Setup work. (See `references/gotchas.md` § 1.)
2. **Probabilistic encryption blocks SOQL `WHERE` equality filters.** Deterministic supports equality filter (and sort). Wrong scheme = wrong queries. (See `references/gotchas.md` § 2.)
3. **Formula / Roll-Up / unique-indexed External ID cannot be encrypted.** Encrypt the source field instead. (See `references/gotchas.md` § 3.)
4. **Cache-Only Key Service outage = encryption operations fail.** A customer-HSM outage stops new writes that need encryption. Trade for the strongest custody posture. (See `references/gotchas.md` § 4.)
5. **Field Audit Trail retention requires metadata XML, not Setup UI.** `HistoryRetentionPolicy` is set per object via Tooling API or metadata deploy — not a checkbox. (See `references/gotchas.md` § 5.)
6. **Tenant secret rotation re-encrypts all data.** Plan the operation as a maintenance window for orgs with significant encrypted data volume. (See `references/gotchas.md` § 6.)
7. **Real-Time Event Monitoring is Pub/Sub-only as of recent releases.** Old code paths against the streaming-API channels are deprecated. (See `references/gotchas.md` § 7.)

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Shield Architecture Decision Document | License inventory, component selection, per-field scheme decisions, key-management mode, retention policy, Event Monitoring scope, cost projection |
| `HistoryRetentionPolicy` XML per audited object | Metadata payloads ready for deploy |
| Pre-flight license-confirmation runbook | Procurement gate before any Setup work |
| CCKM HSM availability runbook (if CCKM chosen) | Failure-mode response, KMS outage expected behavior |

---

## Related Skills

- `security/platform-encryption` — Setup mechanics for the Platform Encryption component (this skill ends where that one starts).
- `security/event-monitoring` — Setup for Event Monitoring + Real-Time Event Monitoring + Transaction Security Policies.
- `security/field-audit-trail` — Setup mechanics for the per-object retention policy.
- `security/byok-key-rotation` — Operational runbook for tenant-secret rotation and CCKM cache invalidation.
- `architect/hybrid-integration-architecture` — Adjacent decisions when Shield-encrypted data flows to AWS / Heroku / external systems.
