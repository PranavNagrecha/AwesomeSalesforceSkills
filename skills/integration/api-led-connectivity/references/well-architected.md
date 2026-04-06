# Well-Architected Notes -- API-Led Connectivity

## Relevant Pillars

- **Scalability** -- API-led connectivity enables horizontal scaling at each layer independently. System APIs can be scaled to handle backend throughput, Process APIs to handle orchestration load, and Experience APIs to handle consumer traffic. The layered model prevents a single scaling bottleneck from propagating across the architecture.

- **Reliability** -- Layer separation creates natural fault isolation boundaries. A System API failure for one backend does not take down the entire integration. Circuit breakers, retries, and fallback logic can be applied at each layer boundary. Process APIs can implement graceful degradation (return partial data when one System API is down).

- **Security** -- Each API layer is a security enforcement point. System APIs enforce backend-specific authentication (certificates, API keys). Process APIs enforce business-level authorization (which consumers can invoke which operations). Experience APIs enforce consumer-level access control (rate limiting, OAuth scopes). Defense-in-depth is a natural byproduct of the layering.

- **Operational Excellence** -- API-led connectivity supports independent deployment, monitoring, and troubleshooting per layer. Each API has its own CI/CD pipeline, health checks, and logging. Ownership boundaries align with organizational structure (platform team owns System APIs, business team owns Process APIs, channel team owns Experience APIs).

## Architectural Tradeoffs

1. **Reuse vs. latency** -- Every additional layer adds a network hop (~30-100ms per hop depending on infrastructure). The reuse and change-isolation benefits must be weighed against the cumulative latency. For latency-sensitive Salesforce UI integrations (screen load callouts), prefer fewer layers unless reuse across multiple consumers is proven.

2. **Governance vs. agility** -- API-led connectivity encourages governed, cataloged APIs with formal contracts. This is valuable at scale but can slow down small teams building a single integration. Match governance rigor to organizational size and integration portfolio complexity.

3. **Standardization vs. over-engineering** -- The three-layer reference architecture is a starting point, not a mandate. Applying all three layers to every integration regardless of complexity wastes engineering effort and creates unnecessary operational burden. The architecture should be right-sized per integration.

## Anti-Patterns

1. **Point-to-point spaghetti** -- Every consumer connects directly to every backend with custom mapping, auth, and error handling. Backend changes ripple to every consumer. This is the problem API-led connectivity solves, but it re-emerges when teams bypass the API layers "just this once" for speed.

2. **Mandatory three layers regardless of consumer count** -- Applying System + Process + Experience to a one-consumer, one-backend integration adds latency and maintenance cost with zero reuse benefit. The three-layer model is a reference architecture to adapt, not a compliance checklist.

3. **Treating API-led as a MuleSoft-only pattern** -- API-led connectivity is an architectural pattern that can be implemented with any integration platform (MuleSoft, Boomi, custom middleware, or even Salesforce-native tools). Conflating the pattern with a specific product limits architectural thinking and vendor flexibility.

4. **Monolithic Process API** -- Combining all cross-system orchestration into a single Process API creates a new single point of failure and a deployment bottleneck. Process APIs should be scoped to bounded business contexts (order fulfillment, customer onboarding) rather than a single "enterprise bus."

## Official Sources Used

- Integration Patterns -- https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Salesforce Well-Architected Overview -- https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Architecting the Agentic Enterprise with MuleSoft -- https://architect.salesforce.com/fundamentals/mulesoft-architecting-agentic-enterprise
- Trailhead: API-Led Connectivity Essentials -- https://trailhead.salesforce.com/content/learn/modules/application-networks-and-api-led-connectivity-in-mulesoft/explore-api-led-connectivity
- MuleSoft Blog: 5 Integration Patterns to Debunk API-Led Connectivity Myths -- https://blogs.mulesoft.com/api-integration/patterns/patterns-to-debunk-api-led-connectivity-myths/
