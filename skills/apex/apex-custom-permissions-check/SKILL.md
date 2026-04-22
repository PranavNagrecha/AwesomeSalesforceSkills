---
name: apex-custom-permissions-check
description: "Custom Permissions in Apex: FeatureManagement.checkPermission, $Permission global variable, permission-set gating of feature code, Custom Permission metadata. NOT for CRUD/FLS enforcement (use security-apex-crud-fls). NOT for standard Salesforce permissions (use permission-set-architecture)."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
---

# Apex Custom Permissions Check

Activate when gating code paths, feature availability, or field-level behavior behind a Custom Permission. Custom Permissions are the platform's feature-flag primitive — declarative on/off tokens assigned via Permission Sets or Profiles that Apex, LWC, formulas, and validation rules can check consistently.

## Before Starting

- **Create the Custom Permission metadata first.** Setup → Custom Permissions or via `-meta.xml` deployment.
- **Assign via Permission Set, not Profile** for maintainability.
- **Use `FeatureManagement.checkPermission`** for runtime checks — not the deprecated Schema describe path.

## Core Concepts

### Custom Permission metadata

```
<CustomPermission xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Approve Big Deals</label>
    <isLicensed>false</isLicensed>
</CustomPermission>
```

API Name is the handle used in Apex / formulas.

### Apex check

```
Boolean canApprove = FeatureManagement.checkPermission('Approve_Big_Deals');
if (!canApprove) throw new AuraHandledException('Not authorized');
```

Per-user, transaction-cached. Safe to call repeatedly.

### Formula / validation rule

`$Permission.Approve_Big_Deals` returns Boolean for declarative gating.

### LWC

```
import hasApprove from '@salesforce/customPermission/Approve_Big_Deals';
```

Returns Boolean at module load — evaluate in getters.

### Testing

```
@IsTest
static void canApprove() {
    User u = TestUserFactory.makeUser();
    insert new PermissionSetAssignment(
        AssigneeId = u.Id,
        PermissionSetId = [SELECT Id FROM PermissionSet WHERE Name = 'Big_Deal_Approvers'].Id
    );
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

1. **`isLicensed=true`** requires the user's managed-package license; non-licensed users cannot receive it even if assigned.
2. **`Schema.describe` for Custom Permissions is deprecated** — use `FeatureManagement.checkPermission`.
3. **Custom Permission grants propagate through Permission Set Groups** — audit muting flags on groups.

## Output Artifacts

| Artifact | Description |
|---|---|
| Custom Permission metadata | XML file |
| Permission Set granting the CP | Metadata + assignment plan |
| Apex test class | Positive + negative cases with runAs |

## Related Skills

- `security/permission-set-architecture` — permission-set design
- `security/security-apex-crud-fls` — CRUD/FLS enforcement
- `lwc/lwc-user-permission-aware-components` — LWC permission checks
