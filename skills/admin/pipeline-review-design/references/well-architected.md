# Well-Architected Notes — Pipeline Review Design

## Relevant Pillars

- **Operational Excellence** — Pipeline Inspection is fundamentally an operational visibility tool. The quality of the review process it enables depends on how well the underlying configuration is maintained: accurate stage-to-forecast-category mappings, appropriate Days in Stage thresholds, and forecast hierarchy completeness. A poorly configured inspection view produces false signals that erode manager trust and cause the team to revert to manual workarounds. Operational Excellence requires that the configuration be correct, documented, and periodically reviewed as sales processes evolve.

- **Reliability** — Pipeline Inspection relies on Collaborative Forecasting infrastructure, the forecast hierarchy, and the underlying Opportunity data model. Reliability risks include: stages with incorrect ForecastCategoryName mappings silently distorting inspection totals; users missing from the forecast hierarchy causing invisible data gaps; and split-based forecast type associations producing unexpected amount values. Reliable pipeline review design means each dependency is verified and each failure mode is documented before the inspection view is used to make business decisions.

- **Security** — Access to Pipeline Inspection is governed by the Collaborative Forecasts hierarchy and the "View All Forecasts" permission. This means access control for pipeline inspection is not managed through standard record-level sharing — it is managed through hierarchy position. Admins must understand that adding a user to the forecast hierarchy grants them visibility into all subordinate deals in the inspection view, not just deals they own. Security review should confirm that hierarchy expansion does not inadvertently expose deal data to users who should not see it.

- **Performance** — Pipeline Inspection is a platform-rendered view and does not introduce custom SOQL queries or Apex execution. Performance considerations are limited to ensuring the forecast hierarchy is not excessively deep and that the number of active forecast types associated with Pipeline Inspection does not proliferate unnecessarily. An inspection view with many associated forecast type selectors creates a UX confusion and usability concern, not a platform performance concern.

## Architectural Tradeoffs

**Pipeline Inspection vs. CRM Analytics Pipeline Dashboards:** Pipeline Inspection provides native, zero-configuration pipeline change metrics within the Forecasts page. CRM Analytics dashboards offer more flexibility, historical trending, and multi-dimensional slicing, but require analytics licenses, dataset configuration, and ongoing dashboard maintenance. For teams that primarily need weekly inline deal-change visibility, Pipeline Inspection is the lower-overhead choice. For teams that need executive reporting, historical trend analysis, or cross-object analytics, CRM Analytics is the correct path. These are not mutually exclusive — many orgs use both.

**Global Days in Stage threshold vs. stage-specific thresholds:** The platform enforces a single global Days in Stage threshold. Teams with variable-duration sales stages must compensate through meeting discipline (manager-level filtering during review) rather than configuration. Attempting to simulate stage-specific thresholds through custom formula fields introduces maintenance overhead and diverges from the platform-native metric. Accepting the global threshold limitation and building structured review discipline around it is the architecturally cleaner approach.

**Forecast category override vs. stage-level mapping:** When the same stage can represent different confidence levels for different deals, enabling "Allow Forecast Category Override" gives reps per-deal control over how their opportunities appear in Pipeline Inspection. This adds rep responsibility for data quality but allows the stage taxonomy to remain stable. Changing stage-level ForecastCategoryName mappings to reflect the majority case is simpler to maintain but less flexible. The right choice depends on how consistently the stage maps to a single confidence level across the sales motion.

## Anti-Patterns

1. **Enabling Pipeline Inspection without auditing Stage-to-ForecastCategoryName mappings first** — The most common configuration error is turning on Pipeline Inspection and sending managers to the view before verifying that all Stage values have correct ForecastCategoryName values. Deals grouped incorrectly (e.g., Commit-confidence deals appearing in Best Case, or revenue-bearing deals mapped to Omitted and invisible) produce a first impression of the feature that is actively misleading. Always complete the stage audit before directing users to the inspection view.

2. **Using Pipeline Inspection as the sole mechanism for pipeline accuracy enforcement** — Pipeline Inspection is a visibility tool, not an enforcement tool. It surfaces deal changes but does not prevent reps from pushing close dates, reducing amounts, or moving stages backward. Teams that rely only on Pipeline Inspection without complementary enforcement mechanisms (validation rules, approval processes) will find that deal hygiene problems are visible in the inspection view but never addressed at the data entry point.

3. **Associating every active forecast type with Pipeline Inspection** — Each associated forecast type adds a selector tab in the inspection view. For orgs with multiple forecast types, associating all of them creates a confusing multi-tab view that most managers do not understand. Limit Pipeline Inspection associations to the 1-2 forecast types the sales team actively uses for pipeline reviews.

## Official Sources Used

- Pipeline Inspection Metrics and Fields — https://help.salesforce.com/s/articleView?id=sf.pipeline_inspection_metrics_fields.htm&type=5
- Guidelines and Limits for Pipeline Inspection — https://help.salesforce.com/s/articleView?id=sf.pipeline_inspection_guidelines_and_limits.htm&type=5
- Customize Pipeline Forecast Categories — https://help.salesforce.com/s/articleView?id=sf.forecasts3_pipeline_forecast_categories.htm&type=5
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Collaborative Forecasts Implementation Guide — https://help.salesforce.com/s/articleView?id=sf.forecasts3_implement.htm&type=5
