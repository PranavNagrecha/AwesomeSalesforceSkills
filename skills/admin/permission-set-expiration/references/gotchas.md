# Gotchas — Permission Set Expiration

Non-obvious Salesforce platform behaviours that cause real production problems when access is time-boxed.

## Gotcha 1: The Expiration Control Is Off by Default and Lives on a Page Nobody Visits

**What happens:** An admin opens a permission set, clicks Manage Assignments, adds a user, and sees no expiration option anywhere. They conclude the org is on an edition that lacks the feature, or that the feature was never released, and fall back to a calendar reminder. Meanwhile the `ExpirationDate` field is fully functional through the API in the same org.

**Why:** The UI and the field are gated separately. `UserManagementSettings.psaExpirationUIEnabled` is described as indicating "if admins can use an updated user interface that includes an assignment expiration for permission sets and permission set groups (true) or not (false)," and its documented default value is `false`. The field itself has been on `PermissionSetAssignment` since API version 52.0 regardless. The toggle lives on the **User Management Settings** Setup page — a page most admins never open, because everything else they need is under Users, Profiles, or Permission Sets.

**When it occurs:** Any org that has not deliberately turned the setting on. It is especially common in orgs that were created before the setting existed and have never run a settings audit, and in sandboxes refreshed from such an org.

**How to avoid:** Treat the toggle as a prerequisite, not a preference, and check it in metadata rather than by clicking:

```bash
sf project retrieve start --metadata "Settings:UserManagement"
grep -c psaExpirationUIEnabled force-app/main/default/settings/UserManagement.settings-meta.xml
```

Deploy it as part of the org's baseline settings. Retrieve the existing file first and add the element — there is only one settings file per settings component, so a two-line deploy is not a merge.

**Read the evidence precisely.** The gate claim rests on one sentence in the Metadata API guide — the setting "indicates if admins can use an updated user interface that includes an assignment expiration." The Security Guide's own assignment procedure prints the expiration step unconditionally and never mentions the setting, so the two documents do not corroborate each other on what a false value hides. Check the setting before promising an admin a click trail, and if the control turns out to be present with the setting false, trust the org over both documents. `[STALE-RISK: neither guide states outright which Setup controls disappear when psaExpirationUIEnabled is false — re-verify in-org.]`

**Source:** Metadata API Developer Guide v67.0 — `UserManagementSettings`. Object Reference v67.0 — `PermissionSetAssignment.ExpirationDate`. Salesforce Security Guide v67.0, p.39 — "Assign a Permission Set to Multiple Users", step 5.

---

## Gotcha 2: The Two Setup Assignment Paths Are Not Equivalent

**What happens:** One admin sets expirations routinely; another swears the option does not exist. Both are in the same org with the same permissions. The difference is which screen they started from.

**Why:** The Security Guide documents two separate procedures. *Assign a Permission Set to Multiple Users* runs Setup → Permission Sets → select the set → Manage Assignments → Add Assignments → select users → **Next**, and at that point: "Optionally, select an expiration date for the user assignment to expire." *Assign Permission Sets to a Single User* runs Setup → Users → select a user → Permission Set Assignments related list → Edit Assignments → Add → Save, and has no expiration step in the documented procedure at all. Admins who habitually provision from the user record land on the path without the control.

**When it occurs:** During onboarding and ad-hoc grants, which is exactly when a temporary elevation is most likely to be created and least likely to be reviewed.

**How to avoid:** Standardise the runbook on the permission-set-side path for anything time-boxed, and state the click trail explicitly in the request ticket rather than leaving it to habit. For bulk or scripted grants, use the API and skip the question entirely. `[STALE-RISK: the Setup UI for assignments is under active change — re-read the "Assign a Permission Set to Multiple Users" and "Assign Permission Sets to a Single User" procedures in the current Security Guide before publishing a click trail.]`

**Source:** Salesforce Security Guide v67.0, Summer '26, pages 38–39 — "Assign Permission Sets to a Single User" and "Assign a Permission Set to Multiple Users".

---

