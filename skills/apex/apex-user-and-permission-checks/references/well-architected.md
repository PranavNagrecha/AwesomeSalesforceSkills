# Well-Architected Notes — Apex User And Permission Checks

## Relevant Pillars

### Security

Permission checks are the authorization boundary inside Apex. Weak checks (profile name strings, cached results, async-context confusion) cause real breach scenarios. Security-tagged findings include:

- profile-name-equality gating
- `checkPermission` in async jobs checking the wrong user
- undefined permission names silently denying (or incorrectly mapping)
- no test exercising denial paths

### Reliability

Permission-gated code that fails wrong (denies valid users, admits invalid users) creates both support tickets and incidents. Reliable code has deployment-time assertions that every referenced custom permission exists and is assigned to at least one test user.

## Architectural Tradeoffs

- **Custom Permissions vs Permission-Set-Name Checks:** Custom Permissions are the admin-managed abstraction. Permission-set-name checks lock the assignment path and break when admins split/rename sets.
- **`FeatureManagement.checkPermission` vs custom SOQL:** Use the built-in for the running user. Use SOQL only when checking a non-running user (async originator).
- **Profile vs Permission Set:** Profile assignments are 1:1 and heavy; permission-set assignments are additive. Prefer permission sets for grants so multiple users with different profiles can share an entitlement.

## Anti-Patterns

1. **Profile-name string check** — renamed profiles and PS-only grants break the gate silently.
2. **Async running-user assumption** — the Queueable's `checkPermission` resolves to the async context user, often different from the enqueuer.
3. **No deployment-time validation of permission existence** — typos or not-yet-deployed permissions deny everyone (silent `false` is UNVERIFIED (2026-10-20)).

## Official Sources Used

- Apex Reference 262 — `FeatureManagement.checkPermission(apiName)` checks a custom permission; argument is its API name; returns enabled/disabled (salesforce_apex_reference_guide.txt L215449-215465); `UserInfo.getUserType()` returns String (L243451-243460); `isMultiCurrencyOrganization()` (L243541-243542)
- Object Reference 264 — User.UserType values (object_reference.txt L300019-300037); CustomPermission / SetupEntityAccess query examples (L88715-88729); `PermissionsModifyAllData` filter (L192754-192757)
- Platform Events 264 — PE Apex trigger runs as Automated Process or the configured user (platform_events.txt L2309, L2366-2368)

- Apex Reference — FeatureManagement: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_FeatureManagement.htm
- Apex Reference — UserInfo: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_userinfo.htm
- Salesforce Help — Custom Permissions: https://help.salesforce.com/s/articleView?id=sf.custom_perms_overview.htm
- Salesforce Help — Permission Sets: https://help.salesforce.com/s/articleView?id=sf.perm_sets_overview.htm
- Object Reference — PermissionSetAssignment: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_permissionsetassignment.htm
- Salesforce Well-Architected — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
