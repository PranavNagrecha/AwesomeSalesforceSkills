# Gotchas — Analytics Dataset Optimization

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Field Count Degrades Performance Even When Queries Only Touch a Few Fields

**What happens:** A dataset with 400 fields runs noticeably slower SAQL queries than a dataset with the same row count and only 40 fields — even when the SAQL expression references the same 8 fields in both cases. Practitioners expect that querying `avg(Amount)` on a 400-field dataset should be no slower than on a 40-field dataset because only `Amount` is accessed.

**When it occurs:** This manifests in production orgs with datasets exceeding 5–10 million rows and field counts above approximately 100–200 fields. In development sandboxes with small row counts, the difference is imperceptible and the problem is invisible until production scale is reached.

**How to avoid:** Audit dashboard SAQL bindings before creating or expanding a dataset. Include only fields referenced in SAQL queries, security predicates, and join keys. The most efficient datasets for query performance are narrow (few fields) and tall (many rows), not wide. Perform field pruning as part of any performance investigation before tuning SAQL expressions.

---

## Gotcha 2: "Epoch" Field Variants Are Auto-Generated and Must Not Be Re-Declared

**What happens:** When a field is declared as type `Date` in a CRM Analytics dataflow schema node, the platform automatically generates a companion epoch integer field with the suffix `_sec_epoch` (e.g., `CloseDate_sec_epoch`). Practitioners who are not aware of this behavior sometimes add an explicit `computeExpression` step to calculate the epoch manually, creating a duplicate field. Others attempt to declare `_sec_epoch` as a separate field in the `sfdcDigest` node and receive a schema conflict error.

**When it occurs:** This occurs whenever a `computeExpression` node tries to create a field with the same name as the auto-generated epoch companion, or when a practitioner explicitly lists `CloseDate_sec_epoch` as a source field in `sfdcDigest`. It also causes confusion when SAQL queries reference `CloseDate_sec_epoch` without understanding that this field only exists if `CloseDate` was declared as Date type — if `CloseDate` was stored as Text, the epoch companion does not exist.

**How to avoid:** Treat `_sec_epoch` companion fields as read-only outputs of the Date type declaration. Do not declare them in `sfdcDigest` or `computeExpression` nodes. If an epoch field is needed and the source field is stored as Text (not Date), use `toDate()` in a `computeExpression` to first convert the Text to a Date field, then reference the resulting `_sec_epoch` companion in subsequent SAQL or downstream transformations.

---

## Gotcha 3: Dataset Splitting Requires SAQL or Dashboard Changes — It Is Not Transparent

**What happens:** After splitting a 30-million-row dataset into three 10-million-row year-specific datasets, practitioners discover that existing dashboards and lenses still point to the original combined dataset name. The optimization produces no improvement until dashboard configurations are updated to target the new year-specific dataset names. Dashboards that used to show multi-year data with a date filter now show only one year's data because the year-specific dataset only contains that year's rows.

**When it occurs:** This catches teams who perform dataset splitting as a backend-only change without updating the dashboard configurations that consume the dataset. It also catches teams who assume CRM Analytics will "see through" the split and automatically route queries to the correct year-specific dataset based on filter context.

**How to avoid:** Treat dataset splitting as a coordinated change that includes both data pipeline changes (new year-specific Recipes or dataflow branches) and dashboard/lens changes (update each widget or lens to reference the correct year-specific dataset). For dashboards that must show cross-year data, either build a lightweight pre-aggregated summary dataset that spans years, or use SAQL `union` across the year-specific datasets — but validate that the union performance is acceptable before replacing the original dashboard. Run user acceptance testing after the split before retiring the original combined dataset.

---

## Gotcha 4: Recipes Cannot Partially Refresh a Dataset — Every Run Is a Full Replacement

**What happens:** When using a Recipe to build an optimized dataset, practitioners sometimes schedule the Recipe to run every hour expecting that "only new or changed rows" will be refreshed. In practice, every Recipe run reads the full input dataset and writes a full-replacement output dataset. There is no incremental append mode in Recipes.

**When it occurs:** This causes two separate problems: (1) high-frequency Recipe schedules consume multiple run-budget slots per hour from the 60-run rolling window, burning through the budget faster than anticipated; (2) for large source datasets, the Recipe runtime for each run is fixed at "process all rows" regardless of how few rows actually changed since the last run.

**How to avoid:** For datasets that require frequent refresh, evaluate whether the source is a Salesforce object (in which case a Dataflow with Data Sync incremental mode may be more appropriate than a Recipe). For Recipes where high-frequency refresh is genuinely needed, scope the Recipe's source filter to limit input rows (e.g., filter to the current month only for a current-month metrics dataset). For historical datasets where data does not change, switch from scheduled refresh to manual or weekly refresh to conserve run-budget slots.

---

## Gotcha 5: Text-Stored Date Fields Produce Empty Timeseries Charts With No Error

**What happens:** A SAQL `timeseries` expression on a date field stored as Text in the dataset produces a chart with no data points and no visible error message. The dashboard renders an empty visualization. Practitioners spend time debugging SAQL syntax, filter logic, and dashboard configuration before discovering the root cause is the field type in the dataset.

**When it occurs:** This happens when a Salesforce Date or Datetime field is ingested by a `sfdcDigest` node without a corresponding `schema` node declaring `"type": "Date"`. The field arrives as a Text column in the dataset containing ISO-8601 strings (e.g., `"2024-03-15T00:00:00.000Z"`). SAQL `timeseries` requires a column of actual Date type — it does not parse Text columns automatically.

**How to avoid:** After every dataflow or Recipe run that introduces date fields, verify column types in Data Manager (Analytics Studio → Data Manager → Datasets → dataset name → Schema tab) before building dashboard queries. Date columns appear with a calendar icon; Text columns appear with an "A" icon. If a date field shows as Text, add a `schema` transformation node to the dataflow immediately after the `sfdcDigest` and declare the field with `"type": "Date"` and the correct `"format"` string. Re-run the dataflow, re-verify the column type, then build the SAQL query.
