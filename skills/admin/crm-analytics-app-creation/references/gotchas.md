# Gotchas — CRM Analytics App Creation

## Gotcha 1: Permission Set Assignment Does Not Grant Data Access

**What happens:** A user assigned the CRM Analytics Plus User permission set can access Analytics Studio and see app names in their app list, but the dashboards inside those apps show no data. The user may also receive "Insufficient Privileges" when opening a dataset lens.

**When it occurs:** Any time an admin stops at permission set assignment without also configuring app-level sharing. Extremely common when admins migrate from standard Salesforce reports (where profile/permission set is sufficient to see records) and assume the same model applies to CRM Analytics.

**How to avoid:** After assigning the CRM Analytics permission set, always open the app in Analytics Studio and configure sharing (App > Share). Assign the user or group at least the Viewer role. Then verify the dataset row-level security predicate is in place if users should see a restricted subset of data. Test with a non-admin user login before marking configuration complete.

---

## Gotcha 2: Datasets Are Not Updated in Real-Time

**What happens:** Users report that data visible in a CRM Analytics dashboard does not match current Salesforce record values. A record updated an hour ago still shows the old value in the dashboard. Users lose confidence in the analytics data.

**When it occurs:** When practitioners configure a dataset refresh schedule (dataflow or recipe) that is infrequent (e.g., nightly), or when the refresh job fails silently and the dataset continues serving the last successful run's data without any user-visible error.

**How to avoid:** Set a refresh schedule appropriate for the use case — daily for historical trend dashboards, every 4–6 hours for operational dashboards. Configure dataflow/recipe failure email notifications in Setup > Analytics > Notifications so failed runs are caught immediately. Surface the dataset's "Last Updated" timestamp in dashboard headers so users understand data currency expectations. Never promise real-time data in CRM Analytics dashboards without a Direct Data or live connection configuration.

---

## Gotcha 3: Faceting Cannot Cross Dataset Boundaries

**What happens:** A developer builds a dashboard with two chart widgets — one showing open cases (from a Case dataset), another showing Opportunity pipeline (from an Opportunity dataset). They enable faceting expecting that clicking a "Region" bar in the Case chart will filter the Opportunity chart to the same region. The click registers no change in the Opportunity widget.

**When it occurs:** Any dashboard that enables faceting but has steps referencing different datasets. Faceting works by propagating a filter to other steps that share the same dataset. Steps on different datasets are outside the faceting scope.

**How to avoid:** Design dashboards with faceting in mind: widgets intended to filter each other must share the same dataset (join at the dataset level, not the dashboard level). For cross-dataset filtering, use selection bindings — configure a binding that reads the selection value from Step A and uses it as a filter parameter in Step B's SAQL query. This requires editing the dashboard JSON or using the advanced binding UI.
