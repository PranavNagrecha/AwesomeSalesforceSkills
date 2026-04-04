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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Flow Runtime Error Diagnosis

Use this skill when a Salesforce Flow generates a runtime error — either producing an unhandled fault email, displaying an error to the user, or failing silently on certain records. This covers reading the fault notification email, interpreting error types, tracing the failure to the specific element, and adding fault path handlers or fixing the root cause.

---

## Before Starting

Gather this context before working on anything in this domain:

- Obtain the fault notification email (if configured) — it contains the Flow API name, version, element name, and error message.
- Identify whether the flow is a Record-Triggered Flow, Auto-Launched Flow, or Screen Flow — the diagnostic steps differ slightly.
- Know the record ID or scenario that triggered the failure, if available. This allows running the debug mode on a specific record.
- Check whether the Flow has any fault paths configured — if not, errors bubble up to the user or send a fault email.

---

## Core Concepts

### Flow Fault Notification Email

When a Flow encounters an unhandled error, it sends a fault email (if configured in Setup > Process Automation Settings > Send Flow Error Emails). The email contains:

- **Flow label and API name**: identifies which flow
- **Flow version**: the version that ran (important — multiple versions may be active via flow version management)
- **Element API name where the error occurred**: e.g., `Get_Account_Records` or `Create_Case_0`
- **Error message**: the platform-specific error, e.g., `INVALID_FIELD: Account.NonExistentField__c`
- **Stack trace of element execution order**: shows which elements ran before the failure

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

### Fault Paths

A **Fault Path** is a connector from a Flow element (Get Records, Create Records, etc.) that runs when that element fails, instead of the normal path. Without a fault path, the error is unhandled — it shows a generic error to the user and sends a fault email.

To add a fault path: In Flow Builder, click the element > Add Fault Path > connect to a fault-handling sub-flow or screen.

### Debug Mode for Diagnosing the Root Cause

Flow Builder's Debug mode (Run > Debug) allows executing the flow with specific input values and tracing each element's execution:

1. In Flow Builder, click Debug.
2. Enter input variable values (e.g., a Record ID for a record-triggered flow).
3. Click Run — the debug panel shows each element that executed, the variable values at each step, and where the flow stopped.

For Record-Triggered Flows in production, the equivalent is running with debug enabled from a specific record's Flows button (if exposed), or using the Flow Debug Trace in the setup area.

---

## Common Patterns

### Tracing NULL_REFERENCE to Its Source

**When to use:** Flow error: `NullPointerException` or `NULL_REFERENCE` error pointing to a formula or decision element.

**How it works:**
1. Identify the element that failed from the error email.
2. In Flow Builder, look at the failed element's inputs — which variable is used there?
3. Trace that variable backwards to where it is set (Get Records element, assignment, or input variable).
4. Common cause: Get Records returned no records (null), and the next element tries to access a field on the null record.
5. Fix: Add a Decision element after Get Records to check `{!recordVariable} is null`. Route the null path to a graceful outcome.

### Diagnosing SOQL Limit Errors

**When to use:** Flow error: `LIMIT_EXCEEDED: Too many SOQL queries: 101`

**How it works:**
1. Look for a Get Records or subflow inside a Loop element in the failing flow.
2. Get Records inside a loop queries for each iteration — 200 iterations = 200 SOQL queries.
3. Fix: Move the Get Records element outside the Loop. Retrieve all needed records once before the loop. Use a Collection Filter within the loop to find the relevant record from the already-retrieved collection.

---

## Decision Guidance

| Error Type | First Check | Likely Fix |
|---|---|---|
| INVALID_FIELD | Has a field been deleted or renamed recently? | Update the element referencing the missing field |
| NULL_REFERENCE | Does the element use a record variable from Get Records? | Add null check after Get Records |
| SOQL limit | Is there a Get Records inside a Loop? | Move Get Records outside the loop |
| DML limit | Is there a Create/Update/Delete inside a Loop? | Collect records in a collection, bulk DML outside loop |
| CANNOT_INSERT_UPDATE | Does the record fail a validation rule or duplicate rule? | Fix the validation rule or check values before DML |
| Error on some records, not all | Is there a conditional path missing a null check? | Add Decision element to handle edge cases |

---

## Recommended Workflow

1. **Get the fault notification email.** Navigate to Setup > Process Automation Settings to confirm fault emails are enabled and routed correctly.
2. **Identify the flow, version, and failing element** from the email. Note the element API name.
3. **Open the flow in Flow Builder** and navigate to the failing element (use Ctrl+F to search by element API name).
4. **Read the error type.** Use the error type table above to narrow the root cause.
5. **Run Debug mode** with a representative record ID. Step through the execution to see variable values at the failing element.
6. **Fix the root cause:** fix the null reference, move elements out of loops, correct field references, or fix the underlying validation/trigger.
7. **Add a fault path** to the previously-failing element so future errors produce a user-friendly message rather than a raw error, even if the root cause is not fully eliminated.
8. **Test the fix** in a sandbox with the same record scenario that triggered the original failure.

---

## Review Checklist

- [ ] Fault notification emails are configured and routing to the admin inbox
- [ ] Fault path handlers added to all Get Records, Create/Update/Delete, and Subflow elements
- [ ] No Get Records or DML elements inside Loop elements (check for limit violations)
- [ ] Null checks added after Get Records where the variable is used in formulas or decisions
- [ ] Fix tested with the original failing record scenario in sandbox
- [ ] Flow version confirmed — ensure the active version is the fixed version

---

## Salesforce-Specific Gotchas

1. **Flow fault emails go to the user who activated the flow, not the admin** — By default, fault emails go to the flow's last modifier. Configure fault email routing in Setup > Process Automation Settings to send to an admin group instead.
2. **Multiple active flow versions can coexist** — Only one version can be active at a time for a given API name. If the error email references version 3 but you fixed version 4, confirm version 4 is the active version.
3. **Debug mode does not trigger actual DML** — The Debug run executes the flow logic but does not commit records. This means you cannot rely on debug to catch DML failures that only appear with real data volumes or trigger interactions.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Root cause analysis | Element name, error type, variable that failed, and triggering scenario |
| Fix recommendation | Specific change to make in Flow Builder with rationale |
| Fault path handler configuration | Screen text or action to show when the fault path fires |

---

## Related Skills

- flow-debugging — setting up debug logs for Flow and trace analysis (diagnostic setup)
- record-triggered-flow-patterns — building reliable record-triggered flows (prevention)
- auto-launched-flow-patterns — auto-launched flow invocation and error handling
