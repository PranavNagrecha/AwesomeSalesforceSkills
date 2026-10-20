# Well-Architected Notes — Manufacturing Cloud Setup

## Relevant Pillars

UNVERIFIED (2026-10-20): the corpus holds no Manufacturing Cloud Developer Guide; the row-count scale, "nightly is the default" and "sub-hourly" statements below are not corpus-grounded (a forecast set's documented `calculationFrequency` is Weekly to Yearly, meta 264 L16754-16763).

- **Reliability** — The ABF recalc and Rebate Payout DPE jobs are the trust spine of Manufacturing Cloud. Stale forecasts erode executive trust in the platform; missed rebate payouts erode partner trust. Monitor DPE job success / failure with alerts and a runbook for failure recovery.
- **Scalability** — At enterprise scale (10K+ accounts, 1K+ products, 24-month schedules), `AccountProductForecast` grows into the millions of rows. ABF recalc duration and storage cost grow with this volume; review DPE performance and `AccountProductForecast` retention policy quarterly.
- **Operational Excellence** — Manufacturing Cloud relies on multiple opt-in DPE jobs (ABF recalc, Rebate Payout, optional Sales Agreement actuals refresh). Document each one's activation and schedule in the org runbook so they survive sandbox refreshes.

## Architectural Tradeoffs

**Native Sales Agreement vs. Custom Multi-Period Opportunity:** Custom multi-period Opportunity models look simpler at first because they reuse familiar Sales Cloud objects. They become unmaintainable at scale because Opportunity Stage doesn't apply, OpportunityLineItem schedules are a separate feature, and reporting can't aggregate planned-vs-actual cleanly. Use `SalesAgreement` from day one.

**ABF Recalc Cadence:** (UNVERIFIED 2026-10-20: the nightly default and DPE granularity claims; the forecast set's `calculationFrequency` runs Weekly to Yearly, meta 264 L16754-16763.) Nightly is the default and right answer for most orgs. Sub-hourly recalc requires custom triggers because DPE has minimum schedule granularity, and the recalc cost scales with `AccountProductForecast` row count. Avoid the sub-hourly path unless the business case is concrete (real-time supply-chain decisions, not generic "fresher data").

**Rebate Engine: Native vs. Custom:** Custom Apex rebate logic accumulates edge-case bugs over years (period boundaries, retroactive corrections, product eligibility). The native Rebate Management engine handles these at the cost of accepting cumulative-tier semantics. If marginal-tier rebates are a hard requirement, the maintenance burden of custom Apex is the cost of business — but it's a cost.

**Channel Revenue Management Module Enablement:** The CRM module adds substantial schema and Setup complexity. Enable only when sell-in / sell-through tracking with partner inventory is a real requirement. Direct-customer rebates do not require CRM.

## Anti-Patterns

1. **Skipping ABF Recalc Activation** — Most common Manufacturing Cloud go-live failure. `AccountProductForecast` empty, executive dashboards blank, team blames "the data."

2. **Custom Multi-Period Opportunity Model** — Reusing Opportunity for multi-period commitments produces unmaintainable reporting and a one-way migration to `SalesAgreement` later.

3. **Custom Rebate Logic Where Native Suffices** — Years of accumulated edge-case bugs when the native engine handles the same calculation correctly.

4. **Forgotten DPE Activations After Sandbox Refresh** — A common pitfall: refreshing a sandbox loses DPE schedules. Add DPE activation to the post-refresh runbook for every Manufacturing Cloud sandbox.

## Official Sources Used

- Manufacturing Cloud Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.mfg_cloud_dev.meta/mfg_cloud_dev/mfg_cloud_dev_intro.htm (UNVERIFIED 2026-10-20: not in the corpus)
- Metadata API Developer Guide 264 — `SalesAgreementSettings` L128607-128700; `AdvAccountForecastSet` L16722-16763; DPE `processType` L27579-27584; `computationMethod` L128795-128801. Object Reference 264 — `ProgramRebateType` L235325-235326, L235555-235565; `ChannelProgram` L65922-65924
- Manufacturing Cloud (Salesforce Help) — https://help.salesforce.com/s/articleView?id=sf.mfg_overview.htm&type=5
- Account-Based Forecasting — https://help.salesforce.com/s/articleView?id=sf.mfg_abf_overview.htm&type=5
- Rebate Management — https://help.salesforce.com/s/articleView?id=sf.rebate_management_overview.htm&type=5
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
