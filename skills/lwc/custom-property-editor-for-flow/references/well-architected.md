# Well-Architected Notes - Custom Property Editor For Flow

## Relevant Pillars

- **User Experience** - the whole point of a custom editor is a clearer, safer builder experience.
- **Operational Excellence** - reusable components and clear contracts reduce admin support burden.

## Architectural Tradeoffs

- **Default Flow property pane vs custom editor:** less complexity versus better design-time UX.
- **Runtime/editor separation vs shared mental model:** cleaner contracts versus tempting shortcuts.
- **Rich builder logic vs simple editor:** more guidance versus more maintenance.

## Anti-Patterns

1. **Custom editor for a trivial case** - complexity without value.
2. **Broken metadata hookup** - editor exists but never runs.
3. **Visual editor with no value-change event** - looks finished, behaves incorrectly.

## Official Sources Used

- Custom Property Editor Interface - https://developer.salesforce.com/docs/platform/lwc/guide/use-flow-custom-property-editor-interface?-escaped-fragment-=.html
- Flow Reference Custom Property Editor - https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_screen_cpe.htm&type=5
- LWC Best Practices - https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
