# Well-Architected Notes — Community Analytics Data

## Relevant Pillars

- **Trusted** — Analytics on community data carries data governance obligations. NetworkActivityAudit contains member-level behavioral data (who logged in, what pages they viewed). Access to this data via custom reports must be governed by appropriate report folder permissions and sharing settings. The 12-month rolling deletion by the platform is a platform-enforced data minimization behavior — complementing this with an explicit retention policy prevents both data loss and unintended long-term accumulation.
- **Adaptable** — Community analytics strategy should anticipate changing requirements. Starting with built-in Engagement Insights is appropriate for early-stage sites, but the architecture should be designed to extend to custom reports and GA4 without rework. Choosing NetworkUserHistoryMonthly for aggregate trend data and GA4 for behavioral funnels from the outset avoids later migration pain.
- **Operational Excellence** — Monitoring and observability for Experience Cloud sites should include documented data lag characteristics (24 hours for Engagement Insights), retention windows (12 months for NetworkActivityAudit), and refresh cadences for any scheduled reports or exports. Stakeholder communication about these constraints is part of a well-operated analytics implementation.

## Architectural Tradeoffs

**Built-in dashboards vs. custom reports:** Engagement Insights requires zero setup and is immediately available but provides no customization or export. Custom report types on NetworkActivityAudit require one-time setup but provide full flexibility, scheduling, and CRM data joins. The tradeoff is setup effort vs. long-term flexibility. For any site where analytics will be reviewed by business stakeholders beyond the admin team, invest in the custom report type early.

**GA4 vs. native reporting:** GA4 and Salesforce native reporting are complementary, not competing. Native reporting confirms who (authenticated member identity, license type, CRM attributes) while GA4 confirms what behavior occurred in session (funnel steps, scroll, time on page). Architectures that rely on only one surface have blind spots. The recommended approach is to run both and cross-reference.

**NetworkActivityAudit vs. NetworkUserHistoryMonthly:** Row-level audit data enables drill-down and filtering by individual member, page, or time period. Monthly aggregates lose drill-down fidelity but avoid storage pressure and survive the 12-month rolling deletion. For long-term trend reporting, use monthly aggregates as the primary store and retain row-level data only for recent months.

## Anti-Patterns

1. **Using CRM Analytics for basic community engagement metrics** — CRM Analytics requires an additional license and significant setup overhead (datasets, dataflows, SAQL). For standard login counts, page views, and member growth, standard Reports on NetworkActivityAudit are simpler, included in Experience Cloud licensing, and sufficient. Only escalate to CRM Analytics when multi-object joins, predictive models, or SAQL complexity exceed what standard Reports can support.

2. **Relying solely on Engagement Insights without a retention plan** — The built-in dashboards are appropriate for day-to-day monitoring but they do not replace a data retention strategy. Organizations that treat Engagement Insights as their only analytics surface discover too late that NetworkActivityAudit records older than 12 months are gone and no historical baseline exists for trend analysis.

3. **Treating GA4 as optional for Experience Cloud analytics** — Practitioners who skip GA4 integration lose session-level behavioral data (funnel progression, bounce rate, conversion) that Salesforce does not natively capture. For any site where self-service success metrics or content performance measurement is a business goal, GA4 integration should be included in the initial site launch checklist.

## Official Sources Used

- Salesforce Help — Web Analytics and Reporting in Experience Cloud — behavioral analytics, Engagement Insights, and GA4 integration guidance
- Salesforce Help — Track Activity with Custom Reports (NetworkActivityAudit) — custom report type setup and NetworkActivityAudit object behavior
- Salesforce Help — Insights for Engagement (Engagement Insights dashboards) — built-in dashboard capabilities and limitations
- Salesforce Help — GA4 Integration for Experience Cloud (Google Analytics 4) — Measurement ID configuration and republish requirement
- Salesforce Well-Architected Overview — architecture quality model framing (Trusted, Adaptable, Operational Excellence)
- Object Reference — NetworkActivityAudit and NetworkUserHistoryMonthly object semantics and field definitions
