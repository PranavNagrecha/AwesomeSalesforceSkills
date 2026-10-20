---
name: apex-custom-permissions-check
description: "Custom Permissions in Apex: FeatureManagement.checkPermission, $Permission global variable, permission-set gating of feature code, Custom Permission metadata. NOT for creating or assigning the permission in Setup — use admin/custom-permissions. NOT for CRUD/FLS enforcement — use apex/apex-stripinaccessible-and-fls-enforcement."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
tags:
  - apex
  - custom-permissions
  - featuremanagement
  - permission-sets
  - authorization
triggers:
  - "featuremanagement.checkpermission apex custom permission"
  - "gate apex feature behind custom permission"
  - "custom permission vs profile permission best practice"
  - "how to check custom permission in lwc and apex"
  - "custom permission in validation rule and formula"
  - "feature flag pattern salesforce custom permission"
inputs:
  - Feature or code path to gate
  - Target user populations (profiles / permission sets)
  - Test scenarios needing permission toggling
outputs:
  - Custom Permission metadata
  - Apex check pattern
  - Permission Set assignment plan
  - Test class using System.runAs with permission set
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
status: stub
---

# Apex Custom Permissions Check

Activate when gating code paths, feature availability, or field-level behavior behind a Custom Permission. Custom Permissions are the platform's feature-flag primitive — declarative on/off tokens assigned via Permission Sets or Profiles that Apex, LWC, formulas, and validation rules can check consistently.

## Before Starting

- **Create the Custom Permission metadata first.** Setup → Custom Permissions (secimpl 262 L1112) or via a `.customPermission` file in the `customPermissions` folder, API version 31.0 and later (api_meta 264 L49023, L49027). In Group and Professional Edition you can install custom permissions from a managed package but cannot create or edit them (secimpl 262 L1080-1085).
- **Assign via Permission Set, not Profile** for maintainability.
- **Use `FeatureManagement.checkPermission`** for runtime checks: `public static Boolean checkPermission(String apiName)`, "Checks whether a custom permission is enabled" (apexref 262 L215449-215454); the Security Guide's own Apex example is the same call (secimpl 262 L1089-1090). UNVERIFIED (2026-10-20): the old claim that a Schema describe path is "deprecated" — neither guide says so; do not assert it.

## Questions to Ask Before Configuring

Each question traces to a gotcha in `references/gotchas.md`.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Is the permission checked in Apex, or only hidden in the LWC?" | A client check is not an authorization boundary (gotcha 2) | The service entry point that calls `FeatureManagement.checkPermission` |
| "Does any LWC compare the import with `=== false`?" | The import is `true` or `undefined`, never `false` (gotcha 1) | A getter that normalises with `=== true` |
| "Is the permission authored by hand or retrieved from an org?" | `isLicensed` is required and read-only (gotcha 3) | A retrieved `.customPermission` with its `isLicensed` left as-is |
| "Does the permission depend on another (requiredPermission)?" | A required permission must be enabled when its parent is (gotcha 4) | The whole chain in one permission set, asserted in a test |
| "Is the permission from a managed package?" | The subscriber needs the namespace prefix in Apex and the LWC import (gotcha 5) | The `ns__Name` form in both places |
| "Which entry points reach the gated work: Apex, Flow, API, Data Loader?" | A gate on one surface leaves the others open (gotcha 2) | A list of every entry point and where each is gated |
| "Who is allowed to flip the feature org-wide?" | Per-user gating does not give a kill switch (gotcha 2) | A separate hierarchy Custom Setting or Custom Metadata flag, if one is wanted |

A proper configuration adds one permission, one permission set, one server-side check per entry point and a deny-branch test, where "just doing it" gives a hidden button and an open endpoint.

## Core Concepts

### Custom Permission metadata

```
<CustomPermission xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Approve Big Deals</label>
    <isLicensed>false</isLicensed>
</CustomPermission>
```

API Name is the handle used in Apex. `isLicensed` is "Required. Read-only" (api_meta 264 L49046-49049); `description` is limited to 255 characters and `label` to 80 (L49043-49052). UNVERIFIED (2026-10-20): use of the name in formulas — the corpus shows `$Permission.CustomPermission.<name>` only for Lightning page component visibility on app, Home and record pages (api_meta 264 L70085-70086).

### Apex check

```
Boolean canApprove = FeatureManagement.checkPermission('Approve_Big_Deals');
if (!canApprove) throw new AuraHandledException('Not authorized');
```

