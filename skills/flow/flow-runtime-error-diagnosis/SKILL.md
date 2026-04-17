---
name: flow-runtime-error-diagnosis
description: "Use when a Salesforce Flow throws a runtime error, sends an unhandled fault email, or produces unexpected results in production or sandbox. Triggers: 'Flow error email', 'Flow failed at element', 'null reference in Flow', 'Flow SOQL limit error', 'Flow DML in loop error'. NOT for Flow design or building new flows (use record-triggered-flow-patterns or other flow/* skills), NOT for Flow debug log setup (use flow-debugging)."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "my Flow is sending error emails and I need to diagnose what is failing"
  - "Flow failed at element Get_Records_0 with INVALID_FIELD error"
  - "Flow throws a null reference error when processing certain records"
  - "Flow is hitting SOQL query limits or DML statement limits"
  - "how do I read the Flow fault path email to find the root cause"
tags:
  - flow
  - error-diagnosis
  - fault-path
  - runtime-error
  - debugging
inputs:
  - "Flow fault email content (stack trace and element name from the error notification)"
  - "Flow API name and version number"
  - "Record ID or scenario that triggers the error (if known)"
outputs:
  - "Root cause identification from the fault email and debug log"
  - "Specific element and variable that caused the failure"
  - "Fix recommendation or fault path handler configuration"
dependencies: []
version: 2.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Flow Runtime Error Diagnosis

Use this skill when a Salesforce Flow generates a runtime error — either producing an unhandled fault email, displaying an error to the user, or failing silently on certain records. This covers reading the fault notification email, interpreting error types, tracing the failure to the specific element, and adding fault path handlers or fixing the root cause.

This is the incident-response companion to `flow/fault-handling` (which covers design-time prevention) and `flow/flow-testing` (which covers regression safety). When a Flow has actually failed in production, this skill is the one you open.

---

## Before Starting

Gather this context before working on anything in this domain:

- Obtain the fault notification email (if configured) — it contains the Flow API name, version, element name, and error message.
- Identify whether the flow is a Record-Triggered Flow, Auto-Launched Flow, or Screen Flow — the diagnostic steps differ slightly.
- Know the record ID or scenario that triggered the failure, if available. This allows running the debug mode on a specific record.
- Check whether the Flow has any fault paths configured — if not, errors bubble up to the user or send a fault email.
- Confirm which Flow VERSION is active — the fault email reports the version that failed, but fixes must go to the currently-active version.

---

## Core Concepts

### Flow Fault Notification Email

When a Flow encounters an unhandled error, it sends a fault email (if configured in Setup → Process Automation Settings → Send Flow Error Emails). The email contains:

- **Flow label and API name**: identifies which flow
- **Flow version**: the version that ran (important — multiple versions may be active via flow version management)
- **Element API name where the error occurred**: e.g., `Get_Account_Records` or `Create_Case_0`
- **Error message**: the platform-specific error, e.g., `INVALID_FIELD: Account.NonExistentField__c`
- **Stack trace of element execution order**: shows which elements ran before the failure
- **Context variable values**: input variables and selected `$Record` field values at the time of failure

Reading the element name from the email is the fastest way to navigate directly to the failing element in Flow Builder.

### Common Runtime Error Types

