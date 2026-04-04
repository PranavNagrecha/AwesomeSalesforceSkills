---
name: pause-elements-and-wait-events
description: "Use this skill when designing or troubleshooting flows that need to suspend execution and wait for an external signal — either a time-based alarm or a platform event. Trigger keywords: pause element, wait element, flow interview suspension, alarm event, platform event resume, async interview. NOT for scheduled flows that recur on a fixed schedule (use scheduled-flows), and NOT for record-triggered flow scheduled paths on a single record (those are set in the Start element, not a Pause element)."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Operational Excellence
triggers:
  - "flow needs to wait for an email reply before continuing the process"
  - "how to pause a flow interview until a specific date or time offset from a field"
  - "flow should resume when a platform event message arrives with matching data"
  - "approval reminder flow that waits multiple days before sending a follow-up"
  - "how to use the wait element or pause element in a Salesforce flow"
  - "paused flow interview is consuming async interview storage or hitting limits"
  - "difference between scheduled path and pause element in record-triggered flow"
tags:
  - pause-element
  - wait-element
  - wait-events
  - alarm-event
  - platform-event-resume
  - async-interviews
  - flow-interview-persistence
  - time-based-flow
inputs:
  - "Flow type (record-triggered, auto-launched, or screen flow)"
  - "Resume trigger: time-based (alarm) or event-driven (platform event)"
  - "For alarms: the Date or DateTime field or literal date to offset from, offset unit and value, and whether business hours apply"
  - "For platform events: the platform event API name and the field filter criteria to match the correct event message"
  - "Whether the paused interview needs to capture data from the resuming event message"
  - "Expected volume of concurrent paused interviews in the org"
outputs:
  - "Configured Pause (Wait) element with correctly typed wait events and resume conditions"
  - "Decision logic distinguishing scheduled path vs. pause element usage"
  - "Guidance on async interview storage impact and limit monitoring approach"
  - "Fault path recommendations for error handling during the paused state"
  - "Testing approach for paused interviews that cannot be stepped through in debug"
dependencies:
  - scheduled-flows
  - auto-launched-flow-patterns
  - fault-handling
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Pause Elements and Wait Events

Use this skill when a flow must suspend its interview — stop mid-execution and persist state — until either a calendar condition or an external platform event signals it to continue. The skill covers the Pause element (also referred to as the Wait element in the Flow Builder UI across releases), wait event types, resume conditions, interview persistence mechanics, storage limits, and testing patterns.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Flow type:** Pause elements are supported in auto-launched flows and screen flows. Record-triggered flows support a simpler time-based continuation through Scheduled Paths in the Start element — that does NOT suspend an interview, it schedules a new execution. If the requirement is event-driven or requires carrying state across multiple time windows in the same interview, a Pause element in an auto-launched flow is required.
- **Process Automation Settings:** For screen flows with user-initiated pauses, "Let Users Pause and Resume Flows" must be enabled in Process Automation Settings. This setting does not apply to auto-launched flows that pause via the Pause element.
- **Async interview storage:** Every paused interview is serialized and written to the database, consuming Async Interview storage (counted against Data Storage). Orgs have an org-wide limit on active paused and waiting interviews. For most editions this limit has historically been 2,000 (Unlimited Edition: 4,000). Starting Summer '25 (release 250), Salesforce began removing this limit; verify the current state for the target org edition.
- **Wait event types available:** Alarm (time-based) and Platform Event (event-driven). A single Pause element can contain multiple wait events and resumes on whichever condition fires first.

---

## Core Concepts

### Concept 1: The Pause Element Suspends, Persists, and Resumes the Same Interview

When a flow reaches a Pause element, the running interview is serialized and written to the database. Execution halts completely — no CPU, DML, or SOQL limits are consumed during the paused state. The interview resumes in a new transaction when its resume condition is satisfied. All variable values set before the Pause element are preserved across the pause boundary.

This is fundamentally different from a scheduled path on a record-triggered flow's Start element: scheduled paths do not suspend an existing interview; they enqueue a new flow execution at the specified future time. There is no variable state continuity across a scheduled path boundary.

### Concept 2: Wait Event Types — Alarm vs. Platform Event

**Alarm wait event:** Resumes the interview at a calculated date and time.

- **Base date:** A Date or DateTime field on a record in the flow scope, or an absolute literal date/time.
- **Offset:** A positive integer (or zero) with unit Hours, Days, or Months applied to the base date.
- **Business hours:** Optionally restrict so the alarm only fires during configured org business hours. If the calculated time falls outside business hours, the alarm fires at the next valid window.
- **Minimum offset:** The alarm cannot fire sooner than approximately 15 minutes after the interview is paused. An offset of 0 days does not mean "immediately" — expect a minimum ~15-minute delay.

**Platform Event wait event:** Resumes the interview when a matching event message is received.

