# Deployment Data Dependencies — Checklist Template

Use this template when planning a cross-org data migration or post-deployment data seeding step.

---

## Scope

**Target environment:** _______________
**Source environment:** _______________
**Migration type:** [ ] Full data migration  [ ] Reference data seeding  [ ] Post-deployment data fix

---

## Org-Specific ID Audit

Review each object in the migration scope and mark any ID references that require resolution:

| Object | Field | ID Type | Resolution Method |
|---|---|---|---|
| Account | RecordTypeId | RecordType ID | RecordType.DeveloperName lookup |
| Case | OwnerId (Queue) | Group ID | GROUP BY Type='Queue', Name lookup |
| ___ | ___ | Custom Setting | Data load (not metadata) |
| ___ | ___ | User ID | Username lookup |

---

## Custom Settings Checklist

- [ ] Identified all Custom Setting objects used by deployed code
- [ ] Exported Custom Setting records from source org (CSV or SOQL)
- [ ] Data load step added to deployment runbook (after metadata deploy)
- [ ] Values verified in target org post-load

---

## RecordType Resolution Checklist

- [ ] No hardcoded RecordType IDs in data files (use DeveloperName column)
- [ ] Apex scripts use `getRecordTypeInfosByDeveloperName()` for all RecordType references
- [ ] SFDMU config uses `RecordType.DeveloperName` mapping where applicable

---

## Queue and User Reference Checklist

- [ ] No hardcoded Queue IDs in Flow or Apex (resolve by Name at runtime)
- [ ] No hardcoded User IDs in data files (resolve by Username or Email)
- [ ] Queues and Users confirmed to exist in target org before data load

---

## Deployment Runbook Steps

1. Deploy metadata package
2. Load Custom Setting data records
3. Load reference / configuration data (RecordTypes resolved by DeveloperName)
4. Load transactional data (Queues and Users resolved by Name/Username)
5. Run post-load validation queries
6. Confirm no INVALID_CROSS_REFERENCE_KEY errors in load results

---

## Validation Queries

Document SOQL queries to confirm data loaded correctly: _______________
