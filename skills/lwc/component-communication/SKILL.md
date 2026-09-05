---
name: component-communication
description: "Choose and implement LWC communication — @api, events, LMS, @wire between parent, child, sibling, or workspace components. Triggers: 'LWC communication pattern', 'should I use LMS or @api', 'three components need to coordinate'. NOT for the mechanics of a single child-to-parent CustomEvent — bubbles / composed / cancelable, detail payload, event naming, or an event that is not reaching the parent — use lwc/lwc-custom-event-patterns. NOT for @wire data provisioning — use lwc/wire-service-patterns. More triggers: props down events up, component boundary design, public api vs public method, cross-hierarchy coordination, shadow boundary communication."
category: lwc
salesforce-version: "Spring '25+"
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
  - "should i use lightning message service or @api"
  - "child component api feels too coupled"
  - "event detail is not crossing component boundaries"
  - "three components need to coordinate and I do not know whether to use @api, events, or LMS"
  - "map out how these lwc components should talk to each other"
  - "pick a communication mechanism for parent child and sibling lwcs"
  - "decide whether to expose an api property or an api method on a child lwc"
  - "refactor lwc components that reach into each other's shadowroot"
  - "wire up three lwcs on a record page so they stay in sync"
  - "pass data from a parent to a child lwc component"
inputs:
  - "component relationship such as parent-child, sibling, utility, or app-wide"
  - "whether the communication is state down, intent up, or cross-hierarchy broadcast"
  - "whether the interaction must cross shadow boundaries or page regions"
outputs:
  - "communication mechanism recommendation"
  - "review findings for coupling, propagation, and lms lifecycle issues"
  - "refactor guidance for public apis, custom events, or message channels"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

Use this skill when the LWC architecture is getting noisy because components are sharing too much, listening too broadly, or bypassing encapsulation to make something "just work." Good communication design keeps state directional, intent explicit, and cross-app coordination rare but disciplined.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the communication going down the tree, back up to an ancestor, or across unrelated component regions?
- Does the parent need to configure the child declaratively, or is the parent trying to trigger a one-off imperative action such as reset or focus?
- Is Lightning Message Service genuinely required, or would a simpler local contract remove coupling?

---

## Questions to Ask Before Configuring

Ask these before a single `dispatchEvent` is written. Each one exists because a specific
platform behaviour, documented in `references/gotchas.md`, punishes the wrong assumption.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Draw the containment tree. Is the component that must react the *owner* of the one that acts, or something further up?" | `bubbles` and `composed` both default to `false`; only the owner's own template can listen without widening them | The propagation setting, chosen once, with a reason recorded next to the `dispatchEvent` |
| "Will this component ever sit in a `<slot>`, inside an Aura wrapper, or be surfaced as a quick action?" | A slotted child needs `bubbles: true` to reach its grandparent; an Aura wrapper can declare the handler only on the first component the event bubbles to | The one legitimate reason to move off the default, or confirmation that there isn't one |
| "What is going into `detail` — primitives, or a record that arrived from `@api` or `@wire`?" | Non-primitives are passed by reference and a listener can mutate them; the guide's rule is to send primitives, or a copy made before dispatch | A payload the listener cannot use to reach back into the child |
| "Which of the child's inputs are booleans, and what does each default to?" | `compact="false"` in markup evaluates to **true**; a boolean defaulting to `true` cannot be turned off statically at all | A boolean contract that behaves the way the markup reads |
| "Does the child ever need to change a value the parent passed down?" | Writing through an `@api` object reference raises `Invalid mutation … is read-only`, and only where LWS plus debug mode make it visible | An upward event plus an owner-side reassignment, instead of a bug that hides in production |
| "Where do the subscribers physically sit — active tab, background console subtab, utility bar, an iframe, an Experience Cloud site?" | Default scope delivers to the active area only; utility items are always active; LMS does not cross an iframe and does not exist in some containers | The `scope` argument, chosen for a reason, and an early answer on whether LMS is even available |
| "Who owns the message channel's field list, and will this ever ship in a managed package?" | `isExposed` cannot be lowered from `true` once set, AppExchange Security Review requires `false`, and Visualforce requires `true` | A named owner for the payload contract and a packaging decision made before the first release |

What a proper design adds over just making it work: the propagation setting, the `detail`
shape and the subscriber scope each become a written contract with a Jest assertion behind
it, so widening any of them later fails a test instead of silently enlarging the public API
of every ancestor component.

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

1. **Classify each hop, one at a time.** For every pair of components that must exchange
   something, write down the direction (down / up / across) and the containment
   relationship. Use the Decision Guidance table above; a hop that does not fit a row is a
   sign the component boundary is wrong, not that a wider mechanism is needed.
2. **Fill in the contract before the code.** Complete
   `templates/component-communication-template.md` — event name, `detail` fields,
   `bubbles`/`composed`, channel name and field list, subscriber scope, and which `@api`
   members are properties versus methods. Answer the seven questions above while filling it.
3. **Build from `references/code-examples.md`.** It carries the full deployable slice:
   the `.messageChannel-meta.xml`, the child with an `@api` setter and an `@api` method, the
   owner/publisher, the scoped subscriber, both `js-meta.xml` files, and `package.xml`.
   Reuse `templates/lwc/component-skeleton/` for loading and error state rather than
   restating it.
