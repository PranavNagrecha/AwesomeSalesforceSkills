---
name: flow-error-monitoring
description: "Set up monitoring + alerting for Flow runtime errors at org scale: routing fault emails, Flow runtime error reports, custom centralized logging (Application_Log__c), escalation thresholds, and trend detection. Also covers the fault-connector-to-central-log convention every flow follows, the paused and failed interview backlog (FlowInterview InterviewStatus, CurrentElement, PauseLabel), active-vs-latest version drift (FlowDefinitionView IsOutOfDate), triage SLAs and ownership, and how to test the monitoring path itself. Triggers: 'flow error monitoring', 'paused flow interviews backlog', 'FlowDefinitionView IsOutOfDate', 'flow error dashboard shows zero errors', 'who receives flow error emails', 'audit flows with no fault path'. NOT for diagnosing a specific flow error — use flow/flow-runtime-error-diagnosis. NOT for debug-mode setup — use flow/flow-debugging. NOT for designing the fault connector itself — use flow/fault-handling."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
tags:
  - flow
  - monitoring
  - alerting
  - error-reports
  - integration-log
  - ops
  - dashboards
  - paused-interviews
  - version-drift
  - application-log
triggers:
  - "flow error monitoring"
  - "flow fault email routing"
  - "flow runtime error report"
  - "centralized flow error logging"
  - "flow error dashboard"
  - "flow error alerting ops"
  - "set up monitoring so we know when a flow fails in production"
  - "route flow error emails to an ops alias instead of the person who edited the flow last"
  - "find every paused or failed flow interview in the org"
  - "build a report of flow errors over the last seven days"
  - "detect flows whose active version is not the latest version"
  - "audit which flows have no fault path writing to a central log"
  - "our flow health dashboard shows zero errors but flows are failing"
  - "alert on-call when a flow fails more than five times in an hour"
  - "test that the fault path actually writes a log record"
  - "decide how fast we must respond to a flow failure and who owns it"
  - "clear the backlog of paused flow interviews"
  - "prove the monitoring we deployed is actually running"
inputs:
  - Flow portfolio scope (single org, org set, multi-business-unit)
  - Flow types present — record-triggered, screen, scheduled, autolaunched
  - Volume of flow executions per day
  - Existing observability stack (Splunk, Datadog, etc.)
  - Whether Apex already writes to a central log object
  - SLA for error response, and who is on the hook per severity band
outputs:
  - Fault-email routing policy with the Flow.settings and ApexEmailNotifications files that implement it
  - Fault-connector-to-central-log convention, and a checker that measures coverage of it
  - Paused and failed interview backlog query with triage ownership
  - Version-drift query (active version vs latest version)
  - Runtime error report + alerting rule set with thresholds per severity
  - A FlowTest proving the fault route is reached, and the manual step that proves the row was written
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Flow Error Monitoring

This skill activates when the question is **"how would we know?"** rather than "why did this
one fail?". It designs the monitoring architecture for a flow portfolio in production: where
errors surface, the one convention every flow follows so they surface in the same place, the
backlogs that accumulate when nobody looks, and the SLA that says who looks.

**This skill owns the architecture, not the diagnosis.** Neighbouring skills own the surfaces
and the fixes, and this package cross-references them rather than restating them:

| It is really about | Go to |
|---|---|
| Reading a debug log to localise one failure to one element | `flow/flow-debugging` |
| Designing the fault connector and the rollback scope on one flow | `flow/fault-handling` |
| What a specific error code or fault email message means | `flow/flow-runtime-error-diagnosis` |
| `Flow.settings` as org policy — who may change it, how it is reviewed | `flow/flow-governance` |
| Quietening a noisy channel, or choosing email vs Slack vs event | `flow/flow-error-notification-patterns` |
| Paused screen-flow interview state and resume mechanics | `flow/flow-interview-debugging` |
| `ApplicationLogger`, `Log_Event__e`, and publish behaviour | `apex/debug-and-logging` |
| Test strategy, path matrices, coverage targets | `flow/flow-testing` |

