# Gotchas — Apex User And Permission Checks

Non-obvious Salesforce platform behaviors that cause real production problems.

## Gotcha 1: `checkPermission` Uses The Running User, Not The Originator

**What happens:** A Queueable calls `FeatureManagement.checkPermission('X')` and gets `false` for a user who has the permission. The running user is the async context user, which may differ from the user who enqueued the job.

**When it occurs:** Queueable, Batch, Scheduled, `@future`, platform event triggers.

**How to avoid:** Pass the originating user's Id into the job and check their permissions via a SOQL on `PermissionSetAssignment` + `SetupEntityAccess` + `CustomPermission`.

---

## Gotcha 2: Whether Admins Bypass Custom Permissions Is Unverified

**What happens:** Teams assume a "Customer Service Agent" permission check returns `true` for a System Administrator who was never granted it. UNVERIFIED (2026-10-20): the reference says only that `checkPermission` "Checks whether a custom permission is enabled" (apexref 262 L215450); no corpus line says "Modify All Data" implies custom permissions.

**When it occurs:** Any user with "Modify All Data" (admins, most integration users).

**How to avoid:** Grant the custom permission to the admin permission set explicitly and test both an admin and a non-admin with `System.runAs`. To detect Modify All Data, query `PermissionSet.PermissionsModifyAllData` (object_reference 264 L192754-192757) — `checkPermission('ModifyAllData')` is not documented (the argument is a custom permission API name, L215460).

---

## Gotcha 3: Typos Return `false`, Not An Error

**What happens:** `FeatureManagement.checkPermission('Perform_Buk_Refund')` (typo) returns `false` for everyone. No exception, no warning — UNVERIFIED (2026-10-20): the reference documents only true/false for enabled/disabled (apexref 262 L215465). Admins spend hours debugging "why does no one have this permission."

**When it occurs:** Any typo, renamed custom permission, or not-yet-deployed custom permission.

**How to avoid:** Add a self-test in deployment validation: `System.assertEquals(true, FeatureManagement.checkPermission('Perform_Bulk_Refund'), 'Bulk refund permission not deployed');` using a test user known to have it.

---

## Gotcha 4: `UserInfo.getProfileId()` Does Not Reflect Permission-Set Grants

**What happens:** A user has "View All Data" via a permission set, but `UserInfo.getProfileId()` returns their standard Profile Id. Code that derives permissions from the profile gets the wrong answer.

**When it occurs:** Any time permission-set grants are used on top of a base profile.

**How to avoid:** Don't derive permissions from `getProfileId()`. Use `checkPermission` or query `PermissionSetAssignment`.

---

## Gotcha 5: `System.runAs(systemAdmin)` Masks Permission Bugs

**What happens:** Unit tests pass in the admin-as-test-user pattern. In production a regular user hits `NoAccessException` or wrong branch.

**When it occurs:** Developers use the admin running the test as their test user.

**How to avoid:** Create a test user with a specific profile and only the permission sets the feature requires. `System.runAs(lowPrivilegeUser)` in every authorization test.

---

## Gotcha 6: `FeatureManagement.checkPackageBooleanValue` Is Separate API

**What happens:** Developers confuse custom permissions (admin-managed) with managed-package feature parameters (`checkPackageBooleanValue`). The APIs are distinct.

**When it occurs:** Building an ISV or extension for a managed package.

**How to avoid:** Custom permissions: `FeatureManagement.checkPermission('Name')`. Managed package feature params: `FeatureManagement.checkPackageBooleanValue('Name')`.

---

## Gotcha 7: Session-Based Permission Sets Need Session Activation

**What happens:** A user has a permission set assigned but `checkPermission` returns `false` because the permission set is session-based and not yet activated in the current session. Activation is per session (`SessionPermSetActivation`; deleting the record ends it — object_reference 264 L264542-264543); the exact `checkPermission` result before activation is UNVERIFIED (2026-10-20).

**When it occurs:** Session-based permission sets with activation controls.

**How to avoid:** Activate the session-based permission set via the UI or API before running the relevant code, or use a non-session permission set for automation-only permissions.

---

## Gotcha 8: Custom Permission `Privileged` SubSystem Metadata

**What happens:** A deployment removes the Custom Permission's assignment from a permission set. Next deploy `checkPermission` returns `false` across the org. Nothing in the code changed.

**When it occurs:** Permission set changes deployed without the permission set updates.

**How to avoid:** Include the permission set metadata (`.permissionset-meta.xml`) in the same deployment as the custom permission, so grants are maintained.
