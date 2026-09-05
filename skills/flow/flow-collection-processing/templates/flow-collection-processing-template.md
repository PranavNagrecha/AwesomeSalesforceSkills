# Flow Collection Processing — Work Template

Use this template when designing or reviewing collection-processing logic in a Salesforce Flow.

---

## Scope

**Flow Name:** (fill in the flow API name)

**Flow Type:** Record-Triggered / Autolaunched / Screen Flow / Scheduled

**Request summary:** (describe what the collection operation must accomplish)

---

## Context Gathered

Answer the Before Starting questions from SKILL.md before proceeding:

- **Source collection SObject type:**
- **Collection size estimate (typical / max):**
- **Operation needed:** [ ] Filter  [ ] Sort  [ ] Transform  [ ] Accumulate/Mutate  [ ] DML
- **Target SObject type (if Transform):**
- **Called from bulk context (record-triggered, data load)?** Yes / No

---

## Element Selection

Use this table to select the correct element:

| Operation | Element to Use | `collectionProcessorType` / `transformType` | Floor |
|---|---|---|---|
| Reduce collection to a subset by condition | Collection Filter | `FilterCollectionProcessor` | API 53.0 |
| Reorder a collection | Collection Sort | `SortCollectionProcessor` + `sortOptions` | API 50.0 / 51.0 |
| Take the top N | Collection Sort | the same, plus `limit` (sort applies first) | API 51.0 |
| One output record per input, copies and literals only | Map processor | `RecommendationMapCollectionProcessor` | API 53.0 |
| One output record per input, some value computed | Transform | `transformType` `Map` + `formulaExpression` | API 59.0 |
| Collapse a collection to one number | Transform | `transformType` `Sum` or `Count` | API 59.0 / 60.0 |
| Join two collections | Transform | `transformType` `InnerJoin` | API 63.0 |
| Set difference / intersection | Assignment | `RemoveAll` / `RemoveUncommon` | API 43.0 |
| Append one record to a collection | Assignment | `Add` (never `AddItem`) | — |
| Count a collection | Assignment | `AssignCount` into a Number variable | API 43.0 |
| Set the same field value on every record | Map processor | `outputSObjectType` = input type, map `Id` + the field | API 53.0 |
| Apply per-record conditional logic | Loop with Decision inside | — | API 30.0 |
| Write all records in one DML call | Update/Create/Delete Records on a collection | — | — |

**Chosen `<apiVersion>` for this flow (max of the floors above):** ______

**Selected element(s):**

---

## Loop Design (if Loop is required)

| Step | Element | Action |
|---|---|---|
| 1 | Loop | Source: `{!sourceCollection}`, Current Item: `{!currentItem}` |
| 2 | Assignment | Modify `{!currentItem}` field(s) as needed |
| 3 | Assignment | Add `{!currentItem}` to `{!outputCollection}` using Add operator |
| 4 | (Decision) | Optional: branch on per-record condition before step 2/3 |
| After Last | DML Element | Reference `{!outputCollection}` — single DML call |

---

## Collection Filter Configuration (if Filter is required)

| Field | Filter conditions applied |
|---|---|
| Source Collection | `{!sourceCollection}` — SObject type: __________ |
| Condition logic | AND / OR |
| Condition 1 | Field __ Operator __ Value __ |
| Condition 2 | Field __ Operator __ Value __ |
| Output Collection | `{!filteredCollection}` |

---

## Transform Field Mapping (if Transform is required)

| Target Field | Source |
|---|---|
| (target SObject field) | Source field or literal value |
| | |
| | |

Note: a **Map processor** (`RecommendationMapCollectionProcessor`) takes copies and literals only.
A **Transform** (`FlowTransform`, API 59.0+) additionally takes `value/formulaExpression` paired with
`formulaDataType` (`api_meta.txt` L70464–L70482). If any row in this table is a formula, the element
is a Transform, not a Map processor. Record which.

---

## DML Commit Plan

| DML Element | Input | Placement |
|---|---|---|
| Update Records | `{!outputCollection}` | After "After Last" exit of Loop, or after Filter/Transform |
| Create Records | `{!newRecordCollection}` | After Transform or loop accumulation |

DML elements must NOT be placed inside a Loop.

---

## Checklist

Copy from SKILL.md review checklist and tick each item:

- [ ] No DML element inside a Loop
- [ ] No Loop body consisting only of Assignments and Decisions (checker **W2**)
- [ ] Every `collectionProcessorType` is one of the three documented values (checker **E1**)
- [ ] Every Sort carrying `limit` also carries `sortOptions` (checker **E2**)
- [ ] Every Map processor names `assignNextValueToReference` and `outputSObjectType` (checker **E3**)
- [ ] Every `transformType` is documented, and no reserved field is written (checker **E4**)
- [ ] Every `AssignCount` target is a non-collection Number variable (checker **E5**)
- [ ] No `AddItem` against anything but a Multipicklist variable (checker **E6**)
- [ ] No processor carries both `formula` and `conditions` (checker **W1**)
- [ ] Every collection variable's `dataType` / `isCollection` / `objectType` is declared
- [ ] Fault paths hang off the Get Records and the DML, not off any processor
- [ ] The chain terminates in an `AssignCount` that a `FlowTest` asserts on
- [ ] `python3 scripts/check_flow_collection_processing.py --manifest-dir <src> --strict` is clean

---

## Version Floors And Unverified Shapes

| Item | Value | Source |
|---|---|---|
| Flow `<apiVersion>` | | max of the element floors above |
| `package.xml` `<version>` | | 66.0 if the FlowTest uses `flowTestDataSources` or `testType` |
| Shapes confirmed by round-trip retrieve | | `sf project retrieve start --metadata Flow:<name>` |

The Metadata API guide ships **no sample XML** for `FlowCollectionProcessor` or
`FlowCollectionMapItem`. Every shape marked `UNVERIFIED (2026-09-05)` in
`references/metadata-examples.md` has to be confirmed against a Builder-authored element in your own
org. List which ones you confirmed, and in which org.

---

## Notes

Record any deviations from the standard pattern and the reason for them — in particular any
Metadata-API-only construct (a collection as the `value` of an `Add`), which must also be stated in
the flow's own `<description>` so the next admin does not destroy it by opening it in Builder.
