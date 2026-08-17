# Examples — Permission Set Expiration

## Example 1: A 90-Day Contractor Elevation That Revokes Itself

**Context:** A financial-services org brings in an external Salesforce contractor for a Q3 data-migration project. The contractor needs Manage Users to create and configure the migration service accounts. The security team has already refused to add the permission to any profile, and the org's existing `PSG_PlatformAdmin_Prod` group carries a dozen other admin capabilities that are out of scope for the engagement.

**Problem:** The default org behaviour for "temporary" access is a ticket that says "remove on 30 September" and a human who forgets. The org already has three prior contractors still holding admin permission sets from engagements that ended in previous years. Nobody wants a fourth.

**Solution:**

Step 1 — Confirm the org can express an expiry at all. Retrieve `UserManagement.settings` and check the toggle:

```bash
sf project retrieve start --metadata "Settings:UserManagement"
```

```xml
<!-- force-app/main/default/settings/UserManagement.settings-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<UserManagementSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <psaExpirationUIEnabled>true</psaExpirationUIEnabled>
</UserManagementSettings>
```

If the element is absent or `false`, the Setup assignment screen shows no expiration control. `psaExpirationUIEnabled` is documented as defaulting to `false` and is available in API version 52.0 and later.

Step 2 — Build a single-purpose elevation permission set, not a reuse of the admin group:

```
Setup → Permission Sets → New
  Label:     Temp Manage Users
  API Name:  PS_Temp_ManageUsers
  License:   None
  System Permission enabled: Manage Users   (nothing else)
```

Step 3 — Confirm the permission is not already granted elsewhere. The Security Guide's rule is that "to revoke a permission, you must remove all instances of the permission from the user," so a second grant makes the expiry meaningless:

`PermissionSet` exposes "one field for each permission" using the `Permissions<PermissionName>` shape — the Object Reference notes that "the number of fields varies depending on the permissions for the organization and license type" and that you get the list from `describeSObjects()`. Confirm the exact field name against a describe before hard-coding it, then filter the user's assignments on it. Profile-owned permission sets appear in this query too, flagged by `IsOwnedByProfile`, so one query covers both grant paths:

```soql
SELECT PermissionSet.Label, PermissionSet.IsOwnedByProfile,
       PermissionSet.Profile.Name, ExpirationDate
FROM PermissionSetAssignment
WHERE AssigneeId = '005XXXXXXXXXXXXXXX'
  AND PermissionSet.PermissionsManageUsers = true
ORDER BY PermissionSet.IsOwnedByProfile DESC
```

A row with `IsOwnedByProfile = true` means the profile already grants Manage Users. Stop and fix the profile — no expiry on a permission set can remove a permission the profile hands out. Read the profile from `PermissionSet.Profile.Name`, not from the permission set's label: "For permission sets that are owned by profiles, don't use Name and Label values that are returned in a query. Name and Label values from queries can change."

The shape is the Object Reference's own. Its Associated Profiles section queries `PermissionSetAssignment` with `PermissionSet.isOwnedByProfile` precisely to specify "whether the permission is granted through a profile or permission set".

Step 4 — Assign with an expiry. Through Setup, the documented flow that offers the expiration step is the permission-set-side one: Setup → Permission Sets → select the set → **Manage Assignments** → **Add Assignments** → select the users → **Next** → set the expiration → **Assign**. The user permissions needed are Assign Permission Sets *and* View Setup and Configuration.

Through the API, write the instant explicitly rather than relying on a date picker:

```apex
PermissionSet elevation = [SELECT Id FROM PermissionSet WHERE Name = 'PS_Temp_ManageUsers' LIMIT 1];
insert new PermissionSetAssignment(
    AssigneeId       = contractorUserId,
    PermissionSetId  = elevation.Id,
    ExpirationDate   = DateTime.newInstanceGmt(2026, 9, 30, 23, 0, 0)
);
```

Step 5 — Verify and diarise:

```soql
SELECT Id, Assignee.Username, PermissionSet.Name, ExpirationDate, IsActive
FROM PermissionSetAssignment
WHERE PermissionSet.Name = 'PS_Temp_ManageUsers'
ORDER BY ExpirationDate ASC
```

**Why it works:** the expiry is a platform primitive on the assignment row, so there is no scheduled job to fail. `ExpirationDate` carries Create, Filter, Nillable, Sort, and Update — the last four are exactly what an access review needs — you can find the population, order it by end date, and extend one row without touching the grant itself. The single-purpose permission set makes the revocation real: when the assignment stops being active there is no second path to Manage Users.

**Source:** Object Reference for the Salesforce Platform v67.0 (PermissionSetAssignment); Metadata API Developer Guide v67.0 (`UserManagementSettings`); Salesforce Security Guide v67.0 (assignment procedure and user permissions).

---

## Example 2: Auditing Time-Boxed Access in an Org That Has User Access Policies Enabled

**Context:** A 4,000-user org enabled user access policies to auto-assign job-function permission set groups from the Department field. Separately, the platform team time-boxes privileged elevations with `ExpirationDate`. The internal audit team asks for "everyone who held elevated access during the last quarter and when it ended."

**Problem:** The first analyst writes one query against `PermissionSetAssignment` and reports 11 elevations. The security lead knows there were more than 30. The query is not wrong — it is incomplete, because a policy org has two different terminal states for an assignment and only one of them is visible by default.

**Solution:**

Run the population as three separate queries and union them in the report, not in SOQL:

