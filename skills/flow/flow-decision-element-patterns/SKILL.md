---
name: flow-decision-element-patterns
description: "Structure Decision elements in Flow: default outcome placement, outcome ordering, compound criteria, null-safe checks, Boolean vs Pick-list comparisons, and avoiding deep nested branching. Trigger keywords: decision element, flow branching. NOT for loop or fault path design, or Screen Flow navigation — use flow/flow-element-naming-conventions."
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
  - hardcoded user id in flow decision
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
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# Flow Decision Element Patterns

## Adoption Signals

- A Decision element has 3+ outcomes.
- Conditions reference nullable fields, formulas, or pick-list values.
- Nested Decision after Decision in a record-triggered or screen flow.
- Performance concern: large collection filtered per-element.

## Out of Scope

- Single-outcome, single-condition gate — use a Get Records filter or
  entry criteria instead.
- Screen branching only — prefer the Screen's built-in component
  visibility.

## Three Operator Behaviours That Drive Everything Else

None of these is visible on the canvas, and each one produces a silent wrong
answer rather than an error.

1. **Text comparisons are case-insensitive — except for Ids.** Decision, Wait,
   and Collection Filter comparisons are case-insensitive for Text, Picklist, and
   Multi-Select Picklist values. Comparisons containing Salesforce Id values are
   **case-sensitive**. So normalising case is wasted work, distinguishing values
   by case does not work, and a hand-copied 15-character Id can fail to match its
   18-character form.
2. **A multi-select picklist is one semicolon-delimited string, not a set.** The
   operators treat `red; blue; green` as a single value, so `EqualTo` matches
   only the entire selection in that exact order. Membership needs `Contains`,
   which is a case-insensitive substring test that will also match a value which
   is a substring of another. Formula operators like `INCLUDES` do not exist in
   the Decision operator list.
3. **A set of operators exists only for `$Record` in a record-triggered flow.**
   They are how "did this change" is expressed. Among the three element types the
   operators reference covers — Decision, Wait, and Collection Filter — they are
   available *only* in Decision elements. Start-element entry conditions are a
   separate surface and **do** support `Is Changed`: on update-triggered flows
   only, not on create, and only with the "every time a record is updated"
   option rather than "only when a record is updated to meet the condition
   requirements."

## The Six Rules

1. **Every Decision has a named default.** Set `defaultConnectorLabel` to the
   case it actually represents — "Tier Low (no criteria met)," not "Default
   Outcome." The default is simultaneously the intended fallback and the
   catch-all for everything nobody considered, and only naming it separates the
   two afterwards.
2. **Outcome order matters.** Evaluation is top-down, first match wins, and Flow
   Builder does not warn about overlap. An outcome whose condition is a superset
   of a later one makes the later one dead code. Most specific first. Review each
   outcome by asking "which record reaches this one and not the one above it?"
3. **Null-safe every nullable field.** `Field = 'A'` is false when the field is
   null, so null and "some other value" share the default. Add an explicit
   outcome with the `IsNull` operator and a `booleanValue` of `true` — the
   operator takes a boolean right-hand value, so comparing to `''` is a different
   and usually wrong test.
4. **Boolean comparisons use the raw variable** against a `booleanValue`, not a
   string.
5. **Picklist equality uses the API value.** Labels are translatable; API values
   are not. Take the value from Setup → Object Manager → the field's value set,
   not from a record detail page.
6. **No Decision nested more than 2 deep.** Each level adds a default that
   silently absorbs cases, and the uncovered combinations are exactly the ones
   nobody thought about. Flatten, then extract a subflow if the flat list grows
   too large.

## Two Things Worth More Than the Six Rules

**Parenthesise every mixed AND/OR expression.** `conditionLogic` references
conditions by number and supports parentheses — write `1 AND (2 OR 3)`. Do it
even when you believe you know the precedence; the parentheses cost nothing and
remove a whole class of review error.

**Outcomes that differ only in a literal are data, not logic.** Three or more
structurally identical outcomes enumerating regions, tiers, or product families
belong in Custom Metadata: Get Records the matching row, and let the Decision
test whether one was found. Adding a region becomes a data change with no flow
edit, no test, and no deploy. This is the highest-leverage refactor available
here and almost nobody reaches for it first.

## Recommended Workflow

1. Write every outcome as a sentence ("if X then Y"), then order them most
   specific to widest and check each against "which record reaches this and not
   the one above?"
2. Name the default after the case it represents.
3. Null-audit every field referenced; add an explicit `IsNull` outcome wherever
   null means something different from "no match."
4. Check the operator semantics for anything multi-select, Id-valued, or
   transition-based before writing the condition — those three are where the
   silent wrong answers live.
5. Parenthesise mixed condition logic, and manage expression cost: extract
   anything beyond about four terms to a named Formula resource, and compute
   expensive cross-object formulas once into a variable before the Decision — a
   formula referenced by six outcomes is evaluated six times, and that multiplies
   again by the interview batch size.
6. If three or more outcomes differ only in a literal, stop and move the mapping
   to Custom Metadata.
7. Log which outcome fired — a breadcrumb in a screen flow, a log row in a
   record-triggered one — so misrouting is diagnosable.

## Official Sources Used

- Flow Operators in Decision, Wait, and Collection Filter Elements — https://help.salesforce.com/s/articleView?id=platform.flow_ref_operators_condition.htm&type=5
- Define Conditions in a Decision or Wait Element — https://help.salesforce.com/s/articleView?id=platform.flow_build_logic_conditions.htm&type=5
- Decision Element — https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_decision.htm&type=5
- How Entry Conditions Work in Record-Triggered Flows — https://help.salesforce.com/s/articleView?id=platform.automate_flow_build_working_with_conditions_record_triggered_flows.htm&type=5
- Flow metadata type (`FlowDecision`, `FlowRule`, `FlowCondition`) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_visual_workflow.htm

The full annotated list is in `references/well-architected.md`.
