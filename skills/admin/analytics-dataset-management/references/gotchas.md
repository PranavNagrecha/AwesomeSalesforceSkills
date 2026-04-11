# Gotchas — Analytics Dataset Management

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: The 60-Run Quota Is Org-Wide and Has No Native Alert

**What happens:** When the total number of dataflow and recipe runs in a rolling 24-hour window reaches 60, any subsequently queued jobs are not executed. The queued jobs appear in Data Manager with a status of "Queued" or are silently skipped depending on the platform version. No email notification is sent, no in-product banner is shown, and downstream dashboards continue serving the data from the last successful run. From the perspective of end users and dashboard viewers, nothing looks obviously wrong — data is just a day or two stale.

**When it occurs:** Orgs with multiple managed packages that include their own dataflows (Revenue Intelligence, Service Analytics, Einstein Activity Capture, Nonprofit Success Pack Analytics, and similar) are most at risk. Each package can add 1–5 nightly or hourly flows without the admin realizing it. Custom flows added on top of a heavy managed-package footprint push the org over 60 runs per day without warning.

**How to avoid:** Before scheduling any new dataflow, export or manually audit the full list of scheduled dataflows and recipes from Data Manager > Schedules, and calculate the total runs per 24-hour window. Keep total projected runs below 55 to preserve headroom for ad-hoc runs and new requirements. Configure failure notifications under Data Manager > Notification Settings so at minimum one person is alerted when a run is skipped or fails.

---

## Gotcha 2: Date Fields Ingested Without a Schema Node Are Permanently Stored as Text

**What happens:** A `sfdcDigest` node in a dataflow pulls a Salesforce Date or Datetime field without a downstream `schema` or `computeExpression` node that declares its type. CRM Analytics stores the column as type Text. The dataflow completes successfully, the dataset appears in Data Manager, and no error is reported. However, any SAQL query that uses the field in a `timeseries`, `group by date`, or date range filter returns zero data or silently ignores the filter. The dashboard appears broken, but the dataflow shows green.

**When it occurs:** Any dataflow built without an explicit schema-typing step on date fields. This is easy to miss when using the drag-and-drop recipe builder if the practitioner does not inspect the inferred column type before publishing. It also occurs when a Salesforce Date field is added to an existing object and the dataflow is updated to include it without adding the corresponding schema declaration.

**How to avoid:** After every dataflow run that introduces new date fields, open the dataset in Data Manager and inspect the Column Type column. Date fields must show `Date`, not `Text`. If a field shows `Text`, add a `schema` node (for new flows) or a `computeExpression` node with `toDate(fieldName, "format-string")` (for existing flows) and re-run the dataflow. For new dataflows, make explicit date declaration part of the build checklist before the first production run.

---

## Gotcha 3: Append-Mode Datasets Grow Without Bound — 500M Org Row Ceiling Blocks All Datasets

**What happens:** CRM Analytics datasets loaded in append mode accumulate rows on every run. There is no automatic expiration, no TTL mechanism, and no platform-enforced row trim. Once the org-wide total across all datasets reaches 500 million rows, every subsequent dataset write operation — across all dataflows and all datasets in the org — fails with a capacity error. Dataflows return an error status; dashboards for unrelated datasets also stop refreshing.

**When it occurs:** Common in orgs that use CRM Analytics to analyze event logs, email activity, case interactions, or any other high-cardinality object. An append-mode dataset loading 500,000 activity records per day will reach 180 million rows in a year. An org with three such datasets hits the 500M ceiling in roughly one year. It also occurs when a recipe is configured to append historical exports without the admin realizing that each run adds rows permanently.

**How to avoid:** For every append-mode dataset, calculate the expected monthly row growth and project when the dataset will need to be trimmed or switched to full-replace. Add a `filter` node in the dataflow to restrict ingested rows to a rolling window (e.g., the last 13 months) unless full history is genuinely required. Periodically check org-wide row consumption in Data Manager > Datasets view. If a historical archive is needed, separate it into a purpose-built archival dataset with a separate, infrequent refresh schedule rather than growing the operational dataset indefinitely.

---

## Gotcha 4: Managed-Package Dataflows Cannot Be Edited — But Count Against the Same Quota

**What happens:** Products like Revenue Intelligence, Service Analytics, and Nonprofit Success Pack Analytics deploy their own dataflows into the org. These flows appear in Data Manager but are locked — they cannot be edited, rescheduled, or deleted without uninstalling the package. They run on the vendor-defined schedule. Their run count is included in the same 60-run/day org quota.

**When it occurs:** Orgs that install multiple analytics-enabled managed packages and then add custom dataflows on top of the managed footprint. Admins often do not know the managed-package flows exist until they audit the schedule list.

**How to avoid:** After installing any managed package that includes CRM Analytics content, immediately audit the Schedules tab in Data Manager and record how many runs per day the package adds. Account for this in all future scheduling decisions. Contact the package vendor to understand whether their flow schedules can be adjusted (some packages expose a configuration setting; others do not). Design custom flows around the managed-package windows.
