# Data Reconciliation Patterns — Work Template

Use this template when working on tasks in this domain.

## Scope

**Skill:** `data-reconciliation-patterns`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **External ID field:** (API name of the External ID field used as the upsert key, e.g., `ERP_Account_Id__c`)
- **Integration method:** (Bulk API 2.0 / REST API / middleware platform name)
- **Expected record count:** (total records expected in Salesforce for the relevant object)
- **Last successful sync timestamp:** (UTC datetime of the last clean sync, e.g., `2026-04-04T22:00:00Z`)
- **CDC enabled:** (yes/no — if yes, list the objects subscribed)
- **Known constraints:** (API call limits, sandbox vs production, object-specific restrictions)
- **Failure modes to watch for:** (validation rules that reject rows, duplicate rules, required fields missing in source)

## Approach

Select the applicable reconciliation level(s) from SKILL.md:

- [ ] Count-level reconciliation (fast, run first)
- [ ] Field-level hash reconciliation (run when counts match but values drift)
- [ ] Record-level full outer join (run when records exist in one system but not the other)
- [ ] CDC replay gap recovery (run when subscriber was offline)
- [ ] Tombstone sweep for hard deletes (run when delta load misses deletions)

**Why this approach:** (explain which pattern from SKILL.md applies and why)

## Checklist

Copy from SKILL.md Review Checklist and tick items as you complete them.

- [ ] External ID field has both Unique and External ID checkboxes checked on the object definition
- [ ] Bulk API 2.0 job `failedResults` endpoint has been checked and returns zero failed rows
- [ ] Count-level reconciliation passes (Salesforce count equals source system count within expected tolerance)
- [ ] Hard delete handling is addressed via CDC DELETE events or a queryAll tombstone sweep
- [ ] CDC subscriber stores `replayId` persistently and gap recovery has been tested
- [ ] SystemModstamp false positives from formula recalculations are accounted for in the delta load filter

## Notes

Record any deviations from the standard pattern and why.
