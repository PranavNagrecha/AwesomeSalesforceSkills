# Well-Architected Notes — LWC State Management

**Scalability:** the mechanism should follow the relationship between the components, not
the developer's preference. `@api` and `CustomEvent` cost nothing at runtime and are
visible in the markup; a message channel adds a deployable metadata dependency and a
subscription lifecycle to every participant. Choosing the heavier mechanism for a
parent-child pair pays that cost permanently for no benefit, and it is the usual reason a
component turns out to be impossible to reuse on a second page.

**Reliability:** every subscription is a leak until its teardown is written. Lightning
Message Service subscriptions outlive the component that created them, so
`disconnectedCallback` has to call `unsubscribe`, and `connectedCallback` needs a guard —
it is not guaranteed to run only once per instance, and a second subscription to the same
channel means every message is handled twice. Hand-rolled stores carry the same obligation;
returning the teardown function from `subscribe` is the cheapest way to make the correct
usage also the easy one.

**User Experience:** the publish-before-subscribe race is the defect users report as
"sometimes it's blank". Nothing on the channel retains the last message, so a component
that renders late sees nothing, and whether it renders late depends on load order and
network speed — it reproduces for users and not for the developer. Designing "I arrived
late" as the normal case, either by retaining the current value somewhere readable or by
having late joiners ask for it, removes a whole class of intermittent bug.

**Container awareness:** Lightning Message Service is not available everywhere. It works in
Lightning Experience standard and console navigation, in the Salesforce mobile app for Aura
and LWC, and in components used in Aura and LWR-based Experience Builder sites — but not in
Salesforce Tabs + Visualforce sites or in Visualforce pages inside Experience Builder
sites, and published messages are constrained by an iframe boundary. Confirm the surfaces a
component will actually run on before the design depends on a channel; the fallback where
it is unavailable is ordinary parent-child plumbing through a wrapper, which works
everywhere.

## Official Sources Used

- Lightning Message Service — Message Service Limitations (supported and unsupported containers, the iframe constraint) — https://developer.salesforce.com/docs/platform/lwc/guide/use-message-channel-considerations.html
- Subscribe and Unsubscribe from a Message Channel (`subscribe`, `unsubscribe`, subscriber options) — https://developer.salesforce.com/docs/platform/lwc/guide/use-message-channel-subscribe.html
- Define the Scope of the Message Service (`APPLICATION_SCOPE` requires `@wire(MessageContext)`) — https://developer.salesforce.com/docs/platform/lwc/guide/use-message-channel-scope.html
- Publish on a Message Channel — https://developer.salesforce.com/docs/platform/lwc/guide/use-message-channel-publish.html
- Communicate Across the DOM — the platform position on pub/sub between components — https://developer.salesforce.com/docs/platform/lwc/guide/events-pubsub.html
