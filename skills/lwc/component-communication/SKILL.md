---
name: component-communication
description: "Use when designing or reviewing how Lightning Web Components pass data and intent between parent, child, sibling, utility, or workspace contexts using `@api`, public methods, custom events, and Lightning Message Service. Triggers: 'LWC communication pattern', 'custom event not reaching parent', 'should I use LMS or @api', 'child component API'. NOT for data provisioning decisions, wire-service strategy, or page navigation when communication is not the main problem."
category: lwc
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - Reliability
  - Scalability
  - User Experience
tags:
  - component-communication
  - custom-events
  - lightning-message-service
  - api-properties
  - shadow-dom
triggers:
  - "how should lwc components talk to each other"
  - "custom event is not reaching the parent component"
  - "should i use lightning message service or @api"
  - "child component api feels too coupled"
  - "event detail is not crossing component boundaries"
inputs:
  - "component relationship such as parent-child, sibling, utility, or app-wide"
  - "whether the communication is state down, intent up, or cross-hierarchy broadcast"
  - "whether the interaction must cross shadow boundaries or page regions"
outputs:
  - "communication mechanism recommendation"
  - "review findings for coupling, propagation, and lms lifecycle issues"
  - "refactor guidance for public apis, custom events, or message channels"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

Use this skill when the LWC architecture is getting noisy because components are sharing too much, listening too broadly, or bypassing encapsulation to make something "just work." Good communication design keeps state directional, intent explicit, and cross-app coordination rare but disciplined.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the communication going down the tree, back up to an ancestor, or across unrelated component regions?
- Does the parent need to configure the child declaratively, or is the parent trying to trigger a one-off imperative action such as reset or focus?
- Is Lightning Message Service genuinely required, or would a simpler local contract remove coupling?

---

## Core Concepts

The right communication mechanism depends on direction and scope. Data should usually flow down, events should usually flow up, and broad broadcasts should be rare. Most LWC communication problems come from choosing the widest mechanism first and then trying to control the side effects later.

### `@api` Is For Parent-To-Child Contract Data

Public properties are the clean way to pass data and configuration into a child. They keep the child declarative and make the dependency obvious in markup. If the child only needs input, prefer `@api` properties over imperative DOM lookups or broad event choreography.

### Public Methods Are For Imperative Child Actions

Use a public `@api` method when the parent must tell a child to do something at a specific moment, such as clear a draft, validate inputs, or move focus. A public method is not a substitute for normal data binding. If a parent calls many child methods regularly, the component boundary may be wrong.

### Custom Events Carry Intent Upward

Children should dispatch custom events when they need to tell an ancestor that something happened. Event names should stay lowercase and intention-revealing. Propagation settings matter: if the event must cross a shadow boundary or bubble farther, that decision must be explicit instead of accidental.

### Lightning Message Service Is For Cross-Hierarchy Communication

LMS is the right answer when the publisher and subscriber are not in a direct ownership relationship, such as workspace tabs, utility components, or sibling regions. It is not the default answer for simple parent-child communication. The moment LMS appears, subscription lifecycle and message scope become architectural concerns.

---

## Common Patterns

### Config Down, Intent Up

**When to use:** A parent owns data or context and a child needs to render it and emit user intent.

**How it works:** Pass `@api` properties into the child. The child dispatches custom events such as `save`, `select`, or `cancel` with a small detail payload.

**Why not the alternative:** Reaching into the child DOM or sharing mutable objects both ways makes the contract brittle.

### Public Method For Reset, Validate, Or Focus

**When to use:** A parent needs to trigger a specific child action that is not naturally modeled as data.

**How it works:** Expose a narrow `@api` method such as `resetForm()` or `focusFirstError()`, obtain the child instance intentionally, and call only the smallest imperative surface needed.

**Why not the alternative:** Encoding one-time actions into permanent data flags usually causes stale state and rerender confusion.

### LMS For Workspace-Scale Coordination

**When to use:** Unrelated components must react to a shared selection, mode, or notification across page regions.

**How it works:** Define a message channel, publish a small payload, subscribe in components that truly need it, and clean up subscriptions when the component goes away.

**Why not the alternative:** A legacy pubsub helper or global DOM event pattern is harder to reason about and easier to leak.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Parent provides config or record context to child | `@api` property | Declarative and easy to read in markup |
| Parent needs child to perform a one-time action | Public `@api` method | Narrow imperative surface for reset, validate, or focus |
| Child needs to notify parent or ancestor that something happened | Custom Event | Keeps ownership upward and intent explicit |
| Unrelated components across regions must coordinate | Lightning Message Service | Designed for cross-hierarchy messaging |
| The solution depends on querying child `shadowRoot` or document-wide selectors | Redesign the boundary | Direct DOM coupling breaks encapsulation and scales poorly |

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

- [ ] Direction is clear: config down, intent up, or cross-hierarchy only when necessary.
- [ ] `@api` properties are used for state, not as a substitute for child methods.
- [ ] Public methods are narrow and action-oriented rather than broad data mutation hooks.
- [ ] Custom event names are lowercase and the propagation model is explicit.
- [ ] LMS subscriptions are scoped intentionally and cleaned up correctly.
- [ ] No component reaches into another component's `shadowRoot` to trigger behavior.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Custom events do not magically cross every boundary** - propagation depends on `bubbles` and `composed`, so cross-boundary behavior must be designed explicitly.
2. **Event names become listener APIs in markup** - uppercase names, spaces, or `on` prefixes create awkward or unsupported listener contracts.
3. **LMS introduces lifecycle responsibility** - a subscription that outlives the intended component scope becomes a debugging problem, not just a code smell.
4. **Direct `shadowRoot` access breaks encapsulation assumptions** - it may appear to work in one version of a component and fail as soon as the child implementation changes.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Communication decision | Recommendation for `@api`, public methods, custom events, or LMS |
| Contract review | Findings on coupling, event propagation, and message-channel scope |
| Refactor outline | Concrete changes to narrow boundaries and simplify communication |

---

## Related Skills

- `lwc/lifecycle-hooks` - use when communication bugs are really timing or cleanup bugs.
- `lwc/wire-service-patterns` - use when the main question is data provisioning instead of component contracts.
- `lwc/navigation-and-routing` - use when the event ultimately exists to drive page navigation rather than local component coordination.
