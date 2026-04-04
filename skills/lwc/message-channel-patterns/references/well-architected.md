# Well-Architected Notes — Message Channel Patterns

## Relevant Pillars

- **User Experience** — LMS enables components in disparate page regions to stay in sync without requiring a full page reload or server round-trip. When used correctly (correct scope, minimal payload, synchronous handler), it produces a fluid, responsive UI. When misused (over-broadcast, heavy payload, stale subscriber), it degrades UX through flicker, stale data, or silent failures.
- **Reliability** — Subscription lifecycle management is the primary reliability concern. A missing `unsubscribe` in `disconnectedCallback` introduces a memory leak and causes stale handler execution after navigation. Deploying a component that imports an undeployed channel causes a hard load failure for the entire component region. Both failure modes are silent at design time and surface only at runtime.
- **Security** — The `isExposed` field on a channel controls whether components in other namespaces can publish or subscribe. Setting `isExposed: true` in a managed package intentionally opens the channel to subscriber orgs and external namespaces. AppExchange security review flags `isExposed: true` as a risk requiring explicit justification. Default new channels to `isExposed: false` unless cross-namespace use is a documented requirement.
- **Performance** — LMS message payloads must be serializable JSON. Large or deeply nested objects increase serialization cost and can cause handlers to block the main thread. Keep payloads minimal — pass IDs and short scalar values, not full record objects. Subscribers that trigger expensive `@wire` re-fetches on every message compound this cost.
- **Operational Excellence** — Message channels are metadata artifacts that must be tracked in source control, deployed in correct order, and documented in architecture diagrams. Channels that accumulate without a clear owner or documented subscriber list become orphaned infrastructure. Include channel name, field schema, publisher components, and subscriber components in team documentation.

## Architectural Tradeoffs

**Scope vs. predictability:** `APPLICATION_SCOPE` ensures all subscribers receive every message, but it also means inactive-tab components receive messages and may perform work the user cannot see. Default scope is predictable for tab-based apps but silently drops messages to inactive subscribers. Choose based on the user scenario, not as a blanket default.

**Payload size vs. consumer flexibility:** A minimal payload (record ID only) reduces bandwidth and serialization cost but forces each subscriber to independently re-fetch record data. A richer payload reduces server calls but creates tighter coupling between publisher and subscriber on the payload contract. For high-frequency channels, lean toward minimal payloads and subscriber-side wire fetches.

**LMS vs. wire service co-ordination:** In many master-detail patterns, the subscriber could alternatively be wired to a `currentPageReference` or a shared URL state parameter. Evaluate whether LMS is truly needed or whether a URL-based or wire-based coordination pattern would be simpler to test, debug, and maintain.

## Anti-Patterns

1. **Using LMS for parent-child communication** — LMS introduces deployment dependencies, lifecycle management overhead, and debugging complexity that is unnecessary when `@api` properties or custom events would serve the same purpose. If components share a direct ownership relationship in the LWC tree, use the appropriate directional mechanism. Reserve LMS for genuinely unrelated component regions.

2. **Omitting disconnectedCallback cleanup** — Subscribing without unsubscribing is a structural reliability defect. In console navigation, components are frequently cached across navigation events and will continue to receive messages and execute handlers on cached state. This pattern causes difficult-to-reproduce bugs that only appear after multi-step navigation flows, not on initial load.

3. **Deploying subscriber components before channel metadata** — Treating the message channel as an afterthought in deployment pipelines causes hard load failures that block entire page regions. Message channel metadata must be treated as a schema dependency, deployed ahead of any component that imports it, using the same discipline applied to custom fields and custom objects.

## Official Sources Used

- Lightning Message Service (LWC Dev Guide) — https://developer.salesforce.com/docs/component-library/documentation/en/lwc/lwc.use_message_channel
- LightningMessageChannel Metadata API Reference — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_lightningmessagechannel.htm
- Communicating Across the DOM (Aura Dev Guide) — https://developer.salesforce.com/docs/atlas.en-us.lightning.meta/lightning/message_channel.htm
- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
- Lightning Component Reference — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide
