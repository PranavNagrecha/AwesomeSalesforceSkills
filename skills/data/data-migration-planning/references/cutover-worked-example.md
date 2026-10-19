# Worked Example — Cutover Runbook and Troubleshooting Table

## Migration folder the checker reads

```text
migration/
├── migration_sequence.csv
├── Account.csv
├── Contact.csv
├── Opportunity.csv
├── OpportunityLineItem.csv
└── objects/            (retrieved target metadata: fields, validationRules)
```

```csv
object,depends_on,bypass_documented
User,,yes
Account,User,yes
Contact,Account,yes
Product2,,yes
PricebookEntry,Product2,yes
Opportunity,Account,yes
OpportunityLineItem,"Opportunity,PricebookEntry",yes
```

`python3 skills/data/data-migration-planning/scripts/check_data_migration_planning.py --manifest-dir migration` must report no ERROR before the rehearsal.

## Cutover runbook (production)

| Step | Action | Owner | Evidence |
|---|---|---|---|
| T-7d | Deploy External ID fields, `Migration_Batch_Id__c`, bypass custom permission and permission set | Release manager | Deployment ID |
| T-7d | Enable "Set Audit Fields upon Record Creation" (if audit values are kept); grant to the migration user | Admin | Setup screenshot |
| T-1d | Set Public Read/Write defaults or enable defer sharing calculation for the load; freeze sharing-rule changes | Admin | Sharing settings export |
| T-0 | Assign bypass permission set to the migration user only | Admin | Assignment record |
| T-0 | Load in sequence order; children sorted by parent key; one batch ID per object per run | Data lead | Job IDs per object |
| T-0 | After each object: source count = successful + failed; no unexplained failed rows | Data lead | Reconciliation sheet |
| T+0 | Remove the bypass permission set; restore sharing defaults; let sharing recalculation finish | Admin | Assignment removed, settings export |
| T+0 | Save one test record per object as a normal user; confirm validation rules and automation fire | QA | Test log |
| T+1d | Orphan checks (children with a source parent key but a blank lookup) and field samples | Data lead | Query results |

## Troubleshooting table

| Symptom | Likely cause | Fix |
|---|---|---|
| Duplicates after a re-run | Insert used instead of upsert, or the key column was blank | Upsert on the External ID; fill the key on every row |
| Upsert rows fail with a 300 error | The key value matches more than one existing record | Make the key Unique after de-duplicating; fix the source |
| Child rows fail to resolve their parent | Parent not loaded yet, wrong key value, or a parent field that isn't an External ID | Load parents first; reference only indexed parent fields; compare key values exactly |
| Master-detail child rows fail as required field missing | Blank parent column | Populate the parent key; route parentless rows to a catch-all parent or hold them out |
| Validation errors for the migration user | Bypass permission not assigned, or the rule lacks `NOT($Permission...)` | Assign the permission set; add the bypass to the rule |
| Emails or callouts fired during the load | Trigger or flow does not check the bypass | Add the check; rerun only after it is deployed |
| Lock errors on parent records | Children of the same parent spread across batches | Sort child files by parent key |
| Load much slower than expected | Ownership and sharing recalculation, dirty data forcing single-row processing, or Data Loader set to SOAP API | Defer sharing, clean the data, switch Data Loader to Bulk API 2.0 |