- You select the platform event object (API name).
- Resume conditions act as field-value filters on the incoming event message (e.g., `CaseId__c = {!recordId}`). All conditions must evaluate to true for the interview to resume.
- An optional record variable can be bound to capture the full event message payload — field values from the event become available to the flow after resume.
- Delivery order between platform event-triggered flows and paused flow interviews subscribed to the same platform event is not guaranteed.

### Concept 3: Resume Conditions and Multi-Event Pauses

A single Pause element can hold multiple wait events. The interview resumes on the first event whose conditions are satisfied — a first-wins race. Each wait event has its own output connector so the flow can branch based on which event fired. This is the basis of the multi-day reminder pattern: add an Alarm for a Day 3 reminder, another Alarm for Day 7 escalation, and a Platform Event as an immediate-response path — the interview resumes on whichever arrives first and takes the corresponding branch.

### Concept 4: Fault Paths and Interview Invalidation

A paused interview can enter a fault or invalid state under these conditions:

- A new flow version is activated while interviews are paused on the old version. Depending on the scope of changes, paused interviews may fail to resume or resume unexpectedly.
- A DML or other error occurs when the interview attempts to resume. Fault connectors on the Pause element's output paths can catch these.
- The Salesforce record that the interview is scoped to is deleted while the interview is paused (relevant for record-triggered flows).

Administrators can view, manage, and delete paused interviews at Setup > Flows > Paused and Failed Flow Interviews.

---

## Common Patterns

### Pattern 1: Multi-Day Approval Reminder with Escalation

**When to use:** An approval request is created and the approver must act within a defined window. If no action is taken within N days, the flow sends a reminder; if still unanswered after another period, it escalates to a manager.

**How it works:**

1. An auto-launched flow is triggered when the approval request record is created (record-triggered or invoked via process).
2. Send an initial notification using a Custom Notification or Email Alert element.
3. Add a Pause element with two Alarm wait events:
   - Alarm A: base date = `{!ApprovalRequest.CreatedDate}`, offset = 3 days. Output path: send reminder email, then loop back to another Pause.
   - Alarm B: base date = `{!ApprovalRequest.CreatedDate}`, offset = 7 days. Output path: send escalation email to manager.
4. Add a third Platform Event wait event (`ApprovalDecision__e`) with resume condition `RequestId__c = {!recordId}` to exit the loop immediately when the approver acts.
5. After any path, use a Get Records to check current approval status; if resolved, end the flow; otherwise re-enter the Pause loop.

**Why not the alternative:** A scheduled path on a record-triggered flow cannot maintain state across multiple time windows. You would need multiple flows with inter-flow coordination logic. A single auto-launched flow with Pause elements handles multi-window state cleanly in one unit.

### Pattern 2: Event-Driven Handoff — Flow Waits for External System Confirmation

**When to use:** A flow initiates an outbound integration call (via External Services, Apex, or an HTTP callout), then must wait for an asynchronous callback confirmation before continuing — rather than polling.

**How it works:**

1. Auto-launched flow invokes the external callout and stores a correlation ID returned by the external system in a flow variable (`{!correlationId}`).
2. Add a Pause element with one Platform Event wait event:
   - Event: `IntegrationCallback__e`
   - Resume condition: `CorrelationId__c = {!correlationId}` — ensures only the callback for this specific request resumes this interview.
   - Bind a record variable (`{!callbackPayload}`) to capture the full event message (status, error code, response fields).
3. Add a second Alarm wait event as a timeout: offset = 24 hours from current time. Output path: handle timeout (log fault, notify, compensate).
4. After the platform event resume path, branch on `{!callbackPayload.Status__c}` for success vs. failure handling.

**Why not the alternative:** Polling requires a scheduled flow or Apex scheduled job with repeated SOQL queries, introduces polling interval lag, and adds complexity. A platform event-driven resume reacts within seconds of the external system publishing its callback event, with no wasted queries.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Record-triggered flow must run logic N days after a field value changes | Scheduled Path on the Start element | Purpose-built for single time-based continuation; no async interview storage consumed |
| Flow must suspend and wait for an external system callback or human event signal | Pause element with Platform Event wait event | Only mechanism that can suspend and resume on an external event signal |
| Flow must send reminders at multiple future time intervals with state continuity | Pause element with multiple Alarm wait events in auto-launched flow | Multiple time windows with variable preservation; scheduled paths cannot carry state |
| Screen flow user needs to save progress and return later | User-initiated pause via Save for Later | Handled via Process Automation Settings and the Paused Interviews panel, not the Pause element |
| Org is at or near the paused interview limit | Reduce concurrent interviews; consider scheduled flows or Apex async patterns | The limit is org-wide and affects all flows; no per-flow override exists |
| Platform event delivery order relative to other subscribers is critical | Pause element + ordered publish/confirm pattern | Platform event delivery order across subscribers is not guaranteed |

