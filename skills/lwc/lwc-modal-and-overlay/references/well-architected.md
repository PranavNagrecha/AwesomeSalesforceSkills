# Well-Architected Notes - LWC Modal And Overlay

## Relevant Pillars

### User Experience

Overlays change how users move through the application. Choosing the lightest appropriate pattern and keeping dismissal clear improves flow and reduces friction.

### Reliability

Reliable overlays have explicit open, save, cancel, and close behavior. Weak result contracts or broken focus return create inconsistent experiences that are hard to reproduce.

## Architectural Tradeoffs

- **Modal focus vs on-page continuity:** a modal can focus the user on one task, but it removes page context and requires stronger lifecycle management.
- **Reusable modal component vs parent-owned markup:** centralizing overlay logic improves consistency, while local markup can feel quicker until defects accumulate.
- **Blocking save windows vs cancel freedom:** sometimes close must be delayed briefly, but extended lockout harms usability.

## Anti-Patterns

1. **Modal for every message** - the UI blocks users even when a toast or inline message would be clearer.
2. **Hand-rolled dialog markup everywhere** - focus and dismissal behavior drift across components.
3. **Nested overlay stacks** - users lose context and escape paths become unclear.

## Official Sources Used

- lightning-modal - https://developer.salesforce.com/docs/platform/lightning-component-reference/guide/lightning-modal.html
- Component Reference - https://developer.salesforce.com/docs/platform/lightning-component-reference/guide
- Best Practices for Development with Lightning Web Components - https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
