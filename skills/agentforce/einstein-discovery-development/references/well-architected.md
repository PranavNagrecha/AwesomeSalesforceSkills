# Well-Architected Notes — Einstein Discovery Development

## Relevant Pillars

- **Security** — Prediction API calls must use OAuth (session ID or Connected App); embedding credentials directly in Apex or external scripts is prohibited. Prediction definitions may expose sensitive data through prescriptions and top-predictor values; ensure the Lightning components displaying them are behind appropriate object-level and field-level security. Sensitive fields used as model inputs (e.g., income, age proxies) must be evaluated for bias and data residency compliance before story creation.
- **Performance** — The synchronous predict endpoint accepts up to 200 record IDs per call; exceeding this requires pagination. For large populations, bulk predict jobs are the correct mechanism and must not be replaced with looped synchronous calls. Response size grows substantially when `maxMiddleValues` and `maxPrescriptions` are enabled; only request factors when the consumer will display them.
- **Scalability** — Org-level daily predictions limits are shared across all prediction definitions. A single prediction definition running unrestricted bulk jobs can exhaust the limit for all others. Distribute bulk job schedules across the day and monitor daily consumption proactively.
- **Reliability** — Bulk scoring jobs can pause due to the daily limit without any error notification. Dependent pipelines must handle `Paused` status as a recoverable condition, not a failure. Model refresh jobs complete asynchronously; downstream scoring jobs must not start until the refreshed model is activated.
- **Operational Excellence** — Model versions must be explicitly activated after a refresh job; this step is easy to omit in automated pipelines. Operational runbooks should capture the active model version, the refresh schedule, the daily limit usage baseline, and the field mapping configuration for each prediction definition.

## Architectural Tradeoffs

**Synchronous vs. Bulk Scoring:** The synchronous predict endpoint provides low latency but is limited to 200 records per call. It is appropriate for interactive user workflows but inappropriate for org-wide scoring runs. Using synchronous calls in a batch loop to simulate bulk scoring will exhaust API limits and daily prediction limits far faster than a single bulk job.

**Real-Time vs. Scheduled Scoring:** Einstein Discovery does not support event-driven scoring—there is no trigger mechanism that re-scores a record when a related field changes. Architectures that require "current" prediction scores must either accept periodic staleness (scheduled bulk jobs) or incur the cost of an explicit API call on every record open/save. For most enterprise use cases, scheduled bulk jobs with an acceptable staleness window (e.g., nightly) are the correct tradeoff.

**CRM Analytics vs. Einstein Prediction Builder:** Einstein Discovery requires a CRM Analytics license and supports regression, multi-class classification, and time series. Einstein Prediction Builder requires no additional license but only supports binary classification. Choosing Einstein Discovery for a binary use case over-licenses the org; choosing EPB for regression is technically impossible. Establish prediction type before selecting the tool.

## Anti-Patterns

1. **Loop of synchronous predict calls to replace bulk jobs** — Making hundreds of individual `POST /smartdatadiscovery/predict` calls from scheduled Apex to score all records is a common workaround for teams unfamiliar with bulk predict jobs. This hits API call limits, consumes the daily predictions limit faster, and runs significantly slower than a single bulk job. Use `/smartdatadiscovery/predictjobs` for population-level scoring.

2. **Assuming model refresh automatically activates the new model** — Teams who automate model refresh jobs often skip the activation step, believing the system promotes the best model automatically after training. It does not. The prior model remains active until an admin or integration explicitly activates the new version. This leads to orgs scoring with a stale model for weeks after a successful refresh job, undermining the value of the retraining investment.

3. **Not auditing `importWarnings.missingColumns` in production** — The predict endpoint returns HTTP 200 even when column mapping failures degrade prediction quality. If `missingColumns` is non-empty, the score is computed without those features, which can cause significant accuracy degradation silently. Add response-level validation that alerts when `missingColumns` is non-empty in production scoring runs.

## Official Sources Used

- Einstein Discovery REST API Developer Guide (Spring '26) — https://developer.salesforce.com/docs/einstein/einstein-discovery/references/einstein-discovery-rest-api/
- Metadata API Developer Guide: DiscoveryStory, DiscoveryAIModel — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_discoverystory.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Connect REST API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.chatterapi.meta/chatterapi/connect_resources_overview.htm
- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
