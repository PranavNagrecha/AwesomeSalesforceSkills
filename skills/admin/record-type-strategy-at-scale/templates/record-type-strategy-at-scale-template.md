# Record Type Strategy At Scale — Work Template

Use this template when rationalizing record types, planning a Dynamic Forms migration, or auditing layout assignment sprawl.

## Scope

**Skill:** `record-type-strategy-at-scale`

**Request summary:** (fill in what the user asked for)

**Target objects:** (list the objects under review)

## Context Gathered

Complete these before proposing any changes:

- **Total profile count in org (M):**
- **Personas, and which take record type access from a permission set group rather than a profile:**
- **Dynamic Forms enabled:** Yes / No
- **Objects compatible with Dynamic Forms:** (confirm in Lightning App Builder for THIS org)
- **Record type inventory source:** generated from `SELECT SobjectType, DeveloperName, IsActive FROM RecordType` / hand-written (hand-written is a defect — `RecordType` takes no `*` wildcard)

### Per-Object Inventory

| Object | Active Record Type Count | Layout Assignment Count (RT x M, + 1 fallback per profile) | Business Processes Used | Count-guide band (1-4 / 5-8 / 9-12 / 13+) |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |

## Record Type Classification

For each record type on the target objects, classify the differentiation axis:

| Object | Record Type DeveloperName | Differentiation Axis | Consolidation Candidate? |
|---|---|---|---|
| | | Field visibility only / Picklist values / Business process / Combination | Yes / No |
| | | | |
| | | | |

## Target Assignment Matrix

One row per (object, record type, persona). Include the fallback row with no record type. `default` may only be `true` on a profile — a permission-set-carried cell reads `n/a`, never `false`.

| Object | Record Type | Persona | Grant carrier (Profile / PSet name) | `visible` | `default` | Layout |
|---|---|---|---|---|---|---|
| | | | | | | |
| | | | | | | |
| | *(no record type)* | | Profile | — | — | *(fallback)* |

- [ ] Exactly one `default = true` per (object, persona), and it is on a Profile
- [ ] Every active record type appears with `visible = true` for at least one persona
- [ ] Every active record type has a layout in at least one Profile row
- [ ] The fallback row is present for every (object, profile)

## Target State Design

**Record types to keep:** (list with justification)

**Record types to consolidate:** (list with target record type)

**Dynamic Forms rules needed:** (describe visibility rules replacing retired record types)

## Migration Plan

Three deploys, with the data migration alone in the middle.

**Deploy A — additive, reversible**
1. [ ] Retrieve objects, layouts, record types, profiles, and permission sets in ONE manifest
2. [ ] Commit the pre-change visibility snapshot (it stops being retrievable once anything is deactivated)
3. [ ] Merge the layouts into the surviving layout
4. [ ] Union the picklist values onto the surviving record type
5. [ ] Build any FlexiPage replacing a retired record type
6. [ ] Deploy A

**Migration — no metadata moves**
7. [ ] Count records per retiring RecordTypeId
8. [ ] List rows whose picklist values are absent from the union (these blank on reassignment)
9. [ ] Inventory validation rules, before-save flows, duplicate rules, assignment rules that will fire per row
10. [ ] Sandbox sample run; read `failedResults`, not just the success count
11. [ ] Production Bulk API 2.0 `update` of `RecordTypeId`
12. [ ] Confirm zero records remain on the retiring record types

**Deploy B — retirement**
13. [ ] Set `active` to `false` on the retired record types
14. [ ] Prune their `recordTypeVisibilities` and `layoutAssignments` rows — keeping the fallback row
15. [ ] Deploy B as a single package
16. [ ] Run the checker and the per-persona describe audit

## Review Checklist

- [ ] No Apex code or Flow references hardcode Record Type IDs
- [ ] Layout assignment count has been recalculated and is reduced
- [ ] Dynamic Forms compatibility verified for all target objects
- [ ] Picklist value overrides align with business process requirements
- [ ] Data migration tested in sandbox with rollback plan documented
- [ ] Profile layout assignment matrix updated to remove retired record types
- [ ] Reports and list views filtering by record type reviewed for impact
- [ ] `check_record_type_strategy_at_scale.py` run against the retrieved tree; zero ERRORs
- [ ] Per-persona describe audit run: one `isDefaultRecordTypeMapping()` each, and it is not the Master row

## Notes

Record any deviations from the standard pattern and why.
