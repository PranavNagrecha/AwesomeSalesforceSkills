---
name: delegated-administration
description: "Use when configuring delegated administration to allow non-system-admin users to manage specific user groups, reset passwords, assign permission sets, or administer custom objects. NOT for user management (use user-management) or full system admin setup."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "how do I let a manager reset passwords for their team without making them a system admin"
  - "delegate user admin to department heads so HR does not need to raise IT tickets"
  - "allow a non-admin to create users and assign profiles in a specific business unit"
  - "set up a regional admin who can only manage users in their own role hierarchy"
  - "delegated administrator cannot see the manage users button after being configured"
tags:
  - delegated-administration
  - user-management
  - security
  - role-hierarchy
  - profiles
  - permission-sets
inputs:
  - "Target org with existing role hierarchy and profiles defined"
  - "List of users who will act as delegated administrators"
  - "List of profiles the delegated admins are allowed to assign"
  - "List of permission sets (if any) the delegated admins are allowed to assign"
  - "Custom objects (if any) the delegated admins should be able to administer"
outputs:
  - "Configured Delegated Administrator group(s) in Setup"
  - "Delegated admin group members list with scoped access"
  - "Checklist confirming what delegated admins can and cannot do in the target org"
  - "Troubleshooting notes for permission errors"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Delegated Administration

This skill activates when you need to grant a non-System-Administrator user the ability to manage a scoped subset of users — including creating users, resetting passwords, assigning profiles and permission sets, or administering custom objects — without granting them full System Administrator access. It covers setup from scratch, review of existing configuration, and troubleshooting delegated admin permissions that are not working as expected.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the org has a role hierarchy defined. Delegated admins can only manage users whose role is **at or below** their own role in the hierarchy. A delegated admin without a role, or whose role is not above the target users' roles, will not be able to manage those users.
- Identify which profiles the delegated admins should be permitted to assign. Only the specific profiles listed in the Delegated Administrator group can be assigned by that delegated admin; they cannot freely assign any profile in the org.
- Confirm whether custom object administration is required. Delegated admins can be given the ability to customize specific custom objects (fields, page layouts, validation rules), but this is configured separately from user management rights.
- Know the key limit: delegated admins **cannot** manage System Administrator users, regardless of role hierarchy position. This is a platform-enforced constraint.

---

## Core Concepts

### Delegated Administrator Groups

A Delegated Administrator group is the core configuration object. Each group has:
- **Delegated Administrators** — the users who receive the delegated admin rights.
- **Users in Delegated Group** — the set of users those admins can manage, defined by the roles those users hold.
- **Assignable Profiles** — the profiles the delegated admin can assign when creating or editing managed users.
- **Assignable Permission Sets** — (optional) specific permission sets the delegated admin can assign to managed users.
- **Custom Object Administration** — (optional) specific custom objects the delegated admin can customize.

You can create multiple groups to model different business units or regions, each with their own scope.

### Role Hierarchy Enforcement

The role hierarchy is a hard constraint on delegated administration. When you add roles to the "Users in Delegated Group" configuration, the delegated admin can manage any user whose role is at or below the roles listed. The delegated admin's own role does not need to be a parent of the target roles — the role list in the group configuration is what determines scope. However, best practice is to align the delegated admin's role with the top of the roles they manage, to ensure consistent visibility across related features (reports, sharing, etc.).

One critical platform behavior: if a target user's role is not in the configured role list (or below it), the delegated admin will not see that user in their Manage Users view, even if they share a profile or group membership.

### What Delegated Admins Can and Cannot Do

**Can do:**
- Create new users with any profile listed in the group's Assignable Profiles
- Edit user details (name, email, title, phone) for users in their group
- Reset passwords for users in their group
- Freeze or unfreeze users in their group
- Assign or remove permission sets listed in the group's Assignable Permission Sets
- (If configured) Customize specific custom objects: add/edit fields, page layouts, validation rules, and list views

**Cannot do:**
- Create or edit System Administrator users (platform-enforced; no workaround)
- Assign profiles not listed in the group configuration
- Assign permission sets not listed in the group configuration
- Modify their own user record via the delegated admin interface
- Access Setup areas beyond Manage Users and (if configured) the specific custom objects
- Manage users whose roles are not in the group's role scope
- Create other delegated administrator groups or modify group configuration

### Custom Object Administration

Custom object administration rights are configured per Delegated Administrator group. You add specific custom objects to the group, and the delegated admins in that group gain the ability to:
- Create, edit, and delete custom fields on the object
- Create and assign page layouts
- Create validation rules
- Manage list views

This is useful for business unit owners who need to extend a custom object for their team without opening full Setup access.

---

## Common Patterns

### Pattern 1: Setting Up Delegated Administration From Scratch

**When to use:** A department head, regional manager, or HR coordinator needs to manage users in their business unit (create users, reset passwords, assign profiles) without escalating every request to the IT/Salesforce admin team.

**How it works:**

1. Go to **Setup > Users > Delegated Administrators**.
2. Click **New** to create a Delegated Administrator group. Give it a descriptive name (e.g., "APAC Sales Admin Group").
3. In the **Delegated Administrators** related list, click **Add** and search for the users who will act as delegated admins. Save.
4. In the **Users in Delegated Group** related list, click **Add** and select the roles whose users can be managed. The delegated admin will be able to manage users at these roles and all subordinate roles.
5. In the **Assignable Profiles** related list, click **Add** and select the profiles that the delegated admin is permitted to assign when creating or editing users.
6. (Optional) In the **Assignable Permission Sets** related list, click **Add** and select specific permission sets the delegated admin can assign.
7. (Optional) In the **Custom Object Administration** related list, click **Add** and select any custom objects the delegated admin should be able to customize.
8. Confirm the delegated admin users have the **Manage Users** profile permission enabled on their own profile or via a permission set. Without this permission, the Manage Users button does not appear in their personal setup.

