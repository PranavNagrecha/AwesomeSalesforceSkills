# Gotchas — User Management

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Changing a User's License Clears the Profile Field

**What happens:** When you change a user's User License type (e.g., from Salesforce Platform to Salesforce), the Profile field is cleared and must be reselected. If you save without re-selecting a profile, the user receives an error and cannot log in.

**When it occurs:** Any time the User License field is changed on an existing user record. Salesforce enforces license-profile compatibility — profiles are linked to a specific license type, so a profile valid for Salesforce Platform is not valid for the full Salesforce license.

**How to avoid:** After changing the license, always scroll down to the Profile field and explicitly select a new compatible profile before saving. If the user is active, check their access immediately after the change by logging in as them (Setup → Login As) to confirm they can see the expected tabs and objects.

---

## Gotcha 2: Deactivating a User Does Not Remove Them from Queues or Active Approval Steps

**What happens:** After deactivation, the user remains as a member of any queue they belonged to. Cases and leads continue routing to those queues. Active approval process steps that required the deactivated user's approval become permanently stuck — the request can neither advance nor be resubmitted until an admin manually reassigns the approval actor.

**When it occurs:** Every time a user is deactivated without prior cleanup. Particularly impactful when the user was a solo approver on a business-critical process (expense reports, contracts, purchase orders).

**How to avoid:** Before deactivating:
1. Search all Approval Processes for the user as a designated approver
2. Query `ProcessInstanceWorkitem` for pending items assigned to this user
3. Remove the user from all queues (Setup → Queues)
4. Use the "Manage Users" data export or a SOQL query to find all records owned by the user and mass-reassign them
5. Freeze first while you complete this checklist — deactivate only after all items are resolved

---

## Gotcha 3: Login Hours Restrict New Logins but Do Not Terminate Existing Sessions

**What happens:** A user who is already logged in when the end-of-login-hours boundary occurs (e.g., 6 PM) is NOT automatically logged out. Their session remains fully active. The restriction only prevents new logins outside the allowed window.

**When it occurs:** Whenever Login Hours are configured on a profile with the expectation that this will enforce an end-of-day logout. Security teams who configure this setting often assume it acts like an automatic session timeout.

**How to avoid:** To enforce actual session termination at the hour boundary, also configure Setup → Session Settings → "Force logout on session timeout" and set an appropriate session timeout value. Alternatively, use a Named User MFA policy and require reauthentication at the start of each session. Login Hours alone are not sufficient for a hard session cutoff.

---

## Gotcha 4: Chatter Free Users Cannot Be Upgraded to Standard Licenses In-Place

**What happens:** A Chatter Free user who later needs full Salesforce access cannot simply have their license changed to Salesforce. You must deactivate (or delete) the Chatter Free user record and create a brand-new user record with the Salesforce license. This creates a gap in the user's activity history — their Chatter posts may reference the old user record.

**When it occurs:** When a contractor or external collaborator initially gets a Chatter Free account and is later hired full-time. Admins attempt to "upgrade" the license in-place and are blocked by the platform.

**How to avoid:** If there is any possibility a Chatter Free user will need CRM access in the future, provision a full Salesforce license from the start. If the cost is a concern, deactivate them using the full license (which stops consuming it) rather than provisioning Chatter Free. This preserves the user record and allows reactivation with the full license later without data loss.

---

## Gotcha 5: A User Without a Role Cannot See Other Users' Records Even If OWD Is Public Read/Write

**What happens:** A user with no role assigned can see all records when OWD is set to Public Read/Write, but in orgs where OWD is Private or Public Read Only, a user without a role cannot benefit from the role hierarchy — they see only records they own. This is counterintuitive because the user may have a profile with full object permissions.

**When it occurs:** Any time a new user is created without a role in an org where OWD is not Public Read/Write for important objects (Accounts, Opportunities, Cases). Managers who need to see their team's pipeline find that even with Modify All on Opportunities, they cannot navigate to the Opportunities of their direct reports.

