# Well-Architected Notes — LWC Offline And Mobile

## Relevant Pillars

### User Experience

Mobile components succeed or fail on touch ergonomics, constrained space, and graceful fallback when device-specific features are unavailable.

### Reliability

Intermittent connectivity, background/resume behavior, and container differences make reliability a primary design concern.

### Performance

Mobile users are more sensitive to payload size, unnecessary rerenders, and interaction lag than desktop users.

## Architectural Tradeoffs

- **One component for every container vs specialized experience:** Reuse is attractive, but some mobile tasks need deliberate simplification or gating.
- **Deep device integration vs broad portability:** The more the component relies on mobile APIs, the more important runtime detection and fallback become.
- **Server dependence vs offline tolerance:** Rich server-driven behavior is easier to build, but it is fragile for mobile users with inconsistent connectivity.

## Anti-Patterns

1. **Assuming device APIs exist everywhere** — unsupported environments need intentional fallback behavior.
2. **Designing no reconnect or resume path** — mobile sessions are routinely interrupted.
3. **Reusing dense desktop interaction models unchanged** — touch ergonomics and small screens need a different design bias.

## Official Sources Used

- `lightning/mobileCapabilities` Module — https://developer.salesforce.com/docs/platform/lwc/guide/reference-lightning-mobilecapabilities.html
- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
- Salesforce Mobile App Overview — https://help.salesforce.com/s/articleView?id=sf.salesforce1_overview.htm&type=5