**Why not the alternative:** Granting the System Administrator profile or cloning it with broad access creates an uncontrolled security risk. Permission sets alone cannot scope user-management rights to a subset of users — only Delegated Administrator groups provide role-scoped user management.

### Pattern 2: Reviewing Existing Delegated Admin Configuration

**When to use:** An admin suspects a delegated admin has too broad or too narrow access, or a compliance review requires audit of who can manage users.

**How it works:**

1. Go to **Setup > Users > Delegated Administrators**.
2. Review each group for: which users are Delegated Administrators, which roles are in scope, which profiles are assignable, and which permission sets are assignable.
3. For each delegated admin user, confirm their own profile has **Manage Users** enabled — this is a prerequisite that is often missed when the user's profile changes post-setup.
4. Cross-reference the role list against the org's role hierarchy diagram. Roles added to the group include all subordinate roles implicitly — confirm no unintended roles are in scope.
5. Check whether any delegated admins have been inadvertently given System Administrator profile access directly, which would bypass all scoping.

### Pattern 3: Troubleshooting Delegated Admin Permissions Not Working

**When to use:** A configured delegated admin reports they cannot see the Manage Users button, cannot see specific users, or cannot assign a profile or permission set.

**How it works:**

1. **Manage Users button missing:** Check the delegated admin's profile for the **Manage Users** system permission. This permission must be enabled separately — it is not automatically granted by being in a Delegated Administrator group.
2. **Cannot see specific users:** Check that those users' roles are in the Delegated Group's "Users in Delegated Group" configuration. If the target user has no role, or a role not in the list, they will not appear.
3. **Cannot assign a profile:** Check that the target profile is listed in the group's **Assignable Profiles** related list. Also confirm the target profile is not the System Administrator profile — that assignment is always blocked.
4. **Cannot assign a permission set:** Check the **Assignable Permission Sets** related list in the group configuration.
5. **Error when trying to manage a System Admin user:** This is expected platform behavior. System Administrator users are always protected and cannot be managed by delegated admins.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Manager needs to reset passwords only | Delegated Admin group with Manage Users permission, no assignable profiles needed | Least privilege; no profile-assignment rights required |
| HR team needs to onboard users for one business unit | Delegated Admin group scoped to that unit's roles with limited assignable profiles | Role-scoped; prevents HR from creating admins or assigning privileged profiles |
| Business unit owner needs to extend a custom object | Add Custom Object Administration to the Delegated Admin group | Avoids full Setup access; scoped to only the named objects |
| User needs to manage admins in a sub-org | Not possible via delegated administration | System Administrator users are platform-protected; use a separate Salesforce org or sandbox strategy |
| Multiple regions need independent admin groups | Create one Delegated Administrator group per region | Each group has independent role scope, profiles, and permission sets; no cross-region leakage |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Delegated Administrator group created with a clear, descriptive name
- [ ] Delegated Administrators (users) added to the group
- [ ] Roles in "Users in Delegated Group" are correct and do not include unintended subordinate roles
- [ ] Assignable Profiles list is minimal — only profiles the delegated admin legitimately needs to assign
- [ ] Delegated admin users' own profiles have the "Manage Users" system permission enabled
- [ ] Delegated admin confirmed they can see Manage Users in personal setup
- [ ] Tested: delegated admin cannot see or modify System Administrator users
- [ ] Tested: delegated admin cannot assign profiles outside the configured list
- [ ] (If custom object admin) Confirmed only the intended custom objects are listed

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Manage Users permission is a separate prerequisite** — Being added to a Delegated Administrator group does not automatically enable the Manage Users button. The delegated admin's profile or permission set must separately grant the **Manage Users** system permission. Admins who complete group setup and forget this step are confused when delegated admins report seeing no change in their Setup.

2. **Role hierarchy scope is additive, not restrictive** — When you add a role to the "Users in Delegated Group" list, the delegated admin can manage users at that role AND all subordinate roles. If a parent role is inadvertently added, the delegated admin gains access to more users than intended. Always add the most specific (lowest) roles in the intended scope, not the top of a large branch.

3. **System Administrator users are always protected** — No configuration can allow a delegated admin to create, edit, freeze, or reset passwords for System Administrator profile users. This trips up setups where a "super-delegated-admin" is expected to manage all users including admins. There is no workaround; escalate to a full System Administrator for those users.

4. **Custom object admin rights do not extend to standard objects** — Delegated admins granted custom object administration can only customize the specifically named custom objects. They cannot customize standard objects (Accounts, Contacts, Opportunities) and cannot access Setup areas beyond Manage Users and their named custom objects.

5. **Users without a role are invisible to delegated admins** — If a user record has no role assigned, they do not appear in the delegated admin's Manage Users view, even if the user shares the same profile. Always assign roles to users who need to be managed by delegated admins.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Delegated Administrator group | Configured group in Setup > Users > Delegated Administrators with members, role scope, assignable profiles, and optional permission sets |
| Delegated admin verification checklist | Completed checklist confirming what the delegated admin can and cannot do, tested in the org |
| Troubleshooting notes | Documented root cause and resolution for any permission gaps found during review |

---

## Related Skills

- admin/user-management — Use for full user provisioning, deactivation, license assignment, and role/profile setup that falls outside delegated admin scope
