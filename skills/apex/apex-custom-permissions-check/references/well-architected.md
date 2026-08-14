# Well-Architected Notes — Apex Custom Permissions Check

## Relevant Pillars

- **Security** — Primary. Custom permissions are the platform's *authorization* primitive: they answer "may this user do this thing," which is distinct from CRUD/FLS ("may this user read this field") and from sharing ("may this user see this record"). Confusing the three is the dominant failure. Since API version 67.0, "Apex runs in user context by default, meaning that the current user's permissions and field-level security (FLS) are enforced during code execution" — but that default says nothing about your feature gate, so the explicit `FeatureManagement.checkPermission` call remains mandatory.
- **Operational Excellence** — Primary alongside Security. The point of a custom permission over a profile check is that granting the feature becomes an admin assignment rather than a code deploy. That is a change-management property, not a security one, and it is usually the reason the pattern pays for itself.
- **Reliability** — Secondary. Gating one surface and not the others produces a feature that appears controlled and is not. The reliability work is enumerating every entry point — Apex, LWC, Flow, validation rule, API — and covering each.

## Architectural Tradeoffs

| Tradeoff | Decision criteria |
|---|---|
| Custom Permission vs Permission Set object/field permission | Custom Permission when the thing being gated is *behaviour* (an action, a code path, a UI affordance). Object/field permission when the thing being gated is *data*. Never simulate data access control with a custom permission — sharing and FLS are enforced by the platform; your `if` statement is not. |
| Custom Permission vs Custom Setting feature flag | Custom Permission answers "which users"; Custom Setting answers "is the feature on at all". A rollout that needs both a per-user gate and an org-wide kill switch needs both mechanisms, checked in that order. |
| Assign via Permission Set vs Profile | Permission Set, always. Profiles are one-per-user and force cloning to add a capability; permission sets compose. Permission Set Groups add muting, which is worth auditing when a permission unexpectedly does not apply. |
| Check at the entry point vs deep in the call stack | Entry point. A check buried three calls down is easy to bypass by adding a fourth caller. Put it in the `@AuraEnabled` / `@InvocableMethod` / REST resource method and let the rest of the stack assume authorization. |
| Client-side check vs server-side check | Both, for different reasons. The client check prevents the user seeing an action that will fail. The server check is the only one that enforces anything. Shipping only the client check is the most common security defect in this area. |

## Architectural Anti-Patterns

1. **Treating the LWC import as enforcement** — `@salesforce/customPermission/...` resolves to `true` or `undefined` in the browser. It shapes the DOM; it does not stop a direct call to the `@AuraEnabled` method. Every gated Apex method needs its own check.
2. **Identity checks standing in for authorization** — hard-coded profile Ids, profile names, role names, or user Ids. These are environment-specific (Ids), renameable (names), and require a deploy to change (all of them). A custom permission moves the decision to an admin-assignable artifact.
3. **Gating Apex and forgetting the declarative entry points** — Data Loader, Flow, and the REST API never execute your service class. If the rule must hold universally, it belongs additionally in a validation rule using `$Permission.<API_Name>`, which the platform evaluates on every save path.

## Official Sources Used

- Apex Reference Guide — `System.FeatureManagement` class. Confirms the class purpose ("check and modify the values of feature parameters, and to show or hide custom objects and custom permissions in your subscribers' orgs"), the `public static Boolean checkPermission(String apiName)` signature, its description "Checks whether a custom permission is enabled", the `apiName` parameter contract, and the `changeProtection` / `setPackageIntegerValue` signatures. — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_FeatureManagement.htm (verified 2026-08-14)
- Metadata API Developer Guide — `CustomPermission` metadata type. Confirms availability in API version 31.0 and later, the `.customPermission` suffix and `customPermissions` folder, and the field set: `connectedApp` (80-char limit), `description` (255-char limit), `isLicensed` ("Required. Read-only."), `label` (Required, 80-char limit), and `requiredPermission` (API version 32.0 and later). — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_custompermission.htm (verified 2026-08-14)
- Lightning Web Components Developer Guide — Permissions. Confirms the `@salesforce/customPermission` and `@salesforce/userPermission` scoped modules, the verbatim rule that you "evaluate whether it's `true` or `undefined`", the managed-package namespace prefix rule and the same-namespace exception, and the `has{Permission}` naming convention. — https://developer.salesforce.com/docs/platform/lwc/guide/create-get-permissions.html (verified 2026-08-14)
- Apex Developer Guide — Enforce Object and Field Permissions. Confirms that in API version 67.0 and later "Apex runs in user context by default" with FLS enforced, and that "In API version 66.0 and earlier, system mode is the default", plus the precedence of object- and field-level permissions over sharing rules. — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_perms_enforcing.htm (verified 2026-08-14)
- Salesforce Well-Architected — Secure pillar — https://architect.salesforce.com/well-architected/trusted/secure
