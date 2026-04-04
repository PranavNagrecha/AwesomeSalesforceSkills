---
name: screen-flows
description: "Use when designing or reviewing interactive Flow screen experiences, including navigation, validation, screen component choice, custom LWC screen components, and user-safe commit timing. Triggers: 'screen flow validation', 'back button behavior in flow', 'custom flow screen component', 'screen flow UX'. NOT for Experience Cloud guest exposure or custom property editor design-time tooling."
category: flow
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - User Experience
  - Reliability
tags:
  - screen-flows
  - flow-ux
  - screen-components
  - flow-validation
  - navigation
triggers:
  - "how should i design a screen flow"
  - "screen flow validation is confusing"
  - "back button behavior in flow"
  - "custom lwc screen component in flow"
  - "when should screen flow save data"
inputs:
  - "how many screens the interview needs and where data should be committed"
  - "which standard or custom screen components are required"
  - "how validation, back navigation, cancel, and mobile usage should work"
outputs:
  - "screen-flow UX recommendation for navigation, validation, and commit timing"
  - "review findings for weak screen design or risky save placement"
  - "guidance for using standard components versus custom LWC screen components"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-15
---

Use this skill when the Flow is interactive and the quality of the user journey matters as much as the automation logic. Screen flows succeed when they guide the user through a deliberate sequence, validate at the right moments, and commit data only where the consequences are clear. They become fragile when navigation, validation, and side effects are all mixed together casually.

---

## Before Starting

Gather this context before working on anything in this domain:

- How many decision points and data-entry steps are truly necessary for the user to complete the task?
- Which fields can rely on standard screen components, and which require a custom LWC because the runtime UX truly differs?
- At what point should the flow create or update data, and what should happen if the user clicks Back, Cancel, or Next with invalid inputs?

---

## Core Concepts

Screen flows are interviews, not pages. That means the experience is stateful, sequential, and sensitive to where the design commits work. A strong screen flow keeps the user focused on entering or confirming information. A weak one starts performing irreversible actions too early or makes validation unpredictable between screens.

### Commit Timing Is A UX Decision

If the flow creates or updates records before the user reaches a natural confirmation point, Back and Cancel become much harder to reason about. In many cases, the best pattern is to gather inputs first, show a summary or final confirmation, and only then perform the final DML.

### Standard Components Are Usually Better Defaults

Flow screen components cover many common needs without custom code. Reach for a custom LWC screen component only when the interaction model, validation behavior, or rendering requirement truly exceeds what standard screen elements provide.

### Custom Screen Components Need A Validation Contract

A custom LWC used in Flow has to cooperate with Flow runtime validation intentionally. That means implementing the right methods and making sure internal validation, externally supplied error messages, and displayed errors stay consistent with how the user moves between screens.

### Navigation Should Feel Predictable

The number of screens, presence of a Back path, and clarity of button labels all shape the experience. If a flow has too many screens or too much hidden branching, users stop understanding where they are in the process.

---

## Common Patterns

### Gather, Review, Then Commit

**When to use:** The user enters meaningful data or confirms a business transaction.

**How it works:** Use one or more input screens to collect data, add a review screen if the decision matters, and perform DML only after the user confirms.

**Why not the alternative:** Early record mutation makes cancellation and back-navigation behavior harder to trust.

### Standard Components First, Custom Component Only For Real Gaps

**When to use:** Most inputs are standard, but one part of the experience needs custom UX or validation.

**How it works:** Keep the screen mostly standard, then isolate the exceptional interaction in one custom LWC screen component with a clear validation contract.

**Why not the alternative:** Rebuilding entire screens as custom components raises maintenance cost without better Flow design.

### Bounded Screen Count With Clear Branching

**When to use:** A process needs several decisions but should still feel guided.

**How it works:** Keep screens narrowly focused, reduce unnecessary branches, and ensure every path has clear button labels and exit expectations.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Guided user input with standard fields | Use standard Flow screen components | Fastest path to clear, supported UX |
| One input needs specialized rendering or validation | Add a focused custom LWC screen component | Contains custom complexity to one boundary |
| Data changes are significant or hard to undo | Commit near the end after review | Makes user intent and rollback expectations clearer |
| Many screens are needed for one task | Reassess the information architecture | The flow may be too fragmented or broad |
| Public or external-site embedding is the main problem | Use Experience Cloud flow guidance instead | Screen-flow design alone is not the full risk area |

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

- [ ] Each screen has one clear purpose and does not overload the user.
- [ ] Validation timing is predictable for both standard and custom components.
- [ ] Data commit points are intentional and not placed too early.
- [ ] Back, Next, Cancel, and Finish behavior all make sense to a real user.
- [ ] Custom screen components implement the needed validation contract.
- [ ] Mobile or smaller-screen behavior was considered when layout matters.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **A screen flow is not automatically reversible** - once DML has happened, Back and Cancel cannot behave like true undo.
2. **Custom screen components need to cooperate with Flow validation** - they do not get correct validation behavior for free.
3. **Too many screens feel like poor information architecture, not better guidance** - sequence alone does not improve UX.
4. **Standard components are easier to support than fully custom screen UIs** - custom screens should be the exception, not the whole design.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Screen-flow UX design | Recommendation for screens, navigation, and commit timing |
| Validation contract | Guidance for standard versus custom component validation behavior |
| Review findings | Risks in screen count, save placement, and user navigation |

---

## Related Skills

- `flow/flow-for-experience-cloud` - use when the screen flow is being embedded for external users or guest audiences.
- `flow/fault-handling` - use when the harder problem is failure behavior after the user submits.
- `lwc/custom-property-editor-for-flow` - use when the question is about Flow Builder design-time configuration rather than runtime screen UX.