| Error Type | Likely Cause | Common Fix |
|---|---|---|
| `CANNOT_INSERT_UPDATE_ACTIVATE_ENTITY` | Validation rule, duplicate rule, or trigger failure on the DML | Fix the underlying validation rule or add error handling |
| `INVALID_FIELD` | Field referenced in Flow no longer exists or was renamed | Update the Get/Create element to remove or replace the deleted field |
| `NULL_REFERENCE` | Variable used in formula or decision without null check | Add a null check decision before the element that uses the variable |
| `LIMIT_EXCEEDED` (SOQL) | Too many SOQL queries — usually DML/Get in a loop | Move Get Records element outside the loop |
| `LIMIT_EXCEEDED` (DML) | Too many DML statements — DML inside a loop | Use Collection-based approach instead of per-record DML |
| `FIELD_INTEGRITY_EXCEPTION` | Required field not set or picklist value invalid | Verify field values before the DML element |
| `NUMBER_OUTSIDE_VALID_RANGE` | Assignment to a Number/Currency field with a value exceeding precision | Clamp the value or change the field's precision |
| `INSUFFICIENT_ACCESS_OR_READONLY` | Running user lacks FLS or object perm on a field the Flow touches | Grant FLS / adjust running-user context / use "run in system mode" |
| `UNABLE_TO_LOCK_ROW` | Record lock contention from concurrent updates | Retry pattern OR reduce per-interview DML |
| `QUERY_TIMEOUT` | Flow's Get Records query too expensive or too broad | Add selective filter or index the filter field |
| `STRING_TOO_LONG` | Assigning a value > field's max length | Truncate or validate input length before assignment |

### Fault Paths

A **Fault Path** is a connector from a Flow element (Get Records, Create Records, etc.) that runs when that element fails, instead of the normal path. Without a fault path, the error is unhandled — it shows a generic error to the user and sends a fault email.

To add a fault path: In Flow Builder, click the element → Add Fault Path → connect to a fault-handling sub-flow or screen.

See `flow/fault-handling` for the FOUR canonical fault-routing patterns; this skill's job is to decide WHICH pattern fits the failure being diagnosed.

### Debug Mode for Diagnosing the Root Cause

Flow Builder's Debug mode (Run → Debug) allows executing the flow with specific input values and tracing each element's execution:

1. In Flow Builder, click Debug.
2. Enter input variable values (e.g., a Record ID for a record-triggered flow).
3. Click Run — the debug panel shows each element that executed, the variable values at each step, and where the flow stopped.

For Record-Triggered Flows in production, the equivalent is running with debug enabled from a specific record's Flows button (if exposed), or using the Flow Debug Trace in the setup area.

