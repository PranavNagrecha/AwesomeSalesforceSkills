---
name: apex-user-and-permission-checks
description: "Use when Apex needs to check what the running user is, can see, or can do — via UserInfo, FeatureManagement, FeatureManagement.checkPermission, or FeatureManagement.checkPermissionType. Covers custom permissions, permission sets, user licenses, and profile checks. NOT for FLS/CRUD (use Security.stripInaccessible or `with user_mode`), sharing rules, or external user license logic."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "check if the running user has a specific custom permission"
  - "different code path for internal vs community users"
  - "is this user a System Administrator — how do I check without hardcoding profile name"
  - "FeatureManagement.checkPermission returns false unexpectedly"
  - "gate a feature on a permission set rather than a profile"
tags:
  - apex-user-and-permission-checks
  - feature-management
  - custom-permissions
  - user-context
inputs:
  - "the permission or identity property being checked"
  - "the caller's context (trigger, LWC imperative, Queueable)"
  - "whether the check is for gating UI or enforcing server-side authorization"
outputs:
  - "correct use of `FeatureManagement.checkPermission('API_Name')` for custom permissions"
  - "guidance on Profile-name checks vs Permission Set checks"
  - "patterns for internal vs community user branching"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# Apex User And Permission Checks

Activates when Apex needs to branch on who the running user is or what they are allowed to do. Produces correct `FeatureManagement.checkPermission` usage, safe identity reads, and guidance to use custom permissions over profile-name checks.

---

## Before Starting

- What are you actually gating — UI behavior only, or server-side authorization? Server-side checks must be enforced with `stripInaccessible` / `user_mode` regardless of permission flags.
- Does a **Custom Permission** exist for this concept? If not, create one — it's the supported extensibility point.
- Is the check supposed to ignore admins (e.g., "even admins can't do this") or honor them (most permissions do)? Custom Permissions respect "Modify All Data."
- Does this run in a Queueable, Batch, or `@future`? The running user is the async context user, not the originating user.

---

## Core Concepts

### Prefer Custom Permissions Over Profile / Permission-Set Name Checks

The supported way to gate a feature in Apex is a Custom Permission. In Setup create `Perform_Bulk_Refund`, assign it to permission sets or profiles, and check with `FeatureManagement.checkPermission('Perform_Bulk_Refund')`. This returns `true` if the user has the permission via any assignment path.

Checking `Profile.Name == 'Sales Manager'` is brittle: the name can be renamed in production, cloned profiles drift, and this check misses permission-set-based grants.

### `UserInfo` Gives Identity, Not Authorization

`UserInfo.getUserId()`, `.getUserName()`, `.getProfileId()`, and `.getSessionId()` report identity. Use them for logging and relationship lookups. Don't use `UserInfo.getProfileId()` to drive authorization — couple the gate to a permission the admin can grant.

### Async Context Switches The User

Apex in `@future`, Queueable, Batch, Scheduled, and platform event triggers runs as the async context user (often the user who fired the async, but for scheduled jobs the scheduler, for platform events the "Automated Process" user). `FeatureManagement.checkPermission` then checks that user's permissions. If you need the originating user, pass their Id explicitly and look up permissions via a query (see patterns).

### Custom Permission Lookup Paths

`FeatureManagement.checkPermission('Name')` checks if the *running user* has the custom permission via Profile or Permission Set assignment. Multi-permission checks need an AND/OR logic built in Apex.

There is no `checkPermissionFor(userId, 'Name')` built-in. For a user other than the running user, query the `SetupEntityAccess` / `PermissionSetAssignment` / `CustomPermission` graph yourself.

---

## Common Patterns

### Pattern 1: Gate A Feature On A Custom Permission

**When to use:** Any code path that should be available only to users an admin has blessed.

**How it works:**

```apex
public with sharing class BulkRefundService {
    public static void initiate(Set<Id> paymentIds) {
        if (!FeatureManagement.checkPermission('Perform_Bulk_Refund')) {
            throw new NoAccessException('You do not have permission to perform bulk refunds.');
        }
        // proceed
    }
}
```

**Why not the alternative:** Hardcoding `Profile.Name == 'Finance Admin'` misses permission-set assignments and breaks on rename.

### Pattern 2: Check Custom Permission For A Different User

**When to use:** A Queueable running as the automated context needs to verify the originating user's permission.

**How it works:**

```apex
public class RefundQueueable implements Queueable {
    private final Id initiatingUserId;
    private final Set<Id> paymentIds;

    public RefundQueueable(Id initiatingUserId, Set<Id> paymentIds) {
        this.initiatingUserId = initiatingUserId;
        this.paymentIds = paymentIds;
    }

    public void execute(QueueableContext ctx) {
        if (!hasPermission(initiatingUserId, 'Perform_Bulk_Refund')) {
            throw new NoAccessException('Initiating user lacks bulk refund permission.');
        }
        // proceed
    }

    private static Boolean hasPermission(Id userId, String permApiName) {
        return ![
            SELECT Id FROM PermissionSetAssignment
            WHERE AssigneeId = :userId
            AND PermissionSet.PermissionsCustomizeApplication = false
            AND PermissionSetId IN (
                SELECT ParentId FROM SetupEntityAccess
                WHERE SetupEntityType = 'CustomPermission'
                AND SetupEntityId IN (
                    SELECT Id FROM CustomPermission WHERE DeveloperName = :permApiName
                )
            )
        ].isEmpty();
    }
}
```

**Why not the alternative:** `FeatureManagement.checkPermission` silently checks the running (async context) user, not the originating user.

### Pattern 3: Distinguish Internal Vs Community Users

**When to use:** Code behaves differently for Experience Cloud users vs internal licenses.

**How it works:**

```apex
public with sharing class UserContextUtil {
    public static Boolean isInternal() {
        UserType t = UserInfo.getUserType();
        return t == UserType.Standard;
    }
}
```

Where `UserType` is an enum and `Standard` represents internal users. Partner, Customer Success, CspLitePortal and others represent external. Treating internal-only code paths as the default is safer than enumerating every external type.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Gate a feature | Custom Permission + `FeatureManagement.checkPermission` | Admin-manageable, rename-safe |
| Check user identity | `UserInfo` accessors | They are free and cached |
| Check permission for async originator | Query `PermissionSetAssignment` / `SetupEntityAccess` | `checkPermission` uses running user |
| Distinguish internal vs community | `UserInfo.getUserType()` | License-aware and stable |
| Check Modify All Data | `FeatureManagement.checkPermission('ModifyAllData')` (built-in) or `UserInfo.isMultiCurrencyOrganization` equivalent | Avoid Profile-name checks |
| Test the check in unit tests | `System.runAs(testUser)` with proper permissions assigned | Running as System.runAs with Admin masks bugs |

---

## Recommended Workflow

1. Identify the concept being gated (e.g., "can initiate a refund"). Create a Custom Permission with a descriptive DeveloperName.
2. Assign the Custom Permission to the relevant Permission Sets (prefer over profiles).
3. In Apex, call `FeatureManagement.checkPermission('<DeveloperName>')`.
4. For server-side authorization, pair the check with `WITH USER_MODE` on SOQL and DML, or `Security.stripInaccessible`.
5. Write tests under `System.runAs(userWithPerm)` and `System.runAs(userWithoutPerm)` to prove both paths.
6. Avoid caching the result across transactions — permission assignments change.
7. Document the permission in the feature's README so admins know what to grant.

---

## Review Checklist

- [ ] No `Profile.Name == 'Something'` checks in security-sensitive code.
- [ ] Custom Permissions exist and have descriptive DeveloperNames.
- [ ] `FeatureManagement.checkPermission` is called only for the running user; async jobs pass the originator Id explicitly.
- [ ] Server-side authorization is paired with FLS/CRUD enforcement.
- [ ] Tests cover both the allowed and denied paths with `System.runAs`.
- [ ] Permission assignments are documented in the feature's admin guide.

---

## Salesforce-Specific Gotchas

See `references/gotchas.md` for the full list.

1. **Async context users differ from originators** — `checkPermission` in a Queueable checks the async user.
2. **Custom Permissions respect "Modify All Data"** — admins pass any permission check by default.
3. **Profile rename breaks hardcoded name checks** — prefer Custom Permissions.
4. **`System.runAs(admin)` in tests masks permission bugs** — test as real users.
5. **`FeatureManagement.checkPermission` returns `false` for undefined permissions without throwing** — typos silently deny.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `references/examples.md` | Custom permission gating, cross-user lookup, UserType branching |
| `references/gotchas.md` | Async context, profile rename, typo silent-false |
| `references/llm-anti-patterns.md` | Common LLM mistakes: profile-name checks, running-user assumption |
| `references/well-architected.md` | Security framing |
| `scripts/check_apex_user_and_permission_checks.py` | Stdlib lint for profile-name gating and cached permission results |

---

## Related Skills

- **apex-security-patterns** — FLS/CRUD enforcement alongside permission gating
- **apex-async-architecture** — user-context switches in async work
- **apex-callable-interface** — permission-sensitive dynamic invocation
