# Idempotent Integration Patterns — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `idempotent-integration-patterns`

**Request summary:** (fill in what the user or integration team asked for)

---

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here before proceeding.

- **Integration direction:** [ ] Inbound (external → Salesforce) [ ] Outbound (Salesforce → external) [ ] Bidirectional
- **Transport mechanism:** [ ] REST API upsert [ ] Bulk API v2 upsert [ ] Platform Events [ ] Outbound Messages [ ] Custom HTTP callout
- **Stable unique identifier available from external system:** [ ] Yes — field name: _____________ [ ] No — must design surrogate
- **Current retry strategy:** (describe what happens when the integration fails today)
- **Platform Event Publish Behavior (if applicable):** [ ] PublishImmediately (default — must change) [ ] PublishAfterCommit (correct)
- **Known governor limit exposures:** (e.g., volume per day, concurrent callout limits)
- **Idempotency key storage location (for outbound callouts):** (record field name, Platform Cache key, or external store)

---

## Approach

Which pattern from SKILL.md applies? Check all that apply and describe the specific configuration.

- [ ] **Pattern 1 — External ID Upsert for Inbound Sync**
  - Target sObject: _____________
  - External ID field name: _____________
  - Field type: [ ] Text [ ] Number [ ] Email
  - `externalId=true`: [ ] Yes [ ] No (must add)
  - `unique=true`: [ ] Yes [ ] No (must add)
  - Upsert endpoint: `PATCH /services/data/vXX.0/sobjects/{Object}/{ExternalIdField}/{Value}`

- [ ] **Pattern 2 — Platform Event Subscriber with ReplayId Checkpoint**
  - Platform Event API name: _____________
  - Publish Behavior: [ ] PublishAfterCommit (correct) [ ] PublishImmediately (must change)
  - Checkpoint object name: _____________
  - Checkpoint written: [ ] After processing (correct) [ ] Before processing (anti-pattern)
  - Subscriber duplicate guard: [ ] External ID upsert in subscriber body [ ] Existence check before insert

- [ ] **Pattern 3 — Persisted Idempotency Key for Outbound Callouts**
  - Driving record object: _____________
  - Key field name: _____________
  - Key generation location: [ ] At enqueue time (correct) [ ] At callout time (anti-pattern)
  - External system's idempotency header/field: _____________
  - Key TTL / scope per external system docs: _____________

---

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] External ID field is present, marked `externalId=true`, and marked `unique=true` on all target sObjects
- [ ] Platform Event "Publish Behavior" is set to "Publish After Commit" for all events used in transactional patterns
- [ ] Idempotency keys for outbound callouts are generated once at enqueue time and persisted to a durable store before the first attempt
- [ ] Platform Event subscriber stores ReplayId checkpoint after successful processing, not before
- [ ] Subscriber processing logic is itself idempotent (uses upsert or existence check before DML)
- [ ] Retry scenario tested end-to-end: same payload sent twice produces one record, not two
- [ ] Error handling for `MULTIPLE_CHOICES` (300) and `DUPLICATE_VALUE` is in place with alerting

---

## Configuration Notes

Document any non-standard settings or decisions made during implementation.

| Setting | Expected Value | Actual / Decision | Notes |
|---|---|---|---|
| Platform Event Publish Behavior | PublishAfterCommit | | |
| External ID field unique constraint | true | | |
| Idempotency key field name | e.g., `Callout_Idempotency_Key__c` | | |
| ReplayId checkpoint object | e.g., `Event_Replay_Checkpoint__c` | | |
| Key generation location | Enqueue path only | | |

---

## Deviations from Standard Pattern

Record any deviations from the SKILL.md recommended patterns and the justification:

| Deviation | Justification | Risk | Mitigating Control |
|---|---|---|---|
| (describe) | (why) | (what could go wrong) | (how mitigated) |

---

## Test Evidence

| Test Scenario | Expected Result | Actual Result | Pass / Fail |
|---|---|---|---|
| Send same inbound payload twice | Single record; no duplicate | | |
| Retry outbound callout with same key | External system returns cached response; no duplicate action | | |
| Platform Event subscriber restarts mid-stream | Resumes from last ReplayId checkpoint; no skipped events | | |
| Publishing transaction rolls back | No event delivered to subscriber | | |

---

## Notes

(Record any additional context, edge cases, or open questions.)
