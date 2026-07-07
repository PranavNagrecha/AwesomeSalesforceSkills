# Agentforce Grid — Worksheet Planning Template

Use this template to scope an Agentforce Grid run **before** building the worksheet, then
capture the column plan as a JSON spec (see `grid-worksheet-spec.example.json`) and lint it with
`scripts/check_agentforce_grid.py`.

> Grid is **Beta** (introduced Winter '26) and metered in every lifecycle phase. Every planning
> decision below is also a cost decision: cost ≈ rows × (AI + action columns).

## Scope

**Skill:** `agentforce-grid`

**Request summary:** (what the user asked for)

**Goal (pick one):** bulk-update · insight-generation · multi-turn-test

## Before Starting

- **Is this genuinely bulk?** (rows = jobs; a single record does not belong in Grid): 
- **Data source & object:** standard Salesforce object / Data Cloud (Data 360) DMO — which one? 
- **Row filter & Max Results (bounds job count and cost):** 
- **Estimated rows × AI/action columns → Flex Credit estimate reviewed?** (yes/no): 
- **Does the operating user's CRUD/FLS/sharing cover every field read and written?** 

## Column Plan (left to right)

| # | Column name | Type (data/ai/action) | Details | References (must be to the LEFT) |
|---|---|---|---|---|
| 1 |  | data | object / source / fields / filter / maxResults |  |
| 2 |  | ai | mode (prompt-template → template · use-ai → model) + instruction |  |
| 3 |  | action | update-record → object + field (omit for read-only insight runs) |  |

## Review Checklist

- [ ] Task is genuinely bulk (multiple rows)
- [ ] Leftmost column is a data column with a filter and Max Results
- [ ] Every reference points to a column to its left (no forward/unknown references)
- [ ] AI columns declare a mode (template or model)
- [ ] Read-only runs have NO update-record column; write-backs map to the correct object/field
- [ ] Flex Credit / Billing Calculator estimate reviewed for the real row count
- [ ] Previewed a few rows before the full run
- [ ] Beta caveat preserved; no GA claims

## Notes

(Deviations from the standard Data → AI → Action pattern and why.)
