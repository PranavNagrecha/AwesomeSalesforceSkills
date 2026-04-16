---
name: flow-action-framework
description: "Use when designing or troubleshooting Salesforce Flow actions in Flow Builder: standard and core actions, the Apex action element for @InvocableMethod classes, how list-shaped inputs and outputs map at the Flow–Apex boundary, subflows, and choosing between declarative actions versus custom Apex versus packaged invocables. Triggers: 'Flow Apex action', 'add Apex to Flow', 'InvocableMethod in Flow', 'Flow action palette', 'map Flow variables to Apex invocable inputs'. NOT for authoring or testing Apex @InvocableMethod bodies (use the Apex invocable-methods skill), External Services or HTTP callout registration (use flow-external-services), OmniStudio action packs, or LWC screen component local actions."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
  - Performance
triggers:
  - "how do I call Apex from a Flow and wire the input and output variables"
  - "my Flow Apex action does not show my invocable class in the palette"
  - "why does my Flow pass a collection into an Apex action and only some rows come back"
  - "should I use a subflow or an Apex action for this automation step"
  - "what is the difference between a standard Flow action and a custom Apex action"
  - "how do I bulkify an Apex action that Flow calls in record-triggered context"
tags:
  - flow-action-framework
  - flow-builder
  - apex-action
  - invocablemethod
  - invocablevariable
  - subflow
  - core-actions
  - flow-orchestration
inputs:
  - "Flow type (screen, autolaunched, record-triggered) and whether the path runs in bulk"
  - "Whether the step is declarative-only, needs callouts, or needs Apex or a subflow"
  - "Apex class API name and whether @InvocableMethod exists and is visible to Flow"
  - "Input/output variable types in Flow versus wrapper properties on the Apex side"
outputs:
  - "Decision guidance for which action category fits the step"
  - "Flow Builder wiring pattern for Apex actions and variable mapping"
  - "Checklist for list-shaped contracts and fault handling at the action boundary"
  - "Pointers to Apex invocable design (invocable-methods) or External Services when scope shifts"
dependencies:
  - apex/invocable-methods
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-16
---

# Flow Action Framework

This skill activates when work centers on **Flow Builder actions**—the reusable steps in the toolbox and canvas—not on unrelated automation such as Process Builder migration or pure Apex services with no Flow surface. It explains how Salesforce groups work into action categories, how an **Apex action** element binds to an `@InvocableMethod`, why inputs and outputs are **list-shaped** at the platform boundary even when the builder feels single-record, and when a **subflow** or **standard action** is the better orchestration choice. Use it to route design questions, debug missing actions in the palette, and validate that variable mapping matches the invocable contract before runtime failures appear in production interviews.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Which Flow runtime is in play:** Screen flows, autolaunched flows, and record-triggered flows differ in user context, bulk behavior, and whether certain actions or callouts are allowed in the same transaction as triggering DML. Misclassification here is a common source of “works in test, fails in production.”
- **Whether the step must stay declarative:** If the requirement is only field updates, decisions, or platform messaging, a standard action or subflow often beats custom Apex. Apex belongs when the platform does not expose the operation declaratively or when you intentionally centralize logic behind a stable invocable contract.
- **Apex visibility and packaging:** An Apex action appears only when the class is compiled, the method is `public` or `global` and `static`, annotated with `@InvocableMethod`, and the running user can see the class. Managed-namespace classes expose only what the publisher designed. If the action is missing from the palette, verify visibility, API version, and packaging before rewriting Flow logic.
- **List contract at the boundary:** Flow passes a list of input rows into the invocable and expects a list of results aligned to that bulk shape. Treating the action as strictly single-record in design often breaks when record-triggered Flow batches many IDs through one interview.

---

## Core Concepts

### Action categories in Flow Builder

Flow Builder surfaces several families of actions. **Standard and core actions** cover platform capabilities such as record create or update, decisions, assignments, loops, and many productized operations (subject to edition and permissions). **Subflows** package reusable Flow definitions behind an action-shaped boundary with defined input and output variables. **Apex actions** bind to one `@InvocableMethod` on a class and map Flow variables to annotated request and response shapes. **External integrations** can appear as generated actions from External Services or related integration features when registered—those paths are detailed in the External Services skill. Understanding which family you are in determines limits, fault behavior, and how variables are typed.

### Apex action element and the invocable surface

The Flow element that calls Apex is documented as the Apex / invocable action; it resolves to a specific class and method advertised to Flow. The Flow author picks the action, sets input values or collections, and maps outputs to Flow variables or record fields. The Apex side must follow the invocable rules enforced by the compiler: a single list-typed input parameter for the method signature used by Flow, and a void or list return for outputs, with bulk-safe semantics. Field-level discoverability for Flow authors comes from `@InvocableVariable` metadata on wrapper types. This skill stays on the Flow side of that boundary; deep DTO design belongs in `invocable-methods`.

### Bulk interviews and variable typing

