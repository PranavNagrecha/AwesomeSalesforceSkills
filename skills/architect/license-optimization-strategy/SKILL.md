---
name: license-optimization-strategy
description: "Auditing, right-sizing, and reclaiming Salesforce licenses to reduce cost and ensure compliant allocation. Trigger keywords: license audit, license cost reduction, unused licenses, permission set license, login-based license, inactive users, license reclamation, right-size licenses. NOT for provisioning net-new licenses (contact AE). NOT for Experience Cloud community license troubleshooting. NOT for permission set assignment logic outside of license gating."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Security
tags:
  - licensing
  - license-audit
  - cost-optimization
  - permission-set-license
  - login-based-license
  - inactive-users
  - user-management
  - well-architected
inputs:
  - "Current org edition and total license allocations (available from Setup > Company Information)"
  - "List of all active users with LastLoginDate from the User object"
  - "Current permission set license (PSL) assignments and available PSL seats"
  - "Identification of occasional-access users (portal, partner, internal-but-infrequent)"
  - "Business use case for each user type (full CRM, read-only reporting, portal self-service, SSO/identity only)"
outputs:
  - "License utilisation report: assigned vs. available for each license type and PSL"
  - "Inactive user list with recommended freeze or deactivation actions"
  - "License right-sizing recommendation: which users can move to a lower-cost license tier"
  - "Login-Based License assessment: which user populations suit monthly-login billing"
  - "PSL rationalisation plan: PSLs that can be unassigned without loss of functionality"
triggers:
  - how do I audit and reclaim unused Salesforce licenses
  - we have too many full CRM licenses and need to right-size
  - which users could be moved to a permission set license instead
  - login-based license vs full license for occasional users
  - inactive user license reclamation process
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# License Optimization Strategy

This skill activates when an org needs to audit its Salesforce license footprint, reduce unnecessary license spend, reclaim seats from inactive users, or select the right license tier for different user populations. It produces a structured license utilisation report, an inactive-user reclamation plan, and a right-sizing recommendation grounded in Salesforce's three primary license tiers, permission set license mechanics, and login-based license billing rules.

---

## Before Starting

Gather this context before working on anything in this domain:

- Pull the current license counts from Setup > Company Information or via the REST `/services/data/vXX.0/limits` endpoint. This endpoint returns `DailyApiRequests` and also exposes org limits, but the canonical license count lives in Setup > Company Information under "User Licenses" and "Permission Set Licenses."
- Query `SELECT Id, Name, LastLoginDate, IsActive, Profile.UserLicense.Name FROM User WHERE IsActive = true` to establish the full picture of active users and their license types before making any reclamation recommendation.
- The most common wrong assumption: "Salesforce charges for user licenses on active accounts only." In practice, Salesforce charges for licenses allocated (purchased), not consumed. An active user occupying a Salesforce license who has never logged in still consumes a paid seat. Reclamation must target both inactive users and over-allocated license counts at renewal.
- Login-Based Licenses are billed on unique monthly logins, not on seat allocation — this fundamentally changes the economics for infrequent users. Confirm whether the org has LBL entitlements before recommending downgrades.
- Permission Set Licenses gate specific feature sets independently of the base user license. Removing a PSL assignment from a user removes their access to that feature immediately — confirm no active automations or integrations depend on PSL-gated features before unassigning.

---

## Core Concepts

### License Tiers

Salesforce organises standard internal-user licenses into three broad tiers. Understanding which tier is appropriate for each user population is the primary lever for cost optimisation:

1. **Salesforce (CRM) license** — Full access to standard CRM objects (Leads, Accounts, Contacts, Opportunities, Cases) and all non-add-on features of the purchased edition. This is the highest-cost tier. Assign only to users who actively work across multiple CRM objects. Read-only reporting users, occasional approvers, and portal administrators are frequently over-licensed at this tier.

