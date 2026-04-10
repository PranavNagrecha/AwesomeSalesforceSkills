# Gotchas — FSC Relationship Groups

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: FinServ__PrimaryGroup__c is Not Enforced by the Platform — Duplicates Corrupt Rollups Silently

**What happens:** If two ACR records for the same Person Account (across different groups) both have `FinServ__PrimaryGroup__c = true`, the platform accepts both records without any validation error. The FSC rollup engine processes both, producing indeterminate wealth aggregation: assets may be double-counted across both groups, aggregate only to whichever group's ACR was most recently modified, or shift between groups after the next batch rollup job. The rollup fields appear populated, so the problem is invisible until an advisor notices that total assets no longer match the sum of individual financial account balances.

**When it occurs:** During data migrations (when source data has no primary group concept and migration scripts set `FinServ__PrimaryGroup__c = true` on all ACRs as a default), and when advisors or admins add a client to a second group without first clearing the existing primary group designation.

**How to avoid:** Implement a custom validation rule on AccountContactRelation that prevents `FinServ__PrimaryGroup__c = true` on a new or updated ACR if another ACR record for the same `ContactId` already has it set to `true`. In data migrations, enforce a pre-load deduplication step that guarantees exactly one `FinServ__PrimaryGroup__c = true` ACR per ContactId. Post-migration, run a SOQL audit: `SELECT ContactId, COUNT(Id) FROM AccountContactRelation WHERE FinServ__PrimaryGroup__c = true GROUP BY ContactId HAVING COUNT(Id) > 1`.

---

## Gotcha 2: FinServ__IncludeInGroup__c Defaults to False — Member Is Visible But Assets Are Excluded

**What happens:** When ACR records are created via Apex, Data Loader, Flow, or Quick Action without explicitly setting `FinServ__IncludeInGroup__c = true`, the field defaults to `false`. The member appears in the group's relationship panel and is counted as a member, but none of their financial accounts, opportunities, or related records are included in the group's rollup totals. The group's total assets show zero for that member with no error or warning in any log.

**When it occurs:** Any programmatic ACR creation path where `FinServ__IncludeInGroup__c` is not in the insert payload. This includes Apex bulk inserts, CSV Data Loader loads where the column is omitted, Flow Create Record elements where the field is not mapped, and Quick Actions that do not expose the field.

**How to avoid:** Always explicitly set `FinServ__IncludeInGroup__c = true` in every ACR creation path. Never rely on the platform default. In Flow-based group creation, add the field to the Create Record element's field mapping even if the UX does not expose it as a user-facing field. In Data Loader CSV templates, always include the column and pre-populate it with `true`. Post-creation validation: query `SELECT ContactId, FinServ__IncludeInGroup__c FROM AccountContactRelation WHERE AccountId = '<groupId>'` and confirm no `false` values are unexpected.

---

## Gotcha 3: Rollup Totals Are Stale Between Primary Group Change and Next Recalculation Event

**What happens:** When `FinServ__PrimaryGroup__c` is toggled on an ACR (switching a member's primary group from one group to another), the rollup fields on both the old and new groups do not immediately recalculate. The old group continues to show the member's assets in its totals; the new group does not yet show them. This stale state persists until a trigger event fires on a related financial account record (e.g., the financial account is saved or updated) or the batch rollup job runs.

**When it occurs:** Any time a member's primary group designation changes — common in divorce scenarios (splitting one household into two), remarriage scenarios (adding a client to a new spouse's household), or trust restructuring where a client moves from one trust to another.

**How to avoid:** After changing `FinServ__PrimaryGroup__c` on an ACR, manually trigger a rollup recalculation by either: (1) running `FinServ.RollupBatchJob` immediately after the change, or (2) performing a no-op save on the member's financial account records (e.g., a bulk update that sets each record's `LastModifiedDate` indirectly). Document the stale window in runbooks so advisors know to refresh the group view after a primary group change rather than reporting it as a data error.

---

## Gotcha 4: Trust and Professional Group Record Types May Not Be Active in All FSC Orgs

**What happens:** Attempting to create a group Account with the `Trust` or `Professional Group` record type fails with a generic "Record Type is not available" error if those record types have not been explicitly activated and assigned to the running user's profile. In some FSC provisioning paths, only the `Household` record type is active by default on Account.

**When it occurs:** In orgs where Trust and Professional Group functionality was not part of the initial FSC implementation scope, or in orgs that were upgraded from an earlier FSC version that did not include all three group record types. Also occurs when new profiles are created without inheriting record type assignments from the base FSC profile.

**How to avoid:** Before attempting to create Trust or Professional Group records, verify that both record types are active on the Account object (Setup > Object Manager > Account > Record Types) and assigned to all relevant profiles (Setup > Profiles > [Profile Name] > Record Type Settings > Account). Confirm in Setup that the correct FSC page layout is assigned for each record type. Add this as a prerequisite check in any FSC implementation runbook.

---

## Gotcha 5: Using Account.Id Instead of Account.PersonContactId on ACR Breaks Group Membership

**What happens:** ACR requires a Contact Id in its `ContactId` field. For Person Accounts, the underlying Contact is auto-created by Salesforce and its Id is different from the Person Account's Account Id. Using `Account.Id` instead of `Account.PersonContactId` in the ACR `ContactId` field throws an error or, in some org configurations with certain API versions, silently creates a malformed ACR that does not link the member correctly to the group.

**When it occurs:** In Apex bulk insert scripts, Data Loader imports, and third-party integration payloads that query `Account.Id` for Person Accounts and use it directly as the ACR `ContactId` without retrieving the `PersonContactId` field. This is extremely common in data migrations from non-FSC systems where the Person Account architecture is unfamiliar.

**How to avoid:** Always query `SELECT Id, PersonContactId FROM Account WHERE IsPersonAccount = true` when building ACR records. Use `Account.PersonContactId` as the `ContactId` value, not `Account.Id`. In Data Loader or external system integration, retrieve `PersonContactId` via the Account object (it is a standard read-only field) before constructing ACR import files. Add a pre-migration validation step that confirms all ACR `ContactId` values resolve to Contact records, not Account records.
