---
name: flow-testing
description: "Use when defining or reviewing test strategy for Salesforce Flow, including Flow Tests, debug runs, path coverage, test data, and explicit validation of fault paths and custom component behavior. Triggers: 'flow test tool', 'how do i test a flow', 'flow fault path testing', 'flow debug interview'. NOT for Apex unit testing or manual QA planning that is unrelated to Flow behavior."
category: flow
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - Reliability
tags:
  - flow-testing
  - flow-tests
  - path-coverage
  - debug-interview
  - test-data
triggers:
  - "how do i test a salesforce flow"
  - "flow test tool and path coverage"
  - "how should i test flow fault paths"
  - "debug flow interview results"
  - "screen flow custom component testing"
inputs:
  - "which flow type is under test and which paths are business-critical"
  - "what test data is required for happy, edge, and failure scenarios"
  - "whether custom LWC components, Apex actions, or external dependencies are involved"
outputs:
  - "flow test strategy covering happy, edge, and fault paths"
  - "review findings for missing test coverage, weak data setup, or manual-only validation"
  - "guidance on combining Flow Tests, debug runs, and component-level tests where needed"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-15
---

Use this skill when a Flow works in a demo but nobody can yet prove it is safe to change. Flow testing is not one tool. It is a test strategy that combines declarative Flow Tests where they fit, focused debug runs for diagnosis, deliberate test data, and extra coverage at custom component or Apex boundaries when the Flow itself is not the whole system.

---

## Before Starting

Gather this context before working on anything in this domain:

- What business paths matter most: happy path, edge-case branches, validation failures, or external-action failures?
- Is the flow record-triggered, screen, scheduled, or autolaunched, and what test surface is appropriate for that type?
- Which parts of the behavior live outside the flow itself, such as Apex actions, custom LWC screen components, or external integrations?

---

## Core Concepts

Good Flow testing starts with path thinking, not with clicking Debug first. The goal is to prove that the flow behaves correctly when inputs, branching, and failures vary. A happy-path-only test tells you almost nothing about how safe the automation really is in production.

### Flow Tests Need A Path Matrix

For any meaningful flow, start by listing the business outcomes that must be proven. That usually includes the main success path, one or more decision branches, and at least one failure or rejection path. The matrix drives your test data and tells you where declarative Flow Tests, Apex tests, or manual screen validation each belong.

### Debug Runs Are Diagnostic, Not Coverage

Debug mode is useful to inspect runtime behavior and investigate failures, but it is not the same as having repeatable automated coverage. Use debug runs to understand why something failed, then turn that understanding into a repeatable test asset where possible.

### Custom Boundaries Need Their Own Tests

If the flow calls invocable Apex, depends on a custom LWC screen component, or hands off work to other automation, the Flow Test alone may not be enough. The flow should still be tested at the orchestration level, but the custom component or Apex boundary also needs focused tests at its own layer.

### Fault Paths Must Be Intentional Test Cases

Testing only the success path leaves the most operationally important behavior unproven. Validation-rule errors, missing data, duplicate-rule failures, or external action failures should be part of the test plan when they are realistic outcomes.

---

## Common Patterns

### Path Matrix Before Test Authoring

**When to use:** A flow has more than one meaningful branch or outcome.

**How it works:** List each input condition, expected path, and asserted outcome before building tests. This prevents coverage from collapsing into one debug run and one happy-path scenario.

**Why not the alternative:** Writing tests ad hoc usually means the obvious branch gets covered and the risky ones do not.

### Pair Flow Tests With Boundary Tests

**When to use:** The flow interacts with Apex, custom screen LWCs, or external systems.

**How it works:** Test the orchestration in Flow, then test the custom boundary at its native layer too.

**Why not the alternative:** A Flow Test can tell you the flow called something; it may not prove the called boundary is correct in isolation.

### Explicit Fault-Path Test Cases

**When to use:** The flow can fail because of business validation, duplicate detection, or integration issues.

**How it works:** Create data and assertions that prove the flow's failure handling, not just its success handling.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need repeatable coverage for declarative branching | Build Flow Tests around a path matrix | Turns business paths into durable regression assets |
| Need to diagnose a failure quickly | Use Debug first, then convert insight into a test | Debug is for diagnosis, not long-term coverage |
| Flow depends on invocable Apex or external logic | Pair Flow Tests with tests at that boundary | The flow does not own all behavior alone |
| Screen flow uses custom LWC components | Test both the interview path and the component contract | Validation and UI behavior cross the Flow boundary |
| Only happy path is covered today | Add edge and fault cases next | Reliability risk usually lives outside the main path |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] A path matrix exists for success, branch, and failure scenarios.
- [ ] Test data is explicit and not dependent on existing org state.
- [ ] Fault-path behavior is covered where realistic failures exist.
- [ ] Custom screen components or Apex actions have tests at their own boundary.
- [ ] Debug runs are used to learn, not mistaken for repeatable coverage.
- [ ] The chosen test assets align with the flow type and production risk.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Debug success is not regression coverage** - a one-time manual run does not protect future changes.
2. **Custom LWC screen components widen the test surface** - the Flow test and the component validation contract both matter.
3. **Fault handling needs its own test data** - failures rarely prove themselves unless data is arranged to trigger them intentionally.
4. **A flow can be correct while its boundary dependency is wrong** - orchestration coverage does not replace Apex or component tests.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Test matrix | Mapping of paths, inputs, and expected outcomes |
| Coverage review | Findings on missing path, fault, or boundary coverage |
| Test strategy | Recommendation across Flow Tests, debug usage, and boundary tests |

---

## Related Skills

- `flow/fault-handling` - use alongside this skill when failure behavior needs redesign as well as test coverage.
- `flow/screen-flows` - use when the test strategy depends on interactive runtime UX and custom screen components.
- `flow/flow-and-apex-interop` - use when invocable Apex behavior is the main uncertainty behind the flow.
