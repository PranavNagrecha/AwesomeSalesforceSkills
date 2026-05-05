---
name: flow-error-notification-patterns
description: "Fault-path design and error notification for Salesforce Flow — what the default unhandled-fault email contains, when to add a Fault path explicitly, how `$Flow.FaultMessage` works, and how to route errors to a real notification channel (email alert, Apex-published Platform Event, custom log object) instead of relying on the org-default 'apex exception email recipient'. Covers the ordering rule (Fault path on every callout / DML / record-create-or-update), the difference between a screen-flow user-visible error and a record-triggered-flow silent failure, and how to suppress noisy expected-rejection paths. NOT for the basic 'how do I add a Fault connector' (use Salesforce help), NOT for Apex-trigger errors (different runtime, see apex/apex-exception-handling)."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "flow fault path email recipient configuration"
  - "flow unhandled fault apex exception recipient"
  - "$flow.faultmessage fault path screen flow"
  - "record-triggered flow silent failure debug"
  - "flow error custom log platform event notification"
  - "flow fault on screen flow vs record-triggered"
tags:
  - flow
  - fault-path
  - error-handling
  - notification
  - platform-event
  - error-log
inputs:
  - "Flow type (screen / record-triggered before-save / record-triggered after-save / scheduled / autolaunched / orchestration)"
  - "User audience (admin / agent / external community user / no human at all)"
  - "Whether failures are programmer errors (must alert someone) or expected business outcomes (silent / log-only)"
  - "Existing error-notification channels available (email, Slack, custom log object, monitoring tool)"
outputs:
  - "Fault path placement decision per element"
  - "Notification channel mapping per error category"
  - "`$Flow.FaultMessage` rendering decision (screen flows only)"
  - "Suppression rules for expected-rejection paths so noise doesn't drown out real errors"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-04
---

# Flow Error Notification Patterns

Default Salesforce Flow error handling is a single config field: the
"apex exception email recipient" set in Setup → Process Automation →
Process Automation Settings. Every unhandled fault — across every
flow in the org — ends up in that user's inbox as a plain-text dump
of the flow interview state. For a small org with one admin, fine.
For anything past that, it's the wrong shape: noisy, undifferentiated,
slow-to-triage, with no per-flow severity or owner.

This skill is about replacing that default with a deliberate
fault-path + notification design — what to alert on, who to alert,
through which channel, and how to suppress expected rejections so
they don't drown the real signal.

What this skill is NOT. The mechanic of adding a Fault connector to
a Flow element is plain Flow Builder; consult Salesforce help. Apex
trigger error handling is a different runtime — see
`apex/apex-exception-handling`. This skill covers the *design* layer
on top of those mechanics.

---

## Before Starting

- **Identify the audience for each flow.** Screen flow = the user
  sees the error inline. Record-triggered before-save = the user's
  DML transaction fails with a translated error. Record-triggered
  after-save / scheduled / autolaunched = there is no user; failure
  is silent unless someone is notified.
- **Decide what counts as an error vs an expected outcome.** A
  validation rejection is not an error — it's a business outcome.
  A callout timeout is an error. Treating both the same way produces
  inbox flood.
- **Identify the notification channel(s) you have.** Email alert,
  Slack via webhook, Platform Event subscribed by an Apex monitoring
  class, custom `Flow_Error_Log__c` object, observability platform
  ingest. Each has different latency, retention, and triage
  ergonomics.

---

## Core Concepts

### What the default unhandled-fault email actually contains

When a Flow element fails and there's no Fault path, Salesforce sends
a plain-text email to the configured "apex exception email recipient"
containing:

- Flow API name + version
- The element that failed
- Error code + error message (often a SOQL or DML governor message)
- Full interview state — every variable's value at the moment of
  failure (often hundreds of lines)

This is debuggable but not actionable. There's no severity, no owner,
no grouping by flow, no trend visibility. For org-wide scale it's a
flood; for narrow problems it's invisible (a single error email gets
lost in 50 unrelated ones).

### Fault path semantics

Every flow element that can fail (Get Records, Create Records,
Update Records, Action / callout, Delete Records, Loop with
sub-elements) supports a Fault connector. The Fault path:

- Catches the error from that element only.
- Exposes `$Flow.FaultMessage` — a string with the platform's error
  description.
- Continues flow execution along whatever you connect from the Fault
  path.
- **Does NOT propagate the error up.** The flow does NOT fail; it
  branches to the Fault path. If the Fault path itself succeeds,
  the flow ends "successfully" from the platform's perspective —
  the unhandled-fault email is suppressed.

That last point is critical. A common mistake is "I added a fault
path that does nothing" — yes, and now the platform thinks the flow
succeeded, no email fires, and the failure is invisible.

### `$Flow.FaultMessage`

