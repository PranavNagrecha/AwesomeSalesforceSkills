# Well-Architected Notes — Einstein Discovery Deployment

## Relevant Pillars

- **Reliability** — Einstein Discovery deployment reliability depends on explicit model version activation and scheduled bulk predict jobs. Deployments that omit the activation step or fail to schedule recurring scoring jobs produce unreliable, stale predictions. Well-Architected orgs build runbooks for refresh → activate → re-score sequences and monitor scoring job status in Model Manager.
- **Operational Excellence** — Model Manager is the primary operational surface: scheduling, monitoring scoring jobs, reviewing accuracy metrics, configuring drift alerts, and managing model version history. A deployment is not operationally excellent until monitoring, alerting, and refresh/scoring schedules are configured — not just when the prediction definition is activated.
- **Performance** — Bulk predict jobs consume from the org's daily predictions limit. Poorly sized jobs (scoring all records across all prediction definitions simultaneously) can exhaust the limit and pause scoring for the rest of the day. Performance-conscious deployments right-size record filters, stagger job schedules, and monitor limit consumption.
- **Security** — Output fields written to Salesforce records are subject to field-level security (FLS) and object-level security. Ensure that the profiles and permission sets of end users who need to see prediction scores have read access to the Einstein Discovery output fields on the target object. Admins configuring prediction definitions must have CRM Analytics admin permissions.
- **Scalability** — For orgs with large record volumes, bulk predict jobs should be designed with record filters that limit scope to records where predictions are actionable (e.g., open Opportunities only). Scoring all records regardless of status wastes daily limit quota and increases job duration without business value.

## Architectural Tradeoffs

**Declarative admin path vs. developer API path:** The admin deployment path (this skill) covers the Setup UI, Model Manager, Einstein Discovery Flow Action, and page layout mapping. It is faster to deploy and requires no code. The developer API path (`agentforce/einstein-discovery-development`) covers Apex callouts, programmatic bulk job orchestration, and custom integration. Choose the admin path by default for standard record-page predictions and Flow-driven recommendations. Choose the developer path when prediction scoring must be embedded in custom UIs, external systems, or complex orchestration logic.

**Bulk predict jobs vs. record-triggered Flow scoring:** Bulk jobs score large populations efficiently at scheduled intervals but do not provide real-time freshness. The Einstein Discovery Action in a record-triggered Flow provides near-real-time scoring when a record is saved but consumes daily predictions limit per record per save. For most admin deployments, a daily bulk predict schedule is the right default. Record-triggered Flow scoring is appropriate only when real-time predictions on individual records justify the limit consumption cost.

**Model refresh frequency vs. scoring job cadence:** Refreshing the model too infrequently risks model drift (predictions trained on outdated data). Refreshing too frequently increases operational overhead since each refresh requires manual activation of the new version. A monthly refresh cadence with weekly scoring jobs is a reasonable baseline; adjust based on how quickly the underlying data distribution changes.

## Anti-Patterns

1. **Assuming refresh = activation** — Running scheduled model refresh jobs without a corresponding activation step in the runbook. The new model version is never put into production; the org pays for retraining but continues scoring with the stale model indefinitely. Correct approach: build the activate step (Model Manager > Models > Set as Active) explicitly into every post-refresh procedure.

2. **No monitoring after deployment** — Activating a prediction definition, running the initial bulk predict job, and considering the deployment complete. Without drift alert configuration, scoring job failure notifications, and regular accuracy reviews in Model Manager, model degradation goes undetected until business outcomes suffer. Correct approach: configure Model Manager alerts and schedule a monthly accuracy review as part of the deployment handoff.

3. **Over-consuming daily predictions limit with unfiltered bulk jobs** — Scheduling a daily bulk predict job with no record filter, scoring all records on the object including historical closed/inactive records. This exhausts the daily predictions limit quickly, causing jobs to pause and depriving active records of fresh scores. Correct approach: scope bulk predict jobs to the active record population using a record filter (e.g., `StageName != 'Closed Won' AND StageName != 'Closed Lost'`).

## Official Sources Used

- Manage and Deploy Models in Einstein Discovery — https://help.salesforce.com/s/articleView?id=sf.bi_edd_model_manager.htm
- Einstein Discovery Action in Flow — https://help.salesforce.com/s/articleView?id=sf.bi_edd_flow_action.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Einstein Discovery REST API Developer Guide (Spring '26) — https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_einsteinds.meta/bi_dev_guide_einsteinds/
