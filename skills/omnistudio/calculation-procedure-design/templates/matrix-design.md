# Calculation Matrix Design

Field names below are the API names on `CalculationMatrix`,
`CalculationMatrixVersion`, and `CalculationMatrixColumn`. Fill this in before
opening the designer.

## Matrix

- Name (`CalculationMatrix.Name`):
- `MatrixType`: [ ] Standard  [ ] Grouped
  - If Grouped — `GroupKey`: ______  `SubGroupKey`: ______
  - Justification: the same rate structure repeats per partition, and each
    partition changes on its own schedule. (If a row could sensibly wildcard on
    that dimension, it is an **input column**, not a group key.)

## Version

- `VersionNumber`:
- `StartDateTime` (ISO 8601):
- `EndDateTime` (ISO 8601, or null for open-ended):
- `Rank`: ______ (use gaps — 10, 20, 30 — so a correction can slot between)
- `IsEnabled`: [ ] not yet — enable only after the load check below
- Is this a **planned change** (non-overlapping dates) or a **correction**
  (same `StartDateTime`, higher `Rank` than the version it supersedes)?

> Reminder: `CalculationMatrixVersion` uses **`IsEnabled`**.
> `ExpressionSetVersion` uses **`IsActive`**. Neither has a `Status` field.

## Columns

`DataType` must be one of: `Boolean`, `Currency`, `Number`, `NumberRange`,
`Percent`, `Text`, `TextRange`.

| Name | `ColumnType` | `DataType` | `DisplaySequence` | `IsWildcardColumn` | `WildcardColumnValue` | `RangeValues` |
|---|---|---|---|---|---|---|
|  | Input/Output |  |  | true/false |  |  |

Column checks:

- [ ] Every banded dimension uses `NumberRange` or `TextRange` with declared
      `RangeValues` — **not** a Min/Max column pair
- [ ] Every column that carries a fallback token has `IsWildcardColumn = true`
      **and** a set `WildcardColumnValue`
- [ ] Rows use the configured `WildcardColumnValue` token exactly — `*` is a
      literal string here and will never match
- [ ] Wildcard opt-in is deliberate per column (permitting a wildcard on
      `Region` while requiring an exact `ProductTier` is usually what the
      business meant)

<!-- The object reference does not state RangeValues' delimiter or whether a
boundary belongs to the band above or below it. Confirm against a live matrix
before relying on behaviour exactly at a boundary value. -->

## Rows

Paste the table here, or link to the CSV source of truth (preferred — keep the
CSV and the fixture JSON in the same directory so they move together).

- Source CSV path:
- Data-row count in source:

## Load Verification

- `LoadProcessStatus` after upload: ______
  (`Completed` | `CompletedWithErrors` | `Failed` | `InProgress` | `Pending`)
- [ ] Status is **exactly** `Completed` — not merely "not Failed".
      `CompletedWithErrors` is a partial load reported as success.
- `CalculationMatrixRow` count for this version: ______
- [ ] Row count equals the source CSV data-row count

```sql
SELECT Id, Name, VersionNumber, LoadProcessStatus, IsEnabled,
       StartDateTime, EndDateTime, Rank, MatrixType
FROM   CalculationMatrixVersion
WHERE  CalculationMatrixId = :matrixId
ORDER  BY Rank DESC, VersionNumber DESC
```

## Fallback Behaviour

- [ ] Wildcard row present (record which columns wildcard, and to what token)
- [ ] Explicit raise in a following procedure step

Choose by blast radius: a wrong price is worse than a blocked quote in a
regulated line, and better than one in self-service.

## Consuming Procedure

- `ExpressionSet` name:
- `ExpressionSetVersion.VersionNumber`:
- `DecimalScale`: ______ (part of the version contract — a penny difference
  between environments is usually this field)
- `ExpressionSet.ExecutionScale`: [ ] High  [ ] Low
- Callers pass `options.effectiveDate`? [ ] yes  [ ] no — if any path is
  back-dated, this must be yes on **every** path

## Activation Order

Leaves before roots. Nothing auto-activates what it references.

1. [ ] Referenced matrices enabled
2. [ ] Sub-expression-sets activated
3. [ ] Parent procedure activated
4. [ ] Verified by query, not by the designer's green state

## Fixtures

Path (source control, next to the CSV):

- [ ] One case per band boundary (both sides)
- [ ] One case that must hit the wildcard
- [ ] One single-element collection input for every aggregation step
- [ ] Expected values recorded with the `DecimalScale` they were produced at

## Review Checklist

- [ ] Ranges declared as range columns, not Min/Max pairs
- [ ] Wildcard columns opted in with an explicit token
- [ ] `Rank` distinct and gapped; no two enabled versions tied in one window
- [ ] `LoadProcessStatus = 'Completed'` and row count matches source
- [ ] Correction shipped as a new higher-`Rank` version, not an in-place edit
- [ ] Activation order leaves-first, verified by query
- [ ] Fixtures run after activation and diffed against source control