Available inside any Fault path. Contains the error string from the
failing element. Useful in screen flows to show the user what went
wrong:

```
"We couldn't save your changes: {!$Flow.FaultMessage}"
```

In non-screen flows (record-triggered, scheduled, autolaunched),
`$Flow.FaultMessage` is what you log to your notification channel.
Without capturing it, the Fault path has no idea why the parent
element failed.

### Differentiating real errors from expected business rejections

A validation rule rejecting a DML inside a flow IS a fault from the
flow's perspective. But it's not an error from the user's perspective
— it's the system telling them their input is wrong. Treating both
the same way means:

- The user sees a generic "An unexpected error occurred" instead of
  the validation message.
- The admin gets a flood of fault emails for legitimate user input.

The fix is to differentiate inside the Fault path. The
`$Flow.FaultMessage` string contains the validation rule's error
message verbatim — you can detect "VALIDATION" / known business
rejection patterns and route those to a user-facing display, while
unknown errors go to the alert channel.

---

## Common Patterns

### Pattern A — Default-org behavior is wrong; replace with custom error log

**When to use.** Any org with more than one production flow.

**Setup.**

1. Create a custom object `Flow_Error_Log__c` with fields: `Flow_Name__c`, `Element__c`, `Fault_Message__c`, `Record_Id__c`, `User__c`, `Severity__c`.
2. Create a sub-flow `Log_Flow_Error` that takes those fields as input variables and creates a `Flow_Error_Log__c` record.
3. In every production flow, add a Fault path on every fault-capable element. Each Fault path calls `Log_Flow_Error` with the element name, `$Flow.FaultMessage`, the record being processed, and a severity.
4. Build a report on `Flow_Error_Log__c` filtered by recent + high-severity. Subscribe admins.

This is more setup than "set the org-default email recipient" but it
gives:
- Per-flow / per-element grouping in reports.
- Severity that actually means something (admin sets it, not the
  platform).
- Long-term retention — the org-default email goes to inbox; the log
  is queryable for trend analysis.

### Pattern B — Screen flow with user-visible error and silent admin notification

**When to use.** Screen flow where the user should see what went
wrong (validation message, missing data) AND the admin should be
notified asynchronously of programmer-error cases (failed callout,
governor limit hit).

```
[Get Records / DML / Action]
    │
    ├── Success → next element
    │
    └── Fault → [Decision: is this a known business rejection?]
                    │
                    ├── Yes → [Display Text: "Couldn't save: {!$Flow.FaultMessage}"]
                    │           → Screen ends with user-visible error.
                    │
                    └── No (programmer error) →
                            ├── [Action: Publish Flow_Error_Event__e]
                            └── [Display Text: "An unexpected error occurred. Admins have been notified."]
```

The user sees a friendly "couldn't save" or a generic "we've been
notified". The admin's monitoring subscriber catches the
Platform Event for programmer-error cases only.

### Pattern C — Record-triggered after-save: Platform Event for async notification

**When to use.** A record-triggered after-save flow that updates
related records or publishes events; failure is silent to the user
and must be caught.

**Why Platform Event** instead of direct email or `Flow_Error_Log__c`
insert: a Platform Event is durable, triggers an Apex subscriber that
can decide alert routing (email vs Slack vs PagerDuty vs queue), and
keeps the flow's transaction clean — even if the alert delivery is
slow, the flow doesn't wait.

**Approach.**

1. Define `Flow_Error_Event__e` with fields `Flow_Name__c`, `Element__c`, `Fault_Message__c`, `Record_Id__c`.
2. Apex subscriber on the Platform Event routes to the right channel based on `Flow_Name__c`.
3. Every Fault path in record-triggered flows publishes the event.

The flow doesn't know or care whether the alert went to Slack, email,
or both — that's the Apex subscriber's call.

### Pattern D — Suppressing expected-rejection paths

**When to use.** A validation rule that rejects bad input is the
intended behavior; without suppression, every rejection produces a
fault-email or log entry, drowning real signal.

