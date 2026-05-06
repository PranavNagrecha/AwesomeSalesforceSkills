# Well-Architected Notes — LWC Pub/Sub Patterns

## Relevant Pillars

- **Performance** — Leaked subscriptions accumulate handler
  invocations across page navigations. Over time this produces
  duplicate-handler bugs and modest memory pressure. The cost is
  invisible until users notice.
- **Reliability** — LMS is the platform-supported pattern; the
  legacy `c/pubsub` utility is unsupported and accumulates technical
  debt. Reliability of the communication layer scales with whether
  the team picked the supported primitive.

## Architectural Tradeoffs

- **LMS vs `c/pubsub`.** LMS is the modern answer. `c/pubsub` works
  but is community-maintained, LWC-only, and not interoperable with
  Aura or Visualforce. New code uses LMS.
- **LMS vs Platform Events.** LMS is in-tab, low-latency, browser-
  side. Platform Events are cross-tab / cross-user / cross-org,
  durable, server-side. They serve different needs.
- **`APPLICATION_SCOPE` vs `ACTIVE`.** APPLICATION is broader and
  often the right choice for cross-cutting components (utility bar,
  notification surface). ACTIVE is the safer default for page-only
  communication.
- **LMS vs parent-child events.** Parent-child should always use
  props and `CustomEvent`. LMS in parent-child obscures intent.

## Anti-Patterns

1. **Subscribe without unsubscribe.** Leaks handler invocations.
2. **LMS in parent-child relationships.** Use props / CustomEvent.
3. **Cross-tab LMS expectation.** LMS is per-tab.
4. **Non-serializable LMS payloads.** Functions / instances are
   stripped.
5. **Recommending `c/pubsub` for new code.** Use LMS instead.

## Official Sources Used

- Lightning Message Service Developer Guide — https://developer.salesforce.com/docs/component-library/documentation/en/lwc/lwc.message_channel
- Communicate Across the DOM with Lightning Message Service — https://developer.salesforce.com/docs/component-library/documentation/en/lwc/lwc.use_message_channel_dom
- Lightning Component Library: messageService — https://developer.salesforce.com/docs/component-library/bundle/lightning-message-service
- LWC Component Lifecycle — https://developer.salesforce.com/docs/component-library/documentation/en/lwc/lwc.create_lifecycle_hooks
- Salesforce Well-Architected Resilient — https://architect.salesforce.com/well-architected/trusted/resilient
- Salesforce Well-Architected Composable — https://architect.salesforce.com/well-architected/adaptable/composable