2. **Salesforce Platform license** — Access to custom objects, some standard objects (Tasks, Events, Chatter), and Platform-licensed apps. Does NOT include standard CRM objects (no Leads, no Opportunities, no Cases without an explicit entitlement). Significantly cheaper than a full CRM license. Suitable for internal users whose workflow is entirely within a custom-built app or a Lightning app that does not touch CRM objects.

3. **Community / Identity licenses** — Covers Experience Cloud portal users (Customer Community, Customer Community Plus, Partner Community) and pure SSO/Identity-only users. Community licenses are priced per member (named) or per login depending on the license type. Identity licenses provide login and SSO only, with no data access beyond the profile they are assigned to.

### Permission Set Licenses (PSLs)

PSLs are add-on license entitlements that gate specific Salesforce features regardless of the base user license. Examples include: Einstein Analytics PSL (required to access Analytics Studio), Flow Orchestration PSL (required to be assigned to orchestration work items), Revenue Cloud CPQ PSL, and Field Service Mobile PSL. Key behaviors:

- A PSL assignment does not grant a base license. Both the base user license and the PSL must be assigned for the feature to be accessible.
- PSL seats are purchased and consumed independently. The number of PSL seats assigned cannot exceed the number purchased; attempting to assign beyond the limit throws an error.
- Unused PSL assignments do not automatically expire. PSLs should be reviewed at the same frequency as base licenses because they represent real additional cost at renewal.
- Some PSLs are bundled with certain editions (e.g., certain Einstein PSLs with Unlimited Edition) — confirm bundling before purchasing additional PSL seats.

### Login-Based Licensing

Login-Based Licenses (LBL) replace the per-seat billing model with a monthly-login billing model. Instead of paying for a named seat, the org pays per unique user login per calendar month, subject to a monthly allocation. This model suits user populations that log in infrequently — typically fewer than 4–6 times per month — such as external partners, field contractors, or occasional internal reviewers. Key behaviors:

- Monthly login consumption resets on the first of each calendar month (UTC).
- A single user logging in multiple times within a day still counts as one login for that day, but daily logins accumulate across the month toward the monthly allocation.
- If the org exceeds its monthly LBL allocation, Salesforce does NOT lock out users — it charges overage. Monitor consumption via Setup > Login-Based License Usage or query `LoginHistory`.
- LBL is not available for all license types. Verify the specific license type supports LBL before recommending a migration.

### Inactive User Reclamation

Salesforce charges for allocated licenses, but inactive users still consume those seats. The reclamation workflow has three stages:

