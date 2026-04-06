# Examples — Einstein Activity Capture Setup

## Example 1: Enabling EAC with Org-Level OAuth for a Microsoft 365 Enterprise Rollout

**Context:** A 350-rep Sales Cloud org on Microsoft 365 needs to roll out Einstein Activity Capture. The IT team controls Azure AD and wants to avoid asking 350 reps to individually connect their email accounts. Legal has provided a list of 12 excluded domains (competitors, outside legal counsel, HR vendor).

**Problem:** Without a structured approach, admins commonly assign users to a Configuration profile before granting the PSL, resulting in sync never starting and no error surfaced. They also skip exclusion configuration until after go-live, which means personal or sensitive emails sync into Salesforce and cannot be retroactively removed without manual data cleanup.

**Solution:**

```text
Step 1 — Verify PSL availability
  Setup > Company Information > Permission Set Licenses
  Confirm: "Einstein Activity Capture" shows Available = 350+

Step 2 — Enable EAC
  Setup > Activity Settings > Einstein Activity Capture > Enable toggle ON

Step 3 — Define exclusion list (before creating Configuration)
  Excluded domains approved by Legal:
    competitor.com, outside-counsel.com, hr-vendor.com, [9 more]

Step 4 — Create Configuration profile
  Name: EAC-SalesTeam-365-OrgLevel
  Auth Type: Org-Level OAuth
  Email sync: Enabled (inbound + outbound)
  Calendar sync: Bi-directional
  Excluded Domains: [paste approved list]
  Private Activities: Disabled (per sales leadership preference)
  → Click "Authorize" to initiate Azure AD app consent flow
  → Microsoft 365 Global Admin completes consent in AAD portal

Step 5 — Bulk-assign EAC PSL to all 350 users
  Option A: Setup > Permission Set Licenses > Einstein Activity Capture > Manage Assignments
  Option B: Data Loader INSERT on PermissionSetLicenseAssign object
    Required fields: AssigneeId, PermissionSetLicenseId
  *** PSL assignment must complete before Step 6 ***

Step 6 — Add users to Configuration profile
  In Configuration profile > Assigned Users: add all 350 users
  (or assign by Profile if all users share a single profile)
  Sync starts automatically within 1-2 hours — no user action required

Step 7 — Verify sync after 4 hours
  Open a test Contact record with recent email activity
  Check Activity Timeline for synced emails and calendar events
  Setup > Einstein Activity Capture > Unresolved Items — address any unmatched activities
```

**Why it works:** Org-Level OAuth delegates authorization to a single AAD service account rather than 350 individual OAuth tokens. Combined with PSL-first assignment and pre-configured exclusion rules, this eliminates the two most common rollout failure modes: sync not starting due to missing PSL, and sensitive data leaking into records because exclusions were added too late.

---

## Example 2: Separate Configuration Profile for Executive Privacy

**Context:** A Sales org has 5 VP-level executives whose calendar events and emails must not be visible to other sales reps browsing shared Opportunity or Account records. The org is already using EAC for the broader team with a standard Configuration profile.

**Problem:** By default, EAC syncs all activities with no privacy restriction — any rep with access to an Opportunity can see the emails and calendar events the VP has synced. The VP team's Legal advisor flagged this as a privacy concern.

**Solution:**

```text
Step 1 — Create a second Configuration profile for execs
  Name: EAC-Executives-Private
  Auth Type: User-Level OAuth (exec preference — personal account control)
  Email sync: Enabled
  Calendar sync: Enabled (one-directional: email-client to Salesforce only)
  Private Activities: ENABLED
    → Synced activities visible only to the activity owner + System Admins
  Excluded Addresses: [exec assistant addresses if desired]

Step 2 — Remove the 5 execs from the standard Configuration profile
  EAC-SalesTeam-Standard > Assigned Users: remove VP records

Step 3 — Add the 5 execs to the new exec profile
  EAC-Executives-Private > Assigned Users: add VP records

Step 4 — Instruct execs to connect their accounts (User-Level OAuth)
  Each exec navigates to: Profile avatar > Settings > Connected Accounts
  Clicks "Connect" next to their Microsoft 365 or Google account
  Authorizes EAC access

Step 5 — Verify privacy
  Log in as a rep who shares an Opportunity with a VP
  Confirm that VP's synced activities do NOT appear on the Opportunity Activity Timeline
  Log in as the VP and confirm their own activities DO appear on their own records
```

**Why it works:** The `Private Activities` setting on the Configuration profile controls visibility at the configuration level, not per-activity. Isolating executives into a dedicated profile with Private Activities enabled ensures all their synced data is scoped to themselves and admins, regardless of record sharing rules.

---

## Anti-Pattern: Assigning Users to Configuration Before Granting PSL

**What practitioners do:** In Setup, admins create a Configuration profile and immediately add users to it — skipping the PSL assignment step because PSL management is in a different part of Setup.

**What goes wrong:** The user assignment saves with no error. The user does not see a "Connect Account" prompt (User-Level OAuth) or sync does not start (Org-Level OAuth). Support tickets are raised claiming "EAC is broken." Investigation reveals the PSL was never assigned.

**Correct approach:** Always assign the `Einstein Activity Capture` PSL to users BEFORE adding them to a Configuration profile. Check PSL assignment status in Setup > Users > [User] > Permission Set License Assignments. After granting the PSL, remove and re-add the user to the Configuration profile to trigger re-evaluation of their sync eligibility.
