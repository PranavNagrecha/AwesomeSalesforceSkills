---
name: subflows-and-reusability
description: "Use when extracting reusable Flow logic into subflows, defining input and output variables, keeping parent flows maintainable, and sharing common automation contracts across multiple flows. Triggers: 'reuse this flow logic', 'how should subflow variables work', 'too much duplicated flow logic', 'subflow contract design'. NOT for Apex-called Flow execution direction or Flow Orchestration process design."
category: flow
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - Operational Excellence
  - Scalability
  - Reliability
tags:
  - subflows
  - flow-reuse
  - input-output-variables
  - autolaunched-flow
  - maintainability
triggers:
  - "should this logic become a subflow"
  - "how do input and output variables work in a subflow"
  - "too much duplicated logic across flows"
  - "subflow fault handling and contracts"
  - "reusable autolaunched flow pattern"
inputs:
  - "which parent flows repeat the same logic and what outputs they need back"
  - "whether the reusable step is pure calculation, data lookup, mutation, or error handling"
  - "how much of the current flow contract is stable across callers"
outputs:
  - "subflow extraction recommendation with clear input and output contracts"
  - "review findings for over-coupled or under-specified flow reuse"
  - "guidance on when to keep logic inline versus moving it to subflow or Apex"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-15
---

Use this skill when the same Flow logic keeps appearing in more than one place or when one parent flow is becoming too long to reason about safely. A good subflow is a reusable contract with a narrow purpose, explicit inputs, explicit outputs, and predictable side effects. A bad subflow is just a pile of hidden assumptions moved out of sight.

---

## Before Starting

Gather this context before working on anything in this domain:

- How many parent flows need the logic today, and is the contract likely to stay stable across them?
- Is the candidate subflow primarily computing a value, centralizing a lookup, or performing side effects such as DML and notifications?
- What should happen when the called flow fails, returns nothing, or needs to evolve later?

---

## Core Concepts

Subflows are most valuable when they remove repetition without hiding important behavior. The key design decision is whether the reusable unit has a clean contract. If the parent flow still needs to understand many internal assumptions or pass a long list of loosely related variables, the design is not reusable yet.

### Reuse Requires A Stable Contract

A subflow should expose a small set of clearly named inputs and outputs. Variable names such as `inCaseId`, `inPriority`, and `outQueueDeveloperName` are easier to maintain than generic `text1` or `varRecord`. A caller should understand what to pass and what it gets back without reading the entire child flow.

### Subflows Share The Parent Transaction Context

Moving logic into a subflow does not magically reset governor limits, rollback behavior, or fault responsibility. If the subflow does repeated queries inside a loop or throws an unhandled error, the parent still pays the cost. Reuse improves maintainability only if the reused logic is already safe.

### Side Effects Should Be Deliberate

The cleanest reusable subflows often perform one well-bounded job: derive data, centralize a lookup, or apply a consistent decision tree. A child flow that creates records, sends emails, and mutates unrelated state for many different callers is harder to reason about and harder to test safely.

### Activation And Change Management Matter

A reusable child flow becomes a dependency surface. Renaming variables, changing output meaning, or widening side effects can break multiple callers at once. That means subflow changes need release discipline and regression testing across every parent flow that relies on the contract.

---

## Common Patterns

### Shared Lookup Or Decision Subflow

**When to use:** Several flows need the same routing rule, owner lookup, or eligibility decision.

**How it works:** Build an autolaunched flow with narrow inputs, return a small output set, and keep the logic focused on producing a stable answer for callers.

**Why not the alternative:** Copying the same decisions into every flow creates drift and inconsistent behavior over time.

### Reusable Preparation Step Before Main Work

**When to use:** Multiple parent flows need the same record enrichment or normalization step before continuing.

**How it works:** The subflow reads or derives the needed values, returns them cleanly, and leaves final parent-specific actions in the caller.

**Why not the alternative:** Folding all parent-specific side effects into the child flow destroys reuse and makes the contract opaque.

### Escalate Out Of Flow When Reuse Gets Too Complex

**When to use:** The reusable unit needs deep branching, heavy data work, or a broad list of inputs and outputs.

**How it works:** Move the logic to Apex or another more structured boundary and keep Flow responsible for orchestration.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Same decision or lookup is repeated across multiple flows | Extract a subflow with explicit inputs and outputs | Centralizes logic without duplicating maintenance |
| Logic is unique to one short parent flow | Keep it inline | Extraction adds indirection without enough reuse benefit |
| Reusable step has many side effects and hidden dependencies | Redesign or move to Apex | The contract is too wide for healthy Flow reuse |
| Child flow failure needs consistent caller handling | Add clear fault behavior at the call boundary | Subflows do not isolate error design automatically |
| Parent is using subflows to avoid bulk or governor review | Reassess the overall architecture | Limits and rollback still apply across the transaction |

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

- [ ] The subflow solves a repeated problem, not a one-off decomposition habit.
- [ ] Input and output variables are small in number and named as a clear contract.
- [ ] The subflow's side effects are narrow and documented.
- [ ] Parent flows handle subflow failure intentionally.
- [ ] Bulk and transaction behavior were reviewed at the parent-plus-child level.
- [ ] Contract changes are regression-tested across all callers.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Subflows do not reset limits** - the caller and child still consume the same transaction budget.
2. **Wide variable contracts are a design smell** - if a subflow needs many loosely related inputs, the reusable boundary is probably wrong.
3. **A shared child flow can break many parents at once** - contract changes need versioning discipline and regression tests.
4. **Moving logic out of sight is not the same as simplifying it** - some complex reuse should become Apex instead of another Flow layer.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Subflow boundary recommendation | Guidance on what to extract and what to leave in the parent |
| Contract design | Proposed input and output variable set for the child flow |
| Reuse review findings | Risks around side effects, failure handling, and over-decomposition |

---

## Related Skills

- `flow/flow-bulkification` - use alongside this skill when the shared child logic may still be unsafe under volume.
- `flow/fault-handling` - use when the key question is how callers should respond to child-flow failure.
- `flow/flow-and-apex-interop` - use when the reusable unit has outgrown Flow and needs an Apex boundary.
