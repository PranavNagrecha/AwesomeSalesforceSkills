# Gotchas — Analytics Recipe Design

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Lookup Join vs Inner Join — Silent Row Loss

**What happens:** When a Join node is configured as Inner, any row from the left (primary) input dataset that has no matching row in the right (secondary) input dataset is permanently dropped from the output. No warning is emitted, no error is logged, and the recipe run reports "Completed" with a green status. The only observable symptom is that the output dataset has fewer rows than the input.

**When it occurs:** Any time an Inner join is used and the two datasets do not have perfectly matching key values for every row. Common triggers:
- Left dataset has rows with null join keys (e.g., `AccountId` is null on some Opportunity records)
- Right dataset is a filtered subset (e.g., only Active accounts) and the left dataset references inactive or deleted records
- Data quality issues cause key mismatches (e.g., leading/trailing spaces in ID fields)

**How to avoid:** Explicitly choose Lookup (not Inner) when the requirement is "add columns from a secondary dataset to every row of the primary dataset." After each recipe run, compare the input Load node row count against the output dataset row count in Analytics Studio. Any shrinkage requires a join type audit.

---

## Gotcha 2: Recipe Scheduling Is a Separate API Resource — Not Embedded in the Recipe

**What happens:** Developers expect to find a `schedule` property in the recipe definition JSON (the `/wave/recipes/{id}` resource body). No such property exists. Attempts to add a schedule field to the recipe JSON either have no effect or produce a validation error. The recipe runs only on-demand unless a schedule is created through the Schedule Resource API or the Analytics Studio UI scheduling panel.

**When it occurs:** Any time a practitioner tries to configure a recurring recipe refresh by editing the recipe JSON directly, by including a schedule in a deployment package, or by searching the recipe metadata for a schedule property.

**How to avoid:** Use the Schedule Resource API endpoint exclusively:
- Create: `POST /services/data/v62.0/wave/recipes/{recipeId}/schedules`
- Read: `GET /services/data/v62.0/wave/recipes/{recipeId}/schedules`
- Delete: `DELETE /services/data/v62.0/wave/recipes/{recipeId}/schedules`

The request body accepts `scheduleType`, `cronExpression`, and `timeZone`. Schedules survive recipe edits and re-saves — they are not overwritten when the recipe body is updated.

---

## Gotcha 3: Formula Nodes Use the Recipe Expression Language, Not SAQL

**What happens:** Practitioners familiar with CRM Analytics SAQL attempt to write SAQL functions inside a recipe Formula node (e.g., `toDate()`, `dateValue()`, `groupby()`, `sum()`). The recipe expression language has a different function library and syntax. SAQL functions either fail to parse or silently return null depending on the formula editor's validation behavior.

**When it occurs:** When a practitioner:
- Copies a SAQL expression from a lens or dashboard and pastes it into a formula node
- Attempts to use SAQL date parsing functions (`toDate`, `epoch_to_date`) in a formula
- Tries to reference an aggregated value (e.g., `sum(Amount)`) in a formula node placed before an Aggregate node

**How to avoid:** Use only the recipe expression language functions documented in the Salesforce Help "Transformations for Data Prep Recipes" reference. For date operations, use `DATE()`, `YEAR()`, `MONTH()`, `DAY()`. For aggregations, always place the Aggregate node upstream of any Formula node that needs to reference an aggregated value.

---

## Gotcha 4: Recipes Reprocess Full Input on Every Run — No Native Incremental Support

**What happens:** Unlike some ETL frameworks, CRM Analytics recipes do not support native incremental or delta loads. Every scheduled or on-demand run reads the complete input dataset from scratch and reprocesses every row through the entire node graph. For datasets with millions of rows, this means every run consumes the full processing time and quota, regardless of how many rows actually changed since the last run.

**When it occurs:** When a recipe is built on a large connected object (e.g., 5M+ Event or Task records) and the design assumes that only new or changed records will be processed on each run.

**How to avoid:** If partial incremental behavior is required, implement it explicitly:
1. Add a Filter node early in the graph to restrict rows to a recent date window (e.g., `LastModifiedDate >= 30 days ago`).
2. Use an Append node to union the filtered "recent" output with a previously stored full-history dataset.
3. Add a second Output node to persist the full-history dataset for use in the next run's Append step.

This pattern approximates incremental behavior but still reprocesses the filtered window on every run. True change-data-capture incremental loading is not available natively in recipes as of Spring '25.

---

## Gotcha 5: Bucket Node Type Must Match the Source Field Kind

**What happens:** Attempting to create a Measure bucket on a Dimension (string) field, or a Dimension bucket on a Date field, causes a configuration error in the recipe canvas. The bucket type selector options change based on the detected type of the source field. Selecting an incompatible bucket type is either blocked by the UI or produces a recipe validation failure on run.

**When it occurs:** When the source field type is ambiguous or when a field that appears numeric is stored as a string dimension in the dataset (e.g., a ZIP code or phone number stored as a text field).

**How to avoid:** Inspect the source field's data type in the dataset schema view before adding a Bucket node. If a numeric-looking field is stored as a Dimension (string), either cast it to a number in a preceding Formula node, or use a Dimension bucket with discrete value matching instead of range-based Measure bucket logic.
