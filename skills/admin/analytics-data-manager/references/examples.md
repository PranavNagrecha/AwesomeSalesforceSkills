# Examples — Analytics Data Manager

## Example 1: Enabling Account and Opportunity for Sync and Materializing a Sales Dataset

**Context:** A Revenue Operations admin is setting up CRM Analytics for the first time. The org has a standard Salesforce setup with Accounts and Opportunities. The goal is to produce a dataset that a recipe can transform into a pipeline dashboard dataset.

**Problem:** Without guidance, admins often assume that enabling objects in Data Manager makes them immediately available for dashboards. After enabling Account and Opportunity and running a successful sync, they open Analytics Studio lens builder and find neither object available — because connected objects are not datasets.

**Solution:**

```
Step 1 — In Data Manager > Connect, edit the Salesforce Local connection.
Step 2 — Enable Account and Opportunity for sync. Set sync mode to Incremental.
Step 3 — Run a manual sync. Verify in Monitor tab:
         - Account: status = Completed, row count matches expected total
         - Opportunity: status = Completed, row count matches expected total
Step 4 — In Recipe Builder, create a new recipe:
         - Add Input node > select "Account" (now available as a connected object source)
         - Add Input node > select "Opportunity"
         - Add a Join transformation on AccountId
         - Add an Output node with dataset name "SalesPipeline"
Step 5 — Run the recipe. Verify dataset "SalesPipeline" appears in Analytics Studio.
Step 6 — In a dashboard, add a widget that queries the "SalesPipeline" dataset.
```

**Why it works:** Data Manager replicates the raw Salesforce records into connected objects (staging layer). The recipe reads from those connected objects and writes a materialized dataset (analytics layer). Dashboards only access datasets — never connected objects directly. The two-step process (sync then recipe) is the canonical pipeline pattern.

---

## Example 2: Configuring a Snowflake Remote Connection for External Quota Data

**Context:** A Sales Ops team stores quota targets in Snowflake. They want to join Salesforce Opportunity data with Snowflake quota data inside CRM Analytics to produce attainment dashboards.

**Problem:** Admins familiar with dataflows attempt to configure the Snowflake connection inside the dataflow JSON or recipe node settings. The connection option is not present there — remote connections are a Data Manager construct and must be configured before they appear as recipe input sources.

**Solution:**

```
Step 1 — In Data Manager > Connect tab, click "Remote Connections" > "New Remote Connection".
Step 2 — Select connector type: Snowflake.
Step 3 — Supply:
         - Account identifier: <org>.snowflakecomputing.com
         - Warehouse: ANALYTICS_WH
         - Database: SALES_DB
         - Schema: QUOTAS
         - Username: crm_analytics_user
         - Authentication: Key Pair (upload private key PEM file)
Step 4 — Add Salesforce CRM Analytics egress IP ranges to the Snowflake network policy
         (available in Salesforce Help: "IP Addresses to Allowlist").
         Without this, the connection test will time out.
Step 5 — Click "Test Connection". Confirm success before enabling any tables.
Step 6 — Enable the "QUOTA_TARGETS" table for sync. Run a full sync.
Step 7 — In Recipe Builder, add an Input node and select the Snowflake
         "QUOTA_TARGETS" connected object. Join with the Opportunity connected object.
Step 8 — Output the joined dataset as "OpportunityAttainment".
```

**Why it works:** Remote connections decouple credential management from transformation logic. Credentials live in Data Manager; recipes reference the resulting connected objects by name. If credentials need rotation, they are updated once in the remote connection — all recipes that reference those connected objects automatically pick up the new credentials on the next sync.

---

## Example 3: Diagnosing Stale Formula Field Data After Incremental Sync

**Context:** An admin notices that Account-level revenue roll-up data in a CRM Analytics dashboard is out of date, even though Opportunity records were updated yesterday and the sync completed successfully this morning.

**Problem:** The Account object has a formula field `Total_Closed_Revenue__c` that sums child Opportunity amounts. When Opportunities are closed, the Opportunity `LastModifiedDate` is updated, but the Account `LastModifiedDate` is not. Incremental sync on Account uses `LastModifiedDate` to detect changes, so the Accounts with stale formula values are never included in the incremental sync batch.

**Solution:**

```
Step 1 — Identify which fields on Account use cross-object formulas or roll-up summaries
         that reference Opportunity or other child objects.
Step 2 — In Data Manager > Connect, edit the Salesforce Local connection.
Step 3 — For the Account object, change sync mode from Incremental to Full,
         OR keep Incremental as the default and add a scheduled Full sync
         (e.g., nightly at 2 AM) in addition to the incremental runs.
Step 4 — Run a Full sync on Account and verify the formula field values update
         in the connected object schema.
Step 5 — Re-run the downstream recipe to materialize the corrected values into the dataset.
Step 6 — Document which objects require periodic full syncs and add them to
         the sync configuration runbook.
```

**Why it works:** Incremental sync's dependence on `LastModifiedDate` is a platform constraint that cannot be overridden. The only reliable remediation is periodic full syncs for objects with cross-object formula dependencies. This is a known limitation documented in Salesforce Help under "Data Sync Limits and Considerations."

---

## Anti-Pattern: Referencing a Connected Object Directly in a Dashboard SAQL Query

**What practitioners do:** After enabling an object in Data Manager and running a sync, some practitioners attempt to query the connected object directly in a SAQL lens or dashboard step using the object's API name (e.g., `q = load "Account";` assuming "Account" is the connected object).

**What goes wrong:** CRM Analytics SAQL operates against datasets registered in the analytics layer. Connected objects are staging-layer replicas stored in a different internal store and are not accessible via SAQL. The query will return an error ("Dataset not found") or — if a dataset named "Account" happens to exist from a previous recipe run — it will silently query the wrong, possibly stale dataset.

**Correct approach:** Always materialize the connected object into a named dataset via a recipe or dataflow output node before referencing it in any dashboard or lens. The SAQL query should reference the dataset name defined in the recipe's Output node, not the connected object name.
