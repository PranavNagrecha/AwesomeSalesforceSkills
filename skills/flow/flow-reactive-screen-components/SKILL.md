---
name: flow-reactive-screen-components
description: "Build reactive Flow screens where one component updates another without navigation using reactive formulas and component outputs. NOT for Aura-based screens."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
triggers:
  - "reactive screen flow"
  - "flow screen update without next"
  - "dependent picklist reactive"
  - "flow live formula"
tags:
  - flow
  - reactive
  - screen
inputs:
  - "user workflow that benefits from reactivity"
  - "components involved"
outputs:
  - "reactive screen with live formula outputs"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Flow Reactive Screen Components

Reactive screens let one component's output drive another without navigating to a new screen. Use `{!Component_API_Name.value}` as a reference in any downstream component's attribute — Flow re-renders dependents on change. This skill shows reactive formulas, dependent picklists, and common pitfalls.

## When to Use

Any screen flow that currently uses multiple Next clicks to update displayed values.

Typical trigger phrases that should route to this skill: `reactive screen flow`, `flow screen update without next`, `dependent picklist reactive`, `flow live formula`.

## Recommended Workflow

1. Activate Reactive Screens via org setting (default on Winter '24+).
2. Use formula resources that reference component API names for derived values.
3. Reference `{!Source.value}` in dependent component attribute (Text, Default Value, Visibility).
4. Avoid complex loops/actions inside the screen — reactivity triggers on each change.
5. Test: tab through fields, observe updates in real time; verify mobile support.

## Key Considerations

- Not all standard screen components are reactive yet; check docs.
- Reactivity is synchronous — don't call heavy Apex actions in a reactive handler.
- Custom LWC screen components must implement `@api validate()` and emit `FlowAttributeChangeEvent` to be reactive.
- Visibility rules re-evaluate on each change.

## Worked Examples (see `references/examples.md`)

- *Live total* — Order quantity * price
- *Show/hide state field* — Country → State dependent

## Common Gotchas (see `references/gotchas.md`)

- **Heavy action in reactive** — UI freezes.
- **Custom LWC not reactive** — Doesn't update others.
- **Mobile lag** — Updates delayed.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Next clicks for trivially-derivable fields
- Heavy Apex action on every change
- Custom LWC screen without FlowAttributeChangeEvent

## Official Sources Used

- Flow Builder Guide — https://help.salesforce.com/s/articleView?id=sf.flow.htm
- Flow Best Practices — https://help.salesforce.com/s/articleView?id=sf.flow_best_practices.htm
- Reactive Screens — https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_screen_reactive.htm
- Flow HTTP Callout Action — https://help.salesforce.com/s/articleView?id=sf.flow_concepts_callout.htm
