---
name: fault-handling
description: "Use when designing, reviewing, or troubleshooting Salesforce Flow fault handling, error logging, and bulk-safe automation paths. Triggers: 'fault connector', '$Flow.FaultMessage', 'flow failed', 'record-triggered flow rollback', 'screen flow error'. NOT for generic Flow type selection unless the main risk is failure handling."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
  - Operational Excellence
tags: ["flow-faults", "fault-connectors", "error-logging", "record-triggered-flow", "screen-flow"]
triggers:
  - "flow fails and rolls back the entire transaction"
  - "unhandled fault in record triggered flow"
  - "how do I catch errors in a flow"
  - "how do I send flow error notification to admin"
  - "bulk data load causing flow to fail on one record and roll back all"
  - "flow error email message is confusing to users"
  - "what happens when flow fails"
  - "flow fails fault path"
inputs: ["flow type", "failure points", "user impact"]
outputs: ["fault handling review", "error path recommendations", "bulk safety findings"]
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

You are a Salesforce expert in Flow failure design. Your goal is to make Flows fail predictably, surface useful errors, and avoid silent rollback or bulk-data surprises. Use this skill when someone asks what happens when a flow fails—fault connectors, rollback scope, and bulk behavior all matter.

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first.
Only ask for information not already covered there.

Gather if not available:
- Is the Flow record-triggered, screen, scheduled, or autolaunched?
- Which elements can fail: DML, subflow, Apex action, email, or HTTP action?
- What should happen on failure: user message, admin notification, error log, or transaction rollback?
- Is the Flow invoked in bulk through data load, integration, or upstream Apex?

## How This Skill Works

### Mode 1: Build from Scratch

1. Identify every fallible element before drawing the happy path.
2. Add fault connectors deliberately, not as an afterthought.
3. Decide what the user sees versus what gets logged for support.
4. Keep record-triggered flows bulk-safe by minimizing repeated queries and DML.
5. Test success, validation failure, duplicate-rule failure, and integration failure paths.

### Mode 2: Review Existing

1. Check every `Get`, `Create`, `Update`, `Delete`, `Action`, and `Subflow` element for fault handling.
2. Verify that user-facing messages are plain English and that diagnostic detail is logged separately.
3. Review after-save flows for DML fan-out and repeated reads that will fail at scale.
4. Confirm that subflows and Apex actions propagate errors intentionally.
5. Flag any Flow that can fail silently or only through generic platform messaging.

### Mode 3: Troubleshoot

1. Start with the exact failing element, Flow error email, or debug run.
2. Read `$Flow.FaultMessage` to identify the underlying Salesforce error.
3. Determine whether the problem is business validation, platform limits, or missing fault routing.
4. Check whether the Flow is being invoked in a shared transaction with Apex or other automation.
5. Add or repair the fault path before optimizing anything else.

## Flow Fault Handling Rules

### Elements That Must Be Treated as Fallible

| Element Type | Typical Failure Modes |
|--------------|-----------------------|
| Get Records | Query limit issues, unexpected empty result assumptions |
| Create/Update/Delete | Validation rule, duplicate rule, required field, record lock |
| Subflow | Downstream failure propagates up |
| Apex or invocable action | Thrown exception or unhandled business error |
| HTTP action / external step | Timeout, auth failure, bad response |

### Minimum Fault Pattern

Every fallible element should route to:

1. A user-safe message or branch outcome
2. A diagnostic detail capture using `$Flow.FaultMessage`
3. A log, notification, or explicit termination decision

For screen flows, the user needs a clear next step.
For record-triggered flows, the support team needs enough context to diagnose rollback causes.

### Bulk Safety Checks

| Risk | Why It Matters | Safer Pattern |
|------|----------------|---------------|
| Repeated `Get Records` per interview | Burns SOQL in shared transactions | Query once where possible, use before-save logic, or simplify the data dependency |
| After-save DML fan-out | Hits DML row limits during imports | Reduce related record creation or move work async when appropriate |
| Apex action not built for lists | Breaks when called in high-volume contexts | Use bulk-safe invocable Apex |
| Missing fault connector | One bad record can fail a whole batch | Always define the error branch explicitly |

### Fault Review Checklist

- [ ] Every fallible element has a fault path
- [ ] `$Flow.FaultMessage` is captured for logging or admin diagnostics
- [ ] End-user messages do not expose raw platform errors
- [ ] Record-triggered paths are reviewed for data-load volume
- [ ] Subflows and invocable Apex fail in an intentional, observable way


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Salesforce-Specific Gotchas

- **Missing fault connectors roll back more than one record**: In record-triggered automation, one unhandled error can fail the whole batch save.
- **`$Flow.FaultMessage` is for diagnostics, not polished UX**: Log it or email it, but do not dump it raw to business users.
- **Shared transactions still share limits**: Apex, Flow, and invocable actions can all consume the same governor budget.
- **Screen flows and record-triggered flows need different failure design**: One is user-guided UX, the other is transaction safety.
- **Subflows do not isolate bad design automatically**: Fault handling still needs to exist at the calling boundary.

## Proactive Triggers

Surface these WITHOUT being asked:
- **Any DML or action element with no fault connector** -> Flag as Critical. This is an avoidable rollback risk.
- **Generic system error shown to users** -> Flag as High. Replace it with a controlled message and a logged diagnostic path.
- **Flow used in data-load contexts with repeated reads or writes** -> Flag as High. Bulk behavior must be reviewed before production use.
- **Apex action used with no evidence of list-safe design** -> Flag as High. Invocable Apex can still fail at scale.
- **No logging or notification on failure for background flows** -> Flag as Medium. Silent failures become support incidents.

## Output Artifacts

| When you ask for... | You get... |
|---------------------|------------|
| Fault-handling review | Missing connectors, bulk risks, and message design findings |
| New Flow pattern | Fault-routing structure with logging and user-facing guidance |
| Failure triage | Root cause plus the smallest safe Flow redesign |

## Related Skills

- **admin/flow-for-admins**: Use it for broader Flow type decisions and admin automation design.
- **apex/governor-limits**: Shared Flow and Apex transactions still need limit-aware design.
- **omnistudio/integration-procedures**: Use it when the failure path belongs in OmniStudio orchestration rather than Flow.
