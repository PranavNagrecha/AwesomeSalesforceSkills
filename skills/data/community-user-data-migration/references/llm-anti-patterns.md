# LLM Anti-Patterns — Community User Data Migration

Common mistakes AI coding assistants make when generating or advising on Community User Data Migration. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Attempting User Upsert Without Pre-Existing Contact Hierarchy

**What the LLM generates:** A Data Loader CSV or Apex bulk insert that creates User records with a ContactId populated by a formula or lookup, or that omits ContactId entirely and assumes Salesforce will auto-associate the user with a Contact.

**Why it happens:** LLMs conflate internal user creation (which requires no Contact) with external community user creation. Training data contains many examples of internal user setup where ContactId is not present.

**Correct pattern:**

```sql
-- Pre-flight: confirm every source user maps to an existing Contact
SELECT Id, Legacy_External_ID__c
FROM Contact
WHERE Legacy_External_ID__c IN ('ext001', 'ext002', ...)
```

ContactId must reference a real, pre-existing Contact in the destination org. Stage Contacts first, then insert Users. Never rely on Salesforce to create the Contact.

**Detection hint:** Flag any User insert CSV or Apex insert that does not include a validated `ContactId` (or `AccountId` for Person Accounts). Also flag plans that do Contact and User creation in the same batch job.

---

## Anti-Pattern 2: Not Cleaning NetworkMember Records on Old Network After Migration

**What the LLM generates:** A migration plan that updates User ProfileIds to the new site profile and considers the migration complete, with no step to remove stale NetworkMember records for the previous network.

**Why it happens:** LLMs are unaware that NetworkMember auto-creation does not have a corresponding auto-deletion. The LLM models the Profile update as a clean transfer when it is actually an additive operation on NetworkMember.

**Correct pattern:**

```sql
-- Identify stale NetworkMember records on old network after Profile update
SELECT Id, MemberId
FROM NetworkMember
WHERE NetworkId = '0DB_OLD_NETWORK_ID'
AND MemberId IN (
  SELECT Id FROM User WHERE Profile.Name = 'New_Site_Profile'
)
```

Delete the returned records via Data Loader delete after confirming new NetworkMember records exist on the destination network.

**Detection hint:** Flag any migration plan that updates ProfileId but does not include a post-migration NetworkMember query and cleanup step for the source network.

---

## Anti-Pattern 3: Missing Profile-to-Network Association Check Before Migration

**What the LLM generates:** A plan that assigns a community-enabled Profile to Users without first verifying that the Profile is listed under the destination Experience Cloud site's Members configuration.

**Why it happens:** LLMs conflate "profile has community license type" with "profile grants access to the specific network." These are separate conditions — a profile can have the right license type but not be associated with the target site.

**Correct pattern:**

```sql
-- Confirm destination profile is associated with target network
SELECT Id, Name
FROM Profile
WHERE Id IN (
  SELECT ProfileId FROM NetworkMember WHERE NetworkId = '0DB_TARGET_NETWORK_ID'
)
AND Name = 'Target_Community_Profile'
```

If no rows are returned, the profile must be added to the site in Setup > Digital Experiences > [Site] > Administration > Members before executing the migration.

**Detection hint:** Flag migration plans that assign a Profile to Users without including a step to verify the profile-network association. Also flag plans that assume a "Customer Community" profile type automatically grants access to a specific site.

---

## Anti-Pattern 4: Attempting to Update UserType Directly for License Migration

**What the LLM generates:** A Data Loader update CSV or Apex DML that includes a `UserType` field update to change a user's license (e.g., from `PowerCustomerSuccess` to `PowerCustomerSuccessPortal`).

**Why it happens:** LLMs reason that if UserType determines the license, updating UserType should change the license. This is logically coherent but incorrect — Salesforce makes UserType immutable after User creation.

**Correct pattern:**

```
-- UserType cannot be updated after User creation.
-- To change license type: update ProfileId to a Profile associated with
-- the destination license and Experience Cloud site.
-- UserType will reflect the correct value automatically.

UPDATE User SET ProfileId = '00e_DESTINATION_PROFILE_ID' WHERE Id IN (...)
```

**Detection hint:** Flag any User update operation that includes `UserType` in the field list. Flag plans that treat UserType as the mechanism for license migration.

---

## Anti-Pattern 5: Not Deactivating or Accounting for Old Users After In-Org Migration

**What the LLM generates:** A migration plan that creates or updates users in the destination configuration but leaves the source users active, or assumes deactivation immediately frees license seats for the new cohort.

**Why it happens:** LLMs often treat user migration as purely an additive operation. The license seat recalculation lag is not widely documented, so LLMs do not account for it. The deactivation step is also frequently omitted as "out of scope" in generated plans.

**Correct pattern:**

```
Post-migration deactivation steps:
1. Export source user IDs that have been successfully migrated (from success.csv).
2. Set IsActive = false on source users via Data Loader update.
3. Do NOT assume seat recalculation is immediate — build a buffer of at least
   one business day before relying on freed seats.
4. Confirm license counts in Setup > Company Information after the buffer period.
```

**Detection hint:** Flag migration plans that have no deactivation step for source users. Also flag plans that schedule the new user insert immediately after the deactivation job in the same maintenance window without accounting for recalculation lag.

---

## Anti-Pattern 6: Using Salesforce Record IDs from Sandbox as ContactId in Production

**What the LLM generates:** A migration CSV built from a sandbox export that uses sandbox Contact record IDs in the `ContactId` column, then submitted to a production org without replacing the IDs.

**Why it happens:** LLMs that generate SOQL-based migration scripts often use `SELECT Id FROM Contact WHERE ...` syntax, producing sandbox IDs. The LLM does not model the fact that record IDs are environment-specific.

**Correct pattern:**

```sql
-- In destination org: look up ContactId by External ID, not by sandbox record Id
SELECT Id, Legacy_Portal_ID__c FROM Contact
WHERE Legacy_Portal_ID__c IN ('ext001', 'ext002', ...)
```

Use an External ID field on Contact as the stable cross-environment identifier. Never use `Id` values sourced from a different Salesforce org in a migration insert.

**Detection hint:** Flag migration plans that reference Salesforce record IDs (`00Q...`, `003...`, `005...`) sourced from a non-production org. Flag any plan that does not use External IDs for cross-environment joins.