**Debug mode limitations:**
- Does NOT commit DML (you can't catch failures that only appear with real data).
- Does NOT run actual Apex triggers on the object (the trigger framework is bypassed in debug).
- Does NOT send email alerts or Platform Events (actions are simulated).
- Does NOT fully simulate bulk (single interview only).

For bulk-specific failures, Debug won't reproduce — use sandbox bulk load + Flow Interview Log forensics.

---

## Common Patterns

### Pattern 1: Tracing NULL_REFERENCE to Its Source

**When to use:** Flow error: `NullPointerException` or `NULL_REFERENCE` error pointing to a formula or decision element.

**Steps:**
1. Identify the element that failed from the error email.
2. In Flow Builder, look at the failed element's inputs — which variable is used there?
3. Trace that variable backwards to where it is set (Get Records element, assignment, or input variable).
4. Common cause: Get Records returned no records (null), and the next element tries to access a field on the null record.
5. Fix: Add a Decision element after Get Records to check `{!recordVariable} is null`. Route the null path to a graceful outcome (Pattern A from `flow/fault-handling`).

### Pattern 2: Diagnosing SOQL Limit Errors

**When to use:** Flow error: `LIMIT_EXCEEDED: Too many SOQL queries: 101`

**Steps:**
1. Look for a Get Records or subflow inside a Loop element in the failing flow.
2. Get Records inside a loop queries for each iteration — 200 iterations = 200 SOQL queries.
3. Fix: Move the Get Records element outside the Loop. Retrieve all needed records once before the loop. Use a Collection Filter within the loop to find the relevant record from the already-retrieved collection.
4. Cross-reference `flow/flow-bulkification` Pattern 1 (Query-once + reuse).

### Pattern 3: INVALID_FIELD After Schema Change

**When to use:** Flow error: `INVALID_FIELD` on a field that used to work.

**Steps:**
1. Check recent deployments — was the field renamed or deleted?
2. Run `field-impact-analyzer` (runtime agent) or `probe_apex_references` MCP tool to find all other automation that references the same field — other flows, Apex, VRs may be affected too.
3. Fix: update the flow element to reference the renamed field OR restore the deleted field OR remove the reference from the flow.
4. Add a monitoring reminder: when a field is deleted/renamed in future, audit flow dependencies FIRST.

### Pattern 4: UNABLE_TO_LOCK_ROW Contention

**When to use:** Flow error: `UNABLE_TO_LOCK_ROW` on DML elements under high concurrency.

**Steps:**
1. Check what else writes to the same record concurrently (triggers, other flows, external integrations).
2. The lock is held by whoever opened the save transaction first — your Flow is losing the race.
3. Fix options:
   - Reduce Flow's critical-section time (move work out of the transaction via async).
   - Serialize concurrent writers via Platform Events queue.
   - Retry pattern (Pattern B from `flow/fault-handling`).
   - If contention is from data loads, stagger or batch differently.

### Pattern 5: The "Works in Debug but Fails in Production" Trap

**When to use:** Flow passes debug mode in Flow Builder but fails in production.

**Cause:** Debug mode runs in simulated context — no real Apex triggers, no real DML commits, system-admin-like access. Production has all of those.

**Diagnostic steps:**
1. Confirm the flow's running user context in production vs debug (System Admin always passes; real users may not).
2. Check whether object/field permissions differ.
3. Check whether Apex triggers on the object are performing additional DML that the flow is contending with.
4. Reproduce in sandbox under the actual running user's profile — that's the true test.

---

## Decision Guidance

| Error Type | First Check | Likely Fix |
|---|---|---|
| INVALID_FIELD | Has a field been deleted or renamed recently? | Update the element referencing the missing field (Pattern 3) |
| NULL_REFERENCE | Does the element use a record variable from Get Records? | Add null check after Get Records (Pattern 1) |
| SOQL limit | Is there a Get Records inside a Loop? | Move Get Records outside the loop (Pattern 2) |
| DML limit | Is there a Create/Update/Delete inside a Loop? | Collect records in a collection, bulk DML outside loop |
| CANNOT_INSERT_UPDATE | Does the record fail a validation rule or duplicate rule? | Fix the validation rule or check values before DML |
| Error on some records, not all | Is there a conditional path missing a null check? | Add Decision element to handle edge cases |
| UNABLE_TO_LOCK_ROW | Is another process writing to the same record concurrently? | Pattern 4 — serialize, retry, or async |
| INSUFFICIENT_ACCESS | Is the running user missing FLS/object perms? | Grant perms OR run-in-system-mode (carefully) |
| Debug passes, prod fails | Running-user context mismatch | Pattern 5 — reproduce under real user profile |

---

## Recommended Workflow

1. **Get the fault notification email.** Navigate to Setup → Process Automation Settings to confirm fault emails are enabled and routed correctly.
2. **Identify the flow, version, and failing element** from the email. Note the element API name.
3. **Open the flow in Flow Builder** and navigate to the failing element (use Ctrl+F to search by element API name).
4. **Read the error type.** Use the error type table above to narrow the root cause.
5. **Run Debug mode** with a representative record ID. Step through the execution to see variable values at the failing element.
6. **Fix the root cause:** fix the null reference, move elements out of loops, correct field references, or fix the underlying validation/trigger.
7. **Add a fault path** to the previously-failing element so future errors produce a user-friendly message rather than a raw error, even if the root cause is not fully eliminated.
8. **Test the fix** in a sandbox with the same record scenario that triggered the original failure.
9. **Verify the currently-active version** is the fixed version; activate it intentionally rather than relying on deployment order.
10. **Post-mortem**: if this was a production incident, document the root cause + fix in the team's incident log so future similar failures diagnose faster.

---

## Review Checklist

- [ ] Fault notification emails are configured and routing to the admin inbox
- [ ] Fault path handlers added to all Get Records, Create/Update/Delete, and Subflow elements
- [ ] No Get Records or DML elements inside Loop elements (check for limit violations)
- [ ] Null checks added after Get Records where the variable is used in formulas or decisions
- [ ] Fix tested with the original failing record scenario in sandbox
- [ ] Flow version confirmed — ensure the active version is the fixed version
- [ ] Post-mortem recorded (root cause + fix + prevention)
- [ ] Cross-agent lookup done (`field-impact-analyzer` for schema errors; `flow-analyzer` for pattern issues)

---

## Well-Architected Pillar Mapping

- **Reliability** — every runtime error is a Reliability finding; the fix produces Reliability. Missing fault paths escalate Reliability concerns to P0.
- **Operational Excellence** — fault email routing, running-user context discipline, version-management clarity, post-mortem culture. OpsEx determines whether this skill is used once or whether the diagnosis cycle is fast.

---

## Salesforce-Specific Gotchas

1. **Flow fault emails go to the user who activated the flow, not the admin** — By default, fault emails go to the flow's last modifier. Configure fault email routing in Setup → Process Automation Settings to send to an admin group instead.
2. **Multiple active flow versions can coexist** — Only one version can be active at a time for a given API name. If the error email references version 3 but you fixed version 4, confirm version 4 is the active version.
3. **Debug mode does not trigger actual DML** — The Debug run executes the flow logic but does not commit records. This means you cannot rely on debug to catch DML failures that only appear with real data volumes or trigger interactions.
4. **Debug mode bypasses Apex triggers** — the flow sees a simplified transaction. Trigger-ordering bugs don't reproduce in debug.
5. **Flow Interview Log is the forensic trail** — for production failures you can't reproduce, check `FlowInterviewLog` + `FlowInterviewLogEntry` via Setup or SOQL.
6. **Paused flows are a separate failure mode** — `FlowInterview` in `Paused` status isn't an error but is often mistaken for one. Check status before assuming failure.
7. **Custom exception thrown by invocable Apex shows up as generic Flow error** — don't assume the error message is the Apex exception; check the invocable's log separately.
8. **"Run flow as System Admin" in debug hides FLS issues** — always test under the real user's profile before declaring the fix done.
9. **Managed-package flow errors are opaque** — element names are visible but internals aren't. File a case with the package vendor; don't try to patch the managed flow.
10. **Error email rate-limiting** — orgs that fire thousands of flow errors per hour may see emails suppressed silently. Check `FlowInterviewLog` counts, not just email volume.

---

## Proactive Triggers

Surface these WITHOUT being asked:

- **Flow fault email recipient is inactive** → Flag as Critical. Errors disappear silently.
- **Repeated errors on same element over time** → Flag as High. Recurring issue, not transient; root-cause needed.
- **Fault email reports a non-active version** → Flag as High. Version management confusion; deploy and activate discipline needed.
- **Failing element has no fault path** → Flag as High. Even after root-cause fix, add the fault path for future surprises.
- **Error pattern "works in debug, fails in prod"** → Flag as High. Running-user mismatch; Pattern 5 applies.
- **`UNABLE_TO_LOCK_ROW` in Flow Interview Log > threshold** → Flag as High. Concurrency problem, not a flow bug.
- **Missing fault-email configuration at org level** → Flag as Critical. All future flow errors will disappear silently.
- **Post-mortem not documented after a production flow failure** → Flag as Medium. Next incident will take as long to diagnose.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Root cause analysis | Element name, error type, variable that failed, triggering scenario |
| Fix recommendation | Specific change to make in Flow Builder with rationale |
| Fault path handler configuration | Screen text or action to show when the fault path fires |
| Post-mortem entry | Root cause + fix + prevention for the team's incident log |

---

## Related Skills

- `flow/fault-handling` — companion skill; prevents the errors this skill diagnoses.
- `flow/flow-bulkification` — when the error is a bulk-safety violation (SOQL/DML limit).
- `flow/flow-debugging` — setting up debug logs for Flow and trace analysis (diagnostic setup).
- `flow/flow-testing` — write a regression test after the fix so the issue doesn't recur.
- `flow/record-triggered-flow-patterns` — when the root cause is a pattern-level design flaw.
- `apex/trigger-and-flow-coexistence` — when Apex + Flow contention on the same object causes the error.
