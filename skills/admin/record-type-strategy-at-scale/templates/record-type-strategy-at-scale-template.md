# Record Type Strategy At Scale — Work Template

Use this template when rationalizing record types, planning a Dynamic Forms migration, or auditing layout assignment sprawl.

## Scope

**Skill:** `record-type-strategy-at-scale`

**Request summary:** (fill in what the user asked for)

**Target objects:** (list the objects under review)

## Context Gathered

Complete these before proposing any changes:

- **Total profile count in org:**
- **Dynamic Forms enabled:** Yes / No
- **Objects compatible with Dynamic Forms:** (list confirmed compatible objects)

### Per-Object Inventory

| Object | Record Type Count | Layout Assignment Count (RT x Profiles) | Business Processes Used |
|---|---|---|---|
| | | | |
| | | | |
| | | | |

## Record Type Classification

For each record type on the target objects, classify the differentiation axis:

| Object | Record Type DeveloperName | Differentiation Axis | Consolidation Candidate? |
|---|---|---|---|
| | | Field visibility only / Picklist values / Business process / Combination | Yes / No |
| | | | |
| | | | |

## Target State Design

**Record types to keep:** (list with justification)

**Record types to consolidate:** (list with target record type)

**Dynamic Forms rules needed:** (describe visibility rules replacing retired record types)

## Migration Plan

1. [ ] Export current RecordType metadata for target objects
2. [ ] Run SOQL to count records per record type being retired
3. [ ] Prepare Bulk API job to update RecordTypeId on affected records
4. [ ] Test migration in sandbox — verify automation still fires correctly
5. [ ] Update profile layout assignments to remove retired record types
6. [ ] Build Dynamic Forms pages with visibility rules for consolidated record types
7. [ ] Deploy metadata changes (RecordType + Profile XML together)
8. [ ] Delete retired record types after confirming zero records remain on them

## Review Checklist

- [ ] No Apex code or Flow references hardcode Record Type IDs
- [ ] Layout assignment count has been recalculated and is reduced
- [ ] Dynamic Forms compatibility verified for all target objects
- [ ] Picklist value overrides align with business process requirements
- [ ] Data migration tested in sandbox with rollback plan documented
- [ ] Profile layout assignment matrix updated to remove retired record types
- [ ] Reports and list views filtering by record type reviewed for impact

## Notes

Record any deviations from the standard pattern and why.
