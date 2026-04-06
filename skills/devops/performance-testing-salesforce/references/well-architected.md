# Well-Architected Notes — Performance Testing Salesforce

## Relevant Pillars

- **Performance** — This skill directly addresses performance measurement and optimization. Performance testing validates that the org meets EPT and API response time targets under realistic load. Without testing, performance NFRs are aspirational rather than verified.
- **Reliability** — Load testing under concurrency reveals failure modes (governor limit breaches, timeout cascades, lock contention) that only manifest under production-like conditions. Catching these in a sandbox prevents production outages.
- **Scalability** — Performance tests at varying concurrency levels establish the org's scaling curve. This data informs capacity planning decisions — when to optimize, when to re-architect, and when current headroom will be exhausted.
- **Operational Excellence** — Embedding performance tests into the release process creates a repeatable quality gate. Teams that test before every major release catch regressions early rather than discovering them through user complaints.

## Architectural Tradeoffs

1. **First-party (Scale Test) vs. third-party tools** — Scale Test provides native EPT instrumentation and Salesforce-coordinated execution but requires Support case scheduling and only supports UI scenarios. Third-party tools (k6, JMeter) offer API coverage, CI integration, and on-demand execution but cannot produce native EPT metrics. Most orgs need both.

2. **Full Copy sandbox cost vs. test fidelity** — Full Copy sandboxes consume a sandbox allocation and take significant time to refresh, but they are the only environment that provides production-representative data volume and sharing calculations. Testing in smaller sandboxes saves time but produces unreliable results that can lead to worse outcomes than not testing at all.

3. **Test frequency vs. environment availability** — Running performance tests with every sprint maximizes regression detection but ties up a Full Copy sandbox and API limits. Running only before major releases reduces overhead but allows performance debt to accumulate. The recommended compromise is automated API-level smoke tests per sprint with full Scale Test engagements quarterly or before major releases.

## Anti-Patterns

1. **Testing in Developer sandboxes and extrapolating to production** — Developer and Developer Pro sandboxes have 200 MB storage, no production data volume, and no custom indexes. Performance numbers from these environments are not transferable. This anti-pattern creates false confidence and deferred production incidents.

2. **Load testing without defined NFRs** — Running a load test and declaring "it worked" without comparing results to specific, measurable targets (EPT < 3s, API p95 < 2s, zero governor limit breaches) provides no actionable information. Define NFRs before testing, not after.

3. **Spiking to full concurrency without ramp-up** — Sending 500 concurrent requests simultaneously does not represent real user behavior. It triggers rate limiting and connection pooling artifacts that mask actual application performance. Always ramp concurrency gradually over minutes, not seconds.

## Official Sources Used

- Salesforce Help — Scale Test FAQs — https://help.salesforce.com/s/articleView?id=sf.scale_test_faq.htm
- Salesforce Developer Blog — Performance Testing with Scalability Tools (2025) — https://developer.salesforce.com/blogs/2025/performance-testing-scalability
- Trailhead — Optimize Salesforce Performance (EPT) — https://trailhead.salesforce.com/content/learn/modules/lightning-experience-performance-optimization
- Salesforce API Limits Reference — https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/salesforce_app_limits_platform_api.htm
- Salesforce Well-Architected — Resilient Pillar — https://architect.salesforce.com/well-architected/resilient/overview
