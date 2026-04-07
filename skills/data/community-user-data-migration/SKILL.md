---
name: community-user-data-migration
description: "Use this skill to migrate external community/portal user accounts at scale: bulk creating Experience Cloud users via Data Loader, migrating users between license types (Customer Community to Customer Community Plus, or to Partner Community), importing Customer Portal users into Experience Cloud, and resolving Contact/Account hierarchy prerequisites. Trigger keywords: migrate community users, import external users Experience Cloud, bulk create portal users, move users between license types, migrate Customer Community to Partner Community. NOT for internal user data migration. NOT for general data migration (see data/bulk-data-migration). NOT for configuring Experience Cloud sites or profiles from scratch."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "migrate community users to Experience Cloud"
  - "import external users Experience Cloud bulk create portal users"
  - "move users between license types Customer Community to Partner Community"
  - "migrate Customer Community to Customer Community Plus"
  - "bulk create external portal users Data Loader ContactId"
  - "Experience Cloud user migration fails ContactId"
tags:
  - experience-cloud
  - community-users
  - external-users
  - data-migration
  - data-loader
  - license-migration
  - portal-users
inputs:
  - Source system user export (username, email, profile name, contact/account identifiers)
  - Target Salesforce org with Contact and Account hierarchy pre-established
  - Experience Cloud site name(s) and associated profile names
  - License type mapping (source license → destination license)
  - Data Loader or Bulk API 2.0 credentials and endpoint
outputs:
  - Validated user CSV ready for Data Loader insert
  - Migration runbook with pre-flight and post-migration steps
  - NetworkMember cleanup checklist for old networks
  - Post-migration validation SOQL queries
dependencies:
  - data/data-migration-planning
  - security/experience-cloud-security
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Community User Data Migration

Use this skill when bulk-creating or migrating external Experience Cloud / portal user accounts, including moving users between license types and resolving Contact/Account hierarchy requirements. This skill covers the full Data Loader workflow, NetworkMember record management, and profile-to-network association validation.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm every target user has a pre-existing Contact (or Person Account) record in the destination org. There is no implicit Contact creation when inserting Users — bulk insert will fail with a generic DML error if `ContactId` is missing or points to a non-existent record.
- Identify the destination Experience Cloud site name(s) and confirm which Profiles are associated with each network. A profile not linked to the target network will not trigger NetworkMember auto-creation even if it is a community-enabled profile type.
- Know the exact source license type and destination license type for every user cohort. Mixing license types in a single Data Loader job is not possible — profile assignment determines license consumption, so profile must match destination license.
- Confirm active license seat availability in the destination org before the migration window. Deactivated users still occupy license seats during the migration window until explicitly freed.
- Check whether the org uses Person Accounts — Person Account users link via `AccountId` (the person account record) rather than a standard `ContactId`, and the field mapping is different.

---

## Core Concepts

### Contact/Account Hierarchy as Prerequisite

Every external (portal/community) user in Salesforce is linked to either a Contact or a Person Account. This linkage is enforced at the database level: a User record with `UserType` of `PowerCustomerSuccess`, `PowerPartner`, `CustomerSuccess`, or `CspLitePortal` requires a valid `ContactId` (or, for Person Accounts, an `AccountId` on the person account). Attempting a bulk User insert without pre-populated Contacts results in an `INVALID_CROSS_REFERENCE_KEY` or `FIELD_INTEGRITY_EXCEPTION` error on every row.

Migration sequence must therefore be: Contact/Account upsert first → User insert second. Do not attempt to create Users and Contacts in the same Data Loader job.

### NetworkMember Auto-Creation

When a User is assigned a Profile that is associated with an Experience Cloud network (site), Salesforce automatically creates a `NetworkMember` junction record linking the User to that Network. This auto-creation happens on User insert or on Profile update — it is not a separate step.

However, the inverse is not automatic: when a User's Profile is changed to one associated with a different network (license migration scenario), the old `NetworkMember` record for the previous network is not automatically deleted. The user will effectively be a member of both the old and new networks until the stale record is cleaned up.

### License Migration via Profile Update

Migrating a user from Customer Community to Customer Community Plus (or to Partner Community) is accomplished by updating the `ProfileId` field on the User record to a Profile associated with the destination license type and site. The license type consumed by a user is determined by the profile, not by a separate license assignment field.

