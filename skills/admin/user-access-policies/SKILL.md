---
name: user-access-policies
description: "Configuring User Access Policies (UAP) to automatically assign or revoke permission sets and permission set groups based on user attributes. Use when automating permission provisioning on user create/update without Apex triggers. Covers policy configuration, filter criteria, evaluation order, and PSL assignment. NOT for permission set design (use permission-set-architecture). NOT for delegated user management (use delegated-administration)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "automatically assign permission sets when user is created"
  - "revoke permission sets when user profile changes"
  - "automate permission provisioning without Apex triggers"
  - "login-based license assignment via user access policy"
  - "auto-provision permissions based on department or role"
tags:
  - user-access-policies
  - permission-sets
  - provisioning
  - automation
  - admin
inputs:
  - "User field criteria used to identify target users (Profile, Role, UserType, Department, custom fields)"
  - "List of permission sets or permission set groups to grant or revoke"
  - "Org release version (minimum release 242 / Spring '25 for GA)"
outputs:
  - "Configured User Access Policy records with filter criteria and permission assignments"
  - "Review checklist verifying evaluation order, filter logic, and PSL inclusion"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# User Access Policies

This skill activates when a practitioner needs to automate permission set or permission set group assignment and revocation based on user attribute criteria, without writing Apex triggers. It guides policy configuration, filter setup, evaluation order, and permission set license (PSL) assignment using the no-code User Access Policies feature (GA in release 242 / Spring '25).

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the org is on release 242 (Spring '25) or later — UAP reached GA in that release. Enhanced filter support for additional user fields was added in release 246 (Spring '26).
- Identify which user fields will serve as filter criteria: standard fields (Profile, Role, UserType, Department) and any custom user fields available from release 246 onward.
- Know whether the goal is granting permissions, revoking permissions, or both — grant and revoke policies are separate record types with distinct evaluation order (grant runs first).
- Confirm that the permission sets and permission set groups being assigned are already deployed and active in the org.
- Determine if Permission Set Licenses (PSLs) need to be managed alongside permission sets — UAP can assign and revoke PSLs using the same policy mechanism.
- Identify whether existing Apex-based permission assignment triggers exist — UAP does not replace triggers automatically; old triggers must be deactivated to avoid conflicts.

---

## Core Concepts

### Grant vs. Revoke Policy Types

User Access Policies are either Grant policies or Revoke policies. A Grant policy assigns one or more permission sets or permission set groups to users who match the filter criteria. A Revoke policy removes them. The platform evaluates all Grant policies before Revoke policies when a qualifying event occurs. This means if a user matches both a grant and a revoke policy targeting the same permission set, the revoke wins — the permission set is removed after being granted in the same evaluation pass.

### Trigger Events: User Create and User-Field Update

A policy fires on two events: when a user record is created, and when a qualifying user field included in any policy's filter criteria is updated. The platform does not re-evaluate every policy on every save — only policies whose filter fields were touched trigger re-evaluation. This makes it critical to include the correct fields in filter criteria. If a user's Profile changes but no UAP filter references Profile, no re-evaluation occurs.

### Filter Criteria and Available Fields

Filters define which users a policy targets. Standard supported fields include Profile, Role, UserType, and Department. From release 246 (Spring '26), additional custom user fields are supported as filter criteria, significantly expanding no-code provisioning scenarios. Filters use equality conditions and can combine multiple fields with AND logic. A user must match all filter conditions on a policy for that policy to apply.

### Permission Set License (PSL) Assignment

UAP can assign and revoke Permission Set Licenses in addition to permission sets and permission set groups. This is especially useful for managing license-gated features (such as Agentforce or Service Cloud features) without manual provisioning steps. The PSL must exist in the org. Assigning a PSL via UAP does not automatically assign the permission set that consumes it — both must be included in the policy or handled by separate policies.

### Evaluation Order and Conflict Resolution

Within each type (grant or revoke), policies are evaluated in the order they appear in the policy list. The platform processes all active grant policies first, then all active revoke policies. There is no merge or union logic for conflicts across grant and revoke policies — the revoke always takes effect last. Practitioners must design policies with this order in mind to avoid unexpected permission loss.

---

## Common Patterns

### Pattern 1: Profile-Based Permission Provisioning on Create

**When to use:** New users need a standard set of permission sets assigned based on their profile at the time of creation — replacing onboarding Apex triggers.

**How it works:**
1. Create a Grant policy with filter: `Profile = <target profile>`.
2. Add the required permission sets and permission set groups to the policy's assignment list.
3. Activate the policy.
4. When a user is created with the matching profile, the platform automatically assigns all listed permission sets.

**Why not the alternative:** Apex triggers on user creation require code maintenance, are not packageable as declarative configuration, and cannot be managed by admins without developer access. UAP provides the same outcome declaratively.

### Pattern 2: Role-Change Permission Revocation

**When to use:** When a user moves to a different role or department, previously granted permissions for their old role must be revoked automatically.

**How it works:**
1. Create a Revoke policy with filter: `Role = <old role>`.
2. Add the permission sets that should be removed when a user no longer holds that role.
3. Create a corresponding Grant policy for the new role.
4. When the user's Role field is updated, both policies re-evaluate: the old-role revoke fires and the new-role grant fires in the correct order (grant first, then revoke — so the net result for the new role is granted, and the old-role permissions are removed).

**Why not the alternative:** Manual permission cleanup on role changes is error-prone and frequently missed. Apex triggers on User updates are complex to maintain and require handling bulkification and role hierarchy traversal.

### Pattern 3: PSL Assignment Alongside Permission Set Groups

**When to use:** A feature requires both a PSL and a permission set group to function (e.g., an Agentforce feature seat).

**How it works:**
1. Create a Grant policy targeting the appropriate filter (e.g., `Department = Sales`).
2. Add both the PSL and the permission set group to the same policy's assignment list.
3. Activate the policy.
4. On user create or qualifying field update, both the PSL and the permission set group are provisioned in a single policy evaluation.

**Why not the alternative:** Managing PSL assignment separately from permission set assignment creates operational overhead and inconsistency when users move between teams.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need to assign permissions on user create based on Profile | UAP Grant policy with Profile filter | No-code, runs automatically on create, auditable |
| Need to revoke permissions when user changes department | UAP Revoke policy with Department filter | Re-evaluates on field update, no trigger required |
| Need to assign both a PSL and a PSG together | Single UAP Grant policy with both in assignment list | Atomic assignment in one policy evaluation |
| Conflict: same permission set targeted by both grant and revoke | Revoke wins (evaluated after grant) | Design policies to avoid unintended revocation |
| Custom user field needed as filter criterion | Requires release 246 (Spring '26) or later | Enhanced filter support added in release 246 |
| Complex multi-condition logic (OR, nested conditions) | UAP does not support OR logic — use Apex trigger | UAP filter supports AND logic only |
| Existing Apex trigger handles permission assignment | Deactivate trigger before enabling UAP | Both active simultaneously causes race conditions |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm prerequisites** — Verify the org is on release 242 or later. Confirm all permission sets, permission set groups, and PSLs to be assigned exist and are active. Identify whether any Apex triggers currently handle permission assignment for the same users.

2. **Define filter criteria** — Identify the user fields that determine which users a policy targets. Use standard fields (Profile, Role, UserType, Department) for orgs on release 242–245. Use custom user fields only when on release 246+. Document the exact field values that define each user segment.

3. **Design grant and revoke policy pairs** — For each provisioning scenario, plan both the grant policy (who gets what) and any corresponding revoke policy (what is removed when criteria no longer match). Map out evaluation order explicitly to confirm no unintended revocations occur.

4. **Create and configure policies** — In Setup, navigate to User Access Policies. Create Grant policies first, then Revoke policies. For each policy, set the filter criteria and add all permission sets, permission set groups, and PSLs to the assignment list. Save each policy in inactive state initially.

5. **Test in a sandbox** — Activate policies in a sandbox org. Create test users matching filter criteria and verify expected permission sets are assigned. Update a user's qualifying field (e.g., change Profile or Department) and confirm re-evaluation fires and permissions change correctly. Test conflict scenarios where both grant and revoke policies apply to the same user.

6. **Deactivate conflicting Apex triggers** — If existing Apex triggers assign or revoke permissions for the same user population, deactivate or delete them before activating UAP in production. Running both simultaneously can cause duplicate assignments, limit violations, or race conditions.

7. **Deploy and activate in production** — Deploy the UAP metadata to production. Activate policies in the correct order: grant policies first for clarity, then revoke policies. Run a post-activation spot check by creating a test user in each target segment and confirming correct permission assignment.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Org is confirmed on release 242 (Spring '25) or later
- [ ] All referenced permission sets, PSGs, and PSLs exist and are active in the target org
- [ ] Filter criteria cover all qualifying user segments — no users in scope are missed
- [ ] Grant and revoke policies are designed with evaluation order in mind (grant runs before revoke)
- [ ] No active Apex triggers conflict with the new UAP policies
- [ ] Policies have been validated in a sandbox by creating and updating test users
- [ ] Custom user field filters are used only on orgs at release 246 or later
- [ ] PSL assignment is included in the same policy as its corresponding permission set group where needed
- [ ] UAP metadata is included in the deployment package for change management (UserAccessPolicy metadata type)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Revoke always wins over grant in the same evaluation pass** — If a user matches both a Grant policy and a Revoke policy for the same permission set, the revoke takes effect because grant policies run first and revoke policies run second. The permission is removed. Practitioners who assume the most recently created or highest-priority policy wins will be surprised.

2. **Re-evaluation only fires when a filter field is updated** — If none of the fields referenced in any active policy's filter criteria are changed on a user update, no UAP re-evaluation occurs. A user whose Department changes will not trigger re-evaluation if no active policy uses Department as a filter field. This means users can drift out of sync with policies if their qualifying attributes are updated through integrations that bypass standard field tracking.

3. **UAP does not backfill existing users on activation** — Activating a new policy does not retroactively apply it to all existing users who match the filter. The policy only fires going forward on new creates or qualifying updates. Practitioners who activate a policy and expect bulk assignment across existing users will find no changes. A separate data operation or manual assignment run is required for existing users.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| UAP Grant Policy records | Active policies in Setup that assign permission sets/PSGs/PSLs on user create or field update |
| UAP Revoke Policy records | Active policies that remove permission sets/PSGs/PSLs when filter criteria no longer match |
| UserAccessPolicy metadata | Deployable metadata type included in SFDX/sf CLI project for change management |
| Provisioning audit trail | Setup Audit Trail entries recording policy activations, deactivations, and assignment events |

---

## Related Skills

- permission-set-architecture — use when designing the permission set and permission set group structure that UAP will assign; UAP is the provisioning mechanism, not the design tool
- delegated-administration — use when granting non-admin users the ability to manage other users' permissions manually; distinct from automated UAP provisioning
- permission-sets-vs-profiles — use when deciding whether to use profiles or permission sets as the primary access control mechanism before configuring UAP filters

---

## Official Sources Used

- Salesforce Help — User Access Policies: https://help.salesforce.com/s/articleView?id=sf.perm_user_access_policies.htm
- Salesforce Help — Active User Access Policy: https://help.salesforce.com/s/articleView?id=sf.perm_active_user_access_policy.htm
- Release Notes — User Access Policies GA (release 242): https://help.salesforce.com/s/articleView?id=release-notes.rn_permissions_user_access_policies_beta.htm
- Release Notes — UAP Enhanced Filter Support (release 246): https://help.salesforce.com/s/articleView?id=release-notes.rn_permissions_user_access_policy_filters.htm
