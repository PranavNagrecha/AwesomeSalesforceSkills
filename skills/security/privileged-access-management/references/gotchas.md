# Gotchas — Privileged Access Management (PAM)

## Gotcha 1: A session-based permission set loses its activation requirement inside a group

**What happens:** The tightest elevation primitive degrades into a standing grant. The permission set still shows **Session Activation Required**, yet the permissions apply for the whole session with no activation step and no error.

**When it occurs:** Someone folds a session-based permission set into a group to cut the number of assignments an approver makes. The `SessionPermSetActivation` reference states the exception plainly: "If you include session-based permission sets in a permission set group, the permissions in them do not require session-based activation for users assigned to the group."

**How to avoid:** Put the activation requirement on the unit you actually assign. `PermissionSetGroup.HasActivationRequired` is available in API version 53.0 and later and defaults to `false`, so it must be set explicitly. `PermissionUpdateEventLog` (API version 65.0 and later) tracks changes to that flag — that is the detection.

---

## Gotcha 2: "Modify All Data" grants every object permission and stores none of them

**What happens:** An object-level privileged-access report built on `ObjectPermissions` undercounts, and the remediation script that deletes the offending row fails on the rows that matter.

**When it occurs:** Wherever admin-equivalent access is org-wide rather than per-object. The reference is explicit: while "Modify All Data" enables all object permissions, "it doesn't physically store any object permission records in the database". The returned record "will contain an invalid ID that begins with 000", and it "can't be updated or deleted".

**How to avoid:** Bring the org-wide permission into the query — the reference's own example selects `Parent.PermissionsModifyAllData` alongside `PermissionsRead`, so full access surfaces however it was granted. To remove it, disable "Modify All Data" first, then delete the resulting record. An Id beginning `000` is a sentinel, never a DML target.

---

## Gotcha 3: Running the inventory is itself a privileged act

**What happens:** A low-privilege auditor account runs the standing-admin query and gets an empty result or an insufficient-access error. To a reviewer unaware of the access rules, empty reads as "no privileged users".

**When it occurs:** Security provisions a read-only identity for the quarterly review. `PermissionSetAssignment` documents that as of Summer '20 and later, only users holding View Setup and Configuration, Assign Permission Sets, or Manage User can access it. `PermissionSet` needs View Setup and Configuration before object permissions, permission dependencies, and permission set group components become visible.

**How to avoid:** Define the auditor identity as privileged in its own right, with an owner and review date. Requirements differ per object: `SessionPermSetActivation` also accepts Manage Session Permission Set Activations, while `PermissionUpdateEventLog` needs View Event Log Object Data, a different permission again.

---

## Gotcha 4: Profile-owned permission sets have unstable names and labels

**What happens:** A quarterly inventory keyed on `PermissionSet.Label` stops matching its own baseline. Rows appear as new findings, tracked rows vanish, and the diff meant to prove privilege is shrinking turns to noise.

**When it occurs:** In API version 25.0 and later, every profile is associated with a permission set storing that profile's user, object, and field permissions. Those profile-owned sets are the ones the reference warns about: for a permission set owned by a profile, do not rely on the `Name` and `Label` values a query returns, because they can change.

**How to avoid:** Key the baseline on `PermissionSet.ProfileId` plus `PermissionSet.IsOwnedByProfile`, and resolve a readable name through `PermissionSet.Profile.Name` at report time. Store the profile Id; treat the label as display text.

---

## Gotcha 5: Two `PermissionSetAssignment` fields that do not mean what they read as

**What happens:** An audit filtered on `IsActive = true` returns a different population than intended, and a script selecting `IsRevoked` fails with an invalid-field error in the next org.

**When it occurs:** `IsActive` reads like the User record's status flag, so it gets substituted for `Assignee.IsActive` — the filter Salesforce's own privileged-user audit queries use. It indicates whether the *assignment* is active, defaults to `false`, and has properties Defaulted on create, Filter, Group, Sort: neither Create nor Update. `IsRevoked` (API version 57.0 and later) is "available only if user access policies are enabled".

**How to avoid:** Filter the human with `Assignee.IsActive = true`, and probe for `IsRevoked` before selecting it. Keep revocation and expiry separate — the reference's `ALL ROWS` example is scoped to revocation (`WHERE IsRevoked=true ALL ROWS`) and notes "The PermissionSetAssignment record isn't deleted" on revoke. To end a grant, set `ExpirationDate`, the only field here carrying both Create and Update.

---

## Gotcha 6: `SetupAuditTrail` refuses the three things a reviewer reaches for first

**What happens:** The break-glass evidence pack fails to build: the aggregate meant to summarise "changes per admin" throws, the Visualforce page meant to render it errors, and there is no write path.

**When it occurs:** Right after an incident. The reference states: "Aggregate queries aren't supported on this object. For example, SELECT count() FROM SetupAuditTrail works but SELECT count(Id) FROM SetupAuditTrail fails." It is also "not a supported standard controller", and its supported calls are `query()` and `retrieve()` only.

**How to avoid:** Select rows and aggregate in Apex or off-platform. Two fields change how the result reads: `DelegateUser` (API version 35.0 and later) is populated only when a Login-As user executed the action, and `CreatedByContext` (API version 48.0 and later) names the context — the documented example is `Einstein` — so a change attributed to a person may be a service's.

---

## Gotcha 7: A delegate group is an admin factory if nobody reviews its lists

**What happens:** The standing-admin count drops and the org gets less safe. Delegated administrators can grant whatever sits on their group's assignable lists, so one privileged entry reproduces the permission the review just removed.

**When it occurs:** Delegation is the chosen remedy for too many central admins. `DelegateGroup` carries `profiles` — "The profiles that can be assigned to users by delegated administrators" — plus `permissionSets` and `permissionSetGroups`, assignable to users in the specified roles and all subordinate roles. `loginAccess` "Allows users in this group to log in as users in the role hierarchy that they administer".

**How to avoid:** Treat every entry on a delegate group's `profiles`, `permissionSets`, and `permissionSetGroups` lists as privileged access, and run the inventory's permission test against them. Where `loginAccess` is `true`, pair the group with a `SetupAuditTrail` review keyed on `DelegateUser`.
