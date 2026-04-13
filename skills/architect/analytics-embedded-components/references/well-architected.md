# Well-Architected Notes — Analytics Embedded Components

## Relevant Pillars

### Performance

Embedded CRM Analytics dashboards introduce query load at render time. Each dashboard loads its datasets and runs its steps when the component renders. On high-traffic record pages (such as Account or Opportunity pages visited by large sales teams), every page open triggers dataset queries. Design dashboards to use pre-materialized datasets with scheduled dataflows rather than live SOQL-backed datasets for embedded contexts. Avoid embedding multiple large dashboards on a single page — each adds independent query overhead.

The `state` attribute pre-populates filters on load, which can reduce the number of query re-runs a user triggers manually. Using `state` to scope the initial view to the relevant record data improves perceived performance by surfacing useful data immediately.

### User Experience

Embedded analytics works best when the dashboard context matches the user's current context without manual intervention. Use `record-id` with a well-designed dashboard to deliver automatic context scoping — a user on an Account page should see that account's data immediately, without selecting from a filter widget.

Showing dashboards inline on record pages (Pattern A) removes the need to navigate to Analytics Studio, reducing context switching. For Pattern B (custom LWC inside a dashboard), surfacing write-back actions (creating records, updating fields) directly on the dashboard canvas closes the loop between insight and action.

Avoid displaying dashboards to users who lack the CRM Analytics Viewer license or the appropriate app sharing permissions. The component renders but shows an access-denied message, which is confusing. Gate the component's visibility at the page level if license availability is inconsistent across the user population.

### Security

Dashboard embedding inherits the user's CRM Analytics sharing settings. A user who does not have Viewer access to the Analytics app or dashboard will see an error even if the embedding component is present on the page. The `wave-wave-dashboard-lwc` component does not bypass row-level security — the underlying dataset security predicates remain in effect.

Passing `record-id` to a dashboard does not expose the record to users who lack record access. The dashboard queries data using the current user's CRM Analytics permissions, which are separate from Salesforce object permissions. Validate that row-level security predicates in the dataset correctly limit data visibility for embedded contexts.

### Reliability

The mutual exclusivity of `dashboard` and `developer-name` is a reliability risk. A dashboard that silently loads the wrong content (because both attributes were set and the ID-based one took precedence) is harder to diagnose than a hard failure. Use `developer-name` in all sandbox-to-production deployments to ensure the configuration is environment-agnostic.

Invalid `state` JSON causes a silent rendering failure — the dashboard loads in its default state. This can cause critical filters to be missing without any visible error, leading users to draw incorrect conclusions from unfiltered data. Validate state JSON before passing it and add monitoring or tests that verify the dashboard loads in the expected filtered state after deployment.

## Architectural Tradeoffs

**`developer-name` vs `dashboard` (18-char ID):** `developer-name` is portable across environments and is the recommended choice for any configuration that moves between sandbox and production. The `dashboard` ID is environment-specific and creates deployment risk. Tradeoff: if the dashboard is renamed in Analytics Studio, the `developer-name` changes and the embedding component breaks. Treat the developer name as a contract between the dashboard and the embedding component.

**Pattern A (dashboard-in-page) vs iframe:** Pattern A using `wave-wave-dashboard-lwc` provides native record-context binding, action callbacks, and session-aware rendering. An iframe is simpler to set up but loses all context integration — no `record-id` binding, no action listeners, and no response to Lightning data service updates. Use iframe only as a last resort for non-Salesforce page embedding where the native components are not available.

**Pattern B (LWC-in-dashboard) widget property exposure:** Exposing many `targetConfig` properties on a Pattern B LWC gives dashboard designers flexibility but increases maintenance complexity. Keep the property surface minimal — expose only what dashboard designers genuinely need to configure per-dashboard-instance.

## Anti-Patterns

1. **Hardcoding dashboard IDs in LWC markup** — Using the 18-character `0FK` ID directly in markup (`dashboard="0FKxx000000xxxxx"`) creates environment-specific code that breaks when moved between orgs or sandboxes. Use `developer-name` for all persistent configurations.

2. **Embedding dashboards without validating license coverage** — Placing `wave-wave-dashboard-lwc` on record pages for all users when not all users have CRM Analytics Viewer licenses results in a broken experience for unlicensed users. Gate visibility with a permission check or ensure uniform license coverage before broad rollout.

3. **Assuming `record-id` auto-filters the dashboard** — Building the embedding layer and expecting the dashboard to scope itself to the current record without verifying that the dashboard has the corresponding filter/binding configured. This results in dashboards showing global data despite the `record-id` being passed — a silent failure that misleads users.

## Official Sources Used

- Analytics Dashboard Component Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_wave_api.meta/bi_dev_guide_wave_api/wave_api_analytics_dashboard_component.htm
- Attributes for Analytics Dashboards LWC — https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_wave_api.meta/bi_dev_guide_wave_api/wave_api_analytics_dashboard_lwc_attributes.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- LWC for Analytics Dashboards (js-meta.xml targets) — https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_wave_api.meta/bi_dev_guide_wave_api/wave_api_analytics_dashboard_lwc_target.htm
