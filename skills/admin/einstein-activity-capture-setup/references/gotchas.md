# Gotchas — Einstein Activity Capture Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: PSL Assignment Required Before Configuration Profile Assignment

**What happens:** Adding a user to an EAC Configuration profile without first granting the `Einstein Activity Capture` PSL appears to succeed — the UI shows the user in the assignment list. But sync never starts. For User-Level OAuth, the user does not see the "Connect Account" prompt in their personal settings. For Org-Level OAuth, the user's mailbox is silently excluded from the sync batch. No error message is displayed anywhere.

**When it occurs:** Any time an admin creates a Configuration profile and adds users to it in the same session without navigating to PSL assignment first. Also occurs during bulk rollouts where PSL assignment is treated as an afterthought.

**How to avoid:** Follow a strict sequence: (1) verify PSL seats available, (2) assign PSL to users, (3) create or open Configuration profile, (4) add users. After a problematic rollout, audit PSL assignment for all users in the Configuration profile — any user missing the PSL must have it granted, then be removed and re-added to the Configuration to trigger re-evaluation.

---

## Gotcha 2: Exclusion Rules Do Not Apply Retroactively

**What happens:** When an excluded domain or email address is added to a Configuration profile after sync has already been running, the exclusion only prevents future syncs. Emails already synced from the excluded domain remain on Salesforce records as `EmailMessage` records — they are not automatically deleted or hidden.

**When it occurs:** Post-launch configuration changes are the most common trigger. A Legal team review happens after go-live and identifies domains that should not have been syncing. Or an admin adds a new competitor domain exclusion 3 months into production.

**How to avoid:** Compile and review the exclusion list with Legal, Compliance, and HR stakeholders before creating the Configuration profile and before assigning any users. Treat the exclusion list as a pre-go-live gate item, not a post-launch tuning knob. If retroactive removal is necessary after the fact, use Data Loader or SOQL to identify `EmailMessage` records WHERE `FromAddress` or `ToAddress` contains the excluded domain and hard-delete them.

---

## Gotcha 3: Google Workspace Users Cannot Use Org-Level OAuth

**What happens:** Admins setting up EAC for mixed-platform orgs (some users on Microsoft 365, some on Google Workspace) attempt to configure Org-Level OAuth for Google Workspace users, or assume one Configuration profile with Org-Level OAuth covers all users regardless of email platform. Google Workspace users' sync either fails silently or never starts.

**When it occurs:** Any org with Google Workspace users where the admin is not aware of the platform restriction, or where a project requirement mandates Org-Level OAuth without verifying platform compatibility.

**How to avoid:** Always identify the email platform for every user group before selecting auth type. Google Workspace requires User-Level OAuth without exception. For mixed-platform orgs, create separate Configuration profiles — one per email platform — with the appropriate auth type. Assign users to the profile matching their email platform.

---

## Gotcha 4: Storage Spike After Summer '25 Upgrade for Existing EAC Orgs

**What happens:** Orgs that enabled EAC before the Summer '25 release and upgraded to Summer '25 may see a sudden significant increase in org storage consumption. Before Summer '25, synced emails lived in a separate Einstein data store outside org storage quotas. After Summer '25, synced emails are migrated to standard `EmailMessage` records and count against file storage. An org with 500 reps syncing for 12 months can see gigabytes of storage added during the migration window.

**When it occurs:** Any org on EAC that upgrades to Summer '25 or later without having reviewed the release notes for this storage behavior change.

**How to avoid:** Before upgrading to Summer '25 or deploying EAC for the first time on Summer '25+, review org storage in Setup > Storage Usage. Set up a storage alert. Plan data archival or email retention policies. If storage is near capacity, either expand storage or reduce the sync window before the migration completes.

---

## Gotcha 5: Activity Matching Fails Silently When Contact Email Is Absent or Duplicated

**What happens:** EAC matches incoming emails to Salesforce records by comparing the email sender/recipient addresses against Contact and Lead records. If a Contact record has no email address, or if multiple Contact records share the same email address, the incoming email cannot be auto-matched. It lands in the "Unresolved Items" queue rather than appearing on any record. Reps report "emails not showing on the Opportunity" but sync is actually working correctly — matching is failing.

**When it occurs:** Common in orgs with poor data quality — contacts imported without email addresses, or deduplication not having been run before EAC enablement. Also common for shared email addresses (e.g., a distribution list address like `sales@company.com` appearing on multiple Contacts).

**How to avoid:** Before go-live, run a data quality check on Contact and Lead email fields: confirm all records that should be matched have email addresses populated, and identify/resolve duplicate email addresses. After go-live, monitor Setup > Einstein Activity Capture > Unresolved Items weekly during the first month. Items in the Unresolved Items queue require manual user action to associate with the correct record.
