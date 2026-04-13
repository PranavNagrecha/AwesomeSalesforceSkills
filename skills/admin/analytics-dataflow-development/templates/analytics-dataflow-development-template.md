# Analytics Dataflow Development — Work Template

Use this template when building, debugging, or optimizing a CRM Analytics dataflow.

## Scope

**Skill:** `analytics-dataflow-development`

**Request summary:** (fill in what the user asked for — e.g., "build a new Opportunity + Account joined dataset" or "debug a failing nightly dataflow")

---

## Context Gathered

Record answers to the Before Starting questions from SKILL.md before writing any JSON.

- **Source objects and fields:**
  - Object 1: (name, fields needed)
  - Object 2: (name, fields needed)
- **Target dataset name (alias):** (this is the sfdcRegister alias — treat as immutable once in production)
- **Expected row volume:** (rows in primary object after filtering)
- **Join logic:** (which fields join which objects — note that Augment is left-join-only)
- **Calculated fields needed:** (SAQL expressions — note computeExpression for row-level, computeRelative for window/partition)
- **Scheduling frequency:** (how often, what time)
- **Current org run count:** (check Analytics Data Manager — must be below 50/60 before adding new schedule)
- **Known constraints or limits:** (e.g., approaching 250M row cap, existing pipelines consuming same objects)

---

## Node Graph Design (fill before writing JSON)

Map the pipeline from left to right. Filter and SliceDataset must appear before Augment.

```
[sfdcDigest: Object1] → [Filter: condition] → [SliceDataset: trim fields] ─┐
                                                                             ├→ [Augment: join] → [computeExpression: derived fields] → [sfdcRegister: alias]
[sfdcDigest: Object2] → [SliceDataset: trim fields] ──────────────────────┘
```

Nodes (fill in):

| Step | Node Name | Action | Source(s) | Key Config |
|---|---|---|---|---|
| 1 | | sfdcDigest | — | object:, fields: |
| 2 | | filter | step 1 | saqlFilter: |
| 3 | | sliceDataset | step 2 | fields: (only what's needed) |
| 4 | | sfdcDigest | — | object:, fields: |
| 5 | | sliceDataset | step 4 | fields: (only join key + right_select) |
| 6 | | augment | step 3 (left), step 5 (right) | left_key:, right_key:, right_select: |
| 7 | | computeExpression | step 6 | computedFields: |
| 8 | | sfdcRegister | step 7 | alias:, name: |

---

## Dataflow JSON

```json
{
  "TODO_Ingestion_Node": {
    "action": "sfdcDigest",
    "parameters": {
      "object": "TODO_ObjectAPIName",
      "fields": [
        {"name": "Id"},
        {"name": "TODO_FieldAPIName"}
      ]
    }
  },
  "TODO_Filter_Node": {
    "action": "filter",
    "parameters": {
      "source": "TODO_Ingestion_Node",
      "saqlFilter": "TODO_SAQLCondition"
    }
  },
  "TODO_SliceDataset_Node": {
    "action": "sliceDataset",
    "parameters": {
      "source": "TODO_Filter_Node",
      "fields": [
        {"name": "Id"},
        {"name": "TODO_JoinKeyField"}
      ]
    }
  },
  "TODO_Right_Ingestion_Node": {
    "action": "sfdcDigest",
    "parameters": {
      "object": "TODO_RightObjectAPIName",
      "fields": [
        {"name": "Id"},
        {"name": "TODO_AttributeField"}
      ]
    }
  },
  "TODO_Augment_Node": {
    "action": "augment",
    "parameters": {
      "left": "TODO_SliceDataset_Node",
      "left_key": ["TODO_LeftJoinKey"],
      "right": "TODO_Right_Ingestion_Node",
      "right_key": ["Id"],
      "right_select": ["TODO_AttributeField"],
      "relationship": "TODO_RelationshipName"
    }
  },
  "TODO_Register_Node": {
    "action": "sfdcRegister",
    "parameters": {
      "alias": "TODO_DatasetAlias",
      "name": "TODO_DatasetAlias",
      "source": "TODO_Augment_Node"
    }
  }
}
```

---

## Checklist

Copy from SKILL.md review checklist and tick items as you complete them.

- [ ] Filter nodes are placed before all Augment nodes, not after
- [ ] SliceDataset nodes trim unused fields before expensive joins
- [ ] sfdcRegister alias matches the intended dataset API name (changing alias creates a new dataset)
- [ ] Org is under 50 scheduled runs per rolling 24-hour window (leave buffer)
- [ ] Row volume of the registered dataset is confirmed below 250 million rows
- [ ] All node names are unique within the dataflow JSON
- [ ] Dataflow JSON is valid (no trailing commas, correct bracket pairing)
- [ ] Job Progress Details reviewed after first manual run — no node warnings suppressed
- [ ] No `joinType` parameter on any Augment node
- [ ] No `mode`/`appendMode`/`incremental` parameter on any sfdcRegister node
- [ ] computeExpression nodes do not contain aggregate functions (sum, rank, etc.) — use computeRelative for those

---

## Run Results

After the first manual run, record:

- **Run ID:**
- **Run status:**
- **Failing node (if any):**
- **Failing node error message (from Job Progress Details):**
- **Row count of registered dataset:**
- **Slowest node and its duration:**
- **Total run time:**

---

## Notes

Record any deviations from the standard pattern and why. For example:
- Why a Filter was placed after Augment (only if there was no pre-join filter option)
- Why the pipeline was split into two chained dataflows
- Any sfdcRegister alias decisions and downstream dashboards that depend on the alias
