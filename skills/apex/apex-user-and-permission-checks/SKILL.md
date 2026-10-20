---
name: apex-user-and-permission-checks
description: "Use when Apex needs to check what the running user is, can see, or can do — via UserInfo, FeatureManagement, FeatureManagement.checkPermission, or FeatureManagement.checkPermissionType. Covers custom permissions, permission sets, user licenses, and profile checks. NOT for CRUD/FLS enforcement — use apex/apex-stripinaccessible-and-fls-enforcement. NOT for creating or assigning custom permissions in Setup — use admin/custom-permissions."
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
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Apex User And Permission Checks

Activates when Apex needs to branch on who the running user is or what they are allowed to do. Produces correct `FeatureManagement.checkPermission` usage, safe identity reads, and guidance to use custom permissions over profile-name checks.

---

## Before Starting

- What are you actually gating — UI behavior only, or server-side authorization? Server-side checks must be enforced with `stripInaccessible` / `user_mode` regardless of permission flags.
- Does a **Custom Permission** exist for this concept? If not, create one — it's the supported extensibility point.
- Is the check supposed to ignore admins (e.g., "even admins can't do this") or honor them? Whether Custom Permissions follow "Modify All Data" is UNVERIFIED (2026-10-20) — grant the permission to admins explicitly.
- Does this run in a Queueable, Batch, or `@future`? The running user is the async context user, not the originating user.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Does the check run in a Queueable, Batch, `@future` or platform event trigger? | Gotcha 1: `checkPermission` sees the running user | Whether the originator's Id must be passed in |
| Is a Custom Permission already defined for this concept? | Gotcha 3: a misspelt name is not an error | The exact DeveloperName to test |
| Should admins pass the gate? | Gotcha 2: admin behaviour is unverified | An explicit grant instead of an assumption |
| Is any grant made through a session-based permission set? | Gotcha 7: it needs activation | Whether the flow must activate it first |
| Does existing code derive access from the profile? | Gotcha 4: permission sets are invisible to `getProfileId()` | A list of profile-name checks to replace |
| Is this a custom permission or a managed-package feature parameter? | Gotcha 6: separate APIs | The right `FeatureManagement` method |
| Will tests run as an admin? | Gotcha 5: admin masks denials | Low-privilege test users for both paths |

A proper configuration names the permission an admin can grant and tests both paths, where "just doing it" hardcodes a profile name that breaks on the first rename.

---

## Core Concepts

### Prefer Custom Permissions Over Profile / Permission-Set Name Checks

The supported way to gate a feature in Apex is a Custom Permission. In Setup create `Perform_Bulk_Refund`, assign it to permission sets or profiles, and check with `FeatureManagement.checkPermission('Perform_Bulk_Refund')`, which "Checks whether a custom permission is enabled" (apexref 262 L215450-215454); its argument is "The API name of the custom permission" (L215460).

Checking `Profile.Name == 'Sales Manager'` is brittle: the name can be renamed in production, cloned profiles drift, and this check misses permission-set-based grants.

### `UserInfo` Gives Identity, Not Authorization

`UserInfo.getUserId()`, `.getUserName()`, `.getProfileId()`, and `.getSessionId()` report identity. Use them for logging and relationship lookups. Don't use `UserInfo.getProfileId()` to drive authorization — couple the gate to a permission the admin can grant. In async Apex, `getSessionId()` returns null when the code runs as an internal user such as the automated process user (apexref 262 L243297-243299).

### Async Context Switches The User

