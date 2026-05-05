---
name: flow-time-based-patterns
description: "Time-based execution in Salesforce Flow — Scheduled Paths in record-triggered flows (delays measured against a record date or trigger fire time), the Wait element in autolaunched / orchestration flows, scheduled flows that run on a cron-like cadence, and the time-zone rules that decide when 'tomorrow at 9 AM' actually fires. Covers the offset semantics (`+N` days vs `-N` days from a date field), the requeueing behavior on the source record changing, and the workflow-rule-time-based-action replacement playbook. NOT for the basic `Decision` or `Loop` element (that's plain Flow), NOT for Apex `System.scheduleBatch` (different runtime, see apex/scheduled-apex)."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "flow scheduled path record triggered delay"
  - "flow wait element pause time-based"
  - "scheduled flow cron weekly nightly"
  - "workflow rule time based action migration to flow"
  - "flow scheduled path time zone confusion"
  - "scheduled path record changed cancel reschedule"
tags:
  - flow
  - scheduled-path
  - wait-element
  - scheduled-flow
  - time-based
  - workflow-replacement
inputs:
  - "Trigger source: record change (record-triggered flow), schedule (scheduled flow), or in-flow pause (Wait element in orchestration / autolaunched)"
  - "Delay basis: from now, from a record date field, or from a fixed cron expression"
  - "Time zone the user / record / org operates in"
  - "Whether the source record can change after scheduling (and what should happen if so)"
outputs:
  - "Time-based execution choice (Scheduled Path vs Wait vs Scheduled Flow)"
  - "Offset configuration (`+N hours/days/months` from `<date field>` or `<flow runtime>`)"
  - "Time-zone resolution decision (running user's vs org default vs UTC)"
  - "Re-evaluation behavior on source-record change (cancel / let it fire / reschedule)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-04
---

# Flow Time-Based Patterns

Time-based logic in Flow has three distinct mechanisms, each with
different runtime semantics, governor scope, and time-zone behavior.
Confusing them — using a Wait element in a scheduled flow, or
expecting a Scheduled Path to re-evaluate when the source record
changes — produces some of the most confused-debug Flow incidents.

What this skill is NOT. The basic Flow elements (Decision, Loop,
Get / Create / Update Records) work the same way regardless of
time-based wrappers — go to Salesforce help. Apex's
`System.scheduleBatch` and `Schedulable` interface live in a different
runtime — see `apex/scheduled-apex`. The classic Workflow Rule
time-based-action migration story is covered here as one specific
pattern, not the topic of the whole skill.

---

## Before Starting

- **Identify which mechanism actually fits.** Scheduled Paths fire
  off a record-trigger event (record save). Scheduled Flows fire on
  a cron expression independent of any record. Wait elements pause
  a running flow interview. They look similar; they're not
  interchangeable.
- **Decide the time-zone basis.** Scheduled Paths use the **running
  user's** time zone for "9 AM". Scheduled Flows use the **org's
  default** time zone. Wait elements in screen flows depend on the
  user's session time zone. Mixing assumptions is the most common
  time-zone bug.
- **Decide what happens if the source record changes.** Scheduled
  Paths can be configured to cancel-and-reschedule when the trigger
  condition is no longer met (re-evaluation on update). Default is
  "let it fire as scheduled".

---

## Core Concepts

### The three time-based mechanisms

| Mechanism | Where it fires | Trigger | Time-zone basis |
|---|---|---|---|
| **Scheduled Path** in a record-triggered flow | Async, after the record-trigger fires | Record save matching the trigger criteria + a configurable delay | Running user (the user who saved the record) |
| **Scheduled Flow** | Async, on a cron expression | Cron schedule (org-defined) — daily, weekly, hourly, etc. | Org default |
| **Wait Element** | Pauses an autolaunched / orchestration flow interview | Configurable resume condition (absolute time, duration, platform event) | Depends on the resume-condition specification |

A record-triggered flow can have BOTH an immediate path and one or
more Scheduled Paths off the same trigger. A Wait element doesn't
exist in record-triggered flows — only autolaunched and orchestration.

### Scheduled Path offset semantics

A Scheduled Path runs at: *base date* + *offset*. The base date can
be:

- **Trigger fire time** — the moment the record-save fired the flow.
  Offset is `+N hours` / `+N days` / etc.
