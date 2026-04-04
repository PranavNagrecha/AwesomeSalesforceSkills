# Gotchas — Custom Permissions

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Custom Permissions Cannot Be Assigned Directly to Profiles

**What happens:** Admins look in the profile editor for a "Custom Permissions" section and do not find one. Attempting to assign a custom permission to a profile via the Metadata API results in a deployment error. The platform only supports custom permission assignment through permission sets and permission set groups.

**When it occurs:** Every time a team assumes that because profiles control most access, they should also control custom permissions. This is a design assumption that does not match how the platform works.

**How to avoid:** Always assign custom permissions through a permission set. If every user with a given profile needs the permission, create a dedicated "baseline" permission set, add the custom permission to it, and assign that permission set to all users with that profile. For large user populations, use a permission set group as the assignment unit.

---

## Gotcha 2: Apex Unit Tests Return False for FeatureManagement.checkPermission Without Explicit Setup

**What happens:** A developer writes an Apex test for code that calls `FeatureManagement.checkPermission('My_Permission')`. The test runs as the standard test runner context, which has no permission set assignments. The check returns `false` even though the permission set is assigned to all real users in the org. The test either incorrectly passes (if it asserts `false`) or fails unexpectedly (if it asserts `true`), leading to misleading CI results.

**When it occurs:** Any time `FeatureManagement.checkPermission` is used in production code without a corresponding test setup that explicitly assigns the permission set to the test user inside `System.runAs`.

**How to avoid:**
1. In `@TestSetup`, create the permission set in test data or query an existing one by name.
2. Insert a `PermissionSetAssignment` record linking the permission set to the test user.
3. Wrap the code-under-test in `System.runAs(testUser)` so the assignment is visible.
4. Write a separate test method that runs as a user _without_ the permission set to verify the negative case.

---

## Gotcha 3: $Permission Is Only Available in Formula Resources Inside Flow — Not Directly in Conditions

**What happens:** A Flow builder attempts to reference `$Permission.My_Permission` directly inside a Decision element condition row or an Assignment element. The Flow Builder either rejects the reference, shows a validation error, or silently ignores it, depending on the Flow version. The expected access check never fires correctly.

**When it occurs:** When someone familiar with how `$Permission` works in formula fields tries to apply the same syntax directly in Flow conditions without going through a formula resource first.

**How to avoid:** In Flow Builder:
1. Create a new **Resource** of type **Formula**, with a Return Type of **Boolean**.
2. Set the formula value to `$Permission.My_Custom_Permission`.
3. Save the resource with a meaningful name such as `hasMyCustomPermission`.
4. Reference that formula resource variable in your Decision element condition: `{!hasMyCustomPermission} Equals True`.

This extra step is required because Flow evaluates `$Permission` only inside formula contexts, not in direct condition evaluation.

---

## Gotcha 4: API Name Is Effectively Immutable After Production Use

**What happens:** A team decides to rename a custom permission API name (for example from `BetaFeature` to `Beta_New_Case_Console`) after it has been deployed. The Metadata API allows the rename at the metadata level, but all existing `$Permission.BetaFeature` references in validation rules, formula fields, and Apex strings silently break. Validation rules and formulas evaluate `$Permission.BetaFeature` to `false` (no error, just silent grant of access to nobody). Apex strings that reference the old name pass compile-time checks but return `false` at runtime.

**When it occurs:** Any time an API name is changed in production without a coordinated find-and-replace across all dependent metadata and code.

**How to avoid:** Treat the custom permission API name as immutable once it is used in production. If a rename is truly necessary, use a coordinated deployment: update all referencing validation rules, formulas, Apex classes, and Flow formula resources in the same deployment package as the renamed permission. Test thoroughly in a full sandbox first.

---

## Gotcha 5: Managed Package Custom Permissions Are Namespaced and Cannot Be Renamed

**What happens:** When a custom permission is included in a managed package, the platform automatically prepends the package namespace to the API name (for example `MyNS__My_Permission`). Code and metadata in subscriber orgs must use the namespaced form. If the subscriber org also creates a permission with the same local name, the two do not conflict but the namespaced form must be used explicitly in all checks within the package.

**When it occurs:** When ISVs or teams building managed packages include custom permissions and forget to use the namespaced API name in their Apex (`FeatureManagement.checkPermission('MyNS__My_Permission')`) or in subscriber-facing setup instructions.

**How to avoid:** Always use the fully namespaced API name in managed package Apex and documentation. In unmanaged development orgs, the namespace prefix is absent, so use a utility method that conditionally prepends the namespace when running inside a managed context.
