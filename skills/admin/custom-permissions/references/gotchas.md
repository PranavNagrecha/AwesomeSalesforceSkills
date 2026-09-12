# Gotchas — Custom Permissions

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: A Profile *Can* Grant a Custom Permission, and That Grant Is Invisible in the Permission Sets List

**What happens:** The common advice is that custom permissions live only in permission sets. The Metadata API disagrees: `Profile` has a `customPermissions` field of type `ProfileCustomPermissions[]`, available in API version 31.0 and later — the same version and the same `enabled` + `name` shape as `PermissionSet` (`api_meta.txt` L97670 and L97961-97970). A profile-borne grant deploys cleanly. It then hides: the access is carried by the profile's implicit permission set, so an admin auditing **Setup > Custom Permissions > Permission Sets** finds nothing, and a user holds a permission nobody can explain.

**When it occurs:** After a profile is retrieved from a legacy org, hand-edited, or copied between orgs — `customPermissions` nodes ride along in the profile XML unnoticed. Also any time an org still manages access profile-first.

**How to avoid:** Grant through a permission set so the grant is assignable, revocable, and expirable independently of the user's profile. To find grants that are already hiding in profiles, run the `SetupEntityAccess` -> `PermissionSetAssignment` query in `references/metadata-examples.md` and read the `PermissionSet.IsOwnedByProfile` column: `true` means the grant came from a profile. The Object Reference shows the inverse filter, `isOwnedByProfile = false`, precisely because profile-owned rows otherwise pollute the result (`object_reference.txt` L88571-88578). See `admin/permission-sets-vs-profiles` for the migration argument and `admin/permission-set-expiration` for time-boxing a bypass grant.

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

---

## Gotcha 6: Component Visibility Uses a Different `$Permission` Syntax Than Formulas

**What happens:** An admin copies the formula-context expression `$Permission.Bypass_Validation_Rules` into a Dynamic Forms / Lightning page component visibility filter or an In-App Guidance prompt, and the component either never shows or never hides. Component visibility resolves permissions through a different grammar: `{!$Permission.CustomPermission.permissionName}` for custom permissions and `{!$Permission.StandardPermission.permissionName}` for standard ones (`api_meta.txt` L67560-67562 for FlexiPage, L99375-99378 for Prompt, with a working sample at L99472). The extra `CustomPermission.` segment is not optional and the formula form is not a synonym for it.

**When it occurs:** Any time the same permission gates both a validation rule and a page component, which is the normal case for a feature flag, and the practitioner reuses the string.

**How to avoid:** Keep two spellings per permission and treat them as different APIs. The guide also bounds where the expression works at all: `{!$Permission.CustomPermission...}` is "Supported for app, Home, and record pages only" — not on other FlexiPage types. Component-visibility mechanics belong to `admin/dynamic-forms-and-actions`; the In-App Guidance `uiFormulaRule` shape belongs to `admin/in-app-guidance-and-walkthroughs`.

---

## Gotcha 7: `isLicensed` Is Read-Only, So You Cannot Deploy a Permission Into Being License-Gated

**What happens:** A team wants a custom permission that only license-holders can hold, sets `<isLicensed>true</isLicensed>` in the `.customPermission-meta.xml`, and deploys. The field is documented as **"Required. Read-only."** (`api_meta.txt` L46654-46657) and the guide's own sample definition omits it entirely (L46688-46700). The platform owns the value; the deploy does not make the permission license-gated, and the team believes it has an enforcement boundary it does not have.

**When it occurs:** When "custom permission" and "permission set license" get conflated during design, usually while packaging a feature for distribution.

**How to avoid:** Treat `isLicensed` as output, not input — query it back as `CustomPermission.IsLicensed`, available in API version 50.0 and later (`object_reference.txt` L88459-88467). If Salesforce itself must enforce a license boundary, that is a permission set license, not a custom permission (see the pillar note in `references/well-architected.md`). If the gate is purely functional, a plain custom permission is correct and no licensing element is needed.

