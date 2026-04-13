# Analytics Recipe Design — Work Template

Use this template when designing or building a CRM Analytics Data Prep recipe.

## Scope

**Skill:** `analytics-recipe-design`

**Request summary:** (fill in what the user asked for — e.g., "Build a recipe to enrich Opportunity data with Account segment information and schedule it nightly")

---

## Context Gathered

Record answers to the Before Starting questions from SKILL.md before touching the canvas.

| Question | Answer |
|---|---|
| CRM Analytics license confirmed? | [ ] Yes / [ ] No — permission set: |
| Source datasets (names + object origins) | |
| Output dataset name | |
| Join keys and cardinality | |
| Required output columns | |
| Aggregation logic needed? | [ ] Yes / [ ] No — describe: |
| Refresh schedule required? | [ ] Yes / [ ] No — cadence: |
| Input dataset row count estimate | |
| Row-level security predicate needed? | [ ] Yes / [ ] No — predicate field: |

---

## Node Graph Design

Document the intended node sequence before opening the recipe canvas.

| Step | Node Type | Configuration Summary | Join Type (if Join) |
|---|---|---|---|
| 1 | Load | Dataset: | n/a |
| 2 | Load | Dataset: | n/a |
| 3 | Filter | Condition: | n/a |
| 4 | Join | Keys: | (Inner / LeftOuter / RightOuter / Outer / Lookup / MultiValueLookup) |
| 5 | Bucket | Source field: / Output column: | n/a |
| 6 | Formula | Output column: / Expression: | n/a |
| 7 | Aggregate | Group by: / Aggregations: | n/a |
| 8 | Output | Dataset name: | n/a |

Add or remove rows as needed. Every Join node row must have an explicit join type — do not leave blank.

---

## Join Type Rationale

For each Join node, document why that join type was chosen:

| Join Node | Join Type | Rationale |
|---|---|---|
| (e.g., Join 1 — Opps + Accounts) | Lookup | Must preserve all Opportunity rows; Account details are additive |
| | | |

---

## Bucket Node Configuration

For each Bucket node:

| Bucket Node | Source Field | Field Kind | Output Column | Bucket Labels and Ranges |
|---|---|---|---|---|
| | | Measure / Dimension / Date | | |

---

## Formula Node Expressions

For each Formula node (use recipe expression language, not SAQL):

| Formula Node | Output Column | Output Type | Expression |
|---|---|---|---|
| | | Text / Number / Date | |

---

## Schedule Configuration

If a recurring schedule is needed, record the Schedule Resource API call details:

```
POST /services/data/v62.0/wave/recipes/{recipeId}/schedules
Content-Type: application/json

{
  "scheduleType": "cron",
  "cronExpression": "_______________",
  "timeZone": "_______________"
}
```

Common cron patterns:
- Daily at 3 AM: `0 0 3 * * ?`
- Daily at midnight: `0 0 0 * * ?`
- Hourly: `0 0 * * * ?`
- Weekly Sunday 2 AM: `0 0 2 ? * SUN`

Note: The `recipeId` is retrieved from `GET /wave/recipes` — look for the `id` field on the recipe object.

---

## Checklist

Work through this before marking the recipe complete:

- [ ] Every Join node has an explicitly chosen and documented join type
- [ ] All enrichment joins (add columns, preserve all rows) use Lookup or LeftOuter — not Inner
- [ ] Bucket node types match the source field kind (Measure / Dimension / Date)
- [ ] Formula node expressions use recipe expression language (not SAQL)
- [ ] Recipe has been run at least once successfully
- [ ] Output dataset row count verified against input row count — no unexplained shrinkage
- [ ] All output columns confirmed correct in dataset schema view
- [ ] Bucket labels verified on sample rows
- [ ] Schedule configured via Schedule Resource API or Analytics Studio scheduling panel (not in recipe body)
- [ ] Security predicate applied to output dataset (if required)
- [ ] Recipe node names are descriptive (not "Node 1", "Join 2")

---

## Notes

Record any deviations from the standard pattern and why:

(e.g., "Used Inner join on Step 4 because the requirement explicitly states: only show Opportunities with a matched Account — this is intentional filtering, not enrichment.")
