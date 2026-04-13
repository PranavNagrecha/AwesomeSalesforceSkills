# Examples — CRM Analytics vs Tableau Decision

## Example 1: CRM-Heavy Org Choosing CRM Analytics for Native Embedding and Real-Time Salesforce Data

**Context:** A mid-size financial services firm runs all of its client relationship data in Salesforce (Sales Cloud with Financial Services Cloud). The sales leadership team needs pipeline dashboards embedded directly on the Account and Opportunity record pages, visible only to the account owner and their manager hierarchy. The firm has no data warehouse and no existing Tableau investment.

**Problem:** The initial proposal from an external vendor recommends Tableau because "it has better visualizations." The vendor does not flag that Tableau's Salesforce connector is extract-only, or that Salesforce record-level security (account team sharing, territory hierarchy) cannot be enforced in Tableau without a custom row-level security implementation maintained in parallel with every Salesforce sharing rule change.

**Solution:**

Decision criteria documented:
- Data source: 100% Salesforce objects (Opportunity, Account, Activity)
- Freshness requirement: near-real-time (sales reps need current pipeline figures, not yesterday's extract)
- Audience: Salesforce-licensed sales reps and managers working inside Lightning
- Security: Account team sharing must govern analytics row visibility
- Embedding: dashboards required on Lightning record pages

Recommendation: CRM Analytics

Rationale:
1. Tableau's Salesforce connector is extract-only. Near-real-time Salesforce data access requires CRM Analytics dataset sync, not a Tableau scheduled extract.
2. Row-level security in CRM Analytics can enforce the Salesforce sharing model through dataset predicates. Tableau would require a parallel RLS implementation that drifts from Salesforce sharing rules over time.
3. Lightning embedding is native in CRM Analytics via the Analytics component in App Builder. Tableau requires an iFrame integration with a separate Tableau Server or Tableau Cloud license.
4. The firm has no Tableau infrastructure investment to rationalize.

**Why it works:** CRM Analytics is purpose-built for Salesforce-native, sharing-model-aware, Lightning-embedded analytics. The vendor recommendation ignored three architectural constraints that make Tableau the wrong fit for this specific requirement.

---

## Example 2: Enterprise Data Warehouse Scenario Where Tableau's Multi-Source Connectivity Wins

**Context:** A global manufacturing company uses Salesforce Sales Cloud for CRM but runs its primary analytics environment on Snowflake, combining Salesforce pipeline data with ERP production data (SAP), logistics data (Oracle), and marketing attribution data (Marketo). The finance and operations teams are the primary analytics consumers and work primarily outside Salesforce. The company already has 200 Tableau Creator licenses on Tableau Cloud.

**Problem:** An internal Salesforce champion proposes building the cross-system executive dashboard in CRM Analytics because "it's already in Salesforce." The proposal does not account for the fact that CRM Analytics cannot natively query Snowflake, SAP, or Oracle without building separate data pipelines into Salesforce — adding ingestion complexity that the company's data engineering team already manages in Snowflake.

**Solution:**

Decision criteria documented:
- Data sources: Salesforce (20% of total data), Snowflake (primary warehouse), SAP, Oracle, Marketo
- Freshness requirement: daily batch refresh is acceptable for executive reporting
- Audience: finance and operations teams who do not have Salesforce licenses
- Existing investment: 200 Tableau Cloud Creator licenses already under contract
- Salesforce sharing model enforcement: not required for executive cross-system dashboards

Recommendation: Tableau (extend existing Tableau Cloud investment)

Rationale:
1. Snowflake, SAP, and Oracle are all native connectors in Tableau. The multi-source join capability is Tableau's core strength and cannot be replicated in CRM Analytics without significant ETL work.
2. The analytics consumers do not have Salesforce licenses. Adding CRM Analytics PSLs for 200 finance and operations users would be a net-new licensing cost on top of the existing Tableau contract.
3. Daily batch refresh is acceptable, so the Tableau Salesforce connector extract-only limitation is not a disqualifier here — the architecture will extract Salesforce data nightly into Snowflake alongside other sources, using Tableau to blend across all systems.
4. The company already owns Tableau Cloud Creator licenses. Rationalize onto existing infrastructure rather than introducing a parallel analytics platform.

Salesforce data integration approach: Salesforce opportunity and account data is extracted nightly into Snowflake via the company's existing MuleSoft integration. Tableau connects to Snowflake (not directly to Salesforce) for cross-system joins.

**Why it works:** When the analytics requirement is genuinely multi-source and the audience does not live in Salesforce, Tableau is the correct platform. Forcing CRM Analytics into this scenario would require rebuilding the company's entire data warehouse integration inside Salesforce — an architectural anti-pattern that adds cost and complexity without benefit.

---

## Anti-Pattern: Recommending Tableau for "Richer Visualizations" Without Assessing Connector Constraints

**What practitioners do:** An architect recommends Tableau over CRM Analytics for a Salesforce-heavy operational reporting use case because Tableau is perceived as having more sophisticated visualization options or better self-service capabilities.

**What goes wrong:** The team discovers post-deployment that:
- Dashboard data is always one extract cycle stale — sales reps see yesterday's closed won opportunities, not today's.
- The 30-day incremental refresh cap means historical pipeline comparisons beyond 30 days require a full extract scheduled outside business hours.
- Account team security rules that worked in Salesforce Reports are not enforced in Tableau — users see opportunities they are not supposed to see.

**Correct approach:** Assess the Tableau Salesforce connector's specific constraints (extract-only, 30-day cap, no Custom SQL, 10,000-char limit) against the requirement before recommending Tableau for any Salesforce-centric use case. For Salesforce-native operational analytics with sharing model requirements, CRM Analytics is the architecturally correct choice regardless of Tableau's visualization capabilities.