4. **Pin the contract with the three tests in § 5 of `references/code-examples.md`** —
   one asserting `detail`, `bubbles` and `composed` on the dispatched event; one asserting
   the `publish` arguments; one asserting the `subscribe` arguments and `unsubscribe` on
   disconnect through the mapped `lightning/messageService` mock. These are the tests that
   fail when someone widens propagation, changes the payload, or drops the cleanup.
5. **Run the checker over the source tree**:
   `python3 scripts/check_component_communication.py --manifest-dir force-app`. It flags
   uppercase or `on`-prefixed event names, a child writing through an `@api` property,
   `subscribe()` without `unsubscribe()`, `composed: true`, `shadowRoot` reach-through,
   `isExposed` without a `<target>`, and a `@salesforce/messageChannel` import with no
   matching `.messageChannel-meta.xml` in the tree.
6. **Walk the boundary cases from `references/gotchas.md`** before calling it done: the
   slot / Aura wrapper case, the background-console-subtab case, and the boolean-attribute
   case. Each of these looks correct in a two-component sandbox and fails in the real
   container.
7. **Record what you widened and why.** If any event ended up `composed: true`, any
   subscriber ended up `APPLICATION_SCOPE`, or any channel ended up `isExposed: true`, note
   the reason in the component's header comment — the last two are hard to reverse.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Direction is clear: config down, intent up, or cross-hierarchy only when necessary.
- [ ] `@api` properties are used for state, not as a substitute for child methods.
- [ ] Public methods are narrow and action-oriented rather than broad data mutation hooks.
- [ ] Custom event names are lowercase and the propagation model is explicit.
- [ ] LMS subscriptions are scoped intentionally and cleaned up correctly.
- [ ] No component reaches into another component's `shadowRoot` to trigger behavior.
- [ ] Every `detail` field is a primitive, or a copy made before dispatch.
- [ ] Every public boolean defaults to `false` and is written bare in markup to mean true.
- [ ] Subscriber `scope` was chosen from where the component sits, not copied.
- [ ] `subscribe()` is guarded against a repeat `connectedCallback` and paired with `unsubscribe()` in `disconnectedCallback()`.
- [ ] A Jest test asserts `bubbles`, `composed` and the `detail` shape, so widening them fails a test.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Custom events do not magically cross every boundary** - propagation depends on `bubbles` and `composed`, so cross-boundary behavior must be designed explicitly.
2. **Event names become listener APIs in markup** - uppercase names, spaces, or `on` prefixes create awkward or unsupported listener contracts.
3. **LMS introduces lifecycle responsibility** - a subscription that outlives the intended component scope becomes a debugging problem, not just a code smell.
4. **Direct `shadowRoot` access breaks encapsulation assumptions** - it may appear to work in one version of a component and fail as soon as the child implementation changes.
5. **A boolean `@api` property is an HTML boolean attribute** - presence means true, so `compact="false"` in markup sets it to true and only omitting the attribute sets it to false.
6. **Non-primitives arriving through `@api` are read-only proxies** - a child that writes through one raises an invalid-mutation error, but only where Lightning Web Security and debug mode are both on.
7. **`APPLICATION_SCOPE` is the background-subtab option, not the utility-bar option** - utility items already sit in the active area that default scope delivers to.
8. **`isExposed: true` on a message channel cannot be lowered** - and AppExchange Security Review requires it to be false.

The full set, each with the behaviour, when it bites, and how to avoid it, is in
`references/gotchas.md`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Communication decision | Recommendation for `@api`, public methods, custom events, or LMS |
| Contract review | Findings on coupling, event propagation, and message-channel scope |
| Refactor outline | Concrete changes to narrow boundaries and simplify communication |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/code-examples.md` | You are about to write the bundle: message channel XML, child with `@api` setter + method, owner/publisher, scoped subscriber, both Jest tests, `js-meta.xml`, `package.xml`, deploy and verify steps |
| `references/gotchas.md` | An event does not arrive, a boolean input behaves backwards, a subscriber is silent or fires after navigation, or a mutation throws `is read-only` |
| `references/llm-anti-patterns.md` | Reviewing generated LWC code — the six shapes assistants produce most often, with a detection regex each |
| `references/examples.md` | You want the shorter narrative walk-throughs and the shadow-boundary trace before committing to a mechanism |
| `references/well-architected.md` | Justifying the choice in a design review, or you need the official source behind a specific claim |
| `templates/component-communication-template.md` | Step 2 of the workflow — the worksheet that becomes the written contract |

---

## Related Skills

- `lwc/lwc-custom-event-patterns` - use once the mechanism is settled and the question is the event itself: `cancelable`, retargeting, naming, or why it is not arriving.
- `lwc/message-channel-patterns` - use for channel design at scale: payload versioning, multiple publishers, Aura and Visualforce subscribers.
- `lwc/lwc-public-api-hardening` - use when the `@api` surface needs defensive coercion and required-property checks; the decorator does not validate types.
- `lwc/lwc-reactive-state-patterns` - use when the symptom is "it changed but did not rerender" rather than "the message never arrived".
- `lwc/lwc-slots-composition` - use when the parent passes markup rather than data, which changes the propagation answer.
- `lwc/lwc-pubsub-patterns` - use only when the container does not support Lightning Message Service.
- `lwc/lwc-testing` - use to go beyond the two contract tests in this skill's code examples.
- `lwc/lifecycle-hooks` - use when communication bugs are really timing or cleanup bugs.
- `lwc/wire-service-patterns` - use when the main question is data provisioning instead of component contracts.
- `lwc/navigation-and-routing` - use when the event ultimately exists to drive page navigation rather than local component coordination.
