# Well-Architected Notes — Flow Custom Property Editors

## Relevant Pillars

### User Experience

This skill is primarily about admin experience inside Flow Builder. A good editor reduces setup mistakes and makes reusable components more approachable.

### Operational Excellence

Well-designed property editors reduce support load and improve reuse because the configuration model is discoverable, validated, and consistent across Flows.

## Architectural Tradeoffs

- **Default property pane vs custom editor:** The default builder UI is cheaper to maintain, but some components genuinely need stronger validation or guidance.
- **Simple editor vs context-aware editor:** Context-aware editors are more powerful, but they require tighter builder-contract discipline.
- **Runtime flexibility vs design-time safety:** More builder guidance can constrain free-form configuration, which is often a net positive for reusable enterprise components.

## Anti-Patterns

1. **Custom editor for every Flow-exposed component** — unnecessary complexity when the default property pane would suffice.
2. **Metadata, editor, and runtime drifting apart** — Flow Builder appears correct but the configured component fails at runtime.
3. **Builder-side logic doing runtime work** — the editor becomes harder to reason about and maintain.

## Official Sources Used

- Flow Reference — https://help.salesforce.com/s/articleView?id=sf.flow_ref.htm&type=5
- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
- Lightning Component Reference — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide
