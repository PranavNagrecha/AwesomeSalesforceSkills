---
name: flow-decision-element-patterns
description: "Structure Decision elements in Flow: default outcome placement, outcome ordering, compound criteria, null-safe checks, Boolean vs Pick-list comparisons, and avoiding deep nested branching. Trigger keywords: decision element, flow branching. NOT for loop or fault path design, or Screen Flow navigation — use flow/flow-element-naming-conventions."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "decision element"
  - "flow branching"
  - "default outcome"
  - "compound conditions"
  - "hardcoded user id in flow decision"
  - "branch a flow on record type"
  - "check for null before a decision"
  - "order the outcomes of a flow decision"
  - "name the default outcome of a decision element"
  - "write custom condition logic in a flow"
  - "route an opportunity renewal with a decision element"
  - "test whether a field changed inside a flow decision"
  - "compare a multi-select picklist in a flow condition"
  - "flatten nested decisions in a flow"
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
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-12
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

## Questions to Ask Before Configuring

Ask these before opening Flow Builder. Each one maps to a documented failure in
`references/gotchas.md`, cited by number.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| Which of these fields can be null or blank, and does null mean the same thing as "matched nothing"? | A comparison against a null field is simply false, so the null population and the genuinely-different population share one path (Gotcha 3). Text fields have a third case: `IsBlank` covers zero characters or whitespace, `IsNull` covers "not set" (Gotcha 17). | A per-field answer of "null means incomplete" / "null means treat as X" / "null cannot happen because a validation rule blocks it" — the last one is checkable. | An explicit outcome per meaning, so incomplete data goes to a data-quality path instead of being counted as a business decision nobody made. |
| Can two outcomes ever be true for the same record, and if so which should win? | Rules "are evaluated in the order that they're listed, and the connector of the first true rule is used" (`api_meta.txt` L70247–L70250). An earlier broad outcome makes a later narrow one dead code with no warning (Gotcha 4). | A stated precedence per overlapping pair, which is also the review script: "which record reaches this outcome and not the one above it?" | An ordering you can defend at review, and no silently unreachable branch surviving into production. |
| What should happen to a record that matches nothing, and who owns that path? | If no rule is true the default connector runs (`api_meta.txt` L70233–L70234). It is simultaneously the intended fallback and the bucket for everything nobody considered, and nothing distinguishes them afterwards (Gotcha 5). | A business name for the case — "Standard renewal", "Needs triage" — rather than "the else". | A `defaultConnectorLabel` naming the real case, plus a log row where misrouting matters, so "deliberately defaulted" and "silently unmatched" are separable. |
| Is this rule about a *state* or a *transition* — must the record have just changed into it? | "Now equals X" and "just became X" are different rules that look identical on the canvas. `doesRequireRecordChangedToMeetCriteria` exists on `FlowRule`, not only on the Start element (Gotcha 14). | Per-outcome clarity on which branches are transition-shaped and which are plain state. | The transition test placed where it belongs: at the Start element when it gates everything, on the one outcome when it does not — instead of a hand-built comparison that is wrong on insert. |
| Are any of these values a multi-select picklist, or a Salesforce Id? | A multi-select value is one semicolon-delimited string, so `EqualTo` matches only the whole selection and `Contains` is a substring test with collisions (Gotcha 2). Id comparisons are the one case-sensitive text comparison (Gotcha 1). | The field types up front, and the actual API values from the value set rather than labels read off a record page. | Membership tested with an operator that means membership, and Ids compared to references instead of to pasted literals that stop matching after a refresh. |
| How many conditions does the combined rule need, and what is its AND/OR shape? | `conditionLogic` accepts `and`, `or`, or advanced logic such as `1 AND (2 OR 3)` (`api_meta.txt` L71306–L71313), and an unparenthesised mixed expression is a bet (Gotcha 8). Advanced logic is capped at 1,000 characters (Gotcha 13). | The requirement restated as a numbered expression before anything is built, which is where the ambiguity in the requirement surfaces. | Parentheses that make the expression self-documenting, and a term count low enough that the rule stayed in the element instead of outgrowing it. |
| How often will this list of outcomes change, and who will change it? | Outcomes that differ only in a literal — regions, tiers, product families — are data encoded as structure, and every addition costs an edit, a test, and a deploy, forever (Gotcha 12). | An expected change rate and an owner. "Sales ops adds a segment each quarter" and "this has not changed in three years" lead to different designs. | A Custom Metadata lookup for the volatile case, so adding a segment is a data change; branches only where the logic really is logic. |

A proper configuration here buys the ability to answer "why did this record go
there?" from the flow definition alone — ordered outcomes whose overlap is
deliberate, a named default, an explicit branch per meaning of null, and no rule
whose correctness depends on a literal nobody owns. Just building the Decision
produces something that routes most records correctly and cannot explain the
rest.

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

## Reference Files

| File | What it holds |
|---|---|
| `references/gotchas.md` | 17 non-obvious behaviours of conditions, outcomes, and operators, with Metadata API citations. |
| `references/examples.md` | Five worked outcome patterns plus three anti-patterns, as condition-level XML fragments. |
| `references/metadata-examples.md` | A complete, deployable Opportunity renewal-routing flow — ordered outcomes, a null-guard outcome, advanced `conditionLogic`, a named default, `package.xml`, deploy order, and a verification run of the checker. |
| `references/llm-anti-patterns.md` | Ten mistakes assistants make when generating Decision logic. |
| `references/well-architected.md` | Pillar mapping, architectural tradeoffs, hygiene checklist, and the annotated source list. |
