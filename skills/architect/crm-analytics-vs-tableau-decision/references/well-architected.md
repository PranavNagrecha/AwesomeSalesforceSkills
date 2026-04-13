# Well-Architected Notes — CRM Analytics vs Tableau Decision

## Relevant Pillars

- **Performance** — CRM Analytics queries Salesforce datasets that sync from the org's objects, supporting near-real-time access without extract lag. Tableau's Salesforce connector introduces inherent latency through scheduled extract jobs, which affects query performance from a data freshness perspective. The 10,000-character API query limit on the Tableau Salesforce connector is also a performance and scalability constraint at the connector layer.

- **Scalability** — CRM Analytics scales within Salesforce's trust boundary and is subject to Salesforce platform limits on dataset row counts and dataflow steps. Tableau scales horizontally on Tableau Server or Tableau Cloud infrastructure, and is better suited to high-concurrency analyst workloads outside Salesforce. For multi-source analytics at enterprise scale, Tableau's connector ecosystem (Snowflake, Databricks, Redshift) provides broader data platform scalability than CRM Analytics, which is optimized for Salesforce object data.

- **Cost Optimization** — The two platforms have fundamentally different cost structures. CRM Analytics requires per-user Permission Set Licenses layered on top of existing Salesforce user licenses. Tableau uses a separate Creator/Explorer/Viewer model (or Tableau+ capacity model) that is independent of Salesforce licensing. Hybrid architectures that use both platforms incur dual licensing costs. Architects must evaluate total cost of ownership against the specific analytics use case — using CRM Analytics for Salesforce-native BI and Tableau for cross-system BI often avoids over-licensing for either capability.

- **Security** — CRM Analytics can enforce the Salesforce sharing model (OWD, sharing rules, territory hierarchies, account team sharing) through dataset row-level security predicates. Tableau extracts carry no Salesforce record-level security metadata; enforcing equivalent row-level security in Tableau requires a separate, custom implementation that must be kept in sync with every Salesforce sharing model change. This is a significant security architecture difference that must be surfaced in any decision involving regulated or sensitive data.

- **Reliability** — CRM Analytics dataset refresh jobs (dataflows, recipes) are Salesforce platform operations subject to Salesforce's scheduled maintenance windows and platform limits. Tableau extract refresh jobs run on Tableau Server or Tableau Cloud infrastructure, independent of Salesforce maintenance windows. For orgs with strict analytics SLA requirements, the operational dependencies of each refresh architecture differ and should be evaluated against the reliability requirement.

## Architectural Tradeoffs

**Salesforce-native depth vs multi-source breadth:** CRM Analytics provides deep, native integration with Salesforce objects, sharing model, and Lightning embedding. Tableau provides broad connectivity across dozens of data source connectors. Choosing one over the other requires a clear understanding of whether the analytics requirement is Salesforce-centric or enterprise-wide.

**Real-time vs refresh-based data:** CRM Analytics dataset sync can be configured for near-real-time Salesforce data access. Tableau's Salesforce connector is extract-only with scheduled refresh cycles, introducing inherent lag. This tradeoff is non-negotiable — it is a product constraint, not a configuration choice.

**Security model native vs replicated:** CRM Analytics enforces Salesforce security natively through dataset predicates. Tableau requires a parallel, custom row-level security implementation for Salesforce-equivalent access control. In regulated industries (financial services, healthcare, government), the maintenance burden and auditability of a replicated security model is a significant long-term cost.

**License stack simplicity vs capability:** CRM Analytics PSLs keep analytics users within the Salesforce license stack — simpler user management, unified SSO, consistent permission model. Tableau introduces a separate license hierarchy, a separate user directory, and separate governance. This is a systems administration tradeoff, not just a cost one.

**Tableau Next forward path:** Organizations with an Agentforce or Data 360 strategic roadmap should factor Tableau Next (Tableau+, GA June 2025) into the long-term platform decision. Tableau Next positions enterprise BI as an Agentforce-native capability, which changes the calculus for orgs already investing in Salesforce's AI platform.

## Anti-Patterns

1. **Tableau for all Salesforce analytics to avoid a second tool** — Using Tableau as the sole analytics platform for Salesforce-heavy operational use cases because the organization wants to avoid managing two tools. This forces all Salesforce operational reporting through an extract-only connector, producing stale dashboards and requiring a custom row-level security implementation. The correct architectural approach is to match platform to use case: CRM Analytics for Salesforce-native operational BI, Tableau for cross-system enterprise BI.

2. **CRM Analytics for all analytics to maximize Salesforce investment** — Forcing all analytics requirements, including cross-system enterprise BI, through CRM Analytics to justify Salesforce license spend. CRM Analytics is not designed for multi-source BI across non-Salesforce systems. Building complex data pipelines to push non-Salesforce data into Salesforce objects for CRM Analytics to consume is an anti-pattern that creates fragile ingestion dependencies and duplicates data platform infrastructure.

3. **Skipping the freshness and security assessment** — Making the CRM Analytics vs Tableau recommendation based on visualization preference or existing relationships rather than formally documenting the freshness requirement, the sharing model enforcement need, and the connector constraints. Decisions made without this assessment routinely fail post-deployment when the extract lag or security gap is discovered.

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- CRM Analytics Setup and User Guide (Salesforce Help) — https://help.salesforce.com/s/articleView?id=sf.bi_admin_guide.htm
- Tableau Salesforce Connector documentation — https://help.tableau.com/current/pro/desktop/en-us/examples_salesforce.htm
- Tableau Next (Tableau+) product information — https://www.salesforce.com/products/tableau/tableau-next/
- CRM Analytics Limits and Considerations (Salesforce Help) — https://help.salesforce.com/s/articleView?id=sf.bi_admin_limits.htm
- Salesforce Analytics Platform License Overview — https://help.salesforce.com/s/articleView?id=sf.bi_admin_license.htm
