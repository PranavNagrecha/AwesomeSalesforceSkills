---
name: einstein-activity-capture-setup
description: "Configure Einstein Activity Capture (EAC) for an org: enable the feature, create Configuration profiles, set auth type (User-Level or Org-Level OAuth), define email and calendar sync scope, configure excluded domains and privacy settings, assign users, and verify sync health. NOT for manual activity logging, Einstein Opportunity Scoring setup, Pipeline Inspection, or troubleshooting email deliverability outside EAC."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - Reliability
triggers:
  - "How do I set up Einstein Activity Capture to sync emails and calendar events to Salesforce?"
  - "EAC is enabled but emails are not showing up on contact or opportunity records — what did I miss in the configuration?"
  - "How do I prevent personal or internal emails from syncing into Salesforce with Einstein Activity Capture?"
  - "What is the difference between User-Level and Org-Level OAuth for Einstein Activity Capture?"
  - "How do I create an EAC Configuration profile and assign it to sales reps?"
tags:
  - einstein-activity-capture
  - eac
  - email-sync
  - calendar-sync
  - activity-timeline
  - sales-cloud
  - configuration-profile
  - oauth
inputs:
  - Confirmation of Einstein Activity Capture license entitlement (included with Einstein for Sales / Sales Cloud Einstein / Einstein 1 Sales)
  - Email/calendar platform in use (Microsoft Exchange / Office 365 or Google Workspace)
  - List of domains or addresses that must be excluded from sync (legal, HR, executive)
  - "Auth model decision — User-Level OAuth (each user connects own account) vs Org-Level OAuth (service account, admin-managed)"
  - List of user profiles or individuals who should receive EAC access