---

## Before Starting

| Context | Why it matters |
|---|---|
| Flow types in the portfolio | `FlowInterviewLog` is the **screen-flow** log. A record-triggered portfolio monitored through it reports zero errors indefinitely. |
| Who receives flow error email today | The documented default recipient is the user who last modified the flow — not an owner, not an admin, not an alias. |
| Whether Apex already writes to a central log | If `Application_Log__c` exists, flows write to it. A second log object splits the correlation surface. |
| Target org type | Production deploys flows **inactive** by default. A green deploy is not coverage. |
| Bulk exposure | Data loads and scheduled paths turn one fault into hundreds. Whether alerting aggregates is a design decision, not a tuning one. |
| Who can act on a paused interview | Deleting one needs the Manage Flow permission; resuming a shared one depends on an org setting. A backlog nobody can clear is a report, not a process. |

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| **Who receives this org's flow error emails today, and was that a decision?** | Unless `Flow.settings` says otherwise, they go to the last person who modified each flow. In an org with 80 flows that is 80 uncoordinated destinations, some belonging to people who have left. | Turns "we get too many emails" into a two-file change with a named owner — and reveals the failures nobody has been receiving. See gotcha 1. |
| **Which flow types are in scope, and does anything currently rely on `FlowInterviewLog`?** | It decides whether the existing reporting is measuring anything. The object is documented for screen flow interviews only. | Stops a green dashboard being cited as evidence of health, and re-points the report at `FlowInterview` plus your own sink. See gotcha 2 and `references/examples.md` Example 2. |
| **Where does a fault-path row go, and does Apex already write there?** | One sink is queryable, correlatable and reportable. Two sinks are two half-monitored portfolios that need a join nobody has written. | Reuse of `templates/apex/custom_objects/Application_Log__c` and its `Request_Id__c` correlation, instead of a new object invented on the spot. See gotcha 3. |
| **What does the severity picklist actually contain, and what will the flows send?** | The canonical `Severity__c` is `required` **and** `restricted`. A flow assigning `'Error'` instead of `'ERROR'` makes the fault-path write itself fault, and then nothing is logged at all. | A matched vocabulary, so the sink cannot silently reject the rows it exists to hold. See gotcha 3. |
| **Who is allowed to resume or delete a paused interview, and is that the same team that reads the backlog?** | Deletion requires Manage Flow; resuming an interview you do not own depends on `enableFlowInterviewSharingEnabled`. There is no `update()` on the object, so triage state has to live somewhere else. | A backlog with an owner who can actually clear it, and a decision about where "reviewed" is recorded. See gotchas 10 and 11. |
| **What is the response target per severity band, and who is on the hook?** | Alerting thresholds are meaningless without them. "Page on CRITICAL" only means something once someone has agreed what CRITICAL is and what happens at 3am. | The severity table in `templates/flow-error-monitoring-template.md` §4, filled in — which is the artefact the on-call rota is built from. See gotcha 14. |
| **How will we know the monitoring itself has stopped working?** | The most common silent failure is not a flow error — it is monitoring that deployed inactive, a report subscription lost in a sandbox refresh, or a fault path whose own log write faults. | A verification step and a coverage check that run on a schedule, not a one-off deploy confirmation. See gotchas 5 and 7. |

**What a proper configuration adds over just doing it:** one queryable sink that every flow
writes to the same way, a checker that proves which flows do and do not, and a named owner per
severity band — so the first sign of a broken flow is a row in a report on Monday rather than
a customer call in March.

---

## Core Concepts

### The Five Surfaces, and What Each One Cannot Do

A monitoring design chooses deliberately among these. Four are given to you and cover no more
than the first hour of an incident; the fifth is the only one you control.

