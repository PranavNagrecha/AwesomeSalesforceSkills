# Apex User And Permission Checks — Work Template

Use this template when adding or auditing permission gates in Apex.

## Scope

**Skill:** `apex-user-and-permission-checks`

**Request summary:** (what is being gated, and why)

## Gate Classification

- [ ] Server-side authorization (must combine with FLS/CRUD enforcement)
- [ ] UI gating only (safe to show/hide without hard enforcement)
- [ ] Feature flag / rollout (time-limited, admin-owned)
- [ ] Admin-bypassable (standard default)
- [ ] Admin-blocked (rare; call out explicitly)

## Context Gathered

- **Feature name:**
- **Existing check in code (if any):**
- **Who should have this access (roles, profiles, permission sets):**
- **Caller context (sync? async? callback?):**
- **Expected blast radius on accidental deny / accidental allow:**

## Approach

- [ ] Create Custom Permission `{{DeveloperName}}`
- [ ] Assign to Permission Set(s) `{{PS1, PS2}}`
- [ ] Apex gate via `FeatureManagement.checkPermission('{{DeveloperName}}')`
- [ ] Paired with `WITH USER_MODE` or `Security.stripInaccessible` for data access
- [ ] Async-originator lookup via PermissionSetAssignment SOQL (if async)

## Code Sketch

```apex
public with sharing class {{Service}} {
    public static void {{action}}({{inputType}} input) {
        if (!FeatureManagement.checkPermission('{{DeveloperName}}')) {
            throw new NoAccessException('Access required: {{DeveloperName}}');
        }
        // proceed using WITH USER_MODE on any SOQL/DML
    }
}
```

## Checklist

- [ ] No Profile.Name or Permission Set.Name string checks.
- [ ] Custom Permission DeveloperName is a spell-checked constant (no typos).
- [ ] Deployment validation test asserts a known-good user passes the check.
- [ ] Tests cover allowed AND denied paths with `System.runAs` on dedicated test users.
- [ ] If async: originator's Id is passed in and checked via SOQL.
- [ ] Feature's admin documentation names the Custom Permission and default assignments.

## Notes

Any edge cases (session-based perm sets, managed package co-existence, etc.).
