# Well-Architected Notes — Lightning Page Performance Tuning

## Relevant Pillars

- **Performance** — This is the primary pillar. Lightning page performance is determined by component count, component data weight, progressive disclosure strategy, and rendering architecture. EPT (Experienced Page Time) is the platform-native metric that quantifies performance. Every component on the initial viewport adds DOM rendering cost and potentially a server round-trip. The Salesforce-recommended pattern — progressive disclosure via tabs — directly reduces initial render scope and is the single highest-impact optimization for most slow pages.

- **Scalability** — Pages designed without component weight awareness degrade as org complexity grows. A page that loads in 2 seconds with 100K records on a Related List may load in 6 seconds when that child object grows to 1M records. Scalable page design means deferring data-heavy components from initial load so that page performance remains stable as data volume increases. Page variants per role ensure that added components for new user groups do not degrade performance for existing users.

- **Security** — Component visibility filters and page assignment rules control which components render for which users. These are functional controls, but they have a performance dimension: ensuring users only load components they are authorized to see avoids unnecessary data fetching. However, component visibility is not a substitute for field-level security or sharing rules — it controls rendering, not data access. Removing a component from a page variant does not revoke access to the underlying data.

- **Operational Excellence** — Lightning Experience Insights provides ongoing EPT monitoring without manual instrumentation. Using this built-in tool to identify slow pages, measure baselines, and validate improvements is an operational excellence practice. Documenting tab layout rationale and component categorization in page descriptions prevents future editors from undoing performance work.

## Architectural Tradeoffs

**Information density vs. load speed:** Users want all relevant information visible on a single page. Adding more components increases information density but degrades load time. The tradeoff is addressed by progressive disclosure — tabs provide access to all information while deferring the rendering cost of secondary components. The key design decision is which components are "essential" (initial viewport) vs. "secondary" (tabs).

**Tab deferral vs. click cost:** Deferring components to tabs improves initial load but adds a click-and-wait step for users who need the deferred information. For workflows where users access all tabs on every record, tab deferral shifts cost rather than eliminating it. Resolution: use tab deferral when non-default tabs are accessed on fewer than 30% of page views; use component reduction or page variants when all information is needed on every view.

**Page variants vs. maintenance complexity:** Creating multiple page variants for different roles optimizes each role's experience but multiplies the number of pages to maintain. A change to the account record page may need to be applied to 3-4 variants. Resolution: use page variants only when role-specific component needs are genuinely different (not just "nice to have" differences) and consolidate variants that share more than 80% of their component set.

**Dynamic Forms vs. traditional page layouts:** Dynamic Forms allow conditional field visibility, which can improve performance by hiding irrelevant fields. However, Dynamic Forms are not available for all objects and require more configuration effort. Resolution: adopt Dynamic Forms when field-level conditional visibility is needed for both UX and performance reasons, not solely for a marginal performance gain.

## Anti-Patterns

1. **Placing all components on the initial viewport without tabs** — Loading every component on the default view forces all DOM rendering and XHR calls to execute on initial page load. As components are added over time, page load degrades gradually without a clear inflection point. Resolution: establish a component budget (8-10 components on initial viewport) and use tabs for anything beyond the budget.

2. **Using full Related Lists for scan-only use cases** — Full Related List components fetch more data and render more DOM than Related List - Single components. When users only need to see the top 3-5 records of a child object, the full Related List adds unnecessary load. Resolution: default to Related List - Single for most child objects and upgrade to full Related List only when inline editing, sorting, or full-row display is required.

3. **Embedding Report Charts on high-traffic record pages without filtering** — Report Chart components execute their underlying report on every page load. On a record page viewed hundreds of times per day, this multiplies report query load by the page view count. Resolution: move Report Charts to non-default tabs, add record-scoped filters to limit query scope, or replace with a custom LWC that uses cached data.

4. **Optimizing page layout without measuring EPT** — Making layout changes based on intuition rather than EPT measurement leads to effort spent on changes that do not move the metric. Resolution: always measure baseline EPT before making changes and remeasure after deployment. Use Lightning Experience Insights as the authoritative data source.

## Official Sources Used

- Salesforce Help: Lightning Page Performance — https://help.salesforce.com/s/articleView?id=sf.lightning_page_performance.htm
- Salesforce Developer Blog: Designing Lightning Pages for Scale — https://developer.salesforce.com/blogs/2020/designing-lightning-pages-for-scale
- Salesforce Help: Lightning Experience Insights — https://help.salesforce.com/s/articleView?id=sf.lex_lightning_usage_app.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
