# Well-Architected Notes — Experience Cloud Performance

## Relevant Pillars

- **Performance Efficiency** — This is the primary pillar for Experience Cloud performance work. The Well-Architected Performance pillar focuses on delivering fast, responsive experiences by using platform capabilities efficiently and avoiding resource waste. For Experience Cloud, this means leveraging the CDN static layer on LWR sites, enabling browser caching, minimizing Apex round-trips on page load, and deferring below-the-fold component initialization. The LWR architecture is expressly designed to align with this pillar: publish-time static generation, immutable-URL asset versioning, and CDN-first delivery are platform-native performance patterns.

- **Reliability** — CDN caching introduces a reliability tradeoff: edge caches can serve stale content during the 60-second HTML TTL window after a publish. For sites with SLA requirements on content freshness (e.g., financial or healthcare portals where outdated content is a compliance risk), the publish process must be operationalized to account for this window. A reliability-aligned site has documented publish procedures, post-publish validation steps, and stakeholder communication that accounts for CDN propagation latency.

- **Operational Excellence** — Performance settings in Experience Builder (browser caching, CDN toggle) require human review and enablement. They are not automatically optimized. An operationally excellent site configuration includes these settings in a provisioning checklist, a performance audit cadence, and clear ownership for reviewing settings after major Salesforce releases that may introduce new performance options.

- **Security** — CDN delivers content from edge nodes. Publicly cacheable resources are served without Salesforce authentication at the CDN layer. This is expected and intentional for the static LWR layer. However, any dynamic data, user-specific records, or permission-scoped content must not be constructed into the static layer. Architects must confirm that no PII or session-specific data is included in page-level resources that the CDN will cache and serve publicly.

## Architectural Tradeoffs

**LWR static-first vs Aura dynamic rendering:** LWR sites trade flexibility (any component runs anywhere) for performance (publish-time generation of immutable static bundles). The performance gain is significant and measurable, but it requires that all dynamic content be fetched client-side at runtime rather than server-rendered into the page. This means that pages with heavy personalization (unique per-user layouts, record-driven navigation) still require Apex calls regardless of the static layer. The CDN accelerates what it can; Apex optimization handles what it cannot.

**CDN TTL vs content freshness:** The 60-second CDN HTML TTL is a platform decision that prioritizes origin server protection over instantaneous content refresh. Shorter TTL would increase origin load during popular site publishes. Teams that need near-instantaneous content updates must work within this constraint: use Experience Builder's content components for content that changes frequently (rather than hardcoding content into LWC templates that require a publish), and plan publish timing for off-peak windows.

**Eager component loading vs deferred initialization:** Loading all page components eagerly maximizes developer simplicity but wastes server capacity and increases time-to-interactive for users who will never scroll below the fold. Deferred loading via conditional rendering adds complexity but meaningfully improves Largest Contentful Paint and total Apex call count on page load. For high-traffic sites, this is a scalability-relevant decision: each avoided Apex call per page view multiplies across thousands of concurrent sessions.

## Anti-Patterns

1. **Treating CDN as a solution for dynamic data latency** — CDN only accelerates the static layer. Apex wire call latency, User Interface API response times, and record data loading are all outside the CDN's scope. Architects who represent CDN enablement as a complete performance fix set false expectations and miss the real optimization opportunity (Apex consolidation, Platform Cache, deferred loading).

2. **Publishing without accounting for CDN TTL** — Making content changes under time pressure, publishing immediately, and declaring the task complete without waiting for CDN propagation. This leads to support escalations ("we just published but users still see the old version") and erodes trust in the platform. Every publish on a CDN-enabled site has a propagation window; that window must be part of the operational process.

3. **Building performance reviews that ignore Experience Builder settings** — Conducting Apex-focused performance audits while never checking `Settings > Performance` in Experience Builder. The browser caching toggle is a one-click performance improvement that is frequently disabled by omission. Skip-listing platform settings in favor of code review creates blind spots.

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- LWR Sites for Experience Cloud (Caching Policy) — https://developer.salesforce.com/docs/atlas.en-us.exp_cloud_lwr.meta/exp_cloud_lwr/intro_lwr.htm
- Serve Your Experience Cloud Site with the Salesforce CDN — https://help.salesforce.com/s/articleView?id=sf.exp_cloud_basics_glossary_cdn.htm
- Experience Cloud Performance and Scale — https://help.salesforce.com/s/articleView?id=sf.networks_performance_scale.htm