**How to avoid:** During user provisioning, always check the org's OWD settings for the objects the user will work with. If OWD is Private or Public Read Only, assign a role. In orgs with strict private sharing, "no role" is equivalent to "sees only own records" for all role-hierarchy-enabled objects.

---

## Gotcha 6: A Deactivated User Frees the User Licence but Keeps Consuming Every Permission Set Licence

**What happens:** Deactivation returns the seat to the user-licence pool but does not return the
permission set licences. The Object Reference draws the distinction in the field descriptions
themselves: `UserLicense.UsedLicenses` is "the number of user licenses that are assigned to **active
users** in the organization," while `PermissionSetLicense.UsedLicenses` is "the number of this
permission set license that are **currently assigned to users**" — no active-user qualifier. Twenty
leavers over a year quietly hold twenty Einstein or CPQ PSLs, and the next hire who needs one is
blocked while Setup shows the user licences as plentiful.

**When it occurs:** Every deactivation of a user who held a `PermissionSetLicenseAssign` row. It is
invisible in the usual place people look — Company Information shows user licences, and the PSL
count only tells you the total, not who is holding it.

**How to avoid:** Make deleting `PermissionSetLicenseAssign` rows an explicit offboarding step, not
a consequence of deactivation. `PermissionSetLicenseAssign` supports `create()` and `delete()` and
notably **not** `update()` — there is no "revoke" flag to set, you delete the row. The reclamation
query is in `references/metadata-examples.md` section 7. Do not filter on
`UserLicense.UsedLicenses` while auditing: that field "isn't filterable in API version 64.0 or later
when using it in a `WHERE` clause in a SOQL query. Instead, you have to process the data after
fetching all the records."

---

## Gotcha 7: Freezing Is an Update to a Different Object, and That Object Has No Insert

**What happens:** Freeze does not live on `User`. It is `UserLogin.IsFrozen`, and `UserLogin`
supports only `describeSObjects()`, `query()`, `retrieve()` and `update()`. There is no `create()`,
no `delete()`, no `upsert()`. Worse, `UserLogin.UserId` is documented as "This field can't be
updated," so you cannot address the row by the User Id you already have — a bulk freeze keyed on
`005…` Ids fails every row. You must query `UserLogin` for the `05D…` Id first, then update that.

**When it occurs:** Any scripted or bulk freeze. The single-user Setup button hides all of this,
so the pattern only bites the first time someone automates an offboarding runbook.

**How to avoid:** Two-step every time: `SELECT Id, UserId FROM UserLogin WHERE UserId IN (…)`, then
update the returned `Id` with `IsFrozen = true`. The Object Reference's own guidance is "to freeze
or unfreeze multiple users, use Data Loader." Note the asymmetry on the neighbouring field:
`IsPasswordLocked` — "From the API, you can set this field to false, but not true." You can unlock
an account by API; you cannot lock one.

---

## Gotcha 8: Blank CSV Cells Do Not Clear Fields Under Bulk API — You Need `#N/A`

**What happens:** An offboarding update that blanks `UserRoleId`, `ManagerId` or
`FederationIdentifier` appears to succeed and changes nothing. The Data Loader guide states that the
Insert Null Values option "isn't available if either the Use Bulk API or the Use Bulk Api 2.0 option
is selected. Empty field values are ignored when you update records using either API. To set a field
value to null when either API option is selected, use a field value of `#N/A` in the import CSV
file." The load reports 100% success because ignoring a field is not an error.

**When it occurs:** Any Bulk API or Bulk API 2.0 update intended to *remove* a value rather than
replace it — pulling a leaver out of the role hierarchy, detaching a stale SSO federation id,
clearing a manager chain before a reorg. SOAP-mode Data Loader with Insert Null Values ticked
behaves differently, which is why the same CSV works for one admin and not another.

**How to avoid:** Write the literal string `#N/A` in the cell you want nulled, and verify with a
follow-up query rather than trusting the success count. When the intent is to clear a *lookup* on
many users at once, re-query the field afterwards — a silent no-op here leaves a departed user
sitting in the role hierarchy where they still confer visibility upward.

---

## Gotcha 9: Mass-Deactivating Users Who Follow Each Other Destroys Their Chatter Subscriptions Permanently

