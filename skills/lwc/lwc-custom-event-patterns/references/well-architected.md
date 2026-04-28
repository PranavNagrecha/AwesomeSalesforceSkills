# Well-Architected Notes — LWC Custom Event Patterns

This skill maps to **Reliability**, **Operational Excellence**, and **Security** in the Salesforce Well-Architected framework. Custom events are a thin runtime contract between components — getting the contract right keeps the UI predictable, the side effects auditable, and the trust boundary clean.

## Relevant Pillars

- **Reliability** — events that respect shadow DOM boundaries deliver consistently, and listeners that read `event.currentTarget` and `event.detail` defensively avoid retargeting bugs and shared-state corruption:
  - *Available* — a child dispatching with the correct `bubbles`+`composed` combination has a predictable contract; the listener fires every time, not "sometimes when QA looks closely." Forgetting `composed: true` causes the failure to be invisible until production.
  - *Resilient* — `cancelable` events with a proper `defaultPrevented` check let a parent veto a child action without the child needing to know who the parent is. The component remains usable regardless of where in the page it is dropped.
  - *Recoverable* — an event with an immutable detail payload (frozen array, `structuredClone`d object) cannot be corrupted by a misbehaving listener. The dispatcher's internal state is protected even when the listener is third-party code.
- **Operational Excellence** — clear naming and a documented events catalog make components observable and modifiable:
  - *Observable* — when every component has an events catalog (`templates/lwc-custom-event-patterns-template.md`) listing event names, payload shapes, and flag combinations, debugging "why did this event not reach the parent?" becomes a five-minute lookup instead of a `git blame` archaeology session.
  - *Manageable* — single-token lowercase event names match `on<name>` declarative attributes deterministically. No naming drift, no hyphen-vs-camelCase questions, no `onSelect` vs `onselect` mismatches.
  - *Adaptable* — a child that dispatches `bubbles: true, composed: true` can be relocated anywhere in the tree (Aura host, deep LWC nesting, slot projection) without rewiring. The encapsulation seam is the event name + payload contract, not the DOM topology.
- **Security** — custom events are a vector for state leakage and recursive misbehaviour if not defensive:
  - *Trusted* — freezing or cloning the detail payload prevents a downstream component (especially third-party LWCs from AppExchange) from mutating the dispatcher's internal data through the shared reference.
  - *Recursion-safe* — a listener that calls a method which dispatches the same event re-enters the listener. Without a guard flag this loops until the JS stack overflows or the component is unmounted. Documented event flow makes recursive paths visible at design time, not at incident time.
  - *Least-privilege payloads* — `detail` should carry only the IDs and primitives the listener needs. Sending the full record (with FLS-protected fields) leaks data to any ancestor that cares to look. Treat `detail` as a public API on the component.

## Concrete Reliability Wins

| Before defensive practice | After |
|---|---|
| Grandparent listener "sometimes" fires depending on testing order | Always fires (`composed: true` set explicitly) |
| Parent mutates `event.detail.items`, child UI desyncs intermittently | Parent receives a frozen snapshot; mutation throws |
| `event.target` reads `undefined` after retargeting | `event.currentTarget` reads the listener-bound element deterministically |
| Modal closes despite parent vetoing it | `event.defaultPrevented` check honours the veto |
| Recursive event chain crashes the tab on certain user paths | Re-entrancy guard breaks the loop with a logged warning |

## Architectural Tradeoffs

