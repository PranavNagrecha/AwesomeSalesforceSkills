# Well-Architected Notes — LWC Performance

## Relevant Pillars

### Performance

This skill is primarily about reducing payload size, avoiding unnecessary component creation, and giving the rendering engine stable identity for repeated DOM. Those choices directly affect first paint, interaction latency, and rerender cost.

### User Experience

Salesforce users experience performance as responsiveness. Progressive disclosure, bounded lists, and focused data queries keep record pages and app pages usable under realistic data volume.

### Operational Excellence

LWC performance regressions are often mechanical: deprecated directives, missing list keys, layout-based record fetches, or dynamic-component setup drift. A repeatable review checklist and static checker catch those issues before they become production complaints.

## Architectural Tradeoffs

- **Static imports vs dynamic components:** Static imports keep the runtime simpler and avoid network roundtrips. Dynamic components help only when a renderer is optional or unknown until runtime and the LWS plus managed-package constraints are satisfied.
- **Rich first paint vs progressive disclosure:** Loading every panel immediately can reduce follow-up latency, but it makes the initial experience heavier for every user.
- **Single giant list vs pagination or virtualization:** Full visibility sounds convenient, but the DOM and event cost grows fast. Bounded lists usually produce a better overall experience.
- **Custom Apex flexibility vs LDS/GraphQL efficiency:** Custom Apex can shape data exactly, but it also gives up LDS cache sharing and often invites overfetching if the contract is not tight.

## Anti-Patterns

1. **Fetching full layouts for narrow UI needs** — expensive payloads and slower initial render when explicit field reads would do.
2. **Instantiating every optional child component on first paint** — users pay for charts, secondary panels, and heavy renderers they may never open.
3. **Using dynamic import as the default import style** — runtime overhead and platform constraints outweigh the benefit for small or always-needed components.
4. **Keying repeated rows by index or omitting keys** — prevents efficient diffing and increases rerender churn.

## Official Sources Used

- Lightning Web Components Performance Best Practices — https://developer.salesforce.com/blogs/2020/06/lightning-web-components-performance-best-practices
- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
- Lightning Component Reference — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide
- LWC Data Guidelines — https://developer.salesforce.com/docs/platform/lwc/guide/data-guidelines.html
- Reactivity for Fields, Objects, and Arrays — https://developer.salesforce.com/docs/platform/lwc/guide/reactivity-fields.html
- Render Lists — https://developer.salesforce.com/docs/platform/lwc/guide/create-lists.html
- HTML Template Directives — https://developer.salesforce.com/docs/platform/lwc/guide/reference-directives.html
- Dynamic Components — https://developer.salesforce.com/docs/platform/lwc/guide/js-dynamic-components.html
