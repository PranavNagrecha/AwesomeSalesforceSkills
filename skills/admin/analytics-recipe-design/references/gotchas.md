# Gotchas: Analytics Recipe Design

Non-obvious CRM Analytics Data Prep behaviors that cause real production problems. Sources are listed in `well-architected.md`. Line references cite the plain-text extraction of each Summer '26 PDF (`pdftotext -layout`), written as `<guide> L<n>`. A claim that could not be re-read in an official source carries an inline `UNVERIFIED (2026-10-03):` marker.

## Gotcha 1: Inner join drops unmatched left rows and the run still succeeds

**What happens:** A Join node set to `Inner` keeps only rows whose keys match on both sides. Every left-side row with no match is removed from the output. The run completes normally, so the only symptom is an output dataset with fewer rows than its primary input.

**When it occurs:** The left input has null keys (Opportunities with no `AccountId`), the right input is a filtered subset (only active Accounts), or key values differ in format. It also occurs when the join type is accepted without review. `JoinParametersInput.joinType` accepts `Cross`, `Inner`, `LeftOuter`, `Lookup`, `MultiValueLookup`, `Outer`, and `RightOuter` (Data Prep Recipe REST API, Join Parameters Input, `salesforce_recipes_api L2770-2795`), so the type is always an explicit choice.

**How to avoid:** Use `Lookup` or `LeftOuter` when the intent is enrichment. Reserve `Inner` for a real "rows in both" requirement. After the first run, compare the primary input count with the output count and treat any difference as a defect until explained. UNVERIFIED (2026-10-03): the statement that the canvas shows no row-count difference after a join comes from practitioner experience, not from a guide.

---

## Gotcha 2: A schedule is created only through the Schedule resource, never through the recipe body

**What happens:** `GET /wave/recipes/<recipeId>?format=R3` returns `scheduleAttributes`, so teams try to set a schedule by editing the recipe or by posting to an invented `/wave/recipes/<id>/schedules` endpoint with a cron expression. The guide states: "While the scheduleAttributes are part of the Recipe, to update a schedule, the /wave/asset/<assetId>/schedule endpoint must be used" (`salesforce_recipes_api L588-596`). The Schedule resource supports GET (52.0), PUT (40.0), and DELETE (43.0) (`bi_dev_guide_rest L6267-6290`).

**When it occurs:** Automating refreshes from CI, from a package post-install step, or from an LLM-generated script that assumes a cron-style job API.

**How to avoid:** `PUT /wave/asset/<recipeId>/schedule` with a body whose `frequency` is `hourly`, `weekly`, `monthly`, `monthlyrelative`, or `eventdriven` (`bi_dev_guide_rest L1488-1566`). There is no cron expression field. The PUT response is empty unless there is an API error. To run immediately, POST to `/wave/dataflowjobs` with the recipe's `targetDataflowId` (starts with `02KB`) as `dataflowId` and `"command":"start"` (`salesforce_recipes_api L598-616`).

---

## Gotcha 3: Recipes and dataflows share a 60-run rolling 24-hour budget

**What happens:** The org can run at most 60 dataflow and recipe jobs in a rolling 24-hour period. Runs shorter than 2 minutes (and data syncs) do not count, but once the limit is reached no dataflow, recipe, or data sync can run, regardless of size. At most 3 recipe runs execute concurrently. Jobs that are scheduled but not executed time out after 5 minutes. An event-based schedule can have at most 5 dependent jobs. (Analytics Platform Setup Guide, Recipe and Dataflow Limits, `bi_admin_guide_setup L1148-1191`.)

**When it occurs:** An hourly schedule on a recipe that runs longer than 2 minutes consumes 24 of the 60 runs by itself. Several such recipes, plus dataflows, exhaust the budget and later jobs are refused.

**How to avoid:** Pick the slowest frequency that meets the freshness requirement. Count every scheduled job that runs longer than 2 minutes before adding a new one. Use an event-based schedule (`"frequency":"eventdriven"`, `"triggerRule":"$ALL_SALESFORCE_OBJECTS"`) when the recipe only needs to follow the local sync. Since Winter '24, recipe runs over 2 minutes count against the limit (`bi_admin_guide_setup L1149-1150`).

---

## Gotcha 4: The Integration User's permissions decide what the recipe can extract

**What happens:** CRM Analytics extracts Salesforce data as the Integration User. "If the dataflow or recipe is configured to extract data from an object or field on which the Integration User does not have permission, the job fails" (`bi_admin_guide_setup L90-94`). The Integration User's permissions limit extraction only; they do not control who can see dataset rows.

**When it occurs:** A new custom field or object is added to a recipe and nobody grants the Integration User read access. It also occurs after an admin restricts the Integration User profile to hide sensitive fields.

**How to avoid:** Check every object and field in the recipe against the Integration User's access before the first run. Restrict sensitive fields on purpose, then design the recipe without them. Do not delete the Integration User or the Security User; Analytics requires both (`bi_admin_guide_setup L105-106`).

---

## Gotcha 5: A security predicate on the Output node only applies when the dataset is created

