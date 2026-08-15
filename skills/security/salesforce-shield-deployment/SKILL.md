---
name: salesforce-shield-deployment
description: "Roll out Shield (Platform Encryption + Event Monitoring + Field Audit Trail) end-to-end, sequencing feature enablement to avoid data lockout. NOT for Classic Encryption or general PE design — use architect/salesforce-shield-architecture."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "shield rollout plan"
  - "enable event monitoring"
  - "field audit trail retention"
  - "shield encryption field by field"
tags:
  - shield
  - encryption
  - event-monitoring
  - fhr
inputs:
  - "Shield license"
  - "scoped field list"
  - "log retention SLA"
outputs:
  - "Rollout runbook with order of operations"
  - "validation report"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# Salesforce Shield Deployment

Shield is three separately-operated capabilities sold under one name:

> "Salesforce Shield is a trio of security tools that helps you build extra levels of
> trust, compliance, and governance right into your business-critical apps. It
> includes Shield Platform Encryption, Event Monitoring, and Field Audit Trail."
> — Salesforce Security Guide

They share nothing else. Different enablement paths, different permissions, different
failure modes, different rollback stories. Field Audit Trail is not even
self-service: "For information about enabling Field Audit Trail, contact your
Salesforce representative."

Deploying "Shield" as one project is the root cause of most bad Shield rollouts,
because each capability then interferes with the diagnosis of the others.

---

## Before Starting

1. **Confirm which of the three the compliance requirement actually needs.** They
   answer different questions: encryption at rest, forensic history, and detection.
   A programme that needs one and buys three still has to operate three.

2. **Validate the field scope against what can be tracked and encrypted.** Formula,
   roll-up, auto-number, long text, and multi-select fields cannot be
   history-tracked at all. Encryption has its own eligibility list. A scope written
   from a data dictionary will contain fields neither capability can cover.

3. **Establish the retention obligation's direction.** A *minimum* ("retain for
   seven years") is nearly free with Field Audit Trail. A *maximum* ("do not retain
   beyond seven years") requires a deletion process you build and schedule, because
   nothing deletes on your behalf.

4. **Name the log destination and the analyst.** Event Monitoring without a consumer
   and a person with the right permissions is a cost, not a capability.

---

## Core Concepts

### The three phases and why the order is what it is

```text
PHASE 1  Field Audit Trail       lowest risk; value is TIME-DEPENDENT
PHASE 2  Event Monitoring        read-only; the instrument for phase 3
PHASE 3  Platform Encryption     one object at a time; changes behaviour
```

FAT first because history not collected today cannot be bought later. Event
Monitoring second because it shows you what phase three changed. Encryption last
because it is the only capability that alters query semantics.

### Field Audit Trail retention is a mechanism, not a number

| Without FAT | With FAT |
|---|---|
| "retains field history data for up to 18 months, and up to 24 months via the API" | "retains archived field history data until you delete it" |
| 20 tracked fields per object | 200 tracked fields per object |

The policy is Metadata API, not Setup:

```xml
<historyRetentionPolicy>
    <archiveAfterMonths>18</archiveAfterMonths>   <!-- min 1, max 18, default 18 -->
    <archiveRetentionYears>7</archiveRetentionYears> <!-- a REMINDER; deletes nothing -->
    <gracePeriodDays>30</gracePeriodDays>          <!-- first archive only -->
    <description>Owner and requirement</description>
</historyRetentionPolicy>
```

Requires the `RetainFieldHistory` permission. Defaults when you deploy nothing: 18
months in production, **one month in sandboxes**, retained until deleted — and
"Salesforce doesn't include the default retention policy when you retrieve the
object's definition through Metadata API," so an empty retrieve is not evidence of no
policy.

Storage: "Field history tracking data and Field Audit Trail data don't count against
your data storage limits."

### The monitoring surfaces are not interchangeable

| Surface | Shape | Permission (login example) |
|---|---|---|
| Event Log File | CSV per event type per day | View Event Log Files |
| Event Log Objects | SOQL-queryable | View Real-Time Event Monitoring Data |
| Real-Time Event Monitoring | Streaming (`LoginEvent`, …) | View Real-Time Event Monitoring Data |
| Login History | Setup page and object | Manage Users |
| Enhanced Transaction Security | Policies with actions | — |

Three different permissions for the same question. An analyst granted one cannot use
the others.

### Encryption is not retroactive

Enabling a policy encrypts subsequent writes. Existing records stay in plaintext until
a re-encryption job runs and completes. Verify per object on Encryption Statistics.

### The cross-capability interaction

"If you turn on Platform Encryption, the previously archived data remains
unencrypted." History archived between phase one and phase three is permanently
unencrypted. State that position; do not let it be discovered.

---

## Common Patterns

### Pattern A — three phases, three gates

Each phase closes on evidence, not on enablement. FAT closes when
`FieldHistoryArchive` is populating and the policy is deployed; Event Monitoring
closes when an incident rehearsal has produced a timeline; encryption closes per
object when the query snapshot diff is clean.

### Pattern B — the incident rehearsal

A scripted investigation — "user X may have exported customer data at 02:00 last
Tuesday" — run end to end, recording how long each step took and what was missing.
The list of what was missing is the deliverable. Full script in
[`references/examples.md`](references/examples.md), Example 3.

### Pattern C — per-object encryption gate

Inventory filters and matching keys → decide drop / deterministic / do-not-encrypt →
snapshot expected results → enable → re-encrypt → verify → diff the snapshot. Example
4.

