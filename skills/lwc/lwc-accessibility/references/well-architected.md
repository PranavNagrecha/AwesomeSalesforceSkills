# Well-Architected Notes - LWC Accessibility

## Relevant Pillars

### User Experience

Accessibility is part of user experience, not an extra pass after styling is finished. Keyboard access, visible focus, and understandable announcements determine whether the component is usable at all for many users.

### Security

Security intersects with accessibility because teams often replace supported platform components with custom DOM manipulation that is harder to secure and harder to make accessible. Staying close to platform primitives reduces both categories of risk.

## Architectural Tradeoffs

- **Custom visual freedom vs reliable semantics:** bespoke markup can match a design faster, but the team inherits keyboard, focus, and ARIA behavior that base components already solve.
- **Icon density vs clarity:** compact icon-heavy UIs save space, but they need stronger labeling and focus treatment to stay understandable.
- **One reusable custom widget vs several simple components:** a single composite control can reduce duplication, but its accessibility contract becomes much more complex.

## Anti-Patterns

1. **Clickable `div` design systems** - interaction spreads across non-semantic containers and becomes expensive to repair.
2. **Modal focus left to chance** - overlays open and close visually, but keyboard users lose context.
3. **ARIA used as a styling patch** - semantics are layered onto incorrect structure instead of choosing the right element first.

## Official Sources Used

- LWC Accessibility - https://developer.salesforce.com/docs/platform/lwc/guide/create-components-accessibility.html
- Lightning Design System Accessibility Overview - https://www.lightningdesignsystem.com/accessibility/overview/
- WCAG 2.1 - https://www.w3.org/TR/WCAG21/
