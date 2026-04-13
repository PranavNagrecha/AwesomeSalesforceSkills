# LLM Anti-Patterns — Analytics Recipe Design

Common mistakes AI coding assistants make when generating or advising on Analytics Recipe Design.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Inner Join When Lookup Is Required

**What the LLM generates:** The assistant suggests an Inner join for an enrichment use case (e.g., "join Opportunities to Accounts to add Account Industry"), without noting that this will silently drop Opportunity rows that have no matching Account.

**Why it happens:** "Inner join" is the most commonly documented join type in SQL training data. LLMs default to it as the prototypical join and conflate "joining two datasets" with "Inner join semantics." The Lookup join type is specific to CRM Analytics and is not present in generic SQL training data, so the model does not surface it without prompting.

**Correct pattern:**

```
When the requirement is: "add columns from dataset B to every row of dataset A"
→ Use: Lookup join (not Inner)

Lookup: preserves all left-side rows, appends matched right-side columns, writes null for unmatched rows
Inner:  drops any left-side row that has no match in the right dataset — SILENT DATA LOSS
```

**Detection hint:** Look for recommendations containing "Inner join" in an enrichment context (phrases like "add details", "enrich", "look up", "append attributes from"). Flag and ask: "Does this join need to preserve all rows from the primary dataset?"

---

## Anti-Pattern 2: Embedding Schedule Configuration Inside the Recipe Definition

**What the LLM generates:** The assistant provides a recipe JSON body or deployment configuration that includes a `schedule` field, `cronExpression`, or `refreshInterval` property inside the recipe definition object, suggesting this is how recipe scheduling is configured.

**Why it happens:** In many ETL tools and job schedulers, the schedule is co-located with the job definition. LLMs generalize this pattern to CRM Analytics recipes without knowing that Salesforce separates the schedule resource from the recipe resource.

**Correct pattern:**

```
# WRONG — schedule does not exist in recipe body
POST /wave/recipes
{ "name": "My Recipe", "schedule": { "cron": "0 0 3 * * ?" } }  ← has no effect

# CORRECT — schedule is a separate API resource
POST /wave/recipes/{recipeId}/schedules
{
  "scheduleType": "cron",
  "cronExpression": "0 0 3 * * ?",
  "timeZone": "America/Los_Angeles"
}
```

**Detection hint:** Any response that includes `schedule`, `cron`, `refreshInterval`, or `frequency` as a property inside a recipe body JSON should be flagged. The schedule is always a POST to the `/schedules` sub-resource.

---

## Anti-Pattern 3: Using SAQL Functions in Formula Node Expressions

**What the LLM generates:** The assistant writes formula node expressions using SAQL syntax — for example, `toDate(CloseDate, "yyyy-MM-dd")`, `dateValue()`, `sum(Amount)`, or `groupby()` — inside a recipe Formula node.

**Why it happens:** CRM Analytics is strongly associated with SAQL in training data. LLMs conflate the query language (SAQL, used in lenses and dashboard queries) with the recipe expression language (used in Formula nodes). The two languages are syntactically different and have overlapping but distinct function libraries.

**Correct pattern:**

```
# WRONG — SAQL syntax does not work in recipe Formula nodes
toDate(CloseDate, "yyyy-MM-dd")       ← SAQL date function, not available in recipes
dateValue(CloseDate)                   ← SAQL function, not available in recipes

# CORRECT — Recipe expression language equivalents
DATE(YEAR(CloseDate), MONTH(CloseDate), DAY(CloseDate))
YEAR(CloseDate)
MONTH(CloseDate)
DAY(CloseDate)
```

**Detection hint:** Flag any formula expression containing `toDate`, `dateValue`, `epoch_to_date`, `groupby`, `sum(`, `count(`, or other SAQL aggregate/date functions. These are not valid in recipe Formula nodes.

---

## Anti-Pattern 4: Assuming Recipes Support Native Incremental Loads

**What the LLM generates:** The assistant describes a recipe design that will "process only new or changed records since the last run" as if this is a native recipe capability, without flagging that recipes reprocess the full input on every run.

**Why it happens:** Incremental/delta loading is a standard feature of ETL tools and is so commonly expected that LLMs assume it exists unless explicitly told otherwise. The concept of "incremental recipe" appears in some Salesforce documentation contexts (e.g., Connected Data Sources can have incremental sync), which LLMs may conflate with recipe-level incremental processing.

**Correct pattern:**

```
# WRONG — assumption
"The recipe will automatically process only records modified since the last run."

# CORRECT — explicit statement of behavior
"Recipes reprocess the full input dataset on every run. There is no native incremental
load support. To approximate incremental behavior:
1. Add a Filter node to restrict rows to a recent date window (e.g., LastModifiedDate >= 30 days ago)
2. Use an Append node to union the filtered output with a stored historical snapshot dataset
3. Add a second Output node to persist the updated historical snapshot for the next run
This is an approximation, not true CDC. Full reprocessing always occurs."
```

**Detection hint:** Flag any response that says recipes will "only process changed records", "detect new rows", "run incrementally", or "pick up where it left off" without explicitly implementing the filter-append workaround pattern.

---

## Anti-Pattern 5: Confusing Bucket Node Types (Measure vs Dimension vs Date)

**What the LLM generates:** The assistant recommends a Measure bucket for a field that is stored as a string dimension (e.g., a status code like "1", "2", "3" stored as text), or recommends a Dimension bucket for a numeric measure field. The recipe either fails to validate or produces incorrect bucket assignments.

**Why it happens:** LLMs infer field type from the field name or sample values rather than from the actual dataset schema. A field named `Priority` with values "1", "2", "3" looks numeric to an LLM but may be stored as a Dimension (string) in the dataset schema, making it incompatible with a Measure bucket.

**Correct pattern:**

```
# Check the field type in the dataset schema before configuring a Bucket node

If field is a Measure (numeric):   → Use Measure bucket with numeric range definitions
If field is a Dimension (string):  → Use Dimension bucket with discrete value groupings
If field is a Date:                → Use Date bucket with calendar period definitions

# For numeric-looking string fields: either cast to number in a preceding Formula node,
# or use a Dimension bucket with explicit discrete value matching ("1" → "Low", etc.)
```

**Detection hint:** Any recipe design that specifies a Bucket node without explicitly stating the source field type (Measure / Dimension / Date) and confirming it matches the bucket type configuration should be flagged for schema verification.

---

## Anti-Pattern 6: Omitting Row Count Verification After Join Nodes

**What the LLM generates:** The assistant provides a complete recipe design that includes Join nodes but does not include any step to verify the output row count against the input row count after the recipe runs.

**Why it happens:** LLMs describe the "happy path" of recipe construction. Row count verification is a runtime validation step that occurs after the recipe runs, not a canvas configuration step, so it is often omitted from design-time guidance.

**Correct pattern:**

```
After every recipe run that includes a Join node:
1. Note the row count of the left-input Load node dataset (visible in Analytics Studio dataset detail)
2. Note the row count of the Output dataset
3. If Output rows < Left input rows and the join type is Inner or RightOuter, investigate for
   unintended row drops — switch to Lookup or LeftOuter if enrichment (not filtering) is the intent
```

**Detection hint:** Any recipe workflow recommendation that includes a Join node but contains no post-run row count comparison step is incomplete. Flag and add: "Verify output row count against input row count after the first run."
