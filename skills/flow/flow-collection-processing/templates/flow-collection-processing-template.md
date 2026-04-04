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

| Operation | Element to Use |
|---|---|
| Reduce collection to a subset by condition | Collection Filter |
| Reorder collection by a field | Collection Sort |
| Map fields from one SObject type to another | Transform |
| Modify fields on each record and keep all | Loop + Assignment (Add to output collection) |
| Apply per-record conditional logic | Loop with Decision inside |
| Write all records in one DML call | Update/Create/Delete Records on collection variable |

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

Note: Formula expressions are not supported in Transform mappings. Compute derived values in a separate Assignment before the Transform element.

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
- [ ] Collection Filter used instead of Loop-with-conditional-accumulation where applicable
- [ ] Collection Sort used instead of manual sorting Loop
- [ ] Transform used instead of Loop-based field remapping where applicable
- [ ] All collection variables have explicit SObject types set
- [ ] "After Last" Loop exit reaches the next intended element
- [ ] Tested with empty collection input
- [ ] DML elements reference collection variables, not single-record variables

---

## Notes

Record any deviations from the standard pattern and the reason for them.