| Surface | Grounded at | Best for | Blind spot |
|---|---|---|---|
| **Error email** | `api_meta.txt` L116961–L116967, L22415–L22417 | Day-one coverage with nothing built | One message per fault; recipient is the last modifier by default |
| **`FlowInterview`** | `object_reference.txt` L139861 | Live state — paused, failed, which element, `Error` text (API 62.0+) | It is state, not history; no `update()` call |
| **`FlowInterviewLog`** | `object_reference.txt` L140059 | Screen-flow interview history | **Screen flows only**; View All Data by default |
| **Debug log `FLOW_*` events** | `apexdev.txt` L38792, L38821 | Exact element, exact limit usage, one run | Prospective and short-lived — `flow/flow-debugging` owns it |
| **Custom log object** | `templates/apex/custom_objects/Application_Log__c` | History, trend, threshold alerting, ownership | Only exists where a fault connector was wired |

### The One Convention

Every fault-capable element in every flow routes its `faultConnector` to a Create Records on
the org's single log object, with the same five fields. That is the whole convention, and it
is the thing this skill is actually asking for:

| Field | Value | Why it is not optional |
|---|---|---|
| `Source__c` | flow API name | The only durable "which flow"; the report groups on it |
| `Flow_Element__c` | element API name | Narrows to a line without a debug log |
| `Message__c` | `$Flow.FaultMessage` (see the marker in `references/metadata-examples.md` §1) | `LongTextArea`, so nothing is truncated |
| `Related_Record_Id__c` | `$Record.Id` | Turns a count into something reproducible |
| `Running_User__c` | `$User.Id` | Permission-shaped failures are invisible without it |
| `Severity__c` | one of `DEBUGL` / `INFOL` / `WARN` / `ERROR` / `FATAL` | `required` and `restricted` — the wrong string makes the log write fault |

`flow/fault-handling` owns *how* to build the connector. This skill owns the fact that all of
them go to the same place, in the same shape, and that a script can prove it.

### Subflows Are the Hole in the Convention

`FlowSubflow` has a `connector` and **no `faultConnector`** (`api_meta.txt` L72625–L72660),
unlike every other fault-capable node type. A convention applied only to top-level flows
therefore leaves every subflow silent. Instrument inside the subflow. Gotcha 13 has the
detail and the guide lines.

### Two Backlogs That Accumulate Quietly

**Paused and failed interviews.** `FlowInterview.InterviewStatus` is a restricted picklist
with the documented values `Completed`, `Error`, `Paused`, `Running`, `VersionPaused`
(`object_reference.txt` L139956–L139971). `Expired` belongs to `FlowInterviewLog`, not here
(gotcha 9). `CurrentElement` tells you where each one is stuck; `interviewLabel`, set at
design time, is the only thing that makes the list readable.

**Version drift.** `FlowDefinitionView.IsOutOfDate` "indicates whether the active flow version
is the latest version of the flow definition" (`object_reference.txt` L139405–L139412). A
`true` row is an ops team reading version 7's fault paths while version 5 runs. Do not reach
for `FlowVersionView` to enumerate versions org-wide — it returns nothing unless filtered
(gotcha 6).

Both queries are in `references/metadata-examples.md` §5.

---

## Common Patterns

### Pattern 1 — The sink, reused rather than invented

`templates/apex/custom_objects/Application_Log__c.object-meta.xml` and its `fields/` already
ship `Source__c`, `Message__c` (`LongTextArea` 32768), `Severity__c`, `Request_Id__c`
(external Id), `Running_User__c`, `Stack_Trace__c`, `Exception_Type__c` and `Quiddity__c`.
Flow monitoring adds exactly two fields — `Flow_Element__c` and `Related_Record_Id__c`
(`references/metadata-examples.md` §2).

Reusing it means one query answers "what is failing in this org", across Apex and Flow, keyed
on `Request_Id__c`. `apex/debug-and-logging` owns the Apex side and the `Log_Event__e`
variant for failures that must survive a rollback.