## Gotcha 3: Expiry Is Not Deletion — the Assignment Row Survives

**What happens:** A compliance report counts rows in `PermissionSetAssignment` to answer "who currently holds this elevated permission set?" It returns the same number the week after an elevation expired as the week before. The report is reading the existence of the assignment, and the assignment still exists.

**Why:** The platform models an assignment's end as a *state*, not as an absence. `IsActive` — "indicates whether the assignment is active (`true`) or not (`false`)" — is the field that carries it, and it is neither createable nor updateable: its properties are Defaulted on create, Filter, Group, Sort. The platform owns it; you can only filter on it. The Object Reference also documents its default as `false`, which is a poor thing to reason from — do not infer the state, query it. A query whose only predicate is "an assignment row exists for this user and this permission set" was a correct liveness test when every assignment was permanent, and stops being one the day the org adopts expiry.

**When it occurs:** Any reporting, integration, or Apex written before the org adopted expiration dates. Nothing about turning time-boxing on invalidates those queries loudly.

**How to avoid:** Audit every query against `PermissionSetAssignment` in the codebase and in reporting when the org turns on time-boxing, and add the state filter. Add `ALL ROWS` to the lapsed-assignment query as well — see the retrieval caveat below.

```soql
-- Live grants only
SELECT Id, Assignee.Username, PermissionSet.Name, ExpirationDate
FROM PermissionSetAssignment
WHERE PermissionSet.Name = 'PS_Temp_ManageUsers'
  AND IsActive = true

-- Everything that has already lapsed. ALL ROWS is defensive here — see below.
SELECT Id, Assignee.Username, PermissionSet.Name, ExpirationDate
FROM PermissionSetAssignment
WHERE PermissionSet.Name = 'PS_Temp_ManageUsers'
  AND IsActive = false ALL ROWS
```

**Retrieval caveat — verify this one in your org.** The Object Reference documents `ALL ROWS` for exactly one case: assignments revoked by a user access policy, where "the `PermissionSetAssignment` record isn't deleted." It says nothing either way about whether a *date-expired* assignment is returned by an ordinary query. `skills/security/privileged-access-management` states that expired assignments are treated as soft deletes and need `ALL ROWS` to retrieve; that claim rests on Salesforce Help, which cannot be fetched and has not been re-verified here. Both readings are consistent with the field metadata, so write the query with `ALL ROWS` — it is correct under either behaviour — and confirm the row count against a known expired assignment in the target org before signing off an audit. `[STALE-RISK: re-verify whether an ordinary SOQL query returns date-expired PermissionSetAssignment rows; the answer decides whether ALL ROWS is required or merely harmless.]`

**Source:** Object Reference for the Salesforce Platform v67.0 — `PermissionSetAssignment.IsActive`, `ExpirationDate`, and the "Revoked Assignments from User Access Policies" usage note. Conflict logged in `well-architected.md`.

---

## Gotcha 4: A Policy-Revoked Assignment Is Invisible Without `ALL ROWS`

**What happens:** In an org with user access policies enabled, an auditor asks for every elevation that ended last quarter. The query returns a fraction of them. Re-running it with different date filters changes nothing, because the missing rows are not the ones the `WHERE` clause is rejecting.

**Why:** Policy revocation is a distinct terminal state from date expiry, and the only retrieval pattern the Object Reference publishes for it carries `ALL ROWS` — the clause that reaches rows an ordinary query does not return. The guide states the behaviour and prints the query; it does not spell out the mechanism, so treat "invisible without `ALL ROWS`" as the documented retrieval contract rather than as a described query-engine rule. The Object Reference: "After you revoke a permission set or permission set group assignment via a user access policy, the `IsRevoked` field is updated to `true`. The `PermissionSetAssignment` record isn't deleted. If the permission set or permission set group is assigned to the user again, the `IsRevoked` field is then updated to `false`." `IsRevoked` exists only when user access policies are enabled, and is available in API version 57.0 and later — so the same query text behaves differently in two orgs depending on a settings flag.

