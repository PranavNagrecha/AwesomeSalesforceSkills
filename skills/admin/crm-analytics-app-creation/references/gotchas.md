# Gotchas: CRM Analytics App Creation

Non-obvious behaviours that leave a new CRM Analytics app empty, stale, over-shared, or undeployable. Each gotcha names its source. Claims that could not be confirmed from a fetched source carry an inline `UNVERIFIED (2026-10-03):` marker. "Setup Guide" means the Analytics Platform Setup Guide (Spring '26); "Security Guide" means the Analytics Security Implementation Guide (Spring '26); "REST Guide" means the CRM Analytics REST API Developer Guide (Summer '26); "Dashboard JSON Guide" means the Analytics Dashboard JSON Developer Guide (Summer '26); "Metadata API" means the Metadata API Developer Guide, Version 67.0.

## Gotcha 1: Permission Set Assignment Does Not Grant Data Access

**What happens:** A user assigned the CRM Analytics Plus User permission set can open Analytics Studio, but dashboards inside an app show nothing or return "Insufficient Privileges." App access is a separate grant: "if a user has the 'Use CRM Analytics' permission, the user must also have Viewer access on an app to view its datasets, lenses, and dashboards." UNVERIFIED (2026-10-03): the exact error text users see varies and was not confirmed.

**When it occurs:** Admins coming from standard reports, where a profile or permission set is enough to see records.

**How to avoid:** After assigning the permission set, share the app (App > Share) with at least Viewer access, then decide row-level security for each dataset. Test with a non-admin user before marking the work complete.

**Source:** Setup Guide, Advanced CRM Analytics Platform Setup, note under the user permission table (Viewer access requirement; "the type of access granted on an app controls the actions that can be performed on its datasets, lenses, and dashboards").

---

## Gotcha 2: Datasets Are Refreshed By Jobs Within A Daily Run Budget

**What happens:** Dashboard values lag the records. A record updated an hour ago still shows its old value until the next recipe or dataflow run, and a failed run leaves the last good data in place. Schedules are bounded: 60 dataflow and recipe runs per rolling 24 hours (runs under 2 minutes and data sync excluded), with 1 concurrent dataflow in sandboxes and Growth production orgs and 2 with Plus.

**When it occurs:** Nightly schedules on operational dashboards, and orgs that add schedules app by app without a shared budget.

**How to avoid:** Set a refresh cadence per dataset and count it against the 60-run budget. Monitor job failures in the Data Manager monitor. Show the data's as-of time on the dashboard. UNVERIFIED (2026-10-03): the earlier path "Setup > Analytics > Notifications" for failure emails was not found in a fetched source. For live data, the limits page refers to "Direct Data for Data Cloud," which is a different data source, not a faster dataset refresh.

**Source:** Setup Guide, CRM Analytics Limits, Recipe and Dataflow Limits; Lens and Dashboard Limits (Direct Data for Data Cloud export limit).

---

## Gotcha 3: Faceting Crosses Datasets Only Through Connected Data Sources

**What happens:** A dashboard has a Case chart and an Opportunity chart, and clicking a Region bar on one does not filter the other. By default, faceting propagates a selection to steps on the same dataset. Steps on different datasets need either a connected data source (the dashboard's `dataSourceLinks`, which the guide calls "Cross-Dataset Faceting with Connected Data Sources") or a binding. This corrects the earlier statement that faceting can never cross datasets.

**When it occurs:** Any dashboard that mixes datasets and relies on click-to-filter.

**How to avoid:** Link the shared field across datasets with a connected data source, or write a selection binding when the relationship is not a simple field match. Control which steps send and receive facets with `broadcastFacet` and `receiveFacetSource`.

**Source:** Dashboard JSON Guide, dataSourceLinks JSON ("defines all data sources configured for the dashboard"; pointer to Configure Cross-Dataset Faceting with Connected Data Sources); aggregateflex step properties (`broadcastFacet`: "Faceting is when a selection in a widget filters other steps in the dashboard"; `receiveFacetSource` modes `all`, `none`, `include`, `exclude`).

---

## Gotcha 4: Connected Objects Are A Cache, Not A Dataset, And Data Sync Has Its Own Limits

**What happens:** After enabling Data Sync for Opportunity, the admin looks for it in the lens explorer and cannot use it. "Connected objects can't be visualized directly, but are used like a cache to speed up other jobs." Sync itself is limited: at most 100 objects enabled for data sync (local and remote), 3 concurrent sync runs, and 24 hours per job for local objects (12 for remote). UNVERIFIED (2026-10-03): the earlier statement that connected objects do not count against dataset row limits was not confirmed.

**When it occurs:** First builds, and orgs that sync every object "just in case."

**How to avoid:** Feed connected objects into a recipe or dataflow that registers a dataset, and build lenses on the dataset. Sync only the objects recipes use; contact Support before enabling sync for more than 100 objects.

**Source:** REST Guide, Replicated Dataset Resources description. Setup Guide, CRM Analytics Limits, Data Sync Limits.

---

## Gotcha 5: Changing Security In The Recipe After The Dataset Exists Does Nothing

**What happens:** An admin edits the recipe's Security Predicate (or a dataflow's `rowLevelSecurityFilter` or `rowLevelSharingSource`) to tighten access and reruns the job. Users still see the old rows: "After a dataset is created, changes to its security settings must be made by editing the dataset." A dataset with no row-level security shows all rows to anyone with app access.

