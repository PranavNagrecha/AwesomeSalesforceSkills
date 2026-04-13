# Well-Architected Notes — Donor Lifecycle Requirements

## Relevant Pillars

- **Operational Excellence** — Fundraising operations require consistent, repeatable donor lifecycle workflows. Moves Management stage definitions, LYBUNT report configurations, and Engagement Plan sequences must be documented and maintained so staff can execute cultivation workflows consistently across portfolio managers.
- **Reliability** — Donor lifecycle data must be accurate for portfolio reviews, board reports, and grant applications. NPSP rollup fields (LastOppDate, TotalGifts) must be recalculated after any bulk data correction. ERD status transitions must be monitored to prevent donors from falling into lapsed status without detection.
- **Security** — High-net-worth donor capacity data, personal relationship notes, and giving history are sensitive. Field-level security should restrict access to wealth screening scores and capacity ratings to authorized gift officers and development leadership only.

## Architectural Tradeoffs

**Opportunity-based cultivation vs. Contact-based tracking:** Using Opportunities for major gift cultivation provides financial pipeline visibility (amount, close date, stage) but requires fundraisers to create Opportunity records before they know a gift will happen. Contact Activity-only tracking is simpler but provides no financial projection for pipeline reporting. The right balance is creating Opportunities when prospects enter formal cultivation, while continuing to log activities on the Contact for relationship history.

**NPSP vs. NPC for new implementations:** NPSP is the legacy platform; NPC is the current offering for new orgs. NPSP has mature moves management tooling (Engagement Plans, LYBUNT reports) but is no longer available for new orgs. NPC's Actionable Segmentation provides portfolio management but uses a different design paradigm. Do not mix NPSP and NPC feature guidance in the same design document.

## Anti-Patterns

1. **Using Contact Activities as the sole cultivation tracking method** — Activities log interactions but provide no pipeline visibility, no financial projections, and no stage-based management view for leadership. Moves Management requires Opportunity records with stage, amount, and close date to be useful.
2. **Conflating NPC Actionable Segmentation with marketing automation** — Segmentation classifies donors for portfolio management. It does not trigger emails, manage campaign audiences, or interface with Marketing Cloud. Designs that expect segmentation to execute outreach require a separate marketing automation layer.
3. **Failing to build pipeline reports alongside moves management configuration** — Moves Management stage configuration without corresponding pipeline report design results in adoption failure — fundraisers update stages but leadership cannot see the pipeline data, negating the entire workflow.

## Official Sources Used

- Moves Management with Nonprofit Success Pack (Trailhead) — https://trailhead.salesforce.com/content/learn/modules/moves-management-with-nonprofit-success-pack
- Nonprofit Cloud Philanthropy and Partnerships — Manage Portfolios and View Donor Profiles (Trailhead) — https://trailhead.salesforce.com/content/learn/modules/nonprofit-cloud-philanthropy-and-partnerships
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
