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

- Salesforce Help — Custom Permissions Overview: https://help.salesforce.com/s/articleView?id=sf.custom_perms_overview.htm
- Salesforce Help — Use Custom Permissions in Formulas: https://help.salesforce.com/s/articleView?id=sf.custom_perms_build_in_formula.htm
- Apex Developer Reference — FeatureManagement Class: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_FeatureManagement.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Metadata API Developer Guide — CustomPermission: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_customperm.htm