Record-triggered and bulk autolaunched paths can supply collections where a novice design assumed scalars. Collection variables, SObject collection variables, and formulas that evaluate per item all interact with how much work a single Apex action invocation performs. Choosing **Loop → Apex** versus **single Apex with a collection input** affects governor use and failure granularity. Standard actions that operate on `$Record` may still run in a bulk context behind the scenes; Apex actions make that bulk shape explicit in the method contract.

---

## Common Patterns

### Pattern 1: Single Apex action with collection input (preferred for bulk)

**When to use:** Multiple records or rows need the same transformation in one transaction and the Apex method is already list-oriented.

**How it works:** Build or verify a wrapper request type with `@InvocableVariable` fields. Flow passes an SObject collection or compatible collection into the Apex action input. Apex returns a matching list of response wrappers; Flow maps outputs with an Assignment or downstream elements.

**Why not the alternative:** Calling Apex inside a loop on a large collection multiplies CPU and DML overhead and obscures partial failure behavior compared to one bulk-chunked invocable.

### Pattern 2: Subflow as the stable action boundary

**When to use:** The same sequence of declarative steps is reused across many parent flows, or you want versioning and testing isolated behind input/output variables.

**How it works:** Create a child flow with input/output variables exposed to the parent. Parent Flow invokes **Run Subflow** and maps variables. Changes to internals of the child stay encapsulated.

**Why not the alternative:** Copy-pasting blocks of elements across flows drifts over time; a subflow gives one canonical implementation without jumping to Apex.

### Pattern 3: Standard action first, Apex only for the gap

**When to use:** The operation is mostly declarative but one step needs unsupported logic.

**How it works:** Implement the narrow Apex invocable for the gap only; keep surrounding steps as standard actions for readability and lower maintenance.

**Why not the alternative:** Replacing large declarative regions with Apex raises testing burden and hides self-documenting Flow structure from admins.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Platform supports the operation declaratively | Standard / core action | Fewer moving parts, easier admin review, no Apex deployment |
| Reuse across many flows with same inputs/outputs | Subflow | Encapsulation and change control without code |
| Logic not available declaratively, or shared with non-Flow callers via Apex | Apex action (`@InvocableMethod`) | Full language power behind a typed invocable contract |
| Typed REST operations from OpenAPI + Named Credential | External Service action (see `flow-external-services`) | Spec-driven fields and validation in Flow Builder |
| Need to teach Flow authors how to write the Apex method body | `invocable-methods` (Apex domain) | Compiler rules, wrappers, tests, and bulk safety live there |

---

## Recommended Workflow

1. Confirm Flow type, entry conditions, and whether the path processes one record, `$Record`-related collections, or unrelated bulk inputs.
2. Inventory the step: can a standard action or subflow satisfy it? If yes, prefer those before Apex.
3. If Apex is required, verify the class and `@InvocableMethod` compile, are visible to the running user, and use the list input contract; open `invocable-methods` for implementation review.
4. In Flow Builder, add the Apex action, map inputs using the correct scalar vs collection types, and name fault paths.
5. Decide failure strategy: unhandled exception vs structured per-row results returned to Flow for branching.
6. Test with bulk data sizes representative of production (especially record-triggered paths).
7. Document the action in team runbooks: inputs, outputs, required permissions, and governor-sensitive notes.

---

## Review Checklist

- [ ] Correct action category chosen (standard vs subflow vs Apex vs integration action).
- [ ] Apex action inputs and outputs match list-oriented invocable contract; no accidental per-row Apex in a tight loop without justification.
- [ ] Running user profile or permission set grants access to the Apex class and any queried objects.
- [ ] Fault connector or structured error outputs defined; no silent interview failures.
- [ ] Bulk scenarios tested for the same Flow path that will run in production.

---

## Salesforce-Specific Gotchas

1. **Missing Apex action in palette** — Usually visibility, API version, `global` vs `public` in managed packages, or the class failing compilation. Flow will not list invalid invocables.
2. **List size and output alignment** — Invocable methods operate on batches; Flow expects the bulk semantics documented for invocable methods. Mismatched assumptions show up as partial updates or “wrong row” symptoms.
3. **Callouts and DML in the same invocable** — Callout constraints still apply inside Apex invoked from Flow; mixing DML and callouts without proper ordering causes `System.CalloutException` in the interview.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Action decision table | Markdown or design-doc table mapping each step to standard, subflow, Apex, or integration action |
| Flow variable map | Document listing Apex action input/output names next to Flow variable API names and types |
| Test matrix | Bulk and single-record cases with expected Apex invocations and fault paths |

---

## Related Skills

- `invocable-methods` — Apex-side `@InvocableMethod` and `@InvocableVariable` design, tests, and bulk safety.
- `flow-external-services` — HTTP callout and External Services actions from Flow.
- `subflows-and-reusability` — Parent/child flow composition and variable contracts.
- `auto-launched-flow-patterns` — Autolaunched entry, bulk collection patterns, and API invocation context.
