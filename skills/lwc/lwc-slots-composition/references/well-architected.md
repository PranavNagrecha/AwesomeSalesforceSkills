# Well-Architected Notes — LWC Slots Composition

## Relevant Pillars

- **Performance** — Slots avoid the runtime cost of stringifying and re-parsing injected markup. A correctly sized slot contract (one default slot + a small set of named slots) keeps the component instantiation tree shallow and lets `slotchange` drive reactive UI changes without polling `renderedCallback`. Avoid wide "catch-all" slot designs that force the child to re-measure large subtrees on every parent update.
- **Reliability** — Slots are the only supported way to pass composable markup — including nested LWCs — from a parent into a child while preserving event bubbling, component lifecycle, and accessibility metadata. String-based or `lwc:dom="manual"` alternatives bypass the framework and routinely break under rerender or locker upgrades.
- **Operational Excellence** — Slot-based APIs are self-documenting in the parent's template (the reader can see which region holds what) and they survive refactors of the child's internal structure without breaking callers. That reduces coordination cost across teams that share a design system.

## Architectural Tradeoffs

| Tradeoff | Choose Slots When | Choose The Alternative When |
|---|---|---|
| Slot vs `@api` string/object | The caller needs to pass markup, including nested components, icons, or accessibility-bearing elements | The caller passes a primitive value (string, number, object) that the child will render itself |
| Reusability vs coupling | The child has a stable chrome with a small, named set of regions | The regions are unstable — if the child keeps changing which slots exist, callers break silently because assignment to a removed slot is dropped without an error |
| Shadow DOM vs light DOM | You want style encapsulation and are willing to style slotted content from the parent | You need `::slotted()`, scoped slots, or third-party CSS to reach inside — light DOM is required |
| Fallback vs explicit API | The fallback is a safe default and callers usually override it | The state matters to the parent's logic — expose an event or `@api` property instead of inferring from slot emptiness |

The core design tension is between *reusability* (slots make the child composable) and *implicit coupling* (slot names become a contract the child cannot change without notice). Name slots conservatively, document each slot in the component's markdown, and treat a slot-name change as a breaking API change.

## Anti-Patterns

1. **Passing data through a slot** — Serializing an object into a slotted element so the child can parse it. This breaks reactivity, accessibility, and locker. Use an `@api` property for data; reserve slots for markup.
2. **`::slotted()` inside a shadow-DOM child's CSS** — Copying the pattern from open Web Components. LWC shadow DOM does not support `::slotted()`; the rule is silently dead. Either style from the parent or convert the child to light DOM.
3. **Multiple default slots in one template** — Declaring two unnamed `<slot>` elements so "any child can go anywhere." Assignment becomes ambiguous and the template fails. Always name additional slots.
4. **Polling `renderedCallback` for slot content** — Manually inspecting `this.template.querySelector('slot').assignedNodes()` on every render tick instead of wiring `onslotchange`. Wastes cycles and misses edge cases; `slotchange` is the framework-supported signal.

## Official Sources Used

- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
- Lightning Component Reference — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide
- LWC Data Guidelines — https://developer.salesforce.com/docs/platform/lwc/guide/data-guidelines.html
- Create Components With Slots — https://developer.salesforce.com/docs/platform/lwc/guide/create-components-slots.html
- Control Slot Assignment — https://developer.salesforce.com/docs/platform/lwc/guide/create-components-slot-assignment.html
- Handle the `slotchange` Event — https://developer.salesforce.com/docs/platform/lwc/guide/create-components-events.html
- Template Directives Reference (`lwc:slot-data`, `lwc:slot-bind`) — https://developer.salesforce.com/docs/platform/lwc/guide/reference-directives.html
