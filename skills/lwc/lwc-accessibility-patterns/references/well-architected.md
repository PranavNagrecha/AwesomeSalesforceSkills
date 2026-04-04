# Well-Architected Notes — LWC Accessibility Patterns

## Relevant Pillars

### User Experience

Accessibility is a quality-of-use requirement, not a post-launch audit item. WCAG 2.1 AA compliance for AppExchange-listed apps means keyboard navigation, screen reader compatibility, and programmatic labeling are requirements the component must meet before release. Deferring accessibility to a remediation pass is more expensive than designing the keyboard contract and ARIA structure up front.

Specific UX concerns this skill addresses:
- Users who navigate by keyboard alone must be able to reach every interactive element and trigger every action.
- Users of screen readers must receive programmatic announcements when async state changes (results load, saves complete, errors appear).
- Focus must travel in a logical order that matches the visual reading order and the business workflow.

### Security

Staying with LWC platform base components (`lightning-button`, `lightning-input`, `lightning-datatable`) reduces custom DOM surface area. Custom DOM manipulation required to simulate accessible widgets introduces code paths that need their own security review. Base components are maintained by Salesforce and receive platform security updates automatically.

## Architectural Tradeoffs

- **Custom widget completeness vs maintenance cost:** A hand-rolled listbox or combobox must implement the full WAI-ARIA keyboard model, focus model, and ARIA state model. The team owns all of it forever. Base components own the maintenance burden instead.
- **Cross-component ARIA relationships vs single-component layout:** Designs that distribute a disclosure button and its controlled panel across separate LWC components cannot use `aria-controls`. The tradeoff is either collapsing the design into a single component template (simpler ARIA, less reuse) or managing the relationship through `@api` methods (correct behavior, more wiring).
- **Visual density vs accessible labeling:** Icon-dense toolbars and compact action columns save space but require explicit `aria-label` on every icon-only control. The tradeoff is either a slightly less compact design that includes visible labels or the engineering cost of maintaining accurate aria-labels across component versions.

## Anti-Patterns

1. **ARIA IDREF spanning shadow boundaries** — using `aria-controls`, `aria-owns`, or `aria-activedescendant` to point from one LWC component to an element inside another. The reference silently fails in all LWC shadow environments (Locker and LWS). The correct architecture is co-locating the linked elements in one template or replacing the ARIA relationship with explicit `@api` state management.
2. **Passive live region insertion** — conditionally rendering an `aria-live` container at the same moment content is needed, then immediately setting its text. Browsers only announce changes to regions they have already observed. The region must be present in the DOM (empty) before the text update fires.
3. **Half-complete custom button semantics** — adding `role="button"` without `tabindex="0"`, or adding `tabindex="0"` without a `keydown` handler for Space, or adding both without `event.preventDefault()` on Space. Each incomplete step produces a different category of keyboard failure.

## Official Sources Used

- LWC Accessibility Guide — https://developer.salesforce.com/docs/platform/lwc/guide/create-components-accessibility.html
- Lightning Design System Accessibility Overview — https://www.lightningdesignsystem.com/accessibility/overview/
- WCAG 2.1 — https://www.w3.org/TR/WCAG21/
- WAI-ARIA Authoring Practices Guide (Listbox Pattern) — https://www.w3.org/WAI/ARIA/apg/patterns/listbox/
- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
- Lightning Component Reference — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide
