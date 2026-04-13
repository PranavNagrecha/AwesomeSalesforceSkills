# LLM Anti-Patterns — Analytics Dataflow Development

Common mistakes AI coding assistants make when generating or advising on CRM Analytics dataflow development. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating the 60-Run Limit as a Calendar-Day Reset

**What the LLM generates:** Advice such as "you have 60 dataflow runs available each day — if you hit the limit, it resets at midnight" or scheduling recommendations that assume a midnight quota refresh.

**Why it happens:** LLMs pattern-match to familiar daily API limits (Salesforce API call limits, email send limits) which do reset at midnight GMT. The CRM Analytics run limit is a rolling window, which is less common and more frequently mischaracterized in informal sources.

**Correct pattern:**

```
The org limit is 60 combined dataflow and recipe runs per rolling 24-hour window.
"Rolling" means the window is measured from each run's start time, not from midnight.
A run that starts at 11:30 PM counts against the 24-hour window ending at 11:30 PM the following day.
Monitor run history in Analytics Data Manager or via the REST API (/wave/dataflowjobs)
to count runs within any 24-hour slice before adding new scheduled dataflows.
```

**Detection hint:** Look for phrases like "resets at midnight," "daily limit," "each day you get 60," or "midnight UTC reset" in any advice about dataflow scheduling. These indicate the rolling-window behavior is not being correctly represented.

---

## Anti-Pattern 2: Misrepresenting the 2-Minute Exemption as Applying to Total Job Runtime

**What the LLM generates:** Advice such as "if your dataflow completes in under 2 minutes total, it won't count against the run quota" or "keep your total dataflow runtime under 2 minutes to avoid quota impact."

**Why it happens:** The 2-minute threshold is associated with CRM Analytics run-count behavior in several sources, but LLMs commonly interpret it as a total-job-runtime threshold rather than a per-node-step threshold. The per-step nature requires understanding the node execution model, which is less likely to appear explicitly in training data.

**Correct pattern:**

```
The 2-minute exemption is evaluated per node step, not per total dataflow runtime.
Each individual node's execution duration is checked independently against the threshold.
A dataflow with 10 nodes each completing in 90 seconds would have all nodes exempt,
even if the total job runtime is 15 minutes.
Use Job Progress Details to review per-step duration — do not rely on total run time
when diagnosing exemption behavior or optimizing for quota management.
```

**Detection hint:** Look for references to "total runtime under 2 minutes," "if the whole job completes in 2 minutes," or "keep the dataflow short to avoid quota" — these indicate confusion between per-node and per-job exemption scope.

---

## Anti-Pattern 3: Assuming Augment Supports Multiple Join Types

**What the LLM generates:** Dataflow JSON that includes a `joinType` parameter on the Augment node (e.g., `"joinType": "inner"`) or advice suggesting inner, right, or full-outer joins are achievable via Augment configuration.

**Why it happens:** LLMs trained on SQL documentation, recipe documentation (which does support multiple join types via the Join node), and general ETL concepts default to assuming join-type selection is a standard feature of any join operation. The Augment node's left-join-only constraint is a dataflow-specific limitation that may not appear prominently in training data.

**Correct pattern:**

```json
{
  "Join_Accounts": {
    "action": "augment",
    "parameters": {
      "left": "Filtered_Opportunities",
      "left_key": ["AccountId"],
      "right": "Extract_Accounts",
      "right_key": ["Id"],
      "right_select": ["Name", "Industry"],
      "relationship": "Account"
    }
  }
}
```

```
Augment in CRM Analytics dataflows is left-join-only. There is no joinType parameter.
All rows from the left input are always preserved.
For inner join semantics, add a Filter node after Augment to drop rows where right-side
key fields are null.
For true inner/right/full-outer join support, use Recipes instead of dataflows.
```

**Detection hint:** Look for `joinType`, `join_type`, `type: inner`, `type: full`, or `type: right` inside any `augment` node parameters. These keys do not exist in the dataflow JSON schema and will cause a parse error or silent ignore.

---

## Anti-Pattern 4: Placing Filter Nodes After Augment Instead of Before

**What the LLM generates:** Dataflow JSON where an sfdcDigest node feeds directly into an Augment node, with a Filter node placed after the Augment to discard unwanted rows.

