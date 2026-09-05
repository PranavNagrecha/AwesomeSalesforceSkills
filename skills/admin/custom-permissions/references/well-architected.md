# Well-Architected Notes — Custom Permissions

## Relevant Pillars

- **Security** — Custom permissions are a named, auditable access control mechanism. They enforce least-privilege access to features and capabilities without broadening CRUD/FLS grants. Using named permissions instead of profile-name checks or hardcoded user IDs keeps the access model declarative and reviewable. Every grant is traceable through a permission set assignment record.

- **User Experience** — Feature gates built on custom permissions allow graduated rollouts and persona-specific UI without deploying new code. UX teams can enable features for specific user groups, gather feedback, and roll back by managing assignment — not by modifying metadata or initiating a release cycle.

- **Operational Excellence** — Custom permissions centralize feature access decisions in a named, searchable metadata object. The API name is the single source of truth for whether a feature is accessible. Rollout and rollback are permission-set assignment operations, not deployments.

## Architectural Tradeoffs

**Named permission vs. custom setting flag**

A custom setting boolean (or custom metadata type flag) can also gate features, and it supports hierarchical values. The tradeoff is that custom settings are not user-identity-aware without additional query logic. `FeatureManagement.checkPermission` reads the current user's session state directly — no SOQL, no hierarchy traversal. For user-specific feature gating, custom permissions are faster and more idiomatic. For org-wide or profile-agnostic flags (for example, enabling a global integration mode), custom settings or custom metadata are more appropriate.

**Validation rule bypass via custom permission vs. via profile**

Using `$Permission` in validation rules is architecturally preferable to `$Profile.Name` for the same reason custom permissions exist in the first place: the permission is independently assignable, renameable (on the label side), and auditable. `$Profile.Name` couples the bypass to an identity attribute that admins change for unrelated reasons and that does not survive profile consolidation projects.

**Custom permission vs. permission set license (PSL)**

A custom permission is a free-form boolean grant with no associated license enforcement. A permission set license is a platform-enforced gate that requires the user to hold a specific license before a permission can be assigned. Use custom permissions when the gate is purely functional (your logic decides what it means). Use PSLs when Salesforce itself enforces the license boundary.

## Anti-Patterns

1. **Using $Profile.Name or hardcoded user IDs as feature gates** — Profile names change, user IDs are not portable across orgs, and neither approach is auditable through the permission set assignment model. Any feature access check that cannot be answered by "which permission set grants this" is a security audit liability and an operational maintenance burden. Replace with a named custom permission.

2. **Storing feature flag state in a Custom Setting or Record field and checking it in Apex instead of using FeatureManagement** — This approach requires SOQL, adds governor limit consumption, and creates a synchronization problem between the "flag" state and the user's actual permission set assignments. For user-specific gates, `FeatureManagement.checkPermission` is the correct idiom because it reads from the platform's access model directly.

3. **Not testing both the positive and negative permission states in unit tests** — Apex tests that only assert behavior when the permission is present miss the equally important case where access should be denied. A class that uses `FeatureManagement.checkPermission` must have coverage for both the granted and denied paths, or the access control logic is untested.

## Official Sources Used

- Metadata API Developer Guide (v62 PDF) — `CustomPermission`, pp. 841-843 (`api_meta.txt` L46625-46752): the file suffix and `customPermissions` folder, API 31.0 availability, the `connectedApp` / `description` / `isLicensed` / `label` / `requiredPermission` field table with character limits, the `CustomPermissionDependencyRequired` subtype, the `Acme_Account_Full_Access` sample definition and its package.xml, and wildcard support in the manifest. Supports `references/metadata-examples.md` sections 1-4, package.xml, and Gotchas 7 and 9. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide (v62 PDF) — `PermissionSet.customPermissions` / `PermissionSetCustomPermissions` (`api_meta.txt` L94780, L94943-94952) and `Profile.customPermissions` / `ProfileCustomPermissions` (L97670, L97961-97970): the `enabled` + `name` shape, API 31.0 for both parents, and the "Only enabled custom permissions are retrieved" rule. Supports the grant XML in `references/metadata-examples.md` section 5 and Gotchas 1 and 8. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide (v62 PDF) — `FlexiPage` / `UiFormulaCriterion` component-visibility expressions (`api_meta.txt` L67560-67562, L99375-99378, sample L99472): the `{!$Permission.CustomPermission.permissionName}` grammar and its "app, Home, and record pages only" scope. Supports the component-visibility snippet in `references/metadata-examples.md` section 6 and Gotcha 6. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Object Reference for the Salesforce Platform (v62 PDF) — `CustomPermission` (`object_reference.txt` L88398-88578), `CustomPermissionDependency` (L88593-88680), `SetupEntityAccess` (L261624-261700): the `DeveloperName` naming contract and 80-character limit, `IsLicensed` from API 50.0, the setup-access rules on all three objects, the `SetupEntityType = 'CustomPermission'` value from API 31.0, and the guide's own coverage queries. Supports every verification query in `references/metadata-examples.md` and Gotchas 1, 8 and 9. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Apex Reference Guide (v62 PDF) — `FeatureManagement.checkPermission(apiName)` (`apexrefguide.txt` L215449-215466) and `FeatureManagement.changeProtection(apiName, typeApiName, protection)` (L215300-215330): the `public static Boolean checkPermission(String apiName)` signature, the "API name of the custom permission" parameter contract, and the packaging method that hides or reveals custom permissions in a subscriber org. Supports the Apex snippet and the Decision Guidance row on Apex checks. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/apexrefguide.pdf
- Metadata API Developer Guide (v62 PDF) — `ConnectedApp.permissionSetName` (`api_meta.txt` L35091-35103): the grounded mechanism for requiring permissions on a connected app, API 46.0+, gated on `isAdminApproved`. Supports the correction of the `connectedApp` field's meaning in `references/metadata-examples.md` section 4. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Lightning Web Components Developer Guide — Permissions: the `@salesforce/customPermission/<Name>` scoped module, the `true`-or-`undefined` evaluation rule, and the managed-package namespace prefix. Consumed indirectly; the verbatim quotes and verification live in `skills/apex/apex-custom-permissions-check/references/well-architected.md`. Supports the LWC snippet in `references/metadata-examples.md` section 6. https://developer.salesforce.com/docs/platform/lwc/guide/create-get-permissions.html
- Salesforce Well-Architected — Overview: the Security and Operational Excellence framing used in Relevant Pillars. https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
