# Well-Architected Notes — OmniStudio Performance

## Relevant Pillars

### Performance

OmniStudio performance is the primary concern of this skill. The Well-Architected Performance pillar focuses on delivering fast, responsive experiences and keeping resource consumption efficient. In OmniStudio, performance degrades when the design ignores the cost of network round trips, synchronous blocking, and redundant data fetching. The canonical optimizations — IP consolidation, DataRaptor caching, async execution, and lazy loading — are all direct applications of this pillar. Performance must be validated against production-representative data volumes, not just small test data sets.

### Scalability

OmniStudio assets that work well with a few records can hit governor limits or produce noticeably longer response times as data volumes grow. DataRaptor Extract calls that return large result sets, Integration Procedures with looping elements over unbounded collections, and FlexCards that render hundreds of cards each with independent data source calls are scalability risks. Well-architected OmniStudio designs bound their data volumes explicitly: paginate large lists, filter at the data source level, and avoid open-ended queries inside IPs.

### Reliability

Async Integration Procedures and external callouts introduce failure modes that synchronous execution surfaces immediately. A well-architected async pattern includes explicit error handling and monitoring, not just fire-and-forget invocation. Reliability in OmniStudio also means the user experience is consistent regardless of network conditions: lazy loading can create step-level wait times that feel inconsistent if the underlying data fetches are not also optimized.

### Operational Excellence

OmniStudio assets are often authored by configuration-focused teams with limited visibility into server-side performance. Operational excellence requires that performance be measurable. OmniStudio debug mode provides element-level timing in Integration Procedures. Setting up baseline benchmarks for critical OmniScript flows and reviewing them after changes is an operational discipline, not a one-time tuning exercise.

---

## Architectural Tradeoffs

**Caching versus freshness:** DataRaptor response caching trades data freshness for speed. The right balance depends on how frequently the underlying data changes and whether the OmniScript is modifying that data. Caching account contact data during a read-only advisory flow is safe. Caching a record the OmniScript is actively editing is not.

**Async execution versus error visibility:** Async IP invocation removes latency from the user path but hides failures. Synchronous execution keeps failures visible and actionable in the UI but makes the user wait. The right choice depends on whether the operation is a user-visible transaction step (sync) or a background side-effect (async).

**IP consolidation versus testability:** Bundling all per-step DataRaptors into one IP reduces round trips but creates larger, more complex IPs. Well-architected IPs keep internal elements named clearly and structured so they can be tested independently with the OmniStudio IP debugger.

**Lazy loading versus predictability:** Lazy loading spreads load time across navigation but makes step-entry latency variable and less predictable. For flows where users navigate non-linearly (back-and-forth frequently), lazy loading combined with caching is the right approach. For linear flows where every step is visited once, eager loading of the first few steps may be preferable.

---

## Anti-Patterns

1. **Per-element DataRaptor calls on every step** — Placing multiple independent DataRaptor Action elements on a single OmniScript step serializes their latency. Every element fires a separate network round trip. The fix is to consolidate all per-step data fetches into a single Integration Procedure call. This is the most common OmniStudio performance anti-pattern in production orgs.

2. **Caching actively-edited records** — Enabling DataRaptor caching on a record the OmniScript is modifying returns pre-edit values when the step is revisited, overwriting user input if data mappings write back to OmniScript JSON nodes. Cache only read-only data within the session.

3. **Treating async IP as a performance fix without error handling** — Making an IP asynchronous eliminates blocking latency but also eliminates error visibility. Without explicit error logging or event emission inside the async IP, failures are silent. An async IP without error handling is an operational debt that surfaces in production as mysteriously missing records or notifications.

4. **Using FlexCard visibility conditions to suppress data fetches** — Conditional visibility controls rendering, not data source invocation. A hidden card still fetches its data. Performance gains from visibility conditions are zero; data savings require changes at the data source or IP level.

---

## Official Sources Used

- OmniStudio OmniScript Help — https://help.salesforce.com/s/articleView?id=sf.os_omniscript.htm
- OmniStudio Integration Procedures Help — https://help.salesforce.com/s/articleView?id=sf.os_integration_procedures.htm
- OmniStudio Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer_guide.meta/omnistudio_developer_guide/omnistudio_intro.htm
- Salesforce Well-Architected Framework — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Integration Patterns and Practices — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