1. **Identify** — Query `User` where `IsActive = true` and `LastLoginDate < LAST_N_DAYS:90` (or your org's threshold). Users who have never logged in (`LastLoginDate = null`) are the highest-priority reclamation targets.
2. **Freeze** — Use `UserLogin.IsFrozen = true` to prevent login without deactivating the user record. This is a safer intermediate step that preserves data associations and can be reversed. Freezing does NOT release the license seat.
3. **Deactivate** — Set `User.IsActive = false`. Deactivation releases the license seat back to the org's available pool. Deactivated users cannot be assigned as record owners going forward; existing ownership is retained (records do not change owner on deactivation).

---

## Common Patterns

### Pattern 1: Inactive User License Reclamation

**When to use:** When a license audit reveals active user records with no recent login activity, indicating paid seats are being consumed by users who no longer need access.

**How it works:**
1. Query for active users with `LastLoginDate` older than the agreed threshold (90 days is a common starting point; adjust for seasonal usage patterns):
   ```soql
   SELECT Id, Name, Username, LastLoginDate, Profile.UserLicense.Name
   FROM User
   WHERE IsActive = true
     AND (LastLoginDate < LAST_N_DAYS:90 OR LastLoginDate = null)
   ORDER BY LastLoginDate ASC NULLS FIRST
   ```
2. Review the list with HR or the business owner to confirm the users are genuinely inactive and not on leave.
3. Freeze confirmed-inactive users via the `UserLogin` object (`IsFrozen = true`) as an intermediate hold.
4. After a notification period (typically 2 weeks), deactivate users not responding to the freeze notification.
5. Confirm the license pool has recovered the expected seats in Setup > Company Information.

**Why not the alternative:** Deactivating immediately without a freeze-and-notify step risks deactivating users who are on leave, causing business disruption and access reinstatement overhead.

### Pattern 2: License Tier Right-Sizing

**When to use:** When a cost review reveals users are assigned full Salesforce (CRM) licenses but their actual workflow is limited to custom objects, read-only dashboards, or a specific internal app.

**How it works:**
1. For each user group (by profile or job function), audit which standard CRM objects they access by querying `SetupEntityAccess` and reviewing profile/permission set object permissions.
2. Identify user groups that access only custom objects, Tasks, Events, and Chatter — these are candidates for the Salesforce Platform license.
3. Identify users who need only SSO login without data access — these are candidates for the Identity license.
4. For each candidate group, validate in a sandbox by cloning the user's profile, applying the lower license, and confirming the app functions as expected.
5. Change the license type in production by updating the user's profile to one assigned to the target license (profiles are bound to licenses; you cannot change the license on a user directly without changing their profile).

**Why not the alternative:** Changing user licenses without testing the profile against the new license type frequently breaks access to objects the team did not know were in scope. Always test in sandbox first.

### Pattern 3: PSL Rationalisation

**When to use:** When PSL seat counts are approaching the purchased limit or when a renewal review reveals PSL costs for features that are no longer actively used.

**How it works:**
1. Query current PSL assignments:
   ```soql
   SELECT PermissionSet.Label, AssigneeId, Assignee.Name, Assignee.LastLoginDate
   FROM PermissionSetAssignment
   WHERE PermissionSet.IsOwnedByProfile = false
     AND PermissionSet.LicenseId != null
   ORDER BY PermissionSet.Label, Assignee.LastLoginDate ASC NULLS FIRST
   ```
2. For each PSL, list assigned users who have not logged in within 90 days. These are the safest unassignment candidates.
3. For remaining assigned users, confirm which PSL-gated features they are actively using. For Einstein Analytics PSL: query `UserAppMenuCustomization` or check Analytics Studio access logs via Event Monitoring.
4. Unassign PSLs from users who do not actively use the feature. Removal is immediate.
5. Document the PSL count recovered and the cost impact at the per-seat PSL price.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Active user with no login in 90+ days | Freeze via UserLogin.IsFrozen, notify, then deactivate | Preserves data integrity while recovering the seat; reduces risk of premature deactivation |
| Internal user accesses only a custom-built app, no CRM objects | Evaluate Platform license downgrade | Platform license is materially cheaper; covers custom objects and most Platform features |
| External partner or contractor logs in fewer than 6 times/month | Evaluate Login-Based License if entitlement exists | LBL economics beat per-seat pricing for infrequent users; verify LBL entitlement first |
| PSL assigned but user has not logged in for 90+ days | Unassign PSL; recover the seat | No feature loss if the user is inactive; seat is available for active users |
| Users need SSO / identity only — no Salesforce data access required | Identity license | Lowest-cost option for SSO-only use cases; grants login and profile access only |
| Org approaching allocated license ceiling before renewal | Reclaim inactive seats before requesting additional licenses | Reclamation avoids unnecessary license purchases; run the inactive user query first |
| Login-Based License monthly allocation is being exceeded regularly | Review user population — may indicate growth requiring seat licenses | LBL overage is charged at a premium; if most LBL users log in frequently, per-seat may be cheaper |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Pull baseline data: export the current license allocation from Setup > Company Information (user license types, seats purchased, seats in use) and the PSL table (PSLs available, total seats, seats in use).
2. Query active users with `LastLoginDate` and license type. Segment into three buckets: never logged in, inactive 90+ days, and active within 90 days. Calculate the license spend per bucket.
3. For inactive users, initiate the freeze-and-notify process. Set a deactivation deadline and track against it. Confirm seat recovery in Setup after deactivation.
4. For active users, profile each group by actual object access and compare against their assigned license tier. Identify groups that qualify for a Platform or Identity license downgrade. Test the downgrade in a sandbox before applying to production.
5. Run the PSL audit query. Identify PSL assignments for inactive users and for features not actively used. Unassign surplus PSLs and document the seat recovery.
6. For any user population that logs in fewer than 6 times per month, evaluate whether a Login-Based License entitlement exists and whether the economics favour migration. Calculate breakeven: (LBL monthly cost per login) vs. (per-seat monthly cost / expected logins per month).
7. Produce the license utilisation report and right-sizing recommendations. Document any license changes made, the business justification, and the projected cost impact at renewal.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] License baseline exported from Setup > Company Information for all license types and PSLs
- [ ] Active-user query run; results segmented into never-logged-in, 90-day-inactive, and active buckets
- [ ] Inactive users frozen and notified before any deactivation; seat recovery confirmed after deactivation
- [ ] License tier right-sizing validated in sandbox before production changes; profile-to-license binding confirmed
- [ ] PSL assignments audited; surplus PSLs unassigned and seat recovery documented
- [ ] Login-Based License economics evaluated for infrequent-access user populations where LBL entitlement exists
- [ ] License utilisation report and right-sizing recommendation document produced with projected cost impact

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Freezing a user does not release the license seat** — `UserLogin.IsFrozen = true` prevents the user from logging in but the license remains allocated. Only deactivating the user (`User.IsActive = false`) releases the seat. This distinction is commonly misunderstood; teams that freeze-and-stop never recover the cost.

