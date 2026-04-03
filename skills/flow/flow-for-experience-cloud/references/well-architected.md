# Well-Architected Notes — Flow For Experience Cloud

## Relevant Pillars

### Security

This skill is security-sensitive because guest or external users interact with the Flow through a site surface. User context, Apex exposure, and data visibility all need deliberate review.

### User Experience

Site-hosted flows are customer-facing or partner-facing experiences. Navigation, finish behavior, and site compatibility are part of the architecture, not just cosmetic choices.

### Reliability

Flows that work internally can fail in Experience Cloud due to runtime differences, unsupported component combinations, or missing exposed resources.

## Architectural Tradeoffs

- **Public reach vs security posture:** Guest exposure reduces friction, but it sharply increases the need for minimal data access and careful Apex review.
- **Direct page placement vs LWC wrapper:** Direct placement is simpler, while a wrapper gives more control over input/output variables and finish behavior.
- **Reuse of internal flows vs site-specific design:** Reuse feels efficient, but site audiences often need a narrower, safer flow contract.

## Anti-Patterns

1. **Reusing internal flows unchanged for external users** — internal assumptions about sharing and Apex access rarely survive site exposure.
2. **Ignoring LWR runtime limitations until build time** — the chosen page runtime can invalidate the intended flow-delivery approach.
3. **Treating guest flows like low-risk forms** — public automation surfaces deserve the same rigor as external APIs.

## Official Sources Used

- Experience Cloud Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.communities_dev.meta/communities_dev/communities_dev_intro.htm
- Flow Builder — https://help.salesforce.com/s/articleView?id=sf.flow.htm&type=5
- LWC `lightning-flow` embedding guide — https://developer.salesforce.com/docs/platform/lwc/guide/use-flow-embed-component.html