**When it occurs:** Only in policy orgs, which makes it worse: the audit query is usually developed in a sandbox where policies were never enabled, passes review, and then under-reports in production.

**How to avoid:** Branch the audit on `userAccessPoliciesEnabled` and run the revoked population as its own query:

```soql
SELECT Id, ExpirationDate, Assignee.Name, PermissionSet.Name,
       LastDeletedByChangeId
FROM PermissionSetAssignment
WHERE IsRevoked = true ALL ROWS
```

Then resolve the change records in a second query rather than traversing the relationship inline:

```soql
SELECT Id, Source FROM UserAccessChange WHERE Id IN :changeIds
```

`UserAccessChange.Source` records "the source of the user access change. For example, `UserAccessPolicyId`," which separates a policy revocation from an admin's manual removal. Reading `UserAccessChange` requires View Setup and Configuration.

**Do not guess the relationship name.** The Object Reference lists the Relationship Name for *both* `LastCreatedByChangeId` and `LastDeletedByChangeId` as `LastCreatedByChange` — on `PermissionSetAssignment` and on `PermissionSetLicenseAssign` alike. A traversal spelled `LastDeletedByChange.Source` appears nowhere in the guide. Select the ID and join in a second query, or confirm the traversal name from `describeSObjects()` in the target org before writing it into a report.

**Source:** Object Reference for the Salesforce Platform v67.0 — `PermissionSetAssignment` Usage, "Revoked Assignments from User Access Policies"; `UserAccessChange`.

---

## Gotcha 5: Extending an Expiry Does Not Require Delete-and-Insert — but Retargeting Does

**What happens:** A contractor's engagement is extended by a quarter. The admin reads "to update an assignment, delete an existing assignment and insert a new one" in the Object Reference, deletes the assignment, and re-inserts it. In a bulk renewal script the insert half fails partway — a license mismatch on one user, a governor limit on another — and a batch of people are left with no assignment at all, mid-quarter, with the original grant already gone.

**Why:** That instruction is about the Create-only fields. `AssigneeId`, `PermissionSetId`, and `PermissionSetGroupId` all carry Create, Filter, Group, Sort — no Update — so changing *who* is assigned or *what* they are assigned genuinely is a delete plus an insert. `ExpirationDate` is the exception: its properties are Create, Filter, Nillable, Sort, **Update**. Extending an expiry is a single-field update on the existing row, and it keeps the original creation audit intact.

**When it occurs:** Renewal season. It is a scripted, bulk operation, which is precisely when a partial failure is expensive and least visible.

**How to avoid:** Update the field. Reserve delete-and-insert for the cases where a Create-only field must change, and when you do need it, insert first where the platform allows it or wrap the operation so a failed insert restores the prior state. Also check licences before a bulk re-insert: the Object Reference's rule is that "when assigning a permission set, if the `PermissionSet` has a `UserLicenseId`, its `UserLicenseId` and the `Profile` `UserLicenseId` must match" — note that this usage text still names `UserLicenseId`, which the same document describes as deprecated and only available up to API version 37.0 in favour of `LicenseId` (API version 38.0 and later). Query `PermissionSet.LicenseId` when you write the pre-flight check.

**Source:** Object Reference for the Salesforce Platform v67.0 — `PermissionSetAssignment` field properties and Usage; `PermissionSet.LicenseId`.

---

## Gotcha 6: An Expiry Cannot Revoke a Permission That Is Granted Twice

**What happens:** A time-boxed elevation lapses exactly on schedule, `IsActive` flips, the audit trail records it — and the user still has the capability. Everything about the expiry worked. The permission simply was not exclusive to that assignment.

**Why:** The Security Guide states the rule without qualification: "To revoke a permission, you must remove all instances of the permission from the user." Permissions aggregate across the profile, every assigned permission set, and every permission set group. An expiry retires one grant; it does not sweep the others. This is the single most common reason a time-boxing programme produces no measurable reduction in privilege.

**When it occurs:** Most often when the elevated permission is one that also appears in a broad job-function permission set — Export Reports, Modify All Data on a specific object, View All Users — or when the org's profiles were never trimmed after a permission-set migration.

