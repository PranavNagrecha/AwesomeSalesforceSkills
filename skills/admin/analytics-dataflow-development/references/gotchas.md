# Gotchas — Analytics Dataflow Development

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Single Failing Node Aborts the Entire Run — Prior Dataset Unchanged

**What happens:** When any node in a dataflow fails — regardless of where in the pipeline it appears — the entire run is aborted immediately. No downstream nodes execute. The previously registered dataset is not modified; it retains the data from the last successful run.

**When it occurs:** Any node failure triggers this: sfdcDigest field not found, Augment key mismatch, computeExpression SAQL syntax error, row count exceeding the 250M dataset limit, or sfdcRegister alias conflict. The run-summary banner often shows only a generic error; the specific failing node must be found in Job Progress Details.

**How to avoid:** Build dataflows incrementally — add a few nodes at a time and do a manual run before adding more. Use the Job Progress Details view (not just the run summary) to diagnose failures. For critical nightly datasets, set up a scheduled report or notification when a dataflow run fails, since the dataset will silently serve stale data until the issue is fixed and a successful run completes.

---

## Gotcha 2: 60-Run Limit Is a Rolling 24-Hour Window, Not a Calendar Day

**What happens:** When the org hits 60 combined dataflow and recipe runs within any rolling 24-hour window, new runs are queued and will not start until earlier runs fall outside the 24-hour window. Runs do not automatically retry; they fail with a quota error.

**When it occurs:** Orgs with many scheduled dataflows and recipes, particularly when multiple jobs are scheduled at the same clock time (e.g., 2 AM), can trigger 30–40 runs in a one-hour burst. Adding even one new scheduled dataflow can push the org over the limit if the burst already approaches 60. The "rolling" behavior means runs from 11 PM last night still count against today's 2 AM window.

**How to avoid:** Before adding a scheduled dataflow, use Analytics Data Manager to review recent run history and count runs within any 24-hour slice. Stagger scheduled run times so no 24-hour window accumulates near 60. Consolidate dataflows that extract from the same Salesforce objects to reduce total run count. Monitor run counts in production using the CRM Analytics REST API (`/wave/dataflowjobs`) as part of any deployment checklist.

---

## Gotcha 3: sfdcRegister Overwrites — No Append or Upsert Mode

**What happens:** Every successful dataflow run that reaches an sfdcRegister node completely replaces the entire registered dataset. The previous data is deleted and the new data is written atomically. There is no `mode: append` or `mode: upsert` parameter on sfdcRegister.

**When it occurs:** Practitioners who need incremental loads (e.g., only new records from the past 7 days appended to a historical dataset) discover this limitation when they notice the dataset only ever contains the most recent extraction window.

**How to avoid:** For historical datasets that require append semantics, use Recipes (which support incremental loads via the Sync Out output type) rather than dataflows. If a dataflow is required, implement the incremental pattern by extracting both the historical dataset (via Edgemart) and the new records (via sfdcDigest), combining them with an Append node, and registering the combined result — effectively rebuilding the full dataset on every run.

---

## Gotcha 4: Augment Is Left-Join-Only — No Inner, Right, or Full-Outer Join

**What happens:** The Augment node always preserves all rows from the left input. Rows from the left input that have no matching key in the right input are included in the output with null values for all right-side fields. Rows from the right input that have no matching key in the left input are silently dropped. There is no `joinType` parameter.

**When it occurs:** Practitioners who expect SQL-style inner join semantics (only matched rows output) are surprised when unmatched left rows appear with null right-side fields. Dashboard visualizations may show unexpected null entries for fields that should have always-populated values.

**How to avoid:** After an Augment node, add a Filter node to drop rows where a key right-side field is null, if inner-join semantics are required. For full multi-join-type flexibility, use Recipes which provide a visual Join node supporting inner, left, right, and full-outer joins.

---

## Gotcha 5: computeRelative 2-Minute Exemption Applies Per Node, Not Per Total Job Runtime

**What happens:** CRM Analytics dataflow nodes that complete in under 2 minutes are exempt from certain run-count tracking behavior. Practitioners assume this means a dataflow with total runtime under 2 minutes is exempt, but the check is applied per node step — each node's individual execution time is evaluated independently against the 2-minute threshold.

**When it occurs:** When diagnosing run-count quota issues or optimizing dataflows for performance, practitioners look at total job wall-clock time rather than individual node durations. This leads to incorrect conclusions about which nodes trigger the quota tracking behavior and which do not.

**How to avoid:** Always inspect per-step duration in Job Progress Details, not just total run time. A 4-minute dataflow may consist of 10 nodes each completing in under 2 minutes (all exempt) or 2 nodes — one at 30 seconds and one at 3.5 minutes — where the latter triggers quota tracking. Use per-node duration data when making optimization decisions about node splitting or scheduling.

---

## Gotcha 6: Changing sfdcRegister Alias Creates a New Dataset Instead of Renaming

**What happens:** If the `alias` parameter in an sfdcRegister node is changed, the next run creates a brand-new dataset with the new alias. The old dataset is not deleted or renamed — it persists and continues to consume dataset storage quota. Any dashboards or SAQL lenses pointing to the old alias continue to work (and serve stale data) while the new alias gets fresh data.

**When it occurs:** Admins rename an alias to clean up naming conventions. After the rename, dashboards appear to be working (pointing to the old dataset) but they are no longer being updated. The discrepancy is not immediately visible because the old dataset still contains data.

**How to avoid:** Treat the sfdcRegister alias as an immutable identifier. If renaming is necessary, update all dashboards and lenses to reference the new alias before the next dataflow run, and manually delete the old dataset after confirming all consumers have been migrated.
