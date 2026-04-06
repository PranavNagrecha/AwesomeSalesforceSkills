# Well-Architected Notes — Collaborative Forecasts

## Relevant Pillars

- **Operational Excellence** — Collaborative Forecasts is primarily an operational tool: it structures how forecast data flows from reps to managers to leadership. Operational excellence considerations dominate: Is the forecast hierarchy correctly mirroring the sales org? Are stage mappings kept current as the stage list evolves? Are quota loads automated and reliable? Misconfigured rollup methods, stale stage mappings, or missing forecast user enablement silently degrade the reliability of every forecast cycle.

- **Reliability** — The forecast must produce accurate and consistent data each period. The key reliability risks are: opportunity stages mapped to Omitted that should be in-pipeline, quota records with incorrect period boundary dates, and split-based opportunities with missing or incorrect split amounts. Each of these produces silent data errors — the forecast page shows no error, but the numbers are wrong.

- **Security** — Forecast visibility is governed by the forecast hierarchy, not standard sharing rules. Users can only see forecast data for their own records and their subordinates' records within the forecast hierarchy (role hierarchy or territory hierarchy). Admin users with "View All Forecasts" permission can see all forecast data. Be aware that enabling a territory-based Forecast Type does not grant additional data access beyond the territory model's sharing rules.

- **Scalability** — The 4-active-Forecast-Type default limit is an architectural constraint. Orgs with complex go-to-market structures (multiple geographies, multiple products, multiple sales motions) can exhaust the limit quickly. Design Forecast Types to cover the highest-value reporting dimensions; combine motions where possible before requesting a limit increase.

## Architectural Tradeoffs

**Cumulative vs Single-Category Rollup:**
Cumulative rollup is more intuitive for managers because the Commit column reflects expected revenue including already-won deals. Single-category rollup is more useful for granular pipeline analysis. The tradeoff is irreversibility: switching method destroys adjustments. Choose before production, document the choice, and treat it as a one-way architectural decision until a low-adjustment-impact window (e.g., start of a new fiscal year) allows a change.

**Role Hierarchy vs Territory Hierarchy per Forecast Type:**
Role-based types reflect the management org chart; territory-based types reflect the coverage model. An org running both introduces complexity for users and admins because hierarchy changes (re-orgs, territory model updates) affect different Forecast Types independently. Keep the number of hierarchy types to the minimum required for stakeholder reporting.

**Forecast Types vs Standard Reports:**
Forecast Types produce manager-editable, adjustment-capable, hierarchy-based views. Standard pipeline reports produce point-in-time snapshots without adjustment context. Forecasts and reports serve different purposes; replacing one with the other causes data reconciliation confusion. Use both intentionally.

## Anti-Patterns

1. **Using a single Opportunity-Amount Forecast Type for a multi-motion sales team** — Orgs with distinct direct and overlay sales motions that try to represent both in a single Forecast Type produce misleading totals. Direct AE revenue and SE overlay revenue appear combined, potentially double-counting deals where both teams are credited. Separate Forecast Types for each motion (direct Amount vs Opportunity Splits) produce accurate, attributable numbers.

2. **Changing rollup method on a live forecast without exporting adjustments first** — The rollup method change is a silent, irreversible data-loss event. Treating it as a routine configuration toggle is an operational anti-pattern that permanently destroys forecast adjustment history. Always treat rollup method as a near-immutable architectural choice; export adjustments before any change.

3. **Skipping ForecastEnabled flag in user provisioning workflows** — Relying on role assignment alone to populate the forecast hierarchy leaves newly provisioned users invisible in forecasts. This is a systemic provisioning anti-pattern: the field must be explicitly set, and its omission produces no error — only a gap in the forecast hierarchy that may not be noticed until end of quarter.

## Official Sources Used

- Salesforce Help — Set Up Collaborative Forecasts — https://help.salesforce.com/s/articleView?id=sf.forecasts3_setting_up_forecasting.htm
- Salesforce Help — Define Forecast Types — https://help.salesforce.com/s/articleView?id=sf.forecasts3_define_forecast_types.htm
- Salesforce Help — Forecast Categories — https://help.salesforce.com/s/articleView?id=sf.forecasts3_forecast_categories.htm
- Salesforce Help — Cumulative Forecast Rollups — https://help.salesforce.com/s/articleView?id=sf.forecasts3_cumulative_rollups.htm
- Salesforce Help — ForecastingQuota Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_forecastingquota.htm
- Salesforce Help — ForecastingAdjustment Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_forecastingadjustment.htm
- Metadata API Developer Guide — ForecastingSettings — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_forecastingsettings.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