---

## Gotcha 8: A Retrieve Cannot Distinguish "Never Granted" From "Revoked"

**What happens:** A team diffs two orgs' permission sets to prove a bypass permission was removed from production, and the diff shows nothing at all. `PermissionSetCustomPermissions` is documented with "Only enabled custom permissions are retrieved" (`api_meta.txt` L94943-94952); the identical sentence governs `ProfileCustomPermissions` (L97961-97963). A `<customPermissions>` node with `<enabled>false</enabled>` therefore never comes back from a retrieve. Absence in source means "not granted" and carries no evidence of whether it was ever granted or deliberately turned off.

**When it occurs:** During access reviews, SOX-style evidence gathering, and any org-comparison tooling that treats retrieved metadata as a complete statement of access.

**How to avoid:** Do not use metadata diffs as revocation evidence for custom permissions. Query the live org through `SetupEntityAccess` (`SetupEntityType = 'CustomPermission'`, valid since API 31.0 — `object_reference.txt` L261686) and capture the result set with a timestamp. Note the corollary for deploys: because absence is not a revocation instruction, removing a `<customPermissions>` node from a permission set file and deploying it does revoke the grant, while `<enabled>false</enabled>` is a shape you will never see in a round-trip and should not hand-author.

---

## Gotcha 9: The API Name Rules Are Stricter Than "Letters, Digits, Underscores"

**What happens:** A permission named `Bypass__Validation` or `Beta_Feature_` is authored by hand, and the deploy fails or Setup rejects the name for reasons the error message states tersely. The `DeveloperName` contract is narrower than the usual API-name folklore: it "can contain only underscores and alphanumeric characters and must be unique in your organization. It must begin with a letter, not include spaces, not end with an underscore, and not contain two consecutive underscores" with a limit of 80 characters (`object_reference.txt` L88439-88448). Two consecutive underscores and a trailing underscore are both illegal — not merely discouraged.

**When it occurs:** When names are generated from labels by a script, or when someone mimics the `__c` custom-field convention and produces a double underscore.

**How to avoid:** Generate names with a single underscore between words, never a trailing one, and never the `__` sequence — which is reserved as the namespace separator (`NamespacePrefix__componentName`, `object_reference.txt` L88510-88520). `label` and `connectedApp` are capped at 80 characters and `description` at 255 (`api_meta.txt` L46647-46652, L46660-46663), so a description that names every consumer has to stay terse. The checker script flags an empty description for exactly this reason: the description is the only place the consumer list can live.

---

## Gotcha 10: A `description` Over 255 Characters Fails The Deploy

**What happens:** A custom permission's `description` grows to hold both the consumer list (Gotcha 9's reason it exists at all) and a sentence of rationale — who owns the bypass, when it was granted, why. The deploy is rejected with `Description: data value too large … (max length=255)`. Nothing about the failure names the field by number; it just fails.

**When it occurs:** Any custom permission whose description reads like a design note instead of a consumer list. The Metadata API Developer Guide states the limit directly in the `CustomPermission` field table: "The custom permission description. Limit: 255 characters" (`api_meta.txt` L46651-46652). It is a headroom problem more than an edge case — `Bypass_Case_Intake_Validation` in `examples/builds/case-onboarding/artefacts/M2-S01` sits at 250 characters today, six characters from the limit, with only a consumer list and an owner name in it.

**How to avoid:** Keep `description` to the consumer list and nothing else; if the list itself does not fit, the permission is doing too much and should split (the "if the sentence needs an 'and'" test in `## Questions to Ask Before Configuring`). Put rationale — approval history, retirement date, who to ask — in the build's `deploy-order.md` or the configuration workbook. `scripts/check_custom_permissions.py` flags this before deploy: `CP-DESC-01` (ERROR) at 255+ characters, `CP-DESC-02` (INFO, headroom only — never fails the run, even under `--strict`) at 200+.