**What happens:** Single deactivation is reversible for Chatter follows: "If you deactivate a user,
any `EntitySubscription` where the user is associated with the `ParentId` or `SubscriberId` field,
meaning all subscriptions both to and from the user, are soft deleted. If the user is reactivated,
the subscriptions are restored." But deactivate several mutually-following users in one operation
and "their subscriptions are hard deleted. In this case, the user-to-user `EntitySubscription` is
deleted twice (double deleted). Such subscriptions can't be restored upon user reactivation."

**When it occurs:** A layoff, a divestiture, or an org-cleanup sweep that deactivates a whole team in
one Data Loader run — precisely the teams whose members follow each other. It also occurs when a
mistaken bulk deactivation is rolled back: the users come back, the follow graph does not.

**How to avoid:** If any of the batch might be reactivated, deactivate in single-record operations
rather than one bulk job, or export `EntitySubscription` for the affected user set first so the
graph can be rebuilt. Relatedly, the API path is not equivalent to the UI path for teams either:
"The user interface provides options to auto-remove a user from teams, but the removal isn't
supported in API" — a Data Loader deactivation silently leaves account and case team memberships in
place that clicking through Setup would have cleared.

---

## Gotcha 10: Login Hours Are Minutes Since Midnight, and Omitting the Element Does Not Remove Them

**What happens:** Two independent traps in the same `Profile` element. First, `loginHours` values are
not times — "Valid values for Start: the number of minutes since midnight. Must be evenly divisible
by 60 (full hours). For example, 300 is 5:00 AM," and likewise "1020 is 5:00 PM" for End. A deploy
carrying `<mondayStart>900</mondayStart>` meaning 9 AM actually sets 3:00 PM, and any value not
divisible by 60 is rejected outright. Second, removing the restriction by deleting the element from
the profile file does nothing: "To delete login hour restrictions from a profile that previously had
them, you must explicitly include an empty `loginHours` tag without any start or end times."

**When it occurs:** The minutes conversion bites on the first hand-authored profile. The removal
trap bites later and harder — a security exception is approved, the admin strips `<loginHours>` from
the profile source, the deploy reports success, and the profile's users are still locked out of the
org at 6 PM because a metadata deploy of a Profile is a merge, not a replacement.

**How to avoid:** Convert deliberately (07:00 = 420, 22:00 = 1320) and let the checker in
`scripts/` catch non-multiples of 60. To lift a restriction, deploy `<loginHours/>` — an explicitly
empty element — and then confirm in Setup rather than trusting the deploy result. If a start time is
set for a day its end must be set too, and start cannot exceed end. The same merge semantics apply
to `loginIpRanges`: omit them and the existing allowlist survives.

---

## Gotcha 11: Users Cannot Be Deleted, and Usernames Are Never Recycled

**What happens:** "You can't delete a user in the user interface or the API," and the guide's own
conclusion is blunt: "Because users can never be deleted, we recommend that you exercise caution
when creating them." The username that user occupies is gone for good — `Username` "must be unique
across all organizations. If you try to create or update a User with a duplicate value for this
field, the operation is rejected." A typo'd username in a provisioning load is therefore permanent
org debt: the row cannot be removed, and the correct username is now taken by the broken record if
the typo happened to be the value you wanted. Contrast `Group`, whose Usage section says outright
"Unlike users, this object can be deleted."

**When it occurs:** Test-user sprawl in sandboxes, mistyped bulk loads, and any provisioning script
that generates usernames from a template without a uniqueness suffix. It also occurs when a sandbox
refresh is expected to "clean up" test users — it does not; it clones them.

**How to avoid:** Validate the CSV before the load, not after — duplicate usernames within the file
and non-email-shaped usernames are exactly what `scripts/check_user_management.py --csv` exists to
catch. In tests, build usernames from `DateTime.now().getTime()` so a cloned org cannot collide. And
treat a provisioning load as irreversible: `allOrNone: true` on the REST path, because a partial
success leaves you unable to distinguish "this username failed" from "this username succeeded and
your retry is now failing on the duplicate."
