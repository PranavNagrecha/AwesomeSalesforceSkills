---
name: agent-actions
description: "Use when designing or reviewing Agentforce actions, including Flow actions, Apex invocable actions, prompt-template actions, action naming, input and output contracts, confirmation requirements, and safe error behavior. Triggers: 'agent actions', 'flow action for agent', 'agent invocable action', 'action schema design', 'agent action error handling'. NOT for topic boundary design or general Apex invocable guidance when the main concern is not an agent-facing action contract."
category: agentforce
salesforce-version: "Spring '26+"
well-architected-pillars:
  - Reliability
  - Security
  - Operational Excellence
triggers:
  - "how should I design Agentforce actions"
  - "when should the agent use a flow action versus apex action"
  - "agent action naming and input schema"
  - "destructive agent action needs confirmation"
  - "agent action error handling review"
tags:
  - agentforce
  - agent-actions
  - invocable-actions
  - action-contracts
  - confirmation-patterns
inputs:
  - "which business capabilities the agent must invoke"
  - "whether the action is declarative Flow, Apex, or prompt-template based"
  - "expected inputs, side effects, and confirmation requirements"
outputs:
  - "agent action design recommendation"
  - "action contract and naming review findings"
  - "error-handling and confirmation guidance"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

# Agent Actions

Use this skill when the agent already knows the right topic, but still needs a safe and understandable way to do work. Agent actions are the operational boundary between conversational intent and real system side effects. Poor action design leads to vague capabilities, hard-to-recover failures, and agents invoking the wrong tool because names or contracts are ambiguous.

The design goal is simple: a small, well-named action set with stable inputs, predictable outputs, and deliberate confirmation for side effects. Salesforce guidance surfaced through current Agentforce documentation search emphasizes keeping action counts low, using clear names and descriptions, and shaping input types so the agent can select and execute actions reliably. Action design should help the agent understand what the tool does, what data it needs, and when failure should be surfaced to the user versus returned as a structured business result.

Agent actions can be Flow-based, Apex invocable, or prompt-template oriented depending on the task. Flow actions are strong when declarative orchestration is enough. Apex invocable actions are better when service-layer control, strict contracts, or heavier logic matter. Prompt-template actions fit generation tasks, not destructive record mutation. The boundary should be chosen intentionally.

---

## Before Starting

Gather this context before working on anything in this domain:

- What exact business task should the action perform, and is it read-only or side-effecting?
- Should the action be declarative Flow, Apex invocable, or prompt-template based?
- What inputs are truly required, and what output shape will help the agent reason about success or failure?
- Does the action need confirmation before mutating data, sending messages, or performing irreversible work?

---

## Core Concepts

### Actions Are Capabilities, Not Conversation Dumps

An action should do one business job clearly. Do not create vague actions like `runProcess` or `handleRequest` that hide several outcomes.

### Naming And Description Drive Tool Selection

The agent relies on action labels, descriptions, and parameter meaning to choose correctly. Human-readable clarity is part of the runtime contract.

### Stable Input And Output Shapes Improve Reliability

The agent needs narrow, predictable parameters and results. Avoid overloading one action with many loosely related required fields or generic object blobs.

### Confirmation And Error Behavior Need Deliberate Design

Destructive or customer-visible side effects should be confirmation-aware. Failures should return clear business meaning rather than raw stack traces or empty silence.

---

## Common Patterns

### Flow Action For Declarative Orchestration

**When to use:** The task can be modeled as clear declarative steps and the admin team should retain ownership.

**How it works:** Use a narrow Flow boundary, keep inputs explicit, and ensure the output is meaningful enough for the agent to continue or explain a failure.

**Why not the alternative:** Apex adds complexity when the task is mainly orchestration.

### Apex Invocable Service Action

**When to use:** The action needs reusable service logic, stricter contracts, or finer transaction control.

**How it works:** Use a bulk-safe invocable method with wrapper DTOs and clear result fields.

### Confirmation-Gated Mutation Action

**When to use:** The action creates, updates, deletes, or externally sends something significant.

**How it works:** Require clear confirmation language and define what the action returns when the user declines or when policy prevents execution.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Declarative orchestration is sufficient | Flow action | Lower implementation overhead |
| Service logic or tighter contract control is needed | Apex invocable action | Better structure and reuse |
| Task is primarily content generation | Prompt-template action | Generation boundary is clearer |
| Action mutates records or triggers external side effects | Add confirmation and explicit failure contract | Safer execution |
| Action name and schema feel generic | Redesign before release | Agent selection quality depends on clarity |

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

- [ ] Each action performs one business capability clearly.
- [ ] Names and descriptions help the agent choose the right tool.
- [ ] Inputs are narrow, typed, and not overloaded with generic payloads.
- [ ] Outputs communicate business success or failure clearly.
- [ ] Destructive or external side effects require deliberate confirmation behavior.
- [ ] The total action set is small enough to stay understandable.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **A technically valid invocable action can still be a poor agent action** - generic names and overloaded schemas hurt tool selection.
2. **Prompt-template actions are not the right tool for transactional mutation** - generation and side effects should not be blurred.
3. **Too many actions reduce action selection quality** - a larger tool belt is not always a better one.
4. **Raw exceptions are weak agent outputs** - business-safe result structures help the agent explain failure and recover.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Action design review | Findings on naming, schema, confirmation, and failure behavior |
| Action boundary recommendation | Flow versus Apex versus prompt-template guidance |
| Contract pattern | Suggested request and response shape for agent-safe execution |

---

## Related Skills

- `agentforce/agent-topic-design` - use when the bigger problem is topic boundary and routing.
- `apex/invocable-methods` - use when the action contract issue is really a generic Flow/Apex boundary question.
- `admin/flow-for-admins` - use when the action should remain a Flow-owned automation with no agent-specific complexity.
