# Well-Architected Notes — Marketing Reporting Requirements

## Relevant Pillars

- **Operational Excellence** — The primary pillar for this skill. Marketing reporting requirements must be documented before any configuration or dashboard build begins. Undocumented attribution decisions are the leading cause of marketing reporting rework. A formal KPI definition register and attribution model decision record reduce operational toil, enable consistent cross-team interpretation of metrics, and make it possible to audit data lineage when numbers are questioned.
- **Reliability** — Attribution accuracy depends on consistent data population: Opportunity Contact Roles must be populated, Campaign Member statuses must be configured, and Campaign Influence must be enabled before the first reporting period. Reliability failures (Contact Roles not populated, lookback window too short) produce silent data gaps rather than visible errors — the report runs but returns zero or incomplete values.
- **Performance** — Campaign Influence reports that span large Opportunity datasets can time out or run slowly without proper filters. Requirements should specify the date range, campaign hierarchy level, and filters that will be applied in production to avoid full-table report scans. For orgs with 100,000+ campaign member records, native reports may require optimization with selective filters or a CRM Analytics dataset.
- **Security** — Not a primary concern for this skill's requirements phase, but attribution model configuration has a security surface: Customizable Campaign Influence model records are visible to all users by default. If attribution credit drives compensation or budget allocation, field-level security on CampaignInfluence.Revenue should be reviewed. Campaign cost data on Campaign records may require profile-based restriction if it is commercially sensitive.

## Architectural Tradeoffs

**Attribution model precision vs. implementation complexity.** First Touch attribution (Primary Campaign Source) requires no additional configuration beyond consistent Contact Role population. It answers one question cleanly but ignores all subsequent campaign touches. Multi-Touch attribution via B2B Marketing Analytics Plus or the Multi-Touch Attribution App answers the full funnel question but requires additional licensing, dataset refresh scheduling, and stakeholder education on why the numbers differ from simpler models. The right answer depends on the business question and the org's willingness to maintain the more complex infrastructure. Requirements must document this tradeoff explicitly rather than defaulting to the most sophisticated option.

**Native reports vs. CRM Analytics for marketing KPIs.** Native Salesforce Campaign Performance Reports are real-time, require no additional license, and cover the majority of standard marketing KPIs. CRM Analytics (and B2B Marketing Analytics Plus) add multi-touch attribution, time-decay models, and cross-object blended datasets, but introduce dataset refresh lag, additional licensing cost, and a separate skill set for dashboard maintenance. Requirements should clearly delineate which KPIs are deliverable natively and which require the analytics layer, rather than building all marketing reporting in CRM Analytics by default.

**Customizable Campaign Influence vs. standard Campaign Influence.** CCI enables richer attribution models but changes the underlying data model: influence credit moves from the Opportunity's Primary Campaign Source field to CampaignInfluence object records. This means standard Campaign Performance Reports (which use Primary Campaign Source) no longer capture influenced revenue — a separate report type must be built against CampaignInfluence. Organizations that enable CCI midproject must rebuild existing attribution reports, retrain stakeholders, and document the data lineage break.

## Anti-Patterns

1. **Attribution model decided after dashboard build.** This is the highest-impact anti-pattern in marketing reporting projects. Changing attribution models post-build forces report type changes, CCI reconfiguration, and in some cases a full Opportunity Contact Role remediation effort. The Well-Architected principle of designing for change requires the attribution decision to be made and locked before any reporting configuration begins.

2. **Using the Campaign Performance Report as the single source of truth for attribution.** The Campaign Performance Report is a valuable operational tool for campaign-level metrics (leads generated, opportunities created, value won at first touch), but it does not capture marketing-influenced pipeline or multi-touch credit. Organizations that use it as their sole attribution report systematically undercount marketing's contribution to influenced pipeline and overweight first-touch campaigns.

3. **Ignoring data quality prerequisites before enabling Campaign Influence.** Enabling Campaign Influence in an org where Opportunities have low Contact Role population rates produces an attribution system that appears to work (no errors) but silently returns incomplete data. The Well-Architected reliability principle requires that data quality prerequisites (Contact Role population rate >90%, Campaign Member statuses configured, MCAE connector active) be confirmed before Campaign Influence is enabled and before attribution dashboards are presented to leadership.

## Official Sources Used

- Campaign Influence Overview — https://help.salesforce.com/s/articleView?id=sf.campaigns_influence_about.htm
- Campaign Performance Report — https://help.salesforce.com/s/articleView?id=sf.campaigns_reports_campaign_performance.htm
- B2B Marketing Analytics (MCAE B2B Marketing Analytics Plus) — https://help.salesforce.com/s/articleView?id=sf.pardot_b2b_marketing_analytics.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
