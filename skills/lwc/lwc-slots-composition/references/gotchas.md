# Gotchas — LWC Slots Composition

Non-obvious behaviors of `<slot>` composition in LWC that cause real production bugs.

## Gotcha 1: Named-Slot Fallback Renders Only When Assignment Is Empty

**What happens:** You add fallback content inside a named slot (`<slot name="footer">Default footer</slot>`). When the parent passes no footer content, the fallback renders as expected. But when the parent accidentally leaves a whitespace-only text node in the slot position, the fallback *stops* rendering and the slot looks blank.

**When it occurs:** Any time the parent template contains stray whitespace or line breaks inside the custom element tag. Multi-line parent markup is the usual culprit.

**How to avoid:** When emptiness matters, verify with `assignedNodes({ flatten: true })` inside a `slotchange` handler and filter out whitespace-only text nodes. Do not rely on fallback alone for conditional wrappers.

---

## Gotcha 2: `slot="..."` Goes On The Parent's Children, Not The Child's `<slot>`

**What happens:** A developer writes `<slot name="header" slot="header">` or `<slot slot="header">` inside the child's template and then wonders why "nothing is being assigned to the header." The `slot` attribute on `<slot>` is meaningless for naming — the `name` attribute is what names a slot.

**When it occurs:** During early refactors from `@api` props to slots, or when copying patterns from Web Components articles that mix terminology.

**How to avoid:** The rule is: child template declares `<slot name="header">`; parent template tags its children with `slot="header"`. Both attributes never appear on the same element.

---

## Gotcha 3: Slotted Content Is Styled By The Parent, Not The Child

**What happens:** Inside a shadow-DOM child's `.css` a developer writes `::slotted(h2) { font-weight: 700; }` and the rule has no effect. The slotted `<h2>` keeps its default weight.

**When it occurs:** Any time a developer assumes LWC shadow DOM mirrors the full custom-elements spec. LWC's shadow DOM has explicitly different scoping rules.

**How to avoid:** Style slotted elements from the parent's CSS (they live in the parent's scope). If you need the child to control slotted styling, use a light-DOM child component or expose a documented CSS hook via custom properties.

---

## Gotcha 4: `slotchange` Fires More Often Than You Think

**What happens:** A `slotchange` handler runs expensive work (logging, metric emission, network call), and developers notice it firing on initial render AND every re-render that touches the assigned nodes — sometimes dozens of times during a single user interaction.

**When it occurs:** Whenever the parent's template re-renders the slotted content, even if the logical set of nodes is unchanged.

**How to avoid:** Treat `slotchange` handlers as idempotent toggles. Compare against the previous `assignedNodes()` snapshot before doing expensive work. Never trigger Apex or navigation from inside a `slotchange` handler.

---

## Gotcha 5: `::slotted()` And Shadow-DOM Slot Styling Do Not Work In LWC Shadow DOM

**What happens:** A developer ports a pattern from open Web Components where `::slotted()` is standard. In LWC's shadow DOM this selector does not match and the CSS appears dead.

**When it occurs:** Library ports, blog-post patterns, or design-system copy-paste.

**How to avoid:** Use parent-side CSS for slotted content. If the pattern fundamentally needs child-side control, convert the child to a light-DOM component (declared in `.js-meta.xml`) where normal CSS cascading applies.

---

## Gotcha 6: Slots Are For Markup, Not Data

**What happens:** A developer "passes a record" through a slot by rendering `<span slot="record">{{JSON.stringify(record)}}</span>` and then tries to parse it in the child. This works once and then falls apart under rerender, accessibility audits, and security review.

**When it occurs:** When a team tries to avoid declaring an `@api` property and reuses a pattern from template engines like Handlebars.

**How to avoid:** Keep the contract clean — slots carry markup; `@api` properties carry data; events carry upward signals. If you find yourself serializing data through markup, stop and add an `@api` property.

---

## Gotcha 7: Scoped Slots Are Light-DOM Only

**What happens:** A developer adds `lwc:slot-bind={row}` to a `<slot>` inside a shadow-DOM child and the template fails to compile or the binding silently does not reach the parent.

**When it occurs:** When teams first discover scoped slots and try to retrofit them into existing shadow-DOM components.

**How to avoid:** Scoped slots (`lwc:slot-data`, `lwc:slot-bind`) are supported only in light-DOM components. Convert the child to light DOM before using them, and document the tradeoff (no style encapsulation) for reviewers.