**Why it happens:** LLMs model dataflows as SQL query execution plans where filter placement is a query optimizer's responsibility, not the developer's. In SQL, writing WHERE after JOIN is idiomatic and the optimizer reorders automatically. CRM Analytics dataflows have no query optimizer — node execution order is literal and sequential, so filter placement is the developer's explicit responsibility.

**Correct pattern:**

```json
{
  "Extract_Opps": { "action": "sfdcDigest", ... },
  "Filter_Open": {
    "action": "filter",
    "parameters": {
      "source": "Extract_Opps",
      "saqlFilter": "StageName != \"Closed Won\""
    }
  },
  "Slim_Fields": {
    "action": "sliceDataset",
    "parameters": { "source": "Filter_Open", "fields": [...] }
  },
  "Join_Account": {
    "action": "augment",
    "parameters": { "left": "Slim_Fields", ... }
  }
}
```

```
Place Filter nodes immediately after sfdcDigest or Edgemart, before any Augment or
computeExpression nodes. CRM Analytics dataflows have no execution planner — nodes
run in the order specified. A Filter placed after Augment wastes the join computation
on rows that will be discarded.
```

**Detection hint:** In any generated dataflow JSON, trace each Filter node's `source` back through the graph. If the path from sfdcDigest to Filter passes through an Augment node, the filter is placed too late.

---

## Anti-Pattern 5: Assuming sfdcRegister Supports Append or Upsert Mode

**What the LLM generates:** Dataflow JSON with parameters like `"mode": "append"`, `"mode": "upsert"`, or `"incrementalField": "CreatedDate"` on the sfdcRegister node, or advice suggesting the sfdcRegister node can be configured to add rows to an existing dataset.

**Why it happens:** Incremental/upsert patterns are common in ETL tooling (Informatica, dbt, standard SQL ETL) and LLMs default to these patterns when asked about data loading strategies. The sfdcRegister constraint (full overwrite only) is a CRM Analytics-specific limitation that contradicts the common ETL default.

**Correct pattern:**

```json
{
  "Register_Dataset": {
    "action": "sfdcRegister",
    "parameters": {
      "alias": "My_Dataset",
      "name": "My_Dataset",
      "source": "Final_Transform_Node"
    }
  }
}
```

```
sfdcRegister always performs a full overwrite of the registered dataset.
There is no append, upsert, or incremental mode parameter.
To achieve append semantics: use an Edgemart node to read the existing dataset,
an sfdcDigest node to pull new records, an Append node to combine them, and
sfdcRegister to overwrite with the combined result.
For true incremental loads, use CRM Analytics Recipes with the Sync Out node,
which supports incremental output modes.
```

**Detection hint:** Look for `"mode"`, `"appendMode"`, `"upsertMode"`, `"incremental"`, or `"incrementalField"` as parameters inside any `sfdcRegister` node definition. None of these keys are valid on sfdcRegister.

---

## Anti-Pattern 6: Recommending computeExpression for Window/Partition Calculations

**What the LLM generates:** SAQL inside a computeExpression node that attempts to reference other rows, use aggregate functions across partitions, or calculate running totals or rank within a group.

**Why it happens:** LLMs conflate `computeExpression` (row-level, no inter-row access) with `computeRelative` (partitioned window expressions). This distinction is dataflow-specific and less likely to appear cleanly in training data.

**Correct pattern:**

```json
"Rank_By_Revenue": {
  "action": "computeRelative",
  "parameters": {
    "source": "Filtered_Accounts",
    "computedFields": [
      {
        "name": "Revenue_Rank",
        "type": "Numeric",
        "windowFunction": "rank",
        "orderBy": [{"name": "AnnualRevenue", "direction": "desc"}],
        "partitionBy": [{"name": "Industry"}]
      }
    ]
  }
}
```

```
computeExpression: row-level SAQL expressions only. No access to other rows.
  Use for: derived fields, type conversions, conditional logic per row.

computeRelative: partitioned window expressions. Evaluates across an ordered partition.
  Use for: running totals, rank, prior-period comparisons, cumulative sums.

If the calculation requires looking at other rows (e.g., "rank this row relative to others
in the same industry"), use computeRelative, not computeExpression.
```

**Detection hint:** Look for aggregate functions (`sum(`, `count(`, `max(`, `rank(`) inside a `computeExpression` saqlExpression value. computeExpression does not support aggregation — these expressions will fail at runtime.
