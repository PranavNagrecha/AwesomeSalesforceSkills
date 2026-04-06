# Territory Data Alignment — Work Template

Use this template when working on tasks involving account-to-territory or user-to-territory data in an ETM org.

## Scope

**Skill:** `territory-data-alignment`

**Request summary:** (fill in what the user asked for)

**Operation type:** (select one)
- [ ] Coverage gap analysis / audit
- [ ] Bulk insert of new account-territory associations
- [ ] Cleanup of stale associations (manual or duplicate)
- [ ] Model migration — copying associations to a new territory model
- [ ] User-territory membership update
- [ ] Other: ___

## Context Gathered

Answer these before starting work:

- **Active Territory2Model ID/Name:**
- **Territory2Model State confirmed as Active:** Yes / No
- **Track Territory Assignment History enabled:** Yes / No / Unknown
- **AssociationCause for new inserts:** Manual / Territory (rule-driven — not inserted via API)
- **Account population size (estimated row count):** ___
- **Bulk API 2.0 required (>50K rows or subquery risk):** Yes / No

## Pre-Operation Baseline

Run these queries and record the results before making any changes:

```soql
-- Total active associations per territory (baseline)
SELECT Territory2.Name, AssociationCause, COUNT(Id) total
FROM ObjectTerritory2Association
WHERE Territory2.Territory2Model.State = 'Active'
GROUP BY Territory2.Name, AssociationCause
ORDER BY Territory2.Name ASC
```

**Baseline total associations:** ___
**Baseline coverage gap count (accounts with no association):** ___

## Data Payload

For insert operations, document the source and deduplication approach:

- **Source of insert data:** (export, spreadsheet, SOQL query, migration mapping)
- **Deduplication method:** (pre-query + set difference / other)
- **Row count before dedup:** ___
- **Row count after dedup (net-new rows):** ___
- **CSV columns:** `ObjectId`, `Territory2Id`, `AssociationCause`

For migration operations, document the model mapping:

| Old Territory DeveloperName | Old Territory2Id | New Territory DeveloperName | New Territory2Id |
|---|---|---|---|
| (fill in) | (fill in) | (fill in) | (fill in) |

## Execution Log

| Step | Action | Status | Notes |
|---|---|---|---|
| 1 | Active model confirmed | | |
| 2 | Baseline queries run | | |
| 3 | Payload prepared and deduplicated | | |
| 4 | Bulk API / Data Loader job submitted | | |
| 5 | Job completed — record counts verified | | |
| 6 | Post-operation coverage query run | | |

**Bulk API Job ID (if applicable):** ___
**Failed records count:** ___
**Failed records log reviewed:** Yes / No

## Post-Operation Verification

```soql
-- Post-operation coverage gap check (should be smaller than baseline)
SELECT COUNT(Id) gap_count
FROM Account
WHERE IsDeleted = false
  AND Id NOT IN (
    SELECT ObjectId
    FROM ObjectTerritory2Association
    WHERE Territory2.Territory2Model.State = 'Active'
  )
```

**Post-operation gap count:** ___
**Delta (gap reduced by):** ___

## Checklist

- [ ] Active territory model confirmed before any write operation
- [ ] `AssociationCause` correctly set for all inserted rows
- [ ] Deduplication completed before bulk insert
- [ ] Coverage gap analysis run before and after operation
- [ ] `AssociationCause` breakdown verified — ratio of rule vs. manual is expected
- [ ] For model migrations: Territory2Id mapping validated using DeveloperName as the stable key
- [ ] Stale UserTerritory2Association rows for inactive users addressed if in scope
- [ ] Bulk API job completed with zero or acceptable failed records
- [ ] Failed record log reviewed and actioned
- [ ] Manual association rationale documented

## Notes and Deviations

(Record any deviations from the standard pattern, edge cases encountered, or decisions made during execution.)
