# Well-Architected Notes — Einstein Next Best Action

## Relevant Pillars

- **Security** — NBA strategies execute in system context (Autolaunched Flows run without user interaction context by default). Recommendation records and their linked acceptance actions must respect field-level security and sharing rules. If acceptance Flows perform DML or callouts, they inherit the running user's permissions only if configured as user-context Flows. Ensure that sensitive recommendation content (e.g., financial offers, compliance actions) is not exposed to users who lack the appropriate permission sets.

- **Reliability** — The ActionReference field on Recommendation records creates a runtime dependency on the referenced Flow or quick action being active and correctly named. A deactivated Flow causes silent acceptance failures with no user-facing error. Build validation checks that cross-reference Recommendation records against active Flows after every deployment. Use ExpirationDate to automatically retire time-bound recommendations rather than relying on manual cleanup.

- **Scalability** — Strategy Flows that query all Recommendation records without filters degrade as the org's recommendation catalog grows. Each strategy invocation runs a Flow interview, consuming org limits. Apply selective SOQL filters in Get Records elements, limit output to 25 or fewer records, and use indexed fields for filtering. For orgs with hundreds of recommendations, consider partitioning by object context or segment using custom fields.

- **Performance** — The Actions & Recommendations component invokes the strategy Flow on page load. If the strategy Flow contains expensive operations (subflows, Apex invocable actions, external callouts), it delays page rendering. Keep strategy Flows lightweight — prefer in-Flow Decision logic over Apex calls for simple filtering. Cache-friendly patterns (static Recommendation records with Flow-side filtering) outperform dynamic recommendation generation at runtime.

- **Operational Excellence** — NBA strategies built as Flows benefit from Flow versioning, change sets, and metadata API deployment. However, Recommendation records are data (not metadata), so they must be managed through data migration tools (Data Loader, SFDX data imports) rather than change sets. Establish a clear promotion process for Recommendation records across sandbox and production environments. Monitor recommendation acceptance and rejection rates to identify stale or irrelevant recommendations.

## Architectural Tradeoffs

1. **Declarative vs. Apex scoring** — Pure Flow strategies are admin-maintainable but limited to simple boolean logic and field comparisons. Adding Invocable Apex for scoring (e.g., weighted formulas, ML model calls) increases recommendation quality but introduces code dependencies and testing requirements. Use Flow-only for simple segmentation; add Apex only when scoring complexity demands it.

2. **Static vs. dynamic recommendations** — Pre-creating Recommendation records and filtering in the strategy Flow is simple and fast. Dynamically generating Recommendation records in Apex at runtime offers maximum flexibility but is harder to audit, version, and test. Prefer static records with dynamic filtering for most use cases.

3. **Single strategy vs. multiple strategies per page** — A Lightning page can host multiple Actions & Recommendations components, each with a different strategy Flow. This enables modular, composable recommendation logic but increases the number of Flow interviews per page load. Consolidate into a single strategy Flow unless there is a clear organizational or performance reason to separate.

## Anti-Patterns

1. **Monolithic strategy Flow with all business rules** — Cramming every recommendation rule into one massive Flow makes it brittle, hard to test, and difficult for multiple teams to maintain. Instead, use subflows or segment recommendations by object context into separate strategy Flows.

2. **Unvalidated ActionReference values** — Treating the ActionReference field as free text without any validation process leads to broken acceptance buttons in production. Establish a CI check or pre-deployment script that verifies every Recommendation record's ActionReference against known active Flows and quick actions.

3. **Ignoring ExpirationDate for time-bound offers** — Leaving ExpirationDate null on promotional or seasonal recommendations results in stale offers persisting indefinitely. Always set ExpirationDate on time-bound recommendations and include an ExpirationDate filter in every strategy Flow.

## Official Sources Used

- Einstein Next Best Action — https://help.salesforce.com/s/articleView?id=sf.einstein_next_best_action.htm
- NBA Implementation Checklist — https://help.salesforce.com/s/articleView?id=sf.nba_implementation_checklist.htm
- Salesforce Well-Architected: Security — https://architect.salesforce.com/well-architected/trusted/security
