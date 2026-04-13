# Gotchas — CRM Analytics vs Tableau Decision

Non-obvious Salesforce platform behaviors and product facts that cause real architectural mistakes in this domain.

## Gotcha 1: Tableau's Native Salesforce Connector Is Extract-Only — Not Live Query

**What happens:** Architects specify Tableau for Salesforce-centric dashboards expecting live or near-real-time data access, similar to how CRM Analytics queries Salesforce datasets. Instead, every Tableau dashboard backed by the Salesforce connector reflects the most recent scheduled extract, not the current state of Salesforce records.

**When it occurs:** Any time Tableau is connected directly to Salesforce using the built-in Salesforce connector (not through an intermediary data warehouse). The extract refresh cadence — whether hourly, daily, or weekly — determines how stale the data is. There is no live/direct query mode.

**How to avoid:** Document the extract-only constraint explicitly in the decision record before recommending Tableau for any Salesforce use case. If near-real-time Salesforce data is required, CRM Analytics is the only viable Salesforce-native answer. If Tableau is still chosen, route Salesforce data through a data warehouse (Snowflake, Databricks) with a separate integration tool managing the extract schedule, and set stakeholder expectations on lag.

---

## Gotcha 2: 30-Day Lookback Cap on Tableau's Salesforce Incremental Refresh

**What happens:** Tableau's Salesforce connector incremental refresh only re-fetches records with a LastModifiedDate within the last 30 days. Records modified more than 30 days ago are not re-fetched in incremental mode. If a record was retroactively updated (e.g., opportunity close date backdated, contact ownership corrected), that change will not appear in the Tableau extract until the next full refresh runs.

**When it occurs:** Any time an organization relies on Tableau's incremental refresh for the Salesforce connector — which is the typical production configuration to avoid the performance cost of full refreshes. Historical data accuracy degrades silently when records beyond the 30-day window are corrected in Salesforce.

**How to avoid:** If historical accuracy across Salesforce data beyond 30 days is required, either schedule full extract refreshes (accepting the performance cost) or route Salesforce data through a warehouse that handles change data capture before Tableau connects. Do not assume incremental refresh equals a complete and accurate extract of all historical changes.

---

## Gotcha 3: "Tableau CRM" Is a Deprecated Name for CRM Analytics — Not the Same as Tableau

**What happens:** "Tableau CRM" was a Salesforce marketing brand applied to what was originally Einstein Analytics (rebranded circa 2020, then rebranded again to CRM Analytics circa 2022). "Tableau CRM" is an entirely different product from Tableau Desktop, Tableau Server, Tableau Cloud, and Tableau Next. They share a name fragment but are separate products with separate codebases, separate licensing, separate user models, and separate feature sets. Conflating them leads to incorrect license procurement, wrong platform selection, and stakeholder confusion.

**When it occurs:** When LLMs, documentation, or practitioners use "Tableau CRM" to mean the Salesforce-embedded analytics product and stakeholders hear it as Tableau (the BI tool). Also occurs when searching older Salesforce documentation that used the Tableau CRM name pre-2022.

**How to avoid:** Always use the current canonical name: CRM Analytics. When reviewing requirements or existing documentation, flag any use of "Tableau CRM" as a reference to CRM Analytics, not to the Tableau product family. When recommending a platform, use the full product name to eliminate ambiguity.

---

## Gotcha 4: Tableau Next (Tableau+ SKU) Is Not an Upgrade to Existing Tableau Licenses

**What happens:** Tableau Next, sold as the Tableau+ SKU, reached general availability in June 2025. It introduces Agentforce integration, agentic BI capabilities, and tighter coupling with Salesforce Data Cloud / Data 360. Organizations with existing Tableau Server, Tableau Cloud, or legacy Tableau Creator/Explorer/Viewer contracts are not automatically upgraded to Tableau Next capabilities. Tableau Next is a new SKU requiring a separate purchasing decision.

**When it occurs:** When architects assume that "upgrading to Tableau Next" is a software version update (like a patch release) rather than a new product tier with a separate commercial agreement. This affects roadmap planning for orgs building toward Agentforce analytics integration.

**How to avoid:** Treat Tableau Next as a distinct product tier in the evaluation. If the organization has an Agentforce or Data 360 roadmap and wants agentic BI, explicitly scope Tableau Next (Tableau+) as a procurement decision separate from the existing Tableau contract. Do not promise Tableau Next capabilities to stakeholders based on an existing Tableau license.

---

## Gotcha 5: CRM Analytics Permission Set Licenses Are Per-User Assignments — Not Org-Wide Enablement

**What happens:** Enabling CRM Analytics in a Salesforce org (through Setup) does not grant all users access to CRM Analytics features. Each user who needs to view or author CRM Analytics content must be assigned a CRM Analytics Permission Set License (PSL) explicitly. The PSL tier (Growth vs Plus) determines which features are available. Pilots that skip license planning for the full rollout population regularly fail at go-live when users report they cannot see the analytics app.

**When it occurs:** When CRM Analytics is positioned as "already included in our Salesforce contract" without confirming which PSL tier is included, how many PSLs the contract covers, and whether the intended user population exceeds that allocation.

**How to avoid:** Before designing any CRM Analytics solution, confirm the PSL count and tier in the org's Salesforce contract. Map the intended user population to the available PSL inventory. If the user population exceeds the PSL count, either procure additional licenses or constrain the rollout scope. Never assume Salesforce user licenses include CRM Analytics access.

---

## Gotcha 6: Tableau Salesforce Connector Has a 10,000-Character API Query Limit and No Custom SQL

**What happens:** The Tableau Salesforce connector passes queries to the Salesforce REST or Bulk API with a hard 10,000-character limit on the query string. It also does not support Custom SQL — a feature available for most database connectors in Tableau that allows arbitrary SQL to be passed to the source. This means complex multi-field selections, long SOQL WHERE clauses, or computed fields cannot be expressed in the connector layer. Data shaping must happen either in Salesforce (formula fields, reports as data sources) or in Tableau Prep before analysis.

**When it occurs:** When a data architect tries to build a complex Salesforce-sourced Tableau workbook with many fields, complex filters, or calculated columns that would normally be expressed as Custom SQL in other database connectors. The 10,000-character limit can be hit with a large field selection across a wide Salesforce object.

**How to avoid:** Pre-shape Salesforce data in Tableau Prep, in a CRM Analytics dataset exported to a warehouse, or by creating Salesforce Reports as the Tableau data source (which bypasses the SOQL query limit by using Salesforce's report API). Alternatively, route Salesforce data through a warehouse (Snowflake, Databricks) where Tableau's full SQL connector capabilities apply.