Evaluated for the running user. UNVERIFIED (2026-10-20): "transaction-cached" and "safe to call repeatedly" — apexref gives no caching or cost statement, so hoist the call out of loops (it is per user, not per record).

### Formula / validation rule

`$Permission.Approve_Big_Deals` for declarative gating. UNVERIFIED (2026-10-20): formula and validation-rule support; the corpus confirms the `$Permission.CustomPermission.<name>` expression only for Lightning page visibility (api_meta 264 L70085).

### LWC

```
import hasApprove from '@salesforce/customPermission/Approve_Big_Deals';
```

Evaluates to `true` or `undefined`, never `false` — "evaluate whether it's `true` or `undefined`" (LWC guide, create-get-permissions.html, fetched 2026-10-20); the earlier "Returns Boolean" was CONTRADICTED by that page. Evaluate in getters and test truthiness.

### Testing

```
@IsTest
static void canApprove() {
    // TestUserFactory.createUser(profileName, permSetNames) is the real signature
    // (templates/apex/tests/TestUserFactory.cls); makeUser() does not exist.
    User u;
    System.runAs(new User(Id = UserInfo.getUserId())) {   // setup-object DML (apex dev guide 264 L9059-9062)
        u = TestUserFactory.createUser('Standard User', new List<String>{ 'Big_Deal_Approvers' });
    }
    System.runAs(u) { ... }
}
```

## Common Patterns

### Pattern: Gate Apex service entry point

```
public with sharing class ApprovalService {
    public void approve(Id oppId) {
        if (!FeatureManagement.checkPermission('Approve_Big_Deals')) {
            throw new AuraHandledException('Not authorized');
        }
    }
}
```

### Pattern: LWC conditional render

```
import hasApprove from '@salesforce/customPermission/Approve_Big_Deals';
export default class Approve extends LightningElement {
    get showButton() { return hasApprove; }
}
```

### Pattern: Validation rule gate

`AND(ISCHANGED(Status), Status='Approved', NOT($Permission.Approve_Big_Deals))`

## Decision Guidance

| Need | Mechanism |
|---|---|
| Feature flag for code path | Custom Permission |
| Object CRUD | Object permission on Permission Set |
| Field-level gate | FLS on Permission Set |
| Temporary admin toggle | Custom Setting + check |
| A/B test | Custom Permission + assignment script |

## Recommended Workflow

1. Define the feature boundary — what code runs for privileged users only.
2. Create the Custom Permission metadata.
3. Create a Permission Set granting it; assign to users.
4. Add `FeatureManagement.checkPermission` at service entry points.
5. Mirror the check in LWC and formulas where needed.
6. Write Apex tests using `System.runAs` + PermissionSetAssignment.
7. Document the permission in the feature runbook.

## Review Checklist

- [ ] Custom Permission metadata exists with clear label
- [ ] Assigned via Permission Set (not Profile)
- [ ] Apex uses `FeatureManagement.checkPermission`
- [ ] LWC uses `@salesforce/customPermission/` import
- [ ] Formulas use `$Permission.<API_Name>`
- [ ] Tests cover both granted and denied
- [ ] No hardcoded user Ids in permission checks
- [ ] Permission documented in feature doc

## Salesforce-Specific Gotchas

1. **`isLicensed`** is "Required. Read-only" and says whether "the appropriate Salesforce license is required before accessing the permission" (api_meta 264 L49046-49049). UNVERIFIED (2026-10-20): that it concerns a managed-package license and that an unlicensed user cannot receive the permission even if assigned.
2. **Use `FeatureManagement.checkPermission`, not a query of `SetupEntityAccess`** — UNVERIFIED (2026-10-20): that any Schema describe route is "deprecated"; no corpus line says so.
3. **A muting permission set can disable permissions inside a Permission Set Group** ("a set of disabled permissions … used in conjunction with PermissionSetGroup", api_meta 264 L92411) — audit it when a grant does not apply. UNVERIFIED (2026-10-20): that custom-permission grants propagate through groups.

## Output Artifacts

| Artifact | Description |
|---|---|
| Custom Permission metadata | XML file |
| Permission Set granting the CP | Metadata + assignment plan |
| Apex test class | Positive + negative cases with runAs |

## Related Skills

- `admin/custom-permissions` — creating and assigning the permission in Setup
- `admin/permission-set-architecture` — permission-set design
- `apex/apex-stripinaccessible-and-fls-enforcement` — CRUD/FLS enforcement
- `apex/apex-user-and-permission-checks` — other user and permission checks in Apex
- `security/permission-set-groups-and-muting` — muting and group composition
