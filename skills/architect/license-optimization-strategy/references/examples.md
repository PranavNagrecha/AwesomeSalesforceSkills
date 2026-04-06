# Examples — License Optimization Strategy

## Example 1: Inactive User Reclamation Audit

**Context:** A 500-seat Enterprise org is approaching its license ceiling 8 months into a 12-month contract. The admin team suspects a significant number of users were created during an onboarding wave and never actively used the system, or have since left the company but were not formally offboarded.

**Problem:** The org has 487 of 500 Salesforce (CRM) licenses in use. Without reclamation, the team will need to purchase additional licenses 4 months early, adding unplanned cost. A simple check of the User list in Setup is not sufficient because `IsActive = true` does not indicate recent usage.

**Solution:**

```soql
-- Step 1: Find users who have never logged in
SELECT Id, Name, Username, CreatedDate, Profile.UserLicense.Name
FROM User
WHERE IsActive = true
  AND LastLoginDate = null
ORDER BY CreatedDate ASC

-- Step 2: Find users inactive for 90+ days
SELECT Id, Name, Username, LastLoginDate, Profile.UserLicense.Name
FROM User
WHERE IsActive = true
  AND LastLoginDate < LAST_N_DAYS:90
ORDER BY LastLoginDate ASC NULLS FIRST
```

```apex
// Step 3: Freeze inactive users in bulk via UserLogin
// (run in Anonymous Apex or a batch, targeting confirmed-inactive user Ids)
List<Id> inactiveUserIds = new List<Id>{
    '005xx000001aaa', '005xx000001bbb' // populate from SOQL results
};

List<UserLogin> loginsToFreeze = [
    SELECT Id, IsFrozen
    FROM UserLogin
    WHERE UserId IN :inactiveUserIds
];

for (UserLogin ul : loginsToFreeze) {
    ul.IsFrozen = true;
}
update loginsToFreeze;
```

After a 14-day notification period, users who do not respond are deactivated by setting `User.IsActive = false`. The org recovers 43 seats, bringing active allocation to 444 of 500 — well within the ceiling for the remainder of the contract.

**Why it works:** Splitting reclamation into a freeze-then-deactivate workflow protects against accidental deactivation of users on leave. Querying `LastLoginDate = null` separately from `LastLoginDate < LAST_N_DAYS:90` prioritises the highest-confidence targets (never-logged-in users) before moving to activity-based inferences.

---

## Example 2: Platform License Right-Sizing for an Internal IT App

**Context:** A manufacturing company built a custom equipment-tracking app on Salesforce. The app uses custom objects only: `Equipment__c`, `MaintenanceSchedule__c`, `ServiceTicket__c`. 120 internal technicians use this app daily but never touch standard CRM objects (Accounts, Contacts, Opportunities, Cases). All 120 users are currently on full Salesforce (CRM) licenses.

**Problem:** The cost difference between a full CRM license and a Salesforce Platform license is substantial at enterprise volume. The company is paying for CRM object access that 120 users never use.

**Solution:**

1. Verify object access by auditing the profiles assigned to the 120 technicians:

```soql
-- Check which standard CRM objects the technician profile has read access to
SELECT Parent.Name, SObjectType, PermissionsRead
FROM ObjectPermissions
WHERE Parent.ProfileId IN (
    SELECT ProfileId FROM User
    WHERE Profile.Name = 'Field Technician'
)
  AND PermissionsRead = true
  AND SObjectType IN ('Lead', 'Opportunity', 'Case', 'Contract')
```

If the query returns zero rows (or returns rows for objects not actually used in any page layout or app), the group is a clean Platform license candidate.

2. In a sandbox, clone the `Field Technician` profile and assign it to the Salesforce Platform license (profile User License field). Confirm the custom app loads correctly, custom objects are accessible, and no referenced standard CRM objects appear in navigation.

3. In production, create the Platform-compatible profile and migrate the 120 users.

**Why it works:** The Salesforce Platform license covers custom objects, Tasks, Events, and Chatter. For a purely custom-object app, it satisfies all functional requirements at a meaningfully lower cost. Validating in sandbox before production prevents access regressions.

---

## Example 3: Login-Based License Evaluation for Partner Users

**Context:** An org has 200 partner users accessing a Partner Community portal. The portal is used for deal registration — partners log in to submit and check status on deals. Usage analysis from `LoginHistory` shows that most partners log in 2–3 times per month.

**Problem:** All 200 partners are on named Partner Community licenses (per-seat). At the contracted per-seat rate, the monthly cost is fixed regardless of actual login volume. With average logins at 2–3 per month per user, the economics may favour Login-Based Licensing.

**Solution:**

```soql
-- Query 90 days of login history for partner users to establish average monthly frequency
SELECT UserId, COUNT(Id) loginCount,
       CALENDAR_MONTH(LoginTime) loginMonth,
       CALENDAR_YEAR(LoginTime) loginYear
FROM LoginHistory
WHERE UserId IN (
    SELECT Id FROM User
    WHERE IsActive = true
      AND Profile.UserLicense.Name = 'Partner Community'
)
  AND LoginTime = LAST_N_DAYS:90
GROUP BY UserId, CALENDAR_MONTH(LoginTime), CALENDAR_YEAR(LoginTime)
ORDER BY loginCount DESC
```

Aggregate results: median logins per user per month = 2.4. At the contracted LBL per-login price vs. the per-seat price, the breakeven is approximately 5 logins/month/user. At 2.4 average logins, LBL would reduce monthly partner license cost by approximately 52%.

**Why it works:** LBL is economically favourable when users log in fewer times per month than the per-seat / per-login breakeven. The `LoginHistory` query provides empirical data to support the business case rather than relying on assumptions. Always confirm that the Partner Community LBL entitlement is available from the AE before building a migration plan.

---

## Anti-Pattern: Bulk Deactivating Users Without Checking Record Ownership

**What practitioners do:** Run a query of all users who have not logged in for 180 days and mass-deactivate them in a data loader operation to quickly recover license seats.

**What goes wrong:** Deactivated users can no longer be assigned as record owners, but their existing owned records are NOT automatically reassigned. Workflows, assignment rules, and queues that reference deactivated users by name fail silently or throw errors. Approval processes where deactivated users are approvers stall. Reports filtering by owner show records under a user who can no longer log in, causing confusion in pipeline reviews.

**Correct approach:** Before deactivating, run a query to identify records owned by each candidate user (`SELECT Id FROM Account WHERE OwnerId = :userId`). For records that need active ownership, reassign before deactivating. Review approval processes and assignment rules referencing the user. Freeze first, allow a notification period, then deactivate.