### Pattern D — explicit retention policy on every in-scope object

Deploy `historyRetentionPolicy` even where the default is acceptable, so the policy is
retrievable, reviewable, and diffable.

---

## Decision Guidance

| Situation | Approach |
|---|---|
| Compliance needs forensic before/after values | Field Audit Trail, after validating the fields are trackable |
| Compliance names a formula or roll-up field | Track its inputs — those field types cannot be tracked |
| Change is made by a Flow or trigger in system context | Field history may not record it — use Event Monitoring or a custom audit object |
| Requirement is "retain ≥ N years" | Deploy the policy and do nothing else; retention is unbounded |
| Requirement is "do not retain beyond N years" | Build and schedule a deletion process; nothing deletes on your behalf |
| Need detection within seconds | Real-Time Event Monitoring |
| Need bulk historical analysis | Event Log Files into a SIEM or data lake |
| Need to block an action in flight | Enhanced Transaction Security — and note the MFA action degrades to a block on mobile, Lightning Experience, and API |
| Field appears in a filter or matching key | Do not encrypt probabilistically — see `security/platform-encryption` |
| Data subject deletion | Delete the record **and** `FieldHistoryArchive` separately |

---

## Recommended Workflow

1. **Scope and validate**: confirm which capabilities the requirement needs, and
   check every named field against the trackability and encryption eligibility
   constraints before committing to it.
2. **Phase 1 — Field Audit Trail**: request enablement through your Salesforce
   representative, deploy an explicit `historyRetentionPolicy` per in-scope object,
   and gate on `FieldHistoryArchive` populating.
3. **Phase 2 — Event Monitoring**: onboard the log destination with a named retention
   period and alert conditions, define the analyst persona with all three
   permissions, and gate on a completed incident rehearsal.
4. **Phase 3 — Platform Encryption, one object at a time**: inventory filters and
   matching keys, snapshot expected query and report results, enable the policy for
   that object, run re-encryption to completion, verify on Encryption Statistics, and
   diff the snapshot before moving on.
5. **Record the cross-capability position**: that history archived before the
   encryption date is unencrypted, where it lives, and what compensating control
   covers it.
6. **Hand over the operational commitments**: the deletion process for a maximum
   retention obligation, the analyst persona and its permissions, and the
   re-encryption step that must accompany every future policy change.

---

## Review Checklist

- [ ] Plan has three phases with an evidence-based gate between each
- [ ] Field scope validated against untrackable field types before sign-off
- [ ] Automation-driven changes covered by something other than field history
- [ ] Explicit `historyRetentionPolicy` deployed on every in-scope object
- [ ] `archiveAfterMonths` within 1–18; `archiveRetentionYears` understood as a reminder
- [ ] Deletion process built and scheduled if the obligation is a maximum
- [ ] Log destination, retention period, alert conditions, and recipient all named
- [ ] Analyst persona holds View Event Log Files, View Real-Time Event Monitoring
      Data, and Manage Users
- [ ] Incident rehearsal completed, with the "what was missing" list captured
- [ ] Encryption enabled one object per change, each with a before/after snapshot
- [ ] Re-encryption completed and verified per object on Encryption Statistics
- [ ] Transaction security policies tested on Lightning, mobile, **and** API
- [ ] `FieldHistoryArchive` included in every data deletion runbook
- [ ] Unencrypted pre-encryption archive documented as a stated position

---

## Salesforce-Specific Gotchas

Full detail with quotes in [`references/gotchas.md`](references/gotchas.md).

1. **"Shield" is three products, not one switch** — and FAT is not self-service.
2. **FAT retention is "until you delete it," not ten years.**
3. **`archiveAfterMonths` caps at 18 months.**
4. **The default retention policy is invisible to Metadata retrieve** — and the
   sandbox default is one month, not 18.
5. **Whole field categories cannot be history-tracked**, and >255-character fields
   are tracked without values.
6. **FAT data does not count against storage** — costing it as storage is a category
   error.
7. **Deleting a record does not delete its archived history.**
8. **Enabling encryption does not encrypt already-archived history.**
9. **The same question has three homes with three different permissions.**
10. **Transaction Security's MFA action silently becomes a block** on mobile,
    Lightning Experience, and API.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Phased rollout runbook | Three phases with the evidence each gate requires, and the owner of each |
| Validated field scope | Every in-scope field checked against trackability and encryption eligibility, with the substitution where it failed |
| Retention policy metadata | Explicit `historyRetentionPolicy` per object, plus the deletion process if the obligation is a maximum |
| Monitoring onboarding record | Destination, retention, alert conditions, recipient, analyst persona and its three permissions |
| Incident rehearsal report | The timeline produced, the elapsed time per step, and the list of what was missing |
| Per-object encryption evidence | Filter inventory, before/after query snapshot diff, and Encryption Statistics confirmation |
| Stated compliance positions | Unencrypted pre-encryption archive; any field the scope named that could not be covered |

---

## Related Skills

- `security/platform-encryption` — the field-by-field encryption decision:
  deterministic versus probabilistic, and what each breaks
- `security/shield-kms-byok-setup` — where the tenant secret comes from, and the
  rotation and destruction runbooks
- `security/event-monitoring` — the monitoring surfaces in depth, and the SIEM
  pipeline this deployment depends on
- `security/field-audit-trail` — the retention policy and `FieldHistoryArchive`
  querying in depth
- `security/customer-data-request-workflow` — the deletion path that must include
  `FieldHistoryArchive`
