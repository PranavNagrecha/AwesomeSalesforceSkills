# Apex Collections Patterns — Work Template

Fill this in as you work. Every heading maps to a step in `SKILL.md` §
Recommended Workflow.

## Scope

**Skill:** `apex-collections-patterns`

**Request summary:** _(what the user asked for, in one sentence)_

**Apex source root scanned:** _(e.g. `force-app/main/default/classes`)_

## Answers to the Seven Questions

| Question | Answer | Consequence |
|---|---|---|
| Access pattern — position, membership, or keyed lookup? | | Container choice |
| Where do the keys come from? | | `Id` vs `String` vs composite |
| Can any record be unsaved when the map is built? | | Constructor vs explicit loop |
| Is a custom class going to be a key or a Set element? | | `equals` + `hashCode` required? |
| Does anything downstream depend on order? | | `Comparator` required? |
| Will the collection be edited while iterated? | | Temporary collection needed? |
| Largest realistic volume in one transaction? | | Bulk-test record count |

## Container Decision

| Collection | Declared type | Access pattern it serves | Why not the alternative |
|---|---|---|---|
| | | | |

## Approach

**Pattern from SKILL.md § Common Patterns:** _(Map<Id, List<SObject>> grouping /
safe Set intersection / composite key class / AggregateResult)_

**Canonical files reused rather than rewritten:** _(e.g.
`templates/apex/TriggerHandler.cls`, `references/code-examples.md` §1)_

**Deviations from the canonical shape, and why:**

## Checker Run

```
python3 skills/apex/apex-collections-patterns/scripts/check_apex_collections_patterns.py \
    --manifest-dir <apex source root> --strict
```

| Severity | Finding | Fixed / accepted (reason) |
|---|---|---|
| | | |

## Test Evidence

- [ ] Grouping asserted on counts per key, not just map size
- [ ] Sort order asserted across every key, including the null case
- [ ] Key equality asserted (two equal keys collapse to one entry)
- [ ] Id-vs-String behaviour asserted where record Ids cross a boundary
- [ ] 200-record bulk case, heap read inside `Test.startTest()` / `Test.stopTest()`

**`sf apex run test` result:**

## Review Checklist

Copy the checklist from `SKILL.md` § Review Checklist and tick each item.

## Notes

_(Anything a future reviewer needs: rejected alternatives, volumes assumed,
UNVERIFIED behaviour you had to test in a scratch org.)_