2. **Profiles are bound to a specific license type** — You cannot change a user's license type without changing their profile. A profile created under a Salesforce (CRM) license cannot be assigned to a user with a Salesforce Platform license. If no Platform-compatible profile exists, one must be created and validated before the license migration. Attempting to assign a mismatched profile throws a validation error.

3. **LastLoginDate reflects the most recent login, not frequency** — A user who logged in once yesterday but was otherwise inactive for six months will have a recent `LastLoginDate`. Do not use `LastLoginDate` alone as a proxy for active users; supplement with `LoginHistory` for a 90-day frequency count when the cost justification requires accurate usage data.

4. **Login-Based License overage is not capped** — If the org's monthly LBL login allocation is exceeded, Salesforce charges overage at the contracted per-login overage rate. There is no automatic throttle or lockout. An LBL population that grows unexpectedly can generate a significant surprise invoice. Monitor LBL consumption via Setup > Login-Based License Usage and set an alert threshold before the monthly allocation is reached.

5. **PSL removal takes effect immediately with no grace period** — Unassigning a PSL from a user removes their access to the gated feature instantly. If the user has an active session, they may see errors mid-session. Schedule PSL unassignments during off-peak hours and confirm no active automations (flows, batch jobs, integrations) depend on PSL-gated features for the affected users.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| License utilisation report | Counts of purchased vs. assigned vs. active-user seats for each license type and PSL; identifies available headroom |
| Inactive user reclamation list | Users segmented by last login date with recommended action (freeze, deactivate, retain) and estimated seat recovery |
| License right-sizing recommendation | Per user-group analysis of actual object usage vs. current license tier, with recommended tier and sandbox validation status |
| PSL rationalisation plan | PSL-by-PSL list of assignments for inactive or non-consuming users, with unassignment status and seat recovery count |
| Login-Based License economics assessment | Breakeven analysis for candidate LBL populations comparing monthly-login cost against per-seat cost |

---

## Related Skills

- architect/multi-org-strategy — licenses are not shared across orgs; use when evaluating whether consolidation or org split affects total license cost
- security/permission-set-management — use after license right-sizing to ensure permission sets are aligned with the new license tier and do not grant access beyond what the license allows
- architect/nfr-definition-for-salesforce — use when license allocation targets need to be captured as formal operational NFRs for a new implementation
