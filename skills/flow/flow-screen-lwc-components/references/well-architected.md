# Well-Architected Notes — Flow Screen LWC Components

## Relevant Pillars

The two pillars that bear most heavily on Flow Screen LWC design are
**Operational Excellence** (because admins consume the component long
after the developer who built it has moved on) and **User Experience**
(because the LWC is a runtime UI surface for end users completing a
business process).

- **Security** — applies via standard LWC security: any data the LWC
  reads from Apex flows through `with sharing` and FLS checks. The Flow
  itself runs in either System Context (default) or User Context, set
  per flow; the LWC inherits whatever sharing posture the Apex it calls
  enforces. Do not assume Flow's run context grants the LWC additional
  privileges — Apex called from the LWC still runs as the user.
- **Performance** — first-screen render time is the dominant metric. A
  screen LWC that pulls fresh data in `connectedCallback` adds latency
  to every screen render. Prefer pre-fetched Flow variables (cheap)
  over per-screen Apex calls (expensive). The synchronous `validate()`
  hook is also a performance constraint: anything done there blocks the
  Next click — keep it pure-function.
- **Scalability** — screen LWCs are per-user, per-screen, per-flow-run,
  so individual scaling is rarely the bottleneck. The bottleneck is the
  Apex they call: a screen LWC that fires an Apex query on every
  keystroke can cripple an org under heavy concurrent flow runs (think
  contact-center scripted flows during an outage). Debounce keystroke-
  triggered server calls.
- **Reliability** — `validate()` is the single point of truth for
  screen-level gating. If it returns the wrong shape, returns a Promise,
  or throws, navigation is silently allowed. The reliability discipline
  is to test the validation contract explicitly with Jest, not just by
  clicking through Flow Builder.
- **Operational Excellence** — `<targetConfig>` is documentation. Every
  `@api` property exposed there has a label admins read in the property
  panel. Treat the labels and descriptions as part of the public
  contract — they are how admins reuse the component. Components with
  cryptic property labels become unreusable shelfware within two
  release cycles.
- **User Experience** — synchronous `validate()` failures render at the
  top of the screen with the message returned. The wording matters: it
  is the single guidance the user sees. "Invalid input" is useless;
  "Case Reference must be CR- followed by 10 digits" is actionable.

## Architectural Tradeoffs

| Tradeoff | A | B | Recommendation |
|---|---|---|---|
| Stock screen component vs custom LWC | Faster to build, accessible by default, declarative validation | Pixel-perfect custom UX, complex cross-field rules, programmatic navigation | Default to stock. Justify custom LWC with a specific gap — see SKILL.md decision table. |
| Reactive (formula resource on stock) vs reactive (custom LWC pair) | Zero code, declarative | Necessary when the reactive output is computed by code that has no formula equivalent | Default to stock + formula resources. Use custom LWC pair only when computation cannot be a formula. |
| `validate()` blocking vs inline error rendering | Blocks Next, hard guard | Renders error but lets user scroll/edit other fields | Use both. `validate()` is the hard gate; inline rendering is the immediate feedback. |
| Programmatic Next vs user-clicked Next | Faster UX (scanner / kiosk), no extra click | Predictable flow path, easier to debug | Default to user-clicked Next. Programmatic Next only for scanner / single-question / kiosk patterns. |
| Apex-defined type input vs primitive inputs | Strong typing across LWC + Flow + Apex boundary | Simpler design-time UX, no extension binding to maintain | Use Apex-defined types when the same shape is consumed by multiple LWCs or invocable actions; otherwise use primitives. |
| Mobile support (`Small` form factor) declared vs not | Component runs on Salesforce mobile | Component is desktop-only by default | Declare mobile only if you have tested on a real device — don't declare blind support. |

## Anti-Patterns

1. **Asynchronous `validate()`.** Returning a Promise from `validate()`
   silently disables the validation. The Flow runtime treats the screen
   as valid. Pre-fetch validation data via `@wire` or
   `connectedCallback` and validate against the cached value
   synchronously. This anti-pattern is not just a bug — it is a
   security and data-integrity risk because users sail past intended
   guards.
2. **Mutating an output `@api` property without dispatching
   `FlowAttributeChangeEvent`.** The LWC's internal state diverges from
   the Flow variable. Downstream Flow elements operate on a stale
   value. The fix is mechanical: every mutation that should be visible
   to the Flow needs a paired `dispatchEvent(new
   FlowAttributeChangeEvent('propName', newValue))`.
3. **Sharing state between two screen LWCs via `pubsub` /
   `lightning/messageService` / DOM querying.** Bypassing the Flow
   variable model removes the Flow's record of what data drove
   downstream behavior, breaks Flow debugging, breaks reactive screen
   semantics, and tightly couples the two LWCs. Always route screen-
   LWC-to-screen-LWC state through a Flow variable.
4. **Hardcoding `FlowNavigationFinishEvent` in a reusable LWC.**
   Components that always call Finish cannot be safely dropped into
   multi-screen flows — they truncate the flow. Reusable screen LWCs
   should default to `Next` and use `availableActions` to detect
   terminal screens, only firing Finish when `FINISH` is in the list and
   `NEXT` is not.
5. **Skipping `<targetConfig>` and exposing `@api` properties only via
   the JS class.** Without `<targetConfig>` declarations, admins
   cannot configure the property in Flow Builder — the LWC works only
   when consumed by another LWC. This collapses the entire reason for
   building a screen LWC.
6. **Cryptic `<property>` labels in `<targetConfig>`.** Properties named
   `prop1`, `value`, `data` with no label or description are
   indistinguishable in the Flow Builder property panel. The component
   becomes a developer-only artifact. Treat labels and descriptions as
   the admin-facing contract.

## Operational Considerations

- **Versioning the I/O contract.** Renaming an `@api` property is a
  breaking change for every Flow that consumes the LWC — the property
  mapping in Flow Builder breaks silently. Add new properties; deprecate
  old ones; never rename. Document the contract in the LWC's README.
- **Testing the validation hook.** Jest tests must call `validate()`
  directly and assert the return shape AND that no Promise is returned:
  `expect(component.validate()).not.toBeInstanceOf(Promise)`. Without
  this, async-validate regressions ship undetected.
- **Telemetry.** When the LWC fires programmatic navigation, log the
  decision (success / failure / which path) to a centralized log object
  via Apex. Otherwise the flow path is unobservable in
  Flow Interview Logs because no Next click is recorded.
- **Migration of older flows.** When introducing a reactive screen LWC
  pair, audit the consuming Flow's API version. Flows below 59.0 do
  not propagate reactive updates; the LWC pair will appear broken
  without the API version being the actual cause.

## Official Sources Used

- Lightning Web Components Dev Guide — Build Components for Flow Screens: https://developer.salesforce.com/docs/platform/lwc/guide/use-flow-builder-screen.html
- Lightning Web Components Dev Guide — `lightning/flowSupport` Module Reference: https://developer.salesforce.com/docs/platform/lwc/guide/reference-lightning-flow-support.html
- Lightning Web Components Dev Guide — Configure a Component for Flow Screens: https://developer.salesforce.com/docs/platform/lwc/guide/reference-targets.html
- Salesforce Help — Reactive Screen Components: https://help.salesforce.com/s/articleView?id=sf.flow_concepts_screen_reactive.htm
- Salesforce Architects — Well-Architected: https://architect.salesforce.com/well-architected/overview
- Winter '24 Release Notes — Reactive Screens: https://help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow_builder_reactive_screens.htm