**What happens:** "After a dataset is created, changes to its security settings must be made by editing the dataset; changes to security settings in the dataflow (rowLevelSharingSource or rowLevelSecurityFilter) or recipe (Security Predicate) have no effect" (Analytics Security Implementation Guide, `bi_admin_guide_security L274-275`). "If row-level security isn't applied to a dataset, any user that has access to the dataset can view all records in the dataset" (`L289`).

**When it occurs:** A recipe ships without a predicate, users open the dataset, and the team later adds a predicate to the recipe's Output node expecting the next run to apply it.

**How to avoid:** Decide row-level security before the first run and set it in the Output node's Security Predicate field (`L300`). If the dataset already exists, change the predicate on the dataset itself. Predicates that reference `$User` need a new user session before a changed value is recognized (`L295`).

---

## Gotcha 6: `WaveRecipe` metadata needs its dataflow, and wildcard retrieval leaves it behind

**What happens:** `WaveRecipe` has a required `dataflow` field holding the recipe's dataflow ID. Deleting a `WaveRecipe` with destructive changes also deletes related `WaveDataflow` components. Wildcard retrieval "doesn't return the recipe's associated dataflows" (Metadata API Developer Guide, WaveRecipe, `api_meta L138986-139058`).

**When it occurs:** A team retrieves `<members>*</members>` for `WaveRecipe`, deploys to another org, and finds the recipe incomplete or unrunnable. It also occurs when a cleanup deploy removes a recipe and its dataflow disappears with it.

**How to avoid:** Name each `WaveRecipe` and its `WaveDataflow` explicitly in `package.xml`. Retrieve from the source org rather than hand-writing the `dataflow` ID. UNVERIFIED (2026-10-03): how a deploy resolves an org-specific `dataflow` ID in a different target org is not described in the guide; test in a sandbox. Schedules are not part of the recipe metadata, so recreate them in the target org with the Schedule resource.

---

## Gotcha 7: Formula nodes use the `Sql` or `Legacy` expression type, not SAQL

**What happens:** Practitioners paste SAQL from a lens (`toDate()`, `group by`, `sum()`) into a Formula node and it fails. The REST API defines `FormulaParametersInput.expressionType` as `Sql` or `Legacy`, and SQL formula fields carry a result type of `DateOnly`, `DateTime`, `Multivalue`, `Number`, or `Text` (`salesforce_recipes_api L2740-2752`, `L4317-4362`).

**When it occurs:** Copying expressions from dashboards, or asking an assistant that answers with SAQL or with Salesforce formula syntax.

**How to avoid:** Write formulas in the recipe editor and validate them there. Put any aggregation in an Aggregate node upstream of the Formula node. UNVERIFIED (2026-10-03): the specific function names available to `Sql` formulas are documented only on help.salesforce.com, which does not serve content to plain HTTP clients.

---

## Gotcha 8: The recipe preview runs as the Security User, so its counts are not the job's counts

**What happens:** "To enable the interactive preview in recipes, Data Prep uses the Security User. When a user previews the results of a recipe, Data Prep shows only the results that the logged-in user has permission to access" (`bi_admin_guide_setup L95-97`). The job itself extracts as the Integration User.

**When it occurs:** A developer validates join row counts in the preview and signs off, but the scheduled job processes rows the developer cannot see, so the output count differs.

**How to avoid:** Reconcile row counts against the output dataset after a real run, not against the preview. Data Prep previews are also limited to 4,000 per hour per user (`bi_admin_guide_setup L1189`).

---

## Gotcha 9: "Recipes cannot run incrementally" is no longer safe to assume

**What happens:** Earlier guidance said every recipe reprocesses its full input with no native incremental option. The current REST API lists `runMode` values `Full`, `Incremental`, and `Streaming` on the recipe definition and on load node input (API 57.0; `salesforce_recipes_api L2953-2956`, `L3660-3663`).

**When it occurs:** Designs that build a manual filter-and-append "incremental" pattern without checking whether the native run mode applies, or designs that assume incremental behavior when the recipe is in `Full` mode.

**How to avoid:** Read the recipe's `runMode` from `GET /wave/recipes/<id>?format=R3` before designing around refresh cost. UNVERIFIED (2026-10-03): which sources and node types support `Incremental` is not stated in the REST guide. Keep the filter, append, and second Output pattern only where the native mode is unavailable, and document it, because the canvas does not explain it.

---

## Gotcha 10: Bucket type must match the source field kind

**What happens:** The REST API defines separate measure, dimension, and date bucket inputs (`salesforce_recipes_api L1812`, `L1915`, `L2001`). A numeric-looking field stored as text (ZIP code, phone number, a "1/2/3" priority) cannot take a measure bucket.

**When it occurs:** The field kind is inferred from its name or sample values instead of the dataset schema.

**How to avoid:** Check the field kind in the dataset schema first. Cast text to number in a Formula node, or use a dimension bucket with discrete values. UNVERIFIED (2026-10-03): whether the canvas blocks the wrong bucket type or fails at run time is not stated in the guides read.
