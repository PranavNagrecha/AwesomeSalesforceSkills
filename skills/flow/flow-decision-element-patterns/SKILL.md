---
name: flow-decision-element-patterns
description: "Structure Decision elements in Flow: default outcome placement, outcome ordering, compound criteria, null-safe checks, Boolean vs Pick-list comparisons, and avoiding deep nested branching. Trigger keywords: decision element, flow branching, default outcome, condition logic, formula in decision. Does NOT cover loop or fault path design, or Screen Flow navigation."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - decision element
  - flow branching
  - default outcome
  - compound conditions
tags:
  - flow
  - decision
  - branching
  - conditions
  - null-safety
inputs:
  - Proposed Decision element or existing branching subgraph
  - Set of conditions with edge cases
outputs:
  - Normalised outcome list (ordered, null-safe, with default)
  - Suggested extraction into sub-flow where nesting is too deep
dependencies:
  - flow/record-triggered-flow-patterns
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# Flow Decision Element Patterns

## When To Use

- A Decision element has 3+ outcomes.
- Conditions reference nullable fields, formulas, or pick-list values.
- Nested Decision after Decision in a record-triggered or screen flow.
- Performance concern: large collection filtered per-element.

## When NOT To Use

- Single-outcome, single-condition gate — use a Get Records filter or
  entry criteria instead.
- Screen branching only — prefer the Screen's built-in component
  visibility.

## The Six Rules

1. **Every Decision has an explicit "Default" outcome** named after
   the case it actually represents (e.g. "No match"), not left as the
   implicit "Execute default outcome if none met" toggle.
2. **Outcome order matters.** Evaluation is top-down, first match wins.
   Put the most specific outcome first, the widest last.
3. **Null-safe every field reference.** `{!Record.Field} = 'A'` is
   **false** when the field is null but also when the field is `'B'`.
   Add an explicit `IS NOT NULL` branch when null means something.
4. **Boolean comparisons use the raw variable.** Use `{!isVIP} = true`
   — not a string or pick-list compare.
5. **Pick-list equality uses API value, not label.** In the Decision
   builder the API name is the one that matches, regardless of
   translation.
6. **No Decision nested more than 2 deep.** Extract into a sub-flow or
   a helper invocable.

## Recommended Workflow

1. List every outcome as a sentence ("if X then Y").
2. Order outcomes from most specific to widest.
3. Add a named default outcome for the "none of the above" case.
4. Null-audit every field referenced. Add explicit null checks where
   missing.
5. If the same condition repeats in 2+ decisions, promote to a Formula
   resource and reuse.
6. If depth exceeds 2, extract to a sub-flow named after the decision
   domain.
7. Add a screen-flow breadcrumb or a record-flow log entry identifying
   which outcome fired, for later triage.

## Official Sources Used

- Flow Decision Element —
  https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_decision.htm
- Flow Operators Reference —
  https://help.salesforce.com/s/articleView?id=sf.flow_ref_operators.htm