**When it occurs:** Security fixes after go-live, and migrations that move predicates into recipes.

**How to avoid:** Change predicates on the dataset (dataset edit page or REST), then retest with a restricted user. If sharing inheritance is used, keep a backup predicate (`'false'` blocks users sharing cannot cover) and check coverage with `GET /wave/security/coverage/datasets/<datasetIdOrApiName>/versions/<versionId>`.

**Source:** Security Guide, Add Row-Level Security with a Security Predicate (note on editing the dataset; warning on no row-level security; `'false'` default with sharing inheritance); Add Row-Level Security by Inheriting Sharing Rules. REST Guide, Security Coverage Dataset Version Resource (API 41.0).

---

## Gotcha 6: Analytics Metadata Deploys Definitions, With Rules That Break Hand Edits

**What happens:** A team hand-edits a retrieved dashboard file and the deployment fails, or deploys an app and finds empty dashboards in the target org. The Metadata API states that "Modifications to the .wdash component are unsupported" and that removing steps from a `.wdash` makes deployment fail. `WaveDataset` carries only `application`, `description`, `masterLabel`, and `type`, so the rows are not part of the deployment. Retrieving `WaveRecipe` with a wildcard "doesn't return the recipe's associated dataflows," and deleting a recipe with `destructiveChanges.xml` also deletes its related `WaveDataflow`. UNVERIFIED (2026-10-03): that a deployed dataset stays empty until its recipe runs in the target org follows from the field list but was not stated in a fetched source.

**When it occurs:** First promotion from sandbox to production.

**How to avoid:** Edit dashboards in the designer or JSON editor, then retrieve; never edit `.wdash` files by hand. Name recipes and their dataflows explicitly in `package.xml`. After deployment, run the recipes in the target org before sharing the app.

**Source:** Metadata API, WaveDashboard (considerations list, `.wdash` suffix, `application` required), WaveDataset (fields), WaveRecipe (wildcard note, deletion note, `securityPredicate`, `targetDatasetAlias`), WaveApplication (`.wapp` in the `wave` folder, `shares`).

---

## Gotcha 7: Templated Apps Carry Contractual Limits And Assets You May Not Want

**What happens:** A team builds on the Sales Analytics template and keeps adding custom objects. "The Sales Analytics and Service Analytics apps limit custom object support a maximum of 10 custom objects and one dataflow per app. These limits are contractual, not technical." Unused template datasets still consume runs and rows.

**When it occurs:** Template apps extended over several releases.

**How to avoid:** Count custom objects before extending a template app. Prune unused template datasets and dashboards so they stop consuming refresh runs and row allocation. Build a custom app when the design needs more than the template allows.

**Source:** Setup Guide, CRM Analytics Limits, Sales Analytics and Service Analytics App Limits; Dataset Row Storage Allocations per License.

---

## Gotcha 8: Sharing Inheritance Costs Time And Still Needs A Backup Predicate

**What happens:** An admin turns on sharing inheritance to avoid writing predicates and sees recipes and queries slow down, while some users see nothing. "The tradeoff for applying sharing inheritance is an increase in the time to complete data syncs, dataflow and recipe jobs, and queries," and sharing inheritance must be paired with a security predicate for cases it cannot honour.

**When it occurs:** Orgs with complex sharing on the source object, and users whose access comes from many sharing rows.

**How to avoid:** Use sharing inheritance with a backup predicate, measure job and query time before and after, and check which source objects are covered with the Security Coverage resources. Use an explicit predicate where inheritance is slow or incomplete.

**Source:** Security Guide, overview note ("If you use sharing inheritance, you must also set a security predicate to take over in situations when sharing settings can't be honored") and Add Row-Level Security by Inheriting Sharing Rules (time trade-off). REST Guide, Security Coverage Dataset Version Resource.
