---
name: omnistudio-remote-actions
description: "Use when configuring, troubleshooting, or choosing between Remote Action types in OmniScript or FlexCard. Triggers: 'remote action', 'OmniScript action', 'IP action', 'Apex action element', 'VlocityOpenInterface2', 'Send/Response JSON Path'. NOT for Integration Procedure internal design (use integration-procedures) or generic Apex callout patterns (use apex integration skills)."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
  - Performance
tags:
  - omnistudio
  - remote-action
  - omniscript
  - flexcard
  - integration-procedure
  - apex-action
  - VlocityOpenInterface2
triggers:
  - "OmniScript remote action not returning expected data"
  - "when to use IP action vs Apex action in OmniScript"
  - "VlocityOpenInterface2 interface contract for OmniStudio"
  - "Send JSON Path and Response JSON Path mapping issues"
  - "remote action invoke mode Fire and Forget vs Promise"
  - "FlexCard action calling an Integration Procedure"
inputs:
  - "OmniScript or FlexCard definition requiring external data or server-side logic"
  - "Apex class candidates implementing VlocityOpenInterface2 or Callable"
  - "Integration Procedure name and expected input/output contract"
outputs:
  - "Remote action configuration with correct type, JSON path mappings, and invoke mode"
  - "Decision on Apex Remote Action vs IP Action vs REST Action"
  - "Troubleshooting findings for broken or slow remote actions"
dependencies:
  - integration-procedures
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# OmniStudio Remote Actions

You are a Salesforce expert in OmniStudio Remote Action configuration. Your goal is to help practitioners select the correct Remote Action type, configure Send/Response JSON Path mappings accurately, and avoid the invoke-mode timing bugs that cause silent data loss in OmniScripts and FlexCards.

---

## Before Starting

Gather this context before working on anything in this domain:

- Which OmniStudio component is consuming the action — OmniScript, FlexCard, or LWC wrapper?
- What server-side operation is required — database read/write, external callout, calculation, or orchestration of multiple steps?
- Is there an existing Integration Procedure or Apex class that handles this logic, or does it need to be built?
- What is the expected input shape (the data available in the OmniScript JSON at the step) and expected output shape?

---

## Core Concepts

### Remote Action Types

OmniStudio provides several action element types that invoke server-side logic from an OmniScript or FlexCard:

| Action Type | Backend | Use When |
|---|---|---|
| **Integration Procedure Action** | Named Integration Procedure | Orchestrating multiple data operations, callouts, or transformations declaratively |
| **Apex Remote Action** | Apex class implementing `vlocity_cmt.VlocityOpenInterface2` (managed) or `omnistudio.VlocityOpenInterface2` (native) | Custom logic that cannot be expressed declaratively, or performance-critical single operations |
| **REST Action** | External REST endpoint via Named Credential | Direct external callout without IP orchestration overhead |
| **DataRaptor Action** | DataRaptor Extract or Load | Simple single-object read or write with field mapping |

The Integration Procedure Action is the most common choice. Default to it unless you have a specific reason to use Apex or REST directly.

### VlocityOpenInterface2 Contract

Apex Remote Actions must implement the `VlocityOpenInterface2` interface. The contract requires a single method:

```apex
global Object invokeMethod(String methodName, Map<String, Object> inputMap,
                           Map<String, Object> outputMap, Map<String, Object> options);
```

- `methodName` is set in the action element's configuration and lets one class serve multiple actions.
- `inputMap` receives the data from the Send JSON Path mapping.
- `outputMap` is where the Apex class puts response data. The Response JSON Path mapping reads from here.
- `options` carries framework metadata (language, user context). Do not write business data here.

The class must be `global` and the method must be `global`. Using `public` causes a runtime binding failure with no compile-time warning.

### Send and Response JSON Path Mapping

Every Remote Action has two critical path configurations:

- **Send JSON Path**: Selects which subset of the OmniScript JSON is sent to the server. If blank, the entire step-level JSON node is sent. Use dot notation (e.g., `AccountInfo.BillingAddress`) to send only what is needed.
- **Response JSON Path**: Determines where in the OmniScript JSON the response data lands. If blank, the response overwrites the step-level node. Misconfigured paths cause data to land in unexpected locations or silently disappear.

### Invoke Mode

The invoke mode controls when and how the action fires:

| Mode | Behavior | Risk |
|---|---|---|
| **Promise (default)** | Fires when the step loads; blocks UI until complete | Safe for data the step needs to render |
| **Fire and Forget** | Fires when the step loads; does not block UI | Response may arrive after the user has moved to the next step — data is lost |
| **On Click** | Fires only when user clicks a button | Requires explicit UX for the trigger |

Fire and Forget is the most common source of intermittent data-loss bugs. The action completes, but the user has already navigated away and the OmniScript JSON no longer contains the step node.

---

## Common Patterns

### Pattern 1: IP Action with Scoped JSON Paths

**When to use:** The action needs to call an Integration Procedure that reads or writes external data, and the OmniScript has a large JSON state.

**How it works:**

1. Set the action type to Integration Procedure.
2. Set Send JSON Path to the specific node the IP needs (e.g., `QuoteRequest`), not the entire JSON.
3. Set Response JSON Path to a dedicated output node (e.g., `QuoteResponse`) to avoid overwriting other data.
4. Set invoke mode to Promise so downstream steps can rely on the data.

**Why not the alternative:** Sending the full JSON wastes payload size and risks leaking unrelated PII to the IP. Leaving Response JSON Path blank risks overwriting sibling data in the step.

### Pattern 2: Apex Remote Action for High-Performance Single Operation

**When to use:** A single Apex operation is needed (e.g., a complex calculation or a governor-sensitive DML) and wrapping it in an IP adds unnecessary overhead.

**How it works:**

1. Create a `global` class implementing `VlocityOpenInterface2`.
2. Implement `invokeMethod`, branching on `methodName` for different operations.
3. Read inputs from `inputMap`, write results to `outputMap`.
4. In the OmniScript action element, set the class name and method name.
5. Configure Send JSON Path to pass only the required input fields.
6. Configure Response JSON Path to a clean output node.

**Why not the alternative:** Integration Procedures add a layer of serialization and step orchestration. For a single Apex call, the direct action is faster and simpler to debug.

### Pattern 3: OmniContinuation for Long-Running Callouts

**When to use:** The external system takes longer than the synchronous Apex timeout (120 seconds) or you need to make multiple callouts that exceed the per-transaction callout limit.

**How it works:**

1. Implement the `Continuation` class pattern in Apex instead of a synchronous callout.
2. Reference the Continuation class in the OmniScript action element.
3. The framework handles the asynchronous callback and resumes the OmniScript.

**Why not the alternative:** Synchronous callouts that exceed 120 seconds fail hard. Continuation keeps the user session alive and avoids governor limit exceptions on chained callouts.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Orchestrate multiple data reads/writes and an external callout | IP Action | Declarative orchestration with built-in error handling per step |
| Single Apex operation with complex logic | Apex Remote Action | Avoids IP overhead; direct control over governor usage |
| Direct external REST call, no transformation needed | REST Action | Simplest path; no IP or Apex class required |
| Simple single-object SOQL read or DML write | DataRaptor Action | Declarative, no code, built-in field mapping |
| Callout exceeding 120-second timeout | OmniContinuation (Apex) | Only pattern that survives long-running external calls |
| Action result needed by the current step's UI | Promise invoke mode | Guarantees data is available before render |
| Action result not needed by current step (logging, analytics) | Fire and Forget invoke mode | Non-blocking, but accept that data may not persist in JSON |

---

## Recommended Workflow

Step-by-step instructions for configuring a Remote Action:

1. **Identify the backend** — Determine whether the operation maps to an existing IP, Apex class, REST endpoint, or DataRaptor. If nothing exists, decide which to build using the Decision Guidance table.
2. **Define the input/output contract** — Write down exactly which fields the action needs from the OmniScript JSON and which fields it returns. This drives Send and Response JSON Path configuration.
3. **Configure the action element** — Add the action to the OmniScript or FlexCard. Set the type, target (IP name, class name, or endpoint), and method name. Configure Send JSON Path to pass only required fields.
4. **Set the invoke mode** — Use Promise unless you have a specific reason for Fire and Forget. If using Fire and Forget, confirm the downstream steps do not read the action's output.
5. **Map the response** — Set Response JSON Path to a dedicated node. Test that the data lands where expected by enabling the OmniScript debugger and inspecting the JSON after the step executes.
6. **Test edge cases** — Test with empty input, null fields, error responses from the backend, and timeout scenarios. Verify the OmniScript handles each gracefully.
7. **Review security** — Confirm the Apex class uses `with sharing` or the IP respects FLS. Verify Named Credentials are used for any external callout rather than hardcoded credentials.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Action type matches the backend complexity (IP for orchestration, Apex for single ops, REST for direct calls)
- [ ] Send JSON Path is scoped to only the fields the backend needs — not the entire JSON
- [ ] Response JSON Path writes to a dedicated node that does not collide with other step data
- [ ] Invoke mode is Promise for any data the current or next step depends on
- [ ] Apex Remote Action class is `global` and implements the correct `VlocityOpenInterface2` namespace
- [ ] Apex `invokeMethod` writes to `outputMap`, not `inputMap` or return value
- [ ] Named Credentials are used for external callouts — no hardcoded URLs or tokens
- [ ] Error handling returns a meaningful message the OmniScript can display to the user
- [ ] OmniScript debugger confirms data lands at the expected JSON path

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Namespace mismatch on VlocityOpenInterface2** — Managed-package orgs use `vlocity_cmt.VlocityOpenInterface2`; native OmniStudio orgs use `omnistudio.VlocityOpenInterface2`. Using the wrong namespace compiles fine but throws a runtime ClassCastException. Check which package type is installed before writing the class.
2. **Fire and Forget data loss on fast navigation** — If a user clicks Next before a Fire and Forget action completes, the response writes to a step node that no longer exists in the active OmniScript JSON. The action succeeds on the server but the client never receives the data. There is no error.
3. **Blank Response JSON Path overwrites sibling data** — When Response JSON Path is empty, the entire action response replaces the step-level JSON node. Any data from other elements in the same step is lost. Always set an explicit Response JSON Path.
4. **outputMap keys are case-sensitive** — The Response JSON Path reads from `outputMap` using exact key names. If Apex writes `accountName` but the OmniScript expects `AccountName`, the field is silently null.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Remote Action configuration | Action element settings including type, target, JSON paths, and invoke mode |
| VlocityOpenInterface2 Apex class | Global class with invokeMethod implementing the required server-side logic |
| Input/output contract documentation | Mapping of OmniScript JSON fields to backend parameters and return values |

---

## Related Skills

- integration-procedures — Use when the Remote Action calls an IP and you need to design or debug the IP itself
- omniscript-design-patterns — Use when the Remote Action is part of a larger OmniScript flow design
- omnistudio-performance — Use when Remote Action latency is causing user experience problems
- omnistudio-debugging — Use when Remote Action failures need step-level trace analysis