- **A field on the triggering record** — e.g. `Opportunity.CloseDate`
  or `Case.SLA_Expiration_Time__c`. Offset can be positive (after
  the date) or negative (before the date — useful for "send a
  reminder 2 days BEFORE the SLA").

Negative-offset paths against a date field that's already in the past
fire **immediately** (the platform considers the scheduled time
already past).

### Re-evaluation on update: the most-misunderstood feature

Default behavior: a Scheduled Path that was queued at trigger fire
time stays queued. If the triggering record is updated to no longer
meet the entry criteria, the Path **still fires** unless re-evaluation
is configured.

Configuring re-evaluation: the Scheduled Path's "Recheck the entry
condition" toggle. When enabled, the platform re-evaluates the
record's state against the entry criteria at the moment the Path
runs. If the criteria no longer matches, the Path silently exits.

This matters for "send a reminder 2 days before SLA expiration" — if
the case is closed before the reminder fires, recheck-on-execution
prevents sending an irrelevant reminder.

### Time zone: the silent landmine

| Mechanism | Time zone resolves as |
|---|---|
| Scheduled Path "+N days at 9 AM" | The **running user's** time zone — the user who saved the record |
| Scheduled Flow on a cron schedule | The **org default** time zone |
| Wait element in a screen flow | The user's **session** time zone (often same as running user, but not guaranteed) |
| `DateTime` literal in a Decision element | UTC unless explicitly converted |

A Scheduled Path on a global team's record-triggered flow fires at
9 AM in **each user's** time zone — meaning records saved in EMEA
fire at 9 AM London, records saved in APAC fire at 9 AM Tokyo. For
some workflows that's correct (regional reminders); for others
(e.g. a global SLA cutoff) it's wrong.

The fix: store the desired fire time in UTC on a record field and
use field-based offset, OR move the logic to a Scheduled Flow that
uses the org default.

---

## Common Patterns

### Pattern A — Send a reminder before a date field

**When to use.** "Email the case owner 2 days before
Case.SLA_Expiration_Time__c — but only if the case is still open."

**Implementation.**

- Record-triggered flow on `Case` after-save with criteria
  `Status != 'Closed' AND SLA_Expiration_Time__c != null`.
- Scheduled Path: `-2 days` from `SLA_Expiration_Time__c`.
- Recheck entry condition: ENABLED. If the case closes before the
  reminder fires, the Path silently exits.

The reminder body uses Action: Send Email Action. Standard fault path
on the email send (see `flow/flow-error-notification-patterns`).

### Pattern B — Cancel-and-reschedule on field change

**When to use.** SLA expiration changed by an admin or escalation
process — the original Scheduled Path should be cancelled and a new
one queued from the new date.

**Implementation.** Salesforce does not expose direct cancel/reschedule
of an already-queued Scheduled Path. Workaround:

- Record-triggered flow with isChanged() criteria on the date field.
- The flow's Scheduled Path uses recheck-on-execution to verify the
  date hasn't changed since queue time.
- Stamp a `Last_Reminder_Sent_For_SLA_At__c` field; the Scheduled
  Path's recheck criteria includes
  `Last_Reminder_Sent_For_SLA_At__c < SLA_Expiration_Time__c` so a
  changed date renders the queued Path invalid.

The actually-firing Path checks state at execution time and silently
exits if the world has changed.

### Pattern C — Scheduled Flow for periodic batch work

**When to use.** "Every weekday at 6 AM, find all open cases with
SLA breach risk and email the owners."

**Implementation.**

- Scheduled Flow with cron expression `0 0 6 ? * MON-FRI`.
- Get Records on Case with criteria.
- Loop / collection process / send emails.
- Time-zone basis: org default.

Scheduled Flows have a per-execution governor scope independent of
the record-triggered flow that might also touch the same records.
Don't try to do per-record work that should have been a Scheduled
Path on the record-triggered flow.

### Pattern D — Wait element for in-flow pause

**When to use.** Autolaunched flow that needs to pause until a
specific time or until a Platform Event fires.

```
[Get Records: pull tasks]
    │
    ▼
[Wait: until Platform Event 'Approval_Decision__e' OR 24 hours]
    │
    ├── on event resume → process approval
    │
    └── on timeout → escalate
```

Wait elements support:
- **Absolute time** — pause until a specified DateTime.
- **Duration** — pause for N hours / days.
- **Platform Event** — pause until a matching event fires (with
  optional filter).

**Constraint.** Wait elements are **only** available in autolaunched
and orchestration flows. They cannot exist in record-triggered or
screen flows.

### Pattern E — Workflow-rule time-based-action migration

**When to use.** Migrating a classic Workflow Rule with a time-based
action (e.g. "if SLA breached, escalate after 4 hours") to Flow.
Salesforce has been deprecating Workflow Rules; this pattern is
common.

**Mapping.**

| Workflow Rule concept | Flow equivalent |
|---|---|
| Rule trigger | Record-triggered flow's start |
| Rule criteria | Flow's entry criteria |
| Time-based queue | Scheduled Path |
| Re-evaluation rule | Recheck entry condition on the Path |
| Workflow action (field update / email / outbound msg) | Flow Action: Update Records / Send Email / Action |

**Common mistake:** the workflow rule's "evaluate when records are
created and any time they're edited" maps to record-triggered flow's
**Run when a record is created or updated**. Forgetting this leaves
the new flow firing only on create.

---

## Decision Guidance

| Situation | Approach | Reason |
|---|---|---|
| "Run X 2 days after this case is created" | Scheduled Path on record-triggered flow, +2 days from trigger fire | Standard pattern |
| "Run X 2 days BEFORE this case's SLA" | Scheduled Path with -2 days from SLA field, recheck enabled | Negative offset against record date field |
| "Run X every weekday at 6 AM" | Scheduled Flow with cron expression | No record trigger; cron-driven |
| "Pause until approval comes in" | Wait element in autolaunched flow with Platform Event resume | Interactive wait |
| "User saved a record but I want the path to fire at the org's 9 AM not the user's" | Move the work to a Scheduled Flow | Scheduled Paths use running-user TZ |
| "If the record changes after queueing, cancel the path" | Recheck entry condition on the Scheduled Path | Default is no recheck; explicit toggle |
| Migrating a classic Workflow Rule with time-based actions | Pattern E mapping | Standard migration playbook |
| "My Wait element doesn't appear in my record-triggered flow" | **You can't add Wait there** — use Scheduled Path | Wait is autolaunched / orchestration only |
| "Negative offset against a past date" | Path fires immediately | Past scheduled times execute immediately |

---

## Recommended Workflow

1. **Pick the mechanism.** Scheduled Path / Scheduled Flow / Wait — not interchangeable.
2. **Decide the base time and offset.** Trigger fire time vs record date field vs cron expression.
3. **Resolve the time zone explicitly.** Running user, org default, or UTC. Document the choice.
4. **Decide re-evaluation behavior.** For Scheduled Paths: "Recheck entry conditions" toggle. Default off; almost always you want it on.
5. **Build it.** Standard Flow Builder.
6. **Test the time-zone case.** Save a record as a user in a different time zone. Confirm the Path fires at the expected absolute time.
7. **Test the recheck case.** Update the source record between queue and execution; confirm recheck behavior.

---

## Review Checklist

- [ ] Mechanism (Scheduled Path / Scheduled Flow / Wait) matches the requirement.
- [ ] Base time and offset are documented.
- [ ] Time zone of execution is named explicitly (running user / org default / UTC).
- [ ] Recheck-entry-condition is configured if the source record can change.
- [ ] Negative-offset path against a past date is acceptable behavior (immediate fire).
- [ ] Wait elements are only used in autolaunched / orchestration flows.
- [ ] Test plan covers the time-zone edge case (user in non-default TZ).
- [ ] Fault path exists per `flow/flow-error-notification-patterns`.

---

## Salesforce-Specific Gotchas

1. **Scheduled Path uses the running user's time zone, not the org's.** A "9 AM" path means 9 AM in EACH saving user's local time. (See `references/gotchas.md` § 1.)
2. **Scheduled Path with negative offset against a past date fires immediately.** "2 days before Aug 1" against a case saved on Aug 5 fires now, not nothing. (See `references/gotchas.md` § 2.)
3. **Recheck entry condition is OFF by default.** A queued Scheduled Path fires even if the source record no longer meets the entry criteria. (See `references/gotchas.md` § 3.)
4. **Wait elements are NOT available in record-triggered flows.** They're autolaunched / orchestration only. (See `references/gotchas.md` § 4.)
5. **Scheduled Flows use the org-default time zone, not the configurer's.** "Daily at 6 AM" means 6 AM in the org's TZ, regardless of who set up the flow. (See `references/gotchas.md` § 5.)
6. **Cancelled / deleted source record while a Scheduled Path is queued** — the Path still fires; recheck condition that includes IsDeleted handles deleted records. (See `references/gotchas.md` § 6.)
7. **Migrating Workflow Rule "evaluate every time a record is edited"** maps to Flow's **Run when a record is created or updated**, not just create. (See `references/gotchas.md` § 7.)

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Time-based mechanism choice | Scheduled Path / Scheduled Flow / Wait, with rationale |
| Offset configuration | Base time + signed offset (e.g. `-2 days from SLA_Expiration_Time__c`) |
| Time-zone documentation | Which TZ resolves the schedule, and why that's correct for the requirement |
| Recheck-entry-condition decision | On / off, with explanation of what changes between queue and execution |
| Test matrix | Time-zone edge case + recheck edge case + negative-offset edge case |

---

## Related Skills

- `flow/flow-error-notification-patterns` — every time-based path needs a fault-handling design.
- `apex/apex-event-bus-subscriber` — when a Wait element resumes on a Platform Event; the Apex side of the same Pub/Sub channel may also subscribe.
- `apex/scheduled-apex` — when the requirement is high-volume cron-driven work that exceeds Flow governors.
- `flow/flow-orchestration-patterns` — Flow Orchestration's stage / step model also uses Wait elements but with different visibility and persistence.
