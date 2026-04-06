# Cross-Object Formula and Rollup Performance — Work Template

Use this template when auditing or remediating cross-object formula spanning limits and rollup summary performance.

## Scope

**Skill:** `cross-object-formula-and-rollup-performance`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- Target object(s):
- Current spanning relationship count: ___ / 15
- Rollup summary fields on the object:
- Maximum child record count per parent:
- Triggers or flows that read rollup values in same transaction: Yes / No
- Rollup filter criteria present: Yes / No
- Filter references cross-object formula on child: Yes / No

## Spanning Relationship Inventory

| # | Relationship Path | Source Metadata Type | Source Name |
|---|---|---|---|
| 1 | | | |
| 2 | | | |

**Total unique spanning relationships:** ___ / 15

## Rollup Timing Analysis

| Rollup Field | Parent Object | Read By (Trigger/Flow) | Same Transaction? | Stale Risk? |
|---|---|---|---|---|
| | | | | |

## Recommendation

(Which pattern from SKILL.md applies and why)

## Checklist

- [ ] Total spanning relationships on the object are at or below 12
- [ ] No trigger or synchronous flow reads a rollup value in the same transaction as child DML
- [ ] Rollup filter criteria reference only indexed fields or rollup is Apex-managed
- [ ] Child record volume per parent is under 200k for native rollups
- [ ] Incremental Apex rollups use FOR UPDATE on parent query
- [ ] Test classes include bulk inserts (200+ children) to verify accuracy

## Notes

(Record any deviations from the standard pattern and why)