Apex in `@future`, Queueable, Batch, Scheduled, and platform event triggers runs as the async context user (often the user who fired the async; for scheduled jobs the scheduler — UNVERIFIED (2026-10-20): the Apex guide says only that "The scheduler runs as system" for class-access purposes, apexdev 264 L17006-17007, not which user `UserInfo` reports). A platform event Apex trigger runs "under the Automated Process entity or the user you select in the trigger configuration" (platform_events 264 L2309; override via PlatformEventSubscriberConfig, L2366-2368). `FeatureManagement.checkPermission` then checks that user's permissions. If you need the originating user, pass their Id explicitly and look up permissions via a query (see patterns).

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
        List<CustomPermission> cps =
            [SELECT Id FROM CustomPermission WHERE DeveloperName = :permApiName];
        if (cps.isEmpty()) return false;
        return ![
            SELECT Id FROM PermissionSetAssignment
            WHERE AssigneeId = :userId
            AND PermissionSetId IN (
                SELECT ParentId FROM SetupEntityAccess
                WHERE SetupEntityType = 'CustomPermission'
                AND SetupEntityId = :cps[0].Id
            )
        ].isEmpty();
    }
}
```

**Why not the alternative:** `FeatureManagement.checkPermission` silently checks the running (async context) user, not the originating user. The query shape follows the CustomPermission usage examples (object_reference 264 L88715-88724). Corrected 2026-10-20: the previous version filtered `PermissionSet.PermissionsCustomizeApplication = false`, which wrongly denied users whose permission set also grants Customize Application, and nested a second semi-join; the CustomPermission Id is now resolved first. The query does not check whether a session-based permission set is activated in the user's session (activation lives in `SessionPermSetActivation`, object_reference 264 L264542-264543), so it can report `true` for a grant that is not active.

### Pattern 3: Distinguish Internal Vs Community Users

**When to use:** Code behaves differently for Experience Cloud users vs internal licenses.

**How it works:**

```apex
public with sharing class UserContextUtil {
    public static Boolean isInternal() {
        return UserInfo.getUserType() == 'Standard';
    }
}
```

Corrected 2026-10-20: `UserInfo.getUserType()` returns a `String`, not an enum (apexref 262 L243451-243460) — the old `UserType t = ...; t == UserType.Standard` did not compile. `Standard` is the internal license value; `PowerPartner`, `CspLitePortal`, `CustomerSuccess`, `PowerCustomerSuccess`, `CsnOnly` and `Guest` are the others (object_reference 264 L300019-300037). Treating internal-only code paths as the default is safer than enumerating every external type.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Gate a feature | Custom Permission + `FeatureManagement.checkPermission` | Admin-manageable, rename-safe |
| Check user identity | `UserInfo` accessors | No query needed ("free and cached" is UNVERIFIED (2026-10-20)) |
| Check permission for async originator | Query `PermissionSetAssignment` / `SetupEntityAccess` | `checkPermission` uses running user |
| Distinguish internal vs community | `UserInfo.getUserType()` | License-aware and stable |
| Check Modify All Data | Query `PermissionSetAssignment` where `PermissionSet.PermissionsModifyAllData = true` (object_reference 264 L192754-192757) | Corrected 2026-10-20: `checkPermission` takes a custom permission API name (apexref 262 L215460), and `isMultiCurrencyOrganization` reports multi-currency (L243541-243542), not MAD |
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
2. **Admin bypass of Custom Permissions is UNVERIFIED (2026-10-20)** — grant the permission set explicitly rather than relying on "Modify All Data".
3. **Profile rename breaks hardcoded name checks** — prefer Custom Permissions.
4. **`System.runAs(admin)` in tests masks permission bugs** — test as real users.
5. **`FeatureManagement.checkPermission` returning `false` (not throwing) for undefined names is UNVERIFIED (2026-10-20)** — the reference documents only true/false for enabled/disabled (apexref 262 L215465); still, test the name.
6. **`UserInfo.getUserType()` returns a String** (apexref 262 L243456) — compare with `'Standard'`, there is no `UserType` enum.

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

- `apex/apex-security-patterns` — FLS/CRUD enforcement alongside permission gating
- `apex/async-apex` — user-context switches in async work
- `apex/apex-callable-interface` — permission-sensitive dynamic invocation
