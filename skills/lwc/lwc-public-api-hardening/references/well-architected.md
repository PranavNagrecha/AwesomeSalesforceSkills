# Well-Architected Notes — LWC Public API Hardening

This skill maps to **Security**, **Reliability**, and **Operational Excellence** in the Salesforce Well-Architected framework. The thread that ties them together: a defensive, well-typed public surface is the single biggest leverage point for keeping LWC consumers (other components, Flow, App Builder, programmatic callers) from accidentally driving the component into an invalid state.

## Relevant Pillars

- **Security** — `@api` is the trust boundary between this component and every other LWC, Flow, App Builder admin, and programmatic caller. Hardening the surface is a security control:
  - *Trusted boundaries* — defensive setters reject malformed input (non-string `recordId`, NaN integers, mutated objects passed by reference) before that input flows into wires, Apex calls, or DOM rendering.
  - *Least privilege via `@api` discipline* — every `@api` property and method is part of the component's public attack surface. Exposing only what consumers need (and nothing implementation-detail-shaped) limits how downstream code can manipulate this component.
  - *Tamper-evident state* — a setter that validates and rejects bad input fails fast (logged, visible, observable) rather than silently producing wrong output that an attacker or buggy caller can exploit.
- **Reliability** — components with hardened public APIs survive every container they end up in:
  - *Predictable across surfaces* — App Builder, Flow runtime, Experience Cloud, programmatic instantiation, and unit tests all hand the component values shaped differently. A defensive setter normalises every shape into the same internal state, so the component renders predictably across all of them.
  - *Resilient to consumer mistakes* — when a parent mistakenly passes `null`, a string instead of a number, a stale object reference, or omits a required property, the hardened component either renders a fallback, fails fast with a clear error, or coerces — never produces silent NaN / undefined / "[object Object]" output.
  - *Recoverable* — `connectedCallback` guards turn missing-required-props into a single visible exception with a useful message, instead of a chain of opaque downstream wire errors.
- **Operational Excellence** — a documented public-API contract is the unit of operability:
  - *Manageable* — the contract template (`templates/lwc-public-api-hardening-template.md`) gives ops one place to look up "what does this component require, what does it emit, what does it expose imperatively." Lifts the cost of triage when a consumer breaks.
  - *Observable* — defensive setters that log on bad input (e.g. `console.warn` in non-prod) make integration bugs visible at the source instead of three wires deep.
  - *Evolvable* — public-API discipline means the component's internals can be refactored freely as long as the `@api` surface stays stable. The contract is the seam between change and consumer.

## Architectural Tradeoffs

| Hardening choice | Cost | Benefit |
|---|---|---|
| Replace `@api foo;` with `@api get/set foo` | More code; one extra backing field per property | Coerces input from every container; survives string/boolean/null cases automatically |
| Throw in `connectedCallback` for missing required props | Hard fail in unit tests that forgot to set them | Visible, debuggable failure with a useful message; avoids a wave of opaque downstream errors |
| Replace `@api` methods with `CustomEvent` flow | Refactor parent + child together | One-way contract; DOM-removal-safe; no recursion traps; testable in isolation |
| Per-target `<targetConfig>` defaults | XML duplication | Each target gets the right default for its admin context; programmatic callers never depend on defaults |
| `propertyType` for SObject input on Flow only | Two `<targetConfig>` blocks (Flow vs others) | Native SObject picker on Flow; typed-Id fallback elsewhere |

## Anti-Patterns

1. **Treating `@api` as a type system.** Annotating `@api recordId` as `number` in JSDoc and assuming it arrives as a number. The framework does not enforce types; it binds values.
2. **Public methods that should be events.** `@api refresh()` couples parent to child internals, invites recursion, and breaks when the child is removed mid-async.
3. **Trusting `default` on a design property as a runtime default.** App Builder sets it; programmatic instantiation, unit tests, and inline composition do not. Mirror the default in JS.
4. **Leaking implementation details via `@api`.** Exposing `_internalRowMap` or a method whose signature mirrors a private helper. The public surface should be the *intent* of the component, not the *shape* of its internals.
5. **Mutating an `@api` value in place.** A setter that does `this._rows.length = 0; this._rows.push(...v);` breaks LWC reactivity. Always reassign with a new value.

## Official Sources Used

- **LWC Developer Guide — `@api` decorator and public properties**: <https://developer.salesforce.com/docs/platform/lwc/guide/create-components-public-properties.html> — canonical reference for declaring public properties, getter/setter pairs, and the runtime semantics that this skill hardens against.
- **LWC Developer Guide — `@api` methods**: <https://developer.salesforce.com/docs/platform/lwc/guide/js-public-methods.html> — reference for public method declaration and the semantics this skill cautions against (over-using methods where events are appropriate).
- **LWC Developer Guide — Configure a Component for Lightning Pages and Lightning App Builder**: <https://developer.salesforce.com/docs/platform/lwc/guide/reference-configuration-tags.html> — schema for `<targets>`, `<targetConfig>`, `<property>`, `default`, `min`, `max`, `datasource`, and the per-target scoping behaviour.
- **LWC Developer Guide — Configure a Component for Flow Screens**: <https://developer.salesforce.com/docs/platform/lwc/guide/use-flow-screen.html> — `propertyType` and the SObject-input pattern that is Flow-only.
- **LWC Developer Guide — Get Started Best Practices**: <https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html> — practitioner guidance on event-vs-method, public surface design, and reactive re-rendering.
- **LWC Developer Guide — Reactivity**: <https://developer.salesforce.com/docs/platform/lwc/guide/reactivity.html> — the rules for class-field reactivity that drive the getter/setter caveats in this skill.
- **Salesforce Well-Architected Framework — Trusted (Secure)**: <https://architect.salesforce.com/well-architected/trusted/secure> — Security pillar framing for trust-boundary controls.
- **Salesforce Well-Architected Framework — Resilient**: <https://architect.salesforce.com/well-architected/adaptable/resilient> — Reliability framing for "predictable across surfaces" and "resilient to consumer mistakes."