**How to avoid:** Prove exclusivity *before* granting, not after expiring. Filter the user's assignments on the `Permissions<PermissionName>` boolean and confirm exactly one row comes back:

```soql
SELECT PermissionSet.Label, PermissionSet.IsOwnedByProfile, PermissionSet.Profile.Name
FROM PermissionSetAssignment
WHERE AssigneeId = '005XXXXXXXXXXXXXXX'
  AND PermissionSet.PermissionsManageUsers = true
```

The Object Reference describes these as "one field for each permission … the number of fields varies depending on the permissions for the organization and license type," and directs you to `describeSObjects()` for the list — so confirm the field name from a describe rather than guessing it. A returned row with `IsOwnedByProfile = true` means the profile grants it and no permission-set expiry will ever remove it.

Key the report on `PermissionSet.ProfileId` or `PermissionSet.Profile.Name`, not on the label. The Object Reference is explicit: "For permission sets that are owned by profiles, don't use Name and Label values that are returned in a query. Name and Label values from queries can change." The `Label` column above is for a human reading the result, not for a join or a stored identifier.

**Source:** Salesforce Security Guide v67.0 — "User Permissions". Object Reference v67.0 — `PermissionSet` `Permissions<PermissionName>` and `IsOwnedByProfile`.

---

## Gotcha 7: Some Grant Mechanisms Have No Expiry at All, and the Gap Is Silent

**What happens:** An access design time-boxes the permission set but not the permission set *license* that the permission set depends on, or not the public group that carries a sharing grant. The elevation "expires" while the underlying capability or visibility remains.

**Why:** The expiry lives on `PermissionSetAssignment` and nowhere else in this family of objects.

| Object | Has `ExpirationDate`? | Supported calls |
|---|---|---|
| `PermissionSetAssignment` | Yes (API version 52.0 and later) | create, delete, describeSObjects, query, retrieve, **update** |
| `PermissionSetLicenseAssign` | **No** | create, delete, describeSObjects, query, retrieve — no update |
| `GroupMember` | **No** (two fields: `GroupId`, `UserOrGroupId`) | create, delete, describeSObjects, getDeleted, getUpdated, query, retrieve |

`MutingPermissionSet` "is used in conjunction with `PermissionSetGroup`" — it is a component of a group, not something assigned to a user, so there is no assignment row to expire. A profile is a lookup on the User record, with no assignment object either. User access policies can `Grant` or `Revoke` a `PackageLicense`, `Group`, or `Queue`, but the `UserAccessPolicyAction` type carries only `action`, `target`, and `type` — no date.

**When it occurs:** In vertical clouds and add-on products, where the meaningful capability is gated by a permission set license rather than by the permission set alone.

**How to avoid:** For each temporary grant, write down every mechanism the capability depends on and mark which ones can expire. Anything in the "no" column needs a named human owner and a dated task, because the platform will not do it. Do not paper over the gap with a scheduled job that pretends to be an expiry — see `llm-anti-patterns.md` Anti-Pattern 1.

**Source:** Object Reference for the Salesforce Platform v67.0 — `PermissionSetLicenseAssign`, `GroupMember`, `MutingPermissionSet`. Metadata API Developer Guide v67.0 — `UserAccessPolicyAction`.

---

## Gotcha 8: The Audit Trail Entry for Expiration Changes Is Still Labelled Beta

**What happens:** A control owner designs an evidence pack around Setup Audit Trail entries for expiration-date changes, only to find the entry missing, inconsistent, or unavailable in the org they are auditing.

**Why:** The Summer '26 Security Guide's list of Setup Audit Trail tracked changes under Permission Sets/Groups reads, verbatim: "Permission set (or group) changes to the assignment expiration date (beta)". The adjacent entries in the same list — "Permission set (or group) assigned or removed for a user", "Permission set group recalculated", "Session activation changed by admin" — carry no such marker. Building a control on a beta line item is a design risk that will not announce itself.

**When it occurs:** During SOX, ISO 27001, or internal audit evidence design, typically months after the elevation programme started, when the evidence is needed retrospectively and it is too late to change the approach.

