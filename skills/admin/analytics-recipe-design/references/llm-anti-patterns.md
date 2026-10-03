# LLM Anti-Patterns: Analytics Recipe Design

Common mistakes AI coding assistants make when generating or advising on CRM Analytics Data Prep recipes. Use these to self-check output before handing it to a user. Facts cited here are grounded in `gotchas.md`.

## Anti-Pattern 1: Recommending Inner Join When Lookup Is Required

**What the LLM generates:** An Inner join for an enrichment request ("join Opportunities to Accounts to add Industry") with no warning that Opportunities lacking a matching Account disappear.

**Why it happens:** Inner join is the prototypical join in SQL training data. The Lookup join type is specific to CRM Analytics, so the model does not surface it unless asked.

**Correct pattern:**

```
Requirement: "add columns from dataset B to every row of dataset A"
Use: joinType = Lookup (or LeftOuter)

Lookup: keeps every left row, fills matched right columns, nulls where unmatched
Inner:  removes every left row with no match; the run still reports success
```

**Detection hint:** "Inner join" next to words like enrich, add details, look up, or append attributes. Ask: must every row of the primary dataset survive?

---

## Anti-Pattern 2: Inventing a Cron-Style Schedule Endpoint

**What the LLM generates:** `POST /wave/recipes/{id}/schedules` with `scheduleType`, `cronExpression`, and `timeZone`, or a `schedule` block inside the recipe body.

**Why it happens:** Most job schedulers accept cron expressions, and most REST APIs nest schedules under the job resource. The model pattern-matches to that shape. An earlier version of this skill made the same mistake.

**Correct pattern:**

```
PUT /services/data/v67.0/wave/asset/<recipeId>/schedule
{
  "frequency": "weekly",
  "daysOfWeek": ["Monday", "Thursday"],
  "time": { "hour": 0, "minute": 45, "timeZone": "America/Los_Angeles" }
}
```

`frequency` is `hourly`, `weekly`, `monthly`, `monthlyrelative`, or `eventdriven`. GET and DELETE use the same URL. The recipe's `scheduleAttributes` field is read-back only.

**Detection hint:** Any `cronExpression`, any `/schedules` (plural) path under `/wave/recipes`, or any schedule property inside a recipe POST or PATCH body.

---

## Anti-Pattern 3: Using the Recipe Id to Run the Recipe

**What the LLM generates:** `POST /wave/dataflowjobs` with `"dataflowId": "05vB..."` (the recipe Id), or a call to a non-existent `/wave/recipes/<id>/run` endpoint.

**Why it happens:** The model assumes the run endpoint takes the Id of the thing being run.

**Correct pattern:** Read `targetDataflowId` (starts with `02KB`) from `GET /wave/recipes/<recipeId>?format=R3`, then POST `{"dataflowId":"02KB...","command":"start"}` to `/wave/dataflowjobs`. Stop a running job with `PATCH /wave/dataflowjobs/<jobId>` and `{"command":"stop"}`.

**Detection hint:** A `dataflowId` that starts with `05v`, or any recipe "run" endpoint other than `/wave/dataflowjobs`.

---

## Anti-Pattern 4: Writing SAQL or Salesforce Formula Syntax in Formula Nodes

**What the LLM generates:** `toDate(CloseDate, "yyyy-MM-dd")`, `sum(Amount)`, or `BLANKVALUE()` inside a recipe Formula node, presented as known-good.

**Why it happens:** CRM Analytics is strongly associated with SAQL, and Salesforce is strongly associated with its own formula language. The recipe engine is neither.

**Correct pattern:** A recipe formula's `expressionType` is `Sql` or `Legacy`, and each SQL formula field declares a result type (`Text`, `Number`, `DateOnly`, `DateTime`, `Multivalue`). Put aggregation in an Aggregate node upstream. Validate every expression in the formula editor, and say so in the answer, because the function reference is not in the REST guide.

**Detection hint:** `toDate`, `dateValue`, `epoch_to_date`, `group by`, or an aggregate function inside a Formula node; or a function list stated as fact without "validate in the editor".

---

## Anti-Pattern 5: Getting Incremental Behavior Wrong in Either Direction

**What the LLM generates:** Either "the recipe only processes changed records" with no mention of run mode, or "recipes can never run incrementally" followed by a hand-built filter-and-append pattern.

**Why it happens:** Older guidance said recipes always reprocess full input. The current API lists `runMode` values `Full`, `Incremental`, and `Streaming` (API 57.0), and the model has seen both claims.

**Correct pattern:** Read the recipe's `runMode` first. With `Full`, budget for full reprocessing. Use the native run mode where it applies. Keep the manual filter, append, and second Output pattern only when the native mode is unavailable, and document it in the recipe description.

**Detection hint:** Any incremental claim that does not mention `runMode`.

---

## Anti-Pattern 6: Confusing Bucket Types

**What the LLM generates:** A measure bucket on a numeric-looking text field (ZIP code, "1/2/3" priority), or a dimension bucket on a true measure.

**Why it happens:** The model infers field type from names and sample values instead of the dataset schema.

**Correct pattern:**

```
Measure field   -> measure bucket with numeric ranges
Dimension field -> dimension bucket with discrete value groups
Date field      -> date bucket with calendar periods
Numeric text    -> cast in a Formula node first, or use a dimension bucket
```

**Detection hint:** A Bucket node design that never states the source field kind.

---

## Anti-Pattern 7: Adding a Security Predicate to the Recipe After the Dataset Exists

**What the LLM generates:** "Add `'OwnerId' == \"$User.Id\"` to the Output node and rerun the recipe" for a dataset that users already open.

**Why it happens:** The model assumes every recipe run reapplies every recipe setting.

**Correct pattern:** The recipe's Security Predicate applies when the dataset is created. For an existing dataset, edit the predicate on the dataset. Set the predicate before the first run on new recipes. Tell the user that `$User` predicates need a new session to pick up changed values.

**Detection hint:** Predicate advice for an existing dataset that only touches the recipe.

---

## Anti-Pattern 8: Wildcard-Retrieving Recipes for Deployment

**What the LLM generates:** A `package.xml` with `<members>*</members>` for `WaveRecipe` and nothing for `WaveDataflow`, or a hand-written `WaveRecipe` file with a made-up `dataflow` ID.

**Why it happens:** Wildcards work for most metadata types, and the model does not know the recipe depends on a separate dataflow component.

**Correct pattern:** Name each `WaveRecipe` and its `WaveDataflow` explicitly, retrieve both from the source org, and recreate schedules in the target org with the Schedule resource. See `metadata-examples.md`.

**Detection hint:** `WaveRecipe` in a manifest without a matching `WaveDataflow`, or a `dataflow` value that was not retrieved.

---

## Anti-Pattern 9: Omitting Row Count Reconciliation After Joins

**What the LLM generates:** A complete recipe design with Join nodes and no step to compare input and output row counts, or a step that compares against the editor preview.

**Why it happens:** Reconciliation happens after the run, so design-time answers skip it. The preview looks like a run but executes as the Security User and shows only rows the previewing user can access.

**Correct pattern:**

```
After the first real job:
1. Note the row count of each Load node's dataset.
2. Note the row count of the output dataset.
3. If output < primary input and the join is Inner or RightOuter, check for unintended drops.
Do not use the editor preview for this comparison.
```

**Detection hint:** A recipe workflow with a Join node and no post-run count comparison.