```soql
-- A. Currently assigned with a scheduled end.
SELECT Id, Assignee.Name, Assignee.Username,
       PermissionSet.Name, PermissionSetGroup.DeveloperName,
       ExpirationDate, IsActive
FROM PermissionSetAssignment
WHERE ExpirationDate != NULL
ORDER BY ExpirationDate DESC

-- B. Assigned with no end date at all — the standing-privilege gap.
SELECT Id, Assignee.Name, PermissionSet.Name
FROM PermissionSetAssignment
WHERE ExpirationDate = NULL
  AND (PermissionSet.Name LIKE 'PS_Temp_%' OR PermissionSetGroup.DeveloperName LIKE 'PSG_Temp_%')

-- C. Revoked by a user access policy. The row still exists, and the
--    Object Reference's own retrieval example carries ALL ROWS.
SELECT Id, ExpirationDate, Assignee.Name, PermissionSet.Name,
       LastDeletedByChangeId
FROM PermissionSetAssignment
WHERE IsRevoked = true ALL ROWS
```

Query C is the one the analyst missed. The Object Reference states it plainly: "After you revoke a permission set or permission set group assignment via a user access policy, the `IsRevoked` field is updated to `true`. The `PermissionSetAssignment` record isn't deleted. If the permission set or permission set group is assigned to the user again, the `IsRevoked` field is then updated to `false`."

`LastCreatedByChangeId` and `LastDeletedByChangeId` point at `UserAccessChange`, whose `Source` field carries "the source of the user access change. For example, `UserAccessPolicyId`." That is how the report distinguishes a policy revocation from an admin's manual removal. Reading `UserAccessChange` requires View Setup and Configuration.

Join to it with a second query on the IDs — `SELECT Id, Source FROM UserAccessChange WHERE Id IN :changeIds` — rather than traversing inline. The Object Reference prints `LastCreatedByChange` as the Relationship Name for *both* change fields, so there is no documented `LastDeletedByChange` traversal to rely on; confirm the name from a describe if you want the single-query form.

Finally, pair the queries with an export of Setup Audit Trail. The Summer '26 Security Guide lists these tracked changes under Permission Sets/Groups: permission set (or group) assigned or removed for a user; and "Permission set (or group) changes to the assignment expiration date (beta)". Export on a cadence — "to download your org's complete setup history for the past 180 days, click Download. After 180 days, setup entity records are deleted."

**Why it works:** the three queries map to the three real terminal states — still assigned with a date, assigned with no date, and revoked-but-retained. `IsRevoked` is filterable, and `ALL ROWS` is the documented way to retrieve the revoked rows. The audit trail supplies the who and when that the assignment row does not carry.

**Source:** Object Reference for the Salesforce Platform v67.0 (PermissionSetAssignment usage, `IsRevoked`, `UserAccessChange`); Salesforce Security Guide v67.0 (Setup Audit Trail tracked changes and the 180-day retention).

---

## Example 3 (Failure): Expiring the Job-Function Group and Taking the Day Job With It

**What practitioners do:** A support-operations lead needs a Tier 2 agent to cover an escalation queue for two weeks. The agent is already assigned `PSG_SupportAgent_Prod`, which contains the escalation permission along with everything else the agent uses daily. Rather than build a narrow elevation set, the lead edits the existing assignment — deletes it and re-inserts it with `ExpirationDate` set to the end of the cover period.

**What goes wrong:** two failures land at once.

1. **The wrong thing expires.** When the date passes, the agent loses the whole `PSG_SupportAgent_Prod` grant, not the escalation capability. Their normal case access disappears mid-shift. The lead intended to remove one permission and removed a job function.
2. **The delete-and-insert was unnecessary and destructive.** `ExpirationDate` is an updateable field. Deleting the assignment reset the row and its creation audit; had the insert failed — a license mismatch, a validation error, a governor limit in a bulk context — the agent would have been left with no assignment at all. The Object Reference's "to update an assignment, delete an existing assignment and insert a new one" applies to the Create-only fields (`AssigneeId`, `PermissionSetId`, `PermissionSetGroupId`), not to the expiry.

**How to recover:**

```apex
// 1. Restore the permanent grant with no end date.
PermissionSetGroup psg = [
    SELECT Id, Status FROM PermissionSetGroup
    WHERE DeveloperName = 'PSG_SupportAgent_Prod' LIMIT 1
];
System.assertEquals('Updated', psg.Status,
    'Group is not recalculated; the grant will not deliver the expected permissions yet.');

insert new PermissionSetAssignment(
    AssigneeId            = agentUserId,
    PermissionSetGroupId  = psg.Id,
    ExpirationDate        = null
);

// 2. Add the escalation capability as its own time-boxed assignment.
PermissionSet escalation = [SELECT Id FROM PermissionSet WHERE Name = 'PS_Temp_CaseEscalation' LIMIT 1];
insert new PermissionSetAssignment(
    AssigneeId      = agentUserId,
    PermissionSetId = escalation.Id,
    ExpirationDate  = DateTime.newInstanceGmt(2026, 9, 14, 23, 0, 0)
);
```

**Correct approach:** attach the expiry to the *smallest grant that contains only the temporary capability*. Expire a permission set group only when the entire group is the temporary thing — a project role, a migration cutover role, an audit-window reader role. Never expire a group that is also somebody's day job.

The `PermissionSetGroup.Status` assertion in the recovery is not decoration. `Status` takes the values `Updated` (the group is current), `Outdated` (requires recalculation), `Updating` (in recalculation), and `Failed`. A grant made against a group that is not `Updated` does not deliver the aggregated permissions yet, and the assignment row reports no error about it.

**Source:** Object Reference for the Salesforce Platform v67.0 (PermissionSetAssignment field properties and usage; `PermissionSetGroup.Status`); Salesforce Security Guide v67.0 ("To revoke a permission, you must remove all instances of the permission from the user").
