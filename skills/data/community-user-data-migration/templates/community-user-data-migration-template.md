# Community User Data Migration — Runbook Template

Use this template to plan and execute a community/portal user migration into Salesforce Experience Cloud.

---

## Migration Overview

| Field | Value |
|---|---|
| **Migration type** | [ ] Net-new user insert [ ] License type migration [ ] Portal consolidation |
| **Source system** | (name of source portal or org) |
| **Destination org** | (org name / environment) |
| **Target Experience Cloud site** | (site name) |
| **Target profile name** | (profile to assign migrated users) |
| **Source license type** | (e.g., Customer Community, Customer Portal) |
| **Destination license type** | (e.g., Customer Community Plus, Partner Community) |
| **Estimated user count** | |
| **Migration window start** | YYYY-MM-DD HH:MM (timezone) |
| **Migration window end** | YYYY-MM-DD HH:MM (timezone) |
| **Runbook author** | |
| **Last updated** | YYYY-MM-DD |

---

## Pre-Flight Checklist

Complete all items before the migration window opens.

### Contact/Account Hierarchy

- [ ] Source user export obtained with external identifier field populated
- [ ] Contact pre-staging CSV built and validated (External ID field: `____________`)
- [ ] Contact upsert job executed in destination org
- [ ] Contact upsert success row count: ________ (must match source row count)
- [ ] SOQL validation run: all source external IDs resolve to a Contact Id in destination org

```sql
-- Validation query: paste ContactId lookup results here
SELECT Id, <External_ID_Field>__c FROM Contact
WHERE <External_ID_Field>__c IN ( /* source IDs */ )
```

### Profile and Network Association

- [ ] Destination Profile name confirmed: `________________________`
- [ ] Profile verified as associated with target network in Setup > Digital Experiences > [Site] > Administration > Members
- [ ] SOQL confirmation run:

```sql
SELECT Id, Name FROM Profile
WHERE Id IN (
  SELECT ProfileId FROM NetworkMember WHERE NetworkId = '<TARGET_NETWORK_ID>'
)
AND Name = '<TARGET_PROFILE_NAME>'
```

Result rows: ________ (must be 1)

### License Seat Availability

- [ ] Available license seats confirmed in Setup > Company Information
- [ ] Available seats: ________ | Users to migrate: ________ | Buffer: ________
- [ ] If in-org migration: deactivation-to-activation buffer planned (minimum 1 business day)

### Migration CSV Validation

- [ ] User migration CSV built with all required columns:
  - `ContactId`, `ProfileId`, `UserType`, `Username`, `Email`, `FirstName`, `LastName`
  - `Alias`, `TimeZoneSidKey`, `LocaleSidKey`, `EmailEncodingKey`, `LanguageLocaleKey`, `IsActive`
- [ ] CSV checker run: `python3 scripts/check_community_user_data_migration.py --csv users.csv --operation insert`
- [ ] No duplicate Usernames in CSV
- [ ] No sandbox username suffixes in CSV
- [ ] UserType value matches destination license:

| License | UserType Value |
|---|---|
| Customer Community | `PowerCustomerSuccess` |
| Customer Community Plus | `PowerCustomerSuccessPortal` |
| Partner Community | `PowerPartner` |

---

## Migration Execution

### Step 1: Contact Pre-Staging (if not already complete)

- [ ] Data Loader operation: **upsert** using External ID field `______________`
- [ ] Success count: ________ | Error count: ________
- [ ] Error log reviewed: all errors resolved

### Step 2: User Insert / Update

- [ ] Data Loader operation: **insert** (new users) / **update** (Profile change only)
- [ ] Batch size: ________ (recommended: 200 rows per job for manageability)
- [ ] Success CSV saved to: `________________________`
- [ ] Error CSV saved to: `________________________`
- [ ] Success count: ________ | Error count: ________
- [ ] Error log reviewed — no unresolved `INVALID_CROSS_REFERENCE_KEY` errors

### Step 3: NetworkMember Verification

- [ ] NetworkMember records confirmed on destination network:

```sql
SELECT Id, MemberId, NetworkId, Network.Name
FROM NetworkMember
WHERE MemberId IN (
  SELECT Id FROM User WHERE Profile.Name = '<TARGET_PROFILE>'
  AND LastModifiedDate = TODAY
)
```

NetworkMember count: ________ (must match success count from Step 2)

### Step 4: Stale NetworkMember Cleanup (license migration only)

- [ ] Stale NetworkMember records identified on old network:

```sql
SELECT Id, MemberId
FROM NetworkMember
WHERE NetworkId = '<OLD_NETWORK_ID>'
AND MemberId IN (
  SELECT Id FROM User WHERE Profile.Name = '<TARGET_PROFILE>'
)
```

Stale record count: ________

- [ ] Stale records deleted via Data Loader delete
- [ ] Post-delete verification: above query returns 0 rows

---

## Post-Migration Validation

### User Count Check

```sql
SELECT COUNT() FROM User
WHERE Profile.Name = '<TARGET_PROFILE>'
AND IsActive = true
```

Count: ________ (must match expected migrated user count)

### Smoke Test

- [ ] Test user selected: `________________________` (username)
- [ ] Test user can log in to destination Experience Cloud site
- [ ] Test user can view expected records (validate sharing)
- [ ] Test user cannot access records outside their permission scope

### Source User Deactivation (in-org migration)

- [ ] Source user cohort exported from success.csv
- [ ] IsActive set to `false` on source users via Data Loader update
- [ ] Deactivation success count: ________
- [ ] License seat recalculation buffer planned: ________ (date to confirm freed seats)

---

## Rollback Plan

If the migration must be rolled back within the maintenance window:

1. If User insert was the last operation:
   - Use success.csv to build a Data Loader delete file
   - Delete inserted Users (this deactivates + deletes if within the same session; note: User records with activity may not be hard-deletable — set IsActive = false instead)

2. If Profile update was the last operation:
   - Revert ProfileId to original profile using original ProfileId values
   - Delete newly created NetworkMember records on destination network
   - Confirm original NetworkMember records are intact on source network

3. Notify stakeholders and document rollback reason.

---

## Notes and Deviations

Record any deviations from this standard runbook and the reason for each deviation.

| Step | Deviation | Reason |
|---|---|---|
| | | |