### Pattern 2 — Fault route to sink, alerting on the sink

```
[Update Records / Action / Get Records]
        │ faultConnector
        ▼
[Create Records: Application_Log__c]   ← unconditional, no notification here
        ▼
      [End]

                     … and separately, on the log object itself:

[Record-triggered flow on Application_Log__c, after save, Severity In (ERROR, FATAL)]
        ▼
[Get Records: same Source__c in the last N minutes]
        ▼
[Decision: count > threshold?] ── yes ──▶ [Action: notify] ──▶ [End]
```

The fault path never notifies. Aggregation lives between the fault and the channel, which is
what keeps a 200-record data load from producing 200 messages (gotcha 14).
`templates/flow/FaultPath_Template.md` is the baseline for the top half.

### Pattern 3 — The report, and what is not deployable with it

A `Report` on the log object, `format` `Summary`, grouped by `Source__c`, filtered to
`ERROR`/`FATAL` — the XML is in `references/metadata-examples.md` §6. What ships with it:
the report, and the folder. What does not: the subscription that mails it. No metadata type
in `api_meta.txt` carries a report subscription, so it is manual configuration with a named
owner and a line in `templates/flow-error-monitoring-template.md` §6.

### Pattern 4 — Coverage as a measurement, not a memory

"Which flows are instrumented" is a checker output over the source tree, not a list someone
maintains:

```bash
python3 scripts/check_flow_error_monitoring.py --manifest-dir force-app/main/default --strict
```

`fault-sink-unreachable` walks every `faultConnector` and reports flows whose fault routes
never reach a Create Records on the log object. `log-write-unusable` catches the log write
that exists but omits the flow name or the fault message. Run it in CI; a portfolio's
instrumentation decays silently otherwise.

### Pattern 5 — Severity bands, and what each one buys

| Severity | Channel | Aggregation | Response target |
|---|---|---|---|
| `FATAL` | page on-call | none — inline | agreed in advance, in the design record |
| `ERROR` | threshold alert from the log object | N in a window | next business day |
| `WARN` | scheduled review of the report | daily | weekly triage |
| `INFOL` / `DEBUGL` | none | — | queried on demand during an investigation |

The bands are only real once §4 of `templates/flow-error-monitoring-template.md` is filled in
with names. `flow/flow-error-notification-patterns` owns the channel choice within a band.

### Pattern 6 — External observability, pushed not pulled

Where Splunk or Datadog already exists, publish from the log object rather than polling
Salesforce on a schedule. The event's `publishBehavior` decides what survives a rollback:
`PublishAfterCommit` is dropped when the transaction fails, `PublishImmediately` is not
(`api_meta.txt` L42206–L42227). `apex/platform-events-apex` and `apex/debug-and-logging` own
the event design; do not define a second error event here.

---

## Decision Guidance

| Situation | Start with | Reason |
|---|---|---|
| No monitoring at all, need coverage today | `apexEmailNotifications`, then `Flow.settings` | Zero build, and it is a safety net under everything built later — but deploy the recipients first |
| Dashboard shows zero errors, flows are failing | Check whether it is built on `FlowInterviewLog` | Screen-flow-only scope is the most common cause of a falsely clean report |
| Too many emails, nobody reads them | Aggregation on the log object, not channel suppression | Suppression discards the count, and the count is the finding |
| "Which flows are unmonitored?" | `check_flow_error_monitoring.py --strict` | The only answer that stays true after the next commit |
| Interviews stuck and nobody knows why | `FlowInterview` on `InterviewStatus` + `CurrentElement` | `PauseLabel` is user-entered and null for scheduled paths |
| Flow behaves unlike the version in the repo | `FlowDefinitionView.IsOutOfDate` | Active version is not the latest version more often than teams expect |
| Deploy succeeded, still no log rows | `IsActive` on `FlowDefinitionView` | Production deploys flows inactive by default |
| One specific failure needs a root cause | `flow/flow-debugging` | This skill tells you it happened; that one tells you why |
| Fault path exists but writes nothing | The `Severity__c` value being assigned | A restricted, required picklist rejects an unmatched string and the log write faults |