outputs:
  - Enabled EAC feature in the org with confirmed license status
  - One or more Configuration profiles defining sync scope, auth type, and exclusion rules
  - Einstein Activity Capture Permission Set License (PSL) assigned to all target users
  - Configuration profiles assigned to target users or profiles
  - Verified sync health — emails and calendar events appearing on Activity Timeline
  - Storage and archival strategy documented (as of Summer '25, synced emails consume org storage)
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Einstein Activity Capture Setup

This skill activates when a practitioner needs to enable, configure, and assign Einstein Activity Capture (EAC) in a Salesforce org — covering the full admin workflow from feature enablement through Configuration profile creation, auth type selection, exclusion rule setup, user assignment, and sync verification. It does NOT cover Einstein Opportunity Scoring setup, Pipeline Inspection, manual activity logging design, or general email deliverability troubleshooting.

---

## Before Starting

Gather this context before working on anything in this domain:

- **License verification:** EAC is included in Einstein for Sales (add-on), Sales Cloud Einstein, and Einstein 1 Sales editions. It is NOT included in core Sales Cloud or Service Cloud. Verify entitlement in Setup > Company Information > Permission Set Licenses — look for `Einstein Activity Capture` PSL seats. Attempting to enable EAC without the correct license results in a silent failure or a greyed-out Setup toggle.
- **Email platform:** EAC supports Microsoft Exchange (on-premises 2013+), Microsoft 365, and Google Workspace (Gmail / Google Calendar). Confirm which platform users are on before choosing auth type — Google Workspace only supports User-Level OAuth; Microsoft 365 supports both User-Level and Org-Level OAuth.
- **Exclusion domain list:** Legal, HR, executive assistants, and competitors often have domains that must not be synced. This list must be finalized before assigning users to a Configuration profile. Exclusions cannot be retroactively applied to already-synced data.
- **Storage impact:** As of Summer '25, EAC-synced emails are stored as standard `EmailMessage` records and consume org file storage. For high-volume orgs (1000+ reps sending 50+ emails/day), storage growth can be significant. Confirm org storage headroom and plan an archival or data retention policy before go-live.
- **Privacy mode:** EAC offers a Private Activities setting at the Configuration level. When enabled, synced activities are visible only to the owning user and admins — not to other reps browsing the same Contact or Opportunity record. Confirm the org's privacy policy requirements before disabling this.

---

## Core Concepts

### Configuration Profiles

A Configuration profile (also called an EAC Configuration) is the central admin artifact for EAC. It defines: which email and calendar events to sync (scope), the authentication model (User-Level vs Org-Level OAuth), the direction of calendar sync (bi-directional or Salesforce-to-email-client only), excluded domains and email addresses, and the privacy mode setting.

Every user who uses EAC must be assigned to exactly one active Configuration profile. Users with no Configuration assignment get the PSL but cannot sync. A single org can have multiple Configuration profiles — for example, one profile for the sales team (full bi-directional sync, no privacy mode) and one for executive assistants (email only, privacy mode on).

Configuration profiles are managed in Setup > Activity Settings > Einstein Activity Capture > Settings.

### Authentication Types

**User-Level OAuth** requires each user to individually authorize EAC to access their email/calendar account by clicking "Connect Account" in their personal Salesforce settings. The authorization token is stored per-user. If the user revokes the token or changes their password, their sync stops — independently of other users. This is the only option for Google Workspace.

**Org-Level OAuth** (Microsoft 365 only) uses a single service account authorized by an admin. The admin grants EAC access to the entire Microsoft 365 tenant (or a defined subset of mailboxes) via Azure Active Directory. Individual users do not need to take action. When a rep leaves, their sync is revoked by removing them from the EAC assignment — not by revoking individual tokens. This model is preferred for large enterprise rollouts because it eliminates the user-authorization friction, but it requires a Microsoft 365 Global Admin to perform the AAD app consent during setup.

### Sync Behavior and the Activity Timeline

EAC syncs emails to Salesforce as `EmailMessage` records associated with matching Contacts and related records (Leads, Opportunities, Accounts, Cases) via address matching. Calendar events sync as `Event` records. Both surfaces appear in the Activity Timeline component on record pages.

Important: prior to Summer '25, EAC-synced activities were stored in a separate Einstein data store and were NOT queryable via standard SOQL on `Task` or `Event`. As of Summer '25, synced emails are stored as standard `EmailMessage` records and ARE queryable. Synced calendar events remain as standard `Event` records with `IsActivitySyncEnabled = true`. Confirm the org's API version and release version when advising on queryability — older behavior docs are misleading.

Activity matching uses the email addresses on the Salesforce Contact/Lead records. If an email domain matches a Contact's email but EAC cannot find a unique Contact match, the activity is placed in the "Unresolved Items" queue for the user to manually associate. Duplicate or missing Contact email addresses are a primary cause of "emails syncing but not appearing on records."

### Permission Set License Assignment

The `Einstein Activity Capture` PSL must be assigned to each user before they can be added to a Configuration profile. Assigning a Configuration profile to a user without first granting the PSL results in the assignment appearing to succeed but sync never starting. The PSL is managed separately from standard Permission Sets — it is assigned via Setup > Users > [User] > Permission Set License Assignments.

---

## Common Patterns

### Pattern: Enterprise Rollout with Org-Level OAuth (Microsoft 365)

**When to use:** Large org (100+ reps) on Microsoft 365 where individual user authorization steps are not operationally feasible, or where IT security requires a centrally managed service account.

**How it works:**
1. A Microsoft 365 Global Admin consents to the Salesforce EAC application in Azure Active Directory, granting EAC permission to read user mailboxes in the tenant.
2. In Salesforce Setup, create a Configuration profile with Auth Type = Org-Level OAuth, configure sync scope, exclusion domains, and privacy settings.
3. Assign the EAC PSL to all target users in bulk via Permission Set License Assignments.
4. Assign users to the Configuration profile. Sync starts automatically within 1–2 hours with no action required from users.

**Why not User-Level OAuth:** With User-Level OAuth at 200+ reps, IT must communicate to each rep, track authorization completion, and handle token refresh failures individually. Org-Level OAuth reduces support overhead to near zero post-setup.

### Pattern: Privacy-Conscious Rollout with Domain Exclusions

**When to use:** Orgs with legal, HR, or compliance requirements that prohibit certain email categories from entering Salesforce, or orgs where executives require that their calendar events remain private.

**How it works:**
1. Before creating the Configuration profile, compile the exclusion list: external domains (competitors, legal counsel, HR vendors), internal domains used for sensitive communication (e.g. `legal.company.com`), and specific email addresses.
2. In the Configuration profile, enter excluded domains under "Excluded Domains" and excluded email addresses under "Excluded Email Addresses."
3. For calendar privacy, enable "Private Events" exclusion so events marked Private in the email client are not synced.
4. For the executive group, create a separate Configuration profile with Private Activities mode enabled, so synced activities are only visible to the exec and admins.
5. Assign users to their respective profiles after all exclusions are confirmed with Legal/Compliance.

**Why not configure exclusions post-launch:** EAC does not retroactively remove already-synced emails when exclusion rules are added. Any email that matched a contact before the exclusion was added remains on the record. Exclusions only prevent future syncs.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Users on Google Workspace | User-Level OAuth only | Google Workspace does not support Org-Level OAuth for EAC |
| Users on Microsoft 365, large rollout (100+) | Org-Level OAuth via Azure AD consent | Eliminates per-user authorization overhead; IT manages centrally |
| Users on Microsoft 365, small rollout (<20) | Either; User-Level is simpler | Org-Level requires Azure AD Global Admin involvement, disproportionate for small teams |
| Org has legal/HR domains that must not sync | Configure Excluded Domains BEFORE user assignment | Exclusions are not retroactive; assign users only after exclusions are confirmed |
| Executive users who need activity privacy | Separate Configuration profile with Private Activities enabled | Prevents other reps from seeing exec emails/calendar on shared records |
| High email volume org (1000+ reps) | Plan storage archival before go-live | As of Summer '25, EAC emails consume org storage; large orgs can exceed storage limits within months |
| Users not seeing synced emails on records | Check Contact email address match and Unresolved Items queue | Sync works but matching fails when Contact email is missing or duplicated |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify license entitlement and seat count.** Navigate to Setup > Company Information > Permission Set Licenses and confirm the `Einstein Activity Capture` PSL exists with sufficient seats for the target user population. If the PSL is absent or seats are insufficient, stop — contact Salesforce AE or Account Manager before proceeding. No configuration will function without the correct license.

2. **Enable Einstein Activity Capture.** Navigate to Setup > Activity Settings > Einstein Activity Capture. Toggle "Enable Einstein Activity Capture" on. If the toggle is greyed out, the PSL is missing or the org type does not support EAC (e.g. Developer Edition without add-on).

3. **Compile exclusion requirements before creating Configuration.** Work with Legal, HR, and Security stakeholders to build the excluded domains and excluded address lists. Also confirm: (a) whether calendar sync should be bi-directional or one-directional, (b) whether Private Activities mode is required, and (c) the email platform (Microsoft 365 / Google Workspace) and auth model.

4. **Create Configuration profile(s).** In Setup > Activity Settings > Einstein Activity Capture > Settings, create a new Configuration. Set the name, auth type (User-Level OAuth or Org-Level OAuth), sync scope (email, calendar, or both), sync directions, excluded domains, excluded addresses, and privacy settings. For Org-Level OAuth, complete the Azure AD app consent flow during this step.

5. **Assign EAC PSL to target users.** For each user who will use EAC, go to Setup > Users > [User] > Permission Set License Assignments and add the `Einstein Activity Capture` PSL. Do this BEFORE adding users to a Configuration profile. Bulk assignment via Data Loader or the PSL assignment page is supported for large user groups.

6. **Assign users to Configuration profile.** Return to the Configuration profile and add users or profiles to the assignment list. For User-Level OAuth, instruct users to connect their email account in their personal Salesforce settings (Profile > Settings > Connected Accounts). For Org-Level OAuth, sync starts automatically within 1–2 hours.

7. **Verify sync and review Unresolved Items.** After 2–4 hours, confirm that emails and calendar events appear on the Activity Timeline of test Contact and Opportunity records. Review the EAC Unresolved Items page for activities that matched no record. Address missing or duplicate Contact email addresses causing matching failures. Monitor storage consumption in Setup > Storage Usage in the first week.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Einstein Activity Capture PSL exists in org with correct seat count confirmed
- [ ] EAC toggle is enabled in Setup > Activity Settings > Einstein Activity Capture
- [ ] Excluded domains and addresses reviewed and approved by Legal/Compliance BEFORE user assignment
- [ ] Configuration profile(s) created with correct auth type, sync scope, directions, and privacy settings
- [ ] For Org-Level OAuth: Azure AD app consent completed by Microsoft 365 Global Admin
- [ ] EAC PSL assigned to ALL target users before Configuration profile assignment
- [ ] Users assigned to correct Configuration profile(s)
- [ ] For User-Level OAuth: users instructed and confirmed to connect their accounts
- [ ] Sync verified — emails and calendar events visible on Activity Timeline for test records
- [ ] Unresolved Items queue reviewed and addressed
- [ ] Org storage consumption monitored with archival plan in place for high-volume orgs

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **PSL must precede Configuration assignment** — Assigning a user to a Configuration profile without first granting the Einstein Activity Capture PSL appears to succeed in the UI but sync never starts. No error is displayed. The fix is to grant the PSL first, then re-save or re-add the user to the Configuration. This is the most common cause of "EAC assigned but not syncing."

2. **Exclusion rules are not retroactive** — Adding an excluded domain to a Configuration profile after users have been syncing does not remove previously synced emails from Salesforce records. Those records persist. Exclusions only prevent future sync. If retroactive removal is required, records must be deleted manually or via a batch Data Loader job querying `EmailMessage` WHERE the from/to address matches the excluded domain.

3. **Storage growth is real as of Summer '25** — Before Summer '25, EAC used a separate data store that did not count against org storage. As of Summer '25, synced emails are stored as standard `EmailMessage` records and consume file storage. A 500-rep team each receiving 40 emails/day can add 1–2 GB of storage per month depending on attachment sizes. Plan for this before go-live.

4. **Google Workspace does not support Org-Level OAuth** — EAC Org-Level OAuth is exclusive to Microsoft 365 via Azure AD. Any guidance recommending Org-Level OAuth for Google Workspace is incorrect — Google Workspace users must always use User-Level OAuth and individually connect their accounts.

5. **Activity Timeline vs SOQL queryability changed in Summer '25** — Prior to Summer '25, EAC-synced emails were in a separate Einstein data store, not queryable via standard SOQL. As of Summer '25, synced emails are queryable as `EmailMessage` records. Always confirm the org's Salesforce release version before advising on queryability.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| EAC Configuration profile | Named configuration defining auth type, sync scope, exclusion rules, and privacy settings for a user group |
| PSL assignment list | Record of which users have been granted the Einstein Activity Capture PSL |
| Sync verification report | Manual or documented check that Activity Timeline shows synced emails/events on test records |
| Storage consumption baseline | Initial storage usage reading taken at go-live to detect unexpected growth |
| Exclusion domain registry | Approved list of excluded domains and addresses, signed off by Legal/Compliance |

---

## Related Skills

- einstein-copilot-for-sales — For Einstein Opportunity Scoring, Pipeline Inspection, and AI email generation that complement EAC in a Sales Cloud Einstein deployment
- permission-sets-vs-profiles — For understanding PSL vs Permission Set assignment patterns when rolling out EAC to large user populations

## Official Sources Used

- Einstein Activity Capture Setup — https://help.salesforce.com/s/articleView?id=sf.einstein_sales_activity_capture.htm
- Considerations for Setting Up Einstein Activity Capture — https://help.salesforce.com/s/articleView?id=sf.einstein_sales_activity_capture_consideration.htm
- Einstein Activity Capture Configuration Profiles — https://help.salesforce.com/s/articleView?id=sf.einstein_sales_activity_capture_configuration.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