- **Composed events are higher blast radius.** Setting `bubbles: true, composed: true` lets the event reach the document root, the Aura wrapper, and any global listener. That is intended when the listener is genuinely far away — but for direct parent / direct child cases it leaks the event into places that may attach unwanted behaviour. Default to false; promote only when the listener cannot otherwise be reached.
- **CustomEvent vs Lightning Message Service is a coupling decision.** CustomEvent ties the dispatcher and listener through DOM topology — they must share an ancestor LWC. LMS decouples them entirely but requires a Message Channel metadata file and a subscription lifecycle. Use CustomEvent when the components are co-designed; use LMS when they are independently deployed or live in unrelated regions.
- **Cancelable events add a two-sided contract.** The dispatcher must check `defaultPrevented`; the listener must call `preventDefault` synchronously inside the handler. This is more brittle than a fire-and-forget event — only use it when veto semantics are genuinely required.
- **`@api` properties cannot do what events do.** Parent-to-child push is `@api`; child-to-parent signal is CustomEvent. Trying to use one in place of the other inverts the data flow and produces components that work but feel wrong to extend. The decision tree in `SKILL.md` is non-negotiable on this point.

## Anti-Patterns

1. **Forgetting `composed: true` on cross-boundary events** — the silent killer. The event dispatches without error, the listener never runs, and the bug is invisible until QA runs the right scenario. Make the flag combination explicit in every dispatch and document it in the events catalog.
2. **Mutating `event.detail` in the listener** — pretending the payload is private state when it is actually a shared reference. Fix at the dispatcher: snapshot before dispatch with `Object.freeze`, `[...arr]`, or `structuredClone`.
3. **Using CustomEvent to push data DOWN to a child** — `dispatchEvent` on `template.querySelector('c-child')` instead of binding an `@api` property. Inverts the natural data flow and hides configuration from markup.
4. **Cross-region broadcast via bubbled+composed CustomEvents** — relying on global propagation to reach an unrelated subtree. Use Lightning Message Service; CustomEvent is for in-tree communication.
5. **Recursive event-driven loops** — a parent listener that updates state, which causes a child re-render, which dispatches the same event back to the parent. Add a flag (`this._handlingX = true; ... finally { this._handlingX = false; }`) or move the side effect outside the handler.
6. **Letting `event.detail` carry FLS-restricted fields** — sending a full SObject record up to the page chrome leaks data to whoever attached a global listener. Send IDs; let the listener re-fetch with the appropriate access level.

## Official Sources Used

- **Lightning Web Components Developer Guide — Communicate with Events**: <https://developer.salesforce.com/docs/platform/lwc/guide/events.html> — canonical guidance on `dispatchEvent(new CustomEvent(...))`, the `bubbles` / `composed` flags, and event naming rules. Confirms the single-lowercase-word naming convention and the deprecation of legacy `pubsub.js`.
- **Lightning Web Components Developer Guide — Configure Event Propagation**: <https://developer.salesforce.com/docs/platform/lwc/guide/events-configure-propagation.html> — the bubbles+composed truth table reproduced in `SKILL.md`, including the cross-shadow retargeting behaviour that drives `event.target` vs `event.currentTarget` choice.
- **Lightning Web Components Developer Guide — Communicate Across the DOM with a Lightning Message Service**: <https://developer.salesforce.com/docs/platform/lwc/guide/use-message-channel.html> — the LMS guidance referenced when CustomEvent is the wrong tool.
- **Lightning Web Components Developer Guide — Communicate Down the Containment Hierarchy**: <https://developer.salesforce.com/docs/platform/lwc/guide/js-props-public.html> — `@api` properties, the parent-to-child equivalent of custom events.
- **MDN — `CustomEvent` constructor**: <https://developer.mozilla.org/en-US/docs/Web/API/CustomEvent/CustomEvent> — the underlying browser contract for `bubbles`, `composed`, `cancelable`, and `detail`.
- **MDN — `Event.stopImmediatePropagation()`**: <https://developer.mozilla.org/en-US/docs/Web/API/Event/stopImmediatePropagation> — the difference between `stopPropagation` and `stopImmediatePropagation` referenced in gotcha 6.
- **Salesforce Architects — Lightning Web Components in Lightning Experience**: <https://architect.salesforce.com/decision-guides/lightning-experience-design> — Well-Architected framing for LWC component design (Reliability, Operational Excellence).
- **Repo skill `lwc/component-communication`** — the higher-level decision tree for `@api` vs CustomEvent vs LMS this skill drills into.
