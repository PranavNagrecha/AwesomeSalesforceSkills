---
name: flow-interview-debugging
description: "Diagnose Flow failures using the Debug Log, Flow Error emails, and the Debug panel; instrument flows so production issues are triageable. NOT for Apex debugging - use apex/salesforce-debug-log-analysis."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "flow error email"
  - "flow debug log"
  - "flow failing in production"
  - "flow interview paused"
tags:
  - flow
  - debug
  - error-handling
inputs:
  - "failing flow + error email"
  - "repro data"
outputs:
  - "root cause + remediation + logging upgrade"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# Flow Interview Debugging

Flow failures are quiet by default. The platform sends one email to one person —
the user who last modified the flow — and writes nothing you can report on. If
that person has left, or the flow runs asynchronously where no user is on screen,
the failure leaves no trace at all beyond the record that did not get created.

This skill covers two jobs that usually arrive together. The first is triage:
given an error email or a user complaint, find the element, the version, the
data, and the running user that produced the failure. The second is
instrumentation: change the flow so the next failure answers those questions
without an investigation.

## Recommended Workflow

1. **Fix the notification path before anything else.** Setup → Quick Find
   `Automation` → **Process Automation Settings** → set **Send Process or Flow
   Error Email to** = **Apex Exception Email Recipients**, then maintain that
   list under Setup → **Apex Exception Email**. Route it to a monitored alias,
   not an individual. Note that these emails contain the interview's data,
   including user-entered values — scope the alias accordingly.
2. **Read the error email in order: element, status code, version, GUID, user.**
   `Error element <Name> (<Type>)` names the failure point; the status code says
   whether it is data, contention, or a downstream trigger; `Version:` tells you
   which version to open (often not the one Flow Builder shows by default);
   `Flow Interview GUID` is the join key; `Current User` tells you whose
   permissions applied.
3. **Reproduce in the debugger for the synchronous path only.** Flow Builder →
   **Debug**. Iterate with roll-back on; do a final pass with roll-back **off**
   so commit-time and downstream automation actually run. For screen flows,
   debug as a low-privilege persona, not as yourself.
4. **Observe the async path where it lives.** Scheduled-path entries queue on
   Setup → **Environments** → **Monitoring** → **Time-Based Workflow**. Interview
   state lives on Setup → **Paused And Failed Flow Interviews**. The debugger
   reaches neither.
5. **Instrument every fallible element.** Put a fault connector on every DML,
   Action, and Subflow element, and point it at a Create Records that writes
   `$Flow.FaultMessage`, `$Flow.InterviewGuid`, the element name as a literal,
   the record Id, and the running user to a custom log object.
6. **Decide per fault path whether the interview should continue.** If the
   business outcome did not happen, end the path — in a record-triggered flow use
   the **Custom Error** element so the transaction rolls back and the user is
   told, rather than committing a half-finished state.
7. **Close the loop with a threshold.** Report on the log object, alert on a rate
   change, and review the Paused And Failed Flow Interviews page on a cadence.

## Key Considerations

**The fault connector is narrower than people expect.** It fires on platform
exceptions — an invalid reference, an object or field the running user cannot
access, a governor breach. It does *not* fire when a Get Records matches zero
rows, because zero rows is a successful query. "Not found" is a Decision, not a
fault path.

**`$Flow.FaultMessage` is only populated inside a fault path**, and only until
something else faults. Read it in the first element after the fault connector.

**There is no global variable that reports which element faulted.** The error
email carries it; the interview does not. Pass the element name in as a literal
at each fault-handler call site, or accept that a shared handler produces
unattributable log rows.

**`$Flow.InterviewGuid` is the only reliable join** between an error email and a
log row. Timestamps collide under bulk load and one record can be touched by
several interviews in a transaction. Store the GUID as an indexed External ID.

**Governor errors are transaction-wide, not flow-wide.** `Too many SOQL queries:
101` means the whole transaction spent 100 queries, and an Apex trigger or a
second flow on the same object may have spent most of them before your first
element ran. Inventory the object's automation before optimizing the flow.

**The 2,000-executed-elements limit was removed at API version 57.0.** Diagnoses
that invoke it on a modern flow are reasoning from retired documentation. The
live ceilings are CPU time and the SOQL/DML governors.

## Worked Examples (see `references/examples.md`)

- *Route error emails off the last modifier* — the Process Automation Settings
  change and its privacy trade-off.
- *A fault path that produces a usable log row* — the Flow XML, including which
  fields carry the interview GUID and the element name.
- *Wrong vs right: fault path on a Get Records that returns nothing* — the same
  flow built both ways.
- *Debugging the path you cannot see* — scheduled and async paths, and the
  Time-Based Workflow queue.
- *Reading a flow error email without guessing* — which line answers which
  question.

## Common Gotchas (see `references/gotchas.md`)

- **Error email goes to the last modifier** — and silently moves every time
  someone saves the flow.
- **Zero rows is not a fault** — the "not found" branch off a fault connector is
  dead code.
- **The debugger skips async and skips commit** — two whole classes of failure
  are invisible in it.
- **The email's version is not the version you have open** — Flow Builder opens
  the latest, the failure was in another one.
- **A fault path that rejoins the happy path** — converts a loud failure into a
  silent partial commit.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Fault connector on a Get Records to catch "no records found".
- A Screen element as the fault handler in a flow type that has no screen.
- Invented globals like `$Flow.CurrentElement` or `$Flow.ErrorElement`.
- "Send the error email to the flow owner" — not one of the platform's options.
- Attributing any limit error to the removed 2,000-element cap.

## Related

- `flow/fault-handling` — the fault-path patterns this skill instruments.
- `flow/flow-runtime-error-diagnosis` — decoding a specific runtime error string.
- `flow/flow-bulkification` — when triage lands on a governor limit.
- `flow/flow-versioning-strategy` — when the failing version is not the current
  one.
- `standards/decision-trees/automation-selection.md` — when a flow keeps failing
  because the work was never a Flow problem.

## Official Sources Used

- Select Flow and Process Error Email Recipients — https://help.salesforce.com/s/articleView?id=sf.flow_troubleshoot_error_email.htm&type=5
- Customize What Happens When a Flow Fails — https://help.salesforce.com/s/articleView?id=platform.flow_build_logic_fault.htm&type=5
- Flow Resource: $Flow Global Variables — https://help.salesforce.com/s/articleView?id=sf.flow_ref_resources_system_variables.htm&type=5
- Test or Troubleshoot Flows with the Flow Builder Debugger — https://help.salesforce.com/s/articleView?id=platform.flow_test_debug.htm&type=5
- Per-Transaction Apex Governor Limits — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm

The full annotated list, including the release notes behind the currency claims,
is in `references/well-architected.md`.