**How to avoid:** Verify in the target org that the entry actually appears before you commit to it as the control's evidence, and keep a second source — the assignment rows themselves, exported on a schedule. Whatever the source, export on a cadence: "to download your org's complete setup history for the past 180 days, click Download. After 180 days, setup entity records are deleted." An annual access review that reaches back further than 180 days will find nothing. `[STALE-RISK: check whether the "(beta)" marker has been removed from the Setup Audit Trail tracked-changes table in the current Security Guide.]`

**Source:** Salesforce Security Guide v67.0, Summer '26 — "Monitor Setup Changes with Setup Audit Trail", tracked changes table and the download/retention note.

---

## Gotcha 9: Session-Based Permission Sets Lose Their Activation Requirement Inside a Group

**What happens:** An architect designs the tightest possible elevation — a session-based permission set, so the grant dies with the session rather than at a wall-clock time. Then, for administrative convenience, someone folds it into a permission set group alongside the user's other access. The session requirement quietly stops applying.

**Why:** The Object Reference attaches an explicit note to `SessionPermSetActivation`: "If you include session-based permission sets in a permission set group, the permissions in them don't require session-based activation for users assigned to the group." `PermissionSet.HasActivationRequired` and `PermissionSetGroup.HasActivationRequired` are separate flags — the group-level one is documented as available in API version 53.0 and later, the permission-set-level one carries no version note — and membership does not propagate the member's requirement to the group.

**When it occurs:** During permission set group consolidation projects, which are usually motivated by reducing the number of assignments — the same instinct that makes folding a session-based set into a group look like tidying up.

**How to avoid:** Keep session-based permission sets out of groups, or set `HasActivationRequired` on the group itself and understand that you have moved the control to the group boundary. When comparing a session-based grant against an `ExpirationDate`, be clear about what each buys: the date bounds a window the user may have walked away from; the session bounds actual presence. Also confirm `PermissionSetGroup.Status` is `Updated` before relying on a group grant at all — `Outdated`, `Updating`, and `Failed` all deliver less than the assignment implies, with no error on the assignment row.

**Source:** Object Reference for the Salesforce Platform v67.0 — `SessionPermSetActivation` Note; `PermissionSet.HasActivationRequired`; `PermissionSetGroup.HasActivationRequired` and `Status`.

---

## Gotcha 10: Integration and Guest Users Cannot Be Time-Boxed Through the UI

**What happens:** A security review requires that an integration user's elevated permission set be time-boxed for a migration window. The admin opens the permission set, clicks Manage Assignments, and cannot find the user.

**Why:** The Security Guide attaches the same note to both procedures that run through Manage Assignments — *Assign a Permission Set to Multiple Users* and *Remove User Assignments from a Permission Set*: "Certain types of users, such as guest, Self-Service, integration, and system users, aren't available in the Manage Assignments page. To view or manage these users, use the `PermissionSetAssignment` API object." The exclusion is by user type, not by permission. The user-record-side *Assign Permission Sets to a Single User* procedure carries no such note — and no expiration step either, per Gotcha 2.

**When it occurs:** Exactly when it matters most — integration users are the accounts most likely to accumulate broad, permanent, unreviewed permissions, and the ones an auditor asks about first.

**How to avoid:** Script these grants. Access to `PermissionSetAssignment` requires View Setup and Configuration, Assign Permission Sets, or Manage User, so the running identity needs one of the three:

```apex
insert new PermissionSetAssignment(
    AssigneeId      = integrationUserId,
    PermissionSetId = migrationElevationId,
    ExpirationDate  = DateTime.newInstanceGmt(2026, 10, 15, 22, 0, 0)
);
```

Record the grant in the change ticket, because there is no Setup screen a reviewer can be pointed at to see it.

**Source:** Salesforce Security Guide v67.0 — Note on "Assign a Permission Set to Multiple Users" and "Remove User Assignments from a Permission Set". Object Reference v67.0 — `PermissionSetAssignment` Special Access Rules.
