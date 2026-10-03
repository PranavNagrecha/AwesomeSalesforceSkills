# Well-Architected Notes — Einstein Discovery Setup

## Relevant Pillars

- **Security** — Einstein Discovery writeback fields require explicit field-level security assignment after creation. Without FLS, prediction scores are invisible to all users, creating a gap between what is being scored and what is accessible. Admins must treat FLS assignment as a mandatory deployment step, not an optional one. Additionally, the explanatory variables selected for the story determine what data Einstein processes — including potentially sensitive fields — so data governance review of included fields is appropriate before story deployment.

- **Reliability** — Model drift is the primary reliability risk. Because refreshed model versions are not automatically activated, it is easy for a production Einstein Discovery deployment to silently score records against a model trained on months-old data while appearing fully functional. Reliable deployments require an operational process — not just a technical one — for reviewing and activating new model versions after each refresh.

- **Operational Excellence** — Einstein Discovery setup introduces ongoing operational obligations: model refresh scheduling, post-refresh activation, bulk scoring job monitoring, and writeback field auditing. These are admin-managed tasks with no automated reminders in the platform. Runbooks documenting each recurring step are essential for sustainable operation. Teams that configure Einstein Discovery and then treat it as self-maintaining will encounter silent model drift, stale scores, and eventual data quality issues.

Note added 2026-10-03: the statements above about default field-level security, activation after refresh, and bulk-only scoring are help-only claims (UNVERIFIED (2026-10-03)). Grounded additions: a prediction definition (`DiscoveryGoal`) holds up to ten active models with ordered segment filters; removing its `pushbackField` deletes the writeback field; model fields carry `isSensitive` and `isDisparateImpact` flags for fairness review (Security); and `terminalStateFilters` define the observed outcomes used for accuracy monitoring (Reliability).

## Architectural Tradeoffs

**Insights-Only vs. Insights and Predictions:** Choosing "Insights only" avoids writeback field creation, FLS concerns, and scoring job management, but provides no live scores on records. This is appropriate when the team's goal is analytical exploration (understanding what drives outcomes) rather than operational scoring (surfacing predictions on active records). Choosing "Insights and Predictions" adds operational overhead but enables record-level scoring and what-if analysis.

**Writeback field vs. developer API scoring:** Using writeback fields (admin path) gives admins control without code, but scores are only as fresh as the last bulk scoring job. Using the developer API (Connect REST `/smartdatadiscovery/predict`) allows on-demand scoring within any integration, but requires developer involvement. For most admin-managed deployments, bulk scoring jobs running nightly or after key events are a practical middle ground.

**Model accuracy vs. refresh cadence:** More frequent model refreshes produce more current models but require more frequent manual activation reviews. Monthly refresh cadences are common; weekly is feasible for active high-volume pipelines. Infrequent refresh on fast-changing data is worse than no refresh at all, because the model's assumptions diverge from reality while the UI continues to present scores with no indication of staleness.

## Anti-Patterns

1. **Setting up Einstein Discovery and treating it as self-maintaining** — After story deployment and initial scoring job setup, admins frequently move on without establishing a recurring operational process. Refresh jobs complete, new model versions accumulate in "Ready" status, and scoring continues against the original model indefinitely. Months later, the team notices that predictions no longer correlate with actual outcomes, but no error was ever raised. Reliable deployments require a documented and calendared activation workflow.

2. **Using Einstein Discovery as a replacement for Einstein Prediction Builder when no CRM Analytics license exists** — Teams without a CRM Analytics license cannot use Einstein Discovery at all. Attempting to access Analytics Studio or the story creation wizard without the license produces access errors. The correct tool for binary predictions without a CRM Analytics license is Einstein Prediction Builder, which has its own Setup-based wizard and does not require the CRM Analytics entitlement.

3. **Ignoring writeback field FLS as part of deployment** — Completing story deployment and bulk scoring setup without assigning FLS results in a fully functional backend (scoring runs, field is populated) with zero user-visible output (reports, layouts, and list views show nothing). This creates the appearance that the feature is broken and often triggers unnecessary debugging or support escalations.

## Official Sources Used

Read for the 2026-10-03 pass (fetched with plain `curl`; line numbers cite the `pdftotext -layout` extraction):

- Metadata API Developer Guide, Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (DiscoveryAIModel write-operation note, file layout, algorithm and prediction types, model field flags, source types L54449-54745; DiscoveryGoal definition, ten-model limit, `pushbackField` deletion note, `terminalStateFilters`, deployed model filters, pushback type, sample, and manifest L54747-55190)
- Analytics Platform Setup Guide, Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/bi_admin_guide_setup.pdf (CRM Analytics Growth, Plus, and Einstein Predictions licences L1622)
- CRM Analytics REST API Developer Guide, Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/bi_dev_guide_rest.pdf (points smartdatadiscovery prediction calls to the separate Einstein Discovery REST API Developer Guide, L529-530)

Listed by the original author and not re-read in this pass (help.salesforce.com, Trailhead retired page, and architect.salesforce.com did not serve readable content; the Einstein Discovery REST API guide URLs returned 404 or empty JSON on 2026-10-03):

- Manage and Deploy Models in Einstein Discovery: https://help.salesforce.com/s/articleView?id=sf.bi_edd_story_deploy.htm
- Einstein Discovery Basics: Create a Model (Trailhead): https://trailhead.salesforce.com/ (page retired; see host index for current equivalent)
- Einstein Discovery Prediction Writeback Fields in Salesforce: https://help.salesforce.com/s/articleView?id=sf.bi_edd_prediction_writeback.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
