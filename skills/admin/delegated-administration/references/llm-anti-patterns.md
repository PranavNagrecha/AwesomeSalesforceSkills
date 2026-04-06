# LLM Anti-Patterns — Delegated Administration

Common mistakes AI coding assistants make when generating or advising on Salesforce Delegated Administration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Ignoring the role hierarchy requirement for delegated admin scope

**What the LLM generates:** "Create a delegated admin group and add the regional manager. They can now manage all users in the org."

**Why it happens:** LLMs describe delegated administration as org-wide user management. Delegated admins can only manage users whose role is at or below their own role in the hierarchy. If the delegated admin has no role, or their role is not above the target users' roles, they cannot manage those users.

**Correct pattern:**

```
Delegated admin scope is constrained by role hierarchy:
1. The delegated admin must have a role in the hierarchy.
2. They can only manage users whose roles are specified in the
   "User Administration" section of the Delegated Admin group.
3. Those specified roles must be at or below the delegated admin's role.
4. They CANNOT manage users in roles above their own or in
   unrelated branches of the hierarchy.

Example: Regional Manager (role: West Region Manager) can manage
users in roles: West Sales Rep, West SDR — but not East Sales Rep.
```

**Detection hint:** If the output says a delegated admin can manage "all users" without referencing role hierarchy constraints, the scope is wrong. Search for `role hierarchy` or `at or below` in the delegated admin instructions.

---

## Anti-Pattern 2: Assuming delegated admins can assign any profile

**What the LLM generates:** "The delegated admin can create new users and assign them whatever profile they need."

**Why it happens:** LLMs generalize user creation as unrestricted. Delegated admins can only assign profiles that are explicitly listed in the Delegated Admin group configuration. They cannot assign System Administrator or any other profile not in their allowed list.

**Correct pattern:**

```
Profile assignment is restricted:
1. In Setup → Delegated Administration → [Group] → User Administration:
   - Specify which profiles the delegated admin can assign.
   - Only these profiles appear in the Profile dropdown when the
     delegated admin creates or edits a user.
2. Best practice: include only the profiles for the business unit
   the delegated admin manages.
3. NEVER include the System Administrator profile in the allowed list
   unless you intend the delegated admin to create full admins.
```

**Detection hint:** If the output says delegated admins can assign "any profile" without mentioning the allowed profile list, the restriction is being ignored. Search for `allowed profiles` or `specify which profiles`.

---

## Anti-Pattern 3: Confusing delegated administration with the System Administrator profile

**What the LLM generates:** "Give the manager a System Administrator profile so they can manage their team's users."

**Why it happens:** LLMs reach for the simplest solution. System Administrator grants full access to everything in the org, not just user management. Delegated administration exists specifically to provide scoped user management without granting full system access.

**Correct pattern:**

```
Delegated Administration vs System Administrator:
- System Administrator: full access to all data, metadata, setup,
  and user management across the entire org. Not appropriate for
  limited user management tasks.
- Delegated Administration: scoped to specific roles, profiles,
  permission sets, and custom objects. No access to org-wide settings,
  metadata, Apex, or other administrative functions.

Use delegated admin for:
- Department heads who need to create/deactivate team members.
- Regional managers who reset passwords for their team.
- HR coordinators who manage user profiles for a business unit.
```

**Detection hint:** If the output recommends the System Administrator profile for someone who only needs to manage users in their team, the solution is over-provisioned. Search for `System Administrator` as a solution for user management.

---

## Anti-Pattern 4: Forgetting to configure permission set assignment delegation

**What the LLM generates:** "Set up delegated administration for the manager. They can now create users, reset passwords, and assign permission sets."

**Why it happens:** LLMs assume permission set assignment is included by default. Delegated admins can only assign permission sets that are explicitly listed in the Delegated Admin group's "Assignable Permission Sets" section. If no permission sets are listed, the delegated admin cannot assign any.

**Correct pattern:**

```
Configure permission set delegation explicitly:
1. In the Delegated Admin group, go to "Assignable Permission Sets."
2. Add the specific permission sets the delegated admin should be
   able to assign to their users.
3. If this section is empty, the delegated admin cannot assign
   any permission sets — only profiles (from the allowed list).
4. Review this list when new permission sets are created to ensure
   delegated admins can assign them if needed.
```

**Detection hint:** If the output says delegated admins can "assign permission sets" without mentioning the explicit assignable permission sets configuration, the setup is incomplete. Search for `Assignable Permission Sets` in the instructions.

---

## Anti-Pattern 5: Not testing delegated admin permissions from the delegated admin's perspective

**What the LLM generates:** "Configure the delegated admin group and the setup is complete."

**Why it happens:** LLMs stop at configuration and skip verification. The admin configuring delegation is a System Administrator who sees everything. Without testing as the delegated admin, issues like missing "Manage Users" button, invisible profiles in dropdowns, or inability to reset passwords go undetected until the delegated admin reports the problem.

**Correct pattern:**

```
Post-configuration verification:
1. Log in as the delegated admin (or use "Login As" from Setup → Users).
2. Verify they can see the "Manage Users" option in Setup.
3. Create a test user and confirm only the allowed profiles appear.
4. Reset a password for a user in an allowed role.
5. Attempt to assign a permission set from the allowed list.
6. Attempt to manage a user OUTSIDE their role scope — confirm it fails.
7. Attempt to assign a profile NOT in the allowed list — confirm it fails.
8. Document the verification results.
```

**Detection hint:** If the output ends at group configuration without a verification/testing step from the delegated admin's perspective, the setup is untested. Search for `log in as` or `verify` or `test` after the configuration steps.
