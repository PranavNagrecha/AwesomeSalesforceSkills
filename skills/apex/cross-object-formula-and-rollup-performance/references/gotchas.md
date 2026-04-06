# Gotchas — Cross-Object Formula and Rollup Performance

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Spanning Limit Counts Across All Metadata Types

**What happens:** A developer adds a validation rule with a single cross-object reference (`Account.Industry`) and a previously working formula field on the same object starts failing to save with "Maximum 15 object references." The formula field itself was not changed.

**When it occurs:** When the cumulative count of unique spanning relationships across formula fields, validation rules, workflow field updates, and cross-object flow references on a single object reaches 15. Any metadata type that adds a new unique relationship path can push another metadata type over the limit.

**How to avoid:** Maintain an inventory of spanning relationships per object. Before adding any cross-object reference in any metadata type, check the current count. Consolidate formulas that reference the same relationship chain into fewer fields where possible.

---

## Gotcha 2: Rollup Filters Do Not Re-Fire on Distant Record Changes

**What happens:** A rollup summary on Account sums Opportunity Amount where a child formula field `Region_Match__c` (which reads `Account.Region__c`) equals true. An admin changes the Account's `Region__c` value, but the rollup does not recalculate — it still shows the old sum.

**When it occurs:** Whenever a rollup filter references a cross-object formula field on the child, and the change occurs on the record that the formula spans to (the grandparent or further). The rollup only recalculates when the direct child record is inserted, updated, deleted, or undeleted.

**How to avoid:** Denormalize the filter value onto the child as a stored field (synced via trigger or flow). When the distant record changes, the trigger updates the stored field on the child, which in turn triggers the rollup recalculation.

---

## Gotcha 3: Full Recalculation After Metadata Deploy Changes Rollup Filter

**What happens:** A deployment changes the filter criteria on a rollup summary field. After deployment, the platform queues a full background recalculation of the rollup across all parent records. During recalculation, parent records show incorrect (partially recalculated) values. On orgs with millions of records, this can take hours.

**When it occurs:** Any metadata change to a rollup summary field's filter criteria — whether through Setup UI, Change Sets, or Metadata API deployment.

**How to avoid:** Schedule rollup filter changes during low-usage windows. Communicate to downstream consumers (reports, dashboards, integrations) that rollup values may be temporarily inaccurate. Monitor the background job in Setup > Deployment Status or via AsyncApexJob queries.

---

## Gotcha 4: Parent Record Locking During Rollup Recalculation

**What happens:** An integration bulk-loads 10,000 child records across 50 parent records using 4 parallel threads. Multiple threads try to update children of the same parent simultaneously. The rollup recalculation locks the parent record, causing UNABLE_TO_LOCK_ROW for concurrent threads.

**When it occurs:** Any time multiple DML operations on child records targeting the same master-detail parent execute in parallel — common in Data Loader parallel mode, MuleSoft parallel processing, or concurrent API calls.

**How to avoid:** Sort child records by parent ID before loading to minimize cross-thread parent contention. Use serial mode in Data Loader for master-detail relationships. In custom integrations, batch child records by parent and process each parent's children in the same thread.

---

## Gotcha 5: Cross-Object Formula Fields Cannot Be Indexed

**What happens:** A developer creates a cross-object formula field and uses it in a SOQL WHERE clause on a large object. The query performs a full table scan because formula fields — especially cross-object ones — are never indexable, even with a Salesforce Support request for custom indexing.

**When it occurs:** Any SOQL query that filters on a cross-object formula field, regardless of record volume. The query optimizer cannot use an index and falls back to a full scan.

**How to avoid:** Replace the cross-object formula with a stored field populated by a trigger or flow. Stored fields can be indexed. Request a custom index from Salesforce Support if query selectivity still requires it.