**Approach.** Inside the Fault path, decision element checks
`$Flow.FaultMessage` against known business-rejection patterns
(validation rule errors typically contain `FIELD_CUSTOM_VALIDATION_EXCEPTION`
or the validation rule's error message verbatim). Match → display to
user, do NOT log. No match → log + alert.

```
Fault → [Decision]
            │
            ├── $Flow.FaultMessage CONTAINS "FIELD_CUSTOM_VALIDATION_EXCEPTION"
            │       → [Display Text: "{!$Flow.FaultMessage}"]
            │       → screen ends; not logged
            │
            └── otherwise (programmer error)
                    → log to Flow_Error_Log__c + display generic message
```

The validation messages still reach the user as the user-friendly
error; the alerting channel only fires on unknown errors.

---

## Decision Guidance

| Situation | Approach | Reason |
|---|---|---|
| Org has only the org-default "apex exception email recipient" | **Replace with Pattern A** | Default is a flood; custom log is queryable, groupable, retainable |
| Screen flow with mixed user error + programmer error potential | **Pattern B** with decision branch | User sees actionable error; admin only alerted on programmer errors |
| Record-triggered after-save flow doing callouts / DML | **Pattern C** with Platform Event | Async, durable, decouples flow from alert delivery |
| Scheduled flow that runs nightly | **Pattern A or C** with severity = high | No user; silent failure is the failure mode |
| Autolaunched flow called from process-builder or other flow | **Pattern A** by default; **C** if high-volume | Caller's context decides whether user is in scope |
| Validation rule rejection is expected | **Pattern D suppression** inside Fault | Don't drown signal with expected-rejection noise |
| Sub-flow that's reused across many parent flows | **Sub-flow logs once with parent flow name** | Each parent passes its name as input variable so logs are attributed correctly |
| Flow Orchestration runs (multi-stage) | Same patterns; **alert at stage boundary** | Stages can run for hours/days; per-step alerting is too noisy |
| Org has Slack / PagerDuty / observability tooling | **Platform Event subscriber routes** | Don't hardcode the channel in the flow |

---

## Recommended Workflow

1. **Inventory production flows** that have no Fault paths. Default-behavior orgs have many.
2. **Build the `Flow_Error_Log__c` object + `Log_Flow_Error` sub-flow** (Pattern A) once per org.
3. **For screen flows:** add Fault paths with the decision branch from Pattern B.
4. **For record-triggered / scheduled / autolaunched:** add Fault paths that log + (optionally) publish a Platform Event (Pattern C).
5. **Build the suppression list** of expected-rejection patterns (Pattern D) in the decision element.
6. **Subscribe admins to a daily / hourly digest** report on the error log object — not real-time on every error, which is its own flood.
7. **Audit periodically:** pull the last 30 days of error log; identify flows with the most errors and address root causes.

---

## Review Checklist

- [ ] Every fault-capable element (Get / Create / Update / Delete / Action / callout) has a Fault path.
- [ ] Fault paths capture `$Flow.FaultMessage` — they don't just silently swallow.
- [ ] Screen flows differentiate user-visible business rejections from programmer errors.
- [ ] Non-screen flows publish to a Platform Event or write to `Flow_Error_Log__c`.
- [ ] Expected-rejection patterns are documented and suppressed from the alert channel.
- [ ] No flow ends with a "do-nothing" Fault path that silently succeeds.
- [ ] Admin notification cadence is digested (daily / hourly), not per-event.
- [ ] Org-default "apex exception email recipient" is set to a fallback inbox, not the primary alert channel.

---

## Salesforce-Specific Gotchas

1. **A "do-nothing" Fault path silently succeeds the flow.** No email, no log, no signal — failure is invisible. (See `references/gotchas.md` § 1.)
2. **Default unhandled-fault email contains the entire interview state** as plain text — easy hundreds of lines of irrelevant variable values. (See `references/gotchas.md` § 2.)
3. **`$Flow.FaultMessage` is empty in some contexts.** The Fault path's surrounding element type matters. (See `references/gotchas.md` § 3.)
4. **Screen flow Fault paths that don't display anything to the user produce a blank screen.** The user thinks the screen broke. (See `references/gotchas.md` § 4.)
5. **Record-triggered before-save flow Fault paths can't send email synchronously** without governor limit risk. Use a Platform Event or `Flow_Error_Log__c` insert. (See `references/gotchas.md` § 5.)
6. **`Send Email Action` inside a Fault path** can throw its own fault, which has no further fault path — the secondary failure is unhandled. (See `references/gotchas.md` § 6.)
7. **Validation rule errors and DML faults look identical to the platform.** Differentiation requires inspecting the message string. (See `references/gotchas.md` § 7.)

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `Flow_Error_Log__c` custom object + fields | Single-org log target for non-screen-flow errors |
| `Log_Flow_Error` sub-flow | Reusable log-the-error step that every Fault path can invoke |
| `Flow_Error_Event__e` Platform Event + Apex subscriber | Async routing layer for orgs with multiple alert channels |
| Suppression-pattern list | Documented validation / business-rejection patterns that don't trigger alerts |
| Daily digest report | Subscribers see grouped error log, not per-event alerts |

---

## Related Skills

- `flow/flow-best-practices` — broader Flow design (this skill is the error-handling chapter).
- `apex/apex-exception-handling` — Apex trigger error handling (different runtime; the same `Flow_Error_Log__c` object can serve both if you generalize the schema).
- `apex/apex-event-bus-subscriber` — when the alert channel uses a Platform Event with an Apex subscriber.
- `admin/email-templates-and-alerts` — when the chosen channel is email and the template is the styling decision.
