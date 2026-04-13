# Examples — Analytics Dataflow Development

## Example 1: Dataflow Optimization — Filter Before Augment

**Context:** An admin builds a CRM Analytics dataflow that joins all Case records to their parent Account records in order to produce a support analytics dataset. The initial build pulls all Cases (500,000 rows), then immediately runs an Augment join against Accounts, then filters to only open Cases afterward. The dataflow runs for 90 minutes and frequently times out.

**Problem:** The Augment node joins all 500,000 Case rows against the Account dataset before the Filter node discards closed Cases. Augment is the most memory-intensive node type; performing it on the full row set wastes compute on rows that will never appear in the output.

**Solution:**

Restructure the node order to filter first, then join:

```json
{
  "Extract_Cases": {
    "action": "sfdcDigest",
    "parameters": {
      "object": "Case",
      "fields": [
        {"name": "Id"},
        {"name": "AccountId"},
        {"name": "Subject"},
        {"name": "Status"},
        {"name": "Priority"},
        {"name": "CreatedDate"}
      ]
    }
  },
  "Filter_Open_Cases": {
    "action": "filter",
    "parameters": {
      "source": "Extract_Cases",
      "saqlFilter": "Status != \"Closed\""
    }
  },
  "Trim_Case_Fields": {
    "action": "sliceDataset",
    "parameters": {
      "source": "Filter_Open_Cases",
      "fields": [
        {"name": "Id"},
        {"name": "AccountId"},
        {"name": "Subject"},
        {"name": "Priority"},
        {"name": "CreatedDate"}
      ]
    }
  },
  "Extract_Accounts": {
    "action": "sfdcDigest",
    "parameters": {
      "object": "Account",
      "fields": [
        {"name": "Id"},
        {"name": "Name"},
        {"name": "Industry"},
        {"name": "OwnerId"}
      ]
    }
  },
  "Join_Account": {
    "action": "augment",
    "parameters": {
      "left": "Trim_Case_Fields",
      "left_key": ["AccountId"],
      "right": "Extract_Accounts",
      "right_key": ["Id"],
      "right_select": ["Name", "Industry", "OwnerId"],
      "relationship": "Account"
    }
  },
  "Register_Support_Dataset": {
    "action": "sfdcRegister",
    "parameters": {
      "alias": "Open_Cases_With_Account",
      "name": "Open_Cases_With_Account",
      "source": "Join_Account"
    }
  }
}
```

**Why it works:** The Filter node reduces 500,000 Case rows to ~40,000 open Cases before they reach the Augment node. The SliceDataset node drops the `Status` field (no longer needed after filtering) before the join, reducing the memory footprint of each row during the join operation. Run time dropped from 90 minutes to under 12 minutes for this org.

---

## Example 2: Diagnosing and Recovering from a Failing Node

**Context:** A nightly dataflow that refreshes the `Pipeline_Analytics` dataset fails at 2 AM. The run summary shows "Failed" but the error message says only "An unexpected error occurred." The dashboard shows yesterday's data because sfdcRegister never completed.

**Problem:** The run-summary error message does not identify which node failed or why. The admin needs to pinpoint the failing node and understand whether the dataset is in a consistent state.

**Solution:**

1. Navigate to Analytics Data Manager → Dataflow Jobs → select the failed run.
2. Click "Job Progress Details." This shows per-node status: each node shows "Completed," "Running," or "Failed" with a node-level error message.
3. In this case, the `computeRelative` node `Rank_By_CloseDate` shows: "Error: orderBy field CloseDate is not present in the source schema." The upstream `SliceDataset` node had been recently edited and accidentally dropped `CloseDate`.
4. Confirm the registered dataset is intact: open `Pipeline_Analytics` in Analytics Studio. Because sfdcRegister never ran, the dataset reflects the last successful run — data is complete but one day stale.
5. Fix the `SliceDataset` node to include `CloseDate`, upload the corrected dataflow JSON, and trigger a manual run.

```json
"Trim_Pipeline_Fields": {
  "action": "sliceDataset",
  "parameters": {
    "source": "Filter_Active",
    "fields": [
      {"name": "Id"},
      {"name": "AccountId"},
      {"name": "Amount"},
      {"name": "CloseDate"},
      {"name": "StageName"}
    ]
  }
}
```

**Why it works:** CRM Analytics dataflows are atomic at the run level. A failing node aborts the run and leaves the registered dataset in its prior state. This is both a safety guarantee (no partial data) and a diagnostic complexity (the dataset looks healthy but is stale). Always check Job Progress Details — not just the run-summary banner — to find the root cause.

---

## Example 3: Adding a Row-Level Calculated Field with computeExpression

**Context:** An admin needs to add a `Days_To_Close` field to an Opportunity dataset — the number of days between `CreatedDate` and `CloseDate`.

**Problem:** sfdcDigest does not support computed fields; the calculation must happen inside the dataflow. Using a recipe function is not an option because this is an existing dataflow.

**Solution:**

```json
"Compute_Days_To_Close": {
  "action": "computeExpression",
  "parameters": {
    "source": "Extract_Opportunities",
    "mergeWithSource": true,
    "computedFields": [
      {
        "name": "Days_To_Close",
        "type": "Numeric",
        "label": "Days to Close",
        "precision": 18,
        "scale": 0,
        "defaultValue": "0",
        "saqlExpression": "dateDiff(\"day\", toDate(CreatedDate_sec_epoch), toDate(CloseDate_sec_epoch))"
      }
    ]
  }
}
```

**Why it works:** `computeExpression` evaluates a SAQL expression in row context for every row in the source. Setting `mergeWithSource: true` preserves all upstream fields and appends the new computed column. Date arithmetic in SAQL requires epoch-seconds fields (suffixed `_sec_epoch`), which CRM Analytics generates automatically for Date and DateTime fields during sfdcDigest ingestion.

---

## Anti-Pattern: Placing sfdcRegister Mid-Pipeline

**What practitioners do:** To debug intermediate node output, some practitioners add a temporary `sfdcRegister` node in the middle of a dataflow to inspect intermediate data, leaving it in place after debugging.

**What goes wrong:** sfdcRegister is a terminal node — placing it mid-pipeline registers a partial dataset with every run. Any downstream nodes after the mid-pipeline register still run and may register the final dataset as well. The org now has a ghost intermediate dataset consuming dataset storage quota, and the org's run time increases because both register operations execute on every scheduled run.

**Correct approach:** Use the Analytics REST API (`/wave/dataflowjobs/{id}/nodes/{nodeId}`) to inspect intermediate node output without registering it. Alternatively, temporarily disable scheduling, run the dataflow manually, and use Job Progress Details to view row counts per node. Remove any debugging register nodes before re-enabling the schedule.
