# Examples — Community User Data Migration

## Example 1: Bulk Migrating Customer Portal Users to Experience Cloud

**Context:** A company is retiring a legacy Salesforce Customer Portal and migrating all portal users into a new Experience Cloud Customer Community site. The destination org has Contacts pre-staged with an External ID field (`Legacy_Portal_ID__c`). There are approximately 8,000 portal users to migrate.

**Problem:** Without a clear field-mapping sequence, teams attempt to insert Users before Contacts are confirmed, resulting in mass `INVALID_CROSS_REFERENCE_KEY` failures. Alternatively, they omit required locale fields, causing partial inserts that are difficult to roll back.

**Solution:**

Step 1 — Confirm Contact pre-staging with a SOQL query:

```sql
SELECT Id, Legacy_Portal_ID__c
FROM Contact
WHERE Legacy_Portal_ID__c != null
ORDER BY Legacy_Portal_ID__c
```

Step 2 — Build the User insert CSV with all required fields. Minimum required columns:

```
ContactId,ProfileId,UserType,Username,Email,FirstName,LastName,Alias,
TimeZoneSidKey,LocaleSidKey,EmailEncodingKey,LanguageLocaleKey,IsActive
```

Step 3 — Map UserType to the correct value for Customer Community:

```
UserType: PowerCustomerSuccess
```

Step 4 — Insert via Data Loader. Capture `success.csv` and `error.csv`. On error, filter the error log for `INVALID_CROSS_REFERENCE_KEY` on ContactId — each such row means the Contact lookup failed. Re-map those rows and re-run.

Step 5 — Verify NetworkMember auto-creation for inserted users:

```sql
SELECT Id, MemberId, NetworkId, Network.Name
FROM NetworkMember
WHERE MemberId IN (
  SELECT Id FROM User WHERE Profile.Name = 'Customer Community User'
  AND CreatedDate = TODAY
)
```

**Why it works:** Staging Contacts first and using an External ID for cross-reference makes the ContactId join deterministic. All required locale fields prevent silent row rejection. Verifying NetworkMember post-insert confirms the site association is working before users attempt to log in.

---

## Example 2: Migrating Users from Customer Community to Customer Community Plus

**Context:** After a license upgrade, an org needs to move 1,200 active Customer Community users to Customer Community Plus. The old site profile is `CC_Member_Profile` and the new site profile is `CCP_Enhanced_Profile`. Both profiles exist; the new profile is already associated with the upgraded network in Setup.

**Problem:** Teams attempt to update `UserType` directly, which Salesforce rejects. Alternatively, they update the ProfileId without verifying the new profile is associated with the target network, leaving users unable to log in despite having the correct license.

**Solution:**

Step 1 — Verify the destination profile is associated with the target network:

```sql
SELECT Id, Name
FROM Profile
WHERE Id IN (
  SELECT ProfileId
  FROM NetworkMember
  WHERE NetworkId = '0DB...'  -- target network Id
)
AND Name = 'CCP_Enhanced_Profile'
```

If this returns no rows, the profile must be added to the network in Setup before proceeding.

Step 2 — Export current users and build the update CSV:

```sql
SELECT Id, ProfileId, Profile.Name, Username
FROM User
WHERE Profile.Name = 'CC_Member_Profile'
AND IsActive = true
```

Step 3 — Update CSV: replace ProfileId column with the Id of `CCP_Enhanced_Profile`. Keep all other fields as-is. Use Data Loader update operation.

Step 4 — After update, check for stale NetworkMember records on the old network:

```sql
SELECT Id, MemberId
FROM NetworkMember
WHERE NetworkId = '0DB...'  -- old network Id
AND MemberId IN (
  SELECT Id FROM User WHERE Profile.Name = 'CCP_Enhanced_Profile'
)
```

Step 5 — Delete stale NetworkMember records returned by the above query using Data Loader delete.

**Why it works:** Profile update is the only supported way to change an external user's license type. Verifying the profile-network association before the update prevents the silent access failure. Cleaning stale NetworkMember records prevents the user from appearing as a member of the old (lower-privilege) site.

---

## Anti-Pattern: Inserting Users Before Contacts Are Confirmed

**What practitioners do:** Export source user data and immediately attempt a Data Loader User insert, expecting Salesforce to create Contacts automatically or to ignore the ContactId requirement.

**What goes wrong:** Every row in the Data Loader job fails with `FIELD_INTEGRITY_EXCEPTION: Contact: id value of incorrect type` or `INVALID_CROSS_REFERENCE_KEY`. Because the error is generic, teams waste significant time debugging what they assume is a field-mapping issue, when the root cause is simply missing Contact records.

**Correct approach:** Always execute the Contact/Account upsert job first and validate row counts before starting the User insert. Use a SOQL query to confirm the Contact External ID join resolves for every row in the User CSV before submitting the insert job.