---

## Recommended Workflow

1. **Establish the recipient of record, in this order.** Deploy `apexEmailNotifications` with
   real recipients **first**, then `Flow.settings` with `enableFlowUseApexExceptionEmail` set
   to `true` (`references/metadata-examples.md` §3 and §4). The reverse order points flow
   error email at an empty list, which is worse than the default. Note the replace-on-deploy
   behaviour in gotcha 8 before touching a file `apex/debug-and-logging` also owns.
2. **Fix the sink before instrumenting anything.** Confirm `Application_Log__c` exists, add
   `Flow_Element__c` and `Related_Record_Id__c` (§2), and read
   `templates/apex/custom_objects/fields/Severity__c.field-meta.xml` so the flows assign a
   value the restricted picklist accepts.
3. **Instrument one flow end to end and prove it.** Use §1 as the shape: every
   fault-capable element's `faultConnector` to one Create Records, all six field mappings,
   `interviewLabel` carrying the record Id. Force a real fault and read the row back — an
   empty `Message__c` means `$Flow.FaultMessage` did not resolve, which is the one marked
   assumption this convention rests on.
4. **Measure the rest of the portfolio instead of listing it.** Run
   `python3 scripts/check_flow_error_monitoring.py --manifest-dir <src> --strict` and work the
   `fault-sink-unreachable` and `log-write-unusable` findings. Remember subflows carry no
   `faultConnector` and must be instrumented from the inside.
5. **Stand up the two backlogs and give them an owner.** The paused/failed interview query and
   the `IsOutOfDate` drift query from §5, on a schedule, with the names filled into
   `templates/flow-error-monitoring-template.md` §4 and §5. A backlog whose owner cannot
   delete an interview — Manage Flow — is a report, not a process.
6. **Build the report and the threshold flow, then record what is not deployable.** The
   `Report` XML in §6, plus the aggregating flow on the log object from Pattern 2. Log the
   subscription and any paging integration in §6 of the design record as manual configuration
   that a sandbox refresh will destroy.
7. **Test the monitoring path itself.** The `FlowTest` in §7 with `HasError` proves the fault
   route is reached; the log row read back proves it was written. Say which artefact supports
   which claim, and verify `IsActive` in the target org before calling any of it live.

---

## Review Checklist

- [ ] `apexEmailNotifications` recipients deployed **before** `enableFlowUseApexExceptionEmail` was set to `true`
- [ ] The org has exactly one error-log object, and Apex writes to the same one
- [ ] `Severity__c` values assigned by flows match the restricted picklist exactly
- [ ] Every fault-capable element in every in-scope flow routes to that sink — proved by the checker, not by inspection
- [ ] Subflows are instrumented internally, since a Subflow element has no `faultConnector`
- [ ] The fault path itself sends no notification; a threshold flow on the log object does
- [ ] `interviewLabel` on any flow with waits or scheduled paths carries the record Id
- [ ] Paused/failed interview backlog has an owner who holds Manage Flow
- [ ] Version-drift query runs on a schedule and `IsOutOfDate = true` rows are triaged
- [ ] Response target and owner recorded per severity band, with names
- [ ] Report subscription and any paging integration recorded as manual, re-created after a refresh
- [ ] A forced fault produced a non-empty `Message__c` row in the target org
- [ ] `IsActive` confirmed in the target org after the production deploy
- [ ] `check_flow_error_monitoring.py --strict` exits 0

---

## Salesforce-Specific Gotchas

Fourteen documented behaviours with guide line ranges are in `references/gotchas.md`. The
three that most often make a monitoring design a placebo:

1. **`FlowInterviewLog` is the screen-flow log.** A record-triggered portfolio monitored
   through it reports zero errors forever, and the report is technically correct.
2. **Production deploys flows inactive by default.** A successful deploy is evidence that
   metadata landed, never that a fault path runs.
3. **The fault path's own log write can fault.** A `required`, `restricted` `Severity__c` and
   an unmatched string is the usual cause, and it produces exactly nothing.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Recipient fences | `Flow.settings` and `apexEmailNotifications` files, deployed in that order, with an owner |
| Instrumented flow | A record-triggered flow whose every fault-capable element routes to one Create Records on the sink |
| Sink extension | `Flow_Element__c` and `Related_Record_Id__c` on the canonical `Application_Log__c` |
| Backlog queries | Paused/failed `FlowInterview` and `FlowDefinitionView.IsOutOfDate`, scheduled, with owners |
| Monitoring report | `Report` XML on the log object, plus a written note of the non-deployable subscription |
| Threshold flow | A record-triggered flow on the log object that applies the alerting rule |
| Coverage report | `check_flow_error_monitoring.py --strict` output over the source tree |
| Design record | `templates/flow-error-monitoring-template.md`, filled in — severity bands, owners, unverified assumptions |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | You are building the artefacts: the instrumented flow, the two additive log fields, the `Flow.settings` and `ApexEmailNotifications` fences, the backlog and drift SOQL, the monitoring `Report`, the `FlowTest`, `package.xml`, deploy order and verification. |
| `references/gotchas.md` | The dashboard is clean and the org is not, the deploy succeeded and nothing logs, or a query returns an empty set you are about to believe. Fourteen platform behaviours with guide line ranges. |
| `references/llm-anti-patterns.md` | You are reviewing generated monitoring advice — ten failure modes, including invented `FlowExecutionErrorEvent` fields and unfiltered `FlowVersionView` queries reported as "no drift found". |
| `references/examples.md` | You want the design walked through three real situations: the drowned inbox, the falsely clean dashboard, and the 200-alert data load. |
| `references/well-architected.md` | You are arguing about one sink versus many, inline versus threshold alerting, or need the sourced claim behind a statement in this package. |
| `templates/flow-error-monitoring-template.md` | You are recording the design: scope, org fences, severity bands with owners, coverage runs, what is not deployable, and the assumptions you still have to verify. |
| `scripts/check_flow_error_monitoring.py` | Before every deploy and in CI — six rules over the metadata tree, from unreachable fault sinks to a log object that would truncate the message. |

---

## Related Skills

- **flow/fault-handling** — owns fault-connector design, `$Flow.FaultMessage` capture and rollback scope on one flow. This skill only requires that every one of them ends at the same place.
- **flow/flow-debugging** — owns the diagnostic method and reading `FLOW_*` debug-log events. Go there once monitoring has told you which flow and when.
- **flow/flow-runtime-error-diagnosis** — owns what a specific error code or fault email message means.
- **flow/flow-error-notification-patterns** — owns channel choice and quietening an already-noisy one. This skill decides that aggregation sits between the fault and the channel.
- **flow/flow-governance** — owns `Flow.settings` as policy, naming, versioning discipline and retirement. Reference its values; do not restate them here.
- **flow/flow-interview-debugging** — owns paused screen-flow interview state and resume mechanics.
- **flow/flow-versioning-strategy** — owns what to do about an `IsOutOfDate = true` row once monitoring has surfaced it.
- **flow/flow-testing** — owns test strategy and coverage. This skill borrows one negative test.
- **apex/debug-and-logging** — owns `ApplicationLogger`, `Application_Log__c`, `Log_Event__e` and publish behaviour. Flows write to its object rather than a second one.
- **apex/platform-events-apex** — owns the event design when errors must reach an external observability platform.
- **admin/reports-and-dashboards** — owns report and dashboard construction beyond the single monitoring report defined here.