Key constraint: the destination Profile must be explicitly associated with the destination Experience Cloud site in Setup > Digital Experiences > [Site] > Administration > Members. A profile that has community-user license features enabled but is not associated with the target network will not grant site access.

### Data Loader Field Mapping for External Users

When inserting Users via Data Loader:

- `UserType` must be set correctly for the license (e.g., `PowerCustomerSuccess` for Customer Community, `PowerCustomerSuccessPortal` for Customer Community Plus, `PowerPartner` for Partner Community).
- `ContactId` must reference a pre-existing Contact in the same org. Use an External ID on Contact for reliable cross-reference during upsert.
- `ProfileId` must reference a Profile that is associated with the target Experience Cloud network.
- `IsActive` should be `true` for active users.
- `Username` must be org-wide unique and typically follows a convention that avoids collision with sandbox copies (e.g., append `.migrated` or environment suffix).

---

## Common Patterns

### Pattern: Bulk External User Insert via Data Loader with Pre-Staged Contacts

**When to use:** Migrating a large volume of net-new external users (Customer Portal, legacy community, or external IdP) into Experience Cloud from a source system export.

**How it works:**

1. Export source user data including email, name, and the external identifier that maps to a Contact record.
2. In the destination org, upsert Contacts using an External ID field (e.g., `Legacy_Customer_ID__c`) to establish the Contact hierarchy. Confirm row counts match.
3. Query `SELECT Id, Legacy_Customer_ID__c FROM Contact` to produce a ContactId lookup map.
4. Build the User CSV: map ContactId, ProfileId (query by name), UserType, Username, Email, FirstName, LastName, Alias, TimeZoneSidKey, LocaleSidKey, EmailEncodingKey, LanguageLocaleKey.
5. Insert Users via Data Loader. Review error log — `INVALID_CROSS_REFERENCE_KEY` on ContactId means the Contact lookup failed; recheck External ID mapping.
6. Verify NetworkMember auto-creation: `SELECT Id, MemberId, NetworkId FROM NetworkMember WHERE MemberId IN (:insertedUserIds)`.

**Why not the alternative:** Creating Users and Contacts in the same job is not supported by the platform. Apex-based bulk creation in a trigger is possible but reintroduces governor limit risk on very large volumes; Data Loader with staged Contacts is more reliable and auditable.

### Pattern: License Type Migration (Profile Update)

**When to use:** Moving existing users from Customer Community to Customer Community Plus, or from Customer Community Plus to Partner Community, within the same org.

**How it works:**

1. Query target users: `SELECT Id, ProfileId, Profile.Name FROM User WHERE Profile.Name = 'Customer Community Login User' AND IsActive = true`.
2. Identify the destination Profile name and confirm it is associated with the target network in Setup.
3. Export User IDs and map to destination ProfileId.
4. Update `ProfileId` field via Data Loader update operation.
5. Post-update: query NetworkMember for old network to identify stale records.
6. Delete stale NetworkMember records for the old network: `SELECT Id FROM NetworkMember WHERE NetworkId = :oldNetworkId AND MemberId IN (:migratedUserIds)`.

