# Well-Architected Notes - LWC Accessibility

## Relevant Pillars

### User Experience

Accessibility is part of user experience, not an extra pass after styling is finished. Keyboard access, visible focus, and understandable announcements determine whether the component is usable at all for many users.

### Security

Security intersects with accessibility because teams often replace supported platform components with custom DOM manipulation that is harder to secure and harder to make accessible. Staying close to platform primitives reduces both categories of risk.

The sharpest instance of that overlap is light DOM. It is the guide's documented answer to
cross-component ARIA id association, and it is also the mode that exposes a component to DOM
scraping and, at the top level, drops Lightning Locker / Lightning Web Security protection. An
accessibility fix that reaches for light DOM is a security decision that needs the same review as
any other, and the guide's own mitigation — nest the light DOM component inside a shadow DOM
ancestor — should be part of the design, not a follow-up.

## Architectural Tradeoffs

- **Custom visual freedom vs reliable semantics:** bespoke markup can match a design faster, but the team inherits keyboard, focus, and ARIA behavior that base components already solve.
- **Icon density vs clarity:** compact icon-heavy UIs save space, but they need stronger labeling and focus treatment to stay understandable.
- **One reusable custom widget vs several simple components:** a single composite control can reduce duplication, but its accessibility contract becomes much more complex.
- **Composition granularity vs labelling:** splitting a field into `c-my-label` + `c-my-input` reads
  well as component design and breaks `for`/`id` association in shadow DOM. The accessible boundary
  is the whole form element — label, control, help text, error text — not each visual part.
- **`delegatesFocus` vs an explicit `@api focus()` method:** delegation is less code and gives the
  host `:focus` styling for free, but it forbids `tabindex` inside the component. An explicit method
  keeps `tabindex` available for composite widgets at the cost of every consumer knowing to call it.
- **Pinning `apiVersion` vs riding the release:** pinning freezes *your* component's framework
  behaviour, but base components and Lightning Data Service always run at the latest version. An
  accessibility regression that arrives via a base component is not held back by your pin.

## Anti-Patterns

1. **Clickable `div` design systems** - interaction spreads across non-semantic containers and becomes expensive to repair.
2. **Modal focus left to chance** - overlays open and close visually, but keyboard users lose context.
3. **ARIA used as a styling patch** - semantics are layered onto incorrect structure instead of choosing the right element first.
4. **ARIA references written across component boundaries** - `aria-labelledby` / `aria-describedby` /
   `for` pointing at an id in another template renders without error and associates nothing.
5. **Id-based selectors in JavaScript and CSS** - `querySelector('#thing')` and `#thing { }` silently
   miss, because template ids are rewritten at render time; use `lwc:ref` / `data-*` / `class`.
6. **`tabindex` used to sequence the tab order** - values other than `0` and `-1` are unsupported;
   tab order is fixed by DOM order, not by numbering.
7. **Accessibility asserted only by eye** - no Jest assertion on `for`/`id`, `aria-invalid`,
   `aria-describedby`, or `activeElement`, so the association can regress without failing a build.

## Official Sources Used

- LWC Developer Guide, *Component Accessibility* (`create-components-accessibility`) — the guide's
  own order of preference: follow WCAG, or use a Lightning base component, or build from an SLDS
  Blueprint (supports "Base components first" in Core Concepts and the Decision Guidance table).
  https://developer.salesforce.com/docs/platform/lwc/guide/create-components-accessibility.html
- LWC Developer Guide, *Accessibility Attributes* (`create-components-accessibility-attributes`) —
  base components associate the label you supply; template `id` values are rewritten at render time;
  ids and ARIA attributes link automatically only within one template and cannot be linked across
  templates in native shadow DOM; ARIA accessors are camel-case; host attribute defaults belong in
  `connectedCallback()`. Supports gotchas 5, 6, 7 and the whole `code-examples.md` design table.
  https://developer.salesforce.com/docs/platform/lwc/guide/create-components-accessibility-attributes.html
- LWC Developer Guide, *Handle Focus* (`create-components-focus`) — only `tabindex` `0` and `-1` are
  supported; focus skips the custom element container; `delegatesFocus` behaviour and its
  incompatibility with `tabindex`. Supports gotchas 1, 8, 9 and the focus contract in the workflow.
  https://developer.salesforce.com/docs/platform/lwc/guide/create-components-focus.html
- LWC Developer Guide, *Reflect Properties to Attributes* (`js-props-html-attributes`) — a property
  exposed with `@api` stops appearing as an HTML attribute; the nine id-referencing attributes
  (`for`, `aria-labelledby`, `aria-describedby`, `aria-controls`, `aria-owns`, `aria-details`,
  `aria-errormessage`, `aria-flowto`, `aria-activedescendant`) must use `setAttribute()` /
  `getAttribute()`. Supports gotcha 7 and the `ariaLabelledBy` accessor in `code-examples.md`.
  https://developer.salesforce.com/docs/platform/lwc/guide/js-props-html-attributes.html
- LWC Developer Guide, *Base Components Accessibility* (`base-components-accessibility`) — base
  components follow the W3C ARIA APG, update ARIA state on interaction, meet or exceed WCAG 2.1 AA
  contrast, and expose `alternative-text` for non-text content (WCAG 1.1.1), visually hidden via
  `slds-assistive-text`. Supports gotchas 2 and 4 and the "don't re-wrap what is already accessible"
  rule. https://developer.salesforce.com/docs/platform/lwc/guide/base-components-accessibility.html
- LWC Developer Guide, *Light DOM* (`create-light-dom`) — light DOM does not scope ids, so
  `<label for>` can reach an `<input id>` in a separate component; base components always render in
  shadow DOM; light DOM exposes components to DOM scraping and is unprotected by Locker/LWS at the
  top level. Supports gotchas 6 and 10 and the Security pillar note above.
  https://developer.salesforce.com/docs/platform/lwc/guide/create-light-dom.html
- LWC Developer Guide, *Support Datatable Accessibility* (`data-table-a11y`) — navigation mode vs
  action mode, the `tabindex="-1"` / `tabindex="0"` switch, and the `data-navigation="enable"` +
  `internalTabIndex` contract custom cell types must implement. Supports gotcha 11.
  https://developer.salesforce.com/docs/platform/lwc/guide/data-table-a11y.html
- LWC Developer Guide, *Access Elements the Component Owns* (`create-components-dom-work`) and
  *Write Jest Tests* (`unit-testing-using-jest-create-tests`) — `lwc:ref` / `this.refs` semantics,
  elements not yet rendered are absent from `querySelector` results, and `element.shadowRoot` as the
  test-only API for asserting shadow-tree state. Supports gotcha 3 and the Jest suite.
  https://developer.salesforce.com/docs/platform/lwc/guide/create-components-dom-work.html
- Lightning Design System Accessibility Overview — the `slds-assistive-text` utility and the
  blueprint markup base components implement (supports the visually-hidden live region in
  `code-examples.md`). https://www.lightningdesignsystem.com/accessibility/overview/
- WCAG 2.1 — the conformance target the guide tells you to follow; the source for live-region and
  focus-order expectations the LWC guide itself does not document.
  https://www.w3.org/TR/WCAG21/