---

## Recommended Workflow

1. **Confirm flow type and use-case fit.** Verify the flow is auto-launched or a screen flow. Determine whether a Scheduled Path on a record-triggered flow's Start element already covers the need (single time-based continuation with no state preservation requirement) before adding a Pause element.
2. **Identify the resume trigger type.** Determine if the resume is time-based (Alarm) or event-driven (Platform Event). For alarms: identify the base date field and offset amount and unit. For platform events: confirm the platform event API name and the specific field-filter resume conditions that uniquely identify the correct event message.
3. **Design the Pause element and wait events.** In Flow Builder, add a Pause element. Add each wait event type. For platform events, define resume conditions that precisely filter the correct event message — do not leave resume conditions blank. Bind a record variable to the event if the payload is needed downstream.
4. **Add fault paths and timeout watchdogs.** Connect the Fault connector from the Pause element to an error-handling subflow or notification element. For platform event waits, add an Alarm wait event as a timeout to prevent interviews from being stranded indefinitely.
5. **Validate async interview volume.** Estimate peak concurrent paused interviews. Check Setup > Paused and Failed Flow Interviews for current counts. If volume may approach the org limit, align with the Salesforce admin on a monitoring and cleanup plan before deployment.
6. **Test each resume path manually.** Pause elements cannot be stepped through in Flow Builder debug mode — the debugger skips them. Use a short alarm offset (~15 minutes) for alarm testing, or publish a test platform event via Developer Console `EventBus.publish()` or Workbench to verify platform event resume paths.
7. **Review version activation risk.** Before activating a new flow version, check for any paused interviews on the current version at Setup > Paused and Failed Flow Interviews. Coordinate activation during a maintenance window when paused interview counts are low to minimize invalidation risk.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Flow type is auto-launched or screen flow — not a record-triggered flow where a scheduled path would suffice
- [ ] Each Platform Event wait event has at least one resume condition field filter to prevent stray events from resuming the wrong interview
- [ ] Alarm base date field is always populated on the record at the time the interview will be paused
- [ ] Fault path is connected from the Pause element and routes to a meaningful error handler (not left unconnected)
- [ ] A timeout Alarm wait event is present alongside any Platform Event wait event to prevent permanently stranded interviews
- [ ] Async interview storage impact has been estimated and confirmed against current org limits
- [ ] Testing plan does not rely on Flow Builder debug — uses real event triggers or manual event publication
- [ ] Flow version activation strategy accounts for any currently paused interviews

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Activating a new flow version can invalidate in-progress paused interviews** — When you activate a new version of a flow, interviews that are paused on the old version may fail to resume or resume incorrectly. This causes silent data loss in long-running flows. Always check for paused interviews before activating a new version and time activations for low-pause-count windows.
2. **Platform event wait event with no resume conditions resumes on every matching event** — Leaving resume conditions blank means every published message of that event type attempts to resume every paused interview subscribed to it. In a high-volume org this causes mass incorrect resumes. Always add precise field-filter resume conditions.
3. **Alarm minimum fire time is approximately 15 minutes, not zero** — An offset of 0 days does not resume the interview immediately. Salesforce enforces a platform-level minimum delay of approximately 15 minutes. Designs requiring sub-15-minute continuation after a pause must use a Platform Event wait event, not an Alarm.
4. **Debug mode skips Pause elements entirely** — The Flow Builder debugger cannot step through a Pause element. It jumps over the pause and follows the first available output connector. Resume conditions and wait event branch logic are invisible to debug runs. All functional testing of Pause element behavior requires real-world event triggers or manual event publication.
5. **Paused interviews count against org-wide async interview storage** — Every paused interview occupies Data Storage. In heavily automated orgs, concurrent paused interviews can approach or reach the org limit (historically 2,000 for most editions), causing new pause attempts to fail. Actively monitor counts and implement periodic cleanup of stale interviews.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Configured Pause element | Flow Builder Pause (Wait) element with typed wait events, resume conditions, timeout alarm, and fault path |
| Resume condition specification | Field-by-field filter list for each Platform Event wait event confirming unique match criteria |
| Interview volume estimate | Count of expected concurrent paused interviews vs. current org limit |
| Test plan | Step-by-step manual test cases for each wait event path, alarm timing, and fault path |

---

## Related Skills

- `scheduled-flows` — Use when repeating logic on a recurring fixed schedule rather than suspending a single interview
- `auto-launched-flow-patterns` — Full auto-launched flow context in which Pause elements most commonly appear
- `fault-handling` — Detailed guidance on flow fault paths, which are critical connectors on Pause element output paths
- `record-triggered-flow-patterns` — Covers scheduled paths, the alternative to Pause elements for single time-based continuation in record-triggered flows