**Why not the alternative:** Attempting to change `UserType` directly is not supported after User creation. License migration must be done through Profile reassignment.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Bulk new external users, Contacts exist | Data Loader User insert with ContactId mapping | Most reliable for large volumes; auditable error log |
| Bulk new external users, no Contacts | Stage Contact upsert first, then User insert | Platform enforces Contact prerequisite; cannot bypass |
| License type change (same org) | Data Loader Profile update on existing Users | UserType is immutable post-creation; Profile drives license |
| Person Account org | Map User to AccountId of person account, not ContactId | Person Account users use different field linkage |
| Single-site to multi-site migration | Update Profile to multi-site profile, clean old NetworkMember | NetworkMember is not auto-cleaned on Profile change |
| Sandbox-to-production promotion | Export Users from sandbox, re-stage Contacts in prod, re-insert | User records cannot be promoted via Change Sets or Metadata API |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Validate Contact/Account hierarchy** — Before touching any User records, query the destination org to confirm every source user maps to an existing Contact (or Person Account). Export `SELECT Id, ExternalId__c FROM Contact` and cross-reference against the source user list. Resolve all missing Contacts before proceeding.
2. **Confirm profile-to-network association** — In Setup > Digital Experiences > [Site] > Administration > Members, verify the target profile appears in the "Selected Profiles" list. Query `SELECT Id, Name FROM Profile WHERE Id IN (SELECT ProfileId FROM NetworkMember WHERE NetworkId = :targetNetworkId)` as a programmatic check.
3. **Prepare and validate the User CSV** — Build the migration CSV with required fields (ContactId, ProfileId, UserType, Username, Email, Alias, TimeZoneSidKey, LocaleSidKey, EmailEncodingKey, LanguageLocaleKey, IsActive). Run a pre-flight check: confirm no duplicate Usernames, all ContactIds resolve, all ProfileIds resolve.
4. **Execute Data Loader insert/update** — Use insert for new users; use update for license migration (Profile change only). Process in batches of no more than 200 rows per job to keep error logs manageable. Capture the success and error CSVs.
5. **Verify NetworkMember records** — After insert, query `SELECT Id, MemberId, NetworkId FROM NetworkMember WHERE MemberId IN (:insertedOrUpdatedUserIds)` to confirm membership was auto-created for the correct network. For license migrations, also query the old network and delete stale NetworkMember records.
6. **Post-migration validation and cleanup** — Confirm user count in destination matches expected count. Deactivate source users (if same org migration) or document deactivation window. Validate that deactivated users are removed from the license count after the grace period. Run smoke tests: log in as a migrated user in a sandbox before production cutover.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All Users in the migration file have a valid, resolvable ContactId (or Person Account AccountId)
- [ ] Target Profile is associated with the destination Experience Cloud network in Setup
- [ ] No duplicate Usernames in the migration CSV or in the org
- [ ] UserType value matches the destination license type
- [ ] NetworkMember records confirmed for new/updated users on the correct network
- [ ] Stale NetworkMember records on old network deleted (license migration scenario)
- [ ] Deactivated source users accounted for in license seat count
- [ ] Error log from Data Loader reviewed — zero unresolved INVALID_CROSS_REFERENCE_KEY errors
- [ ] Smoke test: at least one migrated user can log in to the destination site

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **User insert fails silently on ContactId mismatch** — If the ContactId in the CSV references a Contact in a different org or a deleted Contact, Data Loader returns `INVALID_CROSS_REFERENCE_KEY` with no indication of which field is at fault. Always pre-validate ContactIds with a SOQL query before the insert job.
2. **NetworkMember records not auto-cleaned on Profile change** — When a User's Profile is updated to one associated with a different network, Salesforce creates a new NetworkMember for the new network but does not remove the old one. The user remains a member of both networks. This causes unexpected portal access and inflated member counts on the old site.
3. **Deactivated users still occupy license seats during migration window** — Deactivating a User does not immediately release the license. License seat counts are recalculated on a platform schedule. Plan migration windows to account for this lag; do not assume the freed seats are available the moment you deactivate the old cohort.
4. **UserType is immutable after User creation** — You cannot change a User's `UserType` after the record is created. License migration must be done via Profile reassignment, not by updating UserType. Attempts to update UserType via Apex or the API will throw `FIELD_INTEGRITY_EXCEPTION`.
5. **Sandbox username collision blocks migration testing** — Salesforce appends `.invalid` or a sandbox suffix to usernames when a sandbox is refreshed. If you export Users from a sandbox and attempt to re-insert without adjusting the Username field, the insert will fail on uniqueness constraints in the destination org.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Migration CSV (Users) | Validated Data Loader input file with all required User fields |
| Contact pre-staging CSV | Upsert file for establishing Contact/Account hierarchy before User insert |
| NetworkMember cleanup queries | SOQL to identify and delete stale NetworkMember records post-migration |
| Post-migration validation queries | SOQL set to confirm User counts, NetworkMember records, and Profile assignments |
| Migration runbook | Step-by-step execution plan with rollback notes (see templates/) |

---

## Related Skills

- data/data-migration-planning — Use for overall migration scoping, cutover planning, and rollback design before executing community user migration
- security/experience-cloud-security — Use to validate sharing rules, guest user settings, and profile permissions on the destination site after migration
- data/external-user-data-sharing — Use when migrating users who need specific record-level sharing configurations in the destination org
